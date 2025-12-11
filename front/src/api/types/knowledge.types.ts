/**
 * 知识库相关类型定义
 */

import { BaseEntity, PaginationInfo, ListResponse, BulkOperationResult, ExportOptions } from './common';

/**
 * 知识库基础类型
 */
export interface KnowledgeBase extends BaseEntity {
  id: number;
  name: string;
  description: string;
  ragflowDatasetId?: string;
  connectionStatus: 'connected' | 'disconnected' | 'error';
  isActive: boolean;
  documentCount: number;
  totalSize: number;
  lastSyncAt?: string;
  settings?: KnowledgeBaseSettings;
  metadata?: Record<string, any>;
}

export interface KnowledgeBaseSettings {
  syncInterval?: number;
  autoSync?: boolean;
  retryCount?: number;
  timeout?: number;
  retrievalSettings?: RetrievalSettings;
}

export interface RetrievalSettings {
  topK?: number;
  similarityThreshold?: number;
  includeMetadata?: boolean;
  enableReranking?: boolean;
}

/**
 * 知识库查询参数
 */
export interface KnowledgeBaseListParams {
  page?: number;
  pageSize?: number;
  search?: string;
  status?: string;
  sortBy?: 'name' | 'createdAt' | 'updatedAt' | 'documentCount';
  sortOrder?: 'asc' | 'desc';
  isActive?: boolean;
}

/**
 * 知识库列表响应
 */
export interface KnowledgeBaseListResponse extends ListResponse<KnowledgeBase> {
  statistics: {
    total: number;
    active: number;
    inactive: number;
    totalDocuments: number;
    totalSize: number;
  };
}

/**
 * 知识库统计信息
 */
export interface KnowledgeBaseStatistics {
  id: number;
  documentCount: number;
  totalChunks: number;
  totalSize: number;
  conversationCount: number;
  totalSearches: number;
  lastActivityAt?: string;
  documentTypes: Record<string, number>;
  storageUsage: {
    used: number;
    total: number;
    percentage: number;
  };
  performanceMetrics: {
    averageResponseTime: number;
    successRate: number;
    errorRate: number;
  };
}

/**
 * 知识库操作请求
 */
export interface KnowledgeBaseCreateRequest {
  name: string;
  description: string;
  ragflowDatasetId?: string;
  settings?: KnowledgeBaseSettings;
  isActive?: boolean;
}

export interface KnowledgeBaseUpdateRequest {
  name?: string;
  description?: string;
  ragflowDatasetId?: string;
  settings?: KnowledgeBaseSettings;
  isActive?: boolean;
}

export interface KnowledgeBaseActionRequest {
  action: 'refresh_all' | 'refresh_single';
  knowledgeBaseId?: number;
}

export interface TestConversationRequest {
  question: string;
  contextStrategy?: 'none' | 'last_message' | 'last_round' | 'all';
  maxContextLength?: number;
  conversationId?: number;
}

/**
 * 测试对话响应
 */
export interface TestConversationResponse {
  conversationId: number;
  messageId: number;
  question: string;
  answer: string;
  contextUsed: {
    documents: Array<{
      id: number;
      title: string;
      relevanceScore: number;
    }>;
    fallbackUsed: boolean;
  };
  metadata: {
    responseTime: number;
    tokenUsage: {
      prompt: number;
      completion: number;
      total: number;
    };
  };
}

/**
 * 同步结果
 */
export interface SyncResult {
  created: number;
  updated: number;
  failed: number;
  total: number;
  duration: number;
  errors: Array<{
    id: number;
    name: string;
    error: string;
  }>;
}

export interface RefreshResult {
  success: boolean;
  knowledgeBase: {
    id: number;
    name: string;
    ragflowDatasetId: string;
    documentCount: number;
    status: string;
  };
  duration: number;
  error?: string;
}

/**
 * 对话相关类型
 */
export interface KnowledgeBaseConversation extends BaseEntity {
  id: number;
  knowledgeBaseId: number;
  title: string;
  status: 'active' | 'completed' | 'archived';
  messages: ConversationMessage[];
  tags: string[];
  metadata?: Record<string, any>;
}

