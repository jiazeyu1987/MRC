// 知识库相关的TypeScript类型定义

// 后端API响应的基础类型
export interface ApiResponse<T = any> {
  success: boolean;
  data: T;
  message?: string;
  error_code?: string;
}

// API错误类型
export interface ApiError {
  response?: {
    data?: {
      message?: string;
      error_code?: string;
      details?: any;
    };
    status?: number;
  };
  message?: string;
  code?: string;
}

export interface KnowledgeBase {
  id: number;
  ragflow_dataset_id: string;
  name: string;
  description?: string;
  document_count: number;
  total_size: number; // 文件总大小（字节）
  status: 'active' | 'inactive' | 'error';
  created_at: string;
  updated_at?: string;
  // 额外的前端字段
  linked_roles?: Array<{
    id: number;
    name: string;
    prompt: string;
  }>;
  recent_conversations?: KnowledgeBaseConversation[];
  conversation_count?: number;
}

export interface Reference {
  document_id: string;
  document_title: string;
  snippet: string;
  page_number?: number;
  confidence?: number;
}

export interface KnowledgeBaseConversation {
  id: number;
  knowledge_base_id: number;
  knowledge_base_name?: string;
  title: string;
  user_question: string;
  ragflow_response?: string;
  confidence_score?: number; // 0-1
  references?: {
    references: Reference[];
  };
  metadata?: Record<string, any>;
  status: 'active' | 'archived' | 'error';
  reference_count: number;
  is_high_confidence: boolean;
  created_at: string;
  updated_at?: string;
}

export interface TestConversationRequest {
  action: 'test_conversation';
  question: string;
  title?: string;
}

export interface RetrievalConfig {
  top_k?: number; // 检索文档数量
  similarity_threshold?: number; // 相似度阈值
  include_metadata?: boolean; // 是否包含元数据
  max_context_length?: number; // 最大上下文长度
}

export interface GetConversationsRequest {
  action: 'get_conversations';
  page?: number;
  per_page?: number;
  status?: 'active' | 'archived' | 'error' | '';
}

export interface RefreshAllRequest {
  action: 'refresh_all';
}

export interface RefreshSingleRequest {
  action: 'refresh_single';
  knowledge_base_id: number;
}

// 知识库列表查询参数
export interface KnowledgeBaseListParams {
  search?: string;
  status?: 'active' | 'inactive' | 'error' | '';
  page?: number;
  page_size?: number;
  sort_by?: 'created_at' | 'updated_at' | 'name' | 'document_count' | 'total_size';
  sort_order?: 'asc' | 'desc';
}

// 知识库列表响应数据类型
export interface KnowledgeBaseListResponse {
  knowledge_bases: KnowledgeBase[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
  has_prev: boolean;
  has_next: boolean;
}

// 测试对话列表响应数据类型
export interface ConversationListResponse {
  conversations: KnowledgeBaseConversation[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

// 知识库统计信息类型
export interface KnowledgeBaseStatistics {
  total_count: number;
  active_count: number;
  inactive_count: number;
  error_count: number;
  total_documents: number;
  total_size: number;
  recent_activity?: Array<{
    date: string;
    conversations_count: number;
  }>;
  size_distribution?: Array<{
    size_range: string;
    count: number;
  }>;
}

// 同步结果类型
export interface SyncResult {
  created: number;
  updated: number;
  deleted: number;
  errors: string[];
  details?: Array<{
    ragflow_dataset_id: string;
    name: string;
    action: 'created' | 'updated' | 'error';
    error?: string;
  }>;
}

// 刷新结果类型
export interface RefreshResult {
  action: 'updated' | 'created' | 'error';
  old_info?: {
    ragflow_dataset_id: string;
    name: string;
    document_count: number;
    total_size: number;
    status: string;
  };
  new_info: {
    ragflow_dataset_id: string;
    name: string;
    document_count: number;
    total_size: number;
    status: string;
  };
  error?: string;
}

// 联合请求类型（用于知识库列表POST操作）
export type KnowledgeBaseActionRequest = RefreshAllRequest | RefreshSingleRequest;

// 知识库详情操作请求类型（用于知识库详情POST操作）
export type KnowledgeBaseDetailActionRequest = TestConversationRequest | GetConversationsRequest;

// 导入增强功能类型
export * from './enhanced';

// 扩展知识库类型以支持增强功能
export interface ExtendedKnowledgeBase extends KnowledgeBase {
  conversation_count: number;
  search_count: number;
  last_activity?: string;
  settings: Record<string, any>;
  engagement_score?: number;
  recent_activity?: {
    conversations_last_7_days: number;
    searches_last_7_days: number;
    unique_users_last_7_days: number;
  };
}

// ===== RAGFlow 聊天助手和智能体类型定义 =====

export interface ChatAssistant {
  id: string;
  name: string;
  description?: string;
  avatar?: string;
  created_at?: string;
  updated_at?: string;
  status?: string;
  datasets?: string[];
  language?: string;
  system_prompt?: string;
  knowledge_graph?: boolean;
}

export interface Agent {
  id: string;
  name: string;
  title?: string;
  description?: string;
  avatar?: string;
  created_at?: string;
  updated_at?: string;
  status?: string;
  datasets?: string[];
  language?: string;
  knowledge_graph?: boolean;
  llm_id?: string;
  prompt_config?: Record<string, any>;
}

export interface ChatInteractionRequest {
  message: string;
  chat_id?: string;
  agent_id?: string;
  stream?: boolean;
  conversation_id?: string;
  session_id?: string;
}

export interface ChatInteractionResponse {
  success: boolean;
  data: {
    response: string;
    references?: Array<{
      document_id: string;
      document_name: string;
      content: string;
      score?: number;
    }>;
    usage?: {
      prompt_tokens?: number;
      completion_tokens?: number;
      total_tokens?: number;
    };
    model?: string;
    timestamp?: string;
    conversation_id?: string;
    message_id?: string;
  };
  message?: string;
}

export interface RetrievalRequest {
  query: string;
  dataset_ids: string[];
  top_k?: number;
  retrieval_model?: string;
  similarity_threshold?: number;
}

export interface RetrievalResult {
  data: {
    chunks: Array<{
      id: string;
      content: string;
      document_id: string;
      document_name: string;
      score: number;
      position: number;
      similarity?: number;
    }>;
    total: number;
    query: string;
    retrieval_model: string;
    top_k: number;
    time_used: number;
  };
  success: boolean;
  message?: string;
}

// RAGFlow API 响应类型
export interface RAGFlowApiResponse<T> {
  success: boolean;
  data: T;
  count?: number;
  total?: number;
  message?: string;
  error_code?: string;
}

// 聊天助手列表响应
export interface ChatAssistantListResponse extends RAGFlowApiResponse<ChatAssistant[]> {
}

// 智能体列表响应
export interface AgentListResponse extends RAGFlowApiResponse<Agent[]> {
}

// 检索响应
export interface RetrievalResponse extends RAGFlowApiResponse<RetrievalResult['data']> {
}