import React, { useState, useEffect } from 'react';
import {
  Database,
  FileText,
  Calendar,
  AlertTriangle,
  CheckCircle,
  XCircle,
  MessageCircle,
  HardDrive,
  Clock,
  User,
  Search,
  Send,
  Loader2,
  RefreshCw,
  ExternalLink,
  Upload,
  List,
  Eye,
  FolderOpen,
  FileUp,
  MessageSquare,
  BarChart3,
  BookOpen,
  Filter,
  Download,
  Archive,
  Settings,
  Code,
  TrendingUp,
  Users,
  Activity,
  FileSearch,
  Terminal,
  Plus,
  ChevronRight
} from 'lucide-react';
import { useTheme } from '../theme';
import { knowledgeApi } from '../api/knowledgeApi';
import { enhancedApi } from '../api';
import { KnowledgeBase, KnowledgeBaseConversation } from '../types/knowledge';
import { Document } from '../types/document';
import { handleError } from '../utils/errorHandler';
import DocumentUpload from './DocumentUpload';
import DocumentList from './DocumentList';
import DocumentView from './DocumentView';

// Import our enhanced components
import ConversationInterface from './conversation/ConversationInterface';
import SearchAnalyticsDashboard from './search/SearchAnalyticsDashboard';
import APIDocumentationView from './api/APIDocumentationView';

interface EnhancedKnowledgeBaseDetailsProps {
  knowledgeBaseId: number;
  onBack?: () => void;
  onTestConversation?: (conversation: KnowledgeBaseConversation) => void;
}

