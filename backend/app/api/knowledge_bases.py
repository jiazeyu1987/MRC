#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
知识库API资源模块

提供知识库管理的RESTful API接口，包括：
- 知识库列表获取和刷新
- 知识库详情查看
- 知识库测试对话功能
- 统计信息和监控数据

遵循MRC项目的API模式，与其他模块保持一致的响应格式和错误处理
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


class KnowledgeBaseList(Resource):
    """知识库列表资源"""

    def get(self):
        """获取知识库列表"""
        try:
            # 查询参数
            page = request.args.get('page', 1, type=int)
            page_size = min(request.args.get('page_size', current_app.config['DEFAULT_PAGE_SIZE'], type=int),
                           current_app.config['MAX_PAGE_SIZE'])
            search = request.args.get('search', '', type=str)
            status = request.args.get('status', '', type=str)
            sort_by = request.args.get('sort_by', 'created_at', type=str)
            sort_order = request.args.get('sort_order', 'desc', type=str)

            # 使用知识库服务获取列表
            service = get_knowledge_base_service()
            knowledge_bases, total, pagination_info = service.get_knowledge_bases_list(
                page=page,
                per_page=page_size,
                status=status if status else None,
                search=search if search else None,
                sort_by=sort_by,
                sort_order=sort_order
            )

            # 转换为字典格式
            knowledge_bases_data = [kb.to_dict() for kb in knowledge_bases]

            return {
                'success': True,
                'data': {
                    'knowledge_bases': knowledge_bases_data,
                    'total': total,
                    'page': page,
                    'page_size': page_size,
                    'pages': pagination_info.get('pages', 0),
                    'has_prev': pagination_info.get('has_prev', False),
                    'has_next': pagination_info.get('has_next', False)
                }
            }

        except Exception as e:
            current_app.logger.error(f"获取知识库列表失败: {str(e)}")
            return {
                'success': False,
                'error_code': 'INTERNAL_ERROR',
                'message': '获取知识库列表失败'
            }, 500

    def post(self):
        """执行知识库相关操作：刷新数据集"""
        try:
            json_data = request.get_json()
            if not json_data:
                return {
                    'success': False,
                    'error_code': 'INVALID_REQUEST',
                    'message': '请求体不能为空'
                }, 400

            action = json_data.get('action', '')

            if action == 'refresh_all':
                # 刷新所有数据集
                service = get_knowledge_base_service()
                sync_result = service.sync_datasets_from_ragflow()

                return {
                    'success': True,
                    'data': sync_result,
                    'message': f'数据集刷新完成：创建 {sync_result["created"]} 个，更新 {sync_result["updated"]} 个'
                }

            elif action == 'refresh_single':
                # 刷新单个数据集
                knowledge_base_id = json_data.get('knowledge_base_id')
                if not knowledge_base_id:
                    return {
                        'success': False,
                        'error_code': 'INVALID_REQUEST',
                        'message': '缺少知识库ID参数'
                    }, 400

                service = get_knowledge_base_service()
                refresh_result = service.refresh_dataset_from_ragflow(knowledge_base_id)

                return {
                    'success': True,
                    'data': refresh_result,
                    'message': f'知识库刷新成功：{refresh_result["new_info"]["name"]}'
                }

            else:
                return {
                    'success': False,
                    'error_code': 'INVALID_ACTION',
                    'message': f'不支持的操作: {action}'
                }, 400

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"知识库操作失败: {str(e)}")
            return {
                'success': False,
                'error_code': 'INTERNAL_ERROR',
                'message': '知识库操作失败'
            }, 500


