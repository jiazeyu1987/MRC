/**
 * Knowledge Base System Component Tests
 *
 * This file contains comprehensive tests for the Knowledge Base System components:
 * - KnowledgeBaseList: Displays and manages knowledge base lists
 * - KnowledgeBaseDetails: Shows detailed knowledge base information
 * - TestConversation: Provides testing interface for knowledge base conversations
 *
 * Tests cover user interactions, error states, data loading, and edge cases.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';

// Mock the theme hook
jest.mock('../../theme', () => ({
  useTheme: () => ({
    theme: {
      primary: 'bg-blue-600',
      primaryHover: 'hover:bg-blue-700',
      bgSoft: 'bg-blue-50',
      text: 'text-blue-600',
      border: 'border-blue-200',
      ring: 'ring-2 ring-blue-500 ring-offset-2',
      iconBg: 'bg-blue-500',
    }
  })
}));

// Mock the error handler
jest.mock('../../utils/errorHandler', () => ({
  handleError: (error: any, showNotification = true) => {
    const message = error?.response?.data?.message || error?.message || 'An error occurred';
    return message;
  }
}));

// Mock the knowledge API
jest.mock('../../api/knowledgeApi', () => ({
  knowledgeApi: {
    getKnowledgeBases: jest.fn(),
    refreshKnowledgeBases: jest.fn(),
    refreshKnowledgeBase: jest.fn(),
    getKnowledgeBaseDetails: jest.fn(),
    testConversation: jest.fn(),
    getKnowledgeBaseStatistics: jest.fn(),
    getKnowledgeBaseConversations: jest.fn(),
  }
}));

// Import components after mocking
import KnowledgeBaseList from '../KnowledgeBaseList';
import KnowledgeBaseDetails from '../KnowledgeBaseDetails';
import TestConversation from '../TestConversation';
import { KnowledgeBase, KnowledgeBaseConversation, Reference } from '../../types/knowledge';
import { knowledgeApi } from '../../api/knowledgeApi';

// Mock data factories
const createMockKnowledgeBase = (overrides: Partial<KnowledgeBase> = {}): KnowledgeBase => ({
  id: 1,
  ragflow_dataset_id: 'ds_test123',
  name: 'Test Knowledge Base',
  description: 'A test knowledge base for testing',
  document_count: 10,
  total_size: 1024000,
  status: 'active',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-02T00:00:00Z',
  ...overrides
});

const createMockReference = (overrides: Partial<Reference> = {}): Reference => ({
  document_id: 'doc1',
  document_title: 'Test Document',
  snippet: 'This is a test snippet from the document',
  page_number: 1,
  confidence: 0.95,
  ...overrides
});

const createMockConversation = (overrides: Partial<KnowledgeBaseConversation> = {}): KnowledgeBaseConversation => ({
  id: 1,
  knowledge_base_id: 1,
  knowledge_base_name: 'Test Knowledge Base',
  title: 'Test Conversation',
  user_question: 'What is testing?',
  ragflow_response: 'Testing is a process of verifying software functionality.',
  confidence_score: 0.85,
  references: {
    references: [createMockReference()]
  },
  metadata: {},
  status: 'active',
  reference_count: 1,
  is_high_confidence: true,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:01:00Z',
  ...overrides
});

// Helper function to wait for async operations
const waitForAsync = () => act(async () => {
  await new Promise(resolve => setTimeout(resolve, 0));
});

describe('KnowledgeBaseList Component', () => {
  const defaultProps = {
    onKnowledgeBaseSelect: jest.fn(),
    selectedKnowledgeBaseId: undefined,
    multiSelect: false,
    selectedIds: new Set<number>(),
    onSelectionChange: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (knowledgeApi.getKnowledgeBases as jest.Mock).mockResolvedValue({
      knowledge_bases: [createMockKnowledgeBase()],
      total: 1,
      page: 1,
      page_size: 20,
      pages: 1,
      has_prev: false,
      has_next: false,
    });
  });

  describe('Rendering', () => {
    test('renders knowledge base list with title and refresh button', async () => {
      render(<KnowledgeBaseList {...defaultProps} />);

      expect(screen.getByText('知识库列表')).toBeInTheDocument();
      expect(screen.getByText('刷新全部')).toBeInTheDocument();
      expect(screen.getByText('Database')).toBeInTheDocument();
    });

    test('renders search input and status filter', () => {
      render(<KnowledgeBaseList {...defaultProps} />);

      expect(screen.getByPlaceholderText('搜索知识库名称或描述...')).toBeInTheDocument();
      expect(screen.getByText('全部状态')).toBeInTheDocument();
    });

    test('displays loading state while fetching data', async () => {
      (knowledgeApi.getKnowledgeBases as jest.Mock).mockImplementation(() =>
        new Promise(resolve => setTimeout(resolve, 100))
      );

      render(<KnowledgeBaseList {...defaultProps} />);

      expect(screen.getByText('加载知识库列表中...')).toBeInTheDocument();
      expect(screen.getByRole('generic', { name: /loading/i })).toBeInTheDocument();
    });

    test('displays empty state when no knowledge bases exist', async () => {
      (knowledgeApi.getKnowledgeBases as jest.Mock).mockResolvedValue({
        knowledge_bases: [],
        total: 0,
        page: 1,
        page_size: 20,
        pages: 0,
        has_prev: false,
        has_next: false,
      });

      render(<KnowledgeBaseList {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('暂无知识库')).toBeInTheDocument();
        expect(screen.getByText('点击"刷新全部"按钮从RAGFlow获取知识库')).toBeInTheDocument();
      });
    });

    test('displays knowledge base items when data is loaded', async () => {
      const mockKB = createMockKnowledgeBase({
        name: 'Test KB',
        document_count: 5,
        total_size: 2048000,
      });

      (knowledgeApi.getKnowledgeBases as jest.Mock).mockResolvedValue({
        knowledge_bases: [mockKB],
        total: 1,
        page: 1,
        page_size: 20,
        pages: 1,
        has_prev: false,
        has_next: false,
      });

      render(<KnowledgeBaseList {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Test KB')).toBeInTheDocument();
        expect(screen.getByText('5 个文档')).toBeInTheDocument();
        expect(screen.getByText(/2\.00 MB/)).toBeInTheDocument();
        expect(screen.getByText('活跃')).toBeInTheDocument();
      });
    });

    test('displays error state when API call fails', async () => {
      const errorMessage = 'Failed to fetch knowledge bases';
      (knowledgeApi.getKnowledgeBases as jest.Mock).mockRejectedValue(new Error(errorMessage));

      render(<KnowledgeBaseList {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText(errorMessage)).toBeInTheDocument();
      });
    });
  });

  describe('User Interactions', () => {
    test('handles knowledge base selection', async () => {
      const mockKB = createMockKnowledgeBase({ id: 1 });
      const mockOnSelect = jest.fn();

      (knowledgeApi.getKnowledgeBases as jest.Mock).mockResolvedValue({
        knowledge_bases: [mockKB],
        total: 1,
        page: 1,
        page_size: 20,
        pages: 1,
        has_prev: false,
        has_next: false,
      });

      render(<KnowledgeBaseList {...defaultProps} onKnowledgeBaseSelect={mockOnSelect} />);

      await waitFor(() => {
        expect(screen.getByText('Test Knowledge Base')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Test Knowledge Base'));
      expect(mockOnSelect).toHaveBeenCalledWith(mockKB);
    });

    test('handles search functionality', async () => {
      const mockOnSelect = jest.fn();
      render(<KnowledgeBaseList {...defaultProps} onKnowledgeBaseSelect={mockOnSelect} />);

      const searchInput = screen.getByPlaceholderText('搜索知识库名称或描述...');

      await userEvent.type(searchInput, 'test search');
      await waitForAsync();

      expect(knowledgeApi.getKnowledgeBases).toHaveBeenCalledWith(
        expect.objectContaining({
          search: 'test search',
          page: 1,
          page_size: 20,
        })
      );
    });

    test('handles status filter change', async () => {
      render(<KnowledgeBaseList {...defaultProps} />);

      const statusFilter = screen.getByText('全部状态');
      await userEvent.selectOptions(statusFilter, 'active');

      await waitForAsync();

      expect(knowledgeApi.getKnowledgeBases).toHaveBeenCalledWith(
        expect.objectContaining({
          status: 'active',
          page: 1,
          page_size: 20,
        })
      );
    });

    test('handles refresh all functionality', async () => {
      (knowledgeApi.refreshKnowledgeBases as jest.Mock).mockResolvedValue({
        created: 1,
        updated: 0,
        deleted: 0,
        errors: [],
      });

      render(<KnowledgeBaseList {...defaultProps} />);

      const refreshButton = screen.getByText('刷新全部');
      await userEvent.click(refreshButton);

      expect(knowledgeApi.refreshKnowledgeBases).toHaveBeenCalled();
    });

    test('handles single knowledge base refresh', async () => {
      const mockKB = createMockKnowledgeBase({ id: 1 });

      (knowledgeApi.getKnowledgeBases as jest.Mock).mockResolvedValue({
        knowledge_bases: [mockKB],
        total: 1,
        page: 1,
        page_size: 20,
        pages: 1,
        has_prev: false,
        has_next: false,
      });

      (knowledgeApi.refreshKnowledgeBase as jest.Mock).mockResolvedValue({
        action: 'updated',
        new_info: mockKB,
      });

      render(<KnowledgeBaseList {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Test Knowledge Base')).toBeInTheDocument();
      });

      const refreshButtons = screen.getAllByTitle('刷新知识库');
      await userEvent.click(refreshButtons[0]);

      expect(knowledgeApi.refreshKnowledgeBase).toHaveBeenCalledWith(1);
    });

    test('handles pagination navigation', async () => {
      const mockKBs = Array.from({ length: 25 }, (_, i) =>
        createMockKnowledgeBase({ id: i + 1, name: `KB ${i + 1}` })
      );

      (knowledgeApi.getKnowledgeBases as jest.Mock).mockResolvedValue({
        knowledge_bases: mockKBs.slice(0, 20),
        total: 25,
        page: 1,
        page_size: 20,
        pages: 2,
        has_prev: false,
        has_next: true,
      });

      render(<KnowledgeBaseList {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('下一页')).toBeInTheDocument();
      });

      const nextButton = screen.getByText('下一页');
      await userEvent.click(nextButton);

      expect(knowledgeApi.getKnowledgeBases).toHaveBeenCalledWith(
        expect.objectContaining({
          page: 2,
          page_size: 20,
        })
      );
    });
  });

  describe('Multi-select Mode', () => {
    test('renders checkboxes in multi-select mode', async () => {
      const mockKB = createMockKnowledgeBase({ id: 1 });

      (knowledgeApi.getKnowledgeBases as jest.Mock).mockResolvedValue({
        knowledge_bases: [mockKB],
        total: 1,
        page: 1,
        page_size: 20,
        pages: 1,
        has_prev: false,
        has_next: false,
      });

      render(<KnowledgeBaseList {...defaultProps} multiSelect={true} />);

      await waitFor(() => {
        expect(screen.getByRole('checkbox')).toBeInTheDocument();
      });
    });

    test('handles checkbox selection', async () => {
      const mockKB = createMockKnowledgeBase({ id: 1 });
      const mockOnSelectionChange = jest.fn();

      (knowledgeApi.getKnowledgeBases as jest.Mock).mockResolvedValue({
        knowledge_bases: [mockKB],
        total: 1,
        page: 1,
        page_size: 20,
        pages: 1,
        has_prev: false,
        has_next: false,
      });

      render(<KnowledgeBaseList
        {...defaultProps}
        multiSelect={true}
        onSelectionChange={mockOnSelectionChange}
      />);

      await waitFor(() => {
        expect(screen.getByRole('checkbox')).toBeInTheDocument();
      });

      const checkbox = screen.getByRole('checkbox');
      await userEvent.click(checkbox);

      expect(mockOnSelectionChange).toHaveBeenCalledWith(new Set([1]));
    });
  });

  describe('Edge Cases', () => {
    test('handles knowledge bases with zero documents', async () => {
      const mockKB = createMockKnowledgeBase({
        document_count: 0,
        total_size: 0,
        status: 'inactive'
      });

      (knowledgeApi.getKnowledgeBases as jest.Mock).mockResolvedValue({
        knowledge_bases: [mockKB],
        total: 1,
        page: 1,
        page_size: 20,
        pages: 1,
        has_prev: false,
        has_next: false,
      });

      render(<KnowledgeBaseList {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('0 个文档')).toBeInTheDocument();
        expect(screen.getByText('0 B')).toBeInTheDocument();
        expect(screen.getByText('未激活')).toBeInTheDocument();
      });
    });

    test('handles knowledge bases with error status', async () => {
      const mockKB = createMockKnowledgeBase({ status: 'error' });

      (knowledgeApi.getKnowledgeBases as jest.Mock).mockResolvedValue({
        knowledge_bases: [mockKB],
        total: 1,
        page: 1,
        page_size: 20,
        pages: 1,
        has_prev: false,
        has_next: false,
      });

      render(<KnowledgeBaseList {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('错误')).toBeInTheDocument();
      });
    });

    test('handles very large file sizes', async () => {
      const mockKB = createMockKnowledgeBase({
        total_size: 1024 * 1024 * 1024 * 5 // 5GB
      });

      (knowledgeApi.getKnowledgeBases as jest.Mock).mockResolvedValue({
        knowledge_bases: [mockKB],
        total: 1,
        page: 1,
        page_size: 20,
        pages: 1,
        has_prev: false,
        has_next: false,
      });

      render(<KnowledgeBaseList {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText(/5\.00 GB/)).toBeInTheDocument();
      });
    });
  });
});

describe('KnowledgeBaseDetails Component', () => {
  const defaultProps = {
    knowledgeBaseId: 1,
    onBack: jest.fn(),
    onTestConversation: jest.fn(),
  };

  const mockKnowledgeBase = createMockKnowledgeBase({
    id: 1,
    conversation_count: 5,
    linked_roles: [
      { id: 1, name: 'Teacher', prompt: 'A helpful teacher' },
      { id: 2, name: 'Student', prompt: 'An eager student' }
    ]
  });

  beforeEach(() => {
    jest.clearAllMocks();
    (knowledgeApi.getKnowledgeBaseDetails as jest.Mock).mockResolvedValue(mockKnowledgeBase);
    (knowledgeApi.refreshKnowledgeBase as jest.Mock).mockResolvedValue({
      action: 'updated',
      new_info: mockKnowledgeBase,
    });
    (knowledgeApi.testConversation as jest.Mock).mockResolvedValue(createMockConversation());
  });

  describe('Rendering', () => {
    test('renders knowledge base details', async () => {
      render(<KnowledgeBaseDetails {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Test Knowledge Base')).toBeInTheDocument();
        expect(screen.getByText('A test knowledge base for testing')).toBeInTheDocument();
        expect(screen.getByText('活跃')).toBeInTheDocument();
      });
    });

    test('displays loading state', () => {
      (knowledgeApi.getKnowledgeBaseDetails as jest.Mock).mockImplementation(() =>
        new Promise(resolve => setTimeout(resolve, 100))
      );

      render(<KnowledgeBaseDetails {...defaultProps} />);

      expect(screen.getByText('加载知识库详情中...')).toBeInTheDocument();
    });

    test('displays error state when knowledge base not found', async () => {
      (knowledgeApi.getKnowledgeBaseDetails as jest.Mock).mockRejectedValue(new Error('Knowledge base not found'));

      render(<KnowledgeBaseDetails {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Knowledge base not found')).toBeInTheDocument();
        expect(screen.getByText('返回列表')).toBeInTheDocument();
      });
    });

    test('displays statistics cards', async () => {
      render(<KnowledgeBaseDetails {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('文档数量')).toBeInTheDocument();
        expect(screen.getByText('10')).toBeInTheDocument();
        expect(screen.getByText('总大小')).toBeInTheDocument();
        expect(screen.getByText(/1\.00 MB/)).toBeInTheDocument();
        expect(screen.getByText('对话数量')).toBeInTheDocument();
        expect(screen.getByText('5')).toBeInTheDocument();
        expect(screen.getByText('关联角色')).toBeInTheDocument();
        expect(screen.getByText('2')).toBeInTheDocument();
      });
    });

    test('displays warning when no documents exist', async () => {
      const kbWithoutDocs = createMockKnowledgeBase({
        id: 1,
        document_count: 0,
        conversation_count: 2
      });

      (knowledgeApi.getKnowledgeBaseDetails as jest.Mock).mockResolvedValue(kbWithoutDocs);

      render(<KnowledgeBaseDetails {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText(/此知识库当前没有已解析的文档/)).toBeInTheDocument();
        expect(screen.getByText(/知识库中没有已解析的文档，无法进行测试对话/)).toBeInTheDocument();
      });
    });

    test('displays linked roles when available', async () => {
      render(<KnowledgeBaseDetails {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('关联角色')).toBeInTheDocument();
        expect(screen.getByText('Teacher')).toBeInTheDocument();
        expect(screen.getByText('A helpful teacher')).toBeInTheDocument();
        expect(screen.getByText('Student')).toBeInTheDocument();
        expect(screen.getByText('An eager student')).toBeInTheDocument();
      });
    });
  });

  describe('User Interactions', () => {
    test('handles back button click', async () => {
      const mockOnBack = jest.fn();
      render(<KnowledgeBaseDetails {...defaultProps} onBack={mockOnBack} />);

      await waitFor(() => {
        expect(screen.getByText('返回列表')).toBeInTheDocument();
      });

      await userEvent.click(screen.getByText('返回列表'));
      expect(mockOnBack).toHaveBeenCalled();
    });

    test('handles refresh functionality', async () => {
      render(<KnowledgeBaseDetails {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('刷新')).toBeInTheDocument();
      });

      await userEvent.click(screen.getByText('刷新'));
      expect(knowledgeApi.refreshKnowledgeBase).toHaveBeenCalledWith(1);
    });

    test('handles test conversation submission', async () => {
      render(<KnowledgeBaseDetails {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByPlaceholderText('请输入您的问题...')).toBeInTheDocument();
      });

      const testInput = screen.getByPlaceholderText('请输入您的问题...');
      const testButton = screen.getByText('发送问题');

      await userEvent.type(testInput, 'What is testing?');
      await userEvent.click(testButton);

      expect(knowledgeApi.testConversation).toHaveBeenCalledWith(
        1,
        'What is testing?',
        '测试对话 - Test Knowledge Base'
      );
    });

    test('handles test conversation with Enter key', async () => {
      render(<KnowledgeBaseDetails {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByPlaceholderText('请输入您的问题...')).toBeInTheDocument();
      });

      const testInput = screen.getByPlaceholderText('请输入您的问题...');

      await userEvent.type(testInput, 'What is testing?{enter}');

      expect(knowledgeApi.testConversation).toHaveBeenCalledWith(
        1,
        'What is testing?',
        '测试对话 - Test Knowledge Base'
      );
    });

    test('disables test input when no documents exist', async () => {
      const kbWithoutDocs = createMockKnowledgeBase({ document_count: 0 });
      (knowledgeApi.getKnowledgeBaseDetails as jest.Mock).mockResolvedValue(kbWithoutDocs);

      render(<KnowledgeBaseDetails {...defaultProps} />);

      await waitFor(() => {
        const testInput = screen.getByPlaceholderText('请输入您的问题...');
        expect(testInput).toBeDisabled();
        expect(screen.getByText('发送问题')).toBeDisabled();
      });
    });
  });

  describe('Edge Cases', () => {
    test('handles missing description', async () => {
      const kbWithoutDescription = createMockKnowledgeBase({ description: undefined });
      (knowledgeApi.getKnowledgeBaseDetails as jest.Mock).mockResolvedValue(kbWithoutDescription);

      render(<KnowledgeBaseDetails {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Test Knowledge Base')).toBeInTheDocument();
        expect(screen.queryByText('A test knowledge base for testing')).not.toBeInTheDocument();
      });
    });

    test('handles missing updated_at timestamp', async () => {
      const kbWithoutUpdatedAt = { ...mockKnowledgeBase, updated_at: undefined };
      (knowledgeApi.getKnowledgeBaseDetails as jest.Mock).mockResolvedValue(kbWithoutUpdatedAt);

      render(<KnowledgeBaseDetails {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Test Knowledge Base')).toBeInTheDocument();
        expect(screen.queryByText(/更新于/)).not.toBeInTheDocument();
      });
    });

    test('handles knowledge base with error status', async () => {
      const kbWithError = createMockKnowledgeBase({ status: 'error' });
      (knowledgeApi.getKnowledgeBaseDetails as jest.Mock).mockResolvedValue(kbWithError);

      render(<KnowledgeBaseDetails {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('错误')).toBeInTheDocument();
      });
    });
  });
});

describe('TestConversation Component', () => {
  const mockKnowledgeBase = createMockKnowledgeBase({
    id: 1,
    name: 'Test KB',
    document_count: 10
  });

  const defaultProps = {
    knowledgeBase: mockKnowledgeBase,
    onBack: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (knowledgeApi.testConversation as jest.Mock).mockResolvedValue(createMockConversation({
      ragflow_response: 'This is a test response',
      confidence_score: 0.9,
      references: {
        references: [createMockReference()]
      }
    }));
  });

  describe('Rendering', () => {
    test('renders conversation interface with knowledge base info', () => {
      render(<TestConversation {...defaultProps} />);

      expect(screen.getByText('测试对话 - Test KB')).toBeInTheDocument();
      expect(screen.getByText('知识库ID: ds_test123')).toBeInTheDocument();
      expect(screen.getByText('文档数: 10')).toBeInTheDocument();
    });

    test('displays empty state when no messages', () => {
      render(<TestConversation {...defaultProps} />);

      expect(screen.getByText('开始测试对话')).toBeInTheDocument();
      expect(screen.getByText('输入您的问题来测试知识库的回答能力')).toBeInTheDocument();
    });

    test('renders initial conversation when provided', () => {
      const mockConversation = createMockConversation({
        user_question: 'What is testing?',
        ragflow_response: 'Testing is important'
      });

      render(<TestConversation {...defaultProps} conversation={mockConversation} />);

      expect(screen.getByText('What is testing?')).toBeInTheDocument();
      expect(screen.getByText('Testing is important')).toBeInTheDocument();
    });

    test('disables input when knowledge base has no documents', () => {
      const kbWithoutDocs = createMockKnowledgeBase({ document_count: 0 });

      render(<TestConversation {...defaultProps} knowledgeBase={kbWithoutDocs} />);

      expect(screen.getByPlaceholderText('输入您的问题...')).toBeDisabled();
      expect(screen.getByText('发送')).toBeDisabled();
      expect(screen.getByText(/知识库中没有已解析的文档/)).toBeInTheDocument();
    });
  });

  describe('User Interactions', () => {
    test('handles sending a message', async () => {
      render(<TestConversation {...defaultProps} />);

      const input = screen.getByPlaceholderText('输入您的问题...');
      const sendButton = screen.getByText('发送');

      await userEvent.type(input, 'What is testing?');
      await userEvent.click(sendButton);

      expect(screen.getByText('What is testing?')).toBeInTheDocument();
      expect(knowledgeApi.testConversation).toHaveBeenCalledWith(
        1,
        'What is testing?',
        expect.stringContaining('测试对话 - ')
      );
    });

    test('handles sending message with Enter key', async () => {
      render(<TestConversation {...defaultProps} />);

      const input = screen.getByPlaceholderText('输入您的问题...');

      await userEvent.type(input, 'What is testing?{enter}');

      expect(screen.getByText('What is testing?')).toBeInTheDocument();
      expect(knowledgeApi.testConversation).toHaveBeenCalled();
    });

    test('handles sending message with Shift+Enter for new line', async () => {
      render(<TestConversation {...defaultProps} />);

      const input = screen.getByPlaceholderText('输入您的问题...');

      await userEvent.type(input, 'What is testing?{shift>}{enter}{/shift}More details');

      expect(input).toHaveValue('What is testing?\nMore details');
    });

    test('handles back button click', async () => {
      const mockOnBack = jest.fn();
      render(<TestConversation {...defaultProps} onBack={mockOnBack} />);

      const backButton = screen.getByRole('button').closest('button');
      await userEvent.click(backButton!);

      expect(mockOnBack).toHaveBeenCalled();
    });

    test('handles message copying', async () => {
      Object.assign(navigator, {
        clipboard: {
          writeText: jest.fn().mockResolvedValue(undefined),
        },
      });

      render(<TestConversation {...defaultProps} />);

      const input = screen.getByPlaceholderText('输入您的问题...');
      await userEvent.type(input, 'Test message{enter}');

      await waitFor(() => {
        expect(screen.getByText('Test message')).toBeInTheDocument();
      });

      const copyButtons = screen.getAllByText('复制');
      await userEvent.click(copyButtons[0]);

      expect(navigator.clipboard.writeText).toHaveBeenCalledWith('Test message');
      expect(screen.getByText('已复制')).toBeInTheDocument();
    });

    test('handles conversation export', async () => {
      const mockConversation = createMockConversation();
      render(<TestConversation {...defaultProps} conversation={mockConversation} />);

      // Mock the download functionality
      const mockCreateObjectURL = jest.fn().mockReturnValue('blob:url');
      global.URL.createObjectURL = mockCreateObjectURL;
      global.URL.revokeObjectURL = jest.fn();

      const createElementSpy = jest.spyOn(document, 'createElement');
      const mockAnchor = { click: jest.fn() };
      createElementSpy.mockReturnValue(mockAnchor as any);

      const exportButton = screen.getByText('导出');
      await userEvent.click(exportButton);

      expect(createElementSpy).toHaveBeenCalledWith('a');
      expect(mockAnchor.click).toHaveBeenCalled();
    });

    test('handles conversation history clear', async () => {
      const mockConversation = createMockConversation();

      // Mock window.confirm
      window.confirm = jest.fn(() => true);

      render(<TestConversation {...defaultProps} conversation={mockConversation} />);

      const clearButton = screen.getByText('清空');
      await userEvent.click(clearButton);

      expect(window.confirm).toHaveBeenCalledWith('确定要清空对话历史吗？');
      expect(screen.queryByText('What is testing?')).not.toBeInTheDocument();
    });

    test('handles references toggle', async () => {
      const mockConversation = createMockConversation({
        ragflow_response: 'Test response',
        references: {
          references: [createMockReference()]
        }
      });

      render(<TestConversation {...defaultProps} conversation={mockConversation} />);

      const referencesButton = screen.getByText(/参考来源 \(1\)/);
      await userEvent.click(referencesButton);

      expect(screen.getByText('参考来源')).toBeInTheDocument();
      expect(screen.getByText('Test Document')).toBeInTheDocument();
      expect(screen.getByText('This is a test snippet from the document')).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    test('handles API errors during message sending', async () => {
      (knowledgeApi.testConversation as jest.Mock).mockRejectedValue(new Error('API Error'));

      render(<TestConversation {...defaultProps} />);

      const input = screen.getByPlaceholderText('输入您的问题...');
      await userEvent.type(input, 'Test question{enter}');

      await waitFor(() => {
        expect(screen.getByText(/发生错误：API Error/)).toBeInTheDocument();
      });
    });

    test('handles clipboard copy failure', async () => {
      Object.assign(navigator, {
        clipboard: {
          writeText: jest.fn().mockRejectedValue(new Error('Copy failed')),
        },
      });

      render(<TestConversation {...defaultProps} />);

      const input = screen.getByPlaceholderText('输入您的问题...');
      await userEvent.type(input, 'Test message{enter}');

      await waitFor(() => {
        const copyButtons = screen.getAllByText('复制');
        expect(copyButtons[0]).toBeInTheDocument();
      });

      const copyButtons = screen.getAllByText('复制');
      await userEvent.click(copyButtons[0]);

      // Should handle error gracefully
      expect(screen.queryByText('已复制')).not.toBeInTheDocument();
    });
  });

  describe('Message Display', () => {
    test('displays confidence scores correctly', async () => {
      const mockConversation = createMockConversation({
        confidence_score: 0.85
      });

      render(<TestConversation {...defaultProps} conversation={mockConversation} />);

      expect(screen.getByText('置信度: 85.0%')).toBeInTheDocument();
    });

    test('applies correct confidence colors', async () => {
      const highConfidenceConversation = createMockConversation({ confidence_score: 0.9 });
      const lowConfidenceConversation = createMockConversation({ confidence_score: 0.4 });

      const { rerender } = render(<TestConversation {...defaultProps} conversation={highConfidenceConversation} />);

      expect(screen.getByText('置信度: 90.0%')).toHaveClass('text-green-600');

      rerender(<TestConversation {...defaultProps} conversation={lowConfidenceConversation} />);

      expect(screen.getByText('置信度: 40.0%')).toHaveClass('text-red-600');
    });

    test('displays unknown confidence when undefined', async () => {
      const mockConversation = createMockConversation({ confidence_score: undefined });

      render(<TestConversation {...defaultProps} conversation={mockConversation} />);

      expect(screen.getByText('置信度: 未知')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    test('handles empty response from API', async () => {
      (knowledgeApi.testConversation as jest.Mock).mockResolvedValue(createMockConversation({
        ragflow_response: ''
      }));

      render(<TestConversation {...defaultProps} />);

      const input = screen.getByPlaceholderText('输入您的问题...');
      await userEvent.type(input, 'Test{enter}');

      await waitFor(() => {
        expect(screen.getByText('')).toBeInTheDocument();
      });
    });

    test('handles conversation without references', async () => {
      const mockConversation = createMockConversation({
        references: undefined
      });

      render(<TestConversation {...defaultProps} conversation={mockConversation} />);

      expect(screen.queryByText(/参考来源/)).not.toBeInTheDocument();
    });

    test('handles very long messages', async () => {
      const longMessage = 'A'.repeat(1000);

      render(<TestConversation {...defaultProps} />);

      const input = screen.getByPlaceholderText('输入您的问题...');
      await userEvent.type(input, longMessage);
      await userEvent.click(screen.getByText('发送'));

      expect(screen.getByText(longMessage)).toBeInTheDocument();
    });
  });
});