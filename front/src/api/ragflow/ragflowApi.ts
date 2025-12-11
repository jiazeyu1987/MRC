/**
 * RAGFlow集成API客户端
 *
 * 提供与RAGFlow系统的集成操作
 */

import { httpClient, ApiErrorHandler } from '../shared/http-client';
import type {
  ChatAssistant,
  Agent,
  ChatInteractionRequest,
  ChatInteractionResponse,
  RetrievalRequest,
  RetrievalResult,
} from '../types/knowledge.types';

/**
 * RAGFlow API类
 */
export class RagflowApi {
  private readonly basePath = '/api/ragflow';

  /**
   * 获取聊天助手列表
   */
  async getChatAssistants(): Promise<ChatAssistant[]> {
    try {
      const response = await httpClient.get<{ assistants: ChatAssistant[] }>(
        `${this.basePath}/assistants`
      );
      return response.assistants;
    } catch (error) {
      console.error('Failed to fetch chat assistants:', error);
      throw new Error(ApiErrorHandler.handleError(error, '获取聊天助手失败'));
    }
  }

  /**
   * 获取聊天助手详情
   */
  async getChatAssistant(id: string): Promise<ChatAssistant> {
    try {
      return await httpClient.get<ChatAssistant>(
        `${this.basePath}/assistants/${id}`
      );
    } catch (error) {
      console.error(`Failed to fetch chat assistant ${id}:`, error);
      throw new Error(ApiErrorHandler.handleError(error, '获取聊天助手详情失败'));
    }
  }

  /**
   * 创建聊天助手
   */
  async createChatAssistant(data: {
    name: string;
    description: string;
    avatar?: string;
    datasetIds: string[];
    prompt?: string;
  }): Promise<ChatAssistant> {
    try {
      return await httpClient.post<ChatAssistant>(
        `${this.basePath}/assistants`,
        data
      );
    } catch (error) {
      console.error('Failed to create chat assistant:', error);
      throw new Error(ApiErrorHandler.handleError(error, '创建聊天助手失败'));
    }
  }

  /**
   * 更新聊天助手
   */
  async updateChatAssistant(
    id: string,
    data: {
      name?: string;
      description?: string;
      avatar?: string;
      datasetIds?: string[];
      prompt?: string;
      status?: 'active' | 'inactive';
    }
  ): Promise<ChatAssistant> {
    try {
      return await httpClient.put<ChatAssistant>(
        `${this.basePath}/assistants/${id}`,
        data
      );
    } catch (error) {
      console.error(`Failed to update chat assistant ${id}:`, error);
      throw new Error(ApiErrorHandler.handleError(error, '更新聊天助手失败'));
    }
  }

  /**
   * 删除聊天助手
   */
  async deleteChatAssistant(id: string): Promise<void> {
    try {
      await httpClient.delete(`${this.basePath}/assistants/${id}`);
    } catch (error) {
      console.error(`Failed to delete chat assistant ${id}:`, error);
      throw new Error(ApiErrorHandler.handleError(error, '删除聊天助手失败'));
    }
  }

  /**
   * 获取Agent列表
   */
  async getAgents(): Promise<Agent[]> {
    try {
      const response = await httpClient.get<{ agents: Agent[] }>(
        `${this.basePath}/agents`
      );
      return response.agents;
    } catch (error) {
      console.error('Failed to fetch agents:', error);
      throw new Error(ApiErrorHandler.handleError(error, '获取Agent失败'));
    }
  }

  /**
   * 获取Agent详情
   */
  async getAgent(id: string): Promise<Agent> {
    try {
      return await httpClient.get<Agent>(`${this.basePath}/agents/${id}`);
    } catch (error) {
      console.error(`Failed to fetch agent ${id}:`, error);
      throw new Error(ApiErrorHandler.handleError(error, '获取Agent详情失败'));
    }
  }

  /**
   * 创建Agent
   */
  async createAgent(data: {
    name: string;
    description: string;
    prompt: string;
    datasetIds: string[];
  }): Promise<Agent> {
    try {
      return await httpClient.post<Agent>(`${this.basePath}/agents`, data);
    } catch (error) {
      console.error('Failed to create agent:', error);
      throw new Error(ApiErrorHandler.handleError(error, '创建Agent失败'));
    }
  }

  /**
   * 更新Agent
   */
  async updateAgent(
    id: string,
    data: {
      name?: string;
      description?: string;
      prompt?: string;
      datasetIds?: string[];
      status?: 'active' | 'inactive';
    }
  ): Promise<Agent> {
    try {
      return await httpClient.put<Agent>(`${this.basePath}/agents/${id}`, data);
    } catch (error) {
      console.error(`Failed to update agent ${id}:`, error);
      throw new Error(ApiErrorHandler.handleError(error, '更新Agent失败'));
    }
  }

  /**
   * 删除Agent
   */
  async deleteAgent(id: string): Promise<void> {
    try {
      await httpClient.delete(`${this.basePath}/agents/${id}`);
    } catch (error) {
      console.error(`Failed to delete agent ${id}:`, error);
      throw new Error(ApiErrorHandler.handleError(error, '删除Agent失败'));
    }
  }

  /**
   * 聊天交互
   */
  async chatInteraction(request: ChatInteractionRequest): Promise<ChatInteractionResponse> {
    try {
      return await httpClient.post<ChatInteractionResponse>(
        `${this.basePath}/chat`,
        request
      );
    } catch (error) {
      console.error('Failed to send chat interaction:', error);
      throw new Error(ApiErrorHandler.handleError(error, '聊天交互失败'));
    }
  }

