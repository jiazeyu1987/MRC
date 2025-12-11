#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
文档序列化器

提供文档相关数据的序列化和反序列化功能
"""

from flask_marshmallow import Marshmallow
from marshmallow import fields, validate, validates, ValidationError
from app.models import Document, DocumentChunk
from datetime import datetime
import os

ma = Marshmallow()


class DocumentSchema(ma.SQLAlchemyAutoSchema):
    """文档基础序列化器"""
    class Meta:
        model = Document
        include_fk = True
        load_instance = True

    id = fields.Integer(dump_only=True)
    filename = fields.String(required=True, validate=validate.Length(min=1, max=255))
    original_filename = fields.String(required=True, validate=validate.Length(min=1, max=255))
    file_path = fields.String(dump_only=True)
    file_size = fields.Integer(dump_only=True)
    file_type = fields.String(dump_only=True)
    mime_type = fields.String(dump_only=True)
    processing_status = fields.String(dump_only=True)
    error_message = fields.String(allow_none=True)
    chunk_count = fields.Integer(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    @validates('filename')
    def validate_filename_format(self, value):
        """验证文件名格式"""
        if not value or len(value.strip()) == 0:
            raise ValidationError('文件名不能为空')

        # 检查文件扩展名
        allowed_extensions = ['.pdf', '.docx', '.txt', '.md', '.doc', '.rtf']
        file_ext = os.path.splitext(value)[1].lower()
        if file_ext not in allowed_extensions:
            raise ValidationError(f'不支持的文件类型: {file_ext}')


class DocumentChunkSchema(ma.SQLAlchemyAutoSchema):
    """文档块序列化器"""
    class Meta:
        model = DocumentChunk
        include_fk = True
        load_instance = True

    id = fields.Integer(dump_only=True)
    document_id = fields.Integer(required=True)
    chunk_index = fields.Integer(dump_only=True)
    content = fields.String(dump_only=True)
    chunk_size = fields.Integer(dump_only=True)
    token_count = fields.Integer(dump_only=True)
    embedding_vector = fields.String(dump_only=True)  # 简化表示，实际可能是二进制数据
    created_at = fields.DateTime(dump_only=True)


class DocumentListSchema(ma.Schema):
    """文档列表序列化器"""
    documents = fields.List(fields.Nested(DocumentSchema))
    pagination = fields.Dict()


class DocumentUploadSchema(ma.Schema):
    """文档上传序列化器"""
    chunk_size = fields.Integer(missing=500, validate=validate.Range(min=100, max=2000))
    chunk_overlap = fields.Integer(missing=50, validate=validate.Range(min=0, max=500))
    auto_process = fields.Boolean(missing=True)
    extract_metadata = fields.Boolean(missing=True)
    generate_summary = fields.Boolean(missing=False)


class DocumentProcessingSchema(ma.Schema):
    """文档处理序列化器"""
    processing_status = fields.String(validate=validate.OneOf([
        'pending', 'processing', 'completed', 'failed', 'cancelled'
    ]))
    error_message = fields.String(allow_none=True)
    progress_percentage = fields.Float(validate=validate.Range(min=0, max=100))


class DocumentReprocessSchema(ma.Schema):
    """文档重新处理序列化器"""
    chunk_size = fields.Integer(validate=validate.Range(min=100, max=2000))
    chunk_overlap = fields.Integer(validate=validate.Range(min=0, max=500))
    force_reprocess = fields.Boolean(missing=False)


class DocumentSearchSchema(ma.Schema):
    """文档搜索序列化器"""
    query = fields.String(required=True, validate=validate.Length(min=1, max=500))
    search_type = fields.String(missing='content', validate=validate.OneOf([
        'content', 'filename', 'metadata', 'full_text'
    ]))
    file_types = fields.List(fields.String(), missing=[])
    limit = fields.Integer(missing=20, validate=validate.Range(min=1, max=100))


class DocumentBatchUploadSchema(ma.Schema):
    """批量文档上传序列化器"""
    chunk_size = fields.Integer(missing=500, validate=validate.Range(min=100, max=2000))
    chunk_overlap = fields.Integer(missing=50, validate=validate.Range(min=0, max=500))
    auto_process = fields.Boolean(missing=True)
    max_files = fields.Integer(missing=10, validate=validate.Range(min=1, max=50))


class DocumentStatisticsSchema(ma.Schema):
    """文档统计信息序列化器"""
    total_documents = fields.Integer()
    total_size = fields.Integer()
    file_type_distribution = fields.Dict()
    processing_status_distribution = fields.Dict()
    average_chunk_count = fields.Float()
    last_uploaded = fields.DateTime()


# 导出序列化器实例
document_schema = DocumentSchema()
document_chunk_schema = DocumentChunkSchema()
document_list_schema = DocumentListSchema()
document_upload_schema = DocumentUploadSchema()
document_processing_schema = DocumentProcessingSchema()
document_reprocess_schema = DocumentReprocessSchema()
document_search_schema = DocumentSearchSchema()
document_batch_upload_schema = DocumentBatchUploadSchema()
document_statistics_schema = DocumentStatisticsSchema()