/**
 * 共享HTTP客户端
 *
 * 提供统一的HTTP请求处理、错误处理、拦截器等功能
 */

export interface ApiConfig {
  baseURL: string;
  timeout?: number;
  headers?: Record<string, string>;
  interceptors?: {
    request?: RequestInterceptor[];
    response?: ResponseInterceptor[];
  };
}

export interface RequestInterceptor {
  (config: RequestInit): RequestInit | Promise<RequestInit>;
}

export interface ResponseInterceptor {
  (response: Response): Response | Promise<Response>;
}

export interface ApiError extends Error {
  status?: number;
  data?: any;
  code?: string;
}

export interface ApiResponse<T = any> {
  success: boolean;
  data: T;
  message?: string;
  error?: string;
}

export interface PaginationParams {
  page?: number;
  pageSize?: number;
  limit?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

export interface FilterParams {
  search?: string;
  status?: string;
  dateFrom?: string;
  dateTo?: string;
  [key: string]: any;
}

/**
 * HTTP客户端类
 */
export class HttpClient {
  private config: ApiConfig;
  private requestInterceptors: RequestInterceptor[] = [];
  private responseInterceptors: ResponseInterceptor[] = [];

  constructor(config: ApiConfig) {
    this.config = {
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
      ...config,
    };

    this.requestInterceptors = config.interceptors?.request || [];
    this.responseInterceptors = config.interceptors?.response || [];
  }

  /**
   * 添加请求拦截器
   */
  addRequestInterceptor(interceptor: RequestInterceptor): void {
    this.requestInterceptors.push(interceptor);
  }

  /**
   * 添加响应拦截器
   */
  addResponseInterceptor(interceptor: ResponseInterceptor): void {
    this.responseInterceptors.push(interceptor);
  }

