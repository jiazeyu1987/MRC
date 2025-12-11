/**
 * API客户端统一入口
 *
 * 提供所有API客户端的统一访问接口和管理功能
 */

// 导入新的模块化API客户端
import { knowledgeBaseApi } from './knowledge/knowledgeBaseApi';
import { documentApi } from './documents/documentApi';
import { conversationApi } from './conversations/conversationApi';
import { ragflowApi } from './ragflow/ragflowApi';
import { analyticsApi } from './analytics/analyticsApi';

// 导入共享工具和类型
import { httpClient, ApiErrorHandler } from './shared/http-client';
import { CacheManager } from './shared/cache-manager';
import type { CacheOptions } from './types/common';

// 保留向后兼容的导出
export * from './knowledgeApi';
export * from './roleApi';
export * from './flowApi';
export * from './sessionApi';

/**
 * API客户端集合
 */
export interface ApiClients {
  knowledgeBase: typeof knowledgeBaseApi;
  documents: typeof documentApi;
  conversations: typeof conversationApi;
  ragflow: typeof ragflowApi;
  analytics: typeof analyticsApi;
}

/**
 * API配置接口
 */
export interface ApiConfig {
  baseUrl?: string;
  timeout?: number;
  retryAttempts?: number;
  enableCache?: boolean;
  cacheOptions?: CacheOptions;
  headers?: Record<string, string>;
  interceptors?: {
    request?: Array<(config: Request) => Request>;
    response?: Array<(response: Response) => Response>;
  };
}

/**
 * API客户端管理器
 */
export class ApiManager {
  private static instance: ApiManager;
  private config: ApiConfig;
  private cacheManager: CacheManager;
  private clients: ApiClients;

  private constructor(config: ApiConfig = {}) {
    this.config = {
      baseUrl: import.meta.env.VITE_API_BASE_URL || '/api',
      timeout: 30000,
      retryAttempts: 3,
      enableCache: true,
      cacheOptions: {
        ttl: 5 * 60 * 1000, // 5分钟默认缓存
      },
      ...config,
    };

    this.cacheManager = new CacheManager(this.config.cacheOptions);
    this.clients = this.createClients();
  }

  /**
   * 获取API管理器单例
   */
  static getInstance(config?: ApiConfig): ApiManager {
    if (!ApiManager.instance) {
      ApiManager.instance = new ApiManager(config);
    }
    return ApiManager.instance;
  }

  /**
   * 创建API客户端实例
   */
  private createClients(): ApiClients {
    return {
      knowledgeBase: knowledgeBaseApi,
      documents: documentApi,
      conversations: conversationApi,
      ragflow: ragflowApi,
      analytics: analyticsApi,
    };
  }

  /**
   * 获取所有API客户端
   */
  getClients(): ApiClients {
    return this.clients;
  }

  /**
   * 获取特定API客户端
   */
  getClient<K extends keyof ApiClients>(clientName: K): ApiClients[K] {
    return this.clients[clientName];
  }

  /**
   * 更新配置
   */
  updateConfig(newConfig: Partial<ApiConfig>): void {
    this.config = { ...this.config, ...newConfig };

    // 更新HTTP客户端配置 - 暂时注释，需要在shared/http-client中实现updateConfig方法
    // httpClient.updateConfig({
    //   baseUrl: this.config.baseUrl,
    //   timeout: this.config.timeout,
    //   retryAttempts: this.config.retryAttempts,
    //   headers: this.config.headers,
    // });

    // 更新缓存配置
    if (this.config.cacheOptions) {
      this.cacheManager.updateConfig(this.config.cacheOptions);
    }
  }

  /**
   * 获取当前配置
   */
  getConfig(): ApiConfig {
    return { ...this.config };
  }

  /**
   * 清除所有缓存
   */
  clearCache(): void {
    this.cacheManager.clear();
  }

  /**
   * 清除特定缓存
   */
  clearCacheByPattern(pattern: string): void {
    this.cacheManager.clearByPattern(pattern);
  }

  /**
   * 获取缓存统计
   */
  getCacheStats() {
    return this.cacheManager.getStats();
  }

  /**
   * 测试所有API连接
   */
  async testConnections(): Promise<Record<string, boolean>> {
    const results: Record<string, boolean> = {};

    try {
      // 测试知识库API
      await this.clients.knowledgeBase.listKnowledgeBases({ page: 1, pageSize: 1 });
      results.knowledgeBase = true;
    } catch (error) {
      results.knowledgeBase = false;
    }

    try {
      // 测试RAGFlow API
      const ragflowResult = await this.clients.ragflow.testConnection();
      results.ragflow = ragflowResult.success;
    } catch (error) {
      results.ragflow = false;
    }

    try {
      // 测试分析API
      await this.clients.analytics.getSystemOverview();
      results.analytics = true;
    } catch (error) {
      results.analytics = false;
    }

    return results;
  }
}

/**
 * 创建默认API管理器实例
 */
export const apiManager = ApiManager.getInstance();

/**
 * 导出所有API客户端（新架构）
 */
export const api = apiManager.getClients();

/**
 * 导出单个API客户端（便捷访问）
 */
export const {
  knowledgeBase,
  documents,
  conversations,
  ragflow,
  analytics,
} = api;

/**
 * 向后兼容的enhancedApi导出
 * 映射到新的API结构以保持现有组件兼容性
 */
export const enhancedApi = {
  searchAnalytics: analytics,
  conversation: {
    ...conversations,
    templates: conversations // 映射conversation.templates
  },
  enhancedStatistics: {
    getEnhancedStatistics: analytics.getSearchAnalytics,
    getTopActiveKnowledgeBases: analytics.getSystemOverview
  },
  apiDocumentation: {
    // 临时占位符，需要实现API文档功能
    getDocumentation: async (knowledgeBaseId: number) => ({ message: 'API Documentation - temporarily disabled' }),
    exportDocumentation: async (knowledgeBaseId: number, format: string) => ({ message: 'Export - temporarily disabled' })
  }
};

