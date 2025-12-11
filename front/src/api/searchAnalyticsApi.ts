// 搜索分析API服务

import {
  ApiResponse,
  SearchAnalytics,
  SearchStatistics,
  PopularTerm,
  UsageTrend,
  UserSearchPattern,
  PerformanceInsights,
  RecordSearchRequest,
  SearchAnalyticsParams,
  TopActiveKnowledgeBase,
  EnhancedKnowledgeBaseStatistics
} from '../types/enhanced';

// API基础URL配置 - 使用相对路径以利用Vite代理
const API_BASE_URL = '/api';

// HTTP请求辅助函数
class ApiClient {
  private baseURL: string;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;

    // 在开发环境下，通过Vite代理转发请求
    const fetchUrl = import.meta.env.DEV ? `/api${endpoint.replace('/api', '')}` : url;

    const response = await fetch(fetchUrl, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTP ${response.status}: ${errorText}`);
    }

    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return response.json();
    }

    return response.text() as unknown as T;
  }

  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint);
  }

  async post<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async put<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }
}

const apiClient = new ApiClient(API_BASE_URL);

// 搜索分析API服务
export class SearchAnalyticsApiService {
  /**
   * 获取知识库的搜索分析数据
   */
  async getSearchAnalytics(
    knowledgeBaseId: number,
    days: number = 30
  ): Promise<SearchStatistics> {
    const endpoint = `/knowledge-bases/${knowledgeBaseId}/search-analytics?days=${days}`;
    const response = await apiClient.get<ApiResponse<SearchStatistics>>(endpoint);
    return response.data;
  }

  /**
   * 记录搜索事件
   */
  async recordSearch(
    knowledgeBaseId: number,
    request: RecordSearchRequest
  ): Promise<SearchAnalytics> {
    const endpoint = `/knowledge-bases/${knowledgeBaseId}/search-analytics`;
    const response = await apiClient.post<ApiResponse<SearchAnalytics>>(endpoint, request);
    return response.data;
  }

  /**
   * 批量记录搜索事件
   */
  async batchRecordSearches(
    knowledgeBaseId: number,
    searches: RecordSearchRequest[]
  ): Promise<{ success: number; failed: number; errors: string[] }> {
    const endpoint = `/knowledge-bases/${knowledgeBaseId}/search-analytics/batch`;
    const response = await apiClient.post<ApiResponse<{ success: number; failed: number; errors: string[] }>>(endpoint, {
      searches
    });
    return response.data;
  }

  /**
   * 获取搜索性能洞察
   */
  async getSearchInsights(
    knowledgeBaseId: number,
    days: number = 30
  ): Promise<PerformanceInsights> {
    const endpoint = `/knowledge-bases/${knowledgeBaseId}/search-insights?days=${days}`;
    const response = await apiClient.get<ApiResponse<PerformanceInsights>>(endpoint);
    return response.data;
  }

  /**
   * 获取热门搜索词
   */
  async getPopularTerms(
    knowledgeBaseId: number,
    days: number = 30,
    limit: number = 10
  ): Promise<PopularTerm[]> {
    const endpoint = `/knowledge-bases/${knowledgeBaseId}/popular-terms?days=${days}&limit=${limit}`;
    const response = await apiClient.get<ApiResponse<PopularTerm[]>>(endpoint);
    return response.data;
  }

  /**
   * 获取使用趋势
   */
  async getUsageTrends(
    knowledgeBaseId: number,
    days: number = 30
  ): Promise<UsageTrend[]> {
    const endpoint = `/knowledge-bases/${knowledgeBaseId}/search-analytics/trends?days=${days}`;
    const response = await apiClient.get<ApiResponse<UsageTrend[]>>(endpoint);
    return response.data;
  }

  /**
   * 获取用户搜索模式
   */
  async getUserSearchPatterns(
    knowledgeBaseId: number,
    days: number = 30,
    limit: number = 10
  ): Promise<UserSearchPattern[]> {
    const endpoint = `/knowledge-bases/${knowledgeBaseId}/search-analytics/user-patterns?days=${days}&limit=${limit}`;
    const response = await apiClient.get<ApiResponse<UserSearchPattern[]>>(endpoint);
    return response.data;
  }

  /**
   * 获取无结果搜索分析
   */
  async getNoResultSearches(
    knowledgeBaseId: number,
    days: number = 30
  ): Promise<{ queries: string[]; count: number; percentage: number }> {
    const endpoint = `/knowledge-bases/${knowledgeBaseId}/search-analytics/no-results?days=${days}`;
    const response = await apiClient.get<ApiResponse<{ queries: string[]; count: number; percentage: number }>>(endpoint);
    return response.data;
  }

  /**
   * 获取搜索性能指标
   */
  async getPerformanceMetrics(
    knowledgeBaseId: number,
    days: number = 30
  ): Promise<{
    avg_response_time: number;
    p95_response_time: number;
    p99_response_time: number;
    success_rate: number;
    error_rate: number;
  }> {
    const endpoint = `/knowledge-bases/${knowledgeBaseId}/search-analytics/performance?days=${days}`;
    const response = await apiClient.get<ApiResponse<{
      avg_response_time: number;
      p95_response_time: number;
      p99_response_time: number;
      success_rate: number;
      error_rate: number;
    }>>(endpoint);
    return response.data;
  }

  /**
   * 获取搜索词云数据
   */
  async getSearchWordCloud(
    knowledgeBaseId: number,
    days: number = 30,
    minFrequency: number = 2
  ): Promise<Array<{ text: string; size: number; count: number }>> {
    const endpoint = `/knowledge-bases/${knowledgeBaseId}/search-analytics/wordcloud?days=${days}&min_frequency=${minFrequency}`;
    const response = await apiClient.get<ApiResponse<Array<{ text: string; size: number; count: number }>>>(endpoint);
    return response.data;
  }

  /**
   * 获取搜索热力图数据
   */
  async getSearchHeatmap(
    knowledgeBaseId: number,
    days: number = 7
  ): Promise<Array<{ hour: number; day: number; count: number }>> {
    const endpoint = `/knowledge-bases/${knowledgeBaseId}/search-analytics/heatmap?days=${days}`;
    const response = await apiClient.get<ApiResponse<Array<{ hour: number; day: number; count: number }>>>(endpoint);
    return response.data;
  }

  /**
   * 导出搜索分析数据
   */
  async exportSearchAnalytics(
    knowledgeBaseId: number,
    format: 'csv' | 'json' | 'excel' = 'csv',
    params: SearchAnalyticsParams = {}
  ): Promise<string> {
    const queryParams = new URLSearchParams();
    queryParams.append('format', format);
    if (params.days) queryParams.append('days', params.days.toString());
    if (params.user_id) queryParams.append('user_id', params.user_id);
    if (params.query_type) queryParams.append('query_type', params.query_type);
    if (params.include_performance) queryParams.append('include_performance', params.include_performance.toString());

    const endpoint = `/knowledge-bases/${knowledgeBaseId}/search-analytics/export?${queryParams.toString()}`;

    // 处理文件下载
    const url = `${API_BASE_URL}${endpoint}`;
    const fetchUrl = import.meta.env.DEV ? `/api${endpoint.replace('/api', '')}` : url;

    const response = await fetch(fetchUrl);
    if (!response.ok) {
      throw new Error(`Export failed: ${response.statusText}`);
    }

    return response.text();
  }

  /**
   * 清理旧的搜索分析数据
   */
  async cleanupOldAnalytics(
    knowledgeBaseId: number,
    days: number = 365
  ): Promise<{ deleted_count: number; success: boolean }> {
    const endpoint = `/knowledge-bases/${knowledgeBaseId}/search-analytics/cleanup?days=${days}`;
    const response = await apiClient.post<ApiResponse<{ deleted_count: number; success: boolean }>>(endpoint);
    return response.data;
  }
}

// 知识库增强统计API服务
export class EnhancedStatisticsApiService {
  /**
   * 获取知识库增强统计信息
   */
  async getEnhancedStatistics(
    knowledgeBaseId: number,
    days: number = 30
  ): Promise<EnhancedKnowledgeBaseStatistics> {
    const endpoint = `/knowledge-bases/${knowledgeBaseId}/enhanced-statistics?days=${days}`;
    const response = await apiClient.get<ApiResponse<EnhancedKnowledgeBaseStatistics>>(endpoint);
    return response.data;
  }

  /**
   * 获取最活跃的知识库排行
   */
  async getTopActiveKnowledgeBases(
    limit: number = 10,
    days: number = 30
  ): Promise<TopActiveKnowledgeBase[]> {
    const endpoint = `/knowledge-bases/top-active?limit=${limit}&days=${days}`;
    const response = await apiClient.get<ApiResponse<TopActiveKnowledgeBase[]>>(endpoint);
    return response.data;
  }

  /**
   * 获取所有知识库的综合统计
   */
  async getGlobalStatistics(
    days: number = 30
  ): Promise<{
    total_knowledge_bases: number;
    active_knowledge_bases: number;
    total_conversations: number;
    total_searches: number;
    total_users: number;
    engagement_metrics: {
      avg_conversations_per_kb: number;
      avg_searches_per_kb: number;
      avg_users_per_kb: number;
    };
  }> {
    const endpoint = `/knowledge-bases/global-statistics?days=${days}`;
    const response = await apiClient.get<ApiResponse<{
      total_knowledge_bases: number;
      active_knowledge_bases: number;
      total_conversations: number;
      total_searches: number;
      total_users: number;
      engagement_metrics: {
        avg_conversations_per_kb: number;
        avg_searches_per_kb: number;
        avg_users_per_kb: number;
      };
    }>>(endpoint);
    return response.data;
  }

  /**
   * 获取知识库活动趋势
   */
  async getActivityTrends(
    knowledgeBaseId?: number,
    days: number = 30
  ): Promise<Array<{
    date: string;
    conversations: number;
    searches: number;
    unique_users: number;
  }>> {
    const endpoint = knowledgeBaseId
      ? `/knowledge-bases/${knowledgeBaseId}/activity-trends?days=${days}`
      : `/knowledge-bases/activity-trends?days=${days}`;

    const response = await apiClient.get<ApiResponse<Array<{
      date: string;
      conversations: number;
      searches: number;
      unique_users: number;
    }>>>(endpoint);
    return response.data;
  }
}

// 导出服务实例
export const searchAnalyticsApi = new SearchAnalyticsApiService();
export const enhancedStatisticsApi = new EnhancedStatisticsApiService();

// 导出类型供外部使用
export type {
  SearchAnalytics,
  SearchStatistics,
  PopularTerm,
  UsageTrend,
  UserSearchPattern,
  PerformanceInsights,
  RecordSearchRequest,
  SearchAnalyticsParams,
  TopActiveKnowledgeBase,
  EnhancedKnowledgeBaseStatistics
};