  /**
   * 检索文档内容
   */
  async retrieveDocuments(request: RetrievalRequest): Promise<RetrievalResult> {
    try {
      return await httpClient.post<RetrievalResult>(
        `${this.basePath}/retrieve`,
        request
      );
    } catch (error) {
      console.error('Failed to retrieve documents:', error);
      throw new Error(ApiErrorHandler.handleError(error, '文档检索失败'));
    }
  }

  /**
   * 获取数据集列表
   */
  async getDatasets(): Promise<Array<{
    id: string;
    name: string;
    description: string;
    documentCount: number;
    chunkCount: number;
    createdAt: string;
    updatedAt: string;
  }>> {
    try {
      const response = await httpClient.get<{ datasets: any[] }>(
        `${this.basePath}/datasets`
      );
      return response.datasets;
    } catch (error) {
      console.error('Failed to fetch datasets:', error);
      throw new Error(ApiErrorHandler.handleError(error, '获取数据集失败'));
    }
  }

  /**
   * 获取数据集详情
   */
  async getDataset(id: string): Promise<{
    id: string;
    name: string;
    description: string;
    documentCount: number;
    chunkCount: number;
    metadata?: Record<string, any>;
    createdAt: string;
    updatedAt: string;
  }> {
    try {
      return await httpClient.get<any>(`${this.basePath}/datasets/${id}`);
    } catch (error) {
      console.error(`Failed to fetch dataset ${id}:`, error);
      throw new Error(ApiErrorHandler.handleError(error, '获取数据集详情失败'));
    }
  }

  /**
   * 测试RAGFlow连接
   */
  async testConnection(): Promise<{
    success: boolean;
    message: string;
    responseTime?: number;
    version?: string;
  }> {
    try {
      return await httpClient.get<any>(`${this.basePath}/test-connection`);
    } catch (error) {
      console.error('Failed to test RAGFlow connection:', error);
      return {
        success: false,
        message: ApiErrorHandler.handleError(error, 'RAGFlow连接测试失败'),
      };
    }
  }

  /**
   * 同步数据集
   */
  async syncDatasets(datasetIds?: string[]): Promise<{
    success: boolean;
    synced: number;
    failed: number;
    errors: string[];
    duration: number;
  }> {
    try {
      const response = await httpClient.post<any>(
        `${this.basePath}/sync-datasets`,
        { datasetIds }
      );

      return {
        success: response.success,
        synced: response.synced_count,
        failed: response.failed_count,
        errors: response.errors || [],
        duration: response.duration,
      };
    } catch (error) {
      console.error('Failed to sync datasets:', error);
      throw new Error(ApiErrorHandler.handleError(error, '同步数据集失败'));
    }
  }

  /**
   * 获取使用统计
   */
  async getUsageStatistics(params?: {
    startDate?: string;
    endDate?: string;
    datasetId?: string;
  }): Promise<{
    totalRequests: number;
    totalTokens: number;
    averageResponseTime: number;
    successRate: number;
    dailyUsage: Array<{
      date: string;
      requests: number;
      tokens: number;
    }>;
    datasetUsage: Array<{
      datasetId: string;
      datasetName: string;
      requests: number;
      tokens: number;
    }>;
  }> {
    try {
      const queryParams = new URLSearchParams();

      if (params?.startDate) queryParams.append('start_date', params.startDate);
      if (params?.endDate) queryParams.append('end_date', params.endDate);
      if (params?.datasetId) queryParams.append('dataset_id', params.datasetId);

      const queryString = queryParams.toString();
      const url = `${this.basePath}/usage-statistics${queryString ? `?${queryString}` : ''}`;

      return await httpClient.get<any>(url);
    } catch (error) {
      console.error('Failed to fetch usage statistics:', error);
      throw new Error(ApiErrorHandler.handleError(error, '获取使用统计失败'));
    }
  }

  /**
   * 流式聊天交互
   */
  async streamChatInteraction(
    request: ChatInteractionRequest,
    onMessage: (chunk: string) => void,
    onComplete: (response: ChatInteractionResponse) => void,
    onError: (error: Error) => void
  ): Promise<void> {
    try {
      const response = await fetch(`/api${this.basePath}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('Response body is not readable');
      }

      const decoder = new TextDecoder();
      let buffer = '';

      try {
        while (true) {
          const { done, value } = await reader.read();

          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');

          // 处理完整的行
          for (let i = 0; i < lines.length - 1; i++) {
            const line = lines[i].trim();
            if (line.startsWith('data: ')) {
              const data = line.slice(6);
              if (data === '[DONE]') {
                return;
              }
              try {
                const parsed = JSON.parse(data);
                if (parsed.type === 'content') {
                  onMessage(parsed.content);
                } else if (parsed.type === 'complete') {
                  onComplete(parsed.response);
                }
              } catch (parseError) {
                console.warn('Failed to parse SSE data:', data);
              }
            }
          }

          // 保留最后一个不完整的行
          buffer = lines[lines.length - 1];
        }
      } finally {
        reader.releaseLock();
      }
    } catch (error) {
      console.error('Failed to stream chat interaction:', error);
      onError(error as Error);
    }
  }
}

/**
 * 创建RAGFlow API实例
 */
export const ragflowApi = new RagflowApi();