  /**
   * 执行HTTP请求
   */
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.config.baseURL}${endpoint}`;

    // 应用请求拦截器
    let finalOptions = { ...options };
    for (const interceptor of this.requestInterceptors) {
      finalOptions = await interceptor(finalOptions);
    }

    const config: RequestInit = {
      headers: {
        ...this.config.headers,
        ...finalOptions.headers,
      },
      ...finalOptions,
    };

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.config.timeout);

      const response = await fetch(url, {
        ...config,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      // 应用响应拦截器
      let finalResponse = response;
      for (const interceptor of this.responseInterceptors) {
        finalResponse = await interceptor(finalResponse);
      }

      return this.handleResponse<T>(finalResponse);
    } catch (error) {
      throw this.handleError(error, endpoint);
    }
  }

  /**
   * 处理响应
   */
  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      return this.handleHttpError(response);
    }

    try {
      const data: ApiResponse<T> = await response.json();

      if (!data.success) {
        const error = new Error(data.message || '请求失败') as ApiError;
        error.code = 'API_ERROR';
        error.data = data.error;
        throw error;
      }

      return data.data;
    } catch (error) {
      if (error instanceof SyntaxError) {
        throw new Error('响应格式无效') as ApiError;
      }
      throw error;
    }
  }

  /**
   * 处理HTTP错误
   */
  private async handleHttpError(response: Response): Promise<never> {
    let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
    let errorDetails: any = null;
    let errorCode = `HTTP_${response.status}`;

    try {
      const errorData = await response.json();
      errorMessage = errorData.message || errorMessage;
      errorDetails = errorData.error || errorData;
      if (errorData.error_code) {
        errorCode = errorData.error_code;
      }
    } catch {
      // 如果无法解析错误响应，使用默认错误消息
    }

    const error = new Error(errorMessage) as ApiError;
    error.status = response.status;
    error.data = errorDetails;
    error.code = errorCode;
    throw error;
  }

  /**
   * 处理网络错误
   */
  private handleError(error: any, endpoint: string): ApiError {
    if (error.name === 'AbortError') {
      const apiError = new Error('请求超时') as ApiError;
      apiError.code = 'TIMEOUT';
      throw apiError;
    }

    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      const apiError = new Error('网络连接失败') as ApiError;
      apiError.code = 'NETWORK_ERROR';
      throw apiError;
    }

    // 如果是已经处理过的API错误，直接抛出
    if (error.data !== undefined || error.code !== undefined) {
      return error;
    }

    // 未知错误
    const apiError = new Error(error.message || '请求失败') as ApiError;
    apiError.code = 'UNKNOWN_ERROR';
    throw apiError;
  }

  /**
   * GET请求
   */
  get<T>(endpoint: string, params?: Record<string, any>): Promise<T> {
    const url = this.buildUrl(endpoint, params);
    return this.request<T>(url);
  }

  /**
   * POST请求
   */
  post<T>(endpoint: string, data?: any, params?: Record<string, any>): Promise<T> {
    const url = this.buildUrl(endpoint, params);
    return this.request<T>(url, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  /**
   * PUT请求
   */
  put<T>(endpoint: string, data?: any, params?: Record<string, any>): Promise<T> {
    const url = this.buildUrl(endpoint, params);
    return this.request<T>(url, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  /**
   * DELETE请求
   */
  delete<T>(endpoint: string, params?: Record<string, any>): Promise<T> {
    const url = this.buildUrl(endpoint, params);
    return this.request<T>(url, {
      method: 'DELETE',
    });
  }

  /**
   * PATCH请求
   */
  patch<T>(endpoint: string, data?: any, params?: Record<string, any>): Promise<T> {
    const url = this.buildUrl(endpoint, params);
    return this.request<T>(url, {
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  /**
   * 上传文件
   */
  upload<T>(endpoint: string, file: File, data?: Record<string, any>): Promise<T> {
    const formData = new FormData();
    formData.append('file', file);

    if (data) {
      Object.keys(data).forEach(key => {
        if (data[key] !== undefined) {
          formData.append(key, String(data[key]));
        }
      });
    }

    return this.request<T>(endpoint, {
      method: 'POST',
      body: formData,
      headers: {
        // 不设置Content-Type，让浏览器自动设置boundary
      },
    });
  }

  /**
   * 构建URL
   */
  private buildUrl(endpoint: string, params?: Record<string, any>): string {
    let url = endpoint;

    if (params && Object.keys(params).length > 0) {
      const searchParams = new URLSearchParams();

      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          searchParams.append(key, String(value));
        }
      });

      const queryString = searchParams.toString();
      if (queryString) {
        url += (endpoint.includes('?') ? '&' : '?') + queryString;
      }
    }

    return url;
  }
}

/**
 * 创建默认的HTTP客户端实例
 */
export function createHttpClient(config?: Partial<ApiConfig>): HttpClient {
  // API基础URL配置
  const baseURL =
    import.meta.env.VITE_API_BASE_URL_ALT ||
    import.meta.env.VITE_API_BASE_URL ||
    'http://localhost:5010';

  return new HttpClient({
    baseURL,
    ...config,
  });
}

/**
 * 全局默认HTTP客户端实例
 */
export const httpClient = createHttpClient();

/**
 * 错误处理工具
 */
export class ApiErrorHandler {
  /**
   * 处理API错误
   */
  static handleError(error: unknown, fallbackMessage?: string): string {
    // 将未知错误转换为ApiError格式
    const apiError = this.normalizeError(error);

    if (apiError.data?.message) {
      return apiError.data.message;
    }
    if (error.data?.message) {
      return error.data.message;
    }

    if (apiError.code === 'NETWORK_ERROR') {
      return '网络连接失败，请检查网络连接';
    }

    if (apiError.code === 'TIMEOUT') {
      return '请求超时，请稍后重试';
    }

    if (apiError.status === 401) {
      return '登录已过期，请重新登录';
    }

    if (apiError.status === 403) {
      return '没有权限访问此资源';
    }

    if (apiError.status === 404) {
      return '请求的资源不存在';
    }

    if (apiError.status === 500) {
      return '服务器内部错误，请稍后重试';
    }

    if (apiError.status && apiError.status >= 400) {
      return `请求失败 (${apiError.status})`;
    }

    return apiError.message || fallbackMessage || '请求失败';
  }

  /**
   * 标准化错误对象
   */
  static normalizeError(error: unknown): ApiError {
    if (error && typeof error === 'object') {
      // 如果已经是ApiError格式
      if ('status' in error || 'code' in error) {
        return error as ApiError;
      }

      // 如果是Response对象
      if ('status' in error && 'statusText' in error) {
        const response = error as Response;
        const apiError = new Error(`HTTP ${response.status}: ${response.statusText}`) as ApiError;
        apiError.status = response.status;
        apiError.code = response.status.toString();
        return apiError;
      }
    }

    // 如果是Error实例
    if (error instanceof Error) {
      const apiError = error as ApiError;
      if (!apiError.status) {
        apiError.status = 500;
        apiError.code = 'UNKNOWN_ERROR';
      }
      return apiError;
    }

    // 默认错误
    const apiError = new Error('Unknown error') as ApiError;
    apiError.status = 500;
    apiError.code = 'UNKNOWN_ERROR';
    return apiError;
  }

  /**
   * 检查是否是网络错误
   */
  static isNetworkError(error: ApiError): boolean {
    return error.code === 'NETWORK_ERROR' || error.code === 'TIMEOUT';
  }

  /**
   * 检查是否是认证错误
   */
  static isAuthError(error: ApiError): boolean {
    return error.status === 401 || error.status === 403;
  }

  /**
   * 检查是否是服务器错误
   */
  static isServerError(error: ApiError): boolean {
    return error.status && error.status >= 500;
  }
}