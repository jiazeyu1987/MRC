#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
对话序列化器

提供对话相关数据的序列化和反序列化功能
"""

from flask_marshmallow import Marshmallow
from marshmallow import fields, validate, validates, ValidationError
from app.models import KnowledgeBaseConversation
from datetime import datetime

ma = Marshmallow()


class ConversationMessageSchema(ma.Schema):
    """对话消息序列化器"""
    id = fields.Integer(dump_only=True)
    role = fields.String(required=True, validate=validate.OneOf(['user', 'assistant', 'system']))
    content = fields.String(required=True, validate=validate.Length(min=1, max=10000))
    timestamp = fields.DateTime(dump_only=True)
    token_count = fields.Integer(dump_only=True)
    metadata = fields.Dict(dump_only=True)


class ConversationSchema(ma.SQLAlchemyAutoSchema):
    """对话基础序列化器"""
    class Meta:
        model = KnowledgeBaseConversation
        include_fk = True
        load_instance = True

    id = fields.Integer(dump_only=True)
    knowledge_base_id = fields.Integer(required=True)
    title = fields.String(required=True, validate=validate.Length(min=1, max=255))
    status = fields.String(dump_only=True)
    messages = fields.List(fields.Nested(ConversationMessageSchema), dump_only=True)
    tags = fields.List(fields.String(), missing=[])
    metadata = fields.Dict(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    @validates('title')
    def validate_title_not_empty(self, value):
        """验证标题不为空"""
        if not value or len(value.strip()) == 0:
            raise ValidationError('对话标题不能为空')


class ConversationCreateSchema(ma.Schema):
    """对话创建序列化器"""
    knowledge_base_id = fields.Integer(required=True)
    title = fields.String(required=True, validate=validate.Length(min=1, max=255))
    initial_message = fields.String(allow_none=True, validate=validate.Length(max=2000))
    tags = fields.List(fields.String(), missing=[])
    metadata = fields.Dict(missing={})


class ConversationUpdateSchema(ma.Schema):
    """对话更新序列化器"""
    title = fields.String(validate=validate.Length(min=1, max=255))
    messages = fields.List(fields.Nested(ConversationMessageSchema), allow_none=True)
    tags = fields.List(fields.String(), allow_none=True)
    metadata = fields.Dict(allow_none=True)


class ConversationListSchema(ma.Schema):
    """对话列表序列化器"""
    conversations = fields.List(fields.Nested(ConversationSchema))
    pagination = fields.Dict()


class ConversationExportSchema(ma.Schema):
    """对话导出序列化器"""
    format = fields.String(missing='json', validate=validate.OneOf(['json', 'txt', 'csv', 'markdown']))
    include_metadata = fields.Boolean(missing=True)
    include_timestamps = fields.Boolean(missing=True)
    message_format = fields.String(missing='detailed', validate=validate.OneOf(['detailed', 'simple', 'compact']))


class ConversationTemplateSchema(ma.Schema):
    """对话模板序列化器"""
    id = fields.Integer(dump_only=True)
    name = fields.String(required=True, validate=validate.Length(min=1, max=255))
    description = fields.String(allow_none=True, validate=validate.Length(max=1000))
    knowledge_base_id = fields.Integer(required=True)
    initial_message = fields.String(allow_none=True, validate=validate.Length(max=2000))
    conversation_structure = fields.Dict(dump_only=True)
    tags = fields.List(fields.String(), missing=[])
    usage_count = fields.Integer(dump_only=True)
    is_active = fields.Boolean(missing=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class ConversationTemplateCreateSchema(ma.Schema):
    """对话模板创建序列化器"""
    conversation_id = fields.Integer(required=True)
    template_name = fields.String(required=True, validate=validate.Length(min=1, max=255))
    description = fields.String(allow_none=True, validate=validate.Length(max=1000))
    include_messages = fields.Boolean(missing=True)
    tags = fields.List(fields.String(), missing=[])


class ConversationSearchSchema(ma.Schema):
    """对话搜索序列化器"""
    query = fields.String(validate=validate.Length(min=1, max=500))
    search_in = fields.List(fields.String(), missing=['title', 'messages'], validate=validate.ContainsOnly(['title', 'messages', 'tags']))
    status = fields.String(validate=validate.OneOf(['all', 'active', 'archived']))
    date_from = fields.DateTime(allow_none=True)
    date_to = fields.DateTime(allow_none=True)
    tags = fields.List(fields.String(), missing=[])
    limit = fields.Integer(missing=20, validate=validate.Range(min=1, max=100))
    sort_by = fields.String(missing='created_at', validate=validate.OneOf(['created_at', 'updated_at', 'title']))
    sort_order = fields.String(missing='desc', validate=validate.OneOf(['asc', 'desc']))


class ConversationAnalyticsSchema(ma.Schema):
    """对话分析序列化器"""
    total_conversations = fields.Integer()
    active_conversations = fields.Integer()
    average_message_count = fields.Float()
    average_response_time = fields.Float()
    conversation_duration_stats = fields.Dict()
    popular_tags = fields.List(fields.String())
    daily_stats = fields.List(fields.Dict())
    user_engagement_metrics = fields.Dict()


class ConversationStatsSchema(ma.Schema):
    """对话统计序列化器"""
    message_count = fields.Integer()
    user_message_count = fields.Integer()
    assistant_message_count = fields.Integer()
    total_tokens = fields.Integer()
    average_tokens_per_message = fields.Float()
    conversation_duration = fields.Integer()
    first_response_time = fields.Float()
    last_activity = fields.DateTime()


# 导出序列化器实例
conversation_schema = ConversationSchema()
conversation_create_schema = ConversationCreateSchema()
conversation_update_schema = ConversationUpdateSchema()
conversation_list_schema = ConversationListSchema()
conversation_export_schema = ConversationExportSchema()
conversation_template_schema = ConversationTemplateSchema()
conversation_template_create_schema = ConversationTemplateCreateSchema()
conversation_search_schema = ConversationSearchSchema()
conversation_analytics_schema = ConversationAnalyticsSchema()
conversation_stats_schema = ConversationStatsSchema()