const EnhancedKnowledgeBaseDetails: React.FC<EnhancedKnowledgeBaseDetailsProps> = ({
  knowledgeBaseId,
  onBack,
  onTestConversation
}) => {
  const { theme } = useTheme();
  const [knowledgeBase, setKnowledgeBase] = useState<KnowledgeBase | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Enhanced features state
  const [activeTab, setActiveTab] = useState<'overview' | 'documents' | 'conversations' | 'search-analytics' | 'api-docs'>('overview');
  const [testQuestion, setTestQuestion] = useState<string>('');
  const [testingConversation, setTestingConversation] = useState<boolean>(false);
  const [enhancedStats, setEnhancedStats] = useState<any>(null);
  const [searchStats, setSearchStats] = useState<any>(null);
  const [activeConversations, setActiveConversations] = useState<number>(0);

  // 加载知识库详情
  const loadKnowledgeBaseDetails = async () => {
    try {
      setLoading(true);
      setError(null);

      const details = await knowledgeApi.getKnowledgeBaseDetails(knowledgeBaseId);
      setKnowledgeBase(details);

      // Load enhanced statistics
      try {
        const [stats, searchData] = await Promise.all([
          enhancedApi.enhancedStatistics.getEnhancedStatistics(knowledgeBaseId, 7),
          enhancedApi.searchAnalytics.getSearchAnalytics(knowledgeBaseId, 7)
        ]);
        setEnhancedStats(stats);
        setSearchStats(searchData);
        setActiveConversations(stats?.knowledge_base?.conversation_count || 0);
      } catch (statsError) {
        console.warn('Failed to load enhanced statistics:', statsError);
      }

    } catch (err) {
      setError(handleError(err));
    } finally {
      setLoading(false);
    }
  };

  // 刷新数据
  const handleRefresh = async () => {
    setRefreshing(true);
    await loadKnowledgeBaseDetails();
    setRefreshing(false);
  };

  // 测试对话
  const handleTestConversation = async () => {
    if (!testQuestion.trim() || testingConversation) return;

    setTestingConversation(true);
    try {
      const conversation = await knowledgeApi.testConversation(knowledgeBaseId, {
        action: 'test_conversation',
        question: testQuestion,
        title: `测试对话 - ${testQuestion.slice(0, 30)}`
      });

      if (onTestConversation) {
        onTestConversation(conversation);
      }

      setTestQuestion('');
    } catch (err) {
      setError(handleError(err));
    } finally {
      setTestingConversation(false);
    }
  };

  // 格式化日期
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('zh-CN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // 获取状态信息
  const getStatusInfo = (status: string) => {
    switch (status) {
      case 'active':
        return {
          icon: CheckCircle,
          color: 'text-green-500',
          bgColor: 'bg-green-100',
          text: '活跃'
        };
      case 'inactive':
        return {
          icon: XCircle,
          color: 'text-gray-500',
          bgColor: 'bg-gray-100',
          text: '未激活'
        };
      case 'error':
        return {
          icon: AlertTriangle,
          color: 'text-red-500',
          bgColor: 'bg-red-100',
          text: '错误'
        };
      default:
        return {
          icon: AlertTriangle,
          color: 'text-gray-500',
          bgColor: 'bg-gray-100',
          text: status
        };
    }
  };

  // 组件加载时获取数据
  useEffect(() => {
    if (knowledgeBaseId) {
      loadKnowledgeBaseDetails();
    }
  }, [knowledgeBaseId]);

  // 状态图标组件
  const StatusIcon = ({ status }: { status: string }) => {
    const statusInfo = getStatusInfo(status);
    const Icon = statusInfo.icon;
    return (
      <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${statusInfo.bgColor} ${statusInfo.color}`}>
        <Icon className="w-4 h-4 mr-2" />
        {statusInfo.text}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        <div className="text-center">
          <Loader2 className="w-8 h-8 mx-auto animate-spin text-blue-500 mb-4" />
          <p className="text-gray-500">加载知识库详情中...</p>
        </div>
      </div>
    );
  }

  if (error || !knowledgeBase) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        <div className="text-center">
          <AlertTriangle className="w-12 h-12 mx-auto text-red-500 mb-4" />
          <p className="text-red-600 mb-4">{error || '知识库不存在'}</p>
          {onBack && (
            <button
              onClick={onBack}
              className={`px-4 py-2 text-sm font-medium text-white rounded-md ${theme.primary} ${theme.primaryHover} transition-colors`}
            >
              返回列表
            </button>
          )}
        </div>
      </div>
    );
  }

  const hasNoDocuments = knowledgeBase.document_count === 0;

  // 标签页配置
  const tabs = [
    { id: 'overview', label: '概览', icon: Database },
    { id: 'documents', label: '文档管理', icon: FileText },
    { id: 'conversations', label: '对话历史', icon: MessageSquare },
    { id: 'search-analytics', label: '搜索分析', icon: BarChart3 },
    { id: 'api-docs', label: 'API文档', icon: BookOpen }
  ];

  return (
    <div className="space-y-6">
      {/* 头部信息 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6">
          {/* 返回按钮和操作 */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-4">
              {onBack && (
                <button
                  onClick={onBack}
                  className="flex items-center text-gray-500 hover:text-gray-700 transition-colors"
                >
                  <ExternalLink className="w-4 h-4 mr-2 rotate-180" />
                  返回列表
                </button>
              )}
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={handleRefresh}
                disabled={refreshing}
                className="flex items-center px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {refreshing ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <RefreshCw className="w-4 h-4 mr-2" />
                )}
                {refreshing ? '刷新中...' : '刷新'}
              </button>
              <StatusIcon status={knowledgeBase.status} />
            </div>
          </div>

          {/* 知识库基本信息 */}
          <div className="flex items-start space-x-4">
            <div className={`p-3 rounded-lg ${theme.iconBg} bg-opacity-10`}>
              <Database className={`w-8 h-8 ${theme.text.replace('text-', 'text-')}`} />
            </div>
            <div className="flex-1">
              <h1 className="text-2xl font-bold text-gray-900 mb-2">{knowledgeBase.name}</h1>
              {knowledgeBase.description && (
                <p className="text-gray-600 mb-4">{knowledgeBase.description}</p>
              )}
              <div className="flex items-center space-x-6 text-sm text-gray-500">
                <div className="flex items-center">
                  <Calendar className="w-4 h-4 mr-1" />
                  创建于 {formatDate(knowledgeBase.created_at)}
                </div>
                {knowledgeBase.updated_at && (
                  <div className="flex items-center">
                    <Clock className="w-4 h-4 mr-1" />
                    更新于 {formatDate(knowledgeBase.updated_at)}
                  </div>
                )}
                <div className="flex items-center">
                  <Database className="w-4 h-4 mr-1" />
                  ID: {knowledgeBase.ragflow_dataset_id}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 增强统计信息卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">文档数量</p>
              <p className="text-2xl font-bold text-gray-900">{knowledgeBase.document_count}</p>
            </div>
            <FileText className="w-8 h-8 text-blue-500" />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">对话历史</p>
              <p className="text-2xl font-bold text-gray-900">{activeConversations}</p>
            </div>
            <MessageSquare className="w-8 h-8 text-green-500" />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">搜索次数</p>
              <p className="text-2xl font-bold text-gray-900">{enhancedStats?.knowledge_base?.search_count || 0}</p>
            </div>
            <Search className="w-8 h-8 text-purple-500" />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">参与度评分</p>
              <p className="text-2xl font-bold text-gray-900">{enhancedStats?.engagement_score || 0}</p>
            </div>
            <TrendingUp className="w-8 h-8 text-orange-500" />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">存储大小</p>
              <p className="text-2xl font-bold text-gray-900">{(knowledgeBase.total_size / 1024 / 1024).toFixed(2)} MB</p>
            </div>
            <HardDrive className="w-8 h-8 text-indigo-500" />
          </div>
        </div>
      </div>

      {/* 标签页导航 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="border-b border-gray-200">
          <nav className="flex -mb-px">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === tab.id
                      ? `border-blue-500 text-blue-600 ${theme.text}`
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="w-4 h-4 mr-2" />
                  {tab.label}
                </button>
              );
            })}
          </nav>
        </div>

        {/* 标签页内容 */}
        <div className="p-6">
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* 快速测试对话 */}
              <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-6 border border-blue-200">
                <div className="flex items-center mb-4">
                  <MessageCircle className="w-5 h-5 mr-2 text-blue-500" />
                  <h3 className="text-lg font-semibold text-gray-900">快速测试对话</h3>
                </div>
                <div className="space-y-4">
                  <div>
                    <div className="flex space-x-3">
                      <div className="flex-1 relative">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                        <input
                          type="text"
                          value={testQuestion}
                          onChange={(e) => setTestQuestion(e.target.value)}
                          onKeyPress={(e) => e.key === 'Enter' && handleTestConversation()}
                          placeholder="请输入您的问题来测试知识库..."
                          disabled={testingConversation || hasNoDocuments}
                          className={`w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:outline-none ${theme.ring} transition-colors disabled:bg-gray-100 disabled:cursor-not-allowed`}
                        />
                      </div>
                      <button
                        onClick={handleTestConversation}
                        disabled={!testQuestion.trim() || testingConversation || hasNoDocuments}
                        className={`px-6 py-3 text-sm font-medium text-white rounded-md ${theme.primary} ${theme.primaryHover} disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center`}
                      >
                        {testingConversation ? (
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        ) : (
                          <Send className="w-4 h-4 mr-2" />
                        )}
                        {testingConversation ? '提问中...' : '发送问题'}
                      </button>
                    </div>
                    {hasNoDocuments && (
                      <p className="text-amber-600 text-sm">知识库中没有已解析的文档，无法进行测试对话</p>
                    )}
                  </div>
                </div>
              </div>

              {/* 活动统计 */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-gray-50 rounded-lg p-6">
                  <div className="flex items-center mb-4">
                    <Activity className="w-5 h-5 mr-2 text-blue-500" />
                    <h3 className="text-lg font-semibold text-gray-900">最近活动</h3>
                  </div>
                  <div className="space-y-3">
                    {enhancedStats?.daily_activity?.slice(0, 5).map((activity, index) => (
                      <div key={index} className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-gray-600">{activity.date}</p>
                        </div>
                        <div className="flex space-x-4 text-sm">
                          <div className="flex items-center text-blue-600">
                            <MessageSquare className="w-4 h-4 mr-1" />
                            {activity.conversations}
                          </div>
                          <div className="flex items-center text-purple-600">
                            <Search className="w-4 h-4 mr-1" />
                            {activity.searches}
                          </div>
                        </div>
                      </div>
                    )) || (
                      <p className="text-gray-500 text-sm">暂无活动数据</p>
                    )}
                  </div>
                </div>
                <div className="bg-gray-50 rounded-lg p-6">
                  <div className="flex items-center mb-4">
                    <BarChart3 className="w-5 h-5 mr-2 text-purple-500" />
                    <h3 className="text-lg font-semibold text-gray-900">搜索性能</h3>
                  </div>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">平均响应时间</span>
                      <span className="text-sm font-medium">
                        {searchStats?.performance?.avg_response_time_ms || 0}ms
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">成功率</span>
                      <span className="text-sm font-medium">
                        {searchStats?.success_rate || 0}%
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">点击率</span>
                      <span className="text-sm font-medium">
                        {searchStats?.click_through_rate || 0}%
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'conversations' && (
            <ConversationInterface
              knowledgeBaseId={knowledgeBaseId}
              knowledgeBaseName={knowledgeBase.name}
            />
          )}

          {activeTab === 'search-analytics' && (
            <SearchAnalyticsDashboard
              knowledgeBaseId={knowledgeBaseId}
              knowledgeBaseName={knowledgeBase.name}
            />
          )}

          {activeTab === 'api-docs' && (
            <APIDocumentationView
              knowledgeBaseId={knowledgeBaseId}
              knowledgeBaseName={knowledgeBase.name}
            />
          )}

          {activeTab === 'documents' && (
            <div className="space-y-6">
              {/* 文档上传 */}
              <DocumentUpload knowledgeBaseId={knowledgeBaseId} />

              {/* 文档列表 */}
              <DocumentList knowledgeBaseId={knowledgeBaseId} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default EnhancedKnowledgeBaseDetails;