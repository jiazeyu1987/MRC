// RAGFlow 对话 API 客户端

import { httpClient } from './index';

// RAGFlow 对话相关类型定义
export interface ChatAssistant {
  id: string;
  name: string;
  avatar: string;
  description: string;
  prompt_config: {
    prompt_name: string;
    prompt_text: string;
    quote: boolean;
    t: number;
  };
  dataset_ids: string[];
  create_time: number;
  update_time: number;
}

export interface ChatSession {
  id: string;
  name: string;
  chat_id: string;
  create_time: number;
  update_time: number;
  message_count: number;
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  reference?: {
    documents: Array<{
      doc_name: string;
      page_content: string;
      similarity: number;
      doc_id: string;
    }>;
  };
}

export interface ChatCompletionRequest {
  model?: string;
  messages: ChatMessage[];
  stream?: boolean;
  session_id?: string;
}

export interface ChatCompletionResponse {
  answer: string;
  reference?: {
    documents: Array<{
      doc_name: string;
      page_content: string;
      similarity: number;
      doc_id: string;
    }>;
  };
  metadata?: any;
}

export interface RetrievalRequest {
  question: string;
  dataset_ids?: string[];
  document_ids?: string[];
  top_k?: number;
  similarity_threshold?: number;
}

export interface RetrievalResponse {
  data: Array<{
    chunk_id: string;
    content_with_weight: string;
    similarity: number;
    doc_id: string;
    doc_name: string;
    img_id?: string;
    positions: number[][];
  }>;
}

// RAGFlow 对话 API 服务
export class RAGFlowChatApiService {
  private baseEndpoint: string;

  constructor() {
    this.baseEndpoint = '/api/v1';
  }

  // Chat Assistant 管理
  async listChatAssistants(): Promise<ChatAssistant[]> {
    return httpClient.get(`${this.baseEndpoint}/chats`);
  }

  async createChatAssistant(assistant: Partial<ChatAssistant>): Promise<ChatAssistant> {
    return httpClient.post(`${this.baseEndpoint}/chats`, assistant);
  }

  async updateChatAssistant(chatId: string, assistant: Partial<ChatAssistant>): Promise<ChatAssistant> {
    return httpClient.put(`${this.baseEndpoint}/chats/${chatId}`, assistant);
  }

  async deleteChatAssistant(chatIds: string[]): Promise<void> {
    return httpClient.delete(`${this.baseEndpoint}/chats`, { chat_ids: chatIds });
  }

  // Session 管理
  async listChatSessions(chatId: string): Promise<ChatSession[]> {
    return httpClient.get(`${this.baseEndpoint}/chats/${chatId}/sessions`);
  }

  async createChatSession(chatId: string, sessionName: string): Promise<ChatSession> {
    return httpClient.post(`${this.baseEndpoint}/chats/${chatId}/sessions`, {
      name: sessionName
    });
  }

  async updateChatSession(chatId: string, sessionId: string, session: Partial<ChatSession>): Promise<ChatSession> {
    return httpClient.put(`${this.baseEndpoint}/chats/${chatId}/sessions/${sessionId}`, session);
  }

  async deleteChatSessions(chatId: string, sessionIds: string[]): Promise<void> {
    return httpClient.delete(`${this.baseEndpoint}/chats/${chatId}/sessions`, {
      session_ids: sessionIds
    });
  }

  // 对话完成
  async chatCompletion(chatId: string, request: ChatCompletionRequest): Promise<ChatCompletionResponse> {
    return httpClient.post(`${this.baseEndpoint}/chats/${chatId}/completions`, request);
  }

  // OpenAI 兼容格式
  async chatCompletionOpenAI(chatId: string, request: ChatCompletionRequest): Promise<ChatCompletionResponse> {
    return httpClient.post(`${this.baseEndpoint}/chats_openai/${chatId}/chat/completions`, request);
  }

  // 智能体对话
  async agentCompletion(agentId: string, request: ChatCompletionRequest): Promise<ChatCompletionResponse> {
    return httpClient.post(`${this.baseEndpoint}/agents_openai/${agentId}/chat/completions`, request);
  }

  // 检索/搜索
  async retrieval(request: RetrievalRequest): Promise<RetrievalResponse> {
    return httpClient.post(`${this.baseEndpoint}/retrieval`, request);
  }

  // 获取对话统计信息
  async getChatStatistics(chatId?: string): Promise<{
    total_chats: number;
    total_sessions: number;
    total_messages: number;
    active_sessions: number;
  }> {
    const endpoint = chatId
      ? `${this.baseEndpoint}/chats/${chatId}/statistics`
      : `${this.baseEndpoint}/chats/statistics`;

    return httpClient.get(endpoint);
  }

  // 导出对话记录
  async exportChatHistory(chatId: string, sessionIds?: string[]): Promise<string> {
    const endpoint = `${this.baseEndpoint}/chats/${chatId}/export`;
    const response = await httpClient.post(endpoint, {
      session_ids: sessionIds
    });
    return response.export_url;
  }
}

// 创建服务实例
export const ragflowChatApi = new RAGFlowChatApiService();