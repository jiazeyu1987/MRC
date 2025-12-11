#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RAGFlow数据集模型

定义RAGFlow数据集相关的数据结构和操作
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


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
    ragflow_dataset_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DatasetInfo':
        """从字典创建DatasetInfo对象"""
        created_at = None
        updated_at = None

        # Handle RAGFlow timestamp format
        if data.get('create_date'):
            try:
                created_at = datetime.strptime(data['create_date'], '%a, %d %b %Y %H:%M:%S %Z')
            except (ValueError, AttributeError):
                logger.warning(f"无法解析创建时间: {data.get('create_date')}")

        if data.get('update_date'):
            try:
                updated_at = datetime.strptime(data['update_date'], '%a, %d %b %Y %H:%M:%S %Z')
            except (ValueError, AttributeError):
                logger.warning(f"无法解析更新时间: {data.get('update_date')}")

        return cls(
            id=str(data.get('id', '')),
            name=data.get('name', ''),
            description=data.get('description', ''),
            document_count=int(data.get('document_count', 0)),
            size=int(data.get('token_num', 0)),  # RAGFlow uses token_num for size
            status=data.get('status', '1'),
            created_at=created_at,
            updated_at=updated_at,
            ragflow_dataset_id=data.get('dataset_id'),
            metadata=data.get('metadata', {})
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'document_count': self.document_count,
            'size': self.size,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'ragflow_dataset_id': self.ragflow_dataset_id,
            'metadata': self.metadata or {}
        }

    def is_active(self) -> bool:
        """检查数据集是否活跃"""
        return self.status == '1'

    def is_empty(self) -> bool:
        """检查数据集是否为空"""
        return self.document_count == 0

    def get_size_mb(self) -> float:
        """获取大小（MB）"""
        return round(self.size / (1024 * 1024), 2)


@dataclass
class DatasetSyncResult:
    """数据集同步结果"""
    total_datasets: int
    created_count: int
    updated_count: int
    failed_count: int
    errors: List[Dict[str, Any]]
    duration: float

    def __post_init__(self):
        if self.errors is None:
            self.errors = []

    @property
    def success_count(self) -> int:
        """成功数量"""
        return self.created_count + self.updated_count

    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_datasets == 0:
            return 0.0
        return (self.success_count / self.total_datasets) * 100

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'total_datasets': self.total_datasets,
            'created': self.created_count,
            'updated': self.updated_count,
            'failed': self.failed_count,
            'success_count': self.success_count,
            'success_rate': round(self.success_rate, 2),
            'errors': self.errors,
            'duration': round(self.duration, 2)
        }


@dataclass
class DatasetRefreshResult:
    """数据集刷新结果"""
    dataset_id: str
    success: bool
    new_info: Optional[DatasetInfo] = None
    error_message: Optional[str] = None
    duration: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            'dataset_id': self.dataset_id,
            'success': self.success,
            'duration': round(self.duration, 2)
        }

        if self.new_info:
            result['new_info'] = self.new_info.to_dict()

        if self.error_message:
            result['error_message'] = self.error_message

        return result


@dataclass
class DatasetStatistics:
    """数据集统计信息"""
    dataset_id: str
    document_count: int
    total_tokens: int
    total_size: int
    last_sync_time: Optional[datetime] = None
    sync_status: str = 'unknown'
    processing_documents: int = 0
    failed_documents: int = 0

    def __post_init__(self):
        if self.last_sync_time is None:
            self.last_sync_time = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'dataset_id': self.dataset_id,
            'document_count': self.document_count,
            'total_tokens': self.total_tokens,
            'total_size': self.total_size,
            'last_sync_time': self.last_sync_time.isoformat(),
            'sync_status': self.sync_status,
            'processing_documents': self.processing_documents,
            'failed_documents': self.failed_documents,
            'total_size_mb': round(self.total_size / (1024 * 1024), 2)
        }


class DatasetValidator:
    """数据集验证器"""

    @staticmethod
    def validate_dataset_info(data: Dict[str, Any]) -> List[str]:
        """验证数据集信息"""
        errors = []

        if not data.get('id'):
            errors.append("数据集ID不能为空")

        if not data.get('name'):
            errors.append("数据集名称不能为空")

        document_count = data.get('document_count', 0)
        try:
            document_count = int(document_count)
            if document_count < 0:
                errors.append("文档数量不能为负数")
        except (ValueError, TypeError):
            errors.append("文档数量必须是有效的数字")

        size = data.get('token_num', 0)
        try:
            size = int(size)
            if size < 0:
                errors.append("数据集大小不能为负数")
        except (ValueError, TypeError):
            errors.append("数据集大小必须是有效的数字")

        return errors

    @staticmethod
    def is_valid_dataset(data: Dict[str, Any]) -> bool:
        """检查数据集是否有效"""
        return len(DatasetValidator.validate_dataset_info(data)) == 0