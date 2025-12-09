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
  ApiError,
  // RAGFlow相关类型
  ChatAssistant,
  Agent,
  ChatInteractionRequest,
  ChatInteractionResponse,
  RetrievalRequest,
  RetrievalResult,
  ChatAssistantListResponse,
  AgentListResponse,
  RetrievalResponse,
  RAGFlowApiResponse
} from '../types/knowledge';

import {
  Document,
  DocumentChunk,
  DocumentFilters,
  ChunkSearchFilters,
  UploadResponse,
  ChunkSearchResult,
  DocumentStatistics,
  DocumentListResponse,
  UploadProgress,
} from '../types/document';

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

  async upload<T>(endpoint: string, formData: FormData, onProgress?: (progress: number) => void): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();

      // Setup progress tracking
      if (onProgress) {
        xhr.upload.addEventListener('progress', (event) => {
          if (event.lengthComputable) {
            const progress = (event.loaded / event.total) * 100;
            onProgress(progress);
          }
        });
      }

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const response = JSON.parse(xhr.responseText);
            resolve(response);
          } catch (error) {
            reject(new Error(`Failed to parse response: ${error}`));
          }
        } else {
          reject(new Error(`Upload failed with status: ${xhr.status}`));
        }
      });

      xhr.addEventListener('error', () => {
        reject(new Error('Upload failed'));
      });

      xhr.open('POST', url);
      xhr.send(formData);
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
  },

  // ========== Document Management Methods ==========

  /**
   * 获取知识库的文档列表
   */
  async getDocuments(
    knowledgeBaseId: string,
    filters?: DocumentFilters
  ): Promise<DocumentListResponse> {
    const queryParams = {
      page: filters?.page || 1,
      limit: filters?.limit || 20,
      search: filters?.search,
      status: filters?.status,
      file_type: filters?.file_type,
      sort_by: filters?.sort_by || 'created_at',
      sort_order: filters?.sort_order || 'desc',
    };

    return apiClient.get<DocumentListResponse>(`/api/knowledge-bases/${knowledgeBaseId}/documents`, queryParams);
  },

  /**
   * 上传文档到知识库
   */
  async uploadDocument(
    knowledgeBaseId: string,
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    // Add optional upload_id for progress tracking
    const uploadId = `upload_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    formData.append('upload_id', uploadId);

    try {
      const response = await apiClient.upload<UploadResponse>(
        `/api/knowledge-bases/${knowledgeBaseId}/documents/upload`,
        formData,
        onProgress
      );

      return response;
    } catch (error) {
      console.error('Document upload failed:', error);
      throw error;
    }
  },

  /**
   * 获取文档详情
   */
  async getDocument(knowledgeBaseId: string, documentId: string): Promise<Document> {
    const response = await apiClient.get<{ success: boolean; data: Document }>(
      `/api/knowledge-bases/${knowledgeBaseId}/ragflow-documents/${documentId}`
    );

    if (response.success && response.data) {
      return response.data;
    } else {
      throw new Error('Failed to get document details');
    }
  },

  /**
   * 删除文档
   */
  async deleteDocument(knowledgeBaseId: string, documentId: string): Promise<void> {
    console.log('🗑️ [DEBUG] Deleting document:', { knowledgeBaseId, documentId });

    // Use direct fetch for delete operation since API format is inconsistent
    const url = `${API_BASE_URL}/api/knowledge-bases/${knowledgeBaseId}/ragflow-documents/${documentId}`;

    try {
      const response = await fetch(url, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      console.log('📦 [DEBUG] Delete raw response status:', response.status);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      console.log('📦 [DEBUG] Delete response received:', result);

      if (result.success === true) {
        console.log('✅ [DEBUG] Document deleted successfully');
        return;
      } else {
        const errorMsg = result.message || 'Failed to delete document';
        console.error('❌ [DEBUG] Delete failed:', { result, errorMsg });
        throw new Error(errorMsg);
      }
    } catch (error) {
      console.error('💥 [DEBUG] Delete request failed:', error);
      throw error;
    }
  },

  /**
   * 搜索文档块
   */
  async searchChunks(
    knowledgeBaseId: string,
    query: string,
    filters?: ChunkSearchFilters
  ): Promise<ChunkSearchResult> {
    const requestData = {
      query,
      document_id: filters?.document_id,
      min_relevance_score: filters?.min_relevance_score,
      max_results: filters?.max_results || 10,
    };

    const response = await apiClient.post<{ success: boolean; data: ChunkSearchResult }>(
      `/api/knowledge-bases/${knowledgeBaseId}/chunks/search`,
      requestData
    );

    if (response.success && response.data) {
      return response.data;
    } else {
      throw new Error('Failed to search chunks');
    }
  },

  /**
   * 获取文档的所有块
   */
  async getDocumentChunks(
    knowledgeBaseId: string,
    documentId: string,
    filters?: {
      chunk_index_min?: number;
      chunk_index_max?: number;
      sort_by?: string;
      sort_order?: string;
    }
  ): Promise<{
    document_id: string;
    document_name: string;
    chunks: DocumentChunk[];
    total_chunks: number;
  }> {
    console.log('🔍 [DEBUG] getDocumentChunks called with:', { knowledgeBaseId, documentId, filters });

    const queryParams: Record<string, any> = {};
    if (filters?.chunk_index_min !== undefined) queryParams.chunk_index_min = filters.chunk_index_min;
    if (filters?.chunk_index_max !== undefined) queryParams.chunk_index_max = filters.chunk_index_max;
    if (filters?.sort_by) queryParams.sort_by = filters.sort_by;
    if (filters?.sort_order) queryParams.sort_order = filters.sort_order;

    const apiUrl = `/api/knowledge-bases/${knowledgeBaseId}/ragflow-documents/${documentId}/chunks`;
    console.log('🌐 [DEBUG] Making API request to:', apiUrl, 'with params:', queryParams);

    try {
      const response = await apiClient.get<{
        success: boolean;
        data?: {
          document_id: string;
          document_name: string;
          chunks: DocumentChunk[];
          total_chunks: number;
        };
        error_code?: string;
        message?: string;
      }>(apiUrl, queryParams);

      console.log('📦 [DEBUG] API response received:', response);

      // Check if response has the expected structure for document chunks
      if (response && response.document_id && Array.isArray(response.chunks)) {
        console.log('✅ [DEBUG] Successfully retrieved chunks:', {
          documentId: response.document_id,
          documentName: response.document_name,
          chunkCount: response.total_chunks,
          chunks: response.chunks?.length
        });
        return response;
      } else {
        const errorMsg = 'Invalid response structure';
        console.error('❌ [DEBUG] API returned error:', { response, errorMsg });
        throw new Error(`Failed to get document chunks: ${errorMsg}`);
      }
    } catch (error) {
      console.error('💥 [DEBUG] API request failed:', error);
      throw error;
    }
  },

  /**
   * 获取文档统计信息
   */
  async getDocumentStatistics(knowledgeBaseId: string): Promise<DocumentStatistics> {
    // First try to get from knowledge base details
    const response = await apiClient.get<{
      success: boolean;
      data: {
        document_statistics?: DocumentStatistics;
      };
    }>(`/api/knowledge-bases/${knowledgeBaseId}`);

    if (response.success && response.data?.document_statistics) {
      return response.data.document_statistics;
    } else {
      // Fallback - return basic statistics
      const documentsResponse = await this.getDocuments(knowledgeBaseId, { limit: 1 });
      const documents = documentsResponse.documents || [];

      const stats: DocumentStatistics = {
        total_documents: documentsResponse.pagination?.total || 0,
        total_file_size_bytes: documents.reduce((sum, doc) => sum + doc.file_size, 0),
        total_file_size_mb: documents.reduce((sum, doc) => sum + (doc.file_size / (1024 * 1024)), 0),
        total_chunks: documents.reduce((sum, doc) => sum + doc.chunk_count, 0),
        status_breakdown: {},
        file_type_breakdown: {},
        updated_at: new Date().toISOString(),
      };

      return stats;
    }
  },

  /**
   * 获取上传进度
   */
  async getUploadProgress(knowledgeBaseId: string, uploadId: string): Promise<UploadProgress | null> {
    const response = await apiClient.get<{
      success: boolean;
      data?: UploadProgress;
    }>(`/api/knowledge-bases/${knowledgeBaseId}/documents/upload?upload_id=${uploadId}`);

    return response.success && response.data ? response.data : null;
  },

  /**
   * 取消上传
   */
  async cancelUpload(knowledgeBaseId: string, uploadId: string): Promise<void> {
    // This would need to be implemented in the backend
    console.log('Cancel upload not yet implemented:', { knowledgeBaseId, uploadId });
    // For now, we'll just log it
  },

  // ===== RAGFlow 聊天助手和智能体相关方法 =====

  /**
   * 获取RAGFlow聊天助手列表
   */
  async getChatAssistants(): Promise<ChatAssistantListResponse> {
    return apiClient.get<ChatAssistantListResponse>('/api/ragflow/chats');
  },

  /**
   * 与RAGFlow聊天助手对话
   */
  async chatWithAssistant(chatId: string, message: string, stream: boolean = false): Promise<ChatInteractionResponse> {
    return apiClient.post<ChatInteractionResponse>(`/api/ragflow/chats/${chatId}`, {
      message,
      stream
    });
  },

  /**
   * 获取RAGFlow智能体列表
   */
  async getAgents(): Promise<AgentListResponse> {
    return apiClient.get<AgentListResponse>('/api/ragflow/agents');
  },

  /**
   * 与RAGFlow智能体对话
   */
  async chatWithAgent(agentId: string, message: string, stream: boolean = false): Promise<ChatInteractionResponse> {
    return apiClient.post<ChatInteractionResponse>(`/api/ragflow/agents/${agentId}`, {
      message,
      stream
    });
  },

  /**
   * 执行RAGFlow检索
   */
  async performRetrieval(query: string, datasetIds: string[], topK: number = 10): Promise<RetrievalResponse> {
    return apiClient.post<RetrievalResponse>('/api/ragflow/retrieval', {
      query,
      dataset_ids: datasetIds,
      top_k: topK
    });
  }
};

// 导出API客户端以供其他模块使用
export { apiClient };

// 导出API基础URL以便调试
export { API_BASE_URL };

// ===== RAGFlow 专用API客户端 =====

/**
 * RAGFlow API 客户端
 * 专门用于与RAGFlow聊天助手、智能体和检索功能交互
 */
export const ragflowApi = {
  /**
   * 获取RAGFlow聊天助手列表
   */
  async getChatAssistants(): Promise<ChatAssistantListResponse> {
    return apiClient.get<ChatAssistantListResponse>('/api/ragflow/chats');
  },

  /**
   * 与RAGFlow聊天助手对话
   */
  async chatWithAssistant(chatId: string, message: string, stream: boolean = false): Promise<ChatInteractionResponse> {
    return apiClient.post<ChatInteractionResponse>(`/api/ragflow/chats/${chatId}`, {
      message,
      stream
    });
  },

  /**
   * 获取RAGFlow智能体列表
   */
  async getAgents(): Promise<AgentListResponse> {
    return apiClient.get<AgentListResponse>('/api/ragflow/agents');
  },

  /**
   * 与RAGFlow智能体对话
   */
  async chatWithAgent(agentId: string, message: string, stream: boolean = false): Promise<ChatInteractionResponse> {
    return apiClient.post<ChatInteractionResponse>(`/api/ragflow/agents/${agentId}`, {
      message,
      stream
    });
  },

  /**
   * 执行RAGFlow检索
   */
  async performRetrieval(query: string, datasetIds: string[], topK: number = 10, retrievalModel: string = "Vector"): Promise<RetrievalResponse> {
    return apiClient.post<RetrievalResponse>('/api/ragflow/retrieval', {
      query,
      dataset_ids: datasetIds,
      top_k: topK,
      retrieval_model: retrievalModel
    });
  },

  /**
   * 获取聊天助手详情
   */
  async getChatAssistantDetails(chatId: string): Promise<ChatAssistant | null> {
    try {
      const assistants = await this.getChatAssistants();
      if (assistants.success) {
        return assistants.data.find(assistant => assistant.id === chatId) || null;
      }
      return null;
    } catch (error) {
      console.error('Failed to get chat assistant details:', error);
      return null;
    }
  },

  /**
   * 获取智能体详情
   */
  async getAgentDetails(agentId: string): Promise<Agent | null> {
    try {
      const agents = await this.getAgents();
      if (agents.success) {
        return agents.data.find(agent => agent.id === agentId) || null;
      }
      return null;
    } catch (error) {
      console.error('Failed to get agent details:', error);
      return null;
    }
  }
};