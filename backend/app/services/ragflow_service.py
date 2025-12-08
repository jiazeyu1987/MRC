#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RAGFlow服务模块

用于与RAGFlow API集成的核心服务，提供：
- 数据集管理（获取、刷新知识库）
- 聊天助手功能（基于知识库的问答）
- 连接管理和配置验证
- 重试逻辑和错误处理
- 连接测试和健康检查

遵循MRC项目的现有模式，与LLM服务保持一致的接口风格
"""

import requests
import json
import time
import logging
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..utils.request_tracker import RequestTracker, log_llm_info, log_llm_error, log_llm_warning

logger = logging.getLogger(__name__)


@dataclass
class RAGFlowConfig:
    """RAGFlow配置类"""
    api_base_url: str
    api_key: str
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    verify_ssl: bool = True

    def __post_init__(self):
        """配置验证和规范化"""
        if not self.api_base_url:
            raise ValueError("RAGFlow API基础URL不能为空")

        if not self.api_key:
            raise ValueError("RAGFlow API密钥不能为空")

        # 规范化URL格式
        if self.api_base_url.endswith('/'):
            self.api_base_url = self.api_base_url[:-1]


@dataclass
class DatasetInfo:
    """RAGFlow数据集信息"""
    id: str
    name: str
    description: str
    document_count: int
    size: int
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DatasetInfo':
        """从字典创建DatasetInfo对象"""
        created_at = None
        updated_at = None

        # Handle RAGFlow timestamp format (e.g., "Mon, 08 Dec 2025 11:08:06 GMT")
        if data.get('create_date'):
            try:
                # RAGFlow uses create_date field
                created_at = datetime.strptime(data['create_date'], '%a, %d %b %Y %H:%M:%S %Z')
            except (ValueError, AttributeError):
                pass

        if data.get('update_date'):
            try:
                # RAGFlow uses update_date field
                updated_at = datetime.strptime(data['update_date'], '%a, %d %b %Y %H:%M:%S %Z')
            except (ValueError, AttributeError):
                pass

        return cls(
            id=str(data.get('id', '')),
            name=data.get('name', ''),
            description=data.get('description', ''),
            document_count=int(data.get('document_count', 0)),
            size=int(data.get('token_num', 0)),  # RAGFlow uses token_num for size
            status=data.get('status', '1'),  # RAGFlow uses "1" for active status
            created_at=created_at,
            updated_at=updated_at
        )


@dataclass
class ChatResponse:
    """RAGFlow聊天响应"""
    answer: str
    confidence_score: float
    references: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    response_time: float
    dataset_id: str
    query: str

    @classmethod
    def from_api_response(
        cls,
        api_response: Dict[str, Any],
        query: str,
        dataset_id: str,
        response_time: float
    ) -> 'ChatResponse':
        """从API响应创建ChatResponse对象"""
        return cls(
            answer=api_response.get('answer', ''),
            confidence_score=float(api_response.get('confidence_score', 0.0)),
            references=api_response.get('references', []),
            metadata=api_response.get('metadata', {}),
            response_time=response_time,
            dataset_id=dataset_id,
            query=query
        )


class RAGFlowAPIError(Exception):
    """RAGFlow API错误基类"""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}


class RAGFlowConnectionError(RAGFlowAPIError):
    """RAGFlow连接错误"""
    pass


class RAGFlowConfigError(RAGFlowAPIError):
    """RAGFlow配置错误"""
    pass


class RAGFlowService:
    """
    RAGFlow服务类

    提供与RAGFlow API的完整集成功能，包括：
    - 数据集管理和知识库操作
    - 聊天助手和问答功能
    - 连接测试和健康检查
    - 错误处理和重试逻辑
    """

    def __init__(self, config: Optional[RAGFlowConfig] = None):
        """
        初始化RAGFlow服务

        Args:
            config (RAGFlowConfig): RAGFlow配置，如果为None则从环境变量读取
        """
        if config is None:
            config = self._load_config_from_env()

        self.config = config
        self.session = self._create_session()

        log_llm_info(
            "RAGFLOW_SERVICE",
            "RAGFlow服务已初始化",
            additional_params={
                "api_base_url": self.config.api_base_url,
                "timeout": self.config.timeout,
                "max_retries": self.config.max_retries
            }
        )

    def _load_config_from_env(self) -> RAGFlowConfig:
        """从环境变量加载配置"""
        try:
            api_base_url = os.environ.get('RAGFLOW_API_BASE_URL', '')
            api_key = os.environ.get('RAGFLOW_API_KEY', '')

            if not api_base_url:
                raise RAGFlowConfigError("RAGFLOW_API_BASE_URL环境变量未设置")
            if not api_key:
                raise RAGFlowConfigError("RAGFLOW_API_KEY环境变量未设置")

            return RAGFlowConfig(
                api_base_url=api_base_url,
                api_key=api_key,
                timeout=int(os.environ.get('RAGFLOW_TIMEOUT', '30')),
                max_retries=int(os.environ.get('RAGFLOW_MAX_RETRIES', '3')),
                retry_delay=float(os.environ.get('RAGFLOW_RETRY_DELAY', '1.0')),
                verify_ssl=os.environ.get('RAGFLOW_VERIFY_SSL', 'true').lower() == 'true'
            )
        except ValueError as e:
            raise RAGFlowConfigError(f"RAGFlow配置参数错误: {str(e)}")

    def _create_session(self) -> requests.Session:
        """创建配置了重试逻辑的HTTP会话"""
        session = requests.Session()

        # 配置重试策略
        if self.config.max_retries > 0:
            # 尝试创建重试适配器，兼容不同版本的urllib3
            try:
                retry_strategy = Retry(
                    total=self.config.max_retries,
                    backoff_factor=self.config.retry_delay,
                    status_forcelist=[429, 500, 502, 503, 504]
                )
                adapter = HTTPAdapter(max_retries=retry_strategy)
                session.mount("http://", adapter)
                session.mount("https://", adapter)
            except Exception:
                # 如果重试配置失败，使用无重试的会话
                log_llm_warning(
                    "RAGFLOW_SERVICE",
                    "重试策略配置失败，使用无重试会话",
                    error="Retry configuration failed"
                )

        # 设置默认请求头
        session.headers.update({
            'Authorization': f'Bearer {self.config.api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'MRC-RAGFlow-Service/1.0'
        })

        return session

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        发起HTTP请求（带重试和错误处理）

        Args:
            method (str): HTTP方法
            endpoint (str): API端点
            data (Optional[Dict]): 请求数据
            request_id (Optional[str]): 请求ID用于日志追踪

        Returns:
            Dict[str, Any]: API响应数据

        Raises:
            RAGFlowAPIError: API相关错误
        """
        url = f"{self.config.api_base_url}{endpoint}"

        # 如果没有传入request_id，尝试从当前上下文获取
        if request_id is None:
            context = RequestTracker.get_context()
            request_id = context.request_id if context else "UNKNOWN"

        log_llm_info(
            "RAGFLOW_SERVICE",
            f"发起RAGFlow API请求: {method} {endpoint}",
            request_id,
            url=url,
            has_data=data is not None
        )

        start_time = time.time()

        try:
            if data is not None:
                response = self.session.request(
                    method=method,
                    url=url,
                    json=data,
                    timeout=self.config.timeout,
                    verify=self.config.verify_ssl
                )
            else:
                response = self.session.request(
                    method=method,
                    url=url,
                    timeout=self.config.timeout,
                    verify=self.config.verify_ssl
                )

            response_time = time.time() - start_time

            # 检查HTTP状态码
            if response.status_code >= 400:
                error_data = None
                try:
                    error_data = response.json()
                except (ValueError, json.JSONDecodeError):
                    pass

                log_llm_error(
                    "RAGFLOW_SERVICE",
                    f"RAGFlow API请求失败: HTTP {response.status_code}",
                    request_id,
                    status_code=response.status_code,
                    response_text=response.text[:500],
                    response_time=f"{response_time:.3f}s",
                    error_data=error_data
                )

                raise RAGFlowAPIError(
                    f"RAGFlow API请求失败: HTTP {response.status_code}",
                    status_code=response.status_code,
                    response_data=error_data
                )

            # 解析响应数据
            try:
                response_data = response.json()
            except (ValueError, json.JSONDecodeError) as e:
                log_llm_error(
                    "RAGFLOW_SERVICE",
                    "RAGFlow API响应JSON解析失败",
                    request_id,
                    response_text=response.text[:200],
                    response_time=f"{response_time:.3f}s",
                    error=str(e)
                )
                raise RAGFlowAPIError(f"RAGFlow API响应格式错误: {str(e)}")

            log_llm_info(
                "RAGFLOW_SERVICE",
                "RAGFlow API请求成功",
                request_id,
                status_code=response.status_code,
                response_time=f"{response_time:.3f}s",
                response_keys=list(response_data.keys()) if isinstance(response_data, dict) else "non_dict"
            )

            return response_data

        except requests.exceptions.RequestException as e:
            response_time = time.time() - start_time

            log_llm_error(
                "RAGFLOW_SERVICE",
                "RAGFlow API请求异常",
                request_id,
                error=str(e),
                error_type=type(e).__name__,
                response_time=f"{response_time:.3f}s"
            )

            raise RAGFlowConnectionError(f"RAGFlow连接失败: {str(e)}")

    def test_connection(self, request_id: Optional[str] = None) -> bool:
        """
        测试RAGFlow连接

        Args:
            request_id (Optional[str]): 请求ID

        Returns:
            bool: 连接是否成功
        """
        try:
            # 使用datasets端点进行连接测试（RAGFlow没有health端点）
            response_data = self._make_request('GET', '/api/v1/datasets', request_id=request_id)
            success = response_data.get('code') == 0

            if success:
                log_llm_info(
                    "RAGFLOW_SERVICE",
                    "RAGFlow连接测试成功",
                    request_id
                )
            else:
                log_llm_error(
                    "RAGFLOW_SERVICE",
                    "RAGFlow连接测试失败：响应状态异常",
                    request_id,
                    response_data=response_data
                )

            return success

        except Exception as e:
            log_llm_error(
                "RAGFLOW_SERVICE",
                "RAGFlow连接测试异常",
                request_id,
                error=str(e)
            )
            return False

    def get_datasets(self, request_id: Optional[str] = None) -> List[DatasetInfo]:
        """
        获取RAGFlow数据集列表

        Args:
            request_id (Optional[str]): 请求ID

        Returns:
            List[DatasetInfo]: 数据集信息列表

        Raises:
            RAGFlowAPIError: API调用失败
        """
        try:
            response_data = self._make_request('GET', '/api/v1/datasets', request_id=request_id)

            datasets = []
            # RAGFlow API returns data in 'data' field, not 'datasets'
            for item in response_data.get('data', []):
                try:
                    dataset = DatasetInfo.from_dict(item)
                    datasets.append(dataset)
                except (ValueError, KeyError) as e:
                    log_llm_warning(
                        "RAGFLOW_SERVICE",
                        f"跳过无效的数据集项: {str(e)}",
                        request_id,
                        item_data=item
                    )
                    continue

            log_llm_info(
                "RAGFLOW_SERVICE",
                f"获取RAGFlow数据集成功，共{len(datasets)}个",
                request_id,
                dataset_count=len(datasets)
            )

            return datasets

        except RAGFlowAPIError:
            raise
        except Exception as e:
            log_llm_error(
                "RAGFLOW_SERVICE",
                "获取RAGFlow数据集失败",
                request_id,
                error=str(e)
            )
            raise RAGFlowAPIError(f"获取数据集失败: {str(e)}")

    def get_dataset(self, dataset_id: str, request_id: Optional[str] = None) -> Optional[DatasetInfo]:
        """
        获取指定数据集信息

        Args:
            dataset_id (str): 数据集ID
            request_id (Optional[str]): 请求ID

        Returns:
            Optional[DatasetInfo]: 数据集信息，如果不存在则返回None

        Raises:
            RAGFlowAPIError: API调用失败
        """
        try:
            response_data = self._make_request(
                'GET',
                f'/api/v1/datasets/{dataset_id}',
                request_id=request_id
            )

            dataset = DatasetInfo.from_dict(response_data)

            log_llm_info(
                "RAGFLOW_SERVICE",
                f"获取RAGFlow数据集成功: {dataset.name}",
                request_id,
                dataset_id=dataset_id,
                dataset_name=dataset.name,
                document_count=dataset.document_count
            )

            return dataset

        except RAGFlowAPIError as e:
            if e.status_code == 404:
                log_llm_warning(
                    "RAGFLOW_SERVICE",
                    f"RAGFlow数据集不存在: {dataset_id}",
                    request_id,
                    dataset_id=dataset_id
                )
                return None
            else:
                raise
        except Exception as e:
            log_llm_error(
                "RAGFLOW_SERVICE",
                f"获取RAGFlow数据集失败: {dataset_id}",
                request_id,
                error=str(e)
            )
            raise RAGFlowAPIError(f"获取数据集失败: {str(e)}")

    def refresh_dataset(self, dataset_id: str, request_id: Optional[str] = None) -> bool:
        """
        刷新指定数据集（重新索引）

        Args:
            dataset_id (str): 数据集ID
            request_id (Optional[str]): 请求ID

        Returns:
            bool: 刷新是否成功

        Raises:
            RAGFlowAPIError: API调用失败
        """
        try:
            response_data = self._make_request(
                'POST',
                f'/api/v1/datasets/{dataset_id}/refresh',
                request_id=request_id
            )

            success = response_data.get('success', False)

            if success:
                log_llm_info(
                    "RAGFLOW_SERVICE",
                    f"RAGFlow数据集刷新成功: {dataset_id}",
                    request_id,
                    dataset_id=dataset_id
                )
            else:
                log_llm_warning(
                    "RAGFLOW_SERVICE",
                    f"RAGFlow数据集刷新失败: {dataset_id}",
                    request_id,
                    dataset_id=dataset_id,
                    response_data=response_data
                )

            return success

        except RAGFlowAPIError:
            raise
        except Exception as e:
            log_llm_error(
                "RAGFLOW_SERVICE",
                f"RAGFlow数据集刷新异常: {dataset_id}",
                request_id,
                error=str(e)
            )
            raise RAGFlowAPIError(f"数据集刷新失败: {str(e)}")

    def chat_with_dataset(
        self,
        dataset_id: str,
        question: str,
        request_id: Optional[str] = None,
        **kwargs
    ) -> ChatResponse:
        """
        使用指定数据集进行聊天问答

        Args:
            dataset_id (str): 数据集ID
            question (str): 用户问题
            request_id (Optional[str]): 请求ID
            **kwargs: 额外参数（如top_k, similarity_threshold等）

        Returns:
            ChatResponse: 聊天响应对象

        Raises:
            RAGFlowAPIError: API调用失败
        """
        try:
            # 构建请求数据
            request_data = {
                'question': question,
                'dataset_id': dataset_id,
                **kwargs
            }

            log_llm_info(
                "RAGFLOW_SERVICE",
                f"开始RAGFlow聊天问答",
                request_id,
                dataset_id=dataset_id,
                question_length=len(question),
                question_preview=question[:100] + "..." if len(question) > 100 else question,
                additional_params=kwargs
            )

            start_time = time.time()
            response_data = self._make_request(
                'POST',
                '/api/v1/chat/completions',
                data=request_data,
                request_id=request_id
            )
            response_time = time.time() - start_time

            chat_response = ChatResponse.from_api_response(
                response_data,
                question,
                dataset_id,
                response_time
            )

            log_llm_info(
                "RAGFLOW_SERVICE",
                "RAGFlow聊天问答成功",
                request_id,
                dataset_id=dataset_id,
                response_time=f"{response_time:.3f}s",
                answer_length=len(chat_response.answer),
                confidence_score=chat_response.confidence_score,
                reference_count=len(chat_response.references)
            )

            return chat_response

        except RAGFlowAPIError:
            raise
        except Exception as e:
            log_llm_error(
                "RAGFLOW_SERVICE",
                "RAGFlow聊天问答异常",
                request_id,
                dataset_id=dataset_id,
                error=str(e)
            )
            raise RAGFlowAPIError(f"聊天问答失败: {str(e)}")

    def validate_config(self) -> Tuple[bool, List[str]]:
        """
        验证RAGFlow配置

        Returns:
            Tuple[bool, List[str]]: (是否有效, 错误信息列表)
        """
        errors = []

        try:
            # 验证配置对象
            if not self.config.api_base_url:
                errors.append("API基础URL不能为空")
            elif not self.config.api_base_url.startswith(('http://', 'https://')):
                errors.append("API基础URL格式无效")

            if not self.config.api_key:
                errors.append("API密钥不能为空")
            elif len(self.config.api_key) < 10:
                errors.append("API密钥长度过短")

            if self.config.timeout <= 0:
                errors.append("超时时间必须大于0")

            if self.config.max_retries < 0:
                errors.append("最大重试次数不能为负数")

            if self.config.retry_delay < 0:
                errors.append("重试延迟不能为负数")

            if not errors:
                # 尝试连接测试
                if not self.test_connection():
                    errors.append("RAGFlow服务连接失败")

        except Exception as e:
            errors.append(f"配置验证异常: {str(e)}")

        is_valid = len(errors) == 0

        if is_valid:
            log_llm_info(
                "RAGFLOW_SERVICE",
                "RAGFlow配置验证通过"
            )
        else:
            log_llm_error(
                "RAGFLOW_SERVICE",
                "RAGFlow配置验证失败",
                error_count=len(errors),
                errors=errors
            )

        return is_valid, errors

    def get_service_status(self) -> Dict[str, Any]:
        """
        获取服务状态信息

        Returns:
            Dict[str, Any]: 服务状态
        """
        try:
            is_connected = self.test_connection()

            status = {
                'service': 'ragflow',
                'connected': is_connected,
                'config': {
                    'api_base_url': self.config.api_base_url,
                    'timeout': self.config.timeout,
                    'max_retries': self.config.max_retries,
                    'verify_ssl': self.config.verify_ssl
                },
                'timestamp': datetime.utcnow().isoformat()
            }

            if is_connected:
                try:
                    datasets = self.get_datasets()
                    status['dataset_count'] = len(datasets)
                except:
                    status['dataset_count'] = None
                    status['datasets_error'] = True

            return status

        except Exception as e:
            return {
                'service': 'ragflow',
                'connected': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }


