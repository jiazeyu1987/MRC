/**
 * 文档相关类型定义
 */

import { BaseEntity, PaginationInfo, ListResponse, BulkOperationResult, UploadResponse } from './common';

/**
 * 文档基础类型
 */
export interface Document extends BaseEntity {
  id: number;
  knowledgeBaseId: number;
  title: string;
  description?: string;
  fileName: string;
  fileType: string;
  fileSize: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  processingProgress?: number;
  chunkCount?: number;
  metadata?: Record<string, any>;
  tags?: string[];
  createdAt: string;
  updatedAt: string;
}

/**
 * 文档块类型
 */
export interface DocumentChunk {
  id: string;
  documentId: number;
  content: string;
  chunkIndex: number;
  startPosition?: number;
  endPosition?: number;
  metadata?: Record<string, any>;
  embedding?: number[];
  createdAt: string;
}

/**
 * 文档过滤器
 */
export interface DocumentFilters {
  search?: string;
  status?: string;
  fileType?: string;
  tags?: string[];
  sizeFrom?: number;
  sizeTo?: number;
  dateFrom?: string;
  dateTo?: string;
}

/**
 * 文档块搜索过滤器
 */
export interface ChunkSearchFilters {
  query?: string;
  topK?: number;
  similarityThreshold?: number;
  includeMetadata?: boolean;
}

/**
 * 文档块搜索结果
 */
export interface ChunkSearchResult {
  chunks: DocumentChunk[];
  total: number;
  query: string;
  searchTime: number;
}

/**
 * 文档统计信息
 */
export interface DocumentStatistics {
  id: number;
  title: string;
  fileName: string;
  fileSize: number;
  chunkCount: number;
  processingStatus: string;
  createdAt: string;
  updatedAt: string;
  lastAccessed?: string;
  accessCount: number;
  metadata?: Record<string, any>;
}