class KnowledgeBaseDetail(Resource):
    """知识库详情资源"""

    def get(self, knowledge_base_id):
        """获取知识库详情"""
        try:
            service = get_knowledge_base_service()
            knowledge_base = service.get_knowledge_base_by_id(knowledge_base_id)

            if not knowledge_base:
                return {
                    'success': False,
                    'error_code': 'NOT_FOUND',
                    'message': '知识库不存在'
                }, 404

            # 获取知识库详情（包括统计信息）
            knowledge_base_data = knowledge_base.to_dict()

            # 获取关联的角色信息
            try:
                roles = service.get_knowledge_base_roles(knowledge_base_id)
                knowledge_base_data['linked_roles'] = roles
            except Exception as e:
                current_app.logger.warning(f"获取知识库角色关联失败: {str(e)}")
                knowledge_base_data['linked_roles'] = []

            # 获取最近的测试对话数量
            try:
                recent_conversations = KnowledgeBaseConversation.query.filter_by(
                    knowledge_base_id=knowledge_base_id
                ).order_by(KnowledgeBaseConversation.created_at.desc()).limit(5).all()

                knowledge_base_data['recent_conversations'] = [
                    conv.to_dict(include_references=False)
                    for conv in recent_conversations
                ]
                knowledge_base_data['conversation_count'] = KnowledgeBaseConversation.query.filter_by(
                    knowledge_base_id=knowledge_base_id
                ).count()
            except Exception as e:
                current_app.logger.warning(f"获取测试对话信息失败: {str(e)}")
                knowledge_base_data['recent_conversations'] = []
                knowledge_base_data['conversation_count'] = 0

            return {
                'success': True,
                'data': knowledge_base_data
            }

        except Exception as e:
            current_app.logger.error(f"获取知识库详情失败: {str(e)}")
            return {
                'success': False,
                'error_code': 'INTERNAL_ERROR',
                'message': '获取知识库详情失败'
            }, 500

    def post(self, knowledge_base_id):
        """执行知识库测试对话"""
        try:
            service = get_knowledge_base_service()
            knowledge_base = service.get_knowledge_base_by_id(knowledge_base_id)

            if not knowledge_base:
                return {
                    'success': False,
                    'error_code': 'NOT_FOUND',
                    'message': '知识库不存在'
                }, 404

            json_data = request.get_json()
            if not json_data:
                return {
                    'success': False,
                    'error_code': 'INVALID_REQUEST',
                    'message': '请求体不能为空'
                }, 400

            action = json_data.get('action', '')

            if action == 'test_conversation':
                # 执行测试对话
                question = json_data.get('question', '')
                title = json_data.get('title', f'测试对话 - {datetime.now().strftime("%Y%m%d%H%M%S")}')

                if not question.strip():
                    return {
                        'success': False,
                        'error_code': 'INVALID_REQUEST',
                        'message': '测试问题不能为空'
                    }, 400

                # 调用RAGFlow服务进行对话
                ragflow_service = get_ragflow_service()
                if not ragflow_service:
                    return {
                        'success': False,
                        'error_code': 'SERVICE_UNAVAILABLE',
                        'message': 'RAGFlow服务不可用'
                    }, 503

                try:
                    # 执行RAGFlow对话
                    chat_response = ragflow_service.chat_with_dataset(
                        dataset_id=knowledge_base.ragflow_dataset_id,
                        question=question.strip()
                    )

                    # 创建测试对话记录
                    conversation = KnowledgeBaseConversation(
                        knowledge_base_id=knowledge_base_id,
                        title=title,
                        user_question=question.strip(),
                        ragflow_response=chat_response.answer,
                        confidence_score=chat_response.confidence_score,
                        status='active'
                    )

                    # 设置引用信息
                    if chat_response.references:
                        conversation.references_dict = chat_response.references

                    db.session.add(conversation)
                    db.session.commit()

                    # 返回测试结果
                    result_data = conversation.to_dict(include_references=True, include_metadata=True)

                    return {
                        'success': True,
                        'data': result_data,
                        'message': '测试对话执行成功'
                    }

                except RAGFlowAPIError as e:
                    current_app.logger.error(f"RAGFlow API调用失败: {str(e)}")

                    # 创建错误对话记录
                    conversation = KnowledgeBaseConversation(
                        knowledge_base_id=knowledge_base_id,
                        title=title,
                        user_question=question.strip(),
                        ragflow_response=None,
                        confidence_score=None,
                        status='error'
                    )
                    conversation.extra_data_dict = {'error': str(e)}

                    db.session.add(conversation)
                    db.session.commit()

                    return {
                        'success': False,
                        'error_code': 'RAGFLOW_API_ERROR',
                        'message': f'RAGFlow API调用失败: {str(e)}'
                    }, 500

            elif action == 'get_conversations':
                # 获取测试对话列表
                page = json_data.get('page', 1)
                per_page = min(json_data.get('per_page', 20), current_app.config['MAX_PAGE_SIZE'])
                status_filter = json_data.get('status', '')

                try:
                    query = KnowledgeBaseConversation.query.filter_by(knowledge_base_id=knowledge_base_id)

                    if status_filter:
                        query = query.filter_by(status=status_filter)

                    pagination = query.order_by(
                        KnowledgeBaseConversation.created_at.desc()
                    ).paginate(page=page, per_page=per_page, error_out=False)

                    conversations = [
                        conv.to_dict(include_references=False)
                        for conv in pagination.items
                    ]

                    return {
                        'success': True,
                        'data': {
                            'conversations': conversations,
                            'total': pagination.total,
                            'page': page,
                            'page_size': per_page,
                            'pages': pagination.pages
                        }
                    }

                except Exception as e:
                    current_app.logger.error(f"获取测试对话列表失败: {str(e)}")
                    return {
                        'success': False,
                        'error_code': 'INTERNAL_ERROR',
                        'message': '获取测试对话列表失败'
                    }, 500

            else:
                return {
                    'success': False,
                    'error_code': 'INVALID_ACTION',
                    'message': f'不支持的操作: {action}'
                }, 400

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"知识库详情操作失败: {str(e)}")
            return {
                'success': False,
                'error_code': 'INTERNAL_ERROR',
                'message': '知识库详情操作失败'
            }, 500