/**
 * 导出工具类和类型
 */
export { httpClient, ApiErrorHandler } from './shared/http-client';
export { CacheManager } from './shared/cache-manager';
export * from './types/common';
export * from './types/knowledge.types';

/**
 * 初始化API客户端
 */
export function initializeApi(config?: ApiConfig): ApiManager {
  return ApiManager.getInstance(config);
}

/**
 * 重置API管理器（主要用于测试）
 */
export function resetApiManager(): void {
  (ApiManager as any).instance = null;
}

// 导出默认配置
export const API_CONFIG = {
  BASE_URL: import.meta.env.VITE_API_BASE_URL_ALT ||
           import.meta.env.VITE_API_BASE_URL ||
           'http://localhost:5010',

  TIMEOUT: 30000,
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000,
};

// 通用API错误处理
export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public code?: string,
    public details?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// API响应包装器
export class ApiResponseWrapper<T> {
  constructor(
    public data: T,
    public success: boolean = true,
    public message?: string,
    public timestamp: string = new Date().toISOString()
  ) {}
}

// 请求拦截器
export const requestInterceptor = (config: RequestInit): RequestInit => {
  // 可以在这里添加通用的请求头、认证等
  return {
    ...config,
    headers: {
      'Content-Type': 'application/json',
      'X-Requested-With': 'XMLHttpRequest',
      ...config.headers,
    },
  };
};

// 响应拦截器
export const responseInterceptor = async <T>(
  response: Response,
  endpoint?: string
): Promise<T> => {
  if (!response.ok) {
    const errorText = await response.text();
    throw new ApiError(
      `API请求失败: ${response.statusText}`,
      response.status,
      response.status.toString(),
      { endpoint, errorText }
    );
  }

  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    const data = await response.json();
    return data;
  }

  return response.text() as unknown as T;
};

// 通用HTTP客户端
export class HttpClient {
  private baseURL: string;
  private timeout: number;

  constructor(baseURL: string = API_CONFIG.BASE_URL, timeout: number = API_CONFIG.TIMEOUT) {
    this.baseURL = baseURL;
    this.timeout = timeout;
  }

  private async fetchWithTimeout(url: string, options: RequestInit = {}): Promise<Response> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      return response;
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof Error && error.name === 'AbortError') {
        throw new ApiError(`请求超时 (${this.timeout}ms)`);
      }
      throw error;
    }
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    const fetchUrl = import.meta.env.DEV ? `/api${endpoint.replace('/api', '')}` : url;

    const config = requestInterceptor(options);
    const response = await this.fetchWithTimeout(fetchUrl, config);

    return responseInterceptor<T>(response, endpoint);
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

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'DELETE',
    });
  }

  async patch<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    });
  }
}

// HTTP客户端现在从shared/http-client导入

// API状态枚举
export enum ApiStatus {
  IDLE = 'idle',
  LOADING = 'loading',
  SUCCESS = 'success',
  ERROR = 'error'
}

// 分页信息接口
export interface PaginationInfo {
  page: number;
  per_page: number;
  total: number;
  pages: number;
  has_prev: boolean;
  has_next: boolean;
}

// 排序参数接口
export interface SortParams {
  sort_by: string;
  sort_order: 'asc' | 'desc';
}

// 过滤参数接口
export interface FilterParams {
  search?: string;
  filters?: Record<string, any>;
  date_range?: {
    start_date?: string;
    end_date?: string;
  };
}

// 通用API响应接口
export interface CommonApiResponse<T = any> {
  success: boolean;
  data: T;
  message?: string;
  error_code?: string;
  pagination?: PaginationInfo;
}

// 批量操作结果接口
export interface BulkOperationResult<T = any> {
  success: boolean;
  total: number;
  successful: number;
  failed: number;
  errors: string[];
  results?: T[];
}

// 文件上传响应接口
export interface FileUploadResponse {
  success: boolean;
  file_id?: string;
  file_name?: string;
  file_size?: number;
  file_type?: string;
  upload_url?: string;
  message?: string;
  errors?: string[];
}

// 导出响应接口
export interface ExportResponse {
  success: boolean;
  download_url?: string;
  file_name?: string;
  file_size?: number;
  expires_at?: string;
  message?: string;
}

// 健康检查响应接口
export interface HealthCheckResponse {
  status: 'healthy' | 'unhealthy' | 'degraded';
  timestamp: string;
  version: string;
  uptime: number;
  components: Record<string, {
    status: 'healthy' | 'unhealthy' | 'degraded';
    response_time_ms?: number;
    last_check: string;
    error_message?: string;
  }>;
}

// API版本信息接口
export interface ApiVersionInfo {
  version: string;
  build_number: string;
  build_date: string;
  git_commit: string;
  environment: 'development' | 'staging' | 'production';
}

// 用户偏好设置接口
export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  language: string;
  timezone: string;
  date_format: string;
  time_format: '12h' | '24h';
  notifications: {
    email: boolean;
    browser: boolean;
    in_app: boolean;
  };
  api_settings: {
    default_timeout: number;
    retry_attempts: number;
    auto_save: boolean;
  };
}

// 系统配置接口
export interface SystemConfig {
  api_version: string;
  max_file_size: number;
  allowed_file_types: string[];
  rate_limits: {
    requests_per_minute: number;
    requests_per_hour: number;
    requests_per_day: number;
  };
  features: {
    conversations: boolean;
    search_analytics: boolean;
    api_documentation: boolean;
    bulk_operations: boolean;
    exports: boolean;
  };
}