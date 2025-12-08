import React, { useState, useEffect } from 'react';
import {
  Database,
  AlertCircle,
  Wifi,
  WifiOff,
  Loader2,
  RefreshCw
} from 'lucide-react';
import { useTheme } from '../theme';
import { knowledgeApi } from '../api/knowledgeApi';
import { KnowledgeBase, KnowledgeBaseConversation } from '../types/knowledge';
import { handleError } from '../utils/errorHandler';
import KnowledgeBaseList from './KnowledgeBaseList';
import KnowledgeBaseDetails from './KnowledgeBaseDetails';
import TestConversation from './TestConversation';

type View = 'list' | 'details' | 'conversation';

interface KnowledgeBaseManagementProps {
  manualRefresh?: boolean;
}

interface ConnectionStatus {
  connected: boolean;
  checking: boolean;
  lastChecked: Date | null;
  error: string | null;
}

const KnowledgeBaseManagement: React.FC<KnowledgeBaseManagementProps> = ({ manualRefresh = false }) => {
  const { theme } = useTheme();
  const [view, setView] = useState<View>('list');
  const [selectedKnowledgeBase, setSelectedKnowledgeBase] = useState<KnowledgeBase | null>(null);
  const [selectedConversation, setSelectedConversation] = useState<KnowledgeBaseConversation | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>({
    connected: false,
    checking: true,
    lastChecked: null,
    error: null
  });

  // 检查RAGFlow连接状态
  const checkConnectionStatus = async () => {
    try {
      setConnectionStatus(prev => ({ ...prev, checking: true, error: null }));

      // 尝试获取知识库列表来检查连接状态
      await knowledgeApi.getKnowledgeBases({ page: 1, page_size: 1 });

      setConnectionStatus({
        connected: true,
        checking: false,
        lastChecked: new Date(),
        error: null
      });
    } catch (error) {
      const errorMessage = handleError(error, false);
      setConnectionStatus({
        connected: false,
        checking: false,
        lastChecked: new Date(),
        error: errorMessage
      });
      console.error('RAGFlow connection check failed:', error);
    }
  };

  // 处理知识库选择
  const handleKnowledgeBaseSelect = (knowledgeBase: KnowledgeBase) => {
    setSelectedKnowledgeBase(knowledgeBase);
    setView('details');
    setError(null);
  };

  // 处理测试对话
  const handleTestConversation = (conversation: KnowledgeBaseConversation) => {
    setSelectedConversation(conversation);
    setView('conversation');
    setError(null);
  };

  // 返回列表视图
  const handleBackToList = () => {
    setView('list');
    setSelectedKnowledgeBase(null);
    setSelectedConversation(null);
    setError(null);
  };

  // 返回详情视图
  const handleBackToDetails = () => {
    setView('details');
    setSelectedConversation(null);
    setError(null);
  };

  // 刷新连接状态
  const handleRefreshConnection = async () => {
    await checkConnectionStatus();
  };

  // 组件初始化时检查连接状态
  useEffect(() => {
    checkConnectionStatus();
  }, []);

  // 当手动刷新时触发连接检查
  useEffect(() => {
    if (manualRefresh) {
      checkConnectionStatus();
    }
  }, [manualRefresh]);

  // 获取连接状态指示器组件
  const getConnectionStatusIndicator = () => {
    if (connectionStatus.checking) {
      return (
        <div className="flex items-center text-amber-600">
          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
          <span className="text-sm">检查连接中...</span>
        </div>
      );
    }

    if (connectionStatus.connected) {
      return (
        <div className="flex items-center text-green-600">
          <Wifi className="w-4 h-4 mr-2" />
          <span className="text-sm">RAGFlow已连接</span>
        </div>
      );
    }

    return (
      <div className="flex items-center text-red-600">
        <WifiOff className="w-4 h-4 mr-2" />
        <span className="text-sm">RAGFlow连接失败</span>
      </div>
    );
  };

  // 渲染错误提示
  const renderError = () => {
    if (!error && !connectionStatus.error) return null;

    const errorMessage = error || connectionStatus.error;
    const isConnectionError = !connectionStatus.connected && connectionStatus.error;

    return (
      <div className={`p-4 rounded-lg border-l-4 ${
        isConnectionError
          ? 'bg-amber-50 border-amber-400'
          : 'bg-red-50 border-red-400'
      }`}>
        <div className="flex">
          <AlertCircle className={`w-5 h-5 ${isConnectionError ? 'text-amber-400' : 'text-red-400'}`} />
          <div className="ml-3 flex-1">
            <h3 className={`text-sm font-medium ${isConnectionError ? 'text-amber-800' : 'text-red-800'}`}>
              {isConnectionError ? '连接警告' : '操作错误'}
            </h3>
            <div className={`mt-1 text-sm ${isConnectionError ? 'text-amber-700' : 'text-red-700'}`}>
              <p>{errorMessage}</p>
              {isConnectionError && (
                <div className="mt-2">
                  <p className="text-xs text-amber-600 mb-2">
                    无法连接到RAGFlow服务。知识库功能可能无法正常工作。
                  </p>
                  <button
                    onClick={handleRefreshConnection}
                    disabled={connectionStatus.checking}
                    className={`inline-flex items-center px-3 py-1 text-xs font-medium rounded ${
                      connectionStatus.checking
                        ? 'bg-amber-100 text-amber-400 cursor-not-allowed'
                        : 'bg-amber-100 text-amber-800 hover:bg-amber-200'
                    } transition-colors`}
                  >
                    {connectionStatus.checking ? (
                      <>
                        <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                        检查中...
                      </>
                    ) : (
                      <>
                        <RefreshCw className="w-3 h-3 mr-1" />
                        重新检查
                      </>
                    )}
                  </button>
                </div>
              )}
            </div>
          </div>
          {error && (
            <button
              onClick={() => setError(null)}
              className="ml-auto text-red-400 hover:text-red-600 transition-colors"
            >
              <span className="sr-only">关闭</span>
              <span className="text-xl leading-none">×</span>
            </button>
          )}
        </div>
      </div>
    );
  };

  // 渲染主要内容
  const renderContent = () => {
    switch (view) {
      case 'details':
        if (!selectedKnowledgeBase) {
          return (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
              <div className="text-center">
                <AlertCircle className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                <p className="text-gray-600">请选择一个知识库查看详情</p>
              </div>
            </div>
          );
        }
        return (
          <KnowledgeBaseDetails
            knowledgeBaseId={selectedKnowledgeBase.id}
            onBack={handleBackToList}
            onTestConversation={handleTestConversation}
          />
        );

      case 'conversation':
        if (!selectedKnowledgeBase) {
          return (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
              <div className="text-center">
                <AlertCircle className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                <p className="text-gray-600">请选择一个知识库进行测试对话</p>
              </div>
            </div>
          );
        }
        return (
          <TestConversation
            knowledgeBase={selectedKnowledgeBase}
            conversation={selectedConversation || undefined}
            onBack={handleBackToDetails}
          />
        );

      case 'list':
      default:
        return (
          <KnowledgeBaseList
            onKnowledgeBaseSelect={handleKnowledgeBaseSelect}
            selectedKnowledgeBaseId={selectedKnowledgeBase?.id}
          />
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* 头部标题和连接状态 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className={`p-3 rounded-lg ${theme.iconBg} bg-opacity-10`}>
                <Database className={`w-6 h-6 ${theme.text.replace('text-', 'text-')}`} />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">知识库管理</h1>
                <p className="text-sm text-gray-600 mt-1">
                  管理和测试RAGFlow知识库，检索相关信息并进行对话测试
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              {getConnectionStatusIndicator()}
              {connectionStatus.lastChecked && (
                <div className="text-xs text-gray-500">
                  最后检查: {connectionStatus.lastChecked.toLocaleTimeString('zh-CN')}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 错误提示 */}
      {(error || connectionStatus.error) && renderError()}

      {/* 主要内容区域 */}
      <div className="min-h-[500px]">
        {connectionStatus.checking ? (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
            <div className="text-center">
              <Loader2 className="w-8 h-8 mx-auto animate-spin text-blue-500 mb-4" />
              <p className="text-gray-500">连接检测中...</p>
            </div>
          </div>
        ) : (
          renderContent()
        )}
      </div>
    </div>
  );
};

export default KnowledgeBaseManagement;