class KnowledgeBaseStatistics(Resource):
    """知识库统计信息资源"""

    def get(self):
        """获取知识库统计信息"""
        try:
            service = get_knowledge_base_service()
            statistics = service.get_knowledge_base_statistics()

            return {
                'success': True,
                'data': statistics
            }

        except Exception as e:
            current_app.logger.error(f"获取知识库统计信息失败: {str(e)}")
            return {
                'success': False,
                'error_code': 'INTERNAL_ERROR',
                'message': '获取统计信息失败'
            }, 500


class KnowledgeBaseConversationDetail(Resource):
    """知识库测试对话详情资源"""

    def get(self, knowledge_base_id, conversation_id):
        """获取测试对话详情"""
        try:
            conversation = KnowledgeBaseConversation.query.filter_by(
                id=conversation_id,
                knowledge_base_id=knowledge_base_id
            ).first()

            if not conversation:
                return {
                    'success': False,
                    'error_code': 'NOT_FOUND',
                    'message': '测试对话不存在'
                }, 404

            return {
                'success': True,
                'data': conversation.to_dict(include_references=True, include_metadata=True)
            }

        except Exception as e:
            current_app.logger.error(f"获取测试对话详情失败: {str(e)}")
            return {
                'success': False,
                'error_code': 'INTERNAL_ERROR',
                'message': '获取测试对话详情失败'
            }, 500

    def delete(self, knowledge_base_id, conversation_id):
        """删除测试对话"""
        try:
            conversation = KnowledgeBaseConversation.query.filter_by(
                id=conversation_id,
                knowledge_base_id=knowledge_base_id
            ).first()

            if not conversation:
                return {
                    'success': False,
                    'error_code': 'NOT_FOUND',
                    'message': '测试对话不存在'
                }, 404

            db.session.delete(conversation)
            db.session.commit()

            return {
                'success': True,
                'message': '测试对话删除成功'
            }

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"删除测试对话失败: {str(e)}")
            return {
                'success': False,
                'error_code': 'INTERNAL_ERROR',
                'message': '删除测试对话失败'
            }, 500


# ========== Document Management Resources ==========

class DocumentListResource(Resource):
    """文档列表资源"""

    def get(self, knowledge_base_id):
        """获取知识库的文档列表"""
        try:
            # 查询参数
            page = request.args.get('page', 1, type=int)
            limit = min(request.args.get('limit', 20, type=int), 100)
            search = request.args.get('search', '', type=str)
            status = request.args.get('status', '', type=str)
            file_type = request.args.get('file_type', '', type=str)
            sort_by = request.args.get('sort_by', 'created_at', type=str)
            sort_order = request.args.get('sort_order', 'desc', type=str)

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
            service = DocumentService()
            documents = service.get_documents(knowledge_base_id, filters)

            # 获取总数（简化版本，实际应该有分页计数）
            total = len(documents)

            return {
                'success': True,
                'data': {
                    'documents': documents,  # RAGFlow already returns dictionaries
                    'pagination': {
                        'page': page,
                        'limit': limit,
                        'total': total,
                        'has_more': total > page * limit
                    }
                }
            }

        except Exception as e:
            current_app.logger.error(f"获取文档列表失败: {str(e)}")
            return {
                'success': False,
                'error_code': 'INTERNAL_ERROR',
                'message': '获取文档列表失败'
            }, 500

    def post(self, knowledge_base_id):
        """上传文档到知识库"""
        try:
            # 检查是否有文件上传
            if 'file' not in request.files:
                return {
                    'success': False,
                    'error_code': 'NO_FILE',
                    'message': '没有选择文件'
                }, 400

            file = request.files['file']
            if file.filename == '':
                return {
                    'success': False,
                    'error_code': 'EMPTY_FILE',
                    'message': '文件名为空'
                }, 400

            # 处理文件上传
            service = UploadService()
            result = service.process_upload(file, knowledge_base_id)

            if result['success']:
                return {
                    'success': True,
                    'data': {
                        'document': result['document'],
                        'upload_id': result['upload_id']
                    },
                    'message': '文档上传成功'
                }
            else:
                return {
                    'success': False,
                    'error_code': 'UPLOAD_FAILED',
                    'message': result.get('error', '文档上传失败')
                }, 400

        except Exception as e:
            current_app.logger.error(f"文档上传失败: {str(e)}")
            return {
                'success': False,
                'error_code': 'INTERNAL_ERROR',
                'message': '文档上传失败'
            }, 500


