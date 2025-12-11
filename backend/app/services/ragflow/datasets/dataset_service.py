#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RAGFlow数据集服务

提供RAGFlow数据集的CRUD操作和同步功能
"""

import logging
import time
from typing import List, Dict, Any, Optional, Tuple

from ..client.http_client import RAGFlowHTTPClient
from ..models.config import RAGFlowConfig
from ..models.dataset import DatasetInfo, DatasetSyncResult, DatasetRefreshResult, DatasetValidator
from ..retry.retry_strategy import RetryStrategy

logger = logging.getLogger(__name__)


class RAGFlowDatasetService:
    """RAGFlow数据集服务"""

    def __init__(self, client: RAGFlowHTTPClient):
        self.client = client
        self.retry_strategy = RetryStrategy(client.config)

    def list_datasets(self, page: int = 1, page_size: int = 20,
                      filters: Optional[Dict[str, Any]] = None) -> Tuple[List[DatasetInfo], int]:
        """获取数据集列表"""
        try:
            params = {
                'page': page,
                'page_size': page_size
            }

            if filters:
                params.update(filters)

            response = self.retry_strategy.execute_with_retry(
                self.client.get,
                '/api/v1/datasets',
                params=params
            )

            datasets = []
            if response.get('data'):
                for dataset_data in response['data']:
                    if DatasetValidator.is_valid_dataset(dataset_data):
                        datasets.append(DatasetInfo.from_dict(dataset_data))
                    else:
                        logger.warning(f"跳过无效数据集: {dataset_data.get('id', 'unknown')}")

            total = response.get('total', 0)
            logger.info(f"获取数据集列表成功: {len(datasets)}/{total}")

            return datasets, total

        except Exception as e:
            logger.error(f"获取数据集列表失败: {str(e)}")
            raise

    def get_dataset(self, dataset_id: str) -> Optional[DatasetInfo]:
        """获取单个数据集信息"""
        try:
            response = self.retry_strategy.execute_with_retry(
                self.client.get,
                f'/api/v1/datasets/{dataset_id}'
            )

            if response.get('data'):
                dataset_info = DatasetInfo.from_dict(response['data'])
                logger.info(f"获取数据集信息成功: {dataset_id}")
                return dataset_info
            else:
                logger.warning(f"数据集不存在: {dataset_id}")
                return None

        except Exception as e:
            logger.error(f"获取数据集信息失败 {dataset_id}: {str(e)}")
            raise

    def create_dataset(self, name: str, description: str = "",
                       metadata: Optional[Dict[str, Any]] = None) -> DatasetInfo:
        """创建数据集"""
        try:
            data = {
                'name': name,
                'description': description
            }

            if metadata:
                data['metadata'] = metadata

            response = self.retry_strategy.execute_with_retry(
                self.client.post,
                '/api/v1/datasets',
                data=data
            )

            if response.get('data'):
                dataset_info = DatasetInfo.from_dict(response['data'])
                logger.info(f"创建数据集成功: {dataset_info.name}")
                return dataset_info
            else:
                raise ValueError("创建数据集失败: 响应数据为空")

        except Exception as e:
            logger.error(f"创建数据集失败 {name}: {str(e)}")
            raise

    def update_dataset(self, dataset_id: str, name: Optional[str] = None,
                       description: Optional[str] = None,
                       metadata: Optional[Dict[str, Any]] = None) -> Optional[DatasetInfo]:
        """更新数据集"""
        try:
            data = {}
            if name is not None:
                data['name'] = name
            if description is not None:
                data['description'] = description
            if metadata is not None:
                data['metadata'] = metadata

            if not data:
                logger.warning(f"没有提供更新数据: {dataset_id}")
                return self.get_dataset(dataset_id)

            response = self.retry_strategy.execute_with_retry(
                self.client.put,
                f'/api/v1/datasets/{dataset_id}',
                data=data
            )

            if response.get('data'):
                dataset_info = DatasetInfo.from_dict(response['data'])
                logger.info(f"更新数据集成功: {dataset_info.name}")
                return dataset_info
            else:
                logger.warning(f"更新数据集失败: {dataset_id}")
                return None

        except Exception as e:
            logger.error(f"更新数据集失败 {dataset_id}: {str(e)}")
            raise

    def delete_dataset(self, dataset_id: str) -> bool:
        """删除数据集"""
        try:
            self.retry_strategy.execute_with_retry(
                self.client.delete,
                f'/api/v1/datasets/{dataset_id}'
            )

            logger.info(f"删除数据集成功: {dataset_id}")
            return True

        except Exception as e:
            logger.error(f"删除数据集失败 {dataset_id}: {str(e)}")
            raise

    def sync_datasets(self, local_datasets: List[Dict[str, Any]]) -> DatasetSyncResult:
        """同步数据集（从RAGFlow到本地）"""
        start_time = time.time()
        sync_result = DatasetSyncResult(
            total_datasets=len(local_datasets),
            created_count=0,
            updated_count=0,
            failed_count=0,
            errors=[]
        )

        try:
            # 获取RAGFlow中的所有数据集
            ragflow_datasets, _ = self.list_datasets(page=1, page_size=1000)
            ragflow_dataset_map = {ds.id: ds for ds in ragflow_datasets}

            logger.info(f"开始同步数据集: 本地{sync_result.total_datasets}个, RAGFlow{len(ragflow_datasets)}个")

            for local_dataset in local_datasets:
                try:
                    local_id = str(local_dataset.get('id', ''))
                    ragflow_dataset_id = local_dataset.get('ragflow_dataset_id')

                    if ragflow_dataset_id and ragflow_dataset_id in ragflow_dataset_map:
                        # 更新现有数据集
                        ragflow_dataset = ragflow_dataset_map[ragflow_dataset_id]
                        self._update_local_dataset(local_dataset, ragflow_dataset)
                        sync_result.updated_count += 1
                        logger.debug(f"更新数据集: {local_dataset.get('name')}")

                    else:
                        # 创建新数据集或重新关联
                        if local_id in ragflow_dataset_map:
                            ragflow_dataset = ragflow_dataset_map[local_id]
                            self._update_local_dataset(local_dataset, ragflow_dataset)
                            sync_result.updated_count += 1
                            logger.debug(f"关联数据集: {local_dataset.get('name')}")
                        else:
                            # 按名称查找
                            matching_dataset = self._find_dataset_by_name(
                                local_dataset.get('name'), ragflow_datasets
                            )
                            if matching_dataset:
                                self._update_local_dataset(local_dataset, matching_dataset)
                                sync_result.updated_count += 1
                                logger.debug(f"按名称匹配数据集: {local_dataset.get('name')}")
                            else:
                                logger.warning(f"未找到匹配的数据集: {local_dataset.get('name')}")
                                sync_result.failed_count += 1

                except Exception as e:
                    error_info = {
                        'dataset_id': local_dataset.get('id'),
                        'dataset_name': local_dataset.get('name'),
                        'error': str(e)
                    }
                    sync_result.errors.append(error_info)
                    sync_result.failed_count += 1
                    logger.error(f"同步数据集失败 {local_dataset.get('name')}: {str(e)}")

            sync_result.duration = time.time() - start_time
            logger.info(f"数据集同步完成: 创建{sync_result.created_count}, "
                       f"更新{sync_result.updated_count}, 失败{sync_result.failed_count}, "
                       f"耗时{sync_result.duration:.2f}s")

        except Exception as e:
            sync_result.duration = time.time() - start_time
            error_info = {
                'error': str(e),
                'stage': 'sync_datasets'
            }
            sync_result.errors.append(error_info)
            logger.error(f"数据集同步失败: {str(e)}")

        return sync_result

    def refresh_dataset(self, dataset_id: str) -> DatasetRefreshResult:
        """刷新单个数据集"""
        start_time = time.time()

        try:
            # 从RAGFlow获取最新数据
            ragflow_dataset = self.get_dataset(dataset_id)

            if not ragflow_dataset:
                return DatasetRefreshResult(
                    dataset_id=dataset_id,
                    success=False,
                    error_message="数据集不存在",
                    duration=time.time() - start_time
                )

            # 这里应该更新本地数据库中的数据集信息
            # 由于这是服务层，我们返回更新后的信息
            result = DatasetRefreshResult(
                dataset_id=dataset_id,
                success=True,
                new_info=ragflow_dataset,
                duration=time.time() - start_time
            )

            logger.info(f"刷新数据集成功: {ragflow_dataset.name}")
            return result

        except Exception as e:
            result = DatasetRefreshResult(
                dataset_id=dataset_id,
                success=False,
                error_message=str(e),
                duration=time.time() - start_time
            )
            logger.error(f"刷新数据集失败 {dataset_id}: {str(e)}")
            return result

    def search_datasets(self, query: str, page: int = 1, page_size: int = 20) -> Tuple[List[DatasetInfo], int]:
        """搜索数据集"""
        try:
            params = {
                'q': query,
                'page': page,
                'page_size': page_size
            }

            response = self.retry_strategy.execute_with_retry(
                self.client.get,
                '/api/v1/datasets/search',
                params=params
            )

            datasets = []
            if response.get('data'):
                for dataset_data in response['data']:
                    if DatasetValidator.is_valid_dataset(dataset_data):
                        datasets.append(DatasetInfo.from_dict(dataset_data))

            total = response.get('total', 0)
            logger.info(f"搜索数据集成功: {len(datasets)}/{total} (查询: {query})")

            return datasets, total

        except Exception as e:
            logger.error(f"搜索数据集失败: {str(e)}")
            raise

    def _update_local_dataset(self, local_dataset: Dict[str, Any], ragflow_dataset: DatasetInfo) -> None:
        """更新本地数据集信息"""
        # 这里应该调用数据访问层来更新数据库
        # 由于这是服务层，我们提供更新逻辑
        update_data = {
            'ragflow_dataset_id': ragflow_dataset.id,
            'document_count': ragflow_dataset.document_count,
            'size': ragflow_dataset.size,
            'status': ragflow_dataset.status,
            'updated_at': ragflow_dataset.updated_at
        }

        logger.debug(f"更新本地数据集: {update_data}")
        # 实际的数据库更新应该在调用此服务的地方处理

    def _find_dataset_by_name(self, name: str, datasets: List[DatasetInfo]) -> Optional[DatasetInfo]:
        """按名称查找数据集"""
        for dataset in datasets:
            if dataset.name == name:
                return dataset
        return None

    def get_dataset_statistics(self, dataset_id: str) -> Dict[str, Any]:
        """获取数据集统计信息"""
        try:
            response = self.retry_strategy.execute_with_retry(
                self.client.get,
                f'/api/v1/datasets/{dataset_id}/statistics'
            )

            return response.get('data', {})

        except Exception as e:
            logger.error(f"获取数据集统计失败 {dataset_id}: {str(e)}")
            raise