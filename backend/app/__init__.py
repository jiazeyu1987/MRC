from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_restful import Api
import logging
import os

db = SQLAlchemy()
migrate = Migrate()
cors = CORS()


def create_app(config_name=None):
    """应用工厂函数"""
    app = Flask(__name__)

    # 加载配置
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV') or 'default'

    from app.config import config
    app.config.from_object(config[config_name])

    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app, resources={
        r"/api/*": {
            "origins": "*",  # 开发环境允许所有来源，生产环境需要限制
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    # 配置日志
    setup_logging(app)

    # 初始化监控系统
    init_system_monitoring(app)

    # 注册蓝图和API资源
    register_api(app)

    # 注册错误处理器
    register_error_handlers(app)

    # 注册Shell上下文处理器
    register_shell_context(app)

    return app


def setup_logging(app):
    """配置日志"""
    # 检查是否启用文件日志（通过环境变量或配置）
    enable_file_logging = os.environ.get('LOG_TO_FILE', 'true').lower() == 'true'

    # 移除debug模式限制，让开发环境也支持文件日志
    if enable_file_logging and not app.testing:
        # 确保日志目录存在
        log_dir = os.path.dirname(app.config['LOG_FILE'])
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # 配置文件日志
        file_handler = logging.FileHandler(app.config['LOG_FILE'], encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(getattr(logging, app.config['LOG_LEVEL']))
        app.logger.addHandler(file_handler)

        app.logger.setLevel(getattr(logging, app.config['LOG_LEVEL']))
        app.logger.info('MultiRoleChat startup - File logging enabled')

    # 控制台日志始终启用
    if app.debug:
        app.logger.info('MultiRoleChat startup - Debug mode enabled')


def register_api(app):
    """注册API资源和蓝图"""
    api = Api(app)

    # 导入并注册API资源
    from app.api.roles import RoleList, RoleDetail
    from app.api.flows import FlowList, FlowDetail, FlowCopy, FlowStatistics, FlowClearAll
    from app.api.sessions import SessionList, SessionDetail, SessionExecution, SessionControl, SessionBranch, SessionStatistics, LLMDebugInfo
    from app.api.messages import MessageList, MessageDetail, MessageExport, MessageReplies, MessageStatistics, MessageFlow, MessageSearch
    from app.api.knowledge_bases import (KnowledgeBaseListView, KnowledgeBaseDetailView,
                                        KnowledgeBaseStatisticsView, ConversationDetailView,
                                        DocumentListView, DocumentDetailView, DocumentUploadView,
                                        DocumentChunksView, ConversationListView, ConversationExportView,
                                        ConversationTemplateView, SearchAnalyticsView, SearchInsightsView,
                                        PopularTermsView, EnhancedStatisticsView, TopActiveKnowledgeBasesView,
                                        EnhancedSearchAnalyticsView, RAGFlowChatAssistantListView,
                                        RAGFlowChatAssistantInteractionView, RAGFlowAgentListView,
                                        RAGFlowAgentInteractionView, RAGFlowChatSessionListView,
                                        RAGFlowRetrievalView)
    from app.api.monitoring import (SystemHealth, PerformanceMetrics, PerformanceHistory,
                                  PerformanceSummary, HealthHistory, ComponentHealthTrend,
                                  SystemInfo, MonitoringAlerts, MonitoringControl, MonitoringDashboard)

    # 角色管理接口
    api.add_resource(RoleList, '/api/roles')
    api.add_resource(RoleDetail, '/api/roles/<int:role_id>')

    # 流程模板接口
    api.add_resource(FlowList, '/api/flows')
    api.add_resource(FlowDetail, '/api/flows/<int:flow_id>')
    api.add_resource(FlowCopy, '/api/flows/<int:flow_id>/copy')
    api.add_resource(FlowStatistics, '/api/flows/statistics')
    api.add_resource(FlowClearAll, '/api/flows/clear-all')

    # 会话管理接口
    api.add_resource(SessionList, '/api/sessions')
    api.add_resource(SessionDetail, '/api/sessions/<int:session_id>')
    api.add_resource(SessionExecution, '/api/sessions/<int:session_id>/run-next-step')
    api.add_resource(SessionControl, '/api/sessions/<int:session_id>/control')
    api.add_resource(SessionBranch, '/api/sessions/<int:session_id>/branch')
    api.add_resource(SessionStatistics, '/api/sessions/statistics')

    # LLM调试接口
    api.add_resource(LLMDebugInfo, '/api/llm/debug')

    # 消息管理接口
    api.add_resource(MessageList, '/api/sessions/<int:session_id>/messages')
    api.add_resource(MessageDetail, '/api/sessions/<int:session_id>/messages/<int:message_id>')
    api.add_resource(MessageReplies, '/api/sessions/<int:session_id>/messages/<int:message_id>/replies')
    api.add_resource(MessageExport, '/api/sessions/<int:session_id>/export')
    api.add_resource(MessageFlow, '/api/sessions/<int:session_id>/flow')
    api.add_resource(MessageSearch, '/api/messages/search')

    # 消息统计接口
    from app.api.messages import MessageStatistics, SessionMessageStatistics
    api.add_resource(MessageStatistics, '/api/messages/statistics')
    api.add_resource(SessionMessageStatistics, '/api/sessions/<int:session_id>/messages/statistics')

    # 监控和健康检查接口
    api.add_resource(SystemHealth, '/api/health')
    api.add_resource(PerformanceMetrics, '/api/monitoring/metrics')
    api.add_resource(PerformanceHistory, '/api/monitoring/history')
    api.add_resource(PerformanceSummary, '/api/monitoring/summary')
    api.add_resource(HealthHistory, '/api/monitoring/health-history')
    api.add_resource(ComponentHealthTrend, '/api/monitoring/health-trend/<string:component>')
    api.add_resource(SystemInfo, '/api/monitoring/system-info')
    api.add_resource(MonitoringAlerts, '/api/monitoring/alerts')
    api.add_resource(MonitoringControl, '/api/monitoring/control')
    api.add_resource(MonitoringDashboard, '/api/monitoring/dashboard')

    # LLM对话接口
    from app.api.llm import register_llm_routes
    register_llm_routes(api)

    # 知识库管理接口
    api.add_resource(KnowledgeBaseListView, '/api/knowledge-bases')
    api.add_resource(KnowledgeBaseDetailView, '/api/knowledge-bases/<int:knowledge_base_id>')
    api.add_resource(KnowledgeBaseStatisticsView, '/api/knowledge-bases/<int:knowledge_base_id>/statistics')
    api.add_resource(ConversationDetailView, '/api/knowledge-bases/<int:knowledge_base_id>/conversations/<int:conversation_id>')

    # 文档管理接口
    api.add_resource(DocumentListView, '/api/knowledge-bases/<int:knowledge_base_id>/documents')
    api.add_resource(DocumentDetailView, '/api/knowledge-bases/<int:knowledge_base_id>/documents/<int:document_id>')
    api.add_resource(DocumentUploadView, '/api/knowledge-bases/<int:knowledge_base_id>/documents/upload')
    api.add_resource(DocumentChunksView, '/api/knowledge-bases/<int:knowledge_base_id>/documents/<int:document_id>/chunks')

    # RAGFlow文档管理接口 (使用字符串文档ID)
    # TODO: 需要重新实现RAGFlow文档管理功能
    # from app.api.knowledge_bases import RAGFlowDocumentResource, RAGFlowDocumentChunksResource
    # api.add_resource(RAGFlowDocumentResource, '/api/knowledge-bases/<int:knowledge_base_id>/ragflow-documents/<string:document_id>')
    # api.add_resource(RAGFlowDocumentChunksResource, '/api/knowledge-bases/<int:knowledge_base_id>/ragflow-documents/<string:document_id>/chunks')

    # 增强功能接口 - 对话历史和管理
    api.add_resource(ConversationListView, '/api/knowledge-bases/<int:knowledge_base_id>/conversations')
    # ConversationDetailView 已在第156行注册，避免重复
    api.add_resource(ConversationExportView, '/api/knowledge-bases/<int:knowledge_base_id>/conversations/<int:conversation_id>/export')
    api.add_resource(ConversationTemplateView, '/api/conversation-templates')

    # 增强功能接口 - 搜索分析和洞察
    api.add_resource(SearchAnalyticsView, '/api/knowledge-bases/<int:knowledge_base_id>/search-analytics')
    api.add_resource(SearchInsightsView, '/api/knowledge-bases/<int:knowledge_base_id>/search-insights')
    api.add_resource(PopularTermsView, '/api/knowledge-bases/<int:knowledge_base_id>/popular-terms')

    # 增强功能接口 - 统计和排行
    api.add_resource(EnhancedStatisticsView, '/api/knowledge-bases/<int:knowledge_base_id>/enhanced-statistics')
    api.add_resource(TopActiveKnowledgeBasesView, '/api/knowledge-bases/top-active')

    # 增强功能接口 - API文档和游乐场
    # TODO: 重新实现API文档功能
    # from app.api.knowledge_bases import (
    #     APIDocumentationResource, APIPlaygroundResource, APIRateLimitResource
    # )
    # api.add_resource(APIDocumentationResource, '/api/api-documentation')
    # api.add_resource(APIPlaygroundResource, '/api/api-playground')
    # api.add_resource(APIRateLimitResource, '/api/api-rate-limit')

    # RAGFlow聊天助手和智能体接口
    api.add_resource(RAGFlowChatAssistantListView, '/api/ragflow/chats')
    api.add_resource(RAGFlowChatAssistantInteractionView, '/api/ragflow/chats/<string:chat_id>')
    api.add_resource(RAGFlowChatSessionListView, '/api/ragflow/chats/<string:chat_id>/sessions')
    api.add_resource(RAGFlowAgentListView, '/api/ragflow/agents')
    api.add_resource(RAGFlowAgentInteractionView, '/api/ragflow/agents/<string:agent_id>')
    api.add_resource(RAGFlowRetrievalView, '/api/ragflow/retrieval')

    # LLM文件记录接口
    from app.api.llm_file_records import llm_file_records_bp
    app.register_blueprint(llm_file_records_bp)

    # RAGFlow 对话管理接口 (临时注释，等待实现)
    # from app.api.ragflow_chat import (
    #     ChatAssistantListResource, ChatAssistantResource,
    #     ChatSessionListResource, ChatSessionResource,
    #     ChatCompletionResource, ChatStatisticsResource, RetrievalResource
    # )
    # api.add_resource(ChatAssistantListResource, '/api/v1/chats')
    # api.add_resource(ChatAssistantResource, '/api/v1/chats/<string:chat_id>')
    # api.add_resource(ChatSessionListResource, '/api/v1/chats/<string:chat_id>/sessions')
    # api.add_resource(ChatSessionResource, '/api/v1/chats/<string:chat_id>/sessions/<string:session_id>')
    # api.add_resource(ChatCompletionResource, '/api/v1/chats/<string:chat_id>/completions')
    # api.add_resource(ChatStatisticsResource, '/api/v1/chats/statistics')
    # api.add_resource(ChatStatisticsResource, '/api/v1/chats/<string:chat_id>/statistics')
    # api.add_resource(RetrievalResource, '/api/v1/retrieval')


def register_error_handlers(app):
    """注册错误处理器"""
    from flask import jsonify

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'success': False,
            'error_code': 'BAD_REQUEST',
            'message': '请求参数错误'
        }), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error_code': 'NOT_FOUND',
            'message': '资源未找到'
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({
            'success': False,
            'error_code': 'INTERNAL_ERROR',
            'message': '服务器内部错误'
        }), 500


def init_system_monitoring(app):
    """初始化监控系统"""
    try:
        from app.utils.monitoring import init_monitoring
        return init_monitoring(app)
    except Exception as e:
        app.logger.error(f"监控系统初始化失败: {str(e)}")
        # 监控系统初始化失败不应该阻止应用启动
        pass


def register_shell_context(app):
    """注册Shell上下文处理器"""
    @app.shell_context_processor
    def make_shell_context():
        from app.models import Role, FlowTemplate, FlowStep, Session, SessionRole, Message
        return {
            'db': db,
            'Role': Role,
            'FlowTemplate': FlowTemplate,
            'FlowStep': FlowStep,
            'Session': Session,
            'SessionRole': SessionRole,
            'Message': Message
        }