class DocumentResource(Resource):
    """单个文档资源"""

    def get(self, knowledge_base_id, document_id):
        """获取文档详情"""
        try:
            service = DocumentService()
            document = service.get_document(document_id)

            if not document or document.knowledge_base_id != knowledge_base_id:
                return {
                    'success': False,
                    'error_code': 'NOT_FOUND',
                    'message': '文档不存在'
                }, 404

            return {
                'success': True,
                'data': document.to_dict()
            }

        except Exception as e:
            current_app.logger.error(f"获取文档详情失败: {str(e)}")
            return {
                'success': False,
                'error_code': 'INTERNAL_ERROR',
                'message': '获取文档详情失败'
            }, 500

    def delete(self, knowledge_base_id, document_id):
        """删除文档"""
        try:
            service = DocumentService()

            # 验证文档属于指定的知识库
            document = service.get_document(document_id)
            if not document or document.knowledge_base_id != knowledge_base_id:
                return {
                    'success': False,
                    'error_code': 'NOT_FOUND',
                    'message': '文档不存在'
                }, 404

            # 删除文档
            if service.delete_document(document_id):
                return {
                    'success': True,
                    'message': '文档删除成功'
                }
            else:
                return {
                    'success': False,
                    'error_code': 'DELETE_FAILED',
                    'message': '文档删除失败'
                }, 500

        except Exception as e:
            current_app.logger.error(f"删除文档失败: {str(e)}")
            db.session.rollback()
            return {
                'success': False,
                'error_code': 'INTERNAL_ERROR',
                'message': '删除文档失败'
            }, 500


class DocumentUploadResource(Resource):
    """文档上传资源"""

    def post(self, knowledge_base_id):
        """处理文档上传（带进度跟踪）"""
        try:
            # 检查是否有文件上传
            if 'file' not in request.files:
                return {
                    'success': False,
                    'error_code': 'NO_FILE',
                    'message': '没有选择文件'
                }, 400

            file = request.files['file']
            if file.filename == '':
                return {
                    'success': False,
                    'error_code': 'EMPTY_FILE',
                    'message': '文件名为空'
                }, 400

            # 获取上传ID（用于进度跟踪）
            upload_id = request.form.get('upload_id')

            # 处理文件上传
            service = UploadService()
            result = service.process_upload(file, knowledge_base_id, upload_id)

            if result['success']:
                return {
                    'success': True,
                    'data': {
                        'document_id': result['document_id'],
                        'upload_id': result['upload_id']
                    },
                    'message': '文档上传成功'
                }
            else:
                return {
                    'success': False,
                    'error_code': 'UPLOAD_FAILED',
                    'message': result.get('error', '文档上传失败')
                }, 400

        except Exception as e:
            current_app.logger.error(f"文档上传失败: {str(e)}")
            return {
                'success': False,
                'error_code': 'INTERNAL_ERROR',
                'message': '文档上传失败'
            }, 500

    def get(self, knowledge_base_id):
        """获取上传状态"""
        try:
            upload_id = request.args.get('upload_id')
            if not upload_id:
                return {
                    'success': False,
                    'error_code': 'MISSING_UPLOAD_ID',
                    'message': '缺少上传ID'
                }, 400

            service = UploadService()
            status = service.get_upload_status(upload_id)

            if status:
                return {
                    'success': True,
                    'data': status
                }
            else:
                return {
                    'success': False,
                    'error_code': 'NOT_FOUND',
                    'message': '上传记录不存在'
                }, 404

        except Exception as e:
            current_app.logger.error(f"获取上传状态失败: {str(e)}")
            return {
                'success': False,
                'error_code': 'INTERNAL_ERROR',
                'message': '获取上传状态失败'
            }, 500


