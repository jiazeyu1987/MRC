/**
 * 分析API客户端
 *
 * 提供系统分析、统计和洞察功能
 */

import { httpClient, ApiErrorHandler } from '../shared/http-client';
import type {
  SearchAnalytics,
  SearchInsights,
  KnowledgeBase
} from '../types/knowledge.types';

/**
 * 分析API类
 */
export class AnalyticsApi {
  private readonly basePath = '/api/analytics';

  /**
   * 获取搜索分析数据
   */
  async getSearchAnalytics(
    knowledgeBaseId: number,
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
      const url = `${this.basePath}/search/${knowledgeBaseId}${queryString ? `?${queryString}` : ''}`;

      return await httpClient.get<SearchAnalytics>(url);
    } catch (error) {
      console.error(`Failed to fetch search analytics for knowledge base ${knowledgeBaseId}:`, error);
      throw new Error(ApiErrorHandler.handleError(error, '获取搜索分析失败'));
    }
  }

  /**
   * 获取搜索洞察
   */
  async getSearchInsights(knowledgeBaseId: number): Promise<SearchInsights> {
    try {
      return await httpClient.get<SearchInsights>(
        `${this.basePath}/insights/${knowledgeBaseId}`
      );
    } catch (error) {
      console.error(`Failed to fetch search insights for knowledge base ${knowledgeBaseId}:`, error);
      throw new Error(ApiErrorHandler.handleError(error, '获取搜索洞察失败'));
    }
  }

  /**
   * 获取热门搜索术语
   */
  async getPopularTerms(
    knowledgeBaseId: number,
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
      const url = `${this.basePath}/popular-terms/${knowledgeBaseId}${queryString ? `?${queryString}` : ''}`;

      return await httpClient.get<any>(url);
    } catch (error) {
      console.error(`Failed to fetch popular terms for knowledge base ${knowledgeBaseId}:`, error);
      throw new Error(ApiErrorHandler.handleError(error, '获取热门术语失败'));
    }
  }

  /**
   * 获取系统概览统计
   */
  async getSystemOverview(): Promise<{
    totalKnowledgeBases: number;
    activeKnowledgeBases: number;
    totalDocuments: number;
    totalConversations: number;
    totalUsers: number;
    totalSearches: number;
    averageResponseTime: number;
    systemHealth: 'healthy' | 'warning' | 'critical';
    storageUsage: {
      used: number;
      total: number;
      percentage: number;
    };
    recentActivity: Array<{
      type: string;
      description: string;
      timestamp: string;
      userId?: number;
    }>;
  }> {
    try {
      return await httpClient.get<any>(`${this.basePath}/system/overview`);
    } catch (error) {
      console.error('Failed to fetch system overview:', error);
      throw new Error(ApiErrorHandler.handleError(error, '获取系统概览失败'));
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
      const url = `${this.basePath}/knowledge-bases/active${queryString ? `?${queryString}` : ''}`;

      return await httpClient.get<any>(url);
    } catch (error) {
      console.error('Failed to fetch active knowledge bases:', error);
      throw new Error(ApiErrorHandler.handleError(error, '获取活跃知识库排行失败'));
    }
  }

  /**
   * 获取用户行为分析
   */
  async getUserBehaviorAnalytics(params?: {
    userId?: number;
    startDate?: string;
    endDate?: string;
    groupBy?: 'day' | 'week' | 'month';
  }): Promise<{
    totalUsers: number;
    activeUsers: number;
    newUsers: number;
    userRetention: {
      day1: number;
      day7: number;
      day30: number;
    };
    userActivity: Array<{
      date: string;
      activeUsers: number;
      newUsers: number;
      totalSessions: number;
      averageSessionDuration: number;
    }>;
    topUsers: Array<{
      userId: number;
      username: string;
      activityScore: number;
      searchCount: number;
      conversationCount: number;
    }>;
  }> {
    try {
      const queryParams = new URLSearchParams();
      if (params?.userId) queryParams.append('user_id', String(params.userId));
      if (params?.startDate) queryParams.append('start_date', params.startDate);
      if (params?.endDate) queryParams.append('end_date', params.endDate);
      if (params?.groupBy) queryParams.append('group_by', params.groupBy);

      const queryString = queryParams.toString();
      const url = `${this.basePath}/users/behavior${queryString ? `?${queryString}` : ''}`;

      return await httpClient.get<any>(url);
    } catch (error) {
      console.error('Failed to fetch user behavior analytics:', error);
      throw new Error(ApiErrorHandler.handleError(error, '获取用户行为分析失败'));
    }
  }

  /**
   * 获取内容分析
   */
  async getContentAnalytics(params?: {
    knowledgeBaseId?: number;
    startDate?: string;
    endDate?: string;
    includeDocuments?: boolean;
    includeConversations?: boolean;
  }): Promise<{
    documentStatistics: {
      totalDocuments: number;
      processedDocuments: number;
      failedDocuments: number;
      averageProcessingTime: number;
      documentTypes: Record<string, number>;
      sizeDistribution: Array<{
        range: string;
        count: number;
        totalSize: number;
      }>;
    };
    conversationStatistics: {
      totalConversations: number;
      averageConversationLength: number;
      averageMessagesPerConversation: number;
      conversationTopics: Array<{
        topic: string;
        count: number;
        sentiment: 'positive' | 'neutral' | 'negative';
      }>;
    };
    contentQuality: {
      averageQualityScore: number;
      qualityDistribution: Record<string, number>;
      improvementSuggestions: string[];
    };
  }> {
    try {
      const queryParams = new URLSearchParams();
      if (params?.knowledgeBaseId) queryParams.append('knowledge_base_id', String(params.knowledgeBaseId));
      if (params?.startDate) queryParams.append('start_date', params.startDate);
      if (params?.endDate) queryParams.append('end_date', params.endDate);
      if (params?.includeDocuments !== undefined) queryParams.append('include_documents', String(params.includeDocuments));
      if (params?.includeConversations !== undefined) queryParams.append('include_conversations', String(params.includeConversations));

      const queryString = queryParams.toString();
      const url = `${this.basePath}/content${queryString ? `?${queryString}` : ''}`;

      return await httpClient.get<any>(url);
    } catch (error) {
      console.error('Failed to fetch content analytics:', error);
      throw new Error(ApiErrorHandler.handleError(error, '获取内容分析失败'));
    }
  }

  /**
   * 获取性能指标
   */
  async getPerformanceMetrics(params?: {
    startDate?: string;
    endDate?: string;
    interval?: 'minute' | 'hour' | 'day';
  }): Promise<{
    systemPerformance: {
      averageResponseTime: number;
      requestsPerSecond: number;
      errorRate: number;
      cpuUsage: number;
      memoryUsage: number;
      diskUsage: number;
    };
    apiMetrics: Array<{
      timestamp: string;
      endpoint: string;
      responseTime: number;
      statusCode: number;
      requestCount: number;
    }>;
    llmMetrics: Array<{
      timestamp: string;
      provider: string;
      model: string;
      tokenUsage: number;
      responseTime: number;
      successRate: number;
    }>;
    alerts: Array<{
      type: 'performance' | 'error' | 'resource';
      severity: 'low' | 'medium' | 'high';
      message: string;
      timestamp: string;
      resolved?: boolean;
    }>;
  }> {
    try {
      const queryParams = new URLSearchParams();
      if (params?.startDate) queryParams.append('start_date', params.startDate);
      if (params?.endDate) queryParams.append('end_date', params.endDate);
      if (params?.interval) queryParams.append('interval', params.interval);

      const queryString = queryParams.toString();
      const url = `${this.basePath}/performance${queryString ? `?${queryString}` : ''}`;

      return await httpClient.get<any>(url);
    } catch (error) {
      console.error('Failed to fetch performance metrics:', error);
      throw new Error(ApiErrorHandler.handleError(error, '获取性能指标失败'));
    }
  }

  /**
   * 生成报告
   */
  async generateReport(params: {
    type: 'system' | 'knowledge_base' | 'user' | 'content' | 'performance';
    knowledgeBaseId?: number;
    userId?: number;
    startDate?: string;
    endDate?: string;
    format?: 'json' | 'pdf' | 'csv';
    includeCharts?: boolean;
  }): Promise<{
    reportId: string;
    downloadUrl: string;
    format: string;
    size: number;
    expiresAt: string;
    generatedAt: string;
  }> {
    try {
      return await httpClient.post<any>(`${this.basePath}/reports/generate`, params);
    } catch (error) {
      console.error('Failed to generate report:', error);
      throw new Error(ApiErrorHandler.handleError(error, '生成报告失败'));
    }
  }

  /**
   * 获取报告状态
   */
  async getReportStatus(reportId: string): Promise<{
    reportId: string;
    status: 'pending' | 'processing' | 'completed' | 'failed';
    progress: number;
    downloadUrl?: string;
    error?: string;
    generatedAt?: string;
  }> {
    try {
      return await httpClient.get<any>(`${this.basePath}/reports/${reportId}/status`);
    } catch (error) {
      console.error(`Failed to get report status for ${reportId}:`, error);
      throw new Error(ApiErrorHandler.handleError(error, '获取报告状态失败'));
    }
  }

  /**
   * 获取实时指标
   */
  async getRealTimeMetrics(): Promise<{
    timestamp: string;
    activeUsers: number;
    activeConversations: number;
    currentRequests: number;
    systemLoad: {
      cpu: number;
      memory: number;
      disk: number;
    };
    responseTime: {
      p50: number;
      p95: number;
      p99: number;
    };
    errorRate: number;
    throughput: number;
  }> {
    try {
      return await httpClient.get<any>(`${this.basePath}/realtime/metrics`);
    } catch (error) {
      console.error('Failed to fetch real-time metrics:', error);
      throw new Error(ApiErrorHandler.handleError(error, '获取实时指标失败'));
    }
  }

  /**
   * 导出分析数据
   */
  async exportAnalyticsData(params: {
    type: 'search' | 'user' | 'content' | 'performance';
    knowledgeBaseId?: number;
    startDate?: string;
    endDate?: string;
    format: 'json' | 'csv' | 'xlsx';
    filters?: Record<string, any>;
  }): Promise<{
    exportId: string;
    downloadUrl: string;
    filename: string;
    format: string;
    size: number;
    expiresAt: string;
  }> {
    try {
      const response = await httpClient.post<any>(
        `${this.basePath}/export`,
        params
      );

      return {
        exportId: response.export_id,
        downloadUrl: response.download_url,
        filename: response.filename,
        format: response.format,
        size: response.size,
        expiresAt: response.expires_at,
      };
    } catch (error) {
      console.error('Failed to export analytics data:', error);
      throw new Error(ApiErrorHandler.handleError(error, '导出分析数据失败'));
    }
  }

  /**
   * 获取导出状态
   */
  async getExportStatus(exportId: string): Promise<{
    exportId: string;
    status: 'pending' | 'processing' | 'completed' | 'failed';
    progress: number;
    downloadUrl?: string;
    error?: string;
    createdAt: string;
    completedAt?: string;
  }> {
    try {
      return await httpClient.get<any>(`${this.basePath}/export/${exportId}/status`);
    } catch (error) {
      console.error(`Failed to get export status for ${exportId}:`, error);
      throw new Error(ApiErrorHandler.handleError(error, '获取导出状态失败'));
    }
  }
}

/**
 * 创建分析API实例
 */
export const analyticsApi = new AnalyticsApi();