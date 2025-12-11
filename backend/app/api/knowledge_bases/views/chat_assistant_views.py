#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
聊天助手视图

提供RAGFlow聊天助手的管理和交互功能
"""

from flask import request, current_app
from .base import BaseKnowledgeBaseResource
from datetime import datetime


class RAGFlowChatAssistantListView(BaseKnowledgeBaseResource):
    """RAGFlow聊天助手列表资源"""

    def get(self):
        """获取RAGFlow聊天助手列表"""
        try:
            current_app.logger.info("开始获取RAGFlow聊天助手列表")

            # 使用RAGFlow服务获取聊天助手列表
            chat_assistants = self.ragflow_service.list_chats()

            current_app.logger.info(f"成功获取 {len(chat_assistants)} 个聊天助手")

            return self._format_response(
                data=chat_assistants,
                message=f"获取到 {len(chat_assistants)} 个聊天助手"
            )

        except Exception as e:
            return self._handle_service_error(e, "获取RAGFlow聊天助手列表")


class RAGFlowChatAssistantInteractionView(BaseKnowledgeBaseResource):
    """RAGFlow聊天助手交互资源"""

    def post(self, chat_id):
        """与聊天助手对话"""
        try:
            data = request.get_json() or {}
            message = data.get('message', '')
            conversation_id = data.get('conversation_id')
            session_id = data.get('session_id')

            if not message:
                return self._format_response(
                    error="消息内容不能为空",
                    status=400
                )

            current_app.logger.info(f"与聊天助手 {chat_id} 对话: {message[:50]}...")

            # 使用RAGFlow服务进行对话
            response = self.ragflow_service.chat_with_assistant(
                chat_id=chat_id,
                message=message,
                conversation_id=conversation_id,
                session_id=session_id
            )

            return self._format_response(
                data={
                    'chat_id': chat_id,
                    'message': message,
                    'response': response,
                    'conversation_id': conversation_id,
                    'session_id': session_id,
                    'timestamp': datetime.utcnow().isoformat()
                },
                message="对话成功"
            )

        except Exception as e:
            return self._handle_service_error(e, "与聊天助手对话")

    def get(self, chat_id):
        """获取聊天助手对话历史"""
        try:
            # 查询参数
            limit = min(request.args.get('limit', 20, type=int), 100)
            session_id = request.args.get('session_id')

            # 获取对话历史
            conversation_history = self.ragflow_service.get_chat_history(
                chat_id=chat_id,
                limit=limit,
                session_id=session_id
            )

            return self._format_response(
                data=conversation_history,
                message=f"获取到 {len(conversation_history.get('messages', []))} 条历史消息"
            )

        except Exception as e:
            return self._handle_service_error(e, "获取对话历史")


class RAGFlowAgentListView(BaseKnowledgeBaseResource):
    """RAGFlow智能体列表资源"""

    def get(self):
        """获取RAGFlow智能体列表"""
        try:
            current_app.logger.info("开始获取RAGFlow智能体列表")

            # 使用RAGFlow服务获取智能体列表
            agents = self.ragflow_service.list_agents()

            current_app.logger.info(f"成功获取 {len(agents)} 个智能体")

            return self._format_response(
                data=agents,
                message=f"获取到 {len(agents)} 个智能体"
            )

        except Exception as e:
            return self._handle_service_error(e, "获取RAGFlow智能体列表")


class RAGFlowAgentInteractionView(BaseKnowledgeBaseResource):
    """RAGFlow智能体交互资源"""

    def post(self, agent_id):
        """与智能体对话"""
        try:
            data = request.get_json() or {}
            message = data.get('message', '')
            conversation_id = data.get('conversation_id')

            if not message:
                return self._format_response(
                    error="消息内容不能为空",
                    status=400
                )

            current_app.logger.info(f"与智能体 {agent_id} 对话: {message[:50]}...")

            # 使用RAGFlow服务进行对话
            response = self.ragflow_service.chat_with_agent(
                agent_id=agent_id,
                message=message,
                conversation_id=conversation_id
            )

            return self._format_response(
                data={
                    'agent_id': agent_id,
                    'message': message,
                    'response': response,
                    'conversation_id': conversation_id,
                    'timestamp': datetime.utcnow().isoformat()
                },
                message="智能体对话成功"
            )

        except Exception as e:
            return self._handle_service_error(e, "与智能体对话")


class RAGFlowChatSessionListView(BaseKnowledgeBaseResource):
    """RAGFlow聊天会话列表资源"""

    def get(self):
        """获取聊天会话列表"""
        try:
            # 查询参数
            limit = min(request.args.get('limit', 20, type=int), 100)
            status = request.args.get('status', 'all')

            # 获取聊天会话列表
            sessions = self.ragflow_service.list_chat_sessions(
                limit=limit,
                status=status
            )

            return self._format_response(
                data=sessions,
                message=f"获取到 {len(sessions)} 个聊天会话"
            )

        except Exception as e:
            return self._handle_service_error(e, "获取聊天会话列表")

    def post(self):
        """创建新的聊天会话"""
        try:
            data = request.get_json() or {}
            chat_id = data.get('chat_id')
            title = data.get('title', '新会话')

            if not chat_id:
                return self._format_response(
                    error="缺少聊天助手ID",
                    status=400
                )

            # 创建新会话
            session = self.ragflow_service.create_chat_session(
                chat_id=chat_id,
                title=title
            )

            return self._format_response(
                data=session,
                message="聊天会话创建成功"
            )

        except Exception as e:
            return self._handle_service_error(e, "创建聊天会话")


class RAGFlowRetrievalView(BaseKnowledgeBaseResource):
    """RAGFlow检索测试资源"""

    def post(self, knowledge_base_id):
        """执行检索测试"""
        try:
            # 验证知识库存在
            knowledge_base, error_response = self._validate_knowledge_base_exists(knowledge_base_id)
            if error_response:
                return error_response

            data = request.get_json() or {}
            query = data.get('query', '')
            top_k = min(data.get('top_k', 5), 20)
            retrieval_mode = data.get('retrieval_mode', 'vector')

            if not query:
                return self._format_response(
                    error="查询内容不能为空",
                    status=400
                )

            # 执行检索
            retrieval_result = self.ragflow_service.test_retrieval(
                dataset_id=knowledge_base.ragflow_dataset_id,
                query=query,
                top_k=top_k,
                retrieval_mode=retrieval_mode
            )

            return self._format_response(
                data=retrieval_result,
                message="检索测试完成"
            )

        except Exception as e:
            return self._handle_service_error(e, "执行检索测试")