#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
对话管理视图

提供知识库对话的创建、查询、更新、删除、导出等操作
"""

from flask import request, current_app, jsonify
from .base import BaseConversationResource
from app.services.conversation_service import get_conversation_service


class ConversationListView(BaseConversationResource):
    """对话列表资源"""

    def get(self, knowledge_base_id):
        """获取知识库的对话列表"""
        try:
            # 验证知识库存在
            knowledge_base, error_response = self._validate_knowledge_base_exists(knowledge_base_id)
            if error_response:
                return error_response

            # 查询参数
            page, per_page = self._get_page_params()
            search = request.args.get('search', '', type=str)
            status = request.args.get('status', '', type=str)
            sort_by, sort_order = self._get_sort_params('created_at', 'desc')

            # 使用对话服务获取列表
            service = get_conversation_service()
            conversations, total = service.get_conversations_by_knowledge_base(
                knowledge_base_id=knowledge_base_id,
                page=page,
                per_page=per_page,
                search=search if search else None,
                status=status if status else None,
                sort_by=sort_by,
                sort_order=sort_order
            )

            return self._format_response({
                'conversations': conversations,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                }
            })

        except Exception as e:
            return self._handle_service_error(e, "获取对话列表")

    def post(self, knowledge_base_id):
        """创建新对话"""
        try:
            # 验证知识库存在
            knowledge_base, error_response = self._validate_knowledge_base_exists(knowledge_base_id)
            if error_response:
                return error_response

            json_data = request.get_json()
            if not json_data:
                return self._format_response(
                    error="请求体不能为空",
                    status=400
                )

            # 创建对话
            service = get_conversation_service()
            conversation = service.create_conversation(
                knowledge_base_id=knowledge_base_id,
                title=json_data.get('title', '新对话'),
                initial_message=json_data.get('initial_message'),
                tags=json_data.get('tags', [])
            )

            return self._format_response(
                data=conversation,
                message="对话创建成功"
            )

        except Exception as e:
            return self._handle_service_error(e, "创建对话")


class ConversationDetailView(BaseConversationResource):
    """对话详情资源"""

    def get(self, knowledge_base_id, conversation_id):
        """获取对话详情"""
        try:
            # 验证知识库存在
            knowledge_base, error_response = self._validate_knowledge_base_exists(knowledge_base_id)
            if error_response:
                return error_response

            service = get_conversation_service()
            conversation = service.get_conversation(conversation_id)

            if not conversation:
                return self._format_response(
                    error="对话不存在",
                    status=404
                )

            # 验证对话属于该知识库
            if conversation.get('knowledge_base_id') != knowledge_base_id:
                return self._format_response(
                    error="对话不属于指定的知识库",
                    status=403
                )

            return self._format_response(
                data=conversation
            )

        except Exception as e:
            return self._handle_service_error(e, "获取对话详情")

    def put(self, knowledge_base_id, conversation_id):
        """更新对话"""
        try:
            # 验证知识库存在
            knowledge_base, error_response = self._validate_knowledge_base_exists(knowledge_base_id)
            if error_response:
                return error_response

            json_data = request.get_json()
            if not json_data:
                return self._format_response(
                    error="请求体不能为空",
                    status=400
                )

            service = get_conversation_service()

            # 验证对话存在并属于该知识库
            existing_conversation = service.get_conversation(conversation_id)
            if not existing_conversation:
                return self._format_response(
                    error="对话不存在",
                    status=404
                )

            if existing_conversation.get('knowledge_base_id') != knowledge_base_id:
                return self._format_response(
                    error="对话不属于指定的知识库",
                    status=403
                )

            conversation = service.update_conversation(
                conversation_id=conversation_id,
                title=json_data.get('title'),
                messages=json_data.get('messages'),
                tags=json_data.get('tags')
            )

            return self._format_response(
                data=conversation,
                message="对话更新成功"
            )

        except Exception as e:
            return self._handle_service_error(e, "更新对话")

    def delete(self, knowledge_base_id, conversation_id):
        """删除对话"""
        try:
            # 验证知识库存在
            knowledge_base, error_response = self._validate_knowledge_base_exists(knowledge_base_id)
            if error_response:
                return error_response

            service = get_conversation_service()

            # 验证对话存在并属于该知识库
            existing_conversation = service.get_conversation(conversation_id)
            if not existing_conversation:
                return self._format_response(
                    error="对话不存在",
                    status=404
                )

            if existing_conversation.get('knowledge_base_id') != knowledge_base_id:
                return self._format_response(
                    error="对话不属于指定的知识库",
                    status=403
                )

            success = service.delete_conversation(conversation_id)
            if not success:
                return self._format_response(
                    error="删除对话失败",
                    status=500
                )

            return self._format_response(
                message="对话删除成功"
            )

        except Exception as e:
            return self._handle_service_error(e, "删除对话")


class ConversationExportView(BaseConversationResource):
    """对话导出资源"""

    def get(self, knowledge_base_id, conversation_id):
        """导出对话"""
        try:
            # 验证知识库存在
            knowledge_base, error_response = self._validate_knowledge_base_exists(knowledge_base_id)
            if error_response:
                return error_response

            format_type = request.args.get('format', 'json')
            if format_type not in ['json', 'txt', 'csv', 'markdown']:
                return self._format_response(
                    error="不支持的导出格式",
                    status=400
                )

            service = get_conversation_service()

            # 验证对话存在并属于该知识库
            conversation = service.get_conversation(conversation_id)
            if not conversation:
                return self._format_response(
                    error="对话不存在",
                    status=404
                )

            if conversation.get('knowledge_base_id') != knowledge_base_id:
                return self._format_response(
                    error="对话不属于指定的知识库",
                    status=403
                )

            # 执行导出
            export_result = service.export_conversation(conversation_id, format_type)

            if format_type == 'json':
                return self._format_response(
                    data=export_result,
                    message=f"对话导出成功 (JSON格式)"
                )
            else:
                # 对于非JSON格式，返回文件下载
                return jsonify({
                    'download_url': export_result.get('download_url'),
                    'filename': export_result.get('filename'),
                    'format': format_type
                })

        except Exception as e:
            return self._handle_service_error(e, "导出对话")


class ConversationTemplateView(BaseConversationResource):
    """对话模板资源"""

    def get(self, knowledge_base_id):
        """获取对话模板列表"""
        try:
            # 验证知识库存在
            knowledge_base, error_response = self._validate_knowledge_base_exists(knowledge_base_id)
            if error_response:
                return error_response

            service = get_conversation_service()
            templates = service.get_conversation_templates(knowledge_base_id)

            return self._format_response(
                data=templates
            )

        except Exception as e:
            return self._handle_service_error(e, "获取对话模板")

    def post(self, knowledge_base_id):
        """保存对话为模板"""
        try:
            # 验证知识库存在
            knowledge_base, error_response = self._validate_knowledge_base_exists(knowledge_base_id)
            if error_response:
                return error_response

            json_data = request.get_json()
            if not json_data:
                return self._format_response(
                    error="请求体不能为空",
                    status=400
                )

            conversation_id = json_data.get('conversation_id')
            template_name = json_data.get('template_name')
            description = json_data.get('description', '')

            if not conversation_id or not template_name:
                return self._format_response(
                    error="缺少对话ID或模板名称",
                    status=400
                )

            service = get_conversation_service()
            template = service.save_conversation_as_template(
                conversation_id=conversation_id,
                template_name=template_name,
                description=description
            )

            return self._format_response(
                data=template,
                message="对话模板保存成功"
            )

        except Exception as e:
            return self._handle_service_error(e, "保存对话模板")