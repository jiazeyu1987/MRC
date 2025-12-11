/**
 * 文档API客户端
 *
 * 提供文档相关的API操作
 */

import { httpClient, ApiErrorHandler } from '../shared/http-client';
import type {
  Document,
  DocumentChunk,
  DocumentFilters,
  ChunkSearchFilters,
  UploadResponse,
  ChunkSearchResult,
  DocumentStatistics,
  UploadProgress,
} from '../types/document.types';
import type { ListResponse, BulkOperationResult } from '../types/common';

/**
 * 文档API类
 */
export class DocumentApi {
  private readonly basePath = '/api/documents';

  /**
   * 获取文档列表
   */
  async listDocuments(
    knowledgeBaseId: number,
    params?: DocumentFilters & PaginationParams & FilterParams
  ): Promise<ListResponse<Document>> {
    try {
      const queryParams = this.buildQueryParams(params);
      return await httpClient.get<ListResponse<Document>>(
        `${this.basePath}/knowledge-base/${knowledgeBaseId}${queryParams}`
      );
    } catch (error) {
      console.error(`Failed to fetch documents for knowledge base ${knowledgeBaseId}:`, error);
      throw new Error(ApiErrorHandler.handleError(error, '获取文档列表失败'));
    }
  }

  /**
   * 获取文档详情
   */
  async getDocument(
    knowledgeBaseId: number,
    documentId: number
  ): Promise<Document> {
    try {
      return await httpClient.get<Document>(
        `${this.basePath}/knowledge-base/${knowledgeBaseId}/${documentId}`
      );
    } catch (error) {
      console.error(
        `Failed to fetch document ${documentId} for knowledge base ${knowledgeBaseId}:`,
        error
      );
      throw new Error(ApiErrorHandler.handleError(error, '获取文档详情失败'));
    }
  }

  /**
   * 上传文档
   */
  async uploadDocument(
    knowledgeBaseId: number,
    file: File,
    options?: {
      chunkSize?: number;
      chunkOverlap?: number;
      autoProcess?: boolean;
      extractMetadata?: boolean;
      generateSummary?: boolean;
      tags?: string[];
    }
  ): Promise<UploadResponse> {
    try {
      const formData = new FormData();
      formData.append('file', file);

      // 添加选项参数
      if (options) {
        Object.entries(options).forEach(([key, value]) => {
          if (value !== undefined) {
            formData.append(key, String(value));
          }
        });
      }

      return await httpClient.post<UploadResponse>(
        `${this.basePath}/knowledge-base/${knowledgeBaseId}/upload`,
        formData
      );
    } catch (error) {
      console.error(
        `Failed to upload document to knowledge base ${knowledgeBaseId}:`,
        error
      );
      throw new Error(ApiErrorHandler.handleError(error, '文档上传失败'));
    }
  }

  /**
   * 批量上传文档
   */
  async uploadDocuments(
    knowledgeBaseId: number,
    files: File[],
    options?: {
      chunkSize?: number;
      chunkOverlap?: number;
      autoProcess?: boolean;
      maxFiles?: number;
    }
  ): Promise<{
    results: Array<UploadResponse>;
    totalFiles: number;
    successfulUploads: number;
    failedUploads: number;
  }> {
    try {
      const formData = new FormData();

      // 添加文件
      files.forEach((file, index) => {
        formData.append(`files`, file);
      });

      // 添加选项参数
      if (options) {
        Object.entries(options).forEach(([key, value]) => {
          if (value !== undefined) {
            formData.append(key, String(value));
          }
        });
      }

      const response = await httpClient.post<any>(
        `${this.basePath}/knowledge-base/${knowledgeBaseId}/upload-batch`,
        formData
      );

      return {
        results: response.results,
        totalFiles: response.total_files,
        successfulUploads: response.successful_uploads,
        failedUploads: response.failed_uploads,
      };
    } catch (error) {
      console.error(
        `Failed to upload documents to knowledge base ${knowledgeBaseId}:`,
        error
      );
      throw new Error(ApiErrorHandler.handleError(error, '批量文档上传失败'));
    }
  }

  /**
   * 更新文档
   */
  async updateDocument(
    knowledgeBaseId: number,
    documentId: number,
    data: {
      title?: string;
      description?: string;
      tags?: string[];
      metadata?: Record<string, any>;
    }
  ): Promise<Document> {
    try {
      return await httpClient.put<Document>(
        `${this.basePath}/knowledge-base/${knowledgeBaseId}/${documentId}`,
        data
      );
    } catch (error) {
      console.error(
        `Failed to update document ${documentId} for knowledge base ${knowledgeBaseId}:`,
        error
      );
      throw new Error(ApiErrorHandler.handleError(error, '更新文档失败'));
    }
  }

