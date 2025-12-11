#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
知识库API模块

提供模块化的知识库管理API接口
"""

# 导入基础资源类
from .views.base import BaseKnowledgeBaseResource, BaseDocumentResource, BaseConversationResource

# 导入知识库相关视图
from .views.knowledge_base_views import (
    KnowledgeBaseListView,
    KnowledgeBaseDetailView,
    KnowledgeBaseStatisticsView
)

# 导入文档相关视图
from .views.document_views import (
    DocumentListView,
    DocumentDetailView,
    DocumentUploadView,
    DocumentChunksView
)

# 导入对话相关视图
from .views.conversation_views import (
    ConversationListView,
    ConversationDetailView,
    ConversationExportView,
    ConversationTemplateView
)

# 导入分析相关视图
from .views.analytics_views import (
    SearchAnalyticsView,
    EnhancedSearchAnalyticsView,
    SearchInsightsView,
    PopularTermsView,
    EnhancedStatisticsView,
    TopActiveKnowledgeBasesView
)

# 导入聊天助手相关视图
from .views.chat_assistant_views import (
    RAGFlowChatAssistantListView,
    RAGFlowChatAssistantInteractionView,
    RAGFlowAgentListView,
    RAGFlowAgentInteractionView,
    RAGFlowChatSessionListView,
    RAGFlowRetrievalView
)

# 导出所有资源类以供注册
__all__ = [
    # 基础类
    'BaseKnowledgeBaseResource',
    'BaseDocumentResource',
    'BaseConversationResource',

    # 知识库资源
    'KnowledgeBaseListView',
    'KnowledgeBaseDetailView',
    'KnowledgeBaseStatisticsView',

    # 文档资源
    'DocumentListView',
    'DocumentDetailView',
    'DocumentUploadView',
    'DocumentChunksView',

    # 对话资源
    'ConversationListView',
    'ConversationDetailView',
    'ConversationExportView',
    'ConversationTemplateView',

    # 分析资源
    'SearchAnalyticsView',
    'EnhancedSearchAnalyticsView',
    'SearchInsightsView',
    'PopularTermsView',
    'EnhancedStatisticsView',
    'TopActiveKnowledgeBasesView',

    # 聊天助手资源
    'RAGFlowChatAssistantListView',
    'RAGFlowChatAssistantInteractionView',
    'RAGFlowAgentListView',
    'RAGFlowAgentInteractionView',
    'RAGFlowChatSessionListView',
    'RAGFlowRetrievalView',
]