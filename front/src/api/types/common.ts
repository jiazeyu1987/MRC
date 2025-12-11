/**
 * 通用类型定义
 */

export interface BaseEntity {
  id: number | string;
  createdAt: string;
  updatedAt: string;
}

export interface PaginationInfo {
  page: number;
  pageSize: number;
  total: number;
  pages: number;
  hasNext: boolean;
  hasPrev: boolean;
}

export interface ListResponse<T> {
  items: T[];
  pagination: PaginationInfo;
}

export interface ApiResponse<T = any> {
  success: boolean;
  data: T;
  message?: string;
  error?: string;
}

export interface ApiError {
  code: string;
  message: string;
  details?: any;
}

export interface SuccessResponse<T = any> {
  success: true;
  data: T;
  message?: string;
}

export interface ErrorResponse {
  success: false;
  error_code: string;
  message: string;
  errors?: Record<string, string[]>;
}

export type RequestMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';

export interface RequestConfig {
  method?: RequestMethod;
  headers?: Record<string, string>;
  params?: Record<string, any>;
  data?: any;
  timeout?: number;
}

export interface SortOptions {
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

export interface FilterOptions {
  search?: string;
  status?: string | string[];
  dateFrom?: string;
  dateTo?: string;
  [key: string]: any;
}

export interface PaginationOptions {
  page?: number;
  pageSize?: number;
  limit?: number;
  offset?: number;
}

/**
 * 查询参数接口
 */
export interface QueryParams extends SortOptions, FilterOptions, PaginationOptions {
  [key: string]: any;
}

/**
 * 文件上传相关类型
 */
export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
  speed?: number;
  timeRemaining?: number;
}

export interface UploadResponse {
  id: string;
  filename: string;
  size: number;
  url: string;
  uploadId: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress?: UploadProgress;
  error?: string;
}

/**
 * 缓存相关类型
 */
export interface CacheOptions {
  ttl?: number; // 缓存时间（毫秒）
  key?: string; // 缓存键
  invalidateOnMutation?: boolean; // 是否在变更操作时清除缓存
}

export interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
}

/**
 * WebSocket和实时通信类型
 */
export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
  id?: string;
}

export interface RealtimeEvent {
  type: string;
  payload: any;
  timestamp: string;
  source: string;
}

/**
 * 批量操作类型
 */
export interface BulkOperation<T> {
  items: T[];
  operation: 'create' | 'update' | 'delete';
  options?: Record<string, any>;
}

export interface BulkOperationResult {
  success: number;
  failed: number;
  total: number;
  errors: Array<{
    index: number;
    item: any;
    error: string;
  }>;
}

/**
 * 导出相关类型
 */
export interface ExportOptions {
  format: 'json' | 'csv' | 'xlsx' | 'pdf';
  fields?: string[];
  filters?: FilterOptions;
  pagination?: PaginationOptions;
}

export interface ExportResult {
  url: string;
  filename: string;
  size: number;
  format: string;
  expiresAt?: string;
}

/**
 * 搜索相关类型
 */
export interface SearchRequest {
  query: string;
  filters?: FilterOptions;
  pagination?: PaginationOptions;
  sort?: SortOptions;
}

export interface SearchResult<T> {
  items: T[];
  total: number;
  pagination: PaginationInfo;
  suggestions?: string[];
  facets?: Record<string, Array<{ value: string; count: number }>>;
}

export interface SearchSuggestion {
  text: string;
  type: 'history' | 'popular' | 'autocomplete';
  score?: number;
}

/**
 * 统计相关类型
 */
export interface StatisticsData {
  count: number;
  total?: number;
  percentage?: number;
  trend?: 'up' | 'down' | 'stable';
  comparison?: {
    period: string;
    previous: number;
    change: number;
    percentageChange: number;
  };
}

export interface ChartDataPoint {
  date: string;
  value: number;
  label?: string;
  category?: string;
}

/**
 * 状态和枚举
 */
export enum Status {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
  DELETED = 'deleted',
}

export enum Priority {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  URGENT = 'urgent',
}

export enum SortOrder {
  ASC = 'asc',
  DESC = 'desc',
}

/**
 * 验证相关类型
 */
export interface ValidationError {
  field: string;
  message: string;
  code?: string;
}

export interface ValidationResult {
  isValid: boolean;
  errors: ValidationError[];
}

/**
 * 配置和设置类型
 */
export interface AppConfig {
  apiBaseUrl: string;
  timeout: number;
  retryAttempts: number;
  cacheEnabled: boolean;
  debugMode: boolean;
  theme?: string;
  language?: string;
}

export interface UserPreferences {
  pageSize: number;
  theme: 'light' | 'dark' | 'auto';
  language: string;
  notifications: {
    email: boolean;
    push: boolean;
    desktop: boolean;
  };
  autoSave: boolean;
  autoSaveInterval: number;
}

/**
 * 工具函数类型
 */
export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;

export type RequiredFields<T, K extends keyof T> = T & Required<Pick<T, K>>;

export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};