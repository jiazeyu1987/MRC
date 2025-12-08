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
  FileUp
} from 'lucide-react';
import { useTheme } from '../theme';
import { knowledgeApi } from '../api/knowledgeApi';
import { KnowledgeBase, KnowledgeBaseConversation } from '../types/knowledge';
import { Document } from '../types/document';
import { handleError } from '../utils/errorHandler';
import DocumentUpload from './DocumentUpload';
import DocumentList from './DocumentList';
import DocumentView from './DocumentView';

interface KnowledgeBaseDetailsProps {
  knowledgeBaseId: number;
  onBack?: () => void;
  onTestConversation?: (conversation: KnowledgeBaseConversation) => void;
}

const KnowledgeBaseDetails: React.FC<KnowledgeBaseDetailsProps> = ({
  knowledgeBaseId,
  onBack,
  onTestConversation
}) => {
  const { theme } = useTheme();
  const [knowledgeBase, setKnowledgeBase] = useState<KnowledgeBase | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [testQuestion, setTestQuestion] = useState<string>('');
  const [testingConversation, setTestingConversation] = useState<boolean>(false);

  // Document management state
  const [documentView, setDocumentView] = useState<'upload' | 'list' | 'view' | null>(null);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [documentRefreshTrigger, setDocumentRefreshTrigger] = useState<number>(0);

  // 加载知识库详情和统计信息
  const loadKnowledgeBaseDetails = async () => {
    try {
      setLoading(true);
      setError(null);

      const details = await knowledgeApi.getKnowledgeBaseDetails(knowledgeBaseId);
      setKnowledgeBase(details);
    } catch (error) {
      const errorMessage = handleError(error, false);
      setError(errorMessage);
      console.error('Failed to load knowledge base details:', error);
    } finally {
      setLoading(false);
    }
  };

  // 刷新知识库
  const handleRefresh = async () => {
    try {
      setRefreshing(true);
      setError(null);

      const result = await knowledgeApi.refreshKnowledgeBase(knowledgeBaseId);
      console.log('Knowledge base refresh result:', result);

      // 刷新成功后重新加载详情
      await loadKnowledgeBaseDetails();
    } catch (error) {
      const errorMessage = handleError(error);
      setError(errorMessage);
    } finally {
      setRefreshing(false);
    }
  };

  // 测试对话
  const handleTestConversation = async () => {
    if (!testQuestion.trim() || !knowledgeBase) return;

    try {
      setTestingConversation(true);
      setError(null);

      const conversation = await knowledgeApi.testConversation(
        knowledgeBaseId,
        testQuestion.trim(),
        `测试对话 - ${knowledgeBase.name}`
      );

      // 清空输入框
      setTestQuestion('');

      // 通知父组件
      if (onTestConversation) {
        onTestConversation(conversation);
      }
    } catch (error) {
      const errorMessage = handleError(error);
      setError(errorMessage);
    } finally {
      setTestingConversation(false);
    }
  };

  // Document management handlers
  const handleDocumentUpload = () => {
    setDocumentView('upload');
    setSelectedDocument(null);
  };

  const handleDocumentList = () => {
    setDocumentView('list');
    setSelectedDocument(null);
  };

  const handleDocumentSelect = (document: Document) => {
    setSelectedDocument(document);
    setDocumentView('view');
  };

  const handleDocumentBack = () => {
    if (documentView === 'view') {
      setDocumentView('list');
    } else {
      setDocumentView(null);
    }
  };

  const handleDocumentUploadComplete = (documentId: string) => {
    // Refresh knowledge base details to update document count
    loadKnowledgeBaseDetails();

    // Trigger document list refresh
    setDocumentRefreshTrigger(prev => prev + 1);

    // Show success message or switch to list view
    setTimeout(() => {
      setDocumentView('list');
    }, 2000);
  };

  const handleDocumentDelete = (documentId: string) => {
    // Refresh knowledge base details to update document count
    loadKnowledgeBaseDetails();

    // Trigger document list refresh
    setDocumentRefreshTrigger(prev => prev + 1);

    // If viewing the deleted document, go back to list
    if (selectedDocument?.id === documentId) {
      handleDocumentBack();
    }
  };

  // 格式化文件大小
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // 格式化日期
  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
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
                className={`flex items-center px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors`}
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

      {/* 统计信息卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">文档数量</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {knowledgeBase.document_count.toLocaleString()}
              </p>
            </div>
            <div className="p-3 bg-blue-100 rounded-lg">
              <FileText className="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">总大小</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {formatFileSize(knowledgeBase.total_size)}
              </p>
            </div>
            <div className="p-3 bg-green-100 rounded-lg">
              <HardDrive className="w-6 h-6 text-green-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">对话数量</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {knowledgeBase.conversation_count || 0}
              </p>
            </div>
            <div className="p-3 bg-purple-100 rounded-lg">
              <MessageCircle className="w-6 h-6 text-purple-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">关联角色</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {knowledgeBase.linked_roles?.length || 0}
              </p>
            </div>
            <div className="p-3 bg-amber-100 rounded-lg">
              <User className="w-6 h-6 text-amber-600" />
            </div>
          </div>
        </div>
      </div>

      {/* 文档管理 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <FolderOpen className="w-5 h-5 mr-2 text-blue-500" />
              <h2 className="text-lg font-semibold text-gray-900">文档管理</h2>
              {knowledgeBase.document_count > 0 && (
                <span className="ml-3 px-2 py-1 text-sm bg-blue-100 text-blue-700 rounded-full">
                  {knowledgeBase.document_count} 个文档
                </span>
              )}
            </div>

            {!documentView && (
              <div className="flex items-center space-x-2">
                <button
                  onClick={handleDocumentUpload}
                  className={`flex items-center px-4 py-2 text-sm font-medium text-white rounded-md ${theme.primary} ${theme.primaryHover} transition-colors`}
                >
                  <Upload className="w-4 h-4 mr-2" />
                  上传文档
                </button>
                {knowledgeBase.document_count > 0 && (
                  <button
                    onClick={handleDocumentList}
                    className={`flex items-center px-4 py-2 text-sm font-medium ${theme.text} border ${theme.border} rounded-md hover:bg-gray-50 transition-colors`}
                  >
                    <List className="w-4 h-4 mr-2" />
                    文档列表
                  </button>
                )}
              </div>
            )}
          </div>

          {/* Document management content */}
          {documentView ? (
            <div className="mt-4">
              {documentView === 'upload' && (
                <DocumentUpload
                  knowledgeBaseId={knowledgeBaseId.toString()}
                  onUploadComplete={handleDocumentUploadComplete}
                  onUploadError={(error) => setError(error)}
                  maxFileSize={50 * 1024 * 1024} // 50MB
                  maxFiles={10}
                />
              )}

              {documentView === 'list' && (
                <DocumentList
                  knowledgeBaseId={knowledgeBaseId.toString()}
                  onDocumentSelect={handleDocumentSelect}
                  onDocumentDelete={handleDocumentDelete}
                  refreshTrigger={documentRefreshTrigger}
                  className="mt-4"
                />
              )}

              {documentView === 'view' && selectedDocument && (
                <DocumentView
                  knowledgeBaseId={knowledgeBaseId.toString()}
                  documentId={selectedDocument.id}
                  document={selectedDocument}
                  onBack={handleDocumentBack}
                  className="mt-4"
                />
              )}
            </div>
          ) : (
            // Default view with document management summary
            <div className="space-y-4">
              {hasNoDocuments ? (
                <div className="text-center py-8">
                  <FileUp className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">暂无文档</h3>
                  <p className="text-gray-600 mb-4">
                    上传文档到知识库以启用智能问答和内容检索功能
                  </p>
                  <button
                    onClick={handleDocumentUpload}
                    className={`px-4 py-2 text-sm font-medium text-white rounded-md ${theme.primary} ${theme.primaryHover} transition-colors`}
                  >
                    <Upload className="w-4 h-4 mr-2 inline" />
                    上传第一个文档
                  </button>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors cursor-pointer"
                       onClick={handleDocumentUpload}>
                    <div className="flex items-center">
                      <div className="p-2 bg-blue-100 rounded-lg mr-3">
                        <Upload className="w-5 h-5 text-blue-600" />
                      </div>
                      <div>
                        <h4 className="font-medium text-gray-900">上传新文档</h4>
                        <p className="text-sm text-gray-600">添加PDF、Word、文本等文件</p>
                      </div>
                    </div>
                  </div>

                  <div className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors cursor-pointer"
                       onClick={handleDocumentList}>
                    <div className="flex items-center">
                      <div className="p-2 bg-green-100 rounded-lg mr-3">
                        <List className="w-5 h-5 text-green-600" />
                      </div>
                      <div>
                        <h4 className="font-medium text-gray-900">查看文档列表</h4>
                        <p className="text-sm text-gray-600">管理已上传的文档</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Quick stats */}
              {knowledgeBase.document_count > 0 && (
                <div className="mt-6 pt-6 border-t border-gray-200">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
                    <div>
                      <div className="text-2xl font-bold text-gray-900">
                        {knowledgeBase.document_count}
                      </div>
                      <div className="text-sm text-gray-600">文档总数</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-gray-900">
                        {formatFileSize(knowledgeBase.total_size)}
                      </div>
                      <div className="text-sm text-gray-600">总存储大小</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-gray-900">
                        {knowledgeBase.conversation_count || 0}
                      </div>
                      <div className="text-sm text-gray-600">测试对话</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* 警告信息 */}
      {hasNoDocuments && !documentView && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
          <div className="flex">
            <AlertTriangle className="w-5 h-5 text-amber-400 mt-0.5" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-amber-800">注意</h3>
              <p className="mt-1 text-sm text-amber-700">
                此知识库当前没有已解析的文档。测试对话功能可能无法正常工作，建议先上传文档或使用上方的文档管理功能。
              </p>
            </div>
          </div>
        </div>
      )}

      {/* 测试对话 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6">
          <div className="flex items-center mb-4">
            <MessageCircle className="w-5 h-5 mr-2 text-blue-500" />
            <h2 className="text-lg font-semibold text-gray-900">测试对话</h2>
          </div>

          <div className="space-y-4">
            <div>
              <label htmlFor="test-question" className="block text-sm font-medium text-gray-700 mb-2">
                输入您的问题来测试知识库的检索和回答能力
              </label>
              <div className="flex space-x-3">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                  <input
                    id="test-question"
                    type="text"
                    value={testQuestion}
                    onChange={(e) => setTestQuestion(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleTestConversation()}
                    placeholder="请输入您的问题..."
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
                <p className="mt-2 text-sm text-amber-600">
                  知识库中没有已解析的文档，无法进行测试对话
                </p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 关联角色 */}
      {knowledgeBase.linked_roles && knowledgeBase.linked_roles.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-6">
            <div className="flex items-center mb-4">
              <User className="w-5 h-5 mr-2 text-blue-500" />
              <h2 className="text-lg font-semibold text-gray-900">关联角色</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {knowledgeBase.linked_roles.map((role) => (
                <div
                  key={role.id}
                  className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <h3 className="font-medium text-gray-900 mb-1">{role.name}</h3>
                  <p className="text-sm text-gray-600 line-clamp-2">{role.prompt}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default KnowledgeBaseDetails;