  /**
   * 删除文档
   */
  async deleteDocument(
    knowledgeBaseId: number,
    documentId: number
  ): Promise<void> {
    try {
      await httpClient.delete(
        `${this.basePath}/knowledge-base/${knowledgeBaseId}/${documentId}`
      );
    } catch (error) {
      console.error(
        `Failed to delete document ${documentId} for knowledge base ${knowledgeBaseId}:`,
        error
      );
      throw new Error(ApiErrorHandler.handleError(error, '删除文档失败'));
    }
  }

  /**
   * 获取文档块列表
   */
  async getDocumentChunks(
    knowledgeBaseId: number,
    documentId: number
  ): Promise<DocumentChunk[]> {
    try {
      const response = await httpClient.get<ListResponse<DocumentChunk>>(
        `${this.basePath}/knowledge-base/${knowledgeBaseId}/${documentId}/chunks`
      );
      return response.items;
    } catch (error) {
      console.error(
        `Failed to fetch chunks for document ${documentId} in knowledge base ${knowledgeBaseId}:`,
        error
      );
      throw new Error(ApiErrorHandler.handleError(error, '获取文档块失败'));
    }
  }

  /**
   * 搜索文档块
   */
  async searchChunks(
    knowledgeBaseId: number,
    documentId: number,
    filters: ChunkSearchFilters
  ): Promise<ChunkSearchResult> {
    try {
      const queryParams = new URLSearchParams();

      if (filters.query) {
        queryParams.append('query', filters.query);
      }
      if (filters.topK) {
        queryParams.append('top_k', String(filters.topK));
      }
      if (filters.similarityThreshold) {
        queryParams.append('similarity_threshold', String(filters.similarityThreshold));
      }
      if (filters.includeMetadata !== undefined) {
        queryParams.append('include_metadata', String(filters.includeMetadata));
      }

      const queryString = queryParams.toString();
      const url = `${this.basePath}/knowledge-base/${knowledgeBaseId}/${documentId}/chunks/search${queryString ? `?${queryString}` : ''}`;

      return await httpClient.get<ChunkSearchResult>(url);
    } catch (error) {
      console.error(
        `Failed to search chunks in document ${documentId} for knowledge base ${knowledgeBaseId}:`,
        error
      );
      throw new Error(ApiErrorHandler.handleError(error, '搜索文档块失败'));
    }
  }

  /**
   * 重新处理文档块
   */
  async reprocessChunks(
    knowledgeBaseId: number,
    documentId: number,
    options: {
      chunkSize?: number;
      chunkOverlap?: number;
      forceReprocess?: boolean;
    }
  ): Promise<{
    documentId: number;
    chunkCount: number;
    status: string;
    processingTime: number;
  }> {
    try {
      const response = await httpClient.post<any>(
        `${this.basePath}/knowledge-base/${knowledgeBaseId}/${documentId}/chunks/reprocess`,
        options
      );

      return {
        documentId: response.document_id,
        chunkCount: response.chunk_count,
        status: response.status,
        processingTime: response.processing_time,
      };
    } catch (error) {
      console.error(
        `Failed to reprocess chunks for document ${documentId} in knowledge base ${knowledgeBaseId}:`,
        error
      );
      throw new Error(ApiErrorHandler.handleError(error, '重新处理文档块失败'));
    }
  }

  /**
   * 获取文档统计信息
   */
  async getDocumentStatistics(
    knowledgeBaseId: number,
    documentId: number
  ): Promise<DocumentStatistics> {
    try {
      return await httpClient.get<DocumentStatistics>(
        `${this.basePath}/knowledge-base/${knowledgeBaseId}/${documentId}/statistics`
      );
    } catch (error) {
      console.error(
        `Failed to fetch statistics for document ${documentId} in knowledge base ${knowledgeBaseId}:`,
        error
      );
      throw new Error(ApiErrorHandler.handleError(error, '获取文档统计失败'));
    }
  }

  /**
   * 获取文档上传进度
   */
  async getUploadProgress(
    uploadId: string
  ): Promise<UploadProgress> {
    try {
      return await httpClient.get<UploadProgress>(
        `${this.basePath}/upload/${uploadId}/progress`
      );
    } catch (error) {
      console.error(`Failed to get upload progress for ${uploadId}:`, error);
      throw new Error(ApiErrorHandler.handleError(error, '获取上传进度失败'));
    }
  }