export interface ConversationMessage {
  id: number;
  conversationId: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  tokenCount?: number;
  metadata?: Record<string, any>;
}

export interface ConversationListParams {
  page?: number;
  pageSize?: number;
  search?: string;
  status?: string;
  tags?: string[];
  dateFrom?: string;
  dateTo?: string;
  sortBy?: 'createdAt' | 'updatedAt' | 'title';
  sortOrder?: 'asc' | 'desc';
}

export interface ConversationListResponse extends ListResponse<KnowledgeBaseConversation> {
  statistics: {
    total: number;
    active: number;
    completed: number;
    archived: number;
    totalMessages: number;
  };
}

/**
 * 对话导出
 */
export interface ConversationExportOptions extends ExportOptions {
  includeMetadata?: boolean;
  includeTimestamps?: boolean;
  messageFormat?: 'detailed' | 'simple' | 'compact';
  includeSystemMessages?: boolean;
}

export interface ConversationExportResult {
  downloadUrl: string;
  filename: string;
  format: string;
  size: number;
  expiresAt: string;
}

/**
 * RAGFlow集成类型
 */
export interface ChatAssistant {
  id: string;
  name: string;
  description: string;
  avatar?: string;
  status: 'active' | 'inactive';
  createdAt: string;
  updatedAt: string;
}

export interface Agent {
  id: string;
  name: string;
  description: string;
  prompt: string;
  datasetIds: string[];
  status: 'active' | 'inactive';
  createdAt: string;
  updatedAt: string;
}

export interface ChatInteractionRequest {
  message: string;
  conversationId?: string;
  sessionId?: string;
  metadata?: Record<string, any>;
}

export interface ChatInteractionResponse {
  response: string;
  messageId: string;
  conversationId: string;
  sessionId?: string;
  timestamp: string;
  metadata: Record<string, any>;
}

export interface RetrievalRequest {
  datasetId: string;
  query: string;
  topK?: number;
  similarityThreshold?: number;
  includeMetadata?: boolean;
  filters?: Record<string, any>;
}

export interface RetrievalResult {
  results: Array<{
    id: string;
    content: string;
    metadata: Record<string, any>;
    score: number;
  }>;
  total: number;
  query: string;
  datasetId: string;
  retrievalTime: number;
}

/**
 * 搜索分析类型
 */
export interface SearchAnalytics {
  knowledgeBaseId: number;
  dateRange: {
    from: string;
    to: string;
  };
  totalQueries: number;
  uniqueQueries: number;
  averageResponseTime: number;
  popularQueries: Array<{
    query: string;
    count: number;
    averageResponseTime: number;
  }>;
  queryTrends: Array<{
    date: string;
    count: number;
  }>;
  performanceMetrics: {
    averageResponseTime: number;
    successRate: number;
    errorRate: number;
  };
}

export interface SearchInsights {
  knowledgeBaseId: number;
  recommendations: string[];
  issues: Array<{
    type: 'performance' | 'content' | 'usage';
    description: string;
    severity: 'low' | 'medium' | 'high';
    suggestion: string;
  }>;
  optimization: {
    potentialImprovements: string[];
    estimatedImpact: string;
  };
}

/**
 * 批量操作
 */
export interface KnowledgeBaseBulkOperation extends BulkOperation<number> {
  knowledgeBaseIds: number[];
}

/**
 * 知识库验证类型
 */
export interface KnowledgeBaseValidation {
  id: number;
  name: string;
  isValid: boolean;
  errors: Array<{
    field: string;
    message: string;
    code: string;
  }>;
  warnings: Array<{
    field: string;
    message: string;
    code: string;
  }>;
}

export interface KnowledgeBaseValidationResult {
  isValid: boolean;
  totalErrors: number;
  totalWarnings: number;
  validations: KnowledgeBaseValidation[];
}

/**
 * 事件类型
 */
export interface KnowledgeBaseEvent {
  type: 'created' | 'updated' | 'deleted' | 'synced' | 'connected' | 'disconnected';
  knowledgeBaseId: number;
  timestamp: string;
  data?: any;
  userId?: number;
}