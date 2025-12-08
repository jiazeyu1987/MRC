/**
 * Frontend Integration Tests for Document Management System
 *
 * This test suite covers frontend component integration, user interactions,
 * API communication, and error handling for the Document Management features.
 *
 * Test Coverage:
- Component rendering and interaction
- API integration and error handling
- File upload workflows
- Progress tracking
- Search and filtering functionality
- Responsive design
- Accessibility
- Performance
*
* @author Knowledge Base Document Management System
* @version 1.0.0
*/

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';

// Mock API responses
import { knowledgeApi } from '../api/knowledgeApi';

// Import components to test
import DocumentUpload from '../components/DocumentUpload';
import DocumentList from '../components/DocumentList';
import DocumentView from '../components/DocumentView';
import KnowledgeBaseDetails from '../components/KnowledgeBaseDetails';
import TestConversation from '../components/TestConversation';

// Import types
import { Document, DocumentChunk } from '../types/document';
import { KnowledgeBase } from '../types/knowledge';

// Mock React Dropzone
vi.mock('react-dropzone', () => ({
  useDropzone: () => ({
    getRootProps: () => ({ 'data-testid': 'dropzone' }),
    getInputProps: () => ({ 'data-testid': 'file-input' }),
    isDragActive: false,
  }),
}));

// Mock API
vi.mock('../api/knowledgeApi', () => ({
  knowledgeApi: {
    uploadDocument: vi.fn(),
    getDocuments: vi.fn(),
    getDocument: vi.fn(),
    deleteDocument: vi.fn(),
    searchChunks: vi.fn(),
    getDocumentChunks: vi.fn(),
    getUploadProgress: vi.fn(),
    cancelUpload: vi.fn(),
    testConversation: vi.fn(),
    getKnowledgeBaseDetails: vi.fn(),
  },
}));

// Mock theme
vi.mock('../theme', () => ({
  useTheme: () => ({
    theme: {
      primary: 'bg-blue-600',
      primaryHover: 'hover:bg-blue-700',
      text: 'text-gray-700',
      border: 'border-gray-300',
      ring: 'ring-2 ring-blue-500 focus:border-blue-500',
      bgSoft: 'bg-gray-50',
    },
  }),
}));

// Mock errorHandler
vi.mock('../utils/errorHandler', () => ({
  handleError: vi.fn((error: any) => error.message || 'Unknown error'),
}));

