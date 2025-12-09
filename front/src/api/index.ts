// API服务统一导出

// 导入现有的API
export * from './knowledgeApi';
export * from './roleApi';
export * from './flowApi';
export * from './sessionApi';

// 导入增强功能API
export * from './conversationApi';
export * from './searchAnalyticsApi';
export * from './apiDocumentationApi';
export * from './ragflowChatApi';

// 统一的API服务实例
import { conversationApi, conversationTemplateApi } from './conversationApi';
import { searchAnalyticsApi, enhancedStatisticsApi } from './searchAnalyticsApi';
import { apiDocumentationApi } from './apiDocumentationApi';

export const enhancedApi = {
  // 对话相关
  conversation: conversationApi,
  conversationTemplate: conversationTemplateApi,

  // 搜索分析相关
  searchAnalytics: searchAnalyticsApi,
  enhancedStatistics: enhancedStatisticsApi,

  // API文档相关
  apiDocumentation: apiDocumentationApi
};

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

// 创建默认HTTP客户端实例
export const httpClient = new HttpClient();

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