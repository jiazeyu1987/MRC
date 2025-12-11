// 对话历史API服务

import {
  ApiResponse,
  ConversationHistory,
  ConversationTemplate,
  CreateConversationRequest,
  UpdateConversationRequest,
  ConversationListParams,
  ConversationListResponse,
  ExportFormat,
  TemplateParameter
} from '../types/enhanced';

import {
  KnowledgeBase
} from '../types/knowledge';

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

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'DELETE',
    });
  }
}

const apiClient = new ApiClient(API_BASE_URL);

// 对话历史API服务
export class ConversationApiService {
  /**
   * 获取知识库的对话历史
   */
  async getConversations(
    knowledgeBaseId: number,
    params: ConversationListParams = {}
  ): Promise<ConversationListResponse> {
    const queryParams = new URLSearchParams();

    if (params.page) queryParams.append('page', params.page.toString());
    if (params.per_page) queryParams.append('per_page', params.per_page.toString());
    if (params.search) queryParams.append('search', params.search);
    if (params.tags) params.tags.forEach(tag => queryParams.append('tags', tag));
    if (params.user_id) queryParams.append('user_id', params.user_id);
    if (params.is_archived !== undefined) queryParams.append('is_archived', params.is_archived.toString());
    if (params.sort_by) queryParams.append('sort_by', params.sort_by);
    if (params.sort_order) queryParams.append('sort_order', params.sort_order);

    const endpoint = `/knowledge-bases/${knowledgeBaseId}/conversations${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    const response = await apiClient.get<ApiResponse<ConversationListResponse>>(endpoint);
    return response.data;
  }

  /**
   * 创建新对话
   */
  async createConversation(
    knowledgeBaseId: number,
    request: CreateConversationRequest
  ): Promise<ConversationHistory> {
    const endpoint = `/knowledge-bases/${knowledgeBaseId}/conversations`;
    const response = await apiClient.post<ApiResponse<ConversationHistory>>(endpoint, request);
    return response.data;
  }

  /**
   * 获取对话详情
   */
  async getConversation(
    knowledgeBaseId: number,
    conversationId: number
  ): Promise<ConversationHistory> {
    const endpoint = `/knowledge-bases/${knowledgeBaseId}/conversations/${conversationId}`;
    const response = await apiClient.get<ApiResponse<ConversationHistory>>(endpoint);
    return response.data;
  }

  /**
   * 更新对话
   */
  async updateConversation(
    knowledgeBaseId: number,
    conversationId: number,
    request: UpdateConversationRequest
  ): Promise<ConversationHistory> {
    const endpoint = `/knowledge-bases/${knowledgeBaseId}/conversations/${conversationId}`;
    const response = await apiClient.put<ApiResponse<ConversationHistory>>(endpoint, request);
    return response.data;
  }

  /**
   * 删除对话
   */
  async deleteConversation(
    knowledgeBaseId: number,
    conversationId: number
  ): Promise<{ success: boolean; message: string }> {
    const endpoint = `/knowledge-bases/${knowledgeBaseId}/conversations/${conversationId}`;
    const response = await apiClient.delete<ApiResponse<{ success: boolean; message: string }>>(endpoint);
    return { success: response.data.success, message: response.data.message || '' };
  }

  /**
   * 导出对话
   */
  async exportConversation(
    knowledgeBaseId: number,
    conversationId: number,
    format: ExportFormat = 'json'
  ): Promise<string> {
    const endpoint = `/knowledge-bases/${knowledgeBaseId}/conversations/${conversationId}/export?format=${format}`;

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
   * 归档/取消归档对话
   */
  async archiveConversation(
    knowledgeBaseId: number,
    conversationId: number,
    archive: boolean = true
  ): Promise<ConversationHistory> {
    const endpoint = `/knowledge-bases/${knowledgeBaseId}/conversations/${conversationId}`;
    const response = await apiClient.put<ApiResponse<ConversationHistory>>(endpoint, {
      is_archived: archive
    });
    return response.data;
  }

  /**
   * 批量操作对话
   */
  async bulkUpdateConversations(
    knowledgeBaseId: number,
    conversationIds: number[],
    updates: Partial<UpdateConversationRequest>
  ): Promise<{ success: number; failed: number; errors: string[] }> {
    const endpoint = `/knowledge-bases/${knowledgeBaseId}/conversations/bulk`;
    const response = await apiClient.post<ApiResponse<{ success: number; failed: number; errors: string[] }>>(endpoint, {
      conversation_ids: conversationIds,
      updates
    });
    return response.data;
  }
}

// 对话模板API服务
export class ConversationTemplateApiService {
  /**
   * 获取对话模板列表
   */
  async getTemplates(
    category?: string,
    isSystem?: boolean
  ): Promise<ConversationTemplate[]> {
    const queryParams = new URLSearchParams();
    if (category) queryParams.append('category', category);
    if (isSystem !== undefined) queryParams.append('is_system', isSystem.toString());

    const endpoint = `/conversation-templates${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    const response = await apiClient.get<ApiResponse<ConversationTemplate[]>>(endpoint);
    return response.data;
  }

  /**
   * 获取单个对话模板
   */
  async getTemplate(templateId: number): Promise<ConversationTemplate> {
    const endpoint = `/conversation-templates/${templateId}`;
    const response = await apiClient.get<ApiResponse<ConversationTemplate>>(endpoint);
    return response.data;
  }

  /**
   * 创建对话模板
   */
  async createTemplate(template: {
    name: string;
    description?: string;
    category: string;
    prompt: string;
    parameters?: TemplateParameter[];
    is_system?: boolean;
  }): Promise<ConversationTemplate> {
    const endpoint = `/conversation-templates`;
    const response = await apiClient.post<ApiResponse<ConversationTemplate>>(endpoint, template);
    return response.data;
  }

  /**
   * 更新对话模板
   */
  async updateTemplate(
    templateId: number,
    updates: Partial<ConversationTemplate>
  ): Promise<ConversationTemplate> {
    const endpoint = `/conversation-templates/${templateId}`;
    const response = await apiClient.put<ApiResponse<ConversationTemplate>>(endpoint, updates);
    return response.data;
  }

  /**
   * 删除对话模板
   */
  async deleteTemplate(templateId: number): Promise<{ success: boolean; message: string }> {
    const endpoint = `/conversation-templates/${templateId}`;
    const response = await apiClient.delete<ApiResponse<{ success: boolean; message: string }>>(endpoint);
    return { success: response.data.success, message: response.data.message || '' };
  }

  /**
   * 应用对话模板创建对话
   */
  async applyTemplate(
    templateId: number,
    knowledgeBaseId: number,
    parameters: Record<string, any> = {},
    userId?: string
  ): Promise<ConversationHistory> {
    const endpoint = `/knowledge-bases/${knowledgeBaseId}/conversations`;
    const response = await apiClient.post<ApiResponse<ConversationHistory>>(endpoint, {
      template_id: templateId,
      parameters,
      user_id: userId
    });
    return response.data;
  }

  /**
   * 获取模板分类列表
   */
  async getTemplateCategories(): Promise<string[]> {
    const endpoint = `/conversation-templates/categories`;
    const response = await apiClient.get<ApiResponse<string[]>>(endpoint);
    return response.data;
  }
}

// 导出服务实例
export const conversationApi = new ConversationApiService();
export const conversationTemplateApi = new ConversationTemplateApiService();

// 导出类型供外部使用
export type {
  ConversationHistory,
  ConversationTemplate,
  CreateConversationRequest,
  UpdateConversationRequest,
  ConversationListParams,
  ConversationListResponse,
  ExportFormat,
  TemplateParameter
};