import React, { useState, useEffect, useCallback } from 'react';
import { MessageCircle, Search, Filter, Download, Plus, Settings, Clock, Tag, User, Archive } from 'lucide-react';

import {
  ConversationHistory,
  ConversationTemplate,
  ConversationListParams,
  CreateConversationRequest,
  ExportFormat,
  ApiResponse
} from '../../types/enhanced';

import { conversationApi, conversationTemplateApi } from '../../api/conversationApi';

interface ConversationInterfaceProps {
  knowledgeBaseId: number;
  knowledgeBaseName: string;
  className?: string;
}

export const ConversationInterface: React.FC<ConversationInterfaceProps> = ({
  knowledgeBaseId,
  knowledgeBaseName,
  className = ''
}) => {
  // 状态管理
  const [conversations, setConversations] = useState<ConversationHistory[]>([]);
  const [templates, setTemplates] = useState<ConversationTemplate[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<ConversationHistory | null>(null);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [showFilters, setShowFilters] = useState(false);
  const [showNewConversation, setShowNewConversation] = useState(false);
  const [showTemplates, setShowTemplates] = useState(false);

  // 分页状态
  const [pagination, setPagination] = useState({
    page: 1,
    per_page: 20,
    total: 0,
    pages: 0,
    has_prev: false,
    has_next: false
  });

  // 获取对话列表
  const fetchConversations = useCallback(async (params: Partial<ConversationListParams> = {}) => {
    setLoading(true);
    try {
      const response = await conversationApi.getConversations(knowledgeBaseId, {
        page: pagination.page,
        per_page: pagination.per_page,
        search: searchTerm || undefined,
        tags: selectedTags.length > 0 ? selectedTags : undefined,
        ...params
      });

      setConversations(response.conversations);
      setPagination(prev => ({
        ...prev,
        total: response.pagination.total,
        pages: response.pagination.pages,
        has_prev: response.pagination.page > 1,
        has_next: response.pagination.page < response.pagination.pages
      }));
    } catch (error) {
      console.error('获取对话列表失败:', error);
    } finally {
      setLoading(false);
    }
  }, [knowledgeBaseId, pagination.page, pagination.per_page, searchTerm, selectedTags]);

  // 获取模板列表
  const fetchTemplates = useCallback(async () => {
    try {
      const response = await conversationTemplateApi.getTemplates();
      setTemplates(response);
    } catch (error) {
      console.error('获取模板列表失败:', error);
    }
  }, []);

  // 创建新对话
  const createConversation = useCallback(async (request: CreateConversationRequest) => {
    setLoading(true);
    try {
      const newConversation = await conversationApi.createConversation(knowledgeBaseId, request);
      setConversations(prev => [newConversation, ...prev]);
      setSelectedConversation(newConversation);
      setShowNewConversation(false);
      return newConversation;
    } catch (error) {
      console.error('创建对话失败:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  }, [knowledgeBaseId]);

  // 应用模板创建对话
  const applyTemplate = useCallback(async (templateId: number, parameters: Record<string, any> = {}) => {
    setLoading(true);
    try {
      const newConversation = await conversationTemplateApi.applyTemplate(templateId, knowledgeBaseId, parameters);
      setConversations(prev => [newConversation, ...prev]);
      setSelectedConversation(newConversation);
      setShowTemplates(false);
      return newConversation;
    } catch (error) {
      console.error('应用模板失败:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  }, [knowledgeBaseId]);

  // 删除对话
  const deleteConversation = useCallback(async (conversationId: number) => {
    try {
      await conversationApi.deleteConversation(knowledgeBaseId, conversationId);
      setConversations(prev => prev.filter(c => c.id !== conversationId));
      if (selectedConversation?.id === conversationId) {
        setSelectedConversation(null);
      }
    } catch (error) {
      console.error('删除对话失败:', error);
      throw error;
    }
  }, [knowledgeBaseId, selectedConversation]);

  // 导出对话
  const exportConversation = useCallback(async (conversationId: number, format: ExportFormat) => {
    try {
      const exportData = await conversationApi.exportConversation(knowledgeBaseId, conversationId, format);
      // 创建下载链接
      const blob = new Blob([exportData], {
        type: format === 'json' ? 'application/json' : 'text/plain'
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `conversation_${conversationId}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('导出对话失败:', error);
      throw error;
    }
  }, [knowledgeBaseId]);

  // 获取所有标签
  const getAllTags = useCallback(() => {
    const tags = new Set<string>();
    conversations.forEach(conv => {
      conv.tags.forEach(tag => tags.add(tag));
    });
    return Array.from(tags);
  }, [conversations]);

  // 格式化时间
  const formatDate = useCallback((dateString: string) => {
    return new Date(dateString).toLocaleString('zh-CN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }, []);

  // 分页处理
  const handlePageChange = useCallback((newPage: number) => {
    setPagination(prev => ({ ...prev, page: newPage }));
  }, []);

  // 搜索处理
  const handleSearch = useCallback((term: string) => {
    setSearchTerm(term);
    setPagination(prev => ({ ...prev, page: 1 })); // 重置到第一页
  }, []);

  // 标签过滤处理
  const handleTagFilter = useCallback((tag: string, checked: boolean) => {
    if (checked) {
      setSelectedTags(prev => [...prev, tag]);
    } else {
      setSelectedTags(prev => prev.filter(t => t !== tag));
    }
    setPagination(prev => ({ ...prev, page: 1 })); // 重置到第一页
  }, []);

  // 初始化
  useEffect(() => {
    fetchConversations();
    fetchTemplates();
  }, [fetchConversations, fetchTemplates]);

  // 当搜索条件变化时重新获取数据
  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      fetchConversations();
    }, 500); // 防抖500ms

    return () => clearTimeout(debounceTimer);
  }, [searchTerm, selectedTags, pagination.page, fetchConversations]);

  return (
    <div className={`conversation-interface h-full flex ${className}`}>
      {/* 左侧：对话列表 */}
      <div className="w-1/3 border-r border-gray-200 bg-white flex flex-col">
        {/* 头部工具栏 */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">对话历史</h3>
            <div className="flex space-x-2">
              <button
                onClick={() => setShowNewConversation(true)}
                className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                title="新建对话"
              >
                <Plus className="w-4 h-4" />
              </button>
              <button
                onClick={() => setShowTemplates(true)}
                className="p-2 text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                title="从模板创建"
              >
                <Settings className="w-4 h-4" />
              </button>
              <button
                onClick={() => setShowFilters(!showFilters)}
                className="p-2 text-gray-600 hover:bg-gray-50 rounded-lg transition-colors"
                title="过滤选项"
              >
                <Filter className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* 搜索框 */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="搜索对话..."
              value={searchTerm}
              onChange={(e) => handleSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* 过滤选项 */}
          {showFilters && (
            <div className="mt-4 p-3 bg-gray-50 rounded-lg">
              <h4 className="text-sm font-medium text-gray-700 mb-2">标签过滤</h4>
              <div className="flex flex-wrap gap-2">
                {getAllTags().map(tag => (
                  <label key={tag} className="flex items-center space-x-1 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedTags.includes(tag)}
                      onChange={(e) => handleTagFilter(tag, e.target.checked)}
                      className="rounded text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-600">{tag}</span>
                  </label>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* 对话列表 */}
        <div className="flex-1 overflow-y-auto">
          {loading ? (
            <div className="flex items-center justify-center h-32">
              <div className="text-gray-500">加载中...</div>
            </div>
          ) : conversations.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-32 text-gray-500">
              <MessageCircle className="w-12 h-12 mb-2 text-gray-300" />
              <p>暂无对话历史</p>
              <button
                onClick={() => setShowNewConversation(true)}
                className="mt-2 text-blue-600 hover:text-blue-700 text-sm"
              >
                创建第一个对话
              </button>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {conversations.map(conversation => (
                <div
                  key={conversation.id}
                  onClick={() => setSelectedConversation(conversation)}
                  className={`p-4 hover:bg-gray-50 cursor-pointer transition-colors ${
                    selectedConversation?.id === conversation.id ? 'bg-blue-50' : ''
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <h4 className="text-sm font-medium text-gray-900 truncate">
                        {conversation.title}
                      </h4>
                      <div className="flex items-center mt-1 text-xs text-gray-500">
                        <Clock className="w-3 h-3 mr-1" />
                        {formatDate(conversation.updated_at)}
                      </div>
                      <div className="flex items-center mt-1">
                        {conversation.tags.map(tag => (
                          <span
                            key={tag}
                            className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 mr-1"
                          >
                            <Tag className="w-3 h-3 mr-1" />
                            {tag}
                          </span>
                        ))}
                      </div>
                      {conversation.user_id && (
                        <div className="flex items-center mt-1 text-xs text-gray-500">
                          <User className="w-3 h-3 mr-1" />
                          {conversation.user_id}
                        </div>
                      )}
                    </div>
                    <div className="flex items-center space-x-1 ml-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          exportConversation(conversation.id, 'json');
                        }}
                        className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
                        title="导出"
                      >
                        <Download className="w-4 h-4" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteConversation(conversation.id);
                        }}
                        className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                        title="删除"
                      >
                        <Archive className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 分页控制 */}
        {pagination.pages > 1 && (
          <div className="p-4 border-t border-gray-200">
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-700">
                第 {pagination.page} 页，共 {pagination.pages} 页
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => handlePageChange(pagination.page - 1)}
                  disabled={!pagination.has_prev}
                  className="px-3 py-1 text-sm border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                >
                  上一页
                </button>
                <button
                  onClick={() => handlePageChange(pagination.page + 1)}
                  disabled={!pagination.has_next}
                  className="px-3 py-1 text-sm border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                >
                  下一页
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 右侧：对话详情 */}
      <div className="flex-1 flex flex-col">
        {selectedConversation ? (
          <ConversationDetail
            conversation={selectedConversation}
            knowledgeBaseId={knowledgeBaseId}
            onUpdate={(updatedConversation) => {
              setConversations(prev => prev.map(c =>
                c.id === updatedConversation.id ? updatedConversation : c
              ));
              setSelectedConversation(updatedConversation);
            }}
          />
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-500">
            <div className="text-center">
              <MessageCircle className="w-16 h-16 mx-auto mb-4 text-gray-300" />
              <p className="text-lg">选择一个对话查看详情</p>
              <p className="text-sm mt-2">或者创建一个新对话开始聊天</p>
            </div>
          </div>
        )}
      </div>

      {/* 新建对话对话框 */}
      {showNewConversation && (
        <NewConversationDialog
          knowledgeBaseId={knowledgeBaseId}
          knowledgeBaseName={knowledgeBaseName}
          onClose={() => setShowNewConversation(false)}
          onCreate={createConversation}
        />
      )}

      {/* 模板选择对话框 */}
      {showTemplates && (
        <TemplateSelectionDialog
          templates={templates}
          onClose={() => setShowTemplates(false)}
          onSelect={applyTemplate}
        />
      )}
    </div>
  );
};

// 对话详情组件（内部组件）
interface ConversationDetailProps {
  conversation: ConversationHistory;
  knowledgeBaseId: number;
  onUpdate: (conversation: ConversationHistory) => void;
}

const ConversationDetail: React.FC<ConversationDetailProps> = ({
  conversation,
  knowledgeBaseId,
  onUpdate
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(conversation.title);
  const [editTags, setEditTags] = useState(conversation.tags);

  const handleSave = async () => {
    try {
      const updatedConversation = await conversationApi.updateConversation(knowledgeBaseId, conversation.id, {
        title: editTitle,
        tags: editTags
      });
      onUpdate(updatedConversation);
      setIsEditing(false);
    } catch (error) {
      console.error('更新对话失败:', error);
    }
  };

  const handleCancel = () => {
    setEditTitle(conversation.title);
    setEditTags(conversation.tags);
    setIsEditing(false);
  };

  return (
    <div className="h-full flex flex-col">
      {/* 头部 */}
      <div className="p-4 border-b border-gray-200 bg-white">
        {isEditing ? (
          <div className="space-y-3">
            <input
              type="text"
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              placeholder="对话标题"
            />
            <div className="flex space-x-2">
              <input
                type="text"
                value={editTags.join(', ')}
                onChange={(e) => setEditTags(e.target.value.split(',').map(tag => tag.trim()).filter(tag => tag))}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="标签，用逗号分隔"
              />
              <button
                onClick={handleSave}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                保存
              </button>
              <button
                onClick={handleCancel}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                取消
              </button>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">{conversation.title}</h2>
              <div className="flex items-center mt-2 space-x-4">
                <span className="text-sm text-gray-500">
                  {conversation.messages.length} 条消息
                </span>
                {conversation.tags.map(tag => (
                  <span
                    key={tag}
                    className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
            <button
              onClick={() => setIsEditing(true)}
              className="p-2 text-gray-600 hover:bg-gray-50 rounded-lg transition-colors"
            >
              <Settings className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>

      {/* 消息列表 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {conversation.messages.map((message, index) => (
          <div
            key={message.id || index}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-2xl px-4 py-2 rounded-lg ${
                message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-900'
              }`}
            >
              <div className="text-sm font-medium mb-1">
                {message.role === 'user' ? '用户' : '助手'}
              </div>
              <div className="whitespace-pre-wrap">{message.content}</div>
              <div className={`text-xs mt-2 ${
                message.role === 'user' ? 'text-blue-200' : 'text-gray-500'
              }`}>
                {new Date(message.timestamp).toLocaleString('zh-CN')}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// 新建对话对话框组件
interface NewConversationDialogProps {
  knowledgeBaseId: number;
  knowledgeBaseName: string;
  onClose: () => void;
  onCreate: (request: CreateConversationRequest) => Promise<ConversationHistory>;
}

const NewConversationDialog: React.FC<NewConversationDialogProps> = ({
  knowledgeBaseId,
  knowledgeBaseName,
  onClose,
  onCreate
}) => {
  const [title, setTitle] = useState('');
  const [message, setMessage] = useState('');
  const [tags, setTags] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    setLoading(true);
    try {
      await onCreate({
        title: title.trim(),
        messages: message.trim() ? [{
          role: 'user' as const,
          content: message.trim(),
          timestamp: new Date().toISOString()
        }] : [],
        tags: tags.split(',').map(tag => tag.trim()).filter(tag => tag),
        user_id: 'current-user' // 应该从用户上下文获取
      });
      onClose();
    } catch (error) {
      console.error('创建对话失败:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
        <div className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            新建对话 - {knowledgeBaseName}
          </h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                对话标题 *
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="输入对话标题"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                首条消息（可选）
              </label>
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                rows={4}
                placeholder="输入首条消息内容"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                标签
              </label>
              <input
                type="text"
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="标签，用逗号分隔"
              />
            </div>
            <div className="flex space-x-3 pt-4">
              <button
                type="submit"
                disabled={loading || !title.trim()}
                className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? '创建中...' : '创建对话'}
              </button>
              <button
                type="button"
                onClick={onClose}
                className="flex-1 border border-gray-300 py-2 px-4 rounded-lg hover:bg-gray-50 transition-colors"
              >
                取消
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

// 模板选择对话框组件
interface TemplateSelectionDialogProps {
  templates: ConversationTemplate[];
  onClose: () => void;
  onSelect: (templateId: number, parameters?: Record<string, any>) => Promise<ConversationHistory>;
}

const TemplateSelectionDialog: React.FC<TemplateSelectionDialogProps> = ({
  templates,
  onClose,
  onSelect
}) => {
  const [selectedTemplate, setSelectedTemplate] = useState<ConversationTemplate | null>(null);
  const [parameters, setParameters] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(false);

  const handleSelect = async () => {
    if (!selectedTemplate) return;

    setLoading(true);
    try {
      await onSelect(selectedTemplate.id, parameters);
      onClose();
    } catch (error) {
      console.error('应用模板失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleParameterChange = (paramName: string, value: any) => {
    setParameters(prev => ({
      ...prev,
      [paramName]: value
    }));
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl mx-4 max-h-[80vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              选择对话模板
            </h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              ×
            </button>
          </div>

          <div className="space-y-4">
            {templates.length === 0 ? (
              <p className="text-gray-500 text-center py-8">暂无可用模板</p>
            ) : (
              templates.map(template => (
                <div
                  key={template.id}
                  className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                    selectedTemplate?.id === template.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => setSelectedTemplate(template)}
                >
                  <h4 className="font-medium text-gray-900">{template.name}</h4>
                  <p className="text-sm text-gray-600 mt-1">{template.description}</p>
                  <div className="flex items-center mt-2 space-x-4">
                    <span className="text-xs bg-gray-100 text-gray-800 px-2 py-1 rounded">
                      {template.category}
                    </span>
                    <span className="text-xs text-gray-500">
                      使用次数: {template.usage_count}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* 模板参数 */}
          {selectedTemplate && selectedTemplate.parameters.length > 0 && (
            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-3">模板参数</h4>
              <div className="space-y-3">
                {selectedTemplate.parameters.map(param => (
                  <div key={param.name}>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {param.description} {param.required && <span className="text-red-500">*</span>}
                    </label>
                    {param.type === 'select' ? (
                      <select
                        value={parameters[param.name] || param.default_value || ''}
                        onChange={(e) => handleParameterChange(param.name, e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        required={param.required}
                      >
                        <option value="">请选择...</option>
                        {param.options?.map(option => (
                          <option key={option} value={option}>{option}</option>
                        ))}
                      </select>
                    ) : param.type === 'textarea' ? (
                      <textarea
                        value={parameters[param.name] || param.default_value || ''}
                        onChange={(e) => handleParameterChange(param.name, e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        rows={3}
                        required={param.required}
                      />
                    ) : (
                      <input
                        type={param.type}
                        value={parameters[param.name] || param.default_value || ''}
                        onChange={(e) => handleParameterChange(param.name, e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        required={param.required}
                      />
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex space-x-3 mt-6">
            <button
              onClick={handleSelect}
              disabled={!selectedTemplate || loading}
              className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? '应用中...' : selectedTemplate ? '应用模板' : '请选择模板'}
            </button>
            <button
              onClick={onClose}
              className="flex-1 border border-gray-300 py-2 px-4 rounded-lg hover:bg-gray-50 transition-colors"
            >
              取消
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConversationInterface;