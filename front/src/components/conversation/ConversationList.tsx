import React, { useState, useEffect } from 'react';
import { MessageSquare, Plus, Search, Filter, Calendar, Users, Clock, MoreHorizontal, Loader2, Bot, Database, AlertCircle } from 'lucide-react';
import { useTheme } from '../../theme';
import { ragflowChatApi, ChatAssistant, ChatSession } from '../../api/ragflowChatApi';

interface ConversationListProps {
  onConversationSelect: (conversation: { assistant: ChatAssistant; session?: ChatSession }) => void;
  onNewConversation: () => void;
}

const ConversationList: React.FC<ConversationListProps> = ({
  onConversationSelect,
  onNewConversation
}) => {
  const { theme } = useTheme();
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [chatAssistants, setChatAssistants] = useState<ChatAssistant[]>([]);
  const [expandedAssistants, setExpandedAssistants] = useState<Set<string>>(new Set());
  const [assistantSessions, setAssistantSessions] = useState<Map<string, ChatSession[]>>(new Map());
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  // 加载对话助手列表 - 使用真实RAGFlow API
  const loadChatAssistants = async () => {
    try {
      setLoading(true);
      setError(null);

      // 使用真实的RAGFlow API获取对话助手列表
      const response = await ragflowChatApi.listChatAssistants();
      const assistants = Array.isArray(response) ? response : response.data || [];
      setChatAssistants(assistants);

      // 为每个助手获取对话会话历史
      const sessionMap = new Map<string, ChatSession[]>();

      // 并行获取每个助手的会话历史
      const sessionPromises = assistants.map(async (assistant) => {
        try {
          const sessionResponse = await ragflowChatApi.listChatSessions(assistant.id);
          const sessions = Array.isArray(sessionResponse) ? sessionResponse : sessionResponse.data || [];
          return { assistantId: assistant.id, sessions };
        } catch (sessionError) {
          console.error(`Failed to load sessions for assistant ${assistant.id}:`, sessionError);
          // 如果获取会话失败，设置空数组
          return { assistantId: assistant.id, sessions: [] };
        }
      });

      const sessionResults = await Promise.all(sessionPromises);
      sessionResults.forEach(({ assistantId, sessions }) => {
        sessionMap.set(assistantId, sessions);
      });
      setAssistantSessions(sessionMap);

    } catch (err) {
      console.error('Load chat assistants error:', err);
      setError('加载对话助手失败: ' + (err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  // 组件初始化时加载数据
  useEffect(() => {
    loadChatAssistants();
  }, []);

  // 切换助手的展开/折叠状态
  const toggleAssistantExpansion = (assistantId: string) => {
    setExpandedAssistants(prev => {
      const newSet = new Set(prev);
      if (newSet.has(assistantId)) {
        newSet.delete(assistantId);
      } else {
        newSet.add(assistantId);
      }
      return newSet;
    });
  };

  const formatDate = (timestamp: number) => {
    const date = new Date(timestamp * 1000);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);

    if (diffDays > 0) {
      return `${diffDays}天前`;
    } else if (diffHours > 0) {
      return `${diffHours}小时前`;
    } else {
      return '刚刚';
    }
  };

  const filteredAssistants = chatAssistants.filter(assistant => {
    const matchesSearch = assistant.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         assistant.description.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesSearch;
  });

  const getSessionCount = (assistantId: string) => {
    const sessions = assistantSessions.get(assistantId);
    return sessions ? sessions.length : 0;
  };

  const handleSessionClick = (assistant: ChatAssistant, session: ChatSession) => {
    onConversationSelect({ assistant, session });
  };

  const handleAssistantClick = (assistant: ChatAssistant) => {
    onConversationSelect({ assistant });
  };

  return (
    <div className="space-y-6">
      {/* 工具栏 */}
      <div className={`rounded-lg shadow-sm border ${
        theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
      }`}>
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className={`text-lg font-semibold ${
              theme === 'dark' ? 'text-white' : 'text-gray-900'
            }`}>RAGFlow 对话管理</h2>
            <button
              onClick={onNewConversation}
              className={`inline-flex items-center px-4 py-2 text-sm font-medium text-white rounded-lg ${
                theme.primary || 'bg-blue-500'
              } ${
                theme.primaryHover || 'hover:bg-blue-600'
              } transition-colors`}
            >
              <Plus className="w-4 h-4 mr-2" />
              新建对话助手
            </button>
          </div>

          {/* 搜索和过滤 */}
          <div className="flex items-center space-x-4">
            <div className="flex-1 relative">
              <Search className={`absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400`} />
              <input
                type="text"
                placeholder="搜索对话助手..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className={`w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                  theme === 'dark'
                    ? 'bg-gray-800 border-gray-700 text-white placeholder-gray-400'
                    : 'border-gray-300'
                }`}
              />
            </div>
            <button
              onClick={loadChatAssistants}
              className="inline-flex items-center px-3 py-2 text-sm border rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
              disabled={loading}
            >
              <Loader2 className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              刷新
            </button>
          </div>
        </div>
      </div>

      {/* 错误提示 */}
      {error && (
        <div className={`rounded-lg p-4 ${
          theme === 'dark' ? 'bg-red-900 border-red-700' : 'bg-red-50 border-red-200'
        }`}>
          <div className="flex items-center">
            <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
            <span className={theme === 'dark' ? 'text-red-200' : 'text-red-800'}>{error}</span>
          </div>
        </div>
      )}

      {/* 对话助手列表 */}
      <div className={`rounded-lg shadow-sm border ${
        theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
      }`}>
        <div className="divide-y divide-gray-200 dark:divide-gray-700">
          {loading ? (
            <div className="p-12 text-center">
              <Loader2 className="w-8 h-8 mx-auto animate-spin text-blue-500 mb-4" />
              <p className={`${
                theme === 'dark' ? 'text-gray-400' : 'text-gray-500'
              }`}>正在加载对话助手...</p>
            </div>
          ) : filteredAssistants.length === 0 ? (
            <div className="p-12 text-center">
              <Bot className={`w-12 h-12 mx-auto mb-4 ${
                theme === 'dark' ? 'text-gray-600' : 'text-gray-400'
              }`} />
              <p className={`mb-2 ${
                theme === 'dark' ? 'text-gray-400' : 'text-gray-600'
              }`}>暂无对话助手</p>
              <p className={`text-sm ${
                theme === 'dark' ? 'text-gray-500' : 'text-gray-500'
              }`}>
                请确保RAGFlow服务正常运行且已配置对话助手
              </p>
            </div>
          ) : (
            filteredAssistants.map((assistant) => {
              const isExpanded = expandedAssistants.has(assistant.id);
              const sessions = assistantSessions.get(assistant.id) || [];
              const sessionCount = getSessionCount(assistant.id);

              return (
                <div key={assistant.id} className={`border-b ${
                  theme === 'dark' ? 'border-gray-700' : 'border-gray-200'
                } last:border-b-0`}>
                  {/* 助手基本信息 */}
                  <div
                    className={`p-6 cursor-pointer transition-colors ${
                      theme === 'dark' ? 'hover:bg-gray-700' : 'hover:bg-gray-50'
                    }`}
                    onClick={() => handleAssistantClick(assistant)}
                  >
                    <div className="flex items-start justify-between">
                      {/* 左侧内容 */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-3 mb-2">
                          <div className={`p-2 rounded-lg ${
                            theme === 'dark' ? 'bg-blue-900' : 'bg-blue-100'
                          }`}>
                            <Bot className={`w-5 h-5 ${
                              theme === 'dark' ? 'text-blue-400' : 'text-blue-600'
                            }`} />
                          </div>
                          <h3 className={`text-lg font-medium ${
                            theme === 'dark' ? 'text-white' : 'text-gray-900'
                          }`}>
                            {assistant.name}
                          </h3>
                          <span className="inline-flex items-center px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">
                            活跃
                          </span>
                        </div>

                        <p className={`text-sm mb-3 ${
                          theme === 'dark' ? 'text-gray-400' : 'text-gray-600'
                        }`}>{assistant.description}</p>

                        {/* 数据集信息 */}
                        {assistant.dataset_ids && assistant.dataset_ids.length > 0 && (
                          <div className="flex items-center space-x-2 mb-2">
                            <Database className="w-4 h-4 text-blue-500" />
                            <span className={`text-xs ${
                              theme === 'dark' ? 'text-gray-400' : 'text-gray-600'
                            }`}>
                              {assistant.dataset_ids.length} 个数据集
                            </span>
                          </div>
                        )}

                        {/* 配置信息 */}
                        {assistant.prompt_config && (
                          <div className="flex items-center space-x-2 mb-2">
                            <span className="text-xs bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-2 py-1 rounded">
                              {assistant.prompt_config.prompt_name}
                            </span>
                            <span className={`text-xs ${
                              theme === 'dark' ? 'text-gray-500' : 'text-gray-600'
                            }`}>
                              温度: {assistant.prompt_config.t}
                            </span>
                          </div>
                        )}
                      </div>

                      {/* 右侧信息 */}
                      <div className="flex items-center space-x-2">
                        <div className={`text-xs ${
                          theme === 'dark' ? 'text-gray-400' : 'text-gray-500'
                        }`}>
                          <Clock className="w-4 h-4 mr-1" />
                          创建: {formatDate(assistant.create_time)}
                        </div>
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                          theme === 'dark' ? 'bg-purple-100 text-purple-800' : 'bg-purple-100 text-purple-800'
                        }`}>
                          {sessionCount} 个会话
                        </span>
                      </div>
                    </div>

                    {/* 操作按钮 */}
                    <div className="flex items-center space-x-2">
                      <button
                        className={`p-2 rounded-lg transition-colors ${
                          theme === 'dark'
                            ? 'text-blue-400 hover:bg-blue-900/20'
                            : 'text-blue-600 hover:bg-blue-50'
                        }`}
                        onClick={(e) => {
                          e.stopPropagation();
                          // TODO: 实现与助手的对话功能
                        }}
                        title="开始对话"
                      >
                        <MessageSquare className="w-4 h-4" />
                      </button>
                      <button
                        className={`p-2 rounded-lg transition-colors ${
                          theme === 'dark'
                            ? 'text-gray-400 hover:bg-gray-700'
                            : 'text-gray-600 hover:bg-gray-100'
                        }`}
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleAssistantExpansion(assistant.id);
                        }}
                        title={isExpanded ? "收起会话" : "展开会话"}
                      >
                        <Database className={`w-4 h-4 ${isExpanded ? 'rotate-180' : ''} transition-transform`} />
                      </button>
                    </div>
                  </div>

                  {/* 展开的会话列表 */}
                  {isExpanded && (
                    <div className={`px-6 pb-4 ${
                      theme === 'dark' ? 'bg-gray-50' : 'bg-gray-50'
                    }`}>
                      {sessions.length > 0 ? (
                        <div className="space-y-2">
                          {sessions.map((session) => (
                            <div
                              key={session.id}
                              className={`flex items-center justify-between p-3 rounded-lg border ${
                                theme === 'dark'
                                  ? 'border-gray-600 bg-gray-800 hover:bg-gray-700'
                                  : 'border-gray-200 bg-white hover:bg-gray-50'
                              } cursor-pointer transition-colors`}
                              onClick={() => handleSessionClick(assistant, session)}
                            >
                              <div className="flex items-center space-x-3">
                                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                                <div>
                                  <div className={`text-sm font-medium ${
                                    theme === 'dark' ? 'text-white' : 'text-gray-900'
                                  }`}>
                                    {session.name}
                                  </div>
                                  <div className={`text-xs ${
                                    theme === 'dark' ? 'text-gray-400' : 'text-gray-500'
                                  }`}>
                                    创建: {formatDate(session.create_time)} | 消息: {session.messages?.length || 0}
                                  </div>
                                </div>
                              </div>
                              <div className={`text-xs ${
                                theme === 'dark' ? 'text-gray-500' : 'text-gray-400'
                              }`}>
                                {formatDate(session.update_time)}
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="text-center text-sm text-gray-500 py-4">
                          暂无会话记录
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>

        {/* 统计信息 */}
        {!loading && filteredAssistants.length > 0 && (
          <div className={`p-4 border-t ${
            theme === 'dark' ? 'border-gray-700 bg-gray-800' : 'border-t border-gray-200 bg-gray-50'
          }`}>
            <div className={`flex items-center justify-between text-sm ${
              theme === 'dark' ? 'text-gray-400' : 'text-gray-600'
            }`}>
              <div>
                显示 {filteredAssistants.length} 个助手，共 {chatAssistants.length} 个对话助手
              </div>
              <div>
                总会话数: {Array.from(assistantSessions.values()).reduce((sum, sessions) => sum + sessions.length, 0)}
              </div>
            </div>
          </div>
        )}

        {/* 功能提示 */}
        {!loading && chatAssistants.length > 0 && (
          <div className={`p-4 border-t ${
            theme === 'dark' ? 'border-gray-700 bg-gray-800' : 'border-t border-gray-200 bg-blue-50'
          }`}>
            <div className="flex items-start space-x-3">
              <AlertCircle className="w-5 h-5 text-blue-500 mt-0.5" />
              <div className={`text-sm ${
                theme === 'dark' ? 'text-blue-200' : 'text-blue-800'
              }`}>
                <p className="font-medium mb-1">RAGFlow 对话功能</p>
                <ul className="text-sm space-y-1">
                  <li>• 点击助手名称查看详情</li>
                  <li>• 点击"开始对话"与助手进行交流</li>
                  <li>• 展开会话列表查看历史记录</li>
                  <li>• 助手连接到指定数据集进行知识增强对话</li>
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ConversationList;