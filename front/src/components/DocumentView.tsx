/**
 * Document View Component
 *
 * A comprehensive document details viewer with chunk display, search functionality,
 * and document information for the Knowledge Base Document Management system.
 *
 * Features:
 * - Document metadata display
 * - Document chunk listing with search
 * - Chunk content preview and full text view
 * - Chunk metadata and statistics
 * - Processing status and logs
 * - Chunk exclusion/inclusion management
 * - Export and download functionality
 *
 * @author Knowledge Base Document Management System
 * @version 1.0.0
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  ArrowLeft,
  FileText,
  Search,
  Eye,
  EyeOff,
  Download,
  Copy,
  Calendar,
  HardDrive,
  Clock,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Filter,
  Settings,
  X,
  FileSearch,
  Hash,
  MessageSquare
} from 'lucide-react';
import { knowledgeApi } from '../api/knowledgeApi';
import {
  Document,
  DocumentChunk,
  ChunkSearchFilters,
  formatFileSize
} from '../types/document';

interface DocumentViewProps {
  knowledgeBaseId: string;
  documentId?: string;
  document?: Document;
  onBack?: () => void;
  className?: string;
}

interface ChunkSearchResult {
  chunks: DocumentChunk[];
  total_count: number;
  query: string;
  search_time: number;
  filters_applied: Record<string, any>;
}

const DocumentView: React.FC<DocumentViewProps> = ({
  knowledgeBaseId,
  documentId,
  document: initialDocument,
  onBack,
  className = ''
}) => {
  // Component initialization logging
  console.log('🎯 [DocumentView] Component initialized with props:', {
    knowledgeBaseId,
    documentId,
    hasInitialDocument: !!initialDocument,
    initialDocumentId: initialDocument?.id,
    initialRagflowId: initialDocument?.ragflow_document_id,
    initialFilename: initialDocument?.filename
  });

  // State management
  const [document, setDocument] = useState<Document | null>(initialDocument || null);
  const [chunks, setChunks] = useState<DocumentChunk[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedChunks, setExpandedChunks] = useState<Set<string>>(new Set());
  const [showSearchResults, setShowSearchResults] = useState(false);
  const [searchResults, setSearchResults] = useState<ChunkSearchResult | null>(null);

  // UI state
  const [viewMode, setViewMode] = useState<'metadata' | 'chunks'>('chunks');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [sortBy, setSortBy] = useState<'chunk_index' | 'word_count' | 'created_at'>('chunk_index');

  // Load document details if not provided
  const loadDocument = useCallback(async () => {
    console.log('📥 [DocumentView] loadDocument called:', {
      hasDocumentId: !!documentId,
      documentId,
      hasDocument: !!document,
      knowledgeBaseId
    });

    if (!documentId || document) {
      console.log('⏭️ [DocumentView] Skipping loadDocument - conditions not met');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      console.log('🌐 [DocumentView] Calling knowledgeApi.getDocument with:', {
        knowledgeBaseId,
        documentId
      });

      const doc = await knowledgeApi.getDocument(knowledgeBaseId, documentId);
      console.log('✅ [DocumentView] Document loaded successfully:', {
        id: doc.id,
        ragflow_document_id: doc.ragflow_document_id,
        filename: doc.filename,
        processing_status: doc.processing_status
      });

      setDocument(doc);

    } catch (err) {
      console.error('💥 [DocumentView] Error loading document:', {
        error: err,
        errorMessage: err instanceof Error ? err.message : 'Unknown error',
        errorStack: err instanceof Error ? err.stack : undefined,
        params: {
          knowledgeBaseId,
          documentId
        }
      });

      const errorMessage = err instanceof Error ? err.message : 'Failed to load document';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [knowledgeBaseId, documentId, document]);

  // Load document chunks
  const loadChunks = useCallback(async () => {
    if (!document?.id) {
      console.error('🚫 [DocumentView] No document available');
      return;
    }

    console.log('🔍 [DocumentView] Loading chunks for document:', {
      documentId: document.id,
      ragflowDocumentId: document.ragflow_document_id,
      knowledgeBaseId,
      documentName: document.filename
    });

    try {
      setLoading(true);
      setError(null);

      const documentIdToUse = document.ragflow_document_id || document.id;
      console.log('📋 [DocumentView] Using document ID for API call:', documentIdToUse);

      const response = await knowledgeApi.getDocumentChunks(knowledgeBaseId, documentIdToUse, {
        sort_by: sortBy,
        sort_order: sortOrder
      });

      console.log('📦 [DocumentView] API response received:', {
        success: true,
        documentId: response.document_id,
        documentName: response.document_name,
        totalChunks: response.total_chunks,
        actualChunksLength: response.chunks?.length || 0,
        chunksSample: response.chunks?.slice(0, 2).map(chunk => ({
          id: chunk.id,
          contentLength: chunk.content?.length || 0,
          hasContent: !!chunk.content,
          wordCount: chunk.word_count
        }))
      });

      setChunks(response.chunks || []);
      console.log('✅ [DocumentView] Successfully loaded chunks:', response.chunks?.length || 0);

    } catch (err) {
      console.error('💥 [DocumentView] Error loading chunks:', {
        error: err,
        errorMessage: err instanceof Error ? err.message : 'Unknown error',
        errorStack: err instanceof Error ? err.stack : undefined,
        documentInfo: {
          id: document?.id,
          ragflow_document_id: document?.ragflow_document_id,
          filename: document?.filename
        },
        knowledgeBaseId
      });

      const errorMessage = err instanceof Error ? err.message : 'Failed to load document chunks';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [knowledgeBaseId, document, sortBy, sortOrder]);

  // Search chunks
  const searchChunks = useCallback(async (query: string) => {
    if (!query.trim() || !document?.id) {
      setShowSearchResults(false);
      setSearchResults(null);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const filters: ChunkSearchFilters = {
        query: query.trim(),
        max_results: 20
      };

      const results = await knowledgeApi.searchChunks(knowledgeBaseId, query.trim(), filters);
      setSearchResults(results);
      setShowSearchResults(true);

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to search chunks';
      setError(errorMessage);
      console.error('Failed to search chunks:', err);
    } finally {
      setLoading(false);
    }
  }, [knowledgeBaseId, document]);

  // Toggle chunk expansion
  const toggleChunkExpansion = useCallback((chunkId: string) => {
    setExpandedChunks(prev => {
      const newSet = new Set(prev);
      if (newSet.has(chunkId)) {
        newSet.delete(chunkId);
      } else {
        newSet.add(chunkId);
      }
      return newSet;
    });
  }, []);

  // Copy content to clipboard
  const copyToClipboard = useCallback(async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      // Show success message (could use a toast library)
      alert('内容已复制到剪贴板');
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
      alert('复制失败，请手动复制');
    }
  }, []);

  // Format date for display
  const formatDate = useCallback((dateString: string) => {
    return new Date(dateString).toLocaleString('zh-CN');
  }, []);

  // Get processing status info
  const getProcessingStatus = useCallback((doc: Document) => {
    const { upload_status, processing_status, error_message } = doc;

    if (upload_status === 'failed' || processing_status === 'failed') {
      return {
        status: 'failed',
        text: '处理失败',
        color: 'text-red-600',
        icon: AlertCircle,
        message: error_message
      };
    }

    if (upload_status === 'uploading') {
      return {
        status: 'uploading',
        text: '上传中',
        color: 'text-yellow-600',
        icon: Clock,
        message: '文档正在上传到服务器'
      };
    }

    if (processing_status === 'pending') {
      return {
        status: 'pending',
        text: '等待处理',
        color: 'text-yellow-600',
        icon: Clock,
        message: '文档等待RAGFlow处理'
      };
    }

    if (processing_status === 'processing') {
      return {
        status: 'processing',
        text: '处理中',
        color: 'text-blue-600',
        icon: RefreshCw,
        message: '文档正在RAGFlow中处理'
      };
    }

    return {
      status: 'completed',
      text: '已完成',
      color: 'text-green-600',
      icon: CheckCircle,
      message: '文档处理完成'
    };
  }, []);

  // Display chunks based on search results or all chunks
  const displayChunks = useMemo(() => {
    if (showSearchResults && searchResults) {
      return searchResults.chunks;
    }
    return chunks;
  }, [chunks, showSearchResults, searchResults]);

  // Initial load
  useEffect(() => {
    console.log('🔄 [DocumentView] Initial useEffect triggered, calling loadDocument');
    loadDocument();
  }, [loadDocument]);

  useEffect(() => {
    console.log('📋 [DocumentView] Document changed useEffect triggered:', {
      hasDocument: !!document,
      documentId: document?.id,
      ragflowDocumentId: document?.ragflow_document_id,
      filename: document?.filename,
      willCallLoadChunks: !!document
    });

    if (document) {
      loadChunks();
    }
  }, [document, loadChunks]);

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      searchChunks(searchQuery);
    }, 300);

    return () => clearTimeout(timer);
  }, [searchQuery, searchChunks]);

  if (error) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
        <div className="p-6 text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">加载失败</h3>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            重试
          </button>
        </div>
      </div>
    );
  }

  if (loading && !document) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
        <div className="p-6 flex items-center justify-center">
          <RefreshCw className="w-6 h-6 text-blue-500 animate-spin mr-2" />
          <span className="text-gray-600">加载文档详情中...</span>
        </div>
      </div>
    );
  }

  if (!document) {
    return null;
  }

  const statusInfo = getProcessingStatus(document);
  const StatusIcon = statusInfo.icon;

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            {onBack && (
              <button
                onClick={onBack}
                className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors mr-2"
              >
                <ArrowLeft className="w-4 h-4" />
              </button>
            )}
            <div>
              <h3 className="text-lg font-medium text-gray-900">{document.original_filename}</h3>
              <div className="flex items-center mt-1">
                <StatusIcon className={`w-4 h-4 ${statusInfo.color} mr-1`} />
                <span className={`text-sm ${statusInfo.color}`}>{statusInfo.text}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {/* View mode toggle */}
            <div className="flex items-center bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setViewMode('metadata')}
                className={`px-3 py-1 rounded text-sm ${
                  viewMode === 'metadata' ? 'bg-white shadow-sm' : ''
                }`}
              >
                基本信息
              </button>
              <button
                onClick={() => setViewMode('chunks')}
                className={`px-3 py-1 rounded text-sm ${
                  viewMode === 'chunks' ? 'bg-white shadow-sm' : ''
                }`}
              >
                文档块 ({document.chunk_count})
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Status message */}
      {statusInfo.message && (
        <div className={`p-4 border-b ${statusInfo.status === 'failed' ? 'bg-red-50 border-red-200' : 'bg-blue-50 border-blue-200'}`}>
          <div className="flex items-center">
            <StatusIcon className={`w-5 h-5 ${statusInfo.color} mr-2`} />
            <span className={`text-sm ${statusInfo.color}`}>{statusInfo.message}</span>
          </div>
        </div>
      )}

      {/* Content */}
      <div className="p-4">
        {viewMode === 'metadata' ? (
          // Metadata view
          <div className="space-y-6">
            {/* Basic information */}
            <div>
              <h4 className="text-sm font-medium text-gray-900 mb-3">基本信息</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex items-center text-sm">
                  <FileText className="w-4 h-4 text-gray-400 mr-2" />
                  <span className="text-gray-600">文件名:</span>
                  <span className="ml-2 text-gray-900">{document.original_filename}</span>
                </div>
                <div className="flex items-center text-sm">
                  <HardDrive className="w-4 h-4 text-gray-400 mr-2" />
                  <span className="text-gray-600">文件大小:</span>
                  <span className="ml-2 text-gray-900">{formatFileSize(document.file_size)}</span>
                </div>
                <div className="flex items-center text-sm">
                  <Hash className="w-4 h-4 text-gray-400 mr-2" />
                  <span className="text-gray-600">文件类型:</span>
                  <span className="ml-2 text-gray-900">{document.file_type.toUpperCase()}</span>
                </div>
                <div className="flex items-center text-sm">
                  <MessageSquare className="w-4 h-4 text-gray-400 mr-2" />
                  <span className="text-gray-600">文档块数:</span>
                  <span className="ml-2 text-gray-900">{document.chunk_count}</span>
                </div>
              </div>
            </div>

            {/* Processing information */}
            <div>
              <h4 className="text-sm font-medium text-gray-900 mb-3">处理信息</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex items-center text-sm">
                  <Clock className="w-4 h-4 text-gray-400 mr-2" />
                  <span className="text-gray-600">创建时间:</span>
                  <span className="ml-2 text-gray-900">{formatDate(document.created_at)}</span>
                </div>
                <div className="flex items-center text-sm">
                  <Calendar className="w-4 h-4 text-gray-400 mr-2" />
                  <span className="text-gray-600">上传时间:</span>
                  <span className="ml-2 text-gray-900">
                    {document.uploaded_at ? formatDate(document.uploaded_at) : '-'}
                  </span>
                </div>
                <div className="flex items-center text-sm">
                  <CheckCircle className="w-4 h-4 text-gray-400 mr-2" />
                  <span className="text-gray-600">处理完成:</span>
                  <span className="ml-2 text-gray-900">
                    {document.processed_at ? formatDate(document.processed_at) : '-'}
                  </span>
                </div>
                <div className="flex items-center text-sm">
                  <RefreshCw className="w-4 h-4 text-gray-400 mr-2" />
                  <span className="text-gray-600">最后更新:</span>
                  <span className="ml-2 text-gray-900">{formatDate(document.updated_at)}</span>
                </div>
              </div>
            </div>

            {/* Status details */}
            <div>
              <h4 className="text-sm font-medium text-gray-900 mb-3">状态详情</h4>
              <div className="space-y-2">
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm text-gray-600">上传状态</span>
                  <span className={`text-sm font-medium ${statusInfo.color}`}>
                    {document.upload_status}
                  </span>
                </div>
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm text-gray-600">处理状态</span>
                  <span className={`text-sm font-medium ${statusInfo.color}`}>
                    {document.processing_status}
                  </span>
                </div>
                {document.error_message && (
                  <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                    <span className="text-sm font-medium text-red-900">错误信息</span>
                    <p className="text-sm text-red-700 mt-1">{document.error_message}</p>
                  </div>
                )}
              </div>
            </div>

            {/* RAGFlow metadata */}
            {document.ragflow_metadata && Object.keys(document.ragflow_metadata).length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-3">RAGFlow 元数据</h4>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <pre className="text-xs text-gray-600 overflow-x-auto">
                    {JSON.stringify(document.ragflow_metadata, null, 2)}
                  </pre>
                </div>
              </div>
            )}
          </div>
        ) : (
          // Chunks view
          <div className="space-y-4">
            {/* Search bar */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="搜索文档块内容..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>

            {/* Sort controls */}
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-600">排序:</span>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as any)}
                  className="px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="chunk_index">块索引</option>
                  <option value="word_count">词数</option>
                  <option value="created_at">创建时间</option>
                </select>
                <button
                  onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                  className="p-1 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded"
                >
                  {sortOrder === 'asc' ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                </button>
              </div>

              {showSearchResults && searchResults && (
                <div className="text-sm text-gray-600">
                  找到 {searchResults.total_count} 个匹配项
                </div>
              )}
            </div>

            {/* Chunks list */}
            {loading && displayChunks.length === 0 ? (
              <div className="flex items-center justify-center py-12">
                <RefreshCw className="w-6 h-6 text-blue-500 animate-spin mr-2" />
                <span className="text-gray-600">加载文档块中...</span>
              </div>
            ) : displayChunks.length === 0 ? (
              <div className="text-center py-12">
                <FileSearch className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  {searchQuery ? '未找到匹配的文档块' : '暂无文档块'}
                </h3>
                <p className="text-gray-500">
                  {searchQuery ? '尝试使用其他关键词搜索' : '文档可能还在处理中'}
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {displayChunks.map((chunk) => (
                  <div key={chunk.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center">
                        <span className="text-sm font-medium text-gray-900">块 #{chunk.chunk_index}</span>
                        <span className="ml-2 text-sm text-gray-500">
                          {chunk.word_count} 词 • {chunk.character_count} 字符
                        </span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => copyToClipboard(chunk.content)}
                          className="p-1 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded transition-colors"
                          title="复制内容"
                        >
                          <Copy className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => toggleChunkExpansion(chunk.id)}
                          className="p-1 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded transition-colors"
                          title={expandedChunks.has(chunk.id) ? '收起' : '展开'}
                        >
                          {expandedChunks.has(chunk.id) ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                        </button>
                      </div>
                    </div>

                    {/* Content preview */}
                    <div className={`text-sm text-gray-600 ${
                      expandedChunks.has(chunk.id) ? '' : 'line-clamp-3'
                    }`}>
                      {chunk.content_preview || chunk.content}
                    </div>

                    {/* Metadata */}
                    <div className="mt-3 flex items-center justify-between text-xs text-gray-500">
                      <span>创建于 {formatDate(chunk.created_at)}</span>
                      {chunk.ragflow_metadata && (
                        <span>RAGFlow 元数据</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default DocumentView;