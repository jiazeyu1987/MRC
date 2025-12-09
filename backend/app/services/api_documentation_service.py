#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API文档服务模块

提供RAGFlow API文档缓存和检索的业务逻辑层功能，包括：
- API文档的缓存和同步
- 文档检索和分类
- API playground请求验证和执行
- 速率限制和安全验证
- 文档更新和过期管理

遵循MRC项目的现有模式，与其他服务保持一致的接口风格
"""

import logging
import json
import requests
import hashlib
import time
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
from flask import current_app
from sqlalchemy import and_, or_, desc

from app import db
from app.models import APIDocumentationCache
from app.services.ragflow_service import get_ragflow_service, RAGFlowAPIError
from app.services.cache_service import get_cache_service

logger = logging.getLogger(__name__)


class APIDocumentationError(Exception):
    """API文档服务错误基类"""
    pass


class APIDocumentationNotFoundError(APIDocumentationError):
    """API文档未找到错误"""
    pass


class APIRateLimitError(APIDocumentationError):
    """API速率限制错误"""
    def __init__(self, message, retry_after=None):
        super().__init__(message)
        self.retry_after = retry_after


class APIDocumentationService:
    """
    API文档服务类

    提供完整的API文档管理功能，包括：
    - API文档缓存和同步
    - 文档分类和检索
    - Playground请求验证
    - 安全和速率限制
    - 性能监控
    """

    def __init__(self):
        self.ragflow_service = get_ragflow_service()
        self.cache_service = get_cache_service()
        self.rate_limits = {}  # 简单的内存速率限制器

    # 文档缓存和同步
    def cache_api_documentation(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        缓存RAGFlow API文档

        Args:
            force_refresh: 是否强制刷新缓存

        Returns:
            Dict[str, Any]: 缓存结果统计

        Raises:
            APIDocumentationError: 缓存失败
        """
        try:
            # RAGFlow API端点定义
            endpoints = [
                # 文件上传端点
                {
                    'path': '/api/v1/dataset/upload',
                    'method': 'POST',
                    'category': 'documents',
                    'description': '上传单个文件到数据集',
                    'parameters': [
                        {
                            'name': 'dataset_id',
                            'type': 'string',
                            'required': True,
                            'description': '目标数据集ID'
                        },
                        {
                            'name': 'file',
                            'type': 'file',
                            'required': True,
                            'description': '要上传的文件'
                        },
                        {
                            'name': 'name',
                            'type': 'string',
                            'required': False,
                            'description': '自定义文件名'
                        },
                        {
                            'name': 'description',
                            'type': 'string',
                            'required': False,
                            'description': '文件内容描述'
                        }
                    ],
                    'examples': [
                        {
                            'description': '上传PDF文档',
                            'request': {
                                'dataset_id': 'dataset_123',
                                'name': 'My Document',
                                'description': 'Important reference document'
                            },
                            'response': {
                                'code': 0,
                                'message': 'Upload successful',
                                'data': {
                                    'file_id': 'file_123456',
                                    'dataset_id': 'dataset_123',
                                    'filename': 'document.pdf',
                                    'status': 'processing'
                                }
                            }
                        }
                    ]
                },
                {
                    'path': '/api/v1/dataset/upload_batch',
                    'method': 'POST',
                    'category': 'documents',
                    'description': '批量上传文件到数据集',
                    'parameters': [
                        {
                            'name': 'dataset_id',
                            'type': 'string',
                            'required': True,
                            'description': '目标数据集ID'
                        },
                        {
                            'name': 'file',
                            'type': 'file[]',
                            'required': True,
                            'description': '多个文件字段'
                        }
                    ],
                    'examples': [
                        {
                            'description': '批量上传文档',
                            'request': {
                                'dataset_id': 'dataset_123'
                            },
                            'response': {
                                'code': 0,
                                'message': 'Batch upload successful',
                                'data': {
                                    'uploaded_files': ['file_1', 'file_2'],
                                    'failed_files': []
                                }
                            }
                        }
                    ]
                },
                # 数据集管理端点
                {
                    'path': '/api/v1/datasets',
                    'method': 'GET',
                    'category': 'datasets',
                    'description': '获取数据集列表',
                    'parameters': [
                        {
                            'name': 'page',
                            'type': 'integer',
                            'required': False,
                            'description': '页码（默认：1）'
                        },
                        {
                            'name': 'size',
                            'type': 'integer',
                            'required': False,
                            'description': '页大小（默认：20）'
                        }
                    ],
                    'examples': [
                        {
                            'description': '获取数据集列表',
                            'request': {
                                'page': 1,
                                'size': 10
                            },
                            'response': {
                                'code': 0,
                                'data': {
                                    'datasets': [
                                        {
                                            'id': 'dataset_123',
                                            'name': 'My Knowledge Base',
                                            'description': 'Technical documentation',
                                            'document_count': 15
                                        }
                                    ],
                                    'total': 1,
                                    'page': 1
                                }
                            }
                        }
                    ]
                },
                {
                    'path': '/api/v1/datasets/{dataset_id}',
                    'method': 'GET',
                    'category': 'datasets',
                    'description': '获取数据集详情',
                    'parameters': [
                        {
                            'name': 'dataset_id',
                            'type': 'string',
                            'required': True,
                            'description': '数据集ID（路径参数）'
                        }
                    ],
                    'examples': [
                        {
                            'description': '获取数据集详情',
                            'response': {
                                'code': 0,
                                'data': {
                                    'id': 'dataset_123',
                                    'name': 'My Knowledge Base',
                                    'description': 'Technical documentation',
                                    'document_count': 15,
                                    'status': 'active'
                                }
                            }
                        }
                    ]
                },
                # 搜索和对话端点
                {
                    'path': '/api/v1/datasets/{dataset_id}/search',
                    'method': 'POST',
                    'category': 'search',
                    'description': '在数据集中搜索',
                    'parameters': [
                        {
                            'name': 'dataset_id',
                            'type': 'string',
                            'required': True,
                            'description': '数据集ID（路径参数）'
                        },
                        {
                            'name': 'question',
                            'type': 'string',
                            'required': True,
                            'description': '搜索问题'
                        },
                        {
                            'name': 'top_k',
                            'type': 'integer',
                            'required': False,
                            'description': '返回结果数量（默认：10）'
                        }
                    ],
                    'examples': [
                        {
                            'description': '搜索技术文档',
                            'request': {
                                'question': 'How to implement OAuth2?',
                                'top_k': 5
                            },
                            'response': {
                                'code': 0,
                                'data': {
                                    'answer': 'OAuth2 can be implemented...',
                                    'references': [
                                        {
                                            'document_id': 'doc_123',
                                            'content': '...',
                                            'score': 0.95
                                        }
                                    ]
                                }
                            }
                        }
                    ]
                },
                {
                    'path': '/api/v1/datasets/{dataset_id}/chat',
                    'method': 'POST',
                    'category': 'chat',
                    'description': '与数据集进行对话',
                    'parameters': [
                        {
                            'name': 'dataset_id',
                            'type': 'string',
                            'required': True,
                            'description': '数据集ID（路径参数）'
                        },
                        {
                            'name': 'message',
                            'type': 'string',
                            'required': True,
                            'description': '对话消息'
                        },
                        {
                            'name': 'session_id',
                            'type': 'string',
                            'required': False,
                            'description': '会话ID'
                        }
                    ],
                    'examples': [
                        {
                            'description': '与知识库对话',
                            'request': {
                                'message': 'What is the best practice for API design?',
                                'session_id': 'session_123'
                            },
                            'response': {
                                'code': 0,
                                'data': {
                                    'answer': 'Best practices for API design include...',
                                    'session_id': 'session_123'
                                }
                            }
                        }
                    ]
                }
            ]

            cached_count = 0
            updated_count = 0

            for endpoint in endpoints:
                # 检查是否需要更新
                cached = APIDocumentationCache.get_cached_endpoint(
                    endpoint['path'], endpoint['method']
                )

                if not cached or force_refresh or cached.is_expired():
                    # 缓存端点文档
                    self._cache_endpoint(
                        endpoint['path'],
                        endpoint['method'],
                        endpoint['category'],
                        endpoint,
                        endpoint.get('examples', [])
                    )
                    updated_count += 1
                else:
                    cached_count += 1

            # 清理过期的缓存
            expired_count = APIDocumentationCache.cleanup_expired()

            logger.info(f"API documentation cache updated: {cached_count} cached, {updated_count} updated, {expired_count} expired")

            return {
                'total_endpoints': len(endpoints),
                'cached_count': cached_count,
                'updated_count': updated_count,
                'expired_cleaned': expired_count,
                'timestamp': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to cache API documentation: {e}")
            raise APIDocumentationError(f"Failed to cache API documentation: {e}")

    def get_cached_documentation(self, force_refresh: bool = False, category: str = None) -> List[Dict[str, Any]]:
        """
        获取缓存的API文档

        Args:
            force_refresh: 是否强制刷新
            category: 文档分类

        Returns:
            List[Dict[str, Any]]: 缓存的文档列表
        """
        try:
            # 首先缓存API文档
            if force_refresh:
                self.cache_api_documentation(force_refresh=True)

            # 获取缓存的文档
            from app.models import APIDocumentationCache
            query = APIDocumentationCache.query.filter_by(is_active=True)

            if category:
                query = query.filter_by(category=category)

            cached_docs = query.order_by(APIDocumentationCache.last_updated.desc()).all()

            return [doc.to_dict() for doc in cached_docs]

        except Exception as e:
            self.logger.error(f"Failed to get cached documentation: {e}")
            return []

    def get_endpoints(self, category: str = None) -> List[Dict[str, Any]]:
        """
        获取API端点列表

        Args:
            category: 端点类别过滤

        Returns:
            List[Dict[str, Any]]: 端点列表
        """
        try:
            # 检查缓存
            cache_key = f"api_endpoints:{category or 'all'}"
            cached = self.cache_service.get(cache_key)
            if cached:
                return cached

            if category:
                endpoints = APIDocumentationCache.get_by_category(category)
            else:
                endpoints = APIDocumentationCache.query.filter(
                    and_(
                        APIDocumentationCache.is_active == True,
                        APIDocumentationCache.expires_at > datetime.utcnow()
                    )
                ).order_by(APIDocumentationCache.category, APIDocumentationCache.endpoint_path).all()

            endpoint_list = []
            for endpoint in endpoints:
                endpoint_data = endpoint.to_dict()
                endpoint_data['documentation'] = endpoint.documentation
                endpoint_list.append(endpoint_data)

            # 缓存结果（15分钟）
            self.cache_service.set(cache_key, endpoint_list, timeout=900)

            return endpoint_list

        except Exception as e:
            logger.error(f"Failed to get API endpoints: {e}")
            return []

    def get_endpoint_documentation(self, endpoint_path: str, method: str) -> Dict[str, Any]:
        """
        获取特定端点的文档

        Args:
            endpoint_path: 端点路径
            method: HTTP方法

        Returns:
            Dict[str, Any]: 端点文档

        Raises:
            APIDocumentationNotFoundError: 文档未找到
        """
        try:
            cached = APIDocumentationCache.get_cached_endpoint(endpoint_path, method)

            if not cached:
                raise APIDocumentationNotFoundError(f"Documentation not found for {method} {endpoint_path}")

            documentation = cached.to_dict()
            documentation['documentation'] = cached.documentation
            documentation['examples'] = cached.examples

            return documentation

        except Exception as e:
            logger.error(f"Failed to get endpoint documentation: {e}")
            raise

    # Playground功能
    def validate_playground_request(self, request_data: Dict[str, Any]) -> bool:
        """
        验证playground请求

        Args:
            request_data: 请求数据

        Returns:
            bool: 验证是否通过

        Raises:
            APIDocumentationError: 验证失败
        """
        try:
            required_fields = ['endpoint', 'method']
            for field in required_fields:
                if field not in request_data:
                    raise APIDocumentationError(f"Missing required field: {field}")

            endpoint_path = request_data['endpoint']
            method = request_data['method'].upper()

            # 检查端点是否在缓存中
            cached = APIDocumentationCache.get_cached_endpoint(endpoint_path, method)
            if not cached:
                raise APIDocumentationError(f"Endpoint not found in documentation: {method} {endpoint_path}")

            # 验证参数
            if 'parameters' in request_data:
                self._validate_parameters(request_data['parameters'], cached.documentation.get('parameters', []))

            return True

        except Exception as e:
            logger.error(f"Failed to validate playground request: {e}")
            raise

    def check_rate_limit(self, user_id: str = None, limit: int = 60, window_seconds: int = 3600) -> bool:
        """
        检查速率限制

        Args:
            user_id: 用户ID
            limit: 限制次数
            window_seconds: 时间窗口（秒）

        Returns:
            bool: 是否允许请求

        Raises:
            APIRateLimitError: 达到速率限制
        """
        try:
            if not user_id:
                return True  # 如果没有用户ID，跳过限制

            current_time = time.time()
            window_start = current_time - window_seconds

            # 简单的内存速率限制器
            if user_id not in self.rate_limits:
                self.rate_limits[user_id] = []

            # 清理过期的记录
            self.rate_limits[user_id] = [
                req_time for req_time in self.rate_limits[user_id]
                if req_time > window_start
            ]

            # 检查是否超过限制
            if len(self.rate_limits[user_id]) >= limit:
                retry_after = int(window_seconds - (current_time - self.rate_limits[user_id][0]))
                raise APIRateLimitError("Rate limit exceeded", retry_after)

            # 记录当前请求
            self.rate_limits[user_id].append(current_time)

            return True

        except APIRateLimitError:
            raise  # 重新抛出速率限制错误
        except Exception as e:
            logger.error(f"Failed to check rate limit: {e}")
            return True  # 出错时允许请求

    def execute_endpoint(self, endpoint_path: str, method: str,
                         parameters: Dict = None, request_body: Any = None,
                         api_key: str = None, timeout: int = 30) -> Dict[str, Any]:
        """
        执行API端点请求（模拟）

        Args:
            endpoint_path: 端点路径
            method: HTTP方法
            parameters: 请求参数
            request_body: 请求体
            api_key: API密钥
            timeout: 超时时间（秒）

        Returns:
            Dict[str, Any]: 执行结果

        Raises:
            APIDocumentationError: 执行失败
        """
        try:
            # 获取端点文档
            doc = self.get_endpoint_documentation(endpoint_path, method)
            documentation = doc['documentation']

            # 模拟请求执行（实际项目中这里会调用真实的API）
            execution_start = time.time()

            # 构建模拟响应
            mock_response = self._create_mock_response(
                endpoint_path, method, documentation,
                parameters, request_body
            )

            execution_time_ms = int((time.time() - execution_start) * 1000)

            result = {
                'endpoint': endpoint_path,
                'method': method,
                'request_time_ms': execution_time_ms,
                'timestamp': datetime.utcnow().isoformat(),
                'response': mock_response,
                'status_code': 200,
                'success': True
            }

            logger.info(f"Executed mock API request: {method} {endpoint_path} ({execution_time_ms}ms)")
            return result

        except Exception as e:
            logger.error(f"Failed to execute endpoint: {e}")
            return {
                'endpoint': endpoint_path,
                'method': method,
                'request_time_ms': 0,
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e),
                'status_code': 500,
                'success': False
            }

    # 辅助方法
    def _cache_endpoint(self, endpoint_path: str, method: str, category: str,
                       documentation: Dict, examples: List[Dict] = None):
        """缓存单个端点文档"""
        try:
            APIDocumentationCache.cache_endpoint(
                endpoint_path=endpoint_path,
                method=method,
                category=category,
                documentation=documentation,
                examples=examples or []
            )
        except Exception as e:
            logger.error(f"Failed to cache endpoint {method} {endpoint_path}: {e}")

    def _validate_parameters(self, request_params: Dict, param_definitions: List[Dict]):
        """验证请求参数"""
        required_params = [p for p in param_definitions if p.get('required', False)]
        for param in required_params:
            if param['name'] not in request_params:
                raise APIDocumentationError(f"Missing required parameter: {param['name']}")

    def _create_mock_response(self, endpoint_path: str, method: str, documentation: Dict,
                           parameters: Dict, request_body: Any) -> Dict[str, Any]:
        """创建模拟响应"""
        # 基于端点类型创建不同的模拟响应
        category = documentation.get('category', 'unknown')

        if category == 'search':
            return {
                'code': 0,
                'message': 'Search successful',
                'data': {
                    'answer': 'This is a mock search response for testing purposes.',
                    'references': [
                        {
                            'document_id': 'mock_doc_1',
                            'content': 'Mock document content',
                            'score': 0.95,
                            'title': 'Mock Document'
                        }
                    ]
                }
            }
        elif category == 'chat':
            return {
                'code': 0,
                'message': 'Chat response successful',
                'data': {
                    'answer': 'This is a mock chat response for testing purposes.',
                    'session_id': 'mock_session_123'
                }
            }
        elif category == 'datasets':
            return {
                'code': 0,
                'message': 'Datasets retrieved successfully',
                'data': {
                    'datasets': [
                        {
                            'id': 'mock_dataset_1',
                            'name': 'Mock Knowledge Base',
                            'description': 'This is a mock dataset for testing',
                            'document_count': 10,
                            'status': 'active'
                        }
                    ],
                    'total': 1,
                    'page': 1
                }
            }
        elif category == 'documents':
            return {
                'code': 0,
                'message': 'Document operation successful',
                'data': {
                    'file_id': 'mock_file_123',
                    'filename': 'mock_document.pdf',
                    'size': 1024000,
                    'status': 'completed'
                }
            }
        else:
            return {
                'code': 0,
                'message': 'Operation successful',
                'data': {
                    'endpoint': endpoint_path,
                    'method': method,
                    'processed_at': datetime.utcnow().isoformat()
                }
            }

    def get_cache_statistics(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            Dict[str, Any]: 缓存统计数据
        """
        try:
            total_cached = APIDocumentationCache.query.count()
            active_cached = APIDocumentationCache.query.filter(
                and_(
                    APIDocumentationCache.is_active == True,
                    APIDocumentationCache.expires_at > datetime.utcnow()
                )
            ).count()

            expired_cached = total_cached - active_cached

            # 按类别统计
            category_stats = db.session.query(
                APIDocumentationCache.category,
                func.count(APIDocumentationCache.id).label('count')
            ).group_by(APIDocumentationCache.category).all()

            return {
                'total_cached': total_cached,
                'active_cached': active_cached,
                'expired_cached': expired_cached,
                'categories': [
                    {'category': stat.category, 'count': stat.count}
                    for stat in category_stats
                ],
                'cache_efficiency': round((active_cached / max(total_cached, 1)) * 100, 2)
            }

        except Exception as e:
            logger.error(f"Failed to get cache statistics: {e}")
            return {
                'total_cached': 0,
                'active_cached': 0,
                'expired_cached': 0,
                'categories': [],
                'cache_efficiency': 0
            }

    def cleanup_cache(self, days: int = 30) -> int:
        """
        清理过期的API文档缓存

        Args:
            days: 保留天数

        Returns:
            int: 清理的记录数量
        """
        try:
            deleted_count = APIDocumentationCache.cleanup_expired()
            logger.info(f"Cleaned up {deleted_count} expired API documentation cache entries")
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup cache: {e}")
            return 0


# 全局服务实例
_api_documentation_service_instance = None


def get_api_documentation_service() -> APIDocumentationService:
    """获取API文档服务实例（单例模式）"""
    global _api_documentation_service_instance
    if _api_documentation_service_instance is None:
        _api_documentation_service_instance = APIDocumentationService()
    return _api_documentation_service_instance