  /**
   * 取消文档上传
   */
  async cancelUpload(uploadId: string): Promise<void> {
    try {
      await httpClient.post(`${this.basePath}/upload/${uploadId}/cancel`);
    } catch (error) {
      console.error(`Failed to cancel upload ${uploadId}:`, error);
      throw new Error(ApiErrorHandler.handleError(error, '取消上传失败'));
    }
  }

  /**
   * 批量操作文档
   */
  async bulkOperation(
    knowledgeBaseId: number,
    data: {
      action: 'delete' | 'process' | 'reprocess';
      documentIds: number[];
      options?: Record<string, any>;
    }
  ): Promise<BulkOperationResult> {
    try {
      return await httpClient.post<BulkOperationResult>(
        `${this.basePath}/knowledge-base/${knowledgeBaseId}/bulk-operation`,
        data
      );
    } catch (error) {
      console.error(
        `Failed to perform bulk operation on documents in knowledge base ${knowledgeBaseId}:`,
        error
      );
      throw new Error(ApiErrorHandler.handleError(error, '批量操作文档失败'));
    }
  }

  /**
   * 获取文档处理状态
   */
  async getProcessingStatus(
    knowledgeBaseId: number,
    documentId: number
  ): Promise<{
    status: 'pending' | 'processing' | 'completed' | 'failed';
    progress: number;
    stage?: string;
    message?: string;
    error?: string;
  }> {
    try {
      return await httpClient.get<any>(
        `${this.basePath}/knowledge-base/${knowledgeBaseId}/${documentId}/status`
      );
    } catch (error) {
      console.error(
        `Failed to get processing status for document ${documentId} in knowledge base ${knowledgeBaseId}:`,
        error
      );
      throw new Error(ApiErrorHandler.handleError(error, '获取处理状态失败'));
    }
  }

  /**
   * 搜索文档
   */
  async searchDocuments(
    knowledgeBaseId: number,
    params: {
      query?: string;
      filters?: DocumentFilters;
      pagination?: PaginationParams;
    }
  ): Promise<{
    documents: Document[];
    total: number;
    facets?: Record<string, Array<{ value: string; count: number }>>;
    suggestions?: string[];
  }> {
    try {
      const queryParams = new URLSearchParams();

      if (params.query) queryParams.append('query', params.query);

      // 添加分页参数
      if (params.pagination) {
        if (params.pagination.page) {
          queryParams.append('page', String(params.pagination.page));
        }
        if (params.pagination.pageSize) {
          queryParams.append('page_size', String(params.pagination.pageSize));
        }
      }

      // 添加过滤参数
      if (params.filters) {
        Object.entries(params.filters).forEach(([key, value]) => {
          if (value !== undefined && value !== null) {
            if (Array.isArray(value)) {
              value.forEach((v) => queryParams.append(key, String(v)));
            } else {
              queryParams.append(key, String(value));
            }
          }
        });
      }

      const queryString = queryParams.toString();
      const url = `${this.basePath}/knowledge-base/${knowledgeBaseId}/search${queryString ? `?${queryString}` : ''}`;

      return await httpClient.get<any>(url);
    } catch (error) {
      console.error(
        `Failed to search documents in knowledge base ${knowledgeBaseId}:`,
        error
      );
      throw new Error(ApiErrorHandler.handleError(error, '搜索文档失败'));
    }
  }

  /**
   * 构建查询参数
   */
  private buildQueryParams(params?: any): string {
    if (!params) return '';

    const searchParams = new URLSearchParams();

    // 处理分页参数
    if (params.page !== undefined) searchParams.append('page', String(params.page));
    if (params.pageSize !== undefined) searchParams.append('page_size', String(params.pageSize));
    if (params.limit !== undefined) searchParams.append('limit', String(params.limit));
    if (params.offset !== undefined) searchParams.append('offset', String(params.offset));

    // 处理排序参数
    if (params.sortBy) {
      searchParams.append('sort_by', params.sortBy);
      if (params.sortOrder) {
        searchParams.append('sort_order', params.sortOrder);
      }
    }

    // 处理过滤参数
    if (params.search) searchParams.append('search', params.search);
    if (params.status) searchParams.append('status', params.status);
    if (params.fileType) searchParams.append('file_type', params.fileType);
    if (params.sizeFrom) searchParams.append('size_from', String(params.sizeFrom));
    if (params.sizeTo) searchParams.append('size_to', String(params.sizeTo));
    if (params.dateFrom) searchParams.append('date_from', params.dateFrom);
    if (params.dateTo) searchParams.append('date_to', params.dateTo);

    // 处理其他参数
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        searchParams.append(key, String(value));
      }
    });

    const queryString = searchParams.toString();
    return queryString ? `?${queryString}` : '';
  }
}

/**
 * 创建文档API实例
 */
export const documentApi = new DocumentApi();