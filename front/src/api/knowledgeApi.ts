import {
  KnowledgeBase,
  KnowledgeBaseListParams,
  KnowledgeBaseListResponse,
  KnowledgeBaseStatistics,
  KnowledgeBaseConversation,
  ConversationListResponse,
  TestConversationRequest,
  GetConversationsRequest,
  RefreshAllRequest,
  RefreshSingleRequest,
  SyncResult,
  RefreshResult,
  KnowledgeBaseActionRequest,
  KnowledgeBaseDetailActionRequest,
  ApiResponse,
  ApiError
} from '../types/knowledge';

// API基础URL配置 - 使用不常用端口（默认 5010）
// 优先读取新的环境变量 VITE_API_BASE_URL_ALT，兼容旧的 VITE_API_BASE_URL
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL_ALT ||
  import.meta.env.VITE_API_BASE_URL ||
  'http://localhost:5010';

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

    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);

      if (!response.ok) {
        // 尝试解析错误响应
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        let errorDetails: any = null;
        try {
          const errorData: ApiError = await response.json();
          errorMessage = errorData.message || errorMessage;
          errorDetails = errorData;
        } catch {
          // 如果无法解析错误响应，使用默认错误消息
        }
        const error = new Error(errorMessage) as any;
        error.response = {
          data: errorDetails,
          status: response.status,
        };
        throw error;
      }

      const data: ApiResponse<T> = await response.json();

      if (!data.success) {
        throw new Error(data.message || '请求失败');
      }

      return data.data;
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('网络请求失败');
    }
  }

  async get<T>(endpoint: string, params?: Record<string, any>): Promise<T> {
    const url = new URL(endpoint, this.baseURL);
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          url.searchParams.append(key, String(value));
        }
      });
    }

    return this.request<T>(url.pathname + url.search);
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

  async delete<T>(endpoint: string, params?: Record<string, any>): Promise<T> {
    const url = new URL(endpoint, this.baseURL);
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          url.searchParams.append(key, String(value));
        }
      });
    }

    return this.request<T>(url.pathname + url.search, {
      method: 'DELETE',
    });
  }
}

const apiClient = new ApiClient(API_BASE_URL);

// 知识库API服务
export const knowledgeApi = {
  /**
   * 获取知识库列表
   */
  async getKnowledgeBases(params?: KnowledgeBaseListParams): Promise<KnowledgeBaseListResponse> {
    const queryParams = {
      search: params?.search,
      status: params?.status,
      page: params?.page || 1,
      page_size: params?.page_size || 20,
      sort_by: params?.sort_by || 'created_at',
      sort_order: params?.sort_order || 'desc',
    };

    return apiClient.get<KnowledgeBaseListResponse>('/api/knowledge-bases', queryParams);
  },

  /**
   * 刷新知识库列表（从RAGFlow同步）
   */
  async refreshKnowledgeBases(): Promise<SyncResult> {
    const request: RefreshAllRequest = {
      action: 'refresh_all'
    };

    return apiClient.post<SyncResult>('/api/knowledge-bases', request);
  },

  /**
   * 获取知识库详情和统计信息
   */
  async getKnowledgeBaseDetails(id: number): Promise<KnowledgeBase & { statistics: KnowledgeBaseStatistics }> {
    return apiClient.get<KnowledgeBase & { statistics: KnowledgeBaseStatistics }>(`/api/knowledge-bases/${id}`);
  },

  /**
   * 刷新单个知识库
   */
  async refreshKnowledgeBase(id: number): Promise<RefreshResult> {
    const request: RefreshSingleRequest = {
      action: 'refresh_single',
      knowledge_base_id: id
    };

    return apiClient.post<RefreshResult>(`/api/knowledge-bases/${id}`, request);
  },

  /**
   * 在知识库中进行测试对话
   */
  async testConversation(id: number, question: string, title?: string): Promise<KnowledgeBaseConversation> {
    const request: TestConversationRequest = {
      action: 'test_conversation',
      question,
      title: title || `测试对话 - ${new Date().toLocaleString('zh-CN')}`
    };

    return apiClient.post<KnowledgeBaseConversation>(`/api/knowledge-bases/${id}`, request);
  },

  /**
   * 获取知识库的对话列表
   */
  async getConversations(
    id: number,
    page: number = 1,
    perPage: number = 20,
    status: 'active' | 'archived' | 'error' | '' = ''
  ): Promise<ConversationListResponse> {
    const request: GetConversationsRequest = {
      action: 'get_conversations',
      page,
      per_page: perPage,
      status
    };

    return apiClient.post<ConversationListResponse>(`/api/knowledge-bases/${id}`, request);
  },

  /**
   * 获取知识库统计信息
   */
  async getKnowledgeBaseStatistics(): Promise<KnowledgeBaseStatistics> {
    return apiClient.get<KnowledgeBaseStatistics>('/api/knowledge-bases/statistics');
  },

  /**
   * 执行知识库相关的操作（通用操作接口）
   */
  async performKnowledgeBaseAction(actionRequest: KnowledgeBaseActionRequest): Promise<SyncResult | RefreshResult[]> {
    return apiClient.post<SyncResult | RefreshResult[]>('/api/knowledge-bases', actionRequest);
  },

  /**
   * 执行知识库详情相关的操作（通用操作接口）
   */
  async performKnowledgeBaseDetailAction(
    id: number,
    actionRequest: KnowledgeBaseDetailActionRequest
  ): Promise<KnowledgeBaseConversation | ConversationListResponse> {
    return apiClient.post<KnowledgeBaseConversation | ConversationListResponse>(
      `/api/knowledge-bases/${id}`,
      actionRequest
    );
  }
};

// 导出API客户端以供其他模块使用
export { apiClient };

// 导出API基础URL以便调试
export { API_BASE_URL };