class ChunkSearchResource(Resource):
    """文档块搜索资源"""

    def post(self, knowledge_base_id):
        """搜索文档块"""
        try:
            data = request.get_json()
            if not data or 'query' not in data:
                return {
                    'success': False,
                    'error_code': 'MISSING_QUERY',
                    'message': '缺少搜索查询'
                }, 400

            query = data['query']
            filters = {
                'document_id': data.get('document_id'),
                'min_relevance_score': data.get('min_relevance_score', 0.0),
                'max_results': min(data.get('max_results', 10), 50)
            }

            service = ChunkService()
            result = service.search_chunks(knowledge_base_id, query, filters)

            return {
                'success': True,
                'data': {
                    'chunks': result['chunks'],
                    'total_count': result['total_count'],
                    'query': result['query'],
                    'search_time': result['search_time'],
                    'filters_applied': result['filters_applied']
                }
            }

        except Exception as e:
            current_app.logger.error(f"搜索文档块失败: {str(e)}")
            return {
                'success': False,
                'error_code': 'INTERNAL_ERROR',
                'message': '搜索文档块失败'
            }, 500


class DocumentChunksResource(Resource):
    """文档块资源"""

    def get(self, knowledge_base_id, document_id):
        """获取文档的所有块"""
        try:
            # 验证文档属于指定的知识库
            document = Document.query.filter_by(
                id=document_id,
                knowledge_base_id=knowledge_base_id
            ).first()

            if not document:
                return {
                    'success': False,
                    'error_code': 'NOT_FOUND',
                    'message': '文档不存在'
                }, 404

            # 获取过滤器
            filters = {
                'chunk_index_min': request.args.get('chunk_index_min', type=int),
                'chunk_index_max': request.args.get('chunk_index_max', type=int),
                'sort_by': request.args.get('sort_by', 'chunk_index', type=str),
                'sort_order': request.args.get('sort_order', 'asc', type=str)
            }

            # 获取文档块
            service = ChunkService()
            chunks = service.get_document_chunks(document_id, filters)

            return {
                'success': True,
                'data': {
                    'document_id': document_id,
                    'document_name': document.original_filename,
                    'chunks': chunks,
                    'total_chunks': len(chunks)
                }
            }

        except Exception as e:
            current_app.logger.error(f"获取文档块失败: {str(e)}")
            return {
                'success': False,
                'error_code': 'INTERNAL_ERROR',
                'message': '获取文档块失败'
            }, 500


class RAGFlowDocumentResource(Resource):
    """RAGFlow文档资源 (处理字符串文档ID)"""

    def get(self, knowledge_base_id, document_id):
        """获取RAGFlow文档详情"""
        try:
            # 验证知识库存在
            knowledge_base = KnowledgeBase.query.get(knowledge_base_id)
            if not knowledge_base:
                return {
                    'success': False,
                    'error_code': 'NOT_FOUND',
                    'message': '知识库不存在'
                }, 404

            # 从RAGFlow获取所有文档，然后查找指定的文档
            from app.services.ragflow_service import get_ragflow_service
            ragflow_service = get_ragflow_service()
            if not ragflow_service:
                return {
                    'success': False,
                    'error_code': 'SERVICE_UNAVAILABLE',
                    'message': 'RAGFlow服务不可用'
                }, 503

            documents = ragflow_service.get_dataset_documents(knowledge_base.ragflow_dataset_id)

            # 查找指定的文档
            document = None
            for doc in documents:
                if doc.get('id') == document_id:
                    document = doc
                    break

            if not document:
                return {
                    'success': False,
                    'error_code': 'NOT_FOUND',
                    'message': '文档不存在'
                }, 404

            return {
                'success': True,
                'data': document
            }

        except Exception as e:
            current_app.logger.error(f"获取RAGFlow文档详情失败: {str(e)}")
            return {
                'success': False,
                'error_code': 'INTERNAL_ERROR',
                'message': '获取文档详情失败'
            }, 500

    def delete(self, knowledge_base_id, document_id):
        """删除RAGFlow文档"""
        try:
            # 验证知识库存在
            knowledge_base = KnowledgeBase.query.get(knowledge_base_id)
            if not knowledge_base:
                return {
                    'success': False,
                    'error_code': 'NOT_FOUND',
                    'message': '知识库不存在'
                }, 404

            # 从RAGFlow删除文档
            from app.services.ragflow_service import get_ragflow_service
            ragflow_service = get_ragflow_service()
            if not ragflow_service:
                return {
                    'success': False,
                    'error_code': 'SERVICE_UNAVAILABLE',
                    'message': 'RAGFlow服务不可用'
                }, 503

            success = ragflow_service.delete_document(document_id)

            if not success:
                return {
                    'success': False,
                    'error_code': 'DELETE_FAILED',
                    'message': '删除文档失败'
                }, 500

            return {
                'success': True,
                'message': '文档删除成功'
            }

        except Exception as e:
            current_app.logger.error(f"删除RAGFlow文档失败: {str(e)}")
            return {
                'success': False,
                'error_code': 'INTERNAL_ERROR',
                'message': '删除文档失败'
            }, 500


