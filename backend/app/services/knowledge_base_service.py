#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
知识库服务模块

提供知识库的业务逻辑层功能，包括：
- 知识库CRUD操作
- 数据集同步和状态管理
- 统计信息计算
- 缓存管理
- 数据验证和错误处理
- 与RAGFlow服务的集成

遵循MRC项目的现有模式，与其他服务保持一致的接口风格
"""

import logging
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
from flask import current_app
from sqlalchemy import or_, and_, desc, asc, func
from sqlalchemy.orm import joinedload

from app import db
from app.models import KnowledgeBase, RoleKnowledgeBase, Role
from app.services.ragflow_service import get_ragflow_service, DatasetInfo, RAGFlowAPIError
from app.services.cache_service import get_cache_service

logger = logging.getLogger(__name__)


class KnowledgeBaseValidationError(Exception):
    """知识库验证错误"""
    pass


class KnowledgeBaseNotFoundError(Exception):
    """知识库未找到错误"""
    pass


class KnowledgeBaseService:
    """
    知识库服务类

    提供完整的知识库管理功能，包括：
    - 基础CRUD操作
    - 数据集同步和状态管理
    - 统计信息和性能监控
    - 缓存优化和数据验证
    """

    def __init__(self):
        """初始化知识库服务"""
        self.cache_service = get_cache_service()
        self.ragflow_service = get_ragflow_service()
        self.logger = logging.getLogger(__name__)

    # ==================== 基础CRUD操作 ====================

    @staticmethod
    def create_knowledge_base(
        ragflow_dataset_id: str,
        name: str,
        description: Optional[str] = None,
        document_count: int = 0,
        total_size: int = 0,
        status: str = 'active'
    ) -> KnowledgeBase:
        """
        创建新的知识库

        Args:
            ragflow_dataset_id: RAGFlow数据集ID
            name: 知识库名称
            description: 知识库描述
            document_count: 文档数量
            total_size: 总大小（字节）
            status: 状态

        Returns:
            KnowledgeBase: 创建的知识库对象

        Raises:
            KnowledgeBaseValidationError: 验证失败
        """
        try:
            # 验证输入参数
            KnowledgeBaseService._validate_knowledge_base_data(
                ragflow_dataset_id=ragflow_dataset_id,
                name=name,
                status=status
            )

            # 检查RAGFlow数据集ID是否已存在
            existing_kb = KnowledgeBase.query.filter_by(
                ragflow_dataset_id=ragflow_dataset_id
            ).first()

            if existing_kb:
                raise KnowledgeBaseValidationError(
                    f"RAGFlow数据集ID '{ragflow_dataset_id}' 已被知识库 '{existing_kb.name}' 使用"
                )

            # 创建知识库
            knowledge_base = KnowledgeBase(
                ragflow_dataset_id=ragflow_dataset_id,
                name=name,
                description=description,
                document_count=document_count,
                total_size=total_size,
                status=status
            )

            db.session.add(knowledge_base)
            db.session.commit()

            current_app.logger.info(f"创建知识库成功: {name} (ID: {knowledge_base.id})")

            # 清除相关缓存
            KnowledgeBaseService._clear_knowledge_base_cache()

            return knowledge_base

        except KnowledgeBaseValidationError:
            raise
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"创建知识库失败: {str(e)}")
            raise Exception(f"创建知识库失败: {str(e)}")

    @staticmethod
    def get_knowledge_base_by_id(knowledge_base_id: int) -> Optional[KnowledgeBase]:
        """
        根据ID获取知识库

        Args:
            knowledge_base_id: 知识库ID

        Returns:
            Optional[KnowledgeBase]: 知识库对象或None
        """
        try:
            cache_key = f"knowledge_base:id:{knowledge_base_id}"
            cache_service = get_cache_service()

            # 尝试从缓存获取
            cached_kb = cache_service.get(cache_key)
            if cached_kb:
                return cached_kb

            # 从数据库查询
            knowledge_base = KnowledgeBase.query.get(knowledge_base_id)

            # 缓存结果
            if knowledge_base:
                cache_service.set(cache_key, knowledge_base, ttl=600)

            return knowledge_base

        except Exception as e:
            current_app.logger.error(f"获取知识库失败 (ID: {knowledge_base_id}): {str(e)}")
            return None

    @staticmethod
    def get_knowledge_base_by_ragflow_id(ragflow_dataset_id: str) -> Optional[KnowledgeBase]:
        """
        根据RAGFlow数据集ID获取知识库

        Args:
            ragflow_dataset_id: RAGFlow数据集ID

        Returns:
            Optional[KnowledgeBase]: 知识库对象或None
        """
        try:
            cache_key = f"knowledge_base:ragflow_id:{ragflow_dataset_id}"
            cache_service = get_cache_service()

            # 尝试从缓存获取
            cached_kb = cache_service.get(cache_key)
            if cached_kb:
                return cached_kb

            # 从数据库查询
            knowledge_base = KnowledgeBase.query.filter_by(
                ragflow_dataset_id=ragflow_dataset_id
            ).first()

            # 缓存结果
            if knowledge_base:
                cache_service.set(cache_key, knowledge_base, ttl=600)

            return knowledge_base

        except Exception as e:
            current_app.logger.error(f"获取知识库失败 (RAGFlow ID: {ragflow_dataset_id}): {str(e)}")
            return None

    @staticmethod
    def update_knowledge_base(
        knowledge_base_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None
    ) -> KnowledgeBase:
        """
        更新知识库信息

        Args:
            knowledge_base_id: 知识库ID
            name: 新名称
            description: 新描述
            status: 新状态

        Returns:
            KnowledgeBase: 更新后的知识库对象

        Raises:
            KnowledgeBaseNotFoundError: 知识库不存在
            KnowledgeBaseValidationError: 验证失败
        """
        try:
            knowledge_base = KnowledgeBase.query.get(knowledge_base_id)
            if not knowledge_base:
                raise KnowledgeBaseNotFoundError(f"知识库不存在 (ID: {knowledge_base_id})")

            # 更新字段
            if name is not None:
                if not name or not name.strip():
                    raise KnowledgeBaseValidationError("知识库名称不能为空")
                knowledge_base.name = name.strip()

            if description is not None:
                knowledge_base.description = description

            if status is not None:
                KnowledgeBaseService._validate_status(status)
                knowledge_base.status = status

            knowledge_base.updated_at = datetime.utcnow()
            db.session.commit()

            current_app.logger.info(f"更新知识库成功: {knowledge_base.name} (ID: {knowledge_base_id})")

            # 清除相关缓存
            KnowledgeBaseService._clear_knowledge_base_cache(knowledge_base_id)

            return knowledge_base

        except (KnowledgeBaseNotFoundError, KnowledgeBaseValidationError):
            raise
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"更新知识库失败 (ID: {knowledge_base_id}): {str(e)}")
            raise Exception(f"更新知识库失败: {str(e)}")

    @staticmethod
    def delete_knowledge_base(knowledge_base_id: int) -> bool:
        """
        删除知识库

        Args:
            knowledge_base_id: 知识库ID

        Returns:
            bool: 是否删除成功

        Raises:
            KnowledgeBaseNotFoundError: 知识库不存在
        """
        try:
            knowledge_base = KnowledgeBase.query.get(knowledge_base_id)
            if not knowledge_base:
                raise KnowledgeBaseNotFoundError(f"知识库不存在 (ID: {knowledge_base_id})")

            # 检查是否被角色使用
            role_count = RoleKnowledgeBase.query.filter_by(
                knowledge_base_id=knowledge_base_id
            ).count()

            if role_count > 0:
                raise KnowledgeBaseValidationError(
                    f"无法删除知识库 '{knowledge_base.name}'，它被 {role_count} 个角色使用"
                )

            kb_name = knowledge_base.name

            # 删除知识库
            db.session.delete(knowledge_base)
            db.session.commit()

            current_app.logger.info(f"删除知识库成功: {kb_name} (ID: {knowledge_base_id})")

            # 清除相关缓存
            KnowledgeBaseService._clear_knowledge_base_cache(knowledge_base_id)

            return True

        except (KnowledgeBaseNotFoundError, KnowledgeBaseValidationError):
            raise
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"删除知识库失败 (ID: {knowledge_base_id}): {str(e)}")
            raise Exception(f"删除知识库失败: {str(e)}")

    # ==================== 查询和搜索操作 ====================

    @staticmethod
    def get_knowledge_bases_list(
        page: int = 1,
        per_page: int = 20,
        status: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = 'created_at',
        sort_order: str = 'desc'
    ) -> Tuple[List[KnowledgeBase], int, Dict[str, Any]]:
        """
        获取知识库列表（分页）

        Args:
            page: 页码
            per_page: 每页数量
            status: 状态过滤
            search: 搜索关键词
            sort_by: 排序字段
            sort_order: 排序方向

        Returns:
            Tuple[List[KnowledgeBase], int, Dict]: 知识库列表、总数、分页信息
        """
        try:
            query = KnowledgeBase.query

            # 应用过滤条件
            if status:
                query = query.filter_by(status=status)

            if search:
                search_pattern = f"%{search}%"
                query = query.filter(
                    or_(
                        KnowledgeBase.name.ilike(search_pattern),
                        KnowledgeBase.description.ilike(search_pattern),
                        KnowledgeBase.ragflow_dataset_id.ilike(search_pattern)
                    )
                )

            # 应用排序
            if sort_by == 'name':
                order_column = KnowledgeBase.name
            elif sort_by == 'document_count':
                order_column = KnowledgeBase.document_count
            elif sort_by == 'total_size':
                order_column = KnowledgeBase.total_size
            elif sort_by == 'updated_at':
                order_column = KnowledgeBase.updated_at
            else:  # created_at (default)
                order_column = KnowledgeBase.created_at

            if sort_order.lower() == 'asc':
                query = query.order_by(asc(order_column))
            else:
                query = query.order_by(desc(order_column))

            # 分页查询
            pagination = query.paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )

            knowledge_bases = pagination.items
            total = pagination.total

            pagination_info = {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': pagination.pages,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next,
                'prev_num': pagination.prev_num,
                'next_num': pagination.next_num
            }

            return knowledge_bases, total, pagination_info

        except Exception as e:
            current_app.logger.error(f"获取知识库列表失败: {str(e)}")
            return [], 0, {}

    @staticmethod
    def get_all_knowledge_bases(status: Optional[str] = None) -> List[KnowledgeBase]:
        """
        获取所有知识库

        Args:
            status: 状态过滤

        Returns:
            List[KnowledgeBase]: 知识库列表
        """
        try:
            query = KnowledgeBase.query

            if status:
                query = query.filter_by(status=status)

            return query.order_by(KnowledgeBase.name).all()

        except Exception as e:
            current_app.logger.error(f"获取所有知识库失败: {str(e)}")
            return []

    @staticmethod
    def get_knowledge_bases_count(status: Optional[str] = None) -> int:
        """
        获取知识库总数

        Args:
            status: 状态过滤

        Returns:
            int: 知识库总数
        """
        try:
            query = KnowledgeBase.query

            if status:
                query = query.filter_by(status=status)

            return query.count()

        except Exception as e:
            current_app.logger.error(f"获取知识库总数失败: {str(e)}")
            return 0

    # ==================== 数据集同步操作 ====================

    @staticmethod
    def sync_datasets_from_ragflow() -> Dict[str, Any]:
        """
        从RAGFlow同步数据集信息

        Returns:
            Dict[str, Any]: 同步结果统计
        """
        try:
            ragflow_service = get_ragflow_service()
            if not ragflow_service:
                raise Exception("RAGFlow服务不可用")

            # 获取RAGFlow数据集列表
            datasets = ragflow_service.get_datasets()

            sync_result = {
                'total_datasets': len(datasets),
                'created': 0,
                'updated': 0,
                'errors': [],
                'details': []
            }

            for dataset in datasets:
                try:
                    # 查找本地对应的知识库
                    local_kb = KnowledgeBaseService.get_knowledge_base_by_ragflow_id(
                        dataset.id
                    )

                    if local_kb:
                        # 更新现有知识库
                        local_kb.name = dataset.name
                        local_kb.description = dataset.description
                        local_kb.document_count = dataset.document_count
                        local_kb.total_size = dataset.size
                        local_kb.updated_at = datetime.utcnow()

                        sync_result['updated'] += 1
                        sync_result['details'].append({
                            'action': 'updated',
                            'dataset_id': dataset.id,
                            'name': dataset.name,
                            'document_count': dataset.document_count
                        })

                        current_app.logger.info(f"更新知识库: {dataset.name}")
                    else:
                        # 创建新知识库
                        KnowledgeBaseService.create_knowledge_base(
                            ragflow_dataset_id=dataset.id,
                            name=dataset.name,
                            description=dataset.description,
                            document_count=dataset.document_count,
                            total_size=dataset.size
                        )

                        sync_result['created'] += 1
                        sync_result['details'].append({
                            'action': 'created',
                            'dataset_id': dataset.id,
                            'name': dataset.name,
                            'document_count': dataset.document_count
                        })

                        current_app.logger.info(f"创建知识库: {dataset.name}")

                except Exception as e:
                    error_msg = f"处理数据集 '{dataset.name}' 失败: {str(e)}"
                    sync_result['errors'].append(error_msg)
                    current_app.logger.error(error_msg)

            # 提交所有更改
            db.session.commit()

            # 清除缓存
            KnowledgeBaseService._clear_knowledge_base_cache()

            current_app.logger.info(
                f"RAGFlow数据集同步完成: 创建 {sync_result['created']} 个，"
                f"更新 {sync_result['updated']} 个，错误 {len(sync_result['errors'])} 个"
            )

            return sync_result

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"RAGFlow数据集同步失败: {str(e)}")
            raise Exception(f"数据集同步失败: {str(e)}")

    @staticmethod
    def refresh_dataset_from_ragflow(knowledge_base_id: int) -> Dict[str, Any]:
        """
        从RAGFlow刷新特定数据集信息

        Args:
            knowledge_base_id: 知识库ID

        Returns:
            Dict[str, Any]: 刷新结果
        """
        try:
            knowledge_base = KnowledgeBase.query.get(knowledge_base_id)
            if not knowledge_base:
                raise KnowledgeBaseNotFoundError(f"知识库不存在 (ID: {knowledge_base_id})")

            ragflow_service = get_ragflow_service()
            if not ragflow_service:
                raise Exception("RAGFlow服务不可用")

            # 获取RAGFlow数据集信息
            dataset = ragflow_service.get_dataset(knowledge_base.ragflow_dataset_id)
            if not dataset:
                raise Exception(f"RAGFlow数据集不存在: {knowledge_base.ragflow_dataset_id}")

            # 更新本地知识库信息
            old_info = {
                'name': knowledge_base.name,
                'document_count': knowledge_base.document_count,
                'total_size': knowledge_base.total_size
            }

            knowledge_base.name = dataset.name
            knowledge_base.description = dataset.description
            knowledge_base.document_count = dataset.document_count
            knowledge_base.total_size = dataset.size
            knowledge_base.updated_at = datetime.utcnow()

            db.session.commit()

            # 清除缓存
            KnowledgeBaseService._clear_knowledge_base_cache(knowledge_base_id)

            result = {
                'knowledge_base_id': knowledge_base_id,
                'dataset_id': dataset.id,
                'old_info': old_info,
                'new_info': {
                    'name': dataset.name,
                    'document_count': dataset.document_count,
                    'total_size': dataset.size
                }
            }

            current_app.logger.info(f"刷新知识库成功: {dataset.name}")

            return result

        except (KnowledgeBaseNotFoundError, Exception):
            db.session.rollback()
            raise

    # ==================== 角色关联操作 ====================

    @staticmethod
    def assign_knowledge_base_to_role(
        role_id: int,
        knowledge_base_id: int,
        priority: int = 1,
        retrieval_config: Optional[Dict[str, Any]] = None,
        is_active: bool = True
    ) -> RoleKnowledgeBase:
        """
        将知识库分配给角色

        Args:
            role_id: 角色ID
            knowledge_base_id: 知识库ID
            priority: 优先级
            retrieval_config: 检索配置
            is_active: 是否启用

        Returns:
            RoleKnowledgeBase: 角色知识库关联对象
        """
        try:
            # 验证角色和知识库存在
            role = Role.query.get(role_id)
            if not role:
                raise KnowledgeBaseValidationError(f"角色不存在 (ID: {role_id})")

            knowledge_base = KnowledgeBase.query.get(knowledge_base_id)
            if not knowledge_base:
                raise KnowledgeBaseValidationError(f"知识库不存在 (ID: {knowledge_base_id})")

            # 检查是否已存在关联
            existing_association = RoleKnowledgeBase.query.filter_by(
                role_id=role_id,
                knowledge_base_id=knowledge_base_id
            ).first()

            if existing_association:
                raise KnowledgeBaseValidationError(
                    f"角色 '{role.name}' 已关联知识库 '{knowledge_base.name}'"
                )

            # 创建关联
            role_kb = RoleKnowledgeBase(
                role_id=role_id,
                knowledge_base_id=knowledge_base_id,
                priority=priority,
                retrieval_config_dict=retrieval_config or {},
                is_active=is_active
            )

            db.session.add(role_kb)
            db.session.commit()

            current_app.logger.info(
                f"知识库分配成功: 角色 '{role.name}' -> 知识库 '{knowledge_base.name}'"
            )

            return role_kb

        except KnowledgeBaseValidationError:
            raise
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"分配知识库失败: {str(e)}")
            raise Exception(f"分配知识库失败: {str(e)}")

    @staticmethod
    def unassign_knowledge_base_from_role(role_id: int, knowledge_base_id: int) -> bool:
        """
        取消角色与知识库的关联

        Args:
            role_id: 角色ID
            knowledge_base_id: 知识库ID

        Returns:
            bool: 是否取消成功
        """
        try:
            role_kb = RoleKnowledgeBase.query.filter_by(
                role_id=role_id,
                knowledge_base_id=knowledge_base_id
            ).first()

            if not role_kb:
                raise KnowledgeBaseNotFoundError(
                    f"角色知识库关联不存在 (角色ID: {role_id}, 知识库ID: {knowledge_base_id})"
                )

            role_name = role_kb.role.name if role_kb.role else "Unknown"
            kb_name = role_kb.knowledge_base.name if role_kb.knowledge_base else "Unknown"

            db.session.delete(role_kb)
            db.session.commit()

            current_app.logger.info(f"取消知识库关联: 角色 '{role_name}' -> 知识库 '{kb_name}'")

            return True

        except KnowledgeBaseNotFoundError:
            raise
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"取消知识库关联失败: {str(e)}")
            raise Exception(f"取消知识库关联失败: {str(e)}")

    @staticmethod
    def get_role_knowledge_bases(role_id: int, active_only: bool = True) -> List[Dict[str, Any]]:
        """
        获取角色的知识库列表

        Args:
            role_id: 角色ID
            active_only: 是否只返回启用的关联

        Returns:
            List[Dict[str, Any]]: 角色知识库关联列表
        """
        try:
            query = RoleKnowledgeBase.query.filter_by(role_id=role_id)

            if active_only:
                query = query.filter_by(is_active=True)

            # 按优先级排序
            role_kbs = query.order_by(RoleKnowledgeBase.priority).all()

            return [role_kb.to_dict() for role_kb in role_kbs]

        except Exception as e:
            current_app.logger.error(f"获取角色知识库失败 (角色ID: {role_id}): {str(e)}")
            return []

    @staticmethod
    def get_knowledge_base_roles(knowledge_base_id: int) -> List[Dict[str, Any]]:
        """
        获取使用知识库的角色列表

        Args:
            knowledge_base_id: 知识库ID

        Returns:
            List[Dict[str, Any]]: 角色列表
        """
        try:
            role_kbs = RoleKnowledgeBase.query.filter_by(
                knowledge_base_id=knowledge_base_id,
                is_active=True
            ).options(joinedload(RoleKnowledgeBase.role)).all()

            return [
                {
                    'id': role_kb.role.id,
                    'name': role_kb.role.name,
                    'type': role_kb.role.type,
                    'priority': role_kb.priority,
                    'retrieval_config': role_kb.retrieval_config_dict,
                    'created_at': role_kb.created_at.isoformat() if role_kb.created_at else None
                }
                for role_kb in role_kbs
            ]

        except Exception as e:
            current_app.logger.error(f"获取知识库角色失败 (知识库ID: {knowledge_base_id}): {str(e)}")
            return []

    # ==================== 统计和监控操作 ====================

    @staticmethod
    def get_knowledge_base_statistics() -> Dict[str, Any]:
        """
        获取知识库统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            cache_key = "knowledge_base:statistics"
            cache_service = get_cache_service()

            # 尝试从缓存获取
            cached_stats = cache_service.get(cache_key)
            if cached_stats:
                return cached_stats

            # 计算统计信息
            total_kb = KnowledgeBase.query.count()
            active_kb = KnowledgeBase.query.filter_by(status='active').count()
            inactive_kb = KnowledgeBase.query.filter_by(status='inactive').count()
            error_kb = KnowledgeBase.query.filter_by(status='error').count()

            # 文档统计
            doc_stats = db.session.query(
                func.sum(KnowledgeBase.document_count).label('total_documents'),
                func.sum(KnowledgeBase.total_size).label('total_size')
            ).first()

            # 关联统计
            role_associations = RoleKnowledgeBase.query.count()
            active_associations = RoleKnowledgeBase.query.filter_by(is_active=True).count()

            statistics = {
                'knowledge_bases': {
                    'total': total_kb,
                    'active': active_kb,
                    'inactive': inactive_kb,
                    'error': error_kb
                },
                'documents': {
                    'total': doc_stats.total_documents or 0,
                    'total_size': doc_stats.total_size or 0,
                    'total_size_human': KnowledgeBaseService._format_size(
                        doc_stats.total_size or 0
                    )
                },
                'associations': {
                    'total': role_associations,
                    'active': active_associations
                },
                'last_updated': datetime.utcnow().isoformat()
            }

            # 缓存统计信息（5分钟）
            cache_service.set(cache_key, statistics, ttl=300)

            return statistics

        except Exception as e:
            current_app.logger.error(f"获取知识库统计失败: {str(e)}")
            return {
                'knowledge_bases': {'total': 0, 'active': 0, 'inactive': 0, 'error': 0},
                'documents': {'total': 0, 'total_size': 0, 'total_size_human': '0 B'},
                'associations': {'total': 0, 'active': 0},
                'last_updated': datetime.utcnow().isoformat(),
                'error': str(e)
            }

    @staticmethod
    def get_knowledge_base_usage_report(days: int = 30) -> Dict[str, Any]:
        """
        获取知识库使用报告

        Args:
            days: 统计天数

        Returns:
            Dict[str, Any]: 使用报告
        """
        try:
            # 时间范围
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

            # 最近创建的知识库
            recent_kbs = KnowledgeBase.query.filter(
                KnowledgeBase.created_at >= start_date
            ).count()

            # 最近更新的知识库
            updated_kbs = KnowledgeBase.query.filter(
                KnowledgeBase.updated_at >= start_date
            ).count()

            # 最近关联的角色知识库
            recent_associations = RoleKnowledgeBase.query.filter(
                RoleKnowledgeBase.created_at >= start_date
            ).count()

            # 按状态分组统计
            status_stats = db.session.query(
                KnowledgeBase.status,
                func.count(KnowledgeBase.id).label('count')
            ).group_by(KnowledgeBase.status).all()

            # 按文档数量分组统计
            doc_ranges = [
                (0, 10, '0-10'),
                (11, 50, '11-50'),
                (51, 100, '51-100'),
                (101, 500, '101-500'),
                (501, float('inf'), '500+')
            ]

            doc_distribution = []
            for min_doc, max_doc, label in doc_ranges:
                count = KnowledgeBase.query.filter(
                    KnowledgeBase.document_count >= min_doc,
                    KnowledgeBase.document_count <= max_doc
                ).count()

                doc_distribution.append({
                    'range': label,
                    'count': count
                })

            report = {
                'period': {
                    'days': days,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'creation': {
                    'recent_knowledge_bases': recent_kbs,
                    'updated_knowledge_bases': updated_kbs,
                    'recent_associations': recent_associations
                },
                'status_distribution': [
                    {'status': status, 'count': count}
                    for status, count in status_stats
                ],
                'document_distribution': doc_distribution,
                'generated_at': datetime.utcnow().isoformat()
            }

            return report

        except Exception as e:
            current_app.logger.error(f"获取知识库使用报告失败: {str(e)}")
            return {
                'period': {'days': days},
                'error': str(e),
                'generated_at': datetime.utcnow().isoformat()
            }

    # ==================== 状态管理操作 ====================

    @staticmethod
    def update_knowledge_base_status(
        knowledge_base_id: int,
        status: str
    ) -> KnowledgeBase:
        """
        更新知识库状态

        Args:
            knowledge_base_id: 知识库ID
            status: 新状态

        Returns:
            KnowledgeBase: 更新后的知识库对象
        """
        return KnowledgeBaseService.update_knowledge_base(
            knowledge_base_id=knowledge_base_id,
            status=status
        )

    @staticmethod
    def activate_knowledge_base(knowledge_base_id: int) -> KnowledgeBase:
        """
        激活知识库

        Args:
            knowledge_base_id: 知识库ID

        Returns:
            KnowledgeBase: 激活后的知识库对象
        """
        return KnowledgeBaseService.update_knowledge_base_status(
            knowledge_base_id=knowledge_base_id,
            status='active'
        )

    @staticmethod
    def deactivate_knowledge_base(knowledge_base_id: int) -> KnowledgeBase:
        """
        停用知识库

        Args:
            knowledge_base_id: 知识库ID

        Returns:
            KnowledgeBase: 停用后的知识库对象
        """
        return KnowledgeBaseService.update_knowledge_base_status(
            knowledge_base_id=knowledge_base_id,
            status='inactive'
        )

    # ==================== 批量操作 ====================

    @staticmethod
    def bulk_update_status(
        knowledge_base_ids: List[int],
        status: str
    ) -> Dict[str, Any]:
        """
        批量更新知识库状态

        Args:
            knowledge_base_ids: 知识库ID列表
            status: 新状态

        Returns:
            Dict[str, Any]: 批量操作结果
        """
        try:
            KnowledgeBaseService._validate_status(status)

            updated_count = KnowledgeBase.query.filter(
                KnowledgeBase.id.in_(knowledge_base_ids)
            ).update(
                {
                    'status': status,
                    'updated_at': datetime.utcnow()
                },
                synchronize_session=False
            )

            db.session.commit()

            # 清除缓存
            for kb_id in knowledge_base_ids:
                KnowledgeBaseService._clear_knowledge_base_cache(kb_id)

            current_app.logger.info(f"批量更新知识库状态完成: 更新 {updated_count} 个知识库")

            return {
                'updated_count': updated_count,
                'requested_count': len(knowledge_base_ids),
                'status': status
            }

        except KnowledgeBaseValidationError:
            raise
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"批量更新知识库状态失败: {str(e)}")
            raise Exception(f"批量更新状态失败: {str(e)}")

    @staticmethod
    def bulk_delete_knowledge_bases(
        knowledge_base_ids: List[int],
        force: bool = False
    ) -> Dict[str, Any]:
        """
        批量删除知识库

        Args:
            knowledge_base_ids: 知识库ID列表
            force: 是否强制删除（忽略角色关联）

        Returns:
            Dict[str, Any]: 批量操作结果
        """
        try:
            deleted_count = 0
            skipped_count = 0
            errors = []

            for kb_id in knowledge_base_ids:
                try:
                    kb = KnowledgeBase.query.get(kb_id)
                    if not kb:
                        skipped_count += 1
                        continue

                    # 检查角色关联（除非强制删除）
                    if not force:
                        role_count = RoleKnowledgeBase.query.filter_by(
                            knowledge_base_id=kb_id
                        ).count()

                        if role_count > 0:
                            errors.append(f"知识库 '{kb.name}' 被 {role_count} 个角色使用")
                            skipped_count += 1
                            continue

                    # 删除知识库
                    db.session.delete(kb)
                    deleted_count += 1

                    # 清除缓存
                    KnowledgeBaseService._clear_knowledge_base_cache(kb_id)

                except Exception as e:
                    errors.append(f"删除知识库 ID {kb_id} 失败: {str(e)}")
                    skipped_count += 1

            db.session.commit()

            current_app.logger.info(
                f"批量删除知识库完成: 成功删除 {deleted_count} 个，跳过 {skipped_count} 个"
            )

            return {
                'deleted_count': deleted_count,
                'skipped_count': skipped_count,
                'requested_count': len(knowledge_base_ids),
                'errors': errors
            }

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"批量删除知识库失败: {str(e)}")
            raise Exception(f"批量删除失败: {str(e)}")

    # ==================== 验证和工具方法 ====================

    @staticmethod
    def _validate_knowledge_base_data(
        ragflow_dataset_id: str,
        name: str,
        status: str = 'active'
    ) -> None:
        """
        验证知识库数据

        Args:
            ragflow_dataset_id: RAGFlow数据集ID
            name: 知识库名称
            status: 状态

        Raises:
            KnowledgeBaseValidationError: 验证失败
        """
        if not ragflow_dataset_id or not ragflow_dataset_id.strip():
            raise KnowledgeBaseValidationError("RAGFlow数据集ID不能为空")

        if not name or not name.strip():
            raise KnowledgeBaseValidationError("知识库名称不能为空")

        if len(name) > 200:
            raise KnowledgeBaseValidationError("知识库名称长度不能超过200个字符")

        KnowledgeBaseService._validate_status(status)

    @staticmethod
    def _validate_status(status: str) -> None:
        """
        验证状态值

        Args:
            status: 状态值

        Raises:
            KnowledgeBaseValidationError: 状态无效
        """
        valid_statuses = ['active', 'inactive', 'error']
        if status not in valid_statuses:
            raise KnowledgeBaseValidationError(f"无效的状态值: {status}，有效值: {valid_statuses}")

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """
        格式化文件大小

        Args:
            size_bytes: 字节数

        Returns:
            str: 格式化的大小字符串
        """
        if size_bytes == 0:
            return "0 B"

        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        size = float(size_bytes)

        while size >= 1024.0 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1

        return f"{size:.1f} {size_names[i]}"

    @staticmethod
    def _clear_knowledge_base_cache(knowledge_base_id: Optional[int] = None) -> None:
        """
        清除知识库相关缓存

        Args:
            knowledge_base_id: 特定知识库ID，如果为None则清除所有知识库缓存
        """
        try:
            cache_service = get_cache_service()

            if knowledge_base_id:
                # 清除特定知识库缓存
                patterns = [
                    f"knowledge_base:id:{knowledge_base_id}",
                    f"knowledge_base:ragflow_id:*",
                ]

                for pattern in patterns:
                    cache_service.clear(pattern)
            else:
                # 清除所有知识库缓存
                cache_service.clear("knowledge_base:*")
                cache_service.clear("knowledge_base:statistics")

        except Exception as e:
            current_app.logger.warning(f"清除知识库缓存失败: {str(e)}")


# 全局服务实例
_knowledge_base_service: Optional[KnowledgeBaseService] = None


def get_knowledge_base_service() -> KnowledgeBaseService:
    """
    获取知识库服务实例（单例模式）

    Returns:
        KnowledgeBaseService: 知识库服务实例
    """
    global _knowledge_base_service
    if _knowledge_base_service is None:
        _knowledge_base_service = KnowledgeBaseService()
    return _knowledge_base_service


if __name__ == "__main__":
    # 直接运行此文件时执行测试
    print("正在测试知识库服务...")

    try:
        service = get_knowledge_base_service()
        print("✅ 知识库服务创建成功")

        # 测试统计信息
        stats = service.get_knowledge_base_statistics()
        print(f"✅ 获取统计信息成功: {stats['knowledge_bases']['total']} 个知识库")

        # 测试获取知识库列表
        kbs, total, pagination = service.get_knowledge_bases_list(page=1, per_page=10)
        print(f"✅ 获取知识库列表成功: 共 {total} 个")

        # 测试使用报告
        report = service.get_knowledge_base_usage_report(days=7)
        print(f"✅ 获取使用报告成功: {report['period']['days']} 天统计")

    except Exception as e:
        print(f"❌ 知识库服务测试失败: {e}")