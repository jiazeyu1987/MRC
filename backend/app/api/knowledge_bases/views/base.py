#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
知识库API基础资源类

提供通用的CRUD操作和响应格式标准化
"""

from flask import request, current_app
from flask_restful import Resource
from werkzeug.datastructures import FileStorage
from app import db
from app.models import KnowledgeBase, KnowledgeBaseConversation, Document, DocumentChunk
from app.services.knowledge_base_service import get_knowledge_base_service
from app.services.document_service import DocumentService
from app.services.upload_service import UploadService
from app.services.chunk_service import ChunkService
from app.services.ragflow_service import get_ragflow_service, RAGFlowAPIError, RAGFlowService
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BaseKnowledgeBaseResource(Resource):
    """知识库基础资源类"""

    def __init__(self):
        self.knowledge_base_service = get_knowledge_base_service()
        self.document_service = DocumentService()
        self.upload_service = UploadService()
        self.chunk_service = ChunkService()
        self.ragflow_service = get_ragflow_service()

    def _get_page_params(self):
        """获取分页参数"""
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        return page, per_page

    def _get_sort_params(self, default_sort='created_at', default_order='desc'):
        """获取排序参数"""
        sort_by = request.args.get('sort_by', default_sort)
        sort_order = request.args.get('sort_order', default_order)
        return sort_by, sort_order

    def _format_response(self, data=None, message=None, status=200, error=None, error_code=None):
        """格式化标准响应"""
        is_success = error is None and 200 <= status < 300

        response = {
            'success': is_success,
            'status': 'success' if is_success else 'error',
            'timestamp': datetime.utcnow().isoformat(),
        }

        if data is not None:
            response['data'] = data
        if message:
            response['message'] = message
        if error:
            # 保留原有 error 字段，同时用 message 表示主要错误信息
            response['error'] = error
            if 'message' not in response:
                response['message'] = str(error)
        if error_code:
            response['error_code'] = error_code

        return response, status

    def _handle_service_error(self, error, operation="操作"):
        """统一处理服务层错误"""
        logger.error(f"{operation}失败: {str(error)}")

        if isinstance(error, RAGFlowAPIError):
            return self._format_response(
                error=f"RAGFlow API错误: {str(error)}",
                status=503,
                error_code='RAGFLOW_API_ERROR'
            )
        elif isinstance(error, ValueError):
            return self._format_response(
                error=f"参数错误: {str(error)}",
                status=400,
                error_code='INVALID_REQUEST'
            )
        else:
            return self._format_response(
                error=f"服务器内部错误: {str(error)}",
                status=500,
                error_code='INTERNAL_ERROR'
            )

    def _validate_knowledge_base_exists(self, knowledge_base_id):
        """验证知识库是否存在"""
        knowledge_base = KnowledgeBase.query.get(knowledge_base_id)
        if not knowledge_base:
            return None, self._format_response(
                error=f"知识库 {knowledge_base_id} 不存在",
                status=404
            )
        return knowledge_base, None


class BaseDocumentResource(BaseKnowledgeBaseResource):
    """文档基础资源类"""

    def _validate_document_exists(self, document_id):
        """验证文档是否存在"""
        document = Document.query.get(document_id)
        if not document:
            return None, self._format_response(
                error=f"文档 {document_id} 不存在",
                status=404
            )
        return document, None

    def _validate_file_upload(self, file_key='file'):
        """验证文件上传"""
        if file_key not in request.files:
            return None, self._format_response(
                error="没有上传文件",
                status=400
            )

        file = request.files[file_key]
        if file.filename == '':
            return None, self._format_response(
                error="文件名为空",
                status=400
            )

        # 检查文件大小 (50MB限制)
        if hasattr(file, 'content_length') and file.content_length > 50 * 1024 * 1024:
            return None, self._format_response(
                error="文件大小超过50MB限制",
                status=400
            )

        return file, None


class BaseConversationResource(BaseKnowledgeBaseResource):
    """对话基础资源类"""

    def _validate_conversation_exists(self, conversation_id):
        """验证对话是否存在"""
        conversation = KnowledgeBaseConversation.query.get(conversation_id)
        if not conversation:
            return None, self._format_response(
                error=f"对话 {conversation_id} 不存在",
                status=404
            )
        return conversation, None
