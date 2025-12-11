#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
知识库API路由配置

提供新模块化API的路由注册，保持与原有API的兼容性
"""

from flask import Blueprint
from . import (
    # 知识库资源
    KnowledgeBaseListView,
    KnowledgeBaseDetailView,
    KnowledgeBaseStatisticsView,

    # 文档资源
    DocumentListView,
    DocumentDetailView,
    DocumentUploadView,
    DocumentChunksView,

    # 对话资源
    ConversationListView,
    ConversationDetailView,
    ConversationExportView,
    ConversationTemplateView,

    # 分析资源
    SearchAnalyticsView,
    EnhancedSearchAnalyticsView,
    SearchInsightsView,
    PopularTermsView,
    EnhancedStatisticsView,
    TopActiveKnowledgeBasesView,

    # 聊天助手资源
    RAGFlowChatAssistantListView,
    RAGFlowChatAssistantInteractionView,
    RAGFlowAgentListView,
    RAGFlowAgentInteractionView,
    RAGFlowChatSessionListView,
    RAGFlowRetrievalView
)

# 创建蓝图
knowledge_bases_bp = Blueprint('knowledge_bases_v2', __name__, url_prefix='/api/knowledge-bases-v2')


def register_knowledge_base_routes(app):
    """注册知识库API路由到Flask应用"""

    # === 知识库相关路由 ===
    # GET /api/knowledge-bases-v2 - 获取知识库列表
    # POST /api/knowledge-bases-v2 - 执行知识库操作（刷新等）
    app.add_url_rule(
        '/api/knowledge-bases-v2',
        view_func=KnowledgeBaseListView.as_view('knowledge_base_list_v2'),
        methods=['GET', 'POST']
    )

    # GET /api/knowledge-bases-v2/<int:knowledge_base_id> - 获取知识库详情
    # POST /api/knowledge-bases-v2/<int:knowledge_base_id> - 测试知识库对话
    # DELETE /api/knowledge-bases-v2/<int:knowledge_base_id> - 删除知识库
    app.add_url_rule(
        '/api/knowledge-bases-v2/<int:knowledge_base_id>',
        view_func=KnowledgeBaseDetailView.as_view('knowledge_base_detail_v2'),
        methods=['GET', 'POST', 'DELETE']
    )

    # GET /api/knowledge-bases-v2/<int:knowledge_base_id>/statistics - 获取知识库统计信息
    app.add_url_rule(
        '/api/knowledge-bases-v2/<int:knowledge_base_id>/statistics',
        view_func=KnowledgeBaseStatisticsView.as_view('knowledge_base_statistics_v2'),
        methods=['GET']
    )

    # === 文档相关路由 ===
    # GET /api/knowledge-bases-v2/<int:knowledge_base_id>/documents - 获取文档列表
    # POST /api/knowledge-bases-v2/<int:knowledge_base_id>/documents - 上传文档
    app.add_url_rule(
        '/api/knowledge-bases-v2/<int:knowledge_base_id>/documents',
        view_func=DocumentListView.as_view('document_list_v2'),
        methods=['GET', 'POST']
    )

    # GET /api/knowledge-bases-v2/<int:knowledge_base_id>/documents/<int:document_id> - 获取文档详情
    # DELETE /api/knowledge-bases-v2/<int:knowledge_base_id>/documents/<int:document_id> - 删除文档
    app.add_url_rule(
        '/api/knowledge-bases-v2/<int:knowledge_base_id>/documents/<int:document_id>',
        view_func=DocumentDetailView.as_view('document_detail_v2'),
        methods=['GET', 'DELETE']
    )

    # POST /api/knowledge-bases-v2/<int:knowledge_base_id>/documents/upload - 增强版文档上传
    app.add_url_rule(
        '/api/knowledge-bases-v2/<int:knowledge_base_id>/documents/upload',
        view_func=DocumentUploadView.as_view('document_upload_v2'),
        methods=['POST']
    )

    # GET /api/knowledge-bases-v2/<int:knowledge_base_id>/documents/<int:document_id>/chunks - 获取文档块
    # POST /api/knowledge-bases-v2/<int:knowledge_base_id>/documents/<int:document_id>/chunks - 重新处理文档块
    app.add_url_rule(
        '/api/knowledge-bases-v2/<int:knowledge_base_id>/documents/<int:document_id>/chunks',
        view_func=DocumentChunksView.as_view('document_chunks_v2'),
        methods=['GET', 'POST']
    )

    # === 对话相关路由 ===
    # GET /api/knowledge-bases-v2/<int:knowledge_base_id>/conversations - 获取对话列表
    # POST /api/knowledge-bases-v2/<int:knowledge_base_id>/conversations - 创建新对话
    app.add_url_rule(
        '/api/knowledge-bases-v2/<int:knowledge_base_id>/conversations',
        view_func=ConversationListView.as_view('conversation_list_v2'),
        methods=['GET', 'POST']
    )

    # GET /api/knowledge-bases-v2/<int:knowledge_base_id>/conversations/<int:conversation_id> - 获取对话详情
    # PUT /api/knowledge-bases-v2/<int:knowledge_base_id>/conversations/<int:conversation_id> - 更新对话
    # DELETE /api/knowledge-bases-v2/<int:knowledge_base_id>/conversations/<int:conversation_id> - 删除对话
    app.add_url_rule(
        '/api/knowledge-bases-v2/<int:knowledge_base_id>/conversations/<int:conversation_id>',
        view_func=ConversationDetailView.as_view('conversation_detail_v2'),
        methods=['GET', 'PUT', 'DELETE']
    )

    # GET /api/knowledge-bases-v2/<int:knowledge_base_id>/conversations/<int:conversation_id>/export - 导出对话
    app.add_url_rule(
        '/api/knowledge-bases-v2/<int:knowledge_base_id>/conversations/<int:conversation_id>/export',
        view_func=ConversationExportView.as_view('conversation_export_v2'),
        methods=['GET']
    )

    # GET /api/knowledge-bases-v2/<int:knowledge_base_id>/conversation-templates - 获取对话模板
    # POST /api/knowledge-bases-v2/<int:knowledge_base_id>/conversation-templates - 保存对话模板
    app.add_url_rule(
        '/api/knowledge-bases-v2/<int:knowledge_base_id>/conversation-templates',
        view_func=ConversationTemplateView.as_view('conversation_templates_v2'),
        methods=['GET', 'POST']
    )

    # === 分析相关路由 ===
    # GET /api/knowledge-bases-v2/<int:knowledge_base_id>/analytics/search - 搜索分析
    app.add_url_rule(
        '/api/knowledge-bases-v2/<int:knowledge_base_id>/analytics/search',
        view_func=SearchAnalyticsView.as_view('search_analytics_v2'),
        methods=['GET']
    )

    # GET /api/knowledge-bases-v2/<int:knowledge_base_id>/analytics/enhanced - 增强分析
    app.add_url_rule(
        '/api/knowledge-bases-v2/<int:knowledge_base_id>/analytics/enhanced',
        view_func=EnhancedSearchAnalyticsView.as_view('enhanced_search_analytics_v2'),
        methods=['GET']
    )

    # GET /api/knowledge-bases-v2/<int:knowledge_base_id>/analytics/insights - 搜索洞察
    app.add_url_rule(
        '/api/knowledge-bases-v2/<int:knowledge_base_id>/analytics/insights',
        view_func=SearchInsightsView.as_view('search_insights_v2'),
        methods=['GET']
    )

    # GET /api/knowledge-bases-v2/<int:knowledge_base_id>/analytics/popular-terms - 热门术语
    app.add_url_rule(
        '/api/knowledge-bases-v2/<int:knowledge_base_id>/analytics/popular-terms',
        view_func=PopularTermsView.as_view('popular_terms_v2'),
        methods=['GET']
    )

    # GET /api/knowledge-bases-v2/<int:knowledge_base_id>/analytics/enhanced-stats - 增强统计
    app.add_url_rule(
        '/api/knowledge-bases-v2/<int:knowledge_base_id>/analytics/enhanced-stats',
        view_func=EnhancedStatisticsView.as_view('enhanced_statistics_v2'),
        methods=['GET']
    )

    # GET /api/knowledge-bases-v2/analytics/top-knowledge-bases - 活跃知识库排行
    app.add_url_rule(
        '/api/knowledge-bases-v2/analytics/top-knowledge-bases',
        view_func=TopActiveKnowledgeBasesView.as_view('top_knowledge_bases_v2'),
        methods=['GET']
    )

    # === 聊天助手相关路由 ===
    # GET /api/knowledge-bases-v2/chat/assistants - 获取聊天助手列表
    app.add_url_rule(
        '/api/knowledge-bases-v2/chat/assistants',
        view_func=RAGFlowChatAssistantListView.as_view('chat_assistants_v2'),
        methods=['GET']
    )

    # POST /api/knowledge-bases-v2/chat/assistants/<chat_id>/interact - 与聊天助手对话
    # GET /api/knowledge-bases-v2/chat/assistants/<chat_id>/interact - 获取对话历史
    app.add_url_rule(
        '/api/knowledge-bases-v2/chat/assistants/<chat_id>/interact',
        view_func=RAGFlowChatAssistantInteractionView.as_view('chat_assistant_interaction_v2'),
        methods=['GET', 'POST']
    )

    # GET /api/knowledge-bases-v2/chat/agents - 获取智能体列表
    app.add_url_rule(
        '/api/knowledge-bases-v2/chat/agents',
        view_func=RAGFlowAgentListView.as_view('chat_agents_v2'),
        methods=['GET']
    )

    # POST /api/knowledge-bases-v2/chat/agents/<agent_id>/interact - 与智能体对话
    app.add_url_rule(
        '/api/knowledge-bases-v2/chat/agents/<agent_id>/interact',
        view_func=RAGFlowAgentInteractionView.as_view('chat_agent_interaction_v2'),
        methods=['POST']
    )

    # GET /api/knowledge-bases-v2/chat/sessions - 获取聊天会话列表
    # POST /api/knowledge-bases-v2/chat/sessions - 创建新聊天会话
    app.add_url_rule(
        '/api/knowledge-bases-v2/chat/sessions',
        view_func=RAGFlowChatSessionListView.as_view('chat_sessions_v2'),
        methods=['GET', 'POST']
    )

    # POST /api/knowledge-bases-v2/<int:knowledge_base_id>/retrieval - 检索测试
    app.add_url_rule(
        '/api/knowledge-bases-v2/<int:knowledge_base_id>/retrieval',
        view_func=RAGFlowRetrievalView.as_view('ragflow_retrieval_v2'),
        methods=['POST']
    )


def register_blueprint(app):
    """注册知识库蓝图到Flask应用"""
    app.register_blueprint(knowledge_bases_bp)