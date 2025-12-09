// 增强功能的TypeScript类型定义 - 对话历史、搜索分析、API文档

// ==================== 对话历史相关类型 ====================

// 对话消息类型
export interface ConversationMessage {
  id?: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  metadata?: Record<string, any>;
  references?: Reference[];
}

// 对话历史
export interface ConversationHistory {
  id: number;
  knowledge_base_id: number;
  user_id?: string;
  title: string;
  messages: ConversationMessage[];
  tags: string[];
  template_id?: string;
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
  is_archived: boolean;
  message_count: number;
  last_activity?: string;
}

// 对话模板
export interface ConversationTemplate {
  id: number;
  name: string;
  description?: string;
  category: string;
  prompt: string;
  parameters: TemplateParameter[];
  is_system: boolean;
  usage_count: number;
  created_at: string;
  updated_at: string;
}

// 模板参数
export interface TemplateParameter {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'select' | 'textarea';
  description: string;
  required: boolean;
  default_value?: any;
  options?: string[]; // 用于select类型
  validation?: ParameterValidation;
}

// 参数验证规则
export interface ParameterValidation {
  min_length?: number;
  max_length?: number;
  pattern?: string; // 正则表达式
  custom_validator?: string; // 函数名
}

// 创建对话请求
export interface CreateConversationRequest {
  title: string;
  messages?: ConversationMessage[];
  tags?: string[];
  user_id?: string;
  template_id?: number;
  parameters?: Record<string, any>;
}

// 更新对话请求
export interface UpdateConversationRequest {
  title?: string;
  messages?: ConversationMessage[];
  tags?: string[];
  metadata?: Record<string, any>;
}

// 对话列表查询参数
export interface ConversationListParams {
  page?: number;
  per_page?: number;
  search?: string;
  tags?: string[];
  user_id?: string;
  is_archived?: boolean;
  sort_by?: 'created_at' | 'updated_at' | 'title' | 'message_count';
  sort_order?: 'asc' | 'desc';
}

// 对话列表响应
export interface ConversationListResponse {
  conversations: ConversationHistory[];
  pagination: {
    page: number;
    per_page: number;
    total: number;
    pages: number;
  };
}

// 导出格式类型
export type ExportFormat = 'json' | 'markdown' | 'txt' | 'csv';

// ==================== 搜索分析相关类型 ====================

// 搜索分析数据
export interface SearchAnalytics {
  id: number;
  knowledge_base_id: number;
  user_id?: string;
  search_query: string;
  filters: Record<string, any>;
  results_count: number;
  response_time_ms: number;
  clicked_documents: string[];
  created_at: string;
}

// 搜索统计
export interface SearchStatistics {
  period_days: number;
  total_searches: number;
  average_per_day: number;
  performance: {
    avg_response_time_ms: number;
    max_response_time_ms: number;
    min_response_time_ms: number;
    avg_results_count: number;
  };
  popular_terms: PopularTerm[];
  usage_trends: UsageTrend[];
  no_result_searches: number;
  success_rate: number;
  click_through_rate: number;
}

// 热门搜索词
export interface PopularTerm {
  term: string;
  count: number;
  avg_results: number;
  avg_response_time_ms: number;
}

// 使用趋势
export interface UsageTrend {
  date: string;
  search_count: number;
  avg_response_time_ms: number;
  avg_results: number;
}

// 用户搜索模式
export interface UserSearchPattern {
  user_id: string;
  search_count: number;
  unique_queries: number;
  avg_response_time_ms: number;
  top_queries: string[];
}

// 性能洞察
export interface PerformanceInsights {
  performance_rating: 'excellent' | 'good' | 'fair' | 'poor' | 'unknown';
  response_time_status: 'fast' | 'normal' | 'slow' | 'very_slow' | 'unknown';
  success_rate_status: 'excellent' | 'good' | 'fair' | 'poor' | 'unknown';
  recommendations: string[];
  issues: string[];
  strengths: string[];
}

// 搜索事件记录请求
export interface RecordSearchRequest {
  search_query: string;
  user_id?: string;
  filters?: Record<string, any>;
  results_count?: number;
  response_time_ms?: number;
  clicked_documents?: string[];
}

// 搜索分析查询参数
export interface SearchAnalyticsParams {
  days?: number;
  user_id?: string;
  query_type?: 'successful' | 'unsuccessful' | 'all';
  include_performance?: boolean;
}

// ==================== API文档相关类型 ====================

// API文档缓存
export interface APIDocumentationCache {
  id: number;
  endpoint_path: string;
  method: string;
  category: string;
  documentation: APIDocumentation;
  examples: APIExample[];
  last_updated: string;
  expires_at: string;
  is_active: boolean;
}

// API文档结构
export interface APIDocumentation {
  path: string;
  method: string;
  summary: string;
  description?: string;
  parameters: APIParameter[];
  request_body?: APIRequestBody;
  responses: APIResponse[];
  tags: string[];
  security?: APISecurity[];
}

// API参数
export interface APIParameter {
  name: string;
  in: 'query' | 'path' | 'header' | 'cookie';
  description: string;
  required: boolean;
  type: string;
  schema?: APISchema;
  example?: any;
}

// API请求体
export interface APIRequestBody {
  description: string;
  required: boolean;
  content: Record<string, APIMediaType>;
}

// API响应
export interface APIResponse {
  code: string;
  description: string;
  content?: Record<string, APIMediaType>;
  headers?: Record<string, APIHeader>;
}

// API媒体类型
export interface APIMediaType {
  schema: APISchema;
  example?: any;
}

