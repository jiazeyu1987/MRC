#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RAGFlow HTTP客户端

提供与RAGFlow API的HTTP通信功能，包括连接管理、请求处理和响应解析
"""

import requests
import json
import logging
import time
from typing import Optional, Dict, Any, Tuple
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..models.config import RAGFlowConfig, RAGFlowConnectionPool
from .retry import RetryStrategy

logger = logging.getLogger(__name__)


class RAGFlowHTTPClient:
    """RAGFlow HTTP客户端"""

    def __init__(self, config: RAGFlowConfig):
        self.config = config
        self.session: Optional[requests.Session] = None
        self.retry_strategy = RetryStrategy(config)
        self._setup_session()

    def _setup_session(self) -> None:
        """设置HTTP会话"""
        self.session = requests.Session()

        # 设置重试策略
        retry = Retry(
            total=self.config.max_retries,
            backoff_factor=self.config.retry_delay,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"]
        )

        # 设置适配器
        adapter = HTTPAdapter(
            pool_connections=self.config.connection_pool_size,
            pool_maxsize=self.config.max_pool_connections,
            max_retries=retry
        )

        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # 设置默认头部
        self.session.headers.update({
            'Authorization': f'Bearer {self.config.api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'MRC-RAGFlow-Client/1.0'
        })

        logger.debug("RAGFlow HTTP客户端初始化完成")

    def _build_url(self, endpoint: str) -> str:
        """构建完整的API URL"""
        if endpoint.startswith('/'):
            return f"{self.config.api_base_url}{endpoint}"
        return f"{self.config.api_base_url}/{endpoint}"

    def _prepare_request(self, method: str, endpoint: str,
                         data: Optional[Dict[str, Any]] = None,
                         params: Optional[Dict[str, Any]] = None,
                         headers: Optional[Dict[str, str]] = None) -> Tuple[str, Dict, Optional[Dict]]:
        """准备请求"""
        url = self._build_url(endpoint)

        # 合并headers
        request_headers = {}
        if headers:
            request_headers.update(headers)

        # 处理数据
        request_data = None
        if data is not None:
            if method.upper() in ['POST', 'PUT', 'PATCH']:
                request_data = json.dumps(data)

        return url, request_headers, request_data

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """处理响应"""
        try:
            response.raise_for_status()

            if response.content:
                return response.json()
            else:
                return {}

        except requests.exceptions.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {str(e)}, 响应内容: {response.text[:500]}")
            raise ValueError("响应格式无效")
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP错误: {str(e)}, 状态码: {response.status_code}")
            self._handle_http_error(response, e)
        except Exception as e:
            logger.error(f"响应处理失败: {str(e)}")
            raise

    def _handle_http_error(self, response: requests.Response, original_error: Exception) -> None:
        """处理HTTP错误"""
        try:
            error_data = response.json()
            error_message = error_data.get('message', f"HTTP {response.status_code}: {response.reason}")
            error_code = error_data.get('error_code', f'HTTP_{response.status_code}')
        except (ValueError, KeyError):
            error_message = f"HTTP {response.status_code}: {response.reason}"
            error_code = f'HTTP_{response.status_code}'

        from ..models.config import RAGFlowAPIError
        raise RAGFlowAPIError(
            message=error_message,
            status_code=response.status_code,
            response_data={'error_code': error_code, 'response_text': response.text[:500]}
        ) from original_error

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """发送GET请求"""
        return self._request('GET', endpoint, params=params, headers=headers)

    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None,
             params: Optional[Dict[str, Any]] = None,
             headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """发送POST请求"""
        return self._request('POST', endpoint, data=data, params=params, headers=headers)

    def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None,
            params: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """发送PUT请求"""
        return self._request('PUT', endpoint, data=data, params=params, headers=headers)

    def delete(self, endpoint: str, params: Optional[Dict[str, Any]] = None,
               headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """发送DELETE请求"""
        return self._request('DELETE', endpoint, params=params, headers=headers)

    def _request(self, method: str, endpoint: str,
                data: Optional[Dict[str, Any]] = None,
                params: Optional[Dict[str, Any]] = None,
                headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """执行HTTP请求"""
        if not self.session:
            raise RuntimeError("HTTP客户端未正确初始化")

        url, request_headers, request_data = self._prepare_request(
            method, endpoint, data, params, headers
        )

        start_time = time.time()

        try:
            logger.debug(f"发送{method}请求: {url}")

            response = self.session.request(
                method=method,
                url=url,
                data=request_data,
                params=params,
                headers=request_headers,
                timeout=self.config.timeout
            )

            duration = time.time() - start_time
            logger.debug(f"请求完成: {url}, 耗时: {duration:.2f}s, 状态码: {response.status_code}")

            result = self._handle_response(response)

            # 记录请求日志（可选）
            self._log_request(method, url, duration, response.status_code)

            return result

        except requests.exceptions.Timeout as e:
            duration = time.time() - start_time
            logger.error(f"请求超时: {url}, 耗时: {duration:.2f}s")
            from ..models.config import RAGFlowAPIError
            raise RAGFlowAPIError(
                message=f"请求超时: {str(e)}",
                status_code=408
            ) from e

        except requests.exceptions.ConnectionError as e:
            duration = time.time() - start_time
            logger.error(f"连接错误: {url}, 耗时: {duration:.2f}s")
            from ..models.config import RAGFlowConnectionError
            raise RAGFlowConnectionError(
                message=f"连接错误: {str(e)}",
                status_code=503
            ) from e

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"请求失败: {url}, 耗时: {duration:.2f}s, 错误: {str(e)}")
            raise

    def _log_request(self, method: str, url: str, duration: float, status_code: int) -> None:
        """记录请求日志"""
        # 这里可以集成到现有的请求追踪系统
        try:
            from ...utils.request_tracker import log_llm_info
            log_llm_info(f"RAGFlow {method} {url}", {
                'duration': duration,
                'status_code': status_code,
                'method': method,
                'endpoint': url
            })
        except ImportError:
            # 如果请求追踪系统不可用，使用基本日志
            logger.info(f"RAGFlow {method} {url} - {status_code} ({duration:.2f}s)")

    def test_connection(self) -> Dict[str, Any]:
        """测试连接"""
        try:
            # 使用一个简单的端点测试连接
            response = self.get('/api/v1/datasets', params={'page': 1, 'page_size': 1})
            return {
                'success': True,
                'message': '连接成功',
                'response_time': time.time(),
                'server_info': response.get('server', 'unknown')
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'连接失败: {str(e)}',
                'error_type': type(e).__name__
            }

    def close(self) -> None:
        """关闭HTTP客户端"""
        if self.session:
            self.session.close()
            self.session = None
            logger.debug("RAGFlow HTTP客户端已关闭")

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()