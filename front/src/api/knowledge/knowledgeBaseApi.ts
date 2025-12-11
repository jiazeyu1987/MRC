/**
 * 知识库API客户端
 *
 * 提供知识库相关的API操作
 */

import { httpClient, ApiErrorHandler } from '../shared/http-client';
import type {
  KnowledgeBase,
  KnowledgeBaseListParams,
  KnowledgeBaseListResponse,
  KnowledgeBaseStatistics,
  KnowledgeBaseCreateRequest,
  KnowledgeBaseUpdateRequest,
  KnowledgeBaseActionRequest,
  TestConversationRequest,
  TestConversationResponse,
  SyncResult,
  RefreshResult,
  ConversationExportOptions,
  ConversationExportResult,
  SearchAnalytics,
  SearchInsights,
  KnowledgeBaseBulkOperation,
  KnowledgeBaseValidationResult,
} from '../types/knowledge.types';
import type { ListResponse, BulkOperationResult } from '../types/common';

/**
 * 知识库API类
 */
export class KnowledgeBaseApi {
  private readonly basePath = '/api/knowledge-bases';

  /**
   * 获取知识库列表
   */
  async listKnowledgeBases(
    params?: KnowledgeBaseListParams & PaginationParams & FilterParams
  ): Promise<KnowledgeBaseListResponse> {
    try {
      const queryParams = this.buildQueryParams(params);
      return await httpClient.get<KnowledgeBaseListResponse>(
        `${this.basePath}${queryParams}`
      );
    } catch (error) {
      console.error('Failed to fetch knowledge bases:', error);
      throw new Error(ApiErrorHandler.handleError(error, '获取知识库列表失败'));
    }
  }

  /**
   * 获取知识库详情
   */
  async getKnowledgeBase(id: number): Promise<KnowledgeBase> {
    try {
      return await httpClient.get<KnowledgeBase>(`${this.basePath}/${id}`);
    } catch (error) {
      console.error(`Failed to fetch knowledge base ${id}:`, error);
      throw new Error(ApiErrorHandler.handleError(error, '获取知识库详情失败'));
    }
  }

  /**
   * 创建知识库
   */
  async createKnowledgeBase(
    data: KnowledgeBaseCreateRequest
  ): Promise<KnowledgeBase> {
    try {
      return await httpClient.post<KnowledgeBase>(this.basePath, data);
    } catch (error) {
      console.error('Failed to create knowledge base:', error);
      throw new Error(ApiErrorHandler.handleError(error, '创建知识库失败'));
    }
  }

  /**
   * 更新知识库
   */
  async updateKnowledgeBase(
    id: number,
    data: KnowledgeBaseUpdateRequest
  ): Promise<KnowledgeBase> {
    try {
      return await httpClient.put<KnowledgeBase>(`${this.basePath}/${id}`, data);
    } catch (error) {
      console.error(`Failed to update knowledge base ${id}:`, error);
      throw new Error(ApiErrorHandler.handleError(error, '更新知识库失败'));
    }
  }

  /**
   * 删除知识库
   */
  async deleteKnowledgeBase(id: number): Promise<void> {
    try {
      await httpClient.delete(`${this.basePath}/${id}`);
    } catch (error) {
      console.error(`Failed to delete knowledge base ${id}:`, error);
      throw new Error(ApiErrorHandler.handleError(error, '删除知识库失败'));
    }
  }

  /**
   * 执行知识库操作（刷新等）
   */
  async performKnowledgeBaseAction(
    data: KnowledgeBaseActionRequest
  ): Promise<SyncResult | RefreshResult> {
    try {
      const response = await httpClient.post<any>(
        `${this.basePath}`,
        data
      );

      if (data.action === 'refresh_all') {
        return response as SyncResult;
      } else if (data.action === 'refresh_single') {
        return response as RefreshResult;
      }

      throw new Error('不支持的操作类型');
    } catch (error) {
      console.error('Failed to perform knowledge base action:', error);
      throw new Error(ApiErrorHandler.handleError(error, '执行知识库操作失败'));
    }
  }

  /**
   * 测试知识库对话
   */
  async testConversation(
    id: number,
    data: TestConversationRequest
  ): Promise<TestConversationResponse> {
    try {
      return await httpClient.post<TestConversationResponse>(
        `${this.basePath}/${id}/test-conversation`,
        data
      );
    } catch (error) {
      console.error(`Failed to test conversation for knowledge base ${id}:`, error);
      throw new Error(ApiErrorHandler.handleError(error, '测试对话失败'));
    }
  }

  /**
   * 获取知识库统计信息
   */
  async getStatistics(id: number): Promise<KnowledgeBaseStatistics> {
    try {
      return await httpClient.get<KnowledgeBaseStatistics>(
        `${this.basePath}/${id}/statistics`
      );
    } catch (error) {
      console.error(`Failed to fetch statistics for knowledge base ${id}:`, error);
      throw new Error(ApiErrorHandler.handleError(error, '获取统计信息失败'));
    }
  }

  /**
   * 批量操作知识库
   */
  async bulkOperation(
    data: KnowledgeBaseBulkOperation
  ): Promise<BulkOperationResult> {
    try {
      return await httpClient.post<BulkOperationResult>(
        `${this.basePath}/bulk-operation`,
        data
      );
    } catch (error) {
      console.error('Failed to perform bulk operation:', error);
      throw new Error(ApiErrorHandler.handleError(error, '批量操作失败'));
    }
  }

