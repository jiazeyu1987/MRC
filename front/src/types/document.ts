/**
 * Document Management TypeScript Interfaces
 *
 * This file defines TypeScript interfaces for the document management feature
 * in the MRC (Multi-Role Dialogue System) frontend.
 */

// Base Document interface
export interface Document {
  id: string;
  knowledge_base_id: string;
  ragflow_document_id?: string;
  filename: string;
  original_filename: string;
  file_size: number;
  file_type: string;
  mime_type: string;
  upload_status: 'uploading' | 'uploaded' | 'failed';
  processing_status: 'pending' | 'processing' | 'completed' | 'failed';
  chunk_count: number;
  error_message?: string;
  ragflow_metadata?: Record<string, any>;

  created_at: string;
  updated_at: string;
  uploaded_at?: string;
  processed_at?: string;
}

// Document Chunk interface
export interface DocumentChunk {
  id: string;
  document_id: string;
  ragflow_chunk_id?: string;
  chunk_index: number;
  content: string;
  content_preview?: string;
  word_count: number;
  character_count: number;

  ragflow_metadata?: Record<string, any>;
  embedding_vector_id?: string;
  position_start?: number;
  position_end?: number;

  created_at: string;
  updated_at: string;
}

// Processing Log interface
export interface ProcessingLog {
  id: string;
  document_id: string;
  step: 'upload' | 'parse' | 'chunk' | 'index' | 'sync';
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number; // 0-100
  message?: string;
  error_details?: Record<string, any>;

  started_at: string;
  completed_at?: string;
  duration_seconds?: number;
}

// Document Filters interface
export interface DocumentFilters {
  search?: string;
  status?: string;
  file_type?: string;
  sort_by?: 'filename' | 'upload_date' | 'file_size' | 'status' | 'created_at';
  sort_order?: 'asc' | 'desc';
  page?: number;
  limit?: number;
}

// Chunk Search Filters interface
export interface ChunkSearchFilters {
  document_id?: string;
  min_relevance_score?: number;
  max_results?: number;
}

// Upload Response interface
export interface UploadResponse {
  success: boolean;
  document_id?: string;
  upload_id?: string;
  document?: Document;
  error?: string;
  message?: string;
}

// Chunk Search Result interface
export interface ChunkSearchResult {
  chunks: DocumentChunk[];
  total_count: number;
  query: string;
  search_time: number;
  filters_applied: Record<string, any>;
}

// Document Statistics interface
export interface DocumentStatistics {
  total_documents: number;
  total_file_size_bytes: number;
  total_file_size_mb: number;
  total_chunks: number;
  status_breakdown: Record<string, number>;
  file_type_breakdown: Record<string, number>;
  updated_at: string;
}

// Chunk Statistics interface
export interface ChunkStatistics {
  total_chunks: number;
  total_word_count: number;
  total_character_count: number;
  average_chunk_length: number;
  documents_with_chunks: number;
  document_breakdown: DocumentChunkBreakdown[];
  updated_at: string;
}

// Document Chunk Breakdown interface
export interface DocumentChunkBreakdown {
  document_id: string;
  filename: string;
  chunk_count: number;
  total_words: number;
}

// Upload Progress interface
export interface UploadProgress {
  upload_id: string;
  document_id?: string;
  progress: number; // 0-100
  status: 'uploading' | 'processing' | 'completed' | 'failed' | 'cancelled';
  message?: string;
  start_time: string;
  file_size?: number;
  bytes_uploaded?: number;
  upload_speed?: number; // bytes per second
}

// API Response interfaces
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error_code?: string;
  error?: string;
}

// Document List Response interface
export interface DocumentListResponse {
  documents: Document[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    has_more: boolean;
  };
}

// Upload File interface
export interface UploadFile {
  file: File;
  filename: string;
  size: number;
  type: string;
  lastModified: number;
}

// Validation Result interface
export interface ValidationResult {
  valid: boolean;
  error?: string;
  file_info?: {
    original_filename: string;
    file_size: number;
    content_type: string;
  };
}

// File Type Support interface
export interface FileTypeSupport {
  allowed_extensions: string[];
  max_file_size_bytes: number;
  max_file_size_mb: number;
  allowed_mime_types: string[];
}

// Document Reference interface (for conversation integration)
export interface DocumentReference {
  id: string;
  document_id: string;
  chunk_id?: string;
  conversation_id?: string;
  message_id?: string;
  relevance_score?: number;
  reference_count: number;
  created_at: string;
  updated_at: string;
}

// Document Action Types
export type DocumentAction = 'view' | 'edit' | 'delete' | 'download' | 'reprocess' | 'exclude' | 'include';

// Document Status Types
export type DocumentStatus = Document['upload_status'] | Document['processing_status'];

// Processing Step Types
export type ProcessingStep = ProcessingLog['step'];

// Sort Options
export type SortOption = DocumentFilters['sort_by'];

// Sort Order Types
export type SortOrder = DocumentFilters['sort_order'];

// Event interfaces for WebSocket/real-time updates
export interface DocumentProgressEvent {
  type: 'progress_update';
  data: UploadProgress;
}

export interface DocumentStatusChangeEvent {
  type: 'status_change';
  data: {
    document_id: string;
    old_status: DocumentStatus;
    new_status: DocumentStatus;
    message?: string;
  };
}

export interface DocumentErrorEvent {
  type: 'error';
  data: {
    document_id: string;
    error: string;
    step?: ProcessingStep;
  };
}

// Union type for all document events
export type DocumentEvent =
  | DocumentProgressEvent
  | DocumentStatusChangeEvent
  | DocumentErrorEvent;

// Default values and constants
export const DOCUMENT_DEFAULTS = {
  PAGE_SIZE: 20,
  MAX_FILE_SIZE: 50 * 1024 * 1024, // 50MB
  SUPPORTED_EXTENSIONS: ['pdf', 'doc', 'docx', 'txt', 'md', 'html', 'htm', 'rtf', 'jpg', 'jpeg', 'png', 'gif', 'bmp'],
  PROGRESS_UPDATE_INTERVAL: 1000, // 1 second
  SEARCH_MAX_RESULTS: 50,
  CHUNK_PREVIEW_LENGTH: 500,
} as const;

// Helper functions
export const isDocumentCompleted = (document: Document): boolean => {
  return document.upload_status === 'uploaded' && document.processing_status === 'completed';
};

export const isDocumentProcessing = (document: Document): boolean => {
  return document.upload_status === 'uploaded' && document.processing_status === 'processing';
};

export const isDocumentFailed = (document: Document): boolean => {
  return document.upload_status === 'failed' || document.processing_status === 'failed';
};

export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export const getStatusColor = (status: DocumentStatus): string => {
  switch (status) {
    case 'completed':
      return 'text-green-600';
    case 'processing':
      return 'text-blue-600';
    case 'pending':
      return 'text-yellow-600';
    case 'failed':
    case 'uploading':
      return 'text-red-600';
    default:
      return 'text-gray-600';
  }
};

export const getStatusIcon = (status: DocumentStatus): string => {
  switch (status) {
    case 'completed':
      return '✓';
    case 'processing':
      return '⟳';
    case 'pending':
      return '⏳';
    case 'failed':
    case 'uploading':
      return '✗';
    default:
      return '?';
  }
};