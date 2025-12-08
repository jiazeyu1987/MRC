/**
 * Document List Component
 *
 * A comprehensive document listing component with search, filtering, sorting,
 * and document management actions for the Knowledge Base Document Management system.
 *
 * Features:
 * - Searchable document list with real-time filtering
 * - Multiple sort options (name, date, size, status)
 * - Status-based filtering (upload, processing, completed, failed)
 * - File type filtering
 * - Pagination with configurable page sizes
 * - Document preview and actions (view, download, delete)
 * - Batch selection and operations
 * - Real-time status updates
 *
 * @author Knowledge Base Document Management System
 * @version 1.0.0
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Search,
  Filter,
  FileText,
  Download,
  Trash2,
  Eye,
  Calendar,
  HardDrive,
  CheckCircle,
  AlertCircle,
  Clock,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  ChevronLeft,
  ChevronRight,
  MoreVertical,
  Grid,
  List,
  Settings
} from 'lucide-react';
import { knowledgeApi } from '../api/knowledgeApi';
import {
  Document,
  DocumentFilters,
  DocumentListResponse,
  DocumentStatus,
  formatFileSize,
  isDocumentCompleted,
  isDocumentProcessing,
  isDocumentFailed,
  getStatusColor,
  getStatusIcon
} from '../types/document';

interface DocumentListProps {
  knowledgeBaseId: string;
  onDocumentSelect?: (document: Document) => void;
  onDocumentDelete?: (documentId: string) => void;
  refreshTrigger?: number; // Trigger refresh when this changes
  className?: string;
}

interface ViewMode {
  type: 'grid' | 'list';
  columns: number;
}

const DEFAULT_PAGE_SIZE = 20;
const PAGE_SIZE_OPTIONS = [10, 20, 50, 100];

const FILE_TYPE_ICONS = {
  pdf: '📄',
  doc: '📝',
  docx: '📝',
  txt: '📄',
  md: '📝',
  html: '🌐',
  jpg: '🖼️',
  jpeg: '🖼️',
  png: '🖼️',
  gif: '🖼️',
  default: '📎'
};

const DocumentList: React.FC<DocumentListProps> = ({
  knowledgeBaseId,
  onDocumentSelect,
  onDocumentDelete,
  refreshTrigger = 0,
  className = ''
}) => {
  // State management
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);

  // Search and filters
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<DocumentFilters>({
    page: 1,
    limit: DEFAULT_PAGE_SIZE,
    sort_by: 'created_at',
    sort_order: 'desc'
  });
  const [showFilters, setShowFilters] = useState(false);
  const [selectedDocuments, setSelectedDocuments] = useState<Set<string>>(new Set());

  // View settings
  const [viewMode, setViewMode] = useState<ViewMode>({ type: 'list', columns: 1 });

  // Load documents
  const loadDocuments = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const requestFilters = {
        ...filters,
        search: searchQuery || undefined
      };

      const response = await knowledgeApi.getDocuments(knowledgeBaseId, requestFilters);

      console.log('📋 [DocumentList] Documents API response:', {
        hasResponse: !!response,
        documentsCount: response?.documents?.length || 0,
        documentsLength: response?.documents?.length || 0,
        pagination: response?.pagination,
        totalFromPagination: response?.pagination?.total,
        totalSetTo: response?.pagination?.total || 0
      });

      setDocuments(response.documents || []);
      setTotal(response.pagination?.total || 0);

      console.log('📊 [DocumentList] State after setting:', {
        documentsCount: response.documents?.length || 0,
        totalCount: response.pagination?.total || 0
      });

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load documents';
      setError(errorMessage);
      console.error('Failed to load documents:', err);
    } finally {
      setLoading(false);
    }
  }, [knowledgeBaseId, filters, searchQuery]);

  // Refresh documents
  const refreshDocuments = useCallback(() => {
    loadDocuments();
  }, [loadDocuments]);

  // Initial load and refresh trigger
  useEffect(() => {
    loadDocuments();
  }, [loadDocuments, refreshTrigger]);

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      if (filters.page !== 1) {
        setFilters(prev => ({ ...prev, page: 1 }));
      } else {
        loadDocuments();
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [searchQuery, loadDocuments]);

  // Handle filter changes
  const updateFilter = useCallback((key: keyof DocumentFilters, value: any) => {
    setFilters(prev => ({
      ...prev,
      [key]: value,
      page: key === 'page' ? value : 1 // Reset to page 1 when changing filters
    }));
  }, []);

  // Reset filters
  const resetFilters = useCallback(() => {
    setFilters({
      page: 1,
      limit: DEFAULT_PAGE_SIZE,
      sort_by: 'created_at',
      sort_order: 'desc'
    });
    setSearchQuery('');
  }, []);

  // Handle document selection
  const toggleDocumentSelection = useCallback((documentId: string) => {
    setSelectedDocuments(prev => {
      const newSet = new Set(prev);
      if (newSet.has(documentId)) {
        newSet.delete(documentId);
      } else {
        newSet.add(documentId);
      }
      return newSet;
    });
  }, []);

  // Toggle all documents selection
  const toggleAllSelection = useCallback(() => {
    if (selectedDocuments.size === documents.length && documents.length > 0) {
      setSelectedDocuments(new Set());
    } else {
      setSelectedDocuments(new Set(documents.map(doc => doc.id)));
    }
  }, [selectedDocuments, documents]);

  // Delete document
  const deleteDocument = useCallback(async (documentId: string) => {
    try {
      await knowledgeApi.deleteDocument(knowledgeBaseId, documentId);

      // Remove from state
      setDocuments(prev => prev.filter(doc => doc.id !== documentId));
      setTotal(prev => Math.max(0, prev - 1));

      // Remove from selection
      setSelectedDocuments(prev => {
        const newSet = new Set(prev);
        newSet.delete(documentId);
        return newSet;
      });

      if (onDocumentDelete) {
        onDocumentDelete(documentId);
      }

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete document';
      setError(errorMessage);
      console.error('Failed to delete document:', err);
    }
  }, [knowledgeBaseId, onDocumentDelete]);

  // Batch delete
  const deleteSelectedDocuments = useCallback(async () => {
    if (selectedDocuments.size === 0) return;

    const confirmMessage = `确定要删除选中的 ${selectedDocuments.size} 个文档吗？此操作不可撤销。`;
    if (!confirm(confirmMessage)) return;

    try {
      setLoading(true);
      const deletePromises = Array.from(selectedDocuments).map(docId =>
        deleteDocument(docId)
      );

      await Promise.all(deletePromises);
      setSelectedDocuments(new Set());

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete selected documents';
      setError(errorMessage);
      console.error('Failed to delete selected documents:', err);
    } finally {
      setLoading(false);
    }
  }, [selectedDocuments, deleteDocument]);

  // Get file icon
  const getFileIcon = useCallback((filename: string) => {
    const extension = filename.split('.').pop()?.toLowerCase();
    return FILE_TYPE_ICONS[extension as keyof typeof FILE_TYPE_ICONS] || FILE_TYPE_ICONS.default;
  }, []);

  // Get status badge
  const getStatusBadge = useCallback((document: Document) => {
    const uploadStatus = document.upload_status;
    const processingStatus = document.processing_status;

    let status: DocumentStatus;
    let statusText: string;

    if (uploadStatus === 'failed' || processingStatus === 'failed') {
      status = 'failed';
      statusText = '失败';
    } else if (uploadStatus === 'uploading') {
      status = 'uploading';
      statusText = '上传中';
    } else if (processingStatus === 'processing') {
      status = 'processing';
      statusText = '处理中';
    } else if (processingStatus === 'pending') {
      status = 'pending';
      statusText = '等待处理';
    } else {
      status = 'completed';
      statusText = '已完成';
    }

    const IconComponent = getStatusIcon(status);

    return (
      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(status)}`}>
        <span className="mr-1">{IconComponent}</span>
        {statusText}
      </span>
    );
  }, []);

  // Sort options
  const sortOptions = [
    { value: 'filename', label: '文件名' },
    { value: 'created_at', label: '创建时间' },
    { value: 'upload_date', label: '上传时间' },
    { value: 'file_size', label: '文件大小' },
    { value: 'status', label: '状态' }
  ];

  // Status filter options
  const statusOptions = [
    { value: '', label: '全部状态' },
    { value: 'uploading', label: '上传中' },
    { value: 'pending', label: '等待处理' },
    { value: 'processing', label: '处理中' },
    { value: 'completed', label: '已完成' },
    { value: 'failed', label: '失败' }
  ];

  // File type filter options
  const fileTypeOptions = [
    { value: '', label: '全部类型' },
    { value: 'pdf', label: 'PDF' },
    { value: 'doc', label: 'Word文档' },
    { value: 'txt', label: '文本文件' },
    { value: 'jpg', label: '图片' }
  ];

  // Pagination
  const totalPages = Math.ceil(total / filters.limit);
  const paginationStart = (filters.page - 1) * filters.limit + 1;
  const paginationEnd = Math.min(filters.page * filters.limit, total);

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">文档列表</h3>

          <div className="flex items-center space-x-2">
            {/* View mode toggle */}
            <div className="flex items-center bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setViewMode({ type: 'list', columns: 1 })}
                className={`p-1 rounded ${viewMode.type === 'list' ? 'bg-white shadow-sm' : ''}`}
                title="列表视图"
              >
                <List className="w-4 h-4" />
              </button>
              <button
                onClick={() => setViewMode({ type: 'grid', columns: 3 })}
                className={`p-1 rounded ${viewMode.type === 'grid' ? 'bg-white shadow-sm' : ''}`}
                title="网格视图"
              >
                <Grid className="w-4 h-4" />
              </button>
            </div>

            {/* Refresh button */}
            <button
              onClick={refreshDocuments}
              disabled={loading}
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
              title="刷新"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>

            {/* Batch actions */}
            {selectedDocuments.size > 0 && (
              <>
                <button
                  onClick={deleteSelectedDocuments}
                  disabled={loading}
                  className="p-2 text-red-500 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
                  title={`删除选中的 ${selectedDocuments.size} 个文档`}
                >
                  <Trash2 className="w-4 h-4" />
                </button>
                <span className="text-sm text-gray-600">
                  已选择 {selectedDocuments.size} 个
                </span>
              </>
            )}
          </div>
        </div>

        {/* Search and filters */}
        <div className="flex items-center space-x-3">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="搜索文档名称..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Filters toggle */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`p-2 rounded-lg transition-colors ${
              showFilters
                ? 'bg-blue-100 text-blue-600'
                : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
            }`}
          >
            <Filter className="w-4 h-4" />
          </button>
        </div>

        {/* Expanded filters */}
        {showFilters && (
          <div className="mt-4 grid grid-cols-1 md:grid-cols-4 gap-3">
            {/* Status filter */}
            <select
              value={filters.status || ''}
              onChange={(e) => updateFilter('status', e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {statusOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>

            {/* File type filter */}
            <select
              value={filters.file_type || ''}
              onChange={(e) => updateFilter('file_type', e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {fileTypeOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>

            {/* Sort by */}
            <select
              value={filters.sort_by}
              onChange={(e) => updateFilter('sort_by', e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {sortOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>

            {/* Sort order */}
            <select
              value={filters.sort_order}
              onChange={(e) => updateFilter('sort_order', e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="asc">升序</option>
              <option value="desc">降序</option>
            </select>

            {/* Reset button */}
            <button
              onClick={resetFilters}
              className="px-4 py-2 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
            >
              重置筛选
            </button>
          </div>
        )}
      </div>

      {/* Error state */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200">
          <div className="flex items-center">
            <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
            <span className="text-red-700">{error}</span>
          </div>
        </div>
      )}

      {/* Documents content */}
      <div className="p-4">
        {loading && documents.length === 0 ? (
          <div className="flex items-center justify-center py-12">
            <RefreshCw className="w-6 h-6 text-blue-500 animate-spin mr-2" />
            <span className="text-gray-600">加载文档中...</span>
          </div>
        ) : documents.length === 0 ? (
          <div className="text-center py-12">
            <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">暂无文档</h3>
            <p className="text-gray-500">请上传文档到知识库以开始使用</p>
          </div>
        ) : (
          <>
            {/* List view */}
            {viewMode.type === 'list' && (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      <th className="pb-3">
                        <input
                          type="checkbox"
                          checked={selectedDocuments.size === documents.length && documents.length > 0}
                          onChange={toggleAllSelection}
                          className="rounded border-gray-300"
                        />
                      </th>
                      <th className="pb-3">文档名称</th>
                      <th className="pb-3">大小</th>
                      <th className="pb-3">状态</th>
                      <th className="pb-3">上传时间</th>
                      <th className="pb-3">操作</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {documents.map(document => (
                      <tr
                        key={document.id}
                        className={`hover:bg-gray-50 ${
                          selectedDocuments.has(document.id) ? 'bg-blue-50' : ''
                        }`}
                      >
                        <td className="py-3">
                          <input
                            type="checkbox"
                            checked={selectedDocuments.has(document.id)}
                            onChange={() => toggleDocumentSelection(document.id)}
                            className="rounded border-gray-300"
                          />
                        </td>
                        <td className="py-3">
                          <div className="flex items-center">
                            <span className="text-lg mr-2">{getFileIcon(document.filename)}</span>
                            <div>
                              <div className="text-sm font-medium text-gray-900 truncate max-w-xs">
                                {document.original_filename}
                              </div>
                              <div className="text-xs text-gray-500">
                                {document.file_type.toUpperCase()}
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="py-3 text-sm text-gray-600">
                          {formatFileSize(document.file_size)}
                        </td>
                        <td className="py-3">
                          {getStatusBadge(document)}
                        </td>
                        <td className="py-3 text-sm text-gray-600">
                          {new Date(document.created_at).toLocaleDateString('zh-CN')}
                        </td>
                        <td className="py-3">
                          <div className="flex items-center space-x-1">
                            <button
                              onClick={() => onDocumentSelect?.(document)}
                              className="p-1 text-blue-500 hover:text-blue-700 hover:bg-blue-100 rounded transition-colors"
                              title="查看详情"
                            >
                              <Eye className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => deleteDocument(document.id)}
                              className="p-1 text-red-500 hover:text-red-700 hover:bg-red-100 rounded transition-colors"
                              title="删除文档"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Grid view */}
            {viewMode.type === 'grid' && (
              <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-${viewMode.columns} gap-4`}>
                {documents.map(document => (
                  <div
                    key={document.id}
                    className={`border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer ${
                      selectedDocuments.has(document.id) ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
                    }`}
                    onClick={() => toggleDocumentSelection(document.id)}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center">
                        <span className="text-2xl mr-2">{getFileIcon(document.filename)}</span>
                        <div className="flex-1 min-w-0">
                          <h4 className="text-sm font-medium text-gray-900 truncate">
                            {document.original_filename}
                          </h4>
                          <p className="text-xs text-gray-500">
                            {formatFileSize(document.file_size)} • {document.file_type.toUpperCase()}
                          </p>
                        </div>
                      </div>
                      <input
                        type="checkbox"
                        checked={selectedDocuments.has(document.id)}
                        onChange={() => toggleDocumentSelection(document.id)}
                        onClick={(e) => e.stopPropagation()}
                        className="rounded border-gray-300"
                      />
                    </div>

                    <div className="mb-3">
                      {getStatusBadge(document)}
                    </div>

                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <span>{new Date(document.created_at).toLocaleDateString('zh-CN')}</span>
                      <div className="flex items-center space-x-1">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onDocumentSelect?.(document);
                          }}
                          className="p-1 text-blue-500 hover:text-blue-700 hover:bg-blue-100 rounded transition-colors"
                          title="查看详情"
                        >
                          <Eye className="w-3 h-3" />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteDocument(document.id);
                          }}
                          className="p-1 text-red-500 hover:text-red-700 hover:bg-red-100 rounded transition-colors"
                          title="删除文档"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between mt-6 pt-4 border-t border-gray-200">
                <div className="text-sm text-gray-700">
                  显示 {paginationStart} 到 {paginationEnd} 个，共 {total} 个文档
                </div>

                <div className="flex items-center space-x-3">
                  {/* Page size selector */}
                  <select
                    value={filters.limit}
                    onChange={(e) => updateFilter('limit', parseInt(e.target.value))}
                    className="px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {PAGE_SIZE_OPTIONS.map(size => (
                      <option key={size} value={size}>
                        {size} 条/页
                      </option>
                    ))}
                  </select>

                  {/* Pagination controls */}
                  <div className="flex items-center space-x-1">
                    <button
                      onClick={() => updateFilter('page', Math.max(1, filters.page - 1))}
                      disabled={filters.page <= 1}
                      className="p-1 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <ChevronLeft className="w-4 h-4" />
                    </button>

                    <span className="text-sm text-gray-700 px-2">
                      {filters.page} / {totalPages}
                    </span>

                    <button
                      onClick={() => updateFilter('page', Math.min(totalPages, filters.page + 1))}
                      disabled={filters.page >= totalPages}
                      className="p-1 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default DocumentList;