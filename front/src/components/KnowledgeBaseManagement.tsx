import React, { useState, useEffect } from 'react';
import {
  Database,
  AlertCircle,
  Wifi,
  WifiOff,
  Loader2,
  RefreshCw,
  MessageSquare,
  Search,
  Bot,
  BarChart3
} from 'lucide-react';
import { useTheme } from '../theme';
import { knowledgeApi } from '../api/knowledgeApi';
import { KnowledgeBase, KnowledgeBaseConversation } from '../types/knowledge';
import { handleError } from '../utils/errorHandler';
import KnowledgeBaseList from './KnowledgeBaseList';
import EnhancedKnowledgeBaseDetails from './EnhancedKnowledgeBaseDetails';
import ConversationList from './conversation/ConversationList';
import SearchAnalyticsList from './search/SearchAnalyticsList';
import AgentList from './agent/AgentList';

type TabType = 'knowledge-bases' | 'conversations' | 'searches' | 'agents';
type View = 'list' | 'details';

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
  const [activeTab, setActiveTab] = useState<TabType>('knowledge-bases');
  const [view, setView] = useState<View>('list');
  const [selectedKnowledgeBase, setSelectedKnowledgeBase] = useState<KnowledgeBase | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>({
    connected: false,
    checking: true,
    lastChecked: null,
    error: null
  });

  // 选项卡配置
  const tabs = [
    {
      id: 'knowledge-bases' as TabType,
      name: '知识库管理',
      icon: Database,
      description: '管理RAGFlow数据集和文档'
    },
    {
      id: 'conversations' as TabType,
      name: '对话管理',
      icon: MessageSquare,
      description: '管理RAGFlow对话和历史记录'
    },
    {
      id: 'searches' as TabType,
      name: '搜索分析',
      icon: BarChart3,
      description: '查看搜索统计和性能分析'
    },
    {
      id: 'agents' as TabType,
      name: '智能体管理',
      icon: Bot,
      description: '配置和管理AI智能体'
    }
  ];

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

  // 返回列表视图
  const handleBackToList = () => {
    setView('list');
    setSelectedKnowledgeBase(null);
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

  // 选项卡切换处理
  const handleTabChange = (tab: TabType) => {
    setActiveTab(tab);
    // 切换选项卡时重置视图状态
    setView('list');
    setSelectedKnowledgeBase(null);
  };

  // 对话相关处理函数
  const handleConversationSelect = (conversation: any) => {
    // 处理对话选择
    console.log('Selected conversation:', conversation);
  };

  const handleNewConversation = () => {
    // 创建新对话
    console.log('Creating new conversation');
  };

  // 搜索相关处理函数
  const handleDetailedAnalytics = () => {
    // 切换到详细分析视图
    console.log('Showing detailed analytics');
  };

  // 智能体相关处理函数
  const handleAgentSelect = (agent: any) => {
    // 处理智能体选择
    console.log('Selected agent:', agent);
  };

  const handleNewAgent = () => {
    // 创建新智能体
    console.log('Creating new agent');
  };

  // 渲染选项卡
  const renderTabs = () => (
    <div className="border-b-4 border-gray-300 bg-gray-50 p-4">
      <div className="flex flex-wrap gap-2 mb-4">
        <p className="text-sm font-bold text-gray-700 w-full">🧪 选项卡测试区域：</p>
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => handleTabChange(tab.id)}
              className={`
                inline-flex items-center px-4 py-2 rounded-lg font-medium text-sm transition-all
                ${isActive
                  ? 'bg-blue-500 text-white shadow-lg transform scale-105'
                  : 'bg-white text-gray-700 border-2 border-gray-300 hover:bg-gray-100'
                }
              `}
            >
              <tab.icon
                className={`mr-2 h-4 w-4`}
              />
              {tab.name}
            </button>
          );
        })}
      </div>
      <div className="text-xs text-gray-500">
        当前活跃选项卡: <span className="font-bold text-blue-600">{activeTab}</span>
      </div>
    </div>
  );

  // 渲染选项卡内容
  const renderTabContent = () => {
    switch (activeTab) {
      case 'knowledge-bases':
        // 知识库管理 - 保持原有逻辑
        return renderContent();

      case 'conversations':
        return (
          <ConversationList
            onConversationSelect={handleConversationSelect}
            onNewConversation={handleNewConversation}
          />
        );

      case 'searches':
        return (
          <SearchAnalyticsList
            onDetailedAnalytics={handleDetailedAnalytics}
          />
        );

      case 'agents':
        return (
          <AgentList
            onAgentSelect={handleAgentSelect}
            onNewAgent={handleNewAgent}
          />
        );

      default:
        return renderContent();
    }
  };

  // 获取当前选项卡信息
  const getCurrentTabInfo = () => {
    const currentTab = tabs.find(tab => tab.id === activeTab);
    return currentTab || tabs[0];
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
          <EnhancedKnowledgeBaseDetails
            knowledgeBaseId={selectedKnowledgeBase.id}
            onBack={handleBackToList}
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

  const currentTabInfo = getCurrentTabInfo();

  return (
    <div className="space-y-6">
      {/* 头部标题和连接状态 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className={`p-3 rounded-lg ${theme.iconBg} bg-opacity-10`}>
                <currentTabInfo.icon className={`w-6 h-6 ${theme.text.replace('text-', 'text-')}`} />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">{currentTabInfo.name}</h1>
                <p className="text-sm text-gray-600 mt-1">
                  {currentTabInfo.description}
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

        {/* 选项卡导航 */}
        {renderTabs()}
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
          renderTabContent()
        )}
      </div>
    </div>
  );
};

export default KnowledgeBaseManagement;