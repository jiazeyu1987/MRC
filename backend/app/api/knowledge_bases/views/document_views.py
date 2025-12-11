#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
文档管理视图

提供文档的上传、列表、详情、删除等操作
"""

from flask import request, current_app
from .base import BaseDocumentResource


class DocumentListView(BaseDocumentResource):
    """文档列表资源"""

    def get(self, knowledge_base_id):
        """获取知识库的文档列表"""
        try:
            # 首先验证知识库存在
            knowledge_base, error_response = self._validate_knowledge_base_exists(knowledge_base_id)
            if error_response:
                return error_response

            # 查询参数
            page, limit = self._get_page_params()
            limit = min(limit, 100)  # 最大100条
            search = request.args.get('search', '', type=str)
            status = request.args.get('status', '', type=str)
            file_type = request.args.get('file_type', '', type=str)
            sort_by, sort_order = self._get_sort_params()

            # 构建过滤器
            filters = {
                'page': page,
                'limit': limit,
                'search': search if search else None,
                'status': status if status else None,
                'file_type': file_type if file_type else None,
                'sort_by': sort_by,
                'sort_order': sort_order
            }

            # 获取文档列表
            documents = self.document_service.get_documents(knowledge_base_id, filters)

            # 获取总数
            total = len(documents)

            return self._format_response({
                'documents': documents,  # RAGFlow already returns dictionaries
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total,
                    'has_more': total > page * limit
                }
            })

        except Exception as e:
            return self._handle_service_error(e, "获取文档列表")

    def post(self, knowledge_base_id):
        """上传文档到知识库"""
        try:
            # 验证知识库存在
            knowledge_base, error_response = self._validate_knowledge_base_exists(knowledge_base_id)
            if error_response:
                return error_response

            # 验证文件上传
            file, error_response = self._validate_file_upload('file')
            if error_response:
                return error_response

            # 处理文件上传
            result = self.upload_service.process_upload(file, knowledge_base_id)

            if result['success']:
                return self._format_response(
                    data={
                        'document': result['document'],
                        'upload_id': result['upload_id']
                    },
                    message='文档上传成功'
                )
            else:
                return self._format_response(
                    error=result.get('error', '文档上传失败'),
                    status=400
                )

        except Exception as e:
            return self._handle_service_error(e, "文档上传")


class DocumentDetailView(BaseDocumentResource):
    """文档详情资源"""

    def get(self, knowledge_base_id, document_id):
        """获取文档详情"""
        try:
            # 验证知识库存在
            knowledge_base, error_response = self._validate_knowledge_base_exists(knowledge_base_id)
            if error_response:
                return error_response

            # 验证文档存在
            document, error_response = self._validate_document_exists(document_id)
            if error_response:
                return error_response

            # 验证文档属于该知识库
            if document.knowledge_base_id != knowledge_base_id:
                return self._format_response(
                    error="文档不属于指定的知识库",
                    status=403
                )

            # 获取文档详情和块信息
            chunks = self.chunk_service.get_document_chunks(document_id)

            return self._format_response({
                'document': document.to_dict(),
                'chunks': [chunk.to_dict() for chunk in chunks],
                'chunk_count': len(chunks)
            })

        except Exception as e:
            return self._handle_service_error(e, "获取文档详情")

    def delete(self, knowledge_base_id, document_id):
        """删除文档"""
        try:
            # 验证知识库存在
            knowledge_base, error_response = self._validate_knowledge_base_exists(knowledge_base_id)
            if error_response:
                return error_response

            # 验证文档存在
            document, error_response = self._validate_document_exists(document_id)
            if error_response:
                return error_response

            # 验证文档属于该知识库
            if document.knowledge_base_id != knowledge_base_id:
                return self._format_response(
                    error="文档不属于指定的知识库",
                    status=403
                )

            # 执行删除（包括RAGFlow和本地数据库）
            delete_result = self.document_service.delete_document(document_id)

            return self._format_response(
                data=delete_result,
                message=f"文档 {document_id} 删除成功"
            )

        except Exception as e:
            db.session.rollback()
            return self._handle_service_error(e, "删除文档")


class DocumentUploadView(BaseDocumentResource):
    """文档上传资源（增强版）"""

    def post(self, knowledge_base_id):
        """增强版文档上传（支持多文件和额外参数）"""
        try:
            # 验证知识库存在
            knowledge_base, error_response = self._validate_knowledge_base_exists(knowledge_base_id)
            if error_response:
                return error_response

            # 获取上传参数
            json_data = request.get_json() or {}
            chunk_size = json_data.get('chunk_size', 500)
            chunk_overlap = json_data.get('chunk_overlap', 50)
            auto_process = json_data.get('auto_process', True)

            # 处理单文件上传
            if 'file' in request.files:
                file, error_response = self._validate_file_upload('file')
                if error_response:
                    return error_response

                result = self.upload_service.process_upload(
                    file,
                    knowledge_base_id,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    auto_process=auto_process
                )

                if result['success']:
                    return self._format_response(
                        data={
                            'document': result['document'],
                            'upload_id': result['upload_id'],
                            'processing_status': result.get('processing_status', 'pending')
                        },
                        message='文档上传成功'
                    )
                else:
                    return self._format_response(
                        error=result.get('error', '文档上传失败'),
                        status=400
                    )

            # 处理多文件上传
            elif 'files' in request.files:
                files = request.files.getlist('files')
                if not files:
                    return self._format_response(
                        error="没有选择文件",
                        status=400
                    )

                upload_results = []
                for file in files:
                    if file.filename:
                        result = self.upload_service.process_upload(
                            file,
                            knowledge_base_id,
                            chunk_size=chunk_size,
                            chunk_overlap=chunk_overlap,
                            auto_process=auto_process
                        )
                        upload_results.append({
                            'filename': file.filename,
                            'success': result['success'],
                            'document': result.get('document'),
                            'error': result.get('error')
                        })

                return self._format_response(
                    data={
                        'upload_results': upload_results,
                        'total_files': len(files),
                        'successful_uploads': sum(1 for r in upload_results if r['success'])
                    },
                    message=f"批量上传完成：{sum(1 for r in upload_results if r['success'])}/{len(files)} 个文件成功"
                )

            else:
                return self._format_response(
                    error="没有选择文件",
                    status=400
                )

        except Exception as e:
            return self._handle_service_error(e, "文档上传")


class DocumentChunksView(BaseDocumentResource):
    """文档块管理资源"""

    def get(self, knowledge_base_id, document_id):
        """获取文档的所有块"""
        try:
            # 验证知识库和文档存在
            knowledge_base, error_response = self._validate_knowledge_base_exists(knowledge_base_id)
            if error_response:
                return error_response

            document, error_response = self._validate_document_exists(document_id)
            if error_response:
                return error_response

            # 验证文档属于该知识库
            if document.knowledge_base_id != knowledge_base_id:
                return self._format_response(
                    error="文档不属于指定的知识库",
                    status=403
                )

            # 获取文档块
            chunks = self.chunk_service.get_document_chunks(document_id)

            return self._format_response({
                'chunks': [chunk.to_dict() for chunk in chunks],
                'total_chunks': len(chunks)
            })

        except Exception as e:
            return self._handle_service_error(e, "获取文档块")

    def post(self, knowledge_base_id, document_id):
        """重新处理文档块"""
        try:
            # 验证权限
            knowledge_base, error_response = self._validate_knowledge_base_exists(knowledge_base_id)
            if error_response:
                return error_response

            document, error_response = self._validate_document_exists(document_id)
            if error_response:
                return error_response

            if document.knowledge_base_id != knowledge_base_id:
                return self._format_response(
                    error="文档不属于指定的知识库",
                    status=403
                )

            # 获取处理参数
            json_data = request.get_json() or {}
            chunk_size = json_data.get('chunk_size', 500)
            chunk_overlap = json_data.get('chunk_overlap', 50)

            # 重新处理文档块
            result = self.chunk_service.reprocess_document_chunks(
                document_id, chunk_size, chunk_overlap
            )

            return self._format_response(
                data=result,
                message="文档块重新处理完成"
            )

        except Exception as e:
            return self._handle_service_error(e, "重新处理文档块")