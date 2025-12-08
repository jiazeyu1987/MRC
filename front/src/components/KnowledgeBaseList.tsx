import React, { useState, useEffect } from 'react';
import { RefreshCw, Database, FileText, Calendar, Search, AlertCircle, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { useTheme } from '../theme';
import { knowledgeApi } from '../api/knowledgeApi';
import { KnowledgeBase, KnowledgeBaseListParams } from '../types/knowledge';
import { handleError } from '../utils/errorHandler';

interface KnowledgeBaseListProps {
  onKnowledgeBaseSelect?: (knowledgeBase: KnowledgeBase) => void;
  selectedKnowledgeBaseId?: number;
  multiSelect?: boolean;
  selectedIds?: Set<number>;
  onSelectionChange?: (selectedIds: Set<number>) => void;
}

const KnowledgeBaseList: React.FC<KnowledgeBaseListProps> = ({
  onKnowledgeBaseSelect,
  selectedKnowledgeBaseId,
  multiSelect = false,
  selectedIds = new Set(),
  onSelectionChange
}) => {
  const { theme } = useTheme();
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [pagination, setPagination] = useState({
    page: 1,
    pageSize: 20,
    total: 0,
    pages: 0
  });

  // 加载知识库列表
  const loadKnowledgeBases = async (resetPage: boolean = false) => {
    try {
      setLoading(true);
      setError(null);

      const page = resetPage ? 1 : pagination.page;
      const params: KnowledgeBaseListParams = {
        page,
        page_size: pagination.pageSize,
        search: searchTerm || undefined,
        status: statusFilter as any || undefined,
        sort_by: 'created_at',
        sort_order: 'desc'
      };

      const response = await knowledgeApi.getKnowledgeBases(params);

      setKnowledgeBases(response.knowledge_bases);
      setPagination(prev => ({
        ...prev,
        page: response.page,
        total: response.total,
        pages: response.pages
      }));
    } catch (error) {
      const errorMessage = handleError(error, false);
      setError(errorMessage);
      console.error('Failed to load knowledge bases:', error);
    } finally {
      setLoading(false);
    }
  };

  // 刷新所有知识库
  const handleRefreshAll = async () => {
    try {
      setRefreshing(true);
      setError(null);

      const result = await knowledgeApi.refreshKnowledgeBases();

      // 刷新成功后重新加载列表
      await loadKnowledgeBases();

      console.log('Refresh result:', result);

    } catch (error) {
      const errorMessage = handleError(error);
      setError(errorMessage);
    } finally {
      setRefreshing(false);
    }
  };

  // 刷新单个知识库
  const handleRefreshSingle = async (knowledgeBaseId: number) => {
    try {
      const result = await knowledgeApi.refreshKnowledgeBase(knowledgeBaseId);

      // 刷新成功后重新加载列表
      await loadKnowledgeBases();

      console.log('Single refresh result:', result);

    } catch (error) {
      const errorMessage = handleError(error);
      setError(errorMessage);
    }
  };

  // 处理知识库选择
  const handleKnowledgeBaseClick = (knowledgeBase: KnowledgeBase) => {
    if (onKnowledgeBaseSelect) {
      onKnowledgeBaseSelect(knowledgeBase);
    }
  };

  // 处理多选
  const handleCheckboxChange = (knowledgeBaseId: number, checked: boolean) => {
    if (!multiSelect || !onSelectionChange) return;

    const newSelectedIds = new Set(selectedIds);
    if (checked) {
      newSelectedIds.add(knowledgeBaseId);
    } else {
      newSelectedIds.delete(knowledgeBaseId);
    }
    onSelectionChange(newSelectedIds);
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

  // 获取状态图标和颜色
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
          icon: AlertCircle,
          color: 'text-red-500',
          bgColor: 'bg-red-100',
          text: '错误'
        };
      default:
        return {
          icon: AlertCircle,
          color: 'text-gray-500',
          bgColor: 'bg-gray-100',
          text: status
        };
    }
  };

  // 初始化和搜索变化时重新加载数据
  useEffect(() => {
    loadKnowledgeBases(true);
  }, [searchTerm, statusFilter]);

  // 状态图标组件
  const StatusIcon = ({ status }: { status: string }) => {
    const statusInfo = getStatusInfo(status);
    const Icon = statusInfo.icon;
    return (
      <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${statusInfo.bgColor} ${statusInfo.color}`}>
        <Icon className="w-3 h-3 mr-1" />
        {statusInfo.text}
      </div>
    );
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      {/* 头部工具栏 */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center">
            <Database className="w-5 h-5 mr-2 text-blue-500" />
            知识库列表
          </h2>
          <button
            onClick={handleRefreshAll}
            disabled={refreshing || loading}
            className={`flex items-center px-3 py-2 text-sm font-medium text-white rounded-md ${theme.primary} ${theme.primaryHover} disabled:opacity-50 disabled:cursor-not-allowed transition-colors`}
          >
            {refreshing ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <RefreshCw className="w-4 h-4 mr-2" />
            )}
            {refreshing ? '刷新中...' : '刷新全部'}
          </button>
        </div>

        {/* 搜索和过滤 */}
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="搜索知识库名称或描述..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className={`w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none ${theme.ring} transition-colors`}
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className={`px-3 py-2 border border-gray-300 rounded-md focus:outline-none ${theme.ring} transition-colors`}
          >
            <option value="">全部状态</option>
            <option value="active">活跃</option>
            <option value="inactive">未激活</option>
            <option value="error">错误</option>
          </select>
        </div>
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="p-4 bg-red-50 border-l-4 border-red-400">
          <div className="flex">
            <AlertCircle className="w-5 h-5 text-red-400" />
            <div className="ml-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* 知识库列表 */}
      <div className="divide-y divide-gray-200">
        {loading ? (
          <div className="p-8 text-center">
            <Loader2 className="w-8 h-8 mx-auto animate-spin text-blue-500 mb-3" />
            <p className="text-gray-500">加载知识库列表中...</p>
          </div>
        ) : knowledgeBases.length === 0 ? (
          <div className="p-8 text-center">
            <Database className="w-12 h-12 mx-auto text-gray-400 mb-3" />
            <p className="text-gray-500 text-lg font-medium mb-1">暂无知识库</p>
            <p className="text-gray-400 text-sm">
              {searchTerm || statusFilter ? '没有找到符合条件的知识库' : '点击"刷新全部"按钮从RAGFlow获取知识库'}
            </p>
          </div>
        ) : (
          knowledgeBases.map((kb) => {
            const isSelected = selectedKnowledgeBaseId === kb.id || selectedIds.has(kb.id);
            return (
              <div
                key={kb.id}
                className={`p-4 hover:bg-gray-50 transition-colors cursor-pointer ${
                  isSelected ? `${theme.bgSoft} border-l-4 ${theme.border.replace('border-', 'border-l-')}` : ''
                }`}
                onClick={() => handleKnowledgeBaseClick(kb)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3 flex-1">
                    {/* 多选框 */}
                    {multiSelect && (
                      <input
                        type="checkbox"
                        checked={selectedIds.has(kb.id)}
                        onChange={(e) => {
                          e.stopPropagation();
                          handleCheckboxChange(kb.id, e.target.checked);
                        }}
                        className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                    )}

                    {/* 知识库图标 */}
                    <div className={`p-2 rounded-lg ${theme.iconBg} bg-opacity-10`}>
                      <Database className={`w-5 h-5 ${theme.text.replace('text-', 'text-')}`} />
                    </div>

                    {/* 知识库信息 */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="text-sm font-medium text-gray-900 truncate">
                          {kb.name}
                        </h3>
                        <StatusIcon status={kb.status} />
                      </div>

                      {kb.description && (
                        <p className="text-sm text-gray-600 mb-2 line-clamp-2">
                          {kb.description}
                        </p>
                      )}

                      <div className="flex flex-wrap items-center gap-4 text-xs text-gray-500">
                        <div className="flex items-center">
                          <FileText className="w-3 h-3 mr-1" />
                          <span>{kb.document_count.toLocaleString()} 个文档</span>
                        </div>
                        <div className="flex items-center">
                          <Database className="w-3 h-3 mr-1" />
                          <span>{formatFileSize(kb.total_size)}</span>
                        </div>
                        <div className="flex items-center">
                          <Calendar className="w-3 h-3 mr-1" />
                          <span>{formatDate(kb.created_at)}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* 操作按钮 */}
                  <div className="flex items-center space-x-2 ml-4">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRefreshSingle(kb.id);
                      }}
                      className={`p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-colors`}
                      title="刷新知识库"
                    >
                      <RefreshCw className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* 分页信息 */}
      {!loading && knowledgeBases.length > 0 && pagination.pages > 1 && (
        <div className="p-4 border-t border-gray-200 bg-gray-50">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <span>
              显示 {((pagination.page - 1) * pagination.pageSize) + 1} - {Math.min(pagination.page * pagination.pageSize, pagination.total)}
              共 {pagination.total} 个知识库
            </span>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => {
                  setPagination(prev => ({ ...prev, page: Math.max(1, prev.page - 1) }));
                  loadKnowledgeBases();
                }}
                disabled={pagination.page <= 1}
                className="px-3 py-1 border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
              >
                上一页
              </button>
              <span>
                第 {pagination.page} / {pagination.pages} 页
              </span>
              <button
                onClick={() => {
                  setPagination(prev => ({ ...prev, page: Math.min(prev.pages, prev.page + 1) }));
                  loadKnowledgeBases();
                }}
                disabled={pagination.page >= pagination.pages}
                className="px-3 py-1 border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
              >
                下一页
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default KnowledgeBaseList;