describe('Document Management Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('DocumentUpload Component', () => {
    const mockKnowledgeBaseId = 'test-kb-123';

    it('renders upload interface correctly', () => {
      render(
        <DocumentUpload
          knowledgeBaseId={mockKnowledgeBaseId}
          onUploadComplete={vi.fn()}
          onUploadError={vi.fn()}
        />
      );

      expect(screen.getByText('文档上传')).toBeInTheDocument();
      expect(screen.getByTestId('dropzone')).toBeInTheDocument();
      expect(screen.getByText(/拖放文件到这里上传/)).toBeInTheDocument();
    });

    it('handles file selection and upload', async () => {
      const mockOnUploadComplete = vi.fn();
      const mockUploadResponse = {
        success: true,
        document_id: 'doc-123',
        upload_id: 'upload-123',
        document: {
          id: 'doc-123',
          filename: 'test.pdf',
          original_filename: 'test.pdf',
          file_size: 1024,
          file_type: 'pdf',
          upload_status: 'completed' as const,
          processing_status: 'completed' as const,
          chunk_count: 5,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      };

      (knowledgeApi.uploadDocument as any).mockResolvedValue(mockUploadResponse);

      render(
        <DocumentUpload
          knowledgeBaseId={mockKnowledgeBaseId}
          onUploadComplete={mockOnUploadComplete}
          onUploadError={vi.fn()}
        />
      );

      // Simulate file drop
      const dropzone = screen.getByTestId('dropzone');
      const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });

      fireEvent.drop(dropzone, {
        dataTransfer: {
          files: [file],
        },
      });

      // Wait for upload to complete
      await waitFor(() => {
        expect(knowledgeApi.uploadDocument).toHaveBeenCalledWith(
          mockKnowledgeBaseId,
          file,
          expect.any(Function)
        );
      });

      // Check if completion callback was called
      expect(mockOnUploadComplete).toHaveBeenCalledWith('doc-123');
    });

    it('handles upload errors gracefully', async () => {
      const mockOnUploadError = vi.fn();
      const errorMessage = 'Upload failed due to server error';

      (knowledgeApi.uploadDocument as any).mockRejectedValue(new Error(errorMessage));

      render(
        <DocumentUpload
          knowledgeBaseId={mockKnowledgeBaseId}
          onUploadComplete={vi.fn()}
          onUploadError={mockOnUploadError}
        />
      );

      const dropzone = screen.getByTestId('dropzone');
      const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });

      fireEvent.drop(dropzone, {
        dataTransfer: {
          files: [file],
        },
      });

      await waitFor(() => {
        expect(mockOnUploadError).toHaveBeenCalledWith(errorMessage);
      });
    });

    it('validates file types and sizes', async () => {
      const mockOnUploadError = vi.fn();

      render(
        <DocumentUpload
          knowledgeBaseId={mockKnowledgeBaseId}
          onUploadComplete={vi.fn()}
          onUploadError={mockOnUploadError}
          maxFileSize={1024} // 1KB limit
          allowedExtensions={['pdf', 'txt']}
        />
      );

      const dropzone = screen.getByTestId('dropzone');

      // Test oversized file
      const oversizedFile = new File(['x'.repeat(2048)], 'large.txt', { type: 'text/plain' });
      fireEvent.drop(dropzone, {
        dataTransfer: {
          files: [oversizedFile],
        },
      });

      await waitFor(() => {
        expect(screen.getByText(/超过限制/)).toBeInTheDocument();
      });

      // Test unsupported file type
      const unsupportedFile = new File(['test'], 'test.exe', { type: 'application/x-executable' });
      fireEvent.drop(dropzone, {
        dataTransfer: {
          files: [unsupportedFile],
        },
      });

      await waitFor(() => {
        expect(screen.getByText(/不支持的文件类型/)).toBeInTheDocument();
      });
    });
  });

  describe('DocumentList Component', () => {
    const mockKnowledgeBaseId = 'test-kb-123';
    const mockDocuments: Document[] = [
      {
        id: 'doc-1',
        knowledge_base_id: mockKnowledgeBaseId,
        filename: 'document1.pdf',
        original_filename: 'Document 1.pdf',
        file_size: 1024000,
        file_type: 'pdf',
        mime_type: 'application/pdf',
        upload_status: 'completed',
        processing_status: 'completed',
        chunk_count: 10,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
      {
        id: 'doc-2',
        knowledge_base_id: mockKnowledgeBaseId,
        filename: 'document2.txt',
        original_filename: 'Document 2.txt',
        file_size: 512000,
        file_type: 'txt',
        mime_type: 'text/plain',
        upload_status: 'processing',
        processing_status: 'processing',
        chunk_count: 0,
        created_at: '2024-01-02T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
      },
    ];

    it('renders document list correctly', async () => {
      const mockResponse = {
        documents: mockDocuments,
        pagination: {
          page: 1,
          limit: 20,
          total: mockDocuments.length,
          has_more: false,
        },
      };

      (knowledgeApi.getDocuments as any).mockResolvedValue(mockResponse);

      render(
        <DocumentList
          knowledgeBaseId={mockKnowledgeBaseId}
          onDocumentSelect={vi.fn()}
          onDocumentDelete={vi.fn()}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('文档列表')).toBeInTheDocument();
      });

      expect(screen.getByText('Document 1.pdf')).toBeInTheDocument();
      expect(screen.getByText('Document 2.txt')).toBeInTheDocument();
    });

    it('handles search and filtering', async () => {
      const mockResponse = {
        documents: [mockDocuments[0]], // Only first document matches search
        pagination: {
          page: 1,
          limit: 20,
          total: 1,
          has_more: false,
        },
      };

      (knowledgeApi.getDocuments as any).mockResolvedValue(mockResponse);

      render(
        <DocumentList
          knowledgeBaseId={mockKnowledgeBaseId}
          onDocumentSelect={vi.fn()}
          onDocumentDelete={vi.fn()}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('文档列表')).toBeInTheDocument();
      });

      // Perform search
      const searchInput = screen.getByPlaceholderText('搜索文档名称...');
      await userEvent.type(searchInput, 'Document 1');

      // Wait for search results
      await waitFor(() => {
        expect(knowledgeApi.getDocuments).toHaveBeenCalledWith(
          mockKnowledgeBaseId,
          expect.objectContaining({
            search: 'Document 1',
          })
        );
      });
    });

    it('handles document selection and deletion', async () => {
      const mockOnDocumentSelect = vi.fn();
      const mockOnDocumentDelete = vi.fn();

      const mockResponse = {
        documents: mockDocuments,
        pagination: {
          page: 1,
          limit: 20,
          total: mockDocuments.length,
          has_more: false,
        },
      };

      (knowledgeApi.getDocuments as any).mockResolvedValue(mockResponse);
      (knowledgeApi.deleteDocument as any).mockResolvedValue({ success: true });

      render(
        <DocumentList
          knowledgeBaseId={mockKnowledgeBaseId}
          onDocumentSelect={mockOnDocumentSelect}
          onDocumentDelete={mockOnDocumentDelete}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Document 1.pdf')).toBeInTheDocument();
      });

      // Test document selection
      const selectCheckbox = screen.getAllByRole('checkbox')[1]; // Skip header checkbox
      await userEvent.click(selectCheckbox);

      // Test document view
      const viewButton = screen.getByTitle('查看详情');
      await userEvent.click(viewButton);

      expect(mockOnDocumentSelect).toHaveBeenCalledWith(mockDocuments[0]);

      // Test document deletion
      const deleteButton = screen.getByTitle('删除文档');
      await userEvent.click(deleteButton);

      // Confirm deletion (assuming confirmation dialog)
      await waitFor(() => {
        expect(mockOnDocumentDelete).toHaveBeenCalledWith('doc-1');
      });
    });
  });

  describe('DocumentView Component', () => {
    const mockKnowledgeBaseId = 'test-kb-123';
    const mockDocument: Document = {
      id: 'doc-1',
      knowledge_base_id: mockKnowledgeBaseId,
      filename: 'test_document.pdf',
      original_filename: 'Test Document.pdf',
      file_size: 2048000,
      file_type: 'pdf',
      mime_type: 'application/pdf',
      upload_status: 'completed',
      processing_status: 'completed',
      chunk_count: 15,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    };

    const mockChunks: DocumentChunk[] = [
      {
        id: 'chunk-1',
        document_id: 'doc-1',
        chunk_index: 0,
        content: 'This is the first chunk of the document.',
        content_preview: 'This is the first chunk...',
        word_count: 8,
        character_count: 35,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
      {
        id: 'chunk-2',
        document_id: 'doc-1',
        chunk_index: 1,
        content: 'This is the second chunk of the document.',
        content_preview: 'This is the second chunk...',
        word_count: 8,
        character_count: 36,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ];

    it('renders document view correctly', async () => {
      (knowledgeApi.getDocument as any).mockResolvedValue(mockDocument);
      (knowledgeApi.getDocumentChunks as any).mockResolvedValue({
        document_id: 'doc-1',
        document_name: 'Test Document.pdf',
        chunks: mockChunks,
        total_chunks: mockChunks.length,
      });

      render(
        <DocumentView
          knowledgeBaseId={mockKnowledgeBaseId}
          documentId={mockDocument.id}
          document={mockDocument}
          onBack={vi.fn()}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Test Document.pdf')).toBeInTheDocument();
      });

      expect(screen.getByText('2 MB')).toBeInTheDocument();
      expect(screen.getByText('15')).toBeInTheDocument(); // chunk count
    });

    it('handles chunk search and expansion', async () => {
      (knowledgeApi.getDocument as any).mockResolvedValue(mockDocument);
      (knowledgeApi.getDocumentChunks as any).mockResolvedValue({
        document_id: 'doc-1',
        document_name: 'Test Document.pdf',
        chunks: mockChunks,
        total_chunks: mockChunks.length,
      });

      (knowledgeApi.searchChunks as any).mockResolvedValue({
        chunks: [mockChunks[0]],
        total_count: 1,
        query: 'first',
        search_time: 0.1,
        filters_applied: {},
      });

      render(
        <DocumentView
          knowledgeBaseId={mockKnowledgeBaseId}
          documentId={mockDocument.id}
          document={mockDocument}
          onBack={vi.fn()}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Test Document.pdf')).toBeInTheDocument();
      });

      // Switch to chunks view
      const chunksTab = screen.getByText('文档块');
      await userEvent.click(chunksTab);

      // Perform chunk search
      const searchInput = screen.getByPlaceholderText('搜索文档块内容...');
      await userEvent.type(searchInput, 'first');

      await waitFor(() => {
        expect(knowledgeApi.searchChunks).toHaveBeenCalledWith(
          mockKnowledgeBaseId,
          'first',
          expect.objectContaining({
            max_results: 20,
          })
        );
      });

      // Test chunk expansion
      const expandButton = screen.getByTitle('展开');
      await userEvent.click(expandButton);

      expect(screen.getByText('This is the first chunk of the document.')).toBeInTheDocument();
    });

    it('handles metadata view correctly', async () => {
      (knowledgeApi.getDocument as any).mockResolvedValue(mockDocument);

      render(
        <DocumentView
          knowledgeBaseId={mockKnowledgeBaseId}
          documentId={mockDocument.id}
          document={mockDocument}
          onBack={vi.fn()}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Test Document.pdf')).toBeInTheDocument();
      });

      // Check metadata view
      expect(screen.getByText('基本信息')).toBeInTheDocument();
      expect(screen.getByText('Test Document.pdf')).toBeInTheDocument();
      expect(screen.getByText('PDF')).toBeInTheDocument();
      expect(screen.getByText('已完成')).toBeInTheDocument();
    });
  });

  describe('KnowledgeBaseDetails Integration', () => {
    const mockKnowledgeBase: KnowledgeBase = {
      id: 1,
      name: 'Test Knowledge Base',
      description: 'A test knowledge base',
      ragflow_dataset_id: 'dataset-123',
      status: 'active',
      document_count: 5,
      total_size: 10240000,
      conversation_count: 3,
      linked_roles: [],
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    };

    it('integrates document management components', async () => {
      (knowledgeApi.getKnowledgeBaseDetails as any).mockResolvedValue({
        ...mockKnowledgeBase,
        statistics: {
          total_documents: 5,
          total_size_bytes: 10240000,
          total_chunks: 50,
        },
      });

      render(
        <KnowledgeBaseDetails
          knowledgeBaseId={mockKnowledgeBase.id}
          onBack={vi.fn()}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('文档管理')).toBeInTheDocument();
      });

      // Check document management section
      expect(screen.getByText('上传文档')).toBeInTheDocument();
      expect(screen.getByText('文档列表')).toBeInTheDocument();
    });

    it('handles empty knowledge base state', async () => {
      const emptyKnowledgeBase = {
        ...mockKnowledgeBase,
        document_count: 0,
        total_size: 0,
      };

      (knowledgeApi.getKnowledgeBaseDetails as any).mockResolvedValue({
        ...emptyKnowledgeBase,
        statistics: {
          total_documents: 0,
          total_size_bytes: 0,
          total_chunks: 0,
        },
      });

      render(
        <KnowledgeBaseDetails
          knowledgeBaseId={emptyKnowledgeBase.id}
          onBack={vi.fn()}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('暂无文档')).toBeInTheDocument();
      });

      expect(screen.getByText('上传第一个文档')).toBeInTheDocument();
    });
  });

  describe('TestConversation Document Integration', () => {
    const mockKnowledgeBase: KnowledgeBase = {
      id: 1,
      name: 'Test Knowledge Base',
      description: 'A test knowledge base',
      ragflow_dataset_id: 'dataset-123',
      status: 'active',
      document_count: 3,
      total_size: 5120000,
      conversation_count: 0,
      linked_roles: [],
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    };

    const mockDocuments: Document[] = [
      {
        id: 'doc-1',
        knowledge_base_id: '1',
        filename: 'manual.pdf',
        original_filename: 'User Manual.pdf',
        file_size: 2048000,
        file_type: 'pdf',
        mime_type: 'application/pdf',
        upload_status: 'completed',
        processing_status: 'completed',
        chunk_count: 20,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ];

    it('includes document selection in conversation', async () => {
      (knowledgeApi.getDocuments as any).mockResolvedValue({
        documents: mockDocuments,
        pagination: { page: 1, limit: 20, total: 1, has_more: false },
      });

      (knowledgeApi.testConversation as any).mockResolvedValue({
        success: true,
        data: {
          id: 'conv-123',
          user_question: 'What is in the manual?',
          ragflow_response: 'Based on the manual...',
          confidence_score: 0.95,
          created_at: '2024-01-01T00:00:00Z',
          references: { references: [] },
        },
      });

      render(
        <TestConversation
          knowledgeBase={mockKnowledgeBase}
          onBack={vi.fn()}
          onRefreshKnowledgeBase={vi.fn()}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('选择文档')).toBeInTheDocument();
      });

      // Toggle document search
      const selectDocumentsButton = screen.getByText('选择文档');
      await userEvent.click(selectDocumentsButton);

      await waitFor(() => {
        expect(screen.getByText('选择特定文档进行对话')).toBeInTheDocument();
      });

      expect(screen.getByText('User Manual.pdf')).toBeInTheDocument();

      // Select document
      const documentCheckbox = screen.getByRole('checkbox');
      await userEvent.click(documentCheckbox);

      // Send message with selected document context
      const messageInput = screen.getByPlaceholderText('输入您的问题...');
      await userEvent.type(messageInput, 'What is covered in this manual?');

      const sendButton = screen.getByText('发送');
      await userEvent.click(sendButton);

      await waitFor(() => {
        expect(knowledgeApi.testConversation).toHaveBeenCalledWith(
          mockKnowledgeBase.id,
          expect.stringContaining('User Manual.pdf'),
          expect.any(String)
        );
      });
    });
  });

  describe('Error Handling and Edge Cases', () => {
    it('handles network errors gracefully', async () => {
      (knowledgeApi.getDocuments as any).mockRejectedValue(new Error('Network error'));

      render(
        <DocumentList
          knowledgeBaseId='test-kb'
          onDocumentSelect={vi.fn()}
          onDocumentDelete={vi.fn()}
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/加载失败/)).toBeInTheDocument();
      });
    });

    it('handles empty API responses', async () => {
      (knowledgeApi.getDocuments as any).mockResolvedValue({
        documents: [],
        pagination: { page: 1, limit: 20, total: 0, has_more: false },
      });

      render(
        <DocumentList
          knowledgeBaseId='test-kb'
          onDocumentSelect={vi.fn()}
          onDocumentDelete={vi.fn()}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('暂无文档')).toBeInTheDocument();
      });
    });

    it('handles file upload cancellation', async () => {
      const mockOnUploadComplete = vi.fn();

      render(
        <DocumentUpload
          knowledgeBaseId='test-kb'
          onUploadComplete={mockOnUploadComplete}
          onUploadError={vi.fn()}
        />
      );

      // Simulate file upload
      const dropzone = screen.getByTestId('dropzone');
      const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });

      fireEvent.drop(dropzone, {
        dataTransfer: {
          files: [file],
        },
      });

      // Cancel upload
      const cancelButton = screen.getByTitle('取消');
      await userEvent.click(cancelButton);

      // Verify no completion callback was called
      expect(mockOnUploadComplete).not.toHaveBeenCalled();
    });
  });

  describe('Performance and Accessibility', () => {
    it('handles large document lists efficiently', async () => {
      // Generate many documents
      const manyDocuments = Array.from({ length: 1000 }, (_, i) => ({
        id: `doc-${i}`,
        knowledge_base_id: 'test-kb',
        filename: `document_${i}.pdf`,
        original_filename: `Document ${i}.pdf`,
        file_size: 1024000,
        file_type: 'pdf',
        mime_type: 'application/pdf',
        upload_status: 'completed' as const,
        processing_status: 'completed' as const,
        chunk_count: 10,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      }));

      (knowledgeApi.getDocuments as any).mockResolvedValue({
        documents: manyDocuments.slice(0, 20), // Paginated response
        pagination: { page: 1, limit: 20, total: 1000, has_more: true },
      });

      const startTime = performance.now();

      render(
        <DocumentList
          knowledgeBaseId='test-kb'
          onDocumentSelect={vi.fn()}
          onDocumentDelete={vi.fn()}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('文档列表')).toBeInTheDocument();
      });

      const renderTime = performance.now() - startTime;

      // Should render within reasonable time (under 1 second)
      expect(renderTime).toBeLessThan(1000);
    });

    it('provides proper accessibility attributes', () => {
      render(
        <DocumentUpload
          knowledgeBaseId='test-kb'
          onUploadComplete={vi.fn()}
          onUploadError={vi.fn()}
        />
      );

      // Check for proper ARIA labels and roles
      const dropzone = screen.getByTestId('dropzone');
      expect(dropzone).toHaveAttribute('role', 'button');
      expect(dropzone).toHaveAttribute('tabIndex', '0');

      // Check for screen reader friendly text
      expect(screen.getByText('拖放文件到这里上传')).toBeInTheDocument();
      expect(screen.getByText('或点击选择文件')).toBeInTheDocument();
    });
  });
});