#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
知识库序列化器

提供知识库相关数据的序列化和反序列化功能
"""

from flask_marshmallow import Marshmallow
from marshmallow import fields, validate, validates, ValidationError
from app.models import KnowledgeBase
from datetime import datetime

ma = Marshmallow()


class KnowledgeBaseSchema(ma.SQLAlchemyAutoSchema):
    """知识库基础序列化器"""
    class Meta:
        model = KnowledgeBase
        include_fk = True
        load_instance = True

    # 自定义字段
    id = fields.Integer(dump_only=True)
    name = fields.String(required=True, validate=validate.Length(min=1, max=255))
    description = fields.String(allow_none=True)
    ragflow_dataset_id = fields.String(allow_none=True)
    connection_status = fields.String(dump_only=True)
    is_active = fields.Boolean(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    @validates('name')
    def validate_name_not_duplicate(self, value):
        """验证知识库名称不重复"""
        if KnowledgeBase.query.filter_by(name=value).first():
            raise ValidationError('知识库名称已存在')


class KnowledgeBaseCreateSchema(KnowledgeBaseSchema):
    """知识库创建序列化器"""
    name = fields.String(required=True, validate=validate.Length(min=1, max=255))
    description = fields.String(allow_none=True, validate=validate.Length(max=1000))
    ragflow_dataset_id = fields.String(allow_none=True)


class KnowledgeBaseUpdateSchema(KnowledgeBaseSchema):
    """知识库更新序列化器"""
    name = fields.String(validate=validate.Length(min=1, max=255))
    description = fields.String(allow_none=True, validate=validate.Length(max=1000))
    is_active = fields.Boolean()


class KnowledgeBaseListSchema(ma.Schema):
    """知识库列表序列化器"""
    knowledge_bases = fields.List(fields.Nested(KnowledgeBaseSchema))
    total = fields.Integer()
    page = fields.Integer()
    per_page = fields.Integer()
    pages = fields.Integer()
    has_prev = fields.Boolean()
    has_next = fields.Boolean()


class KnowledgeBaseStatisticsSchema(ma.Schema):
    """知识库统计信息序列化器"""
    total_documents = fields.Integer()
    total_chunks = fields.Integer()
    total_conversations = fields.Integer()
    total_searches = fields.Integer()
    document_types = fields.Dict()
    last_updated = fields.DateTime()
    storage_usage = fields.Dict()
    processing_status = fields.Dict()


class KnowledgeBaseTestConversationSchema(ma.Schema):
    """知识库测试对话序列化器"""
    question = fields.String(required=True, validate=validate.Length(min=1, max=2000))
    context_strategy = fields.String(missing='last_message')
    max_context_length = fields.Integer(missing=2000, validate=validate.Range(min=100, max=8000))


class KnowledgeBaseRefreshSchema(ma.Schema):
    """知识库刷新序列化器"""
    action = fields.String(required=True, validate=validate.OneOf(['refresh_all', 'refresh_single']))
    knowledge_base_id = fields.Integer(allow_none=True)


# 导出序列化器实例
knowledge_base_schema = KnowledgeBaseSchema()
knowledge_base_create_schema = KnowledgeBaseCreateSchema()
knowledge_base_update_schema = KnowledgeBaseUpdateSchema()
knowledge_base_list_schema = KnowledgeBaseListSchema()
knowledge_base_statistics_schema = KnowledgeBaseStatisticsSchema()
knowledge_base_test_conversation_schema = KnowledgeBaseTestConversationSchema()
knowledge_base_refresh_schema = KnowledgeBaseRefreshSchema()