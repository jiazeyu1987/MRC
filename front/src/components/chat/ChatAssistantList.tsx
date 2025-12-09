import React, { useState, useEffect } from 'react';
import { MessageSquare, Plus, Search, Filter, Settings, Play, Pause, Trash2, Edit, MoreHorizontal, Clock, AlertCircle, Loader, Zap } from 'lucide-react';
import { useTheme } from '../../theme';
import { ragflowApi, ChatAssistant } from '../../api/knowledgeApi';

interface ChatAssistantListProps {
  onAssistantSelect: (assistant: ChatAssistant) => void;
  onNewAssistant: () => void;
}

const ChatAssistantList: React.FC<ChatAssistantListProps> = ({
  onAssistantSelect,
  onNewAssistant
}) => {
  const { theme } = useTheme();
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [assistants, setAssistants] = useState<ChatAssistant[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // 从RAGFlow API获取聊天助手列表
  useEffect(() => {
    const fetchAssistants = async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await ragflowApi.getChatAssistants();
        if (response.success) {
          setAssistants(response.data);
        } else {
          setError(response.message || '获取聊天助手列表失败');
        }
      } catch (err) {
        console.error('Failed to fetch chat assistants:', err);
        setError('获取聊天助手列表时发生错误');
      } finally {
        setLoading(false);
      }
    };

    fetchAssistants();
  }, []);

  const getStatusBadge = (status?: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-100';
      case 'inactive':
        return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-100';
      case 'training':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-700 dark:text-yellow-100';
      default:
        return 'bg-blue-100 text-blue-800 dark:bg-blue-700 dark:text-blue-100';
    }
  };

  const getStatusText = (status?: string) => {
    switch (status) {
      case 'active':
        return '活跃';
      case 'inactive':
        return '停用';
      case 'training':
        return '训练中';
      default:
        return '未知';
    }
  };

  const formatCreatedAt = (createdAt?: string) => {
    if (!createdAt) return '未知';
    try {
      return new Date(createdAt).toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
      });
    } catch {
      return '格式错误';
    }
  };

  const filteredAssistants = assistants.filter(assistant => {
    const matchesSearch = assistant.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          (assistant.description && assistant.description.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesStatus = statusFilter === 'all' || assistant.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const handleChat = async (assistant: ChatAssistant) => {
    try {
      // TODO: 实现与聊天助手的对话功能
      console.log('Starting chat with assistant:', assistant.name);
      // const response = await ragflowApi.chatWithAssistant(assistant.id, '你好！');
      // 处理对话响应
    } catch (err) {
      console.error('Failed to chat with assistant:', err);
      setError('与聊天助手对话时发生错误');
    }
  };

  return (
    <div className="space-y-6">
      {/* 搜索和过滤栏 */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="搜索聊天助手..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className={`pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 w-full ${
              theme === 'dark' ? 'bg-gray-800 border-gray-700 text-white' : 'bg-white border-gray-300 text-gray-900'
            }`}
          />
        </div>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className={`px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            theme === 'dark' ? 'bg-gray-800 border-gray-700 text-white' : 'bg-white border-gray-300 text-gray-900'
          }`}
        >
          <option value="all">所有状态</option>
          <option value="active">活跃</option>
          <option value="inactive">停用</option>
          <option value="training">训练中</option>
        </select>

        <button
          onClick={onNewAssistant}
          className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
        >
          <Plus className="h-4 w-4" />
          新建聊天助手
        </button>
      </div>

      {/* 加载状态 */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <Loader className="h-8 w-8 animate-spin mr-3" />
          <span>正在获取聊天助手列表...</span>
        </div>
      )}

      {/* 错误状态 */}
      {!loading && error && (
        <div className="flex items-center justify-center py-12 text-red-600">
          <AlertCircle className="h-6 w-6 mr-2" />
          <span>{error}</span>
        </div>
      )}

      {/* 聊天助手列表 */}
      {!loading && !error && (
        <>
          {filteredAssistants.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <MessageSquare className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>暂无聊天助手数据</p>
              <p className="text-sm mt-2">请确保RAGFlow服务正常运行</p>
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {filteredAssistants.map((assistant) => (
                <div
                  key={assistant.id}
                  className={`border rounded-lg p-6 hover:shadow-md transition-shadow cursor-pointer ${
                    theme === 'dark'
                      ? 'bg-gray-800 border-gray-700 hover:bg-gray-700'
                      : 'bg-white border-gray-200 hover:bg-gray-50'
                  }`}
                >
                  {/* 聊天助手头部 */}
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
                        <MessageSquare className="h-6 w-6 text-green-600 dark:text-green-400" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="font-medium text-lg truncate" title={assistant.name}>
                          {assistant.name}
                        </h3>
                        <p className="text-sm text-gray-500 dark:text-gray-400" title={assistant.description}>
                          {assistant.description || '暂无描述'}
                        </p>
                      </div>
                    </div>

                    {/* 状态徽章 */}
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusBadge(assistant.status)}`}>
                      {getStatusText(assistant.status)}
                    </span>
                  </div>

                  {/* 聊天助手信息 */}
                  <div className="space-y-3">
                    {/* 语言和系统提示 */}
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600 dark:text-gray-400">
                        语言: {assistant.language || 'zh-CN'}
                      </span>
                      {assistant.system_prompt && (
                        <span className="text-xs bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-2 py-1 rounded">
                          有系统提示
                        </span>
                      )}
                    </div>

                    {/* 数据集信息 */}
                    {assistant.datasets && assistant.datasets.length > 0 && (
                      <div className="flex items-center space-x-2 text-sm">
                        <Zap className="h-4 w-4 text-purple-500" />
                        <span className="text-gray-600 dark:text-gray-400">
                          {assistant.datasets.length} 个数据集
                        </span>
                      </div>
                    )}

                    {/* 知识图谱 */}
                    {assistant.knowledge_graph && (
                      <div className="flex items-center space-x-2 text-sm">
                        <div className="h-4 w-4 bg-purple-500 rounded-full" />
                        <span className="text-gray-600 dark:text-gray-400">
                          知识图谱
                        </span>
                      </div>
                    )}

                    {/* 头像 */}
                    {assistant.avatar && (
                      <div className="flex items-center space-x-2 text-sm">
                        <div className="w-8 h-8 bg-gray-200 dark:bg-gray-700 rounded-full flex items-center justify-center">
                          <img src={assistant.avatar} alt={assistant.name} className="w-full h-full rounded-full object-cover" />
                        </div>
                        <span className="text-gray-600 dark:text-gray-400">有头像</span>
                      </div>
                    )}

                    {/* 创建时间 */}
                    <div className="flex items-center space-x-2 text-sm text-gray-500 dark:text-gray-400">
                      <Clock className="h-4 w-4" />
                      <span>创建于 {formatCreatedAt(assistant.created_at)}</span>
                    </div>
                  </div>

                  {/* 操作按钮 */}
                  <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700 mt-4">
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleChat(assistant)}
                        className="p-2 text-green-600 hover:bg-green-50 dark:text-green-400 dark:hover:bg-green-900/20 rounded-lg transition-colors"
                        title="开始对话"
                      >
                        <Play className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => onAssistantSelect(assistant)}
                        className="p-2 text-blue-600 hover:bg-blue-50 dark:text-blue-400 dark:hover:bg-blue-900/20 rounded-lg transition-colors"
                        title="查看详情"
                      >
                        <Settings className="h-4 w-4" />
                      </button>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        // TODO: 实现更多操作
                      }}
                      className="p-2 text-gray-600 hover:bg-gray-50 dark:text-gray-400 dark:hover:bg-gray-700 rounded-lg transition-colors"
                      title="更多操作"
                    >
                      <MoreHorizontal className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* 统计信息 */}
      {!loading && !error && filteredAssistants.length > 0 && (
        <div className="text-center text-sm text-gray-500 dark:text-gray-400">
          显示 {filteredAssistants.length} 个聊天助手（共 {assistants.length} 个）
        </div>
      )}

      {/* 功能提示 */}
      {!loading && !error && assistants.length > 0 && (
        <div className={`p-4 rounded-lg border ${
          theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-blue-50 border-blue-200'
        }`}>
          <div className="flex items-start space-x-3">
            <AlertCircle className="h-5 w-5 text-blue-500 mt-0.5" />
            <div className="text-sm text-blue-800 dark:text-blue-200">
              <p className="font-medium mb-1">聊天助手功能</p>
              <ul className="text-sm space-y-1 text-blue-700 dark:text-blue-300">
                <li>• 点击"开始对话"与聊天助手进行交流</li>
                <li>• 点击"查看详情"查看聊天助手的详细配置</li>
                <li>• 聊天助手可以连接到知识库进行增强对话</li>
                <li>• 支持多种语言和系统提示配置</li>
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatAssistantList;