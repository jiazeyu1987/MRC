/**
 * 对话API客户端
 *
 * 提供对话相关的API操作
 */

import { httpClient, ApiErrorHandler } from '../shared/http-client';
import type {
  KnowledgeBaseConversation,
  ConversationMessage,
  ConversationListParams,
  ConversationListResponse,
  ConversationExportOptions,
  ConversationExportResult,
} from '../types/knowledge.types';
import type { ListResponse, BulkOperationResult } from '../types/common';

/**
 * 对话API类
 */
export class ConversationApi {
  private readonly basePath = '/api/conversations';

  /**
   * 获取对话列表
   */
  async listConversations(
    knowledgeBaseId: number,
    params?: ConversationListParams & PaginationParams & FilterParams
  ): Promise<ConversationListResponse> {
    try {
      const queryParams = this.buildQueryParams(params);
      return await httpClient.get<ConversationListResponse>(
        `${this.basePath}/knowledge-base/${knowledgeBaseId}${queryParams}`
      );
    } catch (error) {
      console.error(`Failed to fetch conversations for knowledge base ${knowledgeBaseId}:`, error);
      throw new Error(ApiErrorHandler.handleError(error, '获取对话列表失败'));
    }
  }

  /**
   * 获取对话详情
   */
  async getConversation(
    knowledgeBaseId: number,
    conversationId: number
  ): Promise<KnowledgeBaseConversation> {
    try {
      return await httpClient.get<KnowledgeBaseConversation>(
        `${this.basePath}/knowledge-base/${knowledgeBaseId}/${conversationId}`
      );
    } catch (error) {
      console.error(
        `Failed to fetch conversation ${conversationId} for knowledge base ${knowledgeBaseId}:`,
        error
      );
      throw new Error(ApiErrorHandler.handleError(error, '获取对话详情失败'));
    }
  }

  /**
   * 创建对话
   */
  async createConversation(
    knowledgeBaseId: number,
    data: {
      title: string;
      initialMessage?: string;
      tags?: string[];
      metadata?: Record<string, any>;
    }
  ): Promise<KnowledgeBaseConversation> {
    try {
      return await httpClient.post<KnowledgeBaseConversation>(
        `${this.basePath}/knowledge-base/${knowledgeBaseId}`,
        data
      );
    } catch (error) {
      console.error(`Failed to create conversation for knowledge base ${knowledgeBaseId}:`, error);
      throw new Error(ApiErrorHandler.handleError(error, '创建对话失败'));
    }
  }

  /**
   * 更新对话
   */
  async updateConversation(
    knowledgeBaseId: number,
    conversationId: number,
    data: {
      title?: string;
      messages?: ConversationMessage[];
      tags?: string[];
      metadata?: Record<string, any>;
    }
  ): Promise<KnowledgeBaseConversation> {
    try {
      return await httpClient.put<KnowledgeBaseConversation>(
        `${this.basePath}/knowledge-base/${knowledgeBaseId}/${conversationId}`,
        data
      );
    } catch (error) {
      console.error(
        `Failed to update conversation ${conversationId} for knowledge base ${knowledgeBaseId}:`,
        error
      );
      throw new Error(ApiErrorHandler.handleError(error, '更新对话失败'));
    }
  }

  /**
   * 删除对话
   */
  async deleteConversation(
    knowledgeBaseId: number,
    conversationId: number
  ): Promise<void> {
    try {
      await httpClient.delete(
        `${this.basePath}/knowledge-base/${knowledgeBaseId}/${conversationId}`
      );
    } catch (error) {
      console.error(
        `Failed to delete conversation ${conversationId} for knowledge base ${knowledgeBaseId}:`,
        error
      );
      throw new Error(ApiErrorHandler.handleError(error, '删除对话失败'));
    }
  }

  /**
   * 获取对话消息
   */
  async getMessages(
    knowledgeBaseId: number,
    conversationId: number,
    params?: {
      page?: number;
      pageSize?: number;
      sortOrder?: 'asc' | 'desc';
    }
  ): Promise<ListResponse<ConversationMessage>> {
    try {
      const queryParams = new URLSearchParams();

      if (params?.page) queryParams.append('page', String(params.page));
      if (params?.pageSize) queryParams.append('page_size', String(params.pageSize));
      if (params?.sortOrder) queryParams.append('sort_order', params.sortOrder);

      const queryString = queryParams.toString();
      const url = `${this.basePath}/knowledge-base/${knowledgeBaseId}/${conversationId}/messages${queryString ? `?${queryString}` : ''}`;

      return await httpClient.get<ListResponse<ConversationMessage>>(url);
    } catch (error) {
      console.error(
        `Failed to fetch messages for conversation ${conversationId} in knowledge base ${knowledgeBaseId}:`,
        error
      );
      throw new Error(ApiErrorHandler.handleError(error, '获取对话消息失败'));
    }
  }

  /**
   * 添加消息到对话
   */
  async addMessage(
    knowledgeBaseId: number,
    conversationId: number,
    message: {
      role: 'user' | 'assistant' | 'system';
      content: string;
      metadata?: Record<string, any>;
    }
  ): Promise<ConversationMessage> {
    try {
      return await httpClient.post<ConversationMessage>(
        `${this.basePath}/knowledge-base/${knowledgeBaseId}/${conversationId}/messages`,
        message
      );
    } catch (error) {
      console.error(
        `Failed to add message to conversation ${conversationId} in knowledge base ${knowledgeBaseId}:`,
        error
      );
      throw new Error(ApiErrorHandler.handleError(error, '添加消息失败'));
    }
  }

  /**
   * 导出对话
   */
  async exportConversation(
    knowledgeBaseId: number,
    conversationId: number,
    options: ConversationExportOptions
  ): Promise<ConversationExportResult> {
    try {
      const queryParams = new URLSearchParams();
      queryParams.append('format', options.format);
      if (options.includeMetadata !== undefined) {
        queryParams.append('include_metadata', String(options.includeMetadata));
      }
      if (options.includeTimestamps !== undefined) {
        queryParams.append('include_timestamps', String(options.includeTimestamps));
      }
      if (options.messageFormat) {
        queryParams.append('message_format', options.messageFormat);
      }

      const queryString = queryParams.toString();
      const url = `${this.basePath}/knowledge-base/${knowledgeBaseId}/${conversationId}/export${queryString ? `?${queryString}` : ''}`;

      return await httpClient.get<ConversationExportResult>(url);
    } catch (error) {
      console.error(
        `Failed to export conversation ${conversationId} for knowledge base ${knowledgeBaseId}:`,
        error
      );
      throw new Error(ApiErrorHandler.handleError(error, '导出对话失败'));
    }
  }

  /**
   * 获取对话模板
   */
  async getConversationTemplates(
    knowledgeBaseId: number
  ): Promise<Array<{
    id: number;
    name: string;
    description: string;
    knowledgeBaseId: number;
    initialMessage?: string;
    conversationStructure: any;
    tags: string[];
    usageCount: number;
    isActive: boolean;
    createdAt: string;
    updatedAt: string;
  }>> {
    try {
      return await httpClient.get<any>(
        `${this.basePath}/knowledge-base/${knowledgeBaseId}/templates`
      );
    } catch (error) {
      console.error(`Failed to fetch conversation templates for knowledge base ${knowledgeBaseId}:`, error);
      throw new Error(ApiErrorHandler.handleError(error, '获取对话模板失败'));
    }
  }

