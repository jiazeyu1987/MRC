/**
 * Document Upload Component (Fallback Version)
 *
 * A fallback implementation that works without react-dropzone dependency.
 * This component provides basic file upload functionality using native HTML5 file input.
 *
 * Features:
 * - Basic file upload without drag-and-drop
 * - Progress tracking
 * - Error handling
 * - File validation
 *
 * @author Knowledge Base Document Management System
 * @version 1.0.0
 */

import React, { useState, useCallback, useRef } from 'react';
import {
  Upload,
  File,
  X,
  AlertCircle,
  CheckCircle,
  Clock,
  Trash2,
  Pause,
  Play,
  RefreshCw,
  FileText,
  Image,
  FileCode,
  Archive,
  Video
} from 'lucide-react';
import { knowledgeApi } from '../api/knowledgeApi';
import {
  UploadFile,
  UploadResponse,
  UploadProgress,
  ValidationResult
} from '../types/document';

interface DocumentUploadProps {
  knowledgeBaseId: string;
  onUploadComplete?: (documentId: string) => void;
  onUploadError?: (error: string) => void;
  maxFileSize?: number; // in bytes
  maxFiles?: number;
  allowedExtensions?: string[];
  className?: string;
}

interface QueuedFile extends UploadFile {
  id: string;
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'error';
  progress: number;
  error?: string;
  documentId?: string;
  uploadId?: string;
  abortController?: AbortController;
}

const FILE_ICONS = {
  // Document types
  pdf: FileText,
  doc: FileText,
  docx: FileText,
  txt: FileText,
  md: FileText,
  rtf: FileText,
  html: FileCode,
  htm: FileCode,
  xml: FileCode,
  json: FileCode,

  // Image types
  jpg: Image,
  jpeg: Image,
  png: Image,
  gif: Image,
  bmp: Image,
  svg: Image,
  webp: Image,

  // Archive types
  zip: Archive,
  rar: Archive,
  '7z': Archive,
  tar: Archive,
  gz: Archive,

  // Video types
  mp4: Video,
  avi: Video,
  mov: Video,
  wmv: Video,
  flv: Video,
  webm: Video,

  // Default
  default: File
};

const DEFAULT_MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB
const DEFAULT_MAX_FILES = 10;
const DEFAULT_ALLOWED_EXTENSIONS = [
  'pdf', 'doc', 'docx', 'txt', 'md', 'html', 'htm', 'rtf',
  'jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp',
  'zip', 'rar', '7z', 'tar', 'gz',
  'mp4', 'avi', 'mov', 'wmv', 'flv', 'webm',
  'xml', 'json'
];