# 全局服务实例
_ragflow_service: Optional[RAGFlowService] = None


def get_ragflow_service() -> Optional[RAGFlowService]:
    """
    获取RAGFlow服务实例（单例模式）

    Returns:
        Optional[RAGFlowService]: RAGFlow服务实例，如果配置无效则返回None
    """
    global _ragflow_service

    if _ragflow_service is None:
        try:
            _ragflow_service = RAGFlowService()
        except RAGFlowConfigError as e:
            log_llm_error(
                "RAGFLOW_SERVICE",
                "RAGFlow服务初始化失败：配置错误",
                error=str(e)
            )
            _ragflow_service = None
        except Exception as e:
            log_llm_error(
                "RAGFLOW_SERVICE",
                "RAGFlow服务初始化失败：未知错误",
                error=str(e)
            )
            _ragflow_service = None

    return _ragflow_service


def create_ragflow_service(config: RAGFlowConfig) -> RAGFlowService:
    """
    创建新的RAGFlow服务实例

    Args:
        config (RAGFlowConfig): RAGFlow配置

    Returns:
        RAGFlowService: 新的服务实例
    """
    return RAGFlowService(config)


# 模块初始化时的健康检查
def _init_ragflow_service():
    """初始化RAGFlow服务模块"""
    try:
        service = get_ragflow_service()
        if service:
            is_valid, errors = service.validate_config()
            if not is_valid:
                log_llm_warning(
                    "RAGFLOW_SERVICE",
                    "RAGFlow服务配置验证失败，服务将不可用",
                    errors=errors
                )
        else:
            log_llm_info(
                "RAGFLOW_SERVICE",
                "RAGFlow服务未配置，跳过初始化"
            )
    except Exception as e:
        log_llm_error(
            "RAGFLOW_SERVICE",
            "RAGFlow服务模块初始化失败",
            error=str(e)
        )


# 自动执行初始化
_init_ragflow_service()


if __name__ == "__main__":
    # 直接运行此文件时执行测试
    print("正在测试RAGFlow服务...")

    try:
        service = get_ragflow_service()
        if service:
            print("✅ RAGFlow服务创建成功")

            # 测试配置验证
            is_valid, errors = service.validate_config()
            if is_valid:
                print("✅ 配置验证通过")
            else:
                print(f"❌ 配置验证失败: {errors}")

            # 测试连接
            if service.test_connection():
                print("✅ 连接测试成功")

                # 测试获取数据集
                try:
                    datasets = service.get_datasets()
                    print(f"✅ 获取数据集成功，共{len(datasets)}个")
                    for dataset in datasets[:3]:  # 只显示前3个
                        print(f"   - {dataset.name} ({dataset.document_count}个文档)")
                except Exception as e:
                    print(f"❌ 获取数据集失败: {e}")
            else:
                print("❌ 连接测试失败")
        else:
            print("❌ RAGFlow服务创建失败（配置问题）")

    except Exception as e:
        print(f"❌ RAGFlow服务测试失败: {e}")