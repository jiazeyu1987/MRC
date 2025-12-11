#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RAGFlow配置管理模块

提供RAGFlow服务的配置定义、验证和环境加载功能
"""

import os
import logging
from typing import Optional
from dataclasses import dataclass

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
    connection_pool_size: int = 10
    max_pool_connections: int = 20

    def __post_init__(self):
        """配置验证和规范化"""
        if not self.api_base_url:
            raise ValueError("RAGFlow API基础URL不能为空")

        if not self.api_key:
            raise ValueError("RAGFlow API密钥不能为空")

        # 规范化URL格式
        if self.api_base_url.endswith('/'):
            self.api_base_url = self.api_base_url[:-1]

        # 验证参数范围
        if self.timeout <= 0:
            raise ValueError("超时时间必须大于0")

        if self.max_retries < 0:
            raise ValueError("最大重试次数不能为负数")

        if self.retry_delay < 0:
            raise ValueError("重试延迟不能为负数")

    @classmethod
    def from_env(cls) -> 'RAGFlowConfig':
        """从环境变量加载配置"""
        try:
            api_base_url = os.getenv('RAGFLOW_BASE_URL', '')
            api_key = os.getenv('RAGFLOW_API_KEY', '')

            if not api_base_url:
                raise ValueError("环境变量 RAGFLOW_BASE_URL 未设置")

            if not api_key:
                raise ValueError("环境变量 RAGFLOW_API_KEY 未设置")

            return cls(
                api_base_url=api_base_url,
                api_key=api_key,
                timeout=int(os.getenv('RAGFLOW_TIMEOUT', '30')),
                max_retries=int(os.getenv('RAGFLOW_MAX_RETRIES', '3')),
                retry_delay=float(os.getenv('RAGFLOW_RETRY_DELAY', '1.0')),
                verify_ssl=os.getenv('RAGFLOW_VERIFY_SSL', 'true').lower() == 'true',
                connection_pool_size=int(os.getenv('RAGFLOW_CONNECTION_POOL_SIZE', '10')),
                max_pool_connections=int(os.getenv('RAGFLOW_MAX_POOL_CONNECTIONS', '20'))
            )
        except Exception as e:
            logger.error(f"加载RAGFlow配置失败: {str(e)}")
            raise ValueError(f"RAGFlow配置错误: {str(e)}")

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'RAGFlowConfig':
        """从字典创建配置"""
        return cls(
            api_base_url=config_dict.get('api_base_url', ''),
            api_key=config_dict.get('api_key', ''),
            timeout=config_dict.get('timeout', 30),
            max_retries=config_dict.get('max_retries', 3),
            retry_delay=config_dict.get('retry_delay', 1.0),
            verify_ssl=config_dict.get('verify_ssl', True),
            connection_pool_size=config_dict.get('connection_pool_size', 10),
            max_pool_connections=config_dict.get('max_pool_connections', 20)
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'api_base_url': self.api_base_url,
            'timeout': self.timeout,
            'max_retries': self.max_retries,
            'retry_delay': self.retry_delay,
            'verify_ssl': self.verify_ssl,
            'connection_pool_size': self.connection_pool_size,
            'max_pool_connections': self.max_pool_connections
        }

    def validate_connection(self) -> bool:
        """验证配置的有效性"""
        try:
            # 基本配置验证已在__post_init__中完成
            # 这里可以添加额外的连接验证逻辑
            return True
        except Exception as e:
            logger.error(f"RAGFlow配置验证失败: {str(e)}")
            return False


@dataclass
class RAGFlowConnectionPool:
    """RAGFlow连接池配置"""
    pool_connections: int = 10
    pool_maxsize: int = 20
    max_retries: int = 3
    pool_block: bool = False

    def __post_init__(self):
        """配置验证"""
        if self.pool_connections <= 0:
            raise ValueError("连接池大小必须大于0")

        if self.pool_maxsize <= 0:
            raise ValueError("连接池最大大小必须大于0")

        if self.max_retries < 0:
            raise ValueError("最大重试次数不能为负数")


class RAGFlowConfigManager:
    """RAGFlow配置管理器"""

    def __init__(self):
        self._config: Optional[RAGFlowConfig] = None

    def load_config(self, config_source: Optional[Dict[str, Any]] = None) -> RAGFlowConfig:
        """加载配置"""
        if config_source:
            self._config = RAGFlowConfig.from_dict(config_source)
        else:
            self._config = RAGFlowConfig.from_env()

        logger.info(f"RAGFlow配置加载成功: {self._config.api_base_url}")
        return self._config

    def get_config(self) -> RAGFlowConfig:
        """获取当前配置"""
        if not self._config:
            raise ValueError("RAGFlow配置尚未加载")
        return self._config

    def reload_config(self, config_source: Optional[Dict[str, Any]] = None) -> RAGFlowConfig:
        """重新加载配置"""
        logger.info("重新加载RAGFlow配置")
        return self.load_config(config_source)

    def is_config_loaded(self) -> bool:
        """检查配置是否已加载"""
        return self._config is not None


# 全局配置管理器实例
config_manager = RAGFlowConfigManager()


def get_ragflow_config() -> RAGFlowConfig:
    """获取RAGFlow配置的便捷函数"""
    return config_manager.get_config()


def load_ragflow_config(config_source: Optional[Dict[str, Any]] = None) -> RAGFlowConfig:
    """加载RAGFlow配置的便捷函数"""
    return config_manager.load_config(config_source)