// API模式
export interface APISchema {
  type: string;
  properties?: Record<string, APISchema>;
  items?: APISchema;
  required?: string[];
  format?: string;
  enum?: string[];
  description?: string;
}

// API头部
export interface APIHeader {
  description: string;
  required: boolean;
  schema: APISchema;
}

// API安全
export interface APISecurity {
  type: string;
  description?: string;
  name?: string;
  in?: string;
}

// API示例
export interface APIExample {
  name: string;
  description?: string;
  request: APIExampleRequest;
  response: APIExampleResponse;
}

// API示例请求
export interface APIExampleRequest {
  method: string;
  url: string;
  headers?: Record<string, string>;
  query_params?: Record<string, any>;
  body?: any;
}

// API示例响应
export interface APIExampleResponse {
  status_code: number;
  headers?: Record<string, string>;
  body: any;
}

// API测试请求
export interface APITestRequest {
  endpoint_path: string;
  method: string;
  parameters?: Record<string, any>;
  headers?: Record<string, string>;
  body?: any;
}

// API测试响应
export interface APITestResponse {
  request: {
    method: string;
    url: string;
    headers: Record<string, string>;
    body?: any;
  };
  response: {
    status_code: number;
    status_text: string;
    headers: Record<string, string>;
    body: any;
    response_time_ms: number;
  };
  mock_data: boolean;
  errors?: string[];
}

// 速率限制状态
export interface RateLimitStatus {
  endpoint_limits: Record<string, RateLimit>;
  global_limit: RateLimit;
  current_usage: Record<string, RateLimitUsage>;
  reset_time: string;
}

// 速率限制
export interface RateLimit {
  requests_per_minute: number;
  requests_per_hour: number;
  requests_per_day: number;
}

// 速率限制使用情况
export interface RateLimitUsage {
  current_minute: number;
  current_hour: number;
  current_day: number;
  remaining_minute: number;
  remaining_hour: number;
  remaining_day: number;
}

// API文档分类
export interface APIDocumentationCategory {
  name: string;
  description: string;
  endpoint_count: number;
  endpoints: string[];
}

// ==================== 增强统计相关类型 ====================

// 增强的知识库统计
export interface EnhancedKnowledgeBaseStatistics {
  knowledge_base: {
    id: number;
    name: string;
    status: string;
    document_count: number;
    conversation_count: number;
    search_count: number;
    last_activity?: string;
  };
  period: {
    days: number;
    start_date: string;
    end_date: string;
  };
  conversations: {
    total: number;
    unique_users: number;
    avg_per_day: number;
  };
  searches: {
    total: number;
    avg_response_time_ms: number;
    total_results: number;
    avg_results_per_search: number;
  };
  daily_activity: DailyActivity[];
  engagement_score: number;
}

// 每日活动
export interface DailyActivity {
  date: string;
  conversations: number;
  searches: number;
}

// 活跃知识库排行
export interface TopActiveKnowledgeBase {
  knowledge_base_id: number;
  name: string;
  document_count: number;
  activity_score: number;
  conversations_count: number;
  searches_count: number;
  unique_users_count: number;
  rank: number;
}

// ==================== 通用请求/响应类型 ====================

// 分页参数
export interface PaginationParams {
  page?: number;
  per_page?: number;
  limit?: number;
  offset?: number;
}

// 排序参数
export interface SortParams {
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

// 时间范围参数
export interface DateRangeParams {
  start_date?: string;
  end_date?: string;
  days?: number;
}

// 搜索过滤参数
export interface SearchFilterParams {
  search?: string;
  filters?: Record<string, any>;
}

// 批量操作请求
export interface BulkOperationRequest {
  action: string;
  ids: number[];
  parameters?: Record<string, any>;
}

// 批量操作响应
export interface BulkOperationResponse {
  success: boolean;
  total: number;
  successful: number;
  failed: number;
  errors: string[];
  results: any[];
}

// 健康检查响应
export interface HealthCheckResponse {
  status: 'healthy' | 'unhealthy' | 'degraded';
  timestamp: string;
  version: string;
  uptime: number;
  components: Record<string, ComponentHealth>;
}

// 组件健康状态
export interface ComponentHealth {
  status: 'healthy' | 'unhealthy' | 'degraded';
  response_time_ms?: number;
  last_check: string;
  error_message?: string;
}

// ==================== 联合类型和工具类型 ====================

// 知识库增强功能API响应
export type EnhancedFeaturesApiResponse<T> = ApiResponse<T>;

// 对话操作类型
export type ConversationAction = 'create' | 'update' | 'delete' | 'export' | 'archive' | 'unarchive';

// 搜索操作类型
export type SearchAction = 'record' | 'analyze' | 'insights' | 'trends';

// API文档操作类型
export type APIDocumentationAction = 'view' | 'test' | 'refresh' | 'cache';

// 导出选项
export interface ExportOptions {
  format: ExportFormat;
  include_metadata?: boolean;
  include_references?: boolean;
  date_range?: DateRangeParams;
  filters?: SearchFilterParams;
}

// 用户偏好设置
export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  language: string;
  timezone: string;
  default_export_format: ExportFormat;
  conversation_settings: {
    auto_save: boolean;
    show_timestamps: boolean;
    message_display: 'compact' | 'expanded';
  };
  search_settings: {
    default_period: number;
    show_analytics: boolean;
    auto_record: boolean;
  };
  api_settings: {
    default_timeout: number;
    show_examples: boolean;
    mock_mode: boolean;
  };
}