const DocumentUploadFallback: React.FC<DocumentUploadProps> = ({
  knowledgeBaseId,
  onUploadComplete,
  onUploadError,
  maxFileSize = DEFAULT_MAX_FILE_SIZE,
  maxFiles = DEFAULT_MAX_FILES,
  allowedExtensions = DEFAULT_ALLOWED_EXTENSIONS,
  className = ''
}) => {
  // State management
  const [uploadQueue, setUploadQueue] = useState<QueuedFile[]>([]);
  const [isPaused, setIsPaused] = useState(false);
  const [globalError, setGlobalError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Validate file before upload
  const validateFile = useCallback((file: File): ValidationResult => {
    // Check file size
    if (file.size > maxFileSize) {
      return {
        valid: false,
        error: `文件大小 ${formatFileSize(file.size)} 超过限制 ${formatFileSize(maxFileSize)}`
      };
    }

    // Check file extension
    const extension = file.name.split('.').pop()?.toLowerCase();
    if (!extension || !allowedExtensions.includes(extension)) {
      return {
        valid: false,
        error: `不支持的文件类型: .${extension}。支持的类型: ${allowedExtensions.join(', ')}`
      };
    }

    return {
      valid: true,
      file_info: {
        original_filename: file.name,
        file_size: file.size,
        content_type: file.type
      }
    };
  }, [maxFileSize, allowedExtensions]);

  // Format file size for display
  const formatFileSize = useCallback((bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }, []);

  // Get file icon based on extension
  const getFileIcon = useCallback((filename: string) => {
    const extension = filename.split('.').pop()?.toLowerCase();
    const IconComponent = FILE_ICONS[extension as keyof typeof FILE_ICONS] || FILE_ICONS.default;
    return IconComponent;
  }, []);

  // Add files to upload queue
  const addToQueue = useCallback((files: FileList) => {
    const newFiles: QueuedFile[] = Array.from(files).map(file => {
      const validation = validateFile(file);
      const id = `upload_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

      return {
        id,
        file,
        filename: file.name,
        size: file.size,
        type: file.type,
        lastModified: file.lastModified,
        status: validation.valid ? 'pending' : 'error',
        progress: validation.valid ? 0 : 0,
        error: validation.valid ? undefined : validation.error,
        documentId: undefined,
        uploadId: undefined,
        abortController: validation.valid ? new AbortController() : undefined
      };
    });

    setUploadQueue(prev => [...prev, ...newFiles].slice(-maxFiles)); // Keep only last maxFiles items
    setGlobalError(null);
  }, [validateFile, maxFiles]);

  // Handle file selection
  const handleFileSelect = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      addToQueue(files);
    }
    // Reset input to allow selecting same file again
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, [addToQueue]);

  // Handle file upload
  const uploadFile = useCallback(async (queuedFile: QueuedFile) => {
    if (!queuedFile.abortController || queuedFile.status === 'completed' || queuedFile.status === 'error') {
      return;
    }

    try {
      // Update status to uploading
      setUploadQueue(prev =>
        prev.map(f => f.id === queuedFile.id ? { ...f, status: 'uploading', progress: 0 } : f)
      );

      const uploadId = `upload_${Date.now()}_${queuedFile.id}`;

      // Start upload with progress tracking
      const response = await knowledgeApi.uploadDocument(
        knowledgeBaseId,
        queuedFile.file,
        (progress) => {
          setUploadQueue(prev =>
            prev.map(f =>
              f.id === queuedFile.id
                ? { ...f, progress: Math.round(progress), status: 'uploading' }
                : f
            )
          );
        }
      );

      if (response.success && response.document_id) {
        // Update status to processing (RAGFlow processing)
        setUploadQueue(prev =>
          prev.map(f =>
            f.id === queuedFile.id
              ? {
                  ...f,
                  progress: 100,
                  status: 'processing',
                  documentId: response.document_id,
                  uploadId
                }
              : f
          )
        );

        // Call completion callback
        if (onUploadComplete) {
          onUploadComplete(response.document_id);
        }
      } else {
        throw new Error(response.error || 'Upload failed');
      }

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Upload failed';

      setUploadQueue(prev =>
        prev.map(f =>
          f.id === queuedFile.id
            ? { ...f, status: 'error', error: errorMessage }
            : f
        )
      );

      if (onUploadError) {
        onUploadError(errorMessage);
      }
    }
  }, [knowledgeBaseId, onUploadComplete, onUploadError]);

  // Remove file from queue
  const removeFromQueue = useCallback((queueId: string) => {
    const file = uploadQueue.find(f => f.id === queueId);

    // Abort upload if in progress
    if (file?.abortController && file.status === 'uploading') {
      file.abortController.abort();
    }

    setUploadQueue(prev => prev.filter(f => f.id !== queueId));
  }, [uploadQueue]);

  // Cancel upload
  const cancelUpload = useCallback(async (queueId: string) => {
    const file = uploadQueue.find(f => f.id === queueId);

    if (file?.uploadId) {
      try {
        await knowledgeApi.cancelUpload(knowledgeBaseId, file.uploadId);
      } catch (error) {
        console.warn('Failed to cancel upload:', error);
      }
    }

    if (file?.abortController && file.status === 'uploading') {
      file.abortController.abort();
    }

    removeFromQueue(queueId);
  }, [uploadQueue, knowledgeBaseId, removeFromQueue]);

  // Retry upload
  const retryUpload = useCallback((queueId: string) => {
    const file = uploadQueue.find(f => f.id === queueId);
    if (file) {
      const newAbortController = new AbortController();
      setUploadQueue(prev =>
        prev.map(f =>
          f.id === queueId
            ? { ...f, status: 'pending', progress: 0, error: undefined, abortController: newAbortController }
            : f
        )
      );

      // Retry after a short delay
      setTimeout(() => uploadFile({ ...file, abortController: newAbortController }), 1000);
    }
  }, [uploadQueue, uploadFile]);

  // Clear completed/error files
  const clearCompleted = useCallback(() => {
    setUploadQueue(prev => prev.filter(f =>
      f.status === 'pending' || f.status === 'uploading' || f.status === 'processing'
    ));
  }, []);

  // Auto-start uploads when files are added
  React.useEffect(() => {
    const pendingFiles = uploadQueue.filter(f => f.status === 'pending' && !isPaused);

    if (pendingFiles.length > 0 && !isPaused) {
      // Start uploads sequentially (max 3 concurrent)
      const concurrentLimit = 3;
      const activeUploads = uploadQueue.filter(f => f.status === 'uploading' || f.status === 'processing');

      const availableSlots = concurrentLimit - activeUploads.length;
      const filesToUpload = pendingFiles.slice(0, availableSlots);

      filesToUpload.forEach(file => uploadFile(file));
    }
  }, [uploadQueue, isPaused, uploadFile]);

  // Cleanup on unmount
  React.useEffect(() => {
    return () => {
      // Abort all active uploads
      uploadQueue.forEach(file => {
        if (file.abortController && (file.status === 'uploading' || file.status === 'processing')) {
          file.abortController.abort();
        }
      });
    };
  }, [uploadQueue]);

  const completedCount = uploadQueue.filter(f => f.status === 'completed').length;
  const errorCount = uploadQueue.filter(f => f.status === 'error').length;
  const activeCount = uploadQueue.filter(f =>
    f.status === 'pending' || f.status === 'uploading' || f.status === 'processing'
  ).length;

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">文档上传</h3>

          {/* Action buttons */}
          <div className="flex items-center space-x-2">
            {activeCount > 0 && (
              <>
                <button
                  onClick={() => setIsPaused(!isPaused)}
                  className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                  title={isPaused ? '继续上传' : '暂停上传'}
                >
                  {isPaused ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />}
                </button>

                <button
                  onClick={() => uploadQueue.forEach(f => {
                    if (f.status === 'uploading' || f.status === 'processing') {
                      cancelUpload(f.id);
                    }
                  })}
                  className="p-2 text-red-500 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors"
                  title="取消所有上传"
                >
                  <X className="w-4 h-4" />
                </button>
              </>
            )}

            {(completedCount > 0 || errorCount > 0) && (
              <button
                onClick={clearCompleted}
                className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                title="清除已完成项"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        {/* Status summary */}
        {uploadQueue.length > 0 && (
          <div className="mt-2 text-sm text-gray-600">
            总计 {uploadQueue.length} 个文件 •
            活跃 {activeCount} 个 •
            已完成 {completedCount} 个 •
            错误 {errorCount} 个
          </div>
        )}
      </div>

      {/* File upload area */}
      <div className="p-8 border-2 border-dashed rounded-lg transition-colors cursor-pointer hover:border-gray-400 hover:bg-gray-50">
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={allowedExtensions.map(ext => `.${ext}`).join(',')}
          onChange={handleFileSelect}
          disabled={isPaused}
          className="hidden"
        />

        <div className="text-center cursor-pointer" onClick={() => fileInputRef.current?.click()}>
          <Upload className={`mx-auto h-12 w-12 text-gray-400 mb-4 ${isPaused ? 'opacity-50' : ''}`} />
          <div className="text-gray-600">
            <p className="text-lg font-medium mb-2">
              {isPaused ? '上传已暂停' : '点击选择文件上传'}
            </p>
            <p className="text-sm text-gray-500 mb-4">
              支持多文件选择，最多 {maxFiles} 个文件
            </p>

            <div className="text-xs text-gray-400 space-y-1">
              <p>最大文件大小: {formatFileSize(maxFileSize)}</p>
              <p>支持的格式: {allowedExtensions.join(', ')}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Global error */}
      {globalError && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg mx-4 mt-4">
          <div className="flex items-center">
            <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
            <span className="text-red-700 text-sm">{globalError}</span>
          </div>
        </div>
      )}

      {/* Upload queue */}
      {uploadQueue.length > 0 && (
        <div className="p-4 border-t border-gray-200">
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {uploadQueue.map(file => {
              const FileIcon = getFileIcon(file.filename);

              return (
                <div
                  key={file.id}
                  className={`border rounded-lg p-3 ${
                    file.status === 'error' ? 'border-red-200 bg-red-50' :
                    file.status === 'completed' ? 'border-green-200 bg-green-50' :
                    file.status === 'processing' ? 'border-blue-200 bg-blue-50' :
                    'border-gray-200 bg-white'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center flex-1 min-w-0">
                      <FileIcon className="w-5 h-5 text-gray-400 mr-2 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {file.filename}
                        </p>
                        <p className="text-xs text-gray-500">
                          {formatFileSize(file.size)}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2 ml-2">
                      {/* Status indicator */}
                      <div className="flex items-center">
                        {file.status === 'pending' && <Clock className="w-4 h-4 text-yellow-500" />}
                        {file.status === 'uploading' && <RefreshCw className="w-4 h-4 text-blue-500 animate-spin" />}
                        {file.status === 'processing' && <RefreshCw className="w-4 h-4 text-blue-500 animate-spin" />}
                        {file.status === 'completed' && <CheckCircle className="w-4 h-4 text-green-500" />}
                        {file.status === 'error' && <AlertCircle className="w-4 h-4 text-red-500" />}
                      </div>

                      {/* Action buttons */}
                      <div className="flex items-center space-x-1">
                        {file.status === 'error' && (
                          <button
                            onClick={() => retryUpload(file.id)}
                            className="p-1 text-blue-500 hover:text-blue-700 hover:bg-blue-100 rounded transition-colors"
                            title="重试"
                          >
                            <RefreshCw className="w-3 h-3" />
                          </button>
                        )}

                        {(file.status === 'uploading' || file.status === 'processing') && (
                          <button
                            onClick={() => cancelUpload(file.id)}
                            className="p-1 text-red-500 hover:text-red-700 hover:bg-red-100 rounded transition-colors"
                            title="取消"
                          >
                            <X className="w-3 h-3" />
                          </button>
                        )}

                        <button
                          onClick={() => removeFromQueue(file.id)}
                          className="p-1 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded transition-colors"
                          title="移除"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Progress bar */}
                  {(file.status === 'uploading' || file.status === 'processing') && (
                    <div className="mt-2">
                      <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
                        <span>
                          {file.status === 'uploading' ? '上传中' : '处理中'} {file.progress}%
                        </span>
                        <span>{formatFileSize(Math.round(file.size * file.progress / 100))}</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-1.5">
                        <div
                          className={`h-1.5 rounded-full transition-all duration-300 ${
                            file.status === 'processing' ? 'bg-blue-500' : 'bg-green-500'
                          }`}
                          style={{ width: `${file.progress}%` }}
                        />
                      </div>
                    </div>
                  )}

                  {/* Error message */}
                  {file.status === 'error' && file.error && (
                    <div className="mt-2 text-xs text-red-600 bg-red-100 rounded p-2">
                      {file.error}
                    </div>
                  )}

                  {/* Processing message */}
                  {file.status === 'processing' && (
                    <div className="mt-2 text-xs text-blue-600 bg-blue-100 rounded p-2">
                      正在RAGFlow中处理文档，请稍候...
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentUploadFallback;