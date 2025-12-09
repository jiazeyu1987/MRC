#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
对话服务模块

提供对话历史记录的业务逻辑层功能，包括：
- 对话CRUD操作
- 对话搜索、过滤和分页
- 对话模板管理
- 对话导出功能
- 与知识库的集成

遵循MRC项目的现有模式，与其他服务保持一致的接口风格
"""

import logging
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
from flask import current_app
from sqlalchemy import or_, and_, desc, asc, func
from sqlalchemy.orm import joinedload

from app import db
from app.models import KnowledgeBase, ConversationHistory, ConversationTemplate
from app.services.knowledge_base_service import get_knowledge_base_service
from app.services.cache_service import get_cache_service

logger = logging.getLogger(__name__)


class ConversationValidationError(Exception):
    """对话验证错误"""
    pass


class ConversationNotFoundError(Exception):
    """对话未找到错误"""
    pass


class TemplateNotFoundError(Exception):
    """模板未找到错误"""
    pass


class ConversationServiceError(Exception):
    """对话服务错误基类"""
    pass


class ConversationNotFoundError(ConversationServiceError):
    """对话未找到错误"""
    pass


class ConversationStorageError(ConversationServiceError):
    """对话存储错误"""
    pass


class TemplateNotFoundError(ConversationServiceError):
    """模板未找到错误"""
    pass


class ConversationService:
    """
    对话服务类

    提供完整的对话管理功能，包括：
    - 对话历史记录的CRUD操作
    - 对话搜索和过滤功能
    - 对话模板管理
    - 导出和归档功能
    - 统计和分析
    """

    def __init__(self):
        self.knowledge_base_service = get_knowledge_base_service()
        self.cache_service = get_cache_service()

    # 对话CRUD操作
    def create_conversation(self, knowledge_base_id: int, title: str = "新对话",
                          messages: List[Dict] = None, tags: List[str] = None,
                          template_id: str = None, user_id: str = None) -> ConversationHistory:
        """
        创建新的对话记录

        Args:
            knowledge_base_id: 知识库ID
            title: 对话标题
            messages: 初始消息列表
            tags: 对话标签
            template_id: 使用的模板ID
            user_id: 用户ID

        Returns:
            ConversationHistory: 创建的对话记录

        Raises:
            ConversationNotFoundError: 知识库不存在
            ConversationStorageError: 存储失败
        """
        try:
            # 验证知识库存在
            knowledge_base = self.knowledge_base_service.get_knowledge_base(knowledge_base_id)

            conversation = ConversationHistory(
                knowledge_base_id=knowledge_base_id,
                user_id=user_id,
                title=title,
                messages=messages or [],
                tags=tags or [],
                template_id=template_id,
                metadata={
                    'created_by': user_id,
                    'template_applied': template_id is not None
                }
            )

            db.session.add(conversation)

            # 更新知识库对话计数
            knowledge_base.increment_conversation_count()

            db.session.commit()

            # 清除相关缓存
            self._clear_conversation_cache(knowledge_base_id)

            logger.info(f"Created conversation {conversation.id} for knowledge base {knowledge_base_id}")
            return conversation

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create conversation: {e}")
            raise ConversationStorageError(f"Failed to create conversation: {e}")

    def get_conversation(self, knowledge_base_id: int, conversation_id: int) -> ConversationHistory:
        """
        获取指定的对话记录

        Args:
            knowledge_base_id: 知识库ID
            conversation_id: 对话ID

        Returns:
            ConversationHistory: 对话记录

        Raises:
            ConversationNotFoundError: 对话不存在
        """
        try:
            # 检查缓存
            cache_key = f"conversation:{knowledge_base_id}:{conversation_id}"
            cached = self.cache_service.get(cache_key)
            if cached:
                return cached

            conversation = ConversationHistory.query.filter(
                and_(
                    ConversationHistory.knowledge_base_id == knowledge_base_id,
                    ConversationHistory.id == conversation_id
                )
            ).first()

            if not conversation:
                raise ConversationNotFoundError(f"Conversation {conversation_id} not found")

            # 缓存结果
            self.cache_service.set(cache_key, conversation, timeout=300)  # 5分钟缓存

            return conversation

        except Exception as e:
            logger.error(f"Failed to get conversation {conversation_id}: {e}")
            raise

    def get_conversations(self, knowledge_base_id: int, page: int = 1, per_page: int = 20,
                         search: str = "", tags: List[str] = None,
                         user_id: str = None, is_archived: bool = False) -> Tuple[List[ConversationHistory], int]:
        """
        获取对话列表，支持分页、搜索和过滤

        Args:
            knowledge_base_id: 知识库ID
            page: 页码
            per_page: 每页记录数
            search: 搜索关键词
            tags: 标签过滤
            user_id: 用户ID过滤
            is_archived: 是否归档

        Returns:
            Tuple[List[ConversationHistory], int]: 对话列表和总数
        """
        try:
            query = ConversationHistory.query.filter(
                ConversationHistory.knowledge_base_id == knowledge_base_id
            )

            # 应用过滤条件
            if search:
                query = query.filter(
                    or_(
                        ConversationHistory.title.contains(search),
                        ConversationHistory.tags.contains([search])
                    )
                )

            if tags:
                for tag in tags:
                    query = query.filter(ConversationHistory.tags.contains([tag]))

            if user_id:
                query = query.filter(ConversationHistory.user_id == user_id)

            query = query.filter(ConversationHistory.is_archived == is_archived)

            # 排序和分页
            query = query.order_by(desc(ConversationHistory.updated_at))

            total = query.count()
            conversations = query.offset((page - 1) * per_page).limit(per_page).all()

            return conversations, total

        except Exception as e:
            logger.error(f"Failed to get conversations: {e}")
            return [], 0

    def update_conversation(self, knowledge_base_id: int, conversation_id: int,
                          title: str = None, messages: List[Dict] = None,
                          tags: List[str] = None, template_id: str = None) -> ConversationHistory:
        """
        更新对话记录

        Args:
            knowledge_base_id: 知识库ID
            conversation_id: 对话ID
            title: 新标题
            messages: 新消息列表
            tags: 新标签
            template_id: 新模板ID

        Returns:
            ConversationHistory: 更新后的对话记录

        Raises:
            ConversationNotFoundError: 对话不存在
            ConversationStorageError: 更新失败
        """
        try:
            conversation = self.get_conversation(knowledge_base_id, conversation_id)

            if title is not None:
                conversation.title = title
            if messages is not None:
                conversation.messages = messages
                conversation.conversation_metadata['message_count'] = len(messages)
            if tags is not None:
                conversation.tags = tags
            if template_id is not None:
                conversation.template_id = template_id

            conversation.updated_at = datetime.utcnow()

            # 更新知识库活动时间
            knowledge_base = conversation.knowledge_base
            knowledge_base.update_activity()

            db.session.commit()

            # 清除相关缓存
            self._clear_conversation_cache(knowledge_base_id, conversation_id)

            logger.info(f"Updated conversation {conversation_id}")
            return conversation

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to update conversation {conversation_id}: {e}")
            raise ConversationStorageError(f"Failed to update conversation: {e}")

    def delete_conversation(self, knowledge_base_id: int, conversation_id: int) -> bool:
        """
        删除对话记录

        Args:
            knowledge_base_id: 知识库ID
            conversation_id: 对话ID

        Returns:
            bool: 是否删除成功

        Raises:
            ConversationNotFoundError: 对话不存在
            ConversationStorageError: 删除失败
        """
        try:
            conversation = self.get_conversation(knowledge_base_id, conversation_id)

            db.session.delete(conversation)
            db.session.commit()

            # 清除相关缓存
            self._clear_conversation_cache(knowledge_base_id, conversation_id)

            logger.info(f"Deleted conversation {conversation_id}")
            return True

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to delete conversation {conversation_id}: {e}")
            raise ConversationStorageError(f"Failed to delete conversation: {e}")

    # 对话模板管理
    def get_templates(self, category: str = None, is_system: bool = None) -> List[ConversationTemplate]:
        """
        获取对话模板列表

        Args:
            category: 模板类别过滤
            is_system: 是否系统模板过滤

        Returns:
            List[ConversationTemplate]: 模板列表
        """
        try:
            query = ConversationTemplate.query

            if category:
                query = query.filter(ConversationTemplate.category == category)
            if is_system is not None:
                query = query.filter(ConversationTemplate.is_system == is_system)

            templates = query.order_by(ConversationTemplate.usage_count.desc()).all()

            return templates

        except Exception as e:
            logger.error(f"Failed to get templates: {e}")
            return []

    def get_template(self, template_id: int) -> ConversationTemplate:
        """
        获取指定的对话模板

        Args:
            template_id: 模板ID

        Returns:
            ConversationTemplate: 模板记录

        Raises:
            TemplateNotFoundError: 模板不存在
        """
        try:
            template = ConversationTemplate.query.get(template_id)
            if not template:
                raise TemplateNotFoundError(f"Template {template_id} not found")
            return template

        except Exception as e:
            logger.error(f"Failed to get template {template_id}: {e}")
            raise

    def create_template(self, name: str, category: str, prompt: str,
                        description: str = "", parameters: List[Dict] = None,
                        is_system: bool = False) -> ConversationTemplate:
        """
        创建新的对话模板

        Args:
            name: 模板名称
            category: 模板类别
            prompt: 模板提示词
            description: 模板描述
            parameters: 模板参数
            is_system: 是否系统模板

        Returns:
            ConversationTemplate: 创建的模板记录

        Raises:
            ConversationStorageError: 创建失败
        """
        try:
            template = ConversationTemplate(
                name=name,
                category=category,
                prompt=prompt,
                description=description,
                parameters=parameters or [],
                is_system=is_system
            )

            db.session.add(template)
            db.session.commit()

            logger.info(f"Created conversation template {template.id}")
            return template

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create template: {e}")
            raise ConversationStorageError(f"Failed to create template: {e}")

    def apply_template(self, template_id: int, knowledge_base_id: int,
                      title: str = None, parameters: Dict = None,
                      user_id: str = None) -> ConversationHistory:
        """
        应用对话模板创建新对话

        Args:
            template_id: 模板ID
            knowledge_base_id: 知识库ID
            title: 对话标题
            parameters: 模板参数
            user_id: 用户ID

        Returns:
            ConversationHistory: 创建的对话记录
        """
        try:
            template = self.get_template(template_id)

            # 处理模板参数替换
            prompt = template.prompt
            if parameters:
                for key, value in parameters.items():
                    prompt = prompt.replace(f"{{{key}}}", str(value))

            # 创建初始消息
            messages = [
                {
                    "role": "system",
                    "content": prompt,
                    "timestamp": datetime.utcnow().isoformat()
                }
            ]

            # 增加模板使用次数
            template.increment_usage()

            # 创建对话
            conversation = self.create_conversation(
                knowledge_base_id=knowledge_base_id,
                title=title or f"基于模板: {template.name}",
                messages=messages,
                template_id=str(template_id),
                user_id=user_id
            )

            return conversation

        except Exception as e:
            logger.error(f"Failed to apply template {template_id}: {e}")
            raise ConversationServiceError(f"Failed to apply template: {e}")

    # 对话统计和分析
    def get_conversation_statistics(self, knowledge_base_id: int,
                                   days: int = 30) -> Dict[str, Any]:
        """
        获取对话统计信息

        Args:
            knowledge_base_id: 知识库ID
            days: 统计天数

        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            # 基础统计
            total_conversations = ConversationHistory.query.filter(
                and_(
                    ConversationHistory.knowledge_base_id == knowledge_base_id,
                    ConversationHistory.created_at >= start_date
                )
            ).count()

            # 按日期统计
            daily_stats = db.session.query(
                func.date(ConversationHistory.created_at).label('date'),
                func.count(ConversationHistory.id).label('count')
            ).filter(
                and_(
                    ConversationHistory.knowledge_base_id == knowledge_base_id,
                    ConversationHistory.created_at >= start_date
                )
            ).group_by(func.date(ConversationHistory.created_at))\
             .order_by(func.date(ConversationHistory.created_at)).all()

            # 模板使用统计
            template_stats = db.session.query(
                ConversationTemplate.name,
                func.count(ConversationHistory.id).label('usage_count')
            ).join(
                ConversationHistory,
                ConversationHistory.template_id == ConversationTemplate.id.cast(db.String)
            ).filter(
                and_(
                    ConversationHistory.knowledge_base_id == knowledge_base_id,
                    ConversationHistory.created_at >= start_date
                )
            ).group_by(ConversationTemplate.name)\
             .order_by(func.count(ConversationHistory.id).desc()).all()

            return {
                'total_conversations': total_conversations,
                'period_days': days,
                'daily_stats': [
                    {'date': str(stat.date), 'count': stat.count} for stat in daily_stats
                ],
                'template_usage': [
                    {'template': stat.name, 'count': stat.usage_count} for stat in template_stats
                ],
                'average_per_day': total_conversations / max(days, 1)
            }

        except Exception as e:
            logger.error(f"Failed to get conversation statistics: {e}")
            return {
                'total_conversations': 0,
                'period_days': days,
                'daily_stats': [],
                'template_usage': [],
                'average_per_day': 0
            }

    # 辅助方法
    def _clear_conversation_cache(self, knowledge_base_id: int, conversation_id: int = None):
        """清除对话相关缓存"""
        try:
            # 清除对话列表缓存
            list_cache_key = f"conversations:{knowledge_base_id}:list"
            self.cache_service.delete(list_cache_key)

            # 清除特定对话缓存
            if conversation_id:
                conversation_cache_key = f"conversation:{knowledge_base_id}:{conversation_id}"
                self.cache_service.delete(conversation_cache_key)

        except Exception as e:
            logger.warning(f"Failed to clear conversation cache: {e}")

    def archive_conversation(self, knowledge_base_id: int, conversation_id: int) -> bool:
        """
        归档对话

        Args:
            knowledge_base_id: 知识库ID
            conversation_id: 对话ID

        Returns:
            bool: 是否归档成功
        """
        try:
            conversation = self.get_conversation(knowledge_base_id, conversation_id)
            conversation.is_archived = True
            conversation.updated_at = datetime.utcnow()

            db.session.commit()

            # 清除缓存
            self._clear_conversation_cache(knowledge_base_id, conversation_id)

            logger.info(f"Archived conversation {conversation_id}")
            return True

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to archive conversation {conversation_id}: {e}")
            return False

    def export_conversation(self, knowledge_base_id: int, conversation_id: int,
                           format_type: str = "json") -> Dict[str, Any]:
        """
        导出对话记录

        Args:
            knowledge_base_id: 知识库ID
            conversation_id: 对话ID
            format_type: 导出格式 (json, markdown, text)

        Returns:
            Dict[str, Any]: 导出的对话数据

        Raises:
            ConversationNotFoundError: 对话不存在
        """
        try:
            conversation = self.get_conversation(knowledge_base_id, conversation_id)

            if format_type.lower() == "json":
                return conversation.to_dict()

            elif format_type.lower() == "markdown":
                return self._export_as_markdown(conversation)

            elif format_type.lower() == "text":
                return self._export_as_text(conversation)

            else:
                raise ValueError(f"Unsupported export format: {format_type}")

        except Exception as e:
            logger.error(f"Failed to export conversation {conversation_id}: {e}")
            raise

    def _export_as_markdown(self, conversation: ConversationHistory) -> Dict[str, Any]:
        """导出为Markdown格式"""
        markdown_content = f"# {conversation.title}\n\n"
        markdown_content += f"**创建时间**: {conversation.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        markdown_content += f"**最后更新**: {conversation.updated_at.strftime('%Y-%m-%d %H:%M:%S')}\n"

        if conversation.tags:
            markdown_content += f"**标签**: {', '.join(conversation.tags)}\n"

        markdown_content += "\n## 对话记录\n\n"

        for message in conversation.messages:
            role = message.get('role', 'unknown')
            content = message.get('content', '')
            timestamp = message.get('timestamp', '')

            if role == 'user':
                markdown_content += f"### 👤 用户\n{content}\n\n"
            elif role == 'assistant':
                markdown_content += f"### 🤖 助手\n{content}\n\n"
            else:
                markdown_content += f"### {role.title()}\n{content}\n\n"

        return {
            'content': markdown_content,
            'filename': f"{conversation.title}_{conversation.id}.md",
            'format': 'markdown'
        }

    def _export_as_text(self, conversation: ConversationHistory) -> Dict[str, Any]:
        """导出为纯文本格式"""
        text_content = f"对话标题: {conversation.title}\n"
        text_content += f"创建时间: {conversation.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        text_content += f"最后更新: {conversation.updated_at.strftime('%Y-%m-%d %H:%M:%S')}\n"

        if conversation.tags:
            text_content += f"标签: {', '.join(conversation.tags)}\n"

        text_content += "\n" + "=" * 50 + "\n\n"

        for message in conversation.messages:
            role = message.get('role', 'unknown')
            content = message.get('content', '')

            text_content += f"[{role.title()}]:\n{content}\n\n"

        return {
            'content': text_content,
            'filename': f"{conversation.title}_{conversation.id}.txt",
            'format': 'text'
        }


# 全局服务实例
_conversation_service_instance = None


def get_conversation_service() -> ConversationService:
    """获取对话服务实例（单例模式）"""
    global _conversation_service_instance
    if _conversation_service_instance is None:
        _conversation_service_instance = ConversationService()
    return _conversation_service_instance