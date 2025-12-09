import React, { useState } from 'react';
import { Bot, Plus, Search, Filter, Settings, Play, Pause, Trash2, Edit, MoreHorizontal, Zap, Database, MessageSquare, Brain, Clock } from 'lucide-react';
import { useTheme } from '../../theme';

interface Agent {
  id: string;
  name: string;
  description: string;
  status: 'active' | 'inactive' | 'training';
  type: 'chat' | 'search' | 'hybrid';
  knowledgeBases: string[];
  capabilities: string[];
  totalInteractions: number;
  successRate: number;
  lastActive: string;
  createdAt: string;
  config: {
    temperature: number;
    maxTokens: number;
    responseStyle: 'formal' | 'casual' | 'professional';
    language: string;
  };
}

interface AgentListProps {
  onAgentSelect: (agent: Agent) => void;
  onNewAgent: () => void;
}

const AgentList: React.FC<AgentListProps> = ({
  onAgentSelect,
  onNewAgent
}) => {
  const { theme } = useTheme();
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');

  // 模拟数据 - 实际应该从API获取
  const mockAgents: Agent[] = [
    {
      id: '1',
      name: '技术支持助手',
      description: '专门处理技术问题和故障排除的AI助手',
      status: 'active',
      type: 'chat',
      knowledgeBases: ['技术文档库', 'FAQ知识库'],
      capabilities: ['技术支持', '故障排除', '产品指导'],
      totalInteractions: 1542,
      successRate: 96.5,
      lastActive: '2024-01-15T14:30:00Z',
      createdAt: '2024-01-01T00:00:00Z',
      config: {
        temperature: 0.7,
        maxTokens: 1000,
        responseStyle: 'professional',
        language: 'zh-CN'
      }
    },
    {
      id: '2',
      name: '产品顾问',
      description: '为用户提供产品推荐和购买建议的专业顾问',
      status: 'active',
      type: 'hybrid',
      knowledgeBases: ['产品手册', '行业报告库', '用户评价库'],
      capabilities: ['产品推荐', '购买建议', '市场分析'],
      totalInteractions: 987,
      successRate: 94.2,
      lastActive: '2024-01-15T16:20:00Z',
      createdAt: '2024-01-05T00:00:00Z',
      config: {
        temperature: 0.8,
        maxTokens: 1200,
        responseStyle: 'casual',
        language: 'zh-CN'
      }
    },
    {
      id: '3',
      name: '知识检索专家',
      description: '专注于跨知识库信息检索和整理的专业智能体',
      status: 'inactive',
      type: 'search',
      knowledgeBases: ['技术文档库', '研究论文库', '行业报告库'],
      capabilities: ['信息检索', '数据分析', '报告生成'],
      totalInteractions: 623,
      successRate: 98.1,
      lastActive: '2024-01-14T10:15:00Z',
      createdAt: '2024-01-10T00:00:00Z',
      config: {
        temperature: 0.5,
        maxTokens: 800,
        responseStyle: 'formal',
        language: 'zh-CN'
      }
    },
    {
      id: '4',
      name: '客服智能体',
      description: '7x24小时在线客服，处理用户咨询和投诉',
      status: 'training',
      type: 'chat',
      knowledgeBases: ['FAQ知识库', '服务手册'],
      capabilities: ['客户咨询', '投诉处理', '服务支持'],
      totalInteractions: 445,
      successRate: 92.3,
      lastActive: '2024-01-15T12:45:00Z',
      createdAt: '2024-01-12T00:00:00Z',
      config: {
        temperature: 0.6,
        maxTokens: 900,
        responseStyle: 'professional',
        language: 'zh-CN'
      }
    }
  ];

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'inactive':
        return 'bg-gray-100 text-gray-800';
      case 'training':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status: string) => {
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

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'chat':
        return <MessageSquare className="w-4 h-4 text-blue-500" />;
      case 'search':
        return <Search className="w-4 h-4 text-green-500" />;
      case 'hybrid':
        return <Brain className="w-4 h-4 text-purple-500" />;
      default:
        return <Bot className="w-4 h-4 text-gray-500" />;
    }
  };

  const getTypeText = (type: string) => {
    switch (type) {
      case 'chat':
        return '对话型';
      case 'search':
        return '搜索型';
      case 'hybrid':
        return '混合型';
      default:
        return '未知';
    }
  };

  const getSuccessRateColor = (rate: number) => {
    if (rate >= 95) return 'text-green-600';
    if (rate >= 90) return 'text-yellow-600';
    return 'text-red-600';
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
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

  const filteredAgents = mockAgents.filter(agent => {
    const matchesSearch = agent.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         agent.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || agent.status === statusFilter;
    const matchesType = typeFilter === 'all' || agent.type === typeFilter;

    return matchesSearch && matchesStatus && matchesType;
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <Play className="w-4 h-4 text-green-500" />;
      case 'inactive':
        return <Pause className="w-4 h-4 text-gray-500" />;
      case 'training':
        return <Zap className="w-4 h-4 text-yellow-500 animate-pulse" />;
      default:
        return <Pause className="w-4 h-4 text-gray-500" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* 工具栏 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">智能体管理</h2>
            <button
              onClick={onNewAgent}
              className={`inline-flex items-center px-4 py-2 text-sm font-medium text-white rounded-lg ${theme.primary} ${theme.primaryHover} transition-colors`}
            >
              <Plus className="w-4 h-4 mr-2" />
              创建智能体
            </button>
          </div>

          {/* 搜索和过滤 */}
          <div className="flex items-center space-x-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="搜索智能体..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-gray-700">状态:</label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="all">全部</option>
                <option value="active">活跃</option>
                <option value="inactive">停用</option>
                <option value="training">训练中</option>
              </select>
            </div>

            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-gray-700">类型:</label>
              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="all">全部</option>
                <option value="chat">对话型</option>
                <option value="search">搜索型</option>
                <option value="hybrid">混合型</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* 智能体列表 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="divide-y divide-gray-200">
          {filteredAgents.map((agent) => (
            <div
              key={agent.id}
              className="p-6 hover:bg-gray-50 cursor-pointer transition-colors"
              onClick={() => onAgentSelect(agent)}
            >
              <div className="flex items-start justify-between">
                {/* 左侧内容 */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-3 mb-2">
                    <div className={`p-2 rounded-lg ${theme.iconBg} bg-opacity-10`}>
                      <Bot className={`w-5 h-5 ${theme.text.replace('text-', 'text-')}`} />
                    </div>
                    <div className="flex items-center space-x-2">
                      {getTypeIcon(agent.type)}
                      <h3 className="text-lg font-medium text-gray-900 truncate">
                        {agent.name}
                      </h3>
                    </div>
                    <span className={`inline-flex items-center px-2 py-1 text-xs font-medium rounded-full ${getStatusBadge(agent.status)}`}>
                      {getStatusText(agent.status)}
                    </span>
                  </div>

                  <p className="text-sm text-gray-600 mb-3">{agent.description}</p>

                  <div className="flex items-center space-x-6 text-sm text-gray-600 mb-3">
                    <div className="flex items-center">
                      <Database className="w-4 h-4 mr-1" />
                      <span>{agent.knowledgeBases.length} 个知识库</span>
                    </div>
                    <div className="flex items-center">
                      <MessageSquare className="w-4 h-4 mr-1" />
                      <span>{agent.totalInteractions} 次交互</span>
                    </div>
                    <div className="flex items-center">
                      <Zap className="w-4 h-4 mr-1" />
                      <span className={getSuccessRateColor(agent.successRate)}>
                        {agent.successRate}% 成功率
                      </span>
                    </div>
                    <div className="flex items-center">
                      <Clock className="w-4 h-4 mr-1" />
                      <span>活跃: {formatDate(agent.lastActive)}</span>
                    </div>
                  </div>

                  <div className="flex items-center space-x-4">
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-gray-500">类型:</span>
                      <span className="text-sm font-medium text-gray-700">{getTypeText(agent.type)}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-gray-500">能力:</span>
                      <div className="flex items-center space-x-1">
                        {agent.capabilities.slice(0, 3).map((capability, index) => (
                          <span key={index} className="inline-flex items-center px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded">
                            {capability}
                          </span>
                        ))}
                        {agent.capabilities.length > 3 && (
                          <span className="text-xs text-gray-500">+{agent.capabilities.length - 3}</span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                {/* 右侧操作 */}
                <div className="ml-4 flex items-center space-x-2">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      // 切换状态
                    }}
                    className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
                  >
                    {getStatusIcon(agent.status)}
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      // 编辑配置
                    }}
                    className="p-2 text-gray-400 hover:text-blue-600 transition-colors"
                  >
                    <Settings className="w-5 h-5" />
                  </button>
                  <button className="p-2 text-gray-400 hover:text-gray-600 transition-colors">
                    <MoreHorizontal className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* 分页 */}
        <div className="p-4 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-700">
              显示 1-{filteredAgents.length} 条，共 {filteredAgents.length} 个智能体
            </div>
            <div className="flex items-center space-x-2">
              <button className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed" disabled>
                上一页
              </button>
              <button className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed" disabled>
                下一页
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AgentList;