class RAGFlowDocumentChunksResource(Resource):
    """RAGFlow文档块资源 (处理字符串文档ID)"""

    def get(self, knowledge_base_id, document_id):
        """获取RAGFlow文档的所有块"""
        try:
            # 验证知识库存在
            knowledge_base = KnowledgeBase.query.get(knowledge_base_id)
            if not knowledge_base:
                return {
                    'success': False,
                    'error_code': 'NOT_FOUND',
                    'message': '知识库不存在'
                }, 404

            # 获取过滤器
            filters = {
                'chunk_index_min': request.args.get('chunk_index_min', type=int),
                'chunk_index_max': request.args.get('chunk_index_max', type=int),
                'sort_by': request.args.get('sort_by', 'chunk_index', type=str),
                'sort_order': request.args.get('sort_order', 'asc', type=str)
            }

            # 从RAGFlow获取文档块
            from app.services.ragflow_service import get_ragflow_service
            ragflow_service = get_ragflow_service()
            if not ragflow_service:
                return {
                    'success': False,
                    'error_code': 'SERVICE_UNAVAILABLE',
                    'message': 'RAGFlow服务不可用'
                }, 503

            ragflow_chunks = ragflow_service.get_document_chunks(document_id, knowledge_base.ragflow_dataset_id)

            # 获取文档信息
            documents = ragflow_service.get_dataset_documents(knowledge_base.ragflow_dataset_id)
            document_name = '未知文档'
            for doc in documents:
                if doc.get('id') == document_id:
                    document_name = doc.get('name', '未知文档')
                    break

            # 验证是否有文档块
            if not ragflow_chunks:
                return {
                    'success': False,
                    'error_code': 'NO_CHUNKS',
                    'message': '文档块不存在或为空'
                }, 404

            # 转换RAGFlow chunk格式为前端期望的DocumentChunk格式
            chunks = []
            for idx, ragflow_chunk in enumerate(ragflow_chunks):
                chunk = {
                    'id': ragflow_chunk.get('id', f'chunk_{idx}'),
                    'document_id': document_id,
                    'ragflow_chunk_id': ragflow_chunk.get('id'),
                    'chunk_index': idx,
                    'content': ragflow_chunk.get('content', ''),
                    'content_preview': ragflow_chunk.get('content', '')[:200] + '...' if len(ragflow_chunk.get('content', '')) > 200 else ragflow_chunk.get('content', ''),
                    'word_count': len(ragflow_chunk.get('content', '').split()),
                    'character_count': len(ragflow_chunk.get('content', '')),
                    'ragflow_metadata': {
                        'available': ragflow_chunk.get('available', True),
                        'dataset_id': ragflow_chunk.get('dataset_id'),
                        'docnm_kwd': ragflow_chunk.get('docnm_kwd'),
                        'image_id': ragflow_chunk.get('image_id'),
                        'important_keywords': ragflow_chunk.get('important_keywords', []),
                        'positions': ragflow_chunk.get('positions', []),
                        'questions': ragflow_chunk.get('questions', [])
                    },
                    'created_at': ragflow_chunk.get('create_time', '') or '',
                    'updated_at': ragflow_chunk.get('update_time', '') or ''
                }
                chunks.append(chunk)

            return {
                'success': True,
                'data': {
                    'document_id': document_id,
                    'document_name': document_name,
                    'chunks': chunks,
                    'total_chunks': len(chunks)
                },
                'message': f'成功获取{len(chunks)}个文档块'
            }

        except Exception as e:
            current_app.logger.error(f"获取RAGFlow文档块失败: {str(e)}")
            return {
                'success': False,
                'error_code': 'INTERNAL_ERROR',
                'message': '获取文档块失败'
            }, 500