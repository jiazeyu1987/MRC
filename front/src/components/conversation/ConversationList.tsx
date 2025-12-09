import React, { useState, useEffect } from 'react';
import { MessageSquare, Plus, Search, Filter, Calendar, Users, Clock, MoreHorizontal, Loader2, Bot, Database } from 'lucide-react';
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

  // 加载对话助手列表 - 模拟数据
  const loadChatAssistants = async () => {
    try {
      setLoading(true);
      setError(null);

      // 模拟数据 - 等待 RAGFlow API 实现后使用真实数据
      const mockAssistants: ChatAssistant[] = [
        {
          id: 'chat-001',
          name: '技术支持助手',
          avatar: '🤖',
          description: '专门处理技术问题和故障排除的AI助手',
          prompt_config: {
            prompt_name: '技术支持',
            prompt_text: '你是一个专业的技术支持助手，请耐心解答用户的技术问题。',
            quote: true,
            t: 0.7
          },
          dataset_ids: ['dataset-001', 'dataset-002'],
          create_time: Math.floor(Date.now() / 1000) - 86400 * 7,
          update_time: Math.floor(Date.now() / 1000) - 3600
        },
        {
          id: 'chat-002',
          name: '产品顾问',
          avatar: '🎯',
          description: '为用户提供产品推荐和购买建议的专业顾问',
          prompt_config: {
            prompt_name: '产品顾问',
            prompt_text: '你是一个专业的产品顾问，为用户提供精准的产品推荐和购买建议。',
            quote: true,
            t: 0.8
          },
          dataset_ids: ['dataset-003', 'dataset-004'],
          create_time: Math.floor(Date.now() / 1000) - 86400 * 14,
          update_time: Math.floor(Date.now() / 1000) - 7200
        }
      ];

      const mockSessions: Record<string, ChatSession[]> = {
        'chat-001': [
          {
            id: 'session-001',
            name: 'Python相关问题咨询',
            chat_id: 'chat-001',
            create_time: Math.floor(Date.now() / 1000) - 3600 * 2,
            update_time: Math.floor(Date.now() / 1000) - 1800,
            message_count: 8
          },
          {
            id: 'session-002',
            name: '数据库故障排查',
            chat_id: 'chat-001',
            create_time: Math.floor(Date.now() / 1000) - 86400,
            update_time: Math.floor(Date.now() / 1000) - 3600 * 3,
            message_count: 15
          }
        ],
        'chat-002': [
          {
            id: 'session-003',
            name: '产品功能咨询',
            chat_id: 'chat-002',
            create_time: Math.floor(Date.now() / 1000) - 7200,
            update_time: Math.floor(Date.now() / 1000) - 1800,
            message_count: 5
          }
        ]
      };

      setChatAssistants(mockAssistants);

      const sessionMap = new Map<string, ChatSession[]>();
      Object.entries(mockSessions).forEach(([assistantId, sessions]) => {
        sessionMap.set(assistantId, sessions);
      });
      setAssistantSessions(sessionMap);

    } catch (err) {
      setError('加载对话助手失败');
      console.error('Load chat assistants error:', err);
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

  return (
    <div className="space-y-6">
      {/* 工具栏 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">RAGFlow 对话管理 (模拟数据)</h2>
            <button
              onClick={onNewConversation}
              className={`inline-flex items-center px-4 py-2 text-sm font-medium text-white rounded-lg ${theme.primary} ${theme.primaryHover} transition-colors`}
            >
              <Plus className="w-4 h-4 mr-2" />
              新建对话助手
            </button>
          </div>

          {/* 搜索和过滤 */}
          <div className="flex items-center space-x-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="搜索对话助手..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <button
              onClick={loadChatAssistants}
              className="inline-flex items-center px-3 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              刷新
            </button>
          </div>
        </div>
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <span className="text-red-800">{error}</span>
          </div>
        </div>
      )}

      {/* 对话助手列表 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="divide-y divide-gray-200">
          {loading ? (
            <div className="p-12 text-center">
              <Loader2 className="w-8 h-8 mx-auto animate-spin text-blue-500 mb-4" />
              <p className="text-gray-500">正在加载对话助手...</p>
            </div>
          ) : filteredAssistants.length === 0 ? (
            <div className="p-12 text-center">
              <Bot className="w-12 h-12 mx-auto text-gray-400 mb-4" />
              <p className="text-gray-600 mb-2">暂无对话助手</p>
              <p className="text-sm text-gray-500">
                这是模拟数据展示，真实的 RAGFlow 对话助手功能正在开发中
              </p>
            </div>
          ) : (
            filteredAssistants.map((assistant) => {
              const isExpanded = expandedAssistants.has(assistant.id);
              const sessions = assistantSessions.get(assistant.id) || [];
              const sessionCount = getSessionCount(assistant.id);

              return (
                <div key={assistant.id} className="border-b border-gray-200 last:border-b-0">
                  {/* 助手基本信息 */}
                  <div
                    className="p-6 hover:bg-gray-50 cursor-pointer transition-colors"
                    onClick={() => toggleAssistantExpansion(assistant.id)}
                  >
                    <div className="flex items-start justify-between">
                      {/* 左侧内容 */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-3 mb-2">
                          <div className={`p-2 rounded-lg ${theme.iconBg} bg-opacity-10`}>
                            <Bot className={`w-5 h-5 ${theme.text.replace('text-', 'text-')}`} />
                          </div>
                          <h3 className="text-lg font-medium text-gray-900">
                            {assistant.name}
                          </h3>
                          <span className="inline-flex items-center px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">
                            活跃
                          </span>
                        </div>

                        <p className="text-sm text-gray-600 mb-3">{assistant.description}</p>

                        <div className="flex items-center space-x-6 text-sm text-gray-600">
                          <div className="flex items-center">
                            <Database className="w-4 h-4 mr-1" />
                            <span>{assistant.dataset_ids.length} 个知识库</span>
                          </div>
                          <div className="flex items-center">
                            <MessageSquare className="w-4 h-4 mr-1" />
                            <span>{sessionCount} 个会话</span>
                          </div>
                          <div className="flex items-center">
                            <Clock className="w-4 h-4 mr-1" />
                            <span>更新: {formatDate(assistant.update_time)}</span>
                          </div>
                        </div>

                        {assistant.dataset_ids.length > 0 && (
                          <div className="mt-2 text-sm text-gray-500">
                            关联知识库: {assistant.dataset_ids.join(', ')}
                          </div>
                        )}
                      </div>

                      {/* 右侧操作和展开指示器 */}
                      <div className="ml-4 flex items-center space-x-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onConversationSelect({ assistant });
                          }}
                          className={`inline-flex items-center px-3 py-1 text-xs font-medium rounded ${theme.primary} ${theme.primaryHover} text-white`}
                        >
                          开始对话
                        </button>
                        <div className={`transform transition-transform ${isExpanded ? 'rotate-180' : ''}`}>
                          <MoreHorizontal className="w-5 h-5 text-gray-400" />
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* 展开的会话列表 */}
                  {isExpanded && sessions.length > 0 && (
                    <div className="px-6 pb-4 bg-gray-50">
                      <div className="border-t border-gray-200 pt-4">
                        <h4 className="text-sm font-medium text-gray-700 mb-3">会话列表 ({sessions.length})</h4>
                        <div className="space-y-2">
                          {sessions.map((session) => (
                            <div
                              key={session.id}
                              className="flex items-center justify-between p-3 bg-white border border-gray-200 rounded-lg hover:bg-blue-50 cursor-pointer transition-colors"
                              onClick={() => onConversationSelect({ assistant, session })}
                            >
                              <div className="flex items-center space-x-3">
                                <MessageSquare className="w-4 h-4 text-gray-400" />
                                <div>
                                  <div className="text-sm font-medium text-gray-900">{session.name}</div>
                                  <div className="text-xs text-gray-500">
                                    创建: {formatDate(session.create_time)} |
                                    消息: {session.message_count}
                                  </div>
                                </div>
                              </div>
                              <div className="text-xs text-gray-400">
                                {formatDate(session.update_time)}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}

                  {isExpanded && sessions.length === 0 && (
                    <div className="px-6 pb-4 bg-gray-50">
                      <div className="border-t border-gray-200 pt-4 text-center text-sm text-gray-500">
                        暂无会话记录
                      </div>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>

        {/* 统计信息 */}
        {!loading && filteredAssistants.length > 0 && (
          <div className="p-4 border-t border-gray-200 bg-gray-50">
            <div className="flex items-center justify-between text-sm text-gray-600">
              <div>
                显示 {filteredAssistants.length} 个助手，共 {chatAssistants.length} 个对话助手
              </div>
              <div>
                总会话数: {Array.from(assistantSessions.values()).reduce((sum, sessions) => sum + sessions.length, 0)}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ConversationList;