  /**
   * 验证知识库配置
   */
  async validateKnowledgeBase(id: number): Promise<KnowledgeBaseValidationResult> {
    try {
      return await httpClient.post<KnowledgeBaseValidationResult>(
        `${this.basePath}/${id}/validate`
      );
    } catch (error) {
      console.error(`Failed to validate knowledge base ${id}:`, error);
      throw new Error(ApiErrorHandler.handleError(error, '验证知识库失败'));
    }
  }

  /**
   * 获取搜索分析数据
   */
  async getSearchAnalytics(
    id: number,
    params?: {
      days?: number;
      startDate?: string;
      endDate?: string;
      groupBy?: 'day' | 'week' | 'month';
    }
  ): Promise<SearchAnalytics> {
    try {
      const queryParams = new URLSearchParams();
      if (params?.days) queryParams.append('days', String(params.days));
      if (params?.startDate) queryParams.append('startDate', params.startDate);
      if (params?.endDate) queryParams.append('endDate', params.endDate);
      if (params?.groupBy) queryParams.append('groupBy', params.groupBy);

      const queryString = queryParams.toString();
      const url = `${this.basePath}/${id}/analytics/search${queryString ? `?${queryString}` : ''}`;

      return await httpClient.get<SearchAnalytics>(url);
    } catch (error) {
      console.error(`Failed to fetch search analytics for knowledge base ${id}:`, error);
      throw new Error(ApiErrorHandler.handleError(error, '获取搜索分析失败'));
    }
  }

  /**
   * 获取搜索洞察
   */
  async getSearchInsights(id: number): Promise<SearchInsights> {
    try {
      return await httpClient.get<SearchInsights>(
        `${this.basePath}/${id}/analytics/insights`
      );
    } catch (error) {
      console.error(`Failed to fetch search insights for knowledge base ${id}:`, error);
      throw new Error(ApiErrorHandler.handleError(error, '获取搜索洞察失败'));
    }
  }

  /**
   * 导出知识库对话
   */
  async exportConversations(
    id: number,
    conversationId: number,
    options: ConversationExportOptions
  ): Promise<ConversationExportResult> {
    try {
      const queryParams = new URLSearchParams();
      queryParams.append('format', options.format);
      if (options.includeMetadata !== undefined) {
        queryParams.append('includeMetadata', String(options.includeMetadata));
      }
      if (options.includeTimestamps !== undefined) {
        queryParams.append('includeTimestamps', String(options.includeTimestamps));
      }
      if (options.messageFormat) {
        queryParams.append('messageFormat', options.messageFormat);
      }

      const queryString = queryParams.toString();
      const url = `${this.basePath}/${id}/conversations/${conversationId}/export${queryString ? `?${queryString}` : ''}`;

      return await httpClient.get<ConversationExportResult>(url);
    } catch (error) {
      console.error(
        `Failed to export conversation ${conversationId} for knowledge base ${id}:`,
        error
      );
      throw new Error(ApiErrorHandler.handleError(error, '导出对话失败'));
    }
  }

  /**
   * 获取热门搜索术语
   */
  async getPopularTerms(
    id: number,
    params?: {
      limit?: number;
      days?: number;
      type?: 'all' | 'successful' | 'failed';
    }
  ): Promise<Array<{ term: string; count: number; type: string }>> {
    try {
      const queryParams = new URLSearchParams();
      if (params?.limit) queryParams.append('limit', String(params.limit));
      if (params?.days) queryParams.append('days', String(params.days));
      if (params?.type) queryParams.append('type', params.type);

      const queryString = queryParams.toString();
      const url = `${this.basePath}/${id}/analytics/popular-terms${queryString ? `?${queryString}` : ''}`;

      return await httpClient.get<any>(url);
    } catch (error) {
      console.error(`Failed to fetch popular terms for knowledge base ${id}:`, error);
      throw new Error(ApiErrorHandler.handleError(error, '获取热门术语失败'));
    }
  }

  /**
   * 连接测试
   */
  async testConnection(id: number): Promise<{
    success: boolean;
    message: string;
    responseTime?: number;
  }> {
    try {
      return await httpClient.get<any>(`${this.basePath}/${id}/test-connection`);
    } catch (error) {
      console.error(`Failed to test connection for knowledge base ${id}:`, error);
      return {
        success: false,
        message: ApiErrorHandler.handleError(error, '连接测试失败'),
      };
    }
  }

  /**
   * 获取活跃知识库排行
   */
  async getActiveKnowledgeBases(params?: {
    limit?: number;
    days?: number;
    metric?: 'search_count' | 'document_count' | 'conversation_count';
  }): Promise<Array<KnowledgeBase & { activityScore: number }>> {
    try {
      const queryParams = new URLSearchParams();
      if (params?.limit) queryParams.append('limit', String(params.limit));
      if (params?.days) queryParams.append('days', String(params.days));
      if (params?.metric) queryParams.append('metric', params.metric);

      const queryString = queryParams.toString();
      const url = `${this.basePath}/analytics/active-knowledge-bases${queryString ? `?${queryString}` : ''}`;

      return await httpClient.get<any>(url);
    } catch (error) {
      console.error('Failed to fetch active knowledge bases:', error);
      throw new Error(ApiErrorHandler.handleError(error, '获取活跃知识库排行失败'));
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
    if (params.isActive !== undefined) searchParams.append('is_active', String(params.isActive));

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
 * 创建知识库API实例
 */
export const knowledgeBaseApi = new KnowledgeBaseApi();