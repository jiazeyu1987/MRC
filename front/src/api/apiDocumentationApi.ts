// API文档服务

import {
  ApiResponse,
  APIDocumentationCache,
  APIDocumentation,
  APIExample,
  APITestRequest,
  APITestResponse,
  RateLimitStatus,
  APIDocumentationCategory
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

// API文档服务
export class ApiDocumentationService {
  /**
   * 获取缓存的API文档
   */
  async getDocumentation(
    forceRefresh: boolean = false,
    category?: string
  ): Promise<APIDocumentationCache[]> {
    const queryParams = new URLSearchParams();
    if (forceRefresh) queryParams.append('force_refresh', 'true');
    if (category) queryParams.append('category', category);

    const endpoint = `/api-documentation${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    const response = await apiClient.get<ApiResponse<APIDocumentationCache[]>>(endpoint);
    return response.data;
  }

  /**
   * 获取特定端点的文档
   */
  async getEndpointDocumentation(
    endpointPath: string,
    method: string
  ): Promise<APIDocumentationCache | null> {
    const docs = await this.getDocumentation();
    return docs.find(doc =>
      doc.endpoint_path === endpointPath &&
      doc.method.toLowerCase() === method.toLowerCase()
    ) || null;
  }

  /**
   * 刷新API文档缓存
   */
  async refreshDocumentation(
    category?: string
  ): Promise<APIDocumentationCache[]> {
    return this.getDocumentation(true, category);
  }

  /**
   * 获取API文档分类
   */
  async getDocumentationCategories(): Promise<APIDocumentationCategory[]> {
    const endpoint = `/api-documentation/categories`;
    const response = await apiClient.get<ApiResponse<APIDocumentationCategory[]>>(endpoint);
    return response.data;
  }

  /**
   * 测试API端点
   */
  async testEndpoint(request: APITestRequest): Promise<APITestResponse> {
    const endpoint = `/api-playground`;
    const response = await apiClient.post<ApiResponse<APITestResponse>>(endpoint, request);
    return response.data;
  }

  /**
   * 获取API测试历史
   */
  async getTestHistory(
    limit: number = 20
  ): Promise<Array<{
    id: number;
    request: APITestRequest;
    response: APITestResponse;
    timestamp: string;
    user_id?: string;
  }>> {
    const endpoint = `/api-playground/history?limit=${limit}`;
    const response = await apiClient.get<ApiResponse<Array<{
      id: number;
      request: APITestRequest;
      response: APITestResponse;
      timestamp: string;
      user_id?: string;
    }>>>(endpoint);
    return response.data;
  }

  /**
   * 保存API测试
   */
  async saveTest(
    request: APITestRequest,
    response: APITestResponse,
    name?: string,
    description?: string
  ): Promise<{ id: number; success: boolean }> {
    const endpoint = `/api-playground/save`;
    const result = await apiClient.post<ApiResponse<{ id: number; success: boolean }>>(endpoint, {
      request,
      response,
      name,
      description
    });
    return result.data;
  }

  /**
   * 获取保存的API测试
   */
  async getSavedTests(
    category?: string
  ): Promise<Array<{
    id: number;
    name: string;
    description?: string;
    category?: string;
    request: APITestRequest;
    response: APITestResponse;
    created_at: string;
    updated_at: string;
  }>> {
    const queryParams = new URLSearchParams();
    if (category) queryParams.append('category', category);

    const endpoint = `/api-playground/saved${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    const response = await apiClient.get<ApiResponse<Array<{
      id: number;
      name: string;
      description?: string;
      category?: string;
      request: APITestRequest;
      response: APITestResponse;
      created_at: string;
      updated_at: string;
    }>>>(endpoint);
    return response.data;
  }

  /**
   * 删除保存的API测试
   */
  async deleteSavedTest(testId: number): Promise<{ success: boolean }> {
    const endpoint = `/api-playground/saved/${testId}`;
    const response = await apiClient.delete<ApiResponse<{ success: boolean }>>(endpoint);
    return response.data;
  }

  /**
   * 获取速率限制状态
   */
  async getRateLimitStatus(): Promise<RateLimitStatus> {
    const endpoint = `/api-rate-limit`;
    const response = await apiClient.get<ApiResponse<RateLimitStatus>>(endpoint);
    return response.data;
  }

  /**
   * 生成API客户端代码
   */
  async generateClientCode(
    language: 'javascript' | 'python' | 'curl' | 'java' | 'csharp',
    request: APITestRequest
  ): Promise<string> {
    const endpoint = `/api-playground/generate-code`;
    const response = await apiClient.post<ApiResponse<{ code: string }>>(endpoint, {
      language,
      request
    });
    return response.data.code;
  }

  /**
   * 验证API请求
   */
  async validateRequest(
    request: APITestRequest
  ): Promise<{
    valid: boolean;
    errors: string[];
    warnings: string[];
  }> {
    const endpoint = `/api-playground/validate`;
    const response = await apiClient.post<ApiResponse<{
      valid: boolean;
      errors: string[];
      warnings: string[];
    }>>(endpoint, request);
    return response.data;
  }

  /**
   * 获取API使用统计
   */
  async getUsageStatistics(
    days: number = 30
  ): Promise<{
    total_requests: number;
    successful_requests: number;
    failed_requests: number;
    average_response_time: number;
    most_used_endpoints: Array<{
      endpoint: string;
      method: string;
      count: number;
    }>;
    usage_by_day: Array<{
      date: string;
      requests: number;
      success_rate: number;
    }>;
  }> {
    const endpoint = `/api-documentation/usage-stats?days=${days}`;
    const response = await apiClient.get<ApiResponse<{
      total_requests: number;
      successful_requests: number;
      failed_requests: number;
      average_response_time: number;
      most_used_endpoints: Array<{
        endpoint: string;
        method: string;
        count: number;
      }>;
      usage_by_day: Array<{
        date: string;
        requests: number;
        success_rate: number;
      }>;
    }>>(endpoint);
    return response.data;
  }

  /**
   * 搜索API文档
   */
  async searchDocumentation(
    query: string,
    filters?: {
      category?: string;
      method?: string;
      tags?: string[];
    }
  ): Promise<APIDocumentationCache[]> {
    const queryParams = new URLSearchParams();
    queryParams.append('q', query);

    if (filters?.category) queryParams.append('category', filters.category);
    if (filters?.method) queryParams.append('method', filters.method);
    if (filters?.tags) filters.tags.forEach(tag => queryParams.append('tag', tag));

    const endpoint = `/api-documentation/search?${queryParams.toString()}`;
    const response = await apiClient.get<ApiResponse<APIDocumentationCache[]>>(endpoint);
    return response.data;
  }

  /**
   * 获取API变更日志
   */
  async getChangelog(
    limit: number = 20
  ): Promise<Array<{
    id: number;
    version: string;
    changes: Array<{
      type: 'added' | 'modified' | 'deprecated' | 'removed';
      endpoint: string;
      method: string;
      description: string;
    }>;
    release_date: string;
    author: string;
  }>> {
    const endpoint = `/api-documentation/changelog?limit=${limit}`;
    const response = await apiClient.get<ApiResponse<Array<{
      id: number;
      version: string;
      changes: Array<{
        type: 'added' | 'modified' | 'deprecated' | 'removed';
        endpoint: string;
        method: string;
        description: string;
      }>;
      release_date: string;
      author: string;
    }>>>(endpoint);
    return response.data;
  }

  /**
   * 导出API文档
   */
  async exportDocumentation(
    format: 'json' | 'yaml' | 'openapi' | 'postman',
    category?: string
  ): Promise<string> {
    const queryParams = new URLSearchParams();
    queryParams.append('format', format);
    if (category) queryParams.append('category', category);

    const endpoint = `/api-documentation/export?${queryParams.toString()}`;

    // 处理文件下载
    const url = `${API_BASE_URL}${endpoint}`;
    const fetchUrl = import.meta.env.DEV ? `/api${endpoint.replace('/api', '')}` : url;

    const response = await fetch(fetchUrl);
    if (!response.ok) {
      throw new Error(`Export failed: ${response.statusText}`);
    }

    return response.text();
  }
}

// 导出服务实例
export const apiDocumentationApi = new ApiDocumentationService();

// 导出类型供外部使用
export type {
  APIDocumentationCache,
  APIDocumentation,
  APIExample,
  APITestRequest,
  APITestResponse,
  RateLimitStatus,
  APIDocumentationCategory
};