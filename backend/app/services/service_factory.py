#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
服务工厂

提供服务实例的创建、管理和依赖注入
"""

import logging
from typing import Optional, Dict, Any
from functools import lru_cache

from .ragflow.client.http_client import RAGFlowHTTPClient
from .ragflow.models.config import RAGFlowConfig, config_manager
from .ragflow.datasets.dataset_service import RAGFlowDatasetService
from .ragflow.chat.chat_service import RAGFlowChatService
from .ragflow.retry.retry_strategy import RetryStrategy
from .flow_engine.engine.flow_engine import FlowEngine
from .flow_engine.llm_integration.llm_service import LLMIntegrationService
from .flow_engine.debug_manager.debug_service import DebugService

logger = logging.getLogger(__name__)


class ServiceFactory:
    """服务工厂类"""

    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._initialized = False

    def initialize(self) -> None:
        """初始化所有服务"""
        if self._initialized:
            return

        try:
            logger.info("开始初始化服务工厂")

            # 初始化RAGFlow配置
            config_manager.load_config()
            logger.info("RAGFlow配置初始化完成")

            # 初始化服务实例
            self._initialize_ragflow_services()
            self._initialize_flow_engine_services()
            self._initialize_integration_services()

            self._initialized = True
            logger.info("服务工厂初始化完成")

        except Exception as e:
            logger.error(f"服务工厂初始化失败: {str(e)}")
            raise

    def _initialize_ragflow_services(self) -> None:
        """初始化RAGFlow相关服务"""
        # 创建HTTP客户端
        ragflow_client = RAGFlowHTTPClient(config_manager.get_config())
        self._services['ragflow_client'] = ragflow_client

        # 创建重试策略
        retry_strategy = RetryStrategy(config_manager.get_config())
        self._services['ragflow_retry_strategy'] = retry_strategy

        # 创建数据集服务
        dataset_service = RAGFlowDatasetService(ragflow_client)
        self._services['ragflow_dataset_service'] = dataset_service

        # 创建聊天服务
        chat_service = RAGFlowChatService(ragflow_client)
        self._services['ragflow_chat_service'] = chat_service

        logger.info("RAGFlow服务初始化完成")

    def _initialize_flow_engine_services(self) -> None:
        """初始化流程引擎相关服务"""
        # 创建LLM集成服务
        llm_service = LLMIntegrationService()
        self._services['llm_integration_service'] = llm_service

        # 创建调试服务
        debug_service = DebugService()
        self._services['debug_service'] = debug_service

        # 创建流程引擎
        flow_engine = FlowEngine(llm_service, debug_service)
        self._services['flow_engine'] = flow_engine

        logger.info("流程引擎服务初始化完成")

    def _initialize_integration_services(self) -> None:
        """初始化集成服务"""
        # 这里可以添加其他集成服务
        logger.info("集成服务初始化完成")

    @lru_cache(maxsize=1)
    def get_ragflow_config(self) -> RAGFlowConfig:
        """获取RAGFlow配置"""
        return config_manager.get_config()

    def get_ragflow_client(self) -> RAGFlowHTTPClient:
        """获取RAGFlow HTTP客户端"""
        self._ensure_initialized()
        return self._services['ragflow_client']

    def get_ragflow_dataset_service(self) -> RAGFlowDatasetService:
        """获取RAGFlow数据集服务"""
        self._ensure_initialized()
        return self._services['ragflow_dataset_service']

    def get_ragflow_chat_service(self) -> 'RAGFlowChatService':
        """获取RAGFlow聊天服务"""
        self._ensure_initialized()
        return self._services['ragflow_chat_service']

    def get_flow_engine(self) -> FlowEngine:
        """获取流程引擎"""
        self._ensure_initialized()
        return self._services['flow_engine']

    def get_llm_integration_service(self) -> LLMIntegrationService:
        """获取LLM集成服务"""
        self._ensure_initialized()
        return self._services['llm_integration_service']

    def get_debug_service(self) -> DebugService:
        """获取调试服务"""
        self._ensure_initialized()
        return self._services['debug_service']

    def _ensure_initialized(self) -> None:
        """确保服务已初始化"""
        if not self._initialized:
            raise RuntimeError("服务工厂尚未初始化，请先调用initialize()方法")

    def shutdown(self) -> None:
        """关闭所有服务"""
        logger.info("开始关闭服务工厂")

        # 关闭RAGFlow客户端
        if 'ragflow_client' in self._services:
            self._services['ragflow_client'].close()

        # 清理服务实例
        self._services.clear()
        self._initialized = False

        logger.info("服务工厂已关闭")

    def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        status = {
            'initialized': self._initialized,
            'service_count': len(self._services),
            'services': {}
        }

        if self._initialized:
            for name, service in self._services.items():
                try:
                    status['services'][name] = {
                        'type': type(service).__name__,
                        'available': True
                    }
                except Exception as e:
                    status['services'][name] = {
                        'type': type(service).__name__,
                        'available': False,
                        'error': str(e)
                    }

        return status

    def reload_config(self, config_source: Optional[Dict[str, Any]] = None) -> None:
        """重新加载配置"""
        try:
            logger.info("重新加载服务配置")

            # 关闭现有客户端
            if 'ragflow_client' in self._services:
                self._services['ragflow_client'].close()

            # 重新加载配置
            config_manager.reload_config(config_source)

            # 重新初始化RAGFlow服务
            self._initialize_ragflow_services()

            logger.info("服务配置重新加载完成")

        except Exception as e:
            logger.error(f"重新加载配置失败: {str(e)}")
            raise


# 全局服务工厂实例
service_factory = ServiceFactory()


def initialize_services() -> None:
    """初始化所有服务的便捷函数"""
    service_factory.initialize()


def shutdown_services() -> None:
    """关闭所有服务的便捷函数"""
    service_factory.shutdown()


# 服务获取函数
def get_ragflow_service() -> RAGFlowDatasetService:
    """获取RAGFlow服务的便捷函数"""
    return service_factory.get_ragflow_dataset_service()


def get_ragflow_client() -> RAGFlowHTTPClient:
    """获取RAGFlow客户端的便捷函数"""
    return service_factory.get_ragflow_client()


def get_flow_engine() -> FlowEngine:
    """获取流程引擎的便捷函数"""
    return service_factory.get_flow_engine()


def get_llm_service() -> LLMIntegrationService:
    """获取LLM集成服务的便捷函数"""
    return service_factory.get_llm_integration_service()


def get_debug_service() -> DebugService:
    """获取调试服务的便捷函数"""
    return service_factory.get_debug_service()


# 兼容性函数 - 保持与原有代码的兼容性
def get_ragflow_service_legacy():
    """获取RAGFlow服务的兼容性函数"""
    try:
        return get_ragflow_service()
    except Exception:
        # 如果新服务不可用，创建传统服务实例
        from .ragflow_service import get_ragflow_service as legacy_service
        return legacy_service()


# 装饰器：确保服务已初始化
def ensure_services_initialized(func):
    """确保服务已初始化的装饰器"""
    def wrapper(*args, **kwargs):
        if not service_factory._initialized:
            initialize_services()
        return func(*args, **kwargs)
    return wrapper