  /**
   * 保存对话模板
   */
  async saveConversationTemplate(
    knowledgeBaseId: number,
    data: {
      conversationId: number;
      templateName: string;
      description?: string;
      includeMessages?: boolean;
      tags?: string[];
    }
  ): Promise<any> {
    try {
      return await httpClient.post<any>(
        `${this.basePath}/knowledge-base/${knowledgeBaseId}/templates`,
        data
      );
    } catch (error) {
      console.error(`Failed to save conversation template for knowledge base ${knowledgeBaseId}:`, error);
      throw new Error(ApiErrorHandler.handleError(error, '保存对话模板失败'));
    }
  }

  /**
   * 删除对话模板
   */
  async deleteConversationTemplate(
    knowledgeBaseId: number,
    templateId: number
  ): Promise<void> {
    try {
      await httpClient.delete(
        `${this.basePath}/knowledge-base/${knowledgeBaseId}/templates/${templateId}`
      );
    } catch (error) {
      console.error(
        `Failed to delete conversation template ${templateId} for knowledge base ${knowledgeBaseId}:`,
        error
      );
      throw new Error(ApiErrorHandler.handleError(error, '删除对话模板失败'));
    }
  }

  /**
   * 批量操作对话
   */
  async bulkOperation(
    knowledgeBaseId: number,
    data: {
      action: 'delete' | 'archive' | 'unarchive' | 'export';
      conversationIds: number[];
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
        `Failed to perform bulk operation on conversations in knowledge base ${knowledgeBaseId}:`,
        error
      );
      throw new Error(ApiErrorHandler.handleError(error, '批量操作对话失败'));
    }
  }

  /**
   * 获取对话统计
   */
  async getConversationStatistics(
    knowledgeBaseId: number,
    conversationId: number
  ): Promise<{
    messageCount: number;
    userMessageCount: number;
    assistantMessageCount: number;
    totalTokens: number;
    averageTokensPerMessage: number;
    conversationDuration: number;
    firstResponseTime?: number;
    lastActivity: string;
  }> {
    try {
      return await httpClient.get<any>(
        `${this.basePath}/knowledge-base/${knowledgeBaseId}/${conversationId}/statistics`
      );
    } catch (error) {
      console.error(
        `Failed to fetch statistics for conversation ${conversationId} in knowledge base ${knowledgeBaseId}:`,
        error
      );
      throw new Error(ApiErrorHandler.handleError(error, '获取对话统计失败'));
    }
  }

  /**
   * 搜索对话
   */
  async searchConversations(
    knowledgeBaseId: number,
    params: {
      query?: string;
      filters?: {
        status?: string;
        tags?: string[];
        dateFrom?: string;
        dateTo?: string;
      };
      pagination?: PaginationParams;
    }
  ): Promise<{
    conversations: KnowledgeBaseConversation[];
    total: number;
    facets?: Record<string, Array<{ value: string; count: number }>>;
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
        if (params.filters.status) {
          queryParams.append('status', params.filters.status);
        }
        if (params.filters.tags && params.filters.tags.length > 0) {
          params.filters.tags.forEach((tag) => {
            queryParams.append('tags', tag);
          });
        }
        if (params.filters.dateFrom) {
          queryParams.append('date_from', params.filters.dateFrom);
        }
        if (params.filters.dateTo) {
          queryParams.append('date_to', params.filters.dateTo);
        }
      }

      const queryString = queryParams.toString();
      const url = `${this.basePath}/knowledge-base/${knowledgeBaseId}/search${queryString ? `?${queryString}` : ''}`;

      return await httpClient.get<any>(url);
    } catch (error) {
      console.error(
        `Failed to search conversations in knowledge base ${knowledgeBaseId}:`,
        error
      );
      throw new Error(ApiErrorHandler.handleError(error, '搜索对话失败'));
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
    if (params.tags) {
      if (Array.isArray(params.tags)) {
        params.tags.forEach((tag) => {
          searchParams.append('tags', tag);
        });
      } else {
        searchParams.append('tags', String(params.tags));
      }
    }

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
 * 创建对话API实例
 */
export const conversationApi = new ConversationApi();