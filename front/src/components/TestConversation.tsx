import React, { useState, useEffect, useRef } from 'react';
import {
  Send,
  Download,
  Trash2,
  MessageCircle,
  ExternalLink,
  FileText,
  Copy,
  CheckCircle,
  AlertTriangle,
  Loader2,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { useTheme } from '../theme';
import { knowledgeApi } from '../api/knowledgeApi';
import { KnowledgeBase, KnowledgeBaseConversation, Reference } from '../types/knowledge';
import { handleError } from '../utils/errorHandler';

interface TestConversationProps {
  knowledgeBase: KnowledgeBase;
  conversation?: KnowledgeBaseConversation;
  onBack?: () => void;
}

interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: string;
  isStreaming?: boolean;
  references?: Reference[];
  confidence?: number;
}

const TestConversation: React.FC<TestConversationProps> = ({
  knowledgeBase,
  conversation,
  onBack
}) => {
  const { theme } = useTheme();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState<ChatMessage | null>(null);
  const [showReferences, setShowReferences] = useState<Record<string, boolean>>({});
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Initialize with conversation if provided
  useEffect(() => {
    if (conversation) {
      const initialMessages: ChatMessage[] = [
        {
          id: 'user-1',
          type: 'user',
          content: conversation.user_question,
          timestamp: conversation.created_at,
        },
        {
          id: 'assistant-1',
          type: 'assistant',
          content: conversation.ragflow_response || '暂无回答',
          timestamp: conversation.updated_at || conversation.created_at,
          references: conversation.references?.references || [],
          confidence: conversation.confidence_score,
        }
      ];
      setMessages(initialMessages);
    } else {
      setMessages([]);
    }
  }, [conversation]);

  // Auto scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingMessage]);

  // Handle sending a new message
  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      type: 'user',
      content: inputValue.trim(),
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    // Create streaming message placeholder
    const assistantMessageId = `assistant-${Date.now()}`;
    const streamingAssistantMessage: ChatMessage = {
      id: assistantMessageId,
      type: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
      isStreaming: true,
    };
    setStreamingMessage(streamingAssistantMessage);

    try {
      // Create abort controller for this request
      abortControllerRef.current = new AbortController();

      // Call the knowledge API for test conversation
      const response = await knowledgeApi.testConversation(
        knowledgeBase.id,
        inputValue.trim(),
        `测试对话 - ${new Date().toLocaleString('zh-CN')}`
      );

      // Replace streaming message with actual response
      const finalAssistantMessage: ChatMessage = {
        id: assistantMessageId,
        type: 'assistant',
        content: response.ragflow_response || '抱歉，无法获取回答。',
        timestamp: response.created_at,
        references: response.references?.references || [],
        confidence: response.confidence_score,
        isStreaming: false,
      };

      setStreamingMessage(null);
      setMessages(prev => [...prev, finalAssistantMessage]);

    } catch (error) {
      // Handle error
      const errorMessage: ChatMessage = {
        id: assistantMessageId,
        type: 'assistant',
        content: `发生错误：${handleError(error, false)}`,
        timestamp: new Date().toISOString(),
        isStreaming: false,
      };
      setStreamingMessage(null);
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  };

  // Handle clearing conversation history
  const handleClearHistory = () => {
    if (confirm('确定要清空对话历史吗？')) {
      setMessages([]);
      setStreamingMessage(null);
    }
  };

  // Handle exporting conversation
  const handleExportConversation = () => {
    const exportData = {
      knowledge_base: {
        id: knowledgeBase.id,
        name: knowledgeBase.name,
        description: knowledgeBase.description,
      },
      conversation: messages.map(msg => ({
        type: msg.type,
        content: msg.content,
        timestamp: msg.timestamp,
        confidence: msg.confidence,
        references: msg.references,
      })),
      export_time: new Date().toISOString(),
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `conversation_${knowledgeBase.name}_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Handle copying message content
  const handleCopyMessage = async (message: ChatMessage) => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopiedMessageId(message.id);
      setTimeout(() => setCopiedMessageId(null), 2000);
    } catch (error) {
      console.error('Failed to copy message:', error);
    }
  };

  // Toggle references visibility
  const toggleReferences = (messageId: string) => {
    setShowReferences(prev => ({
      ...prev,
      [messageId]: !prev[messageId]
    }));
  };

  // Format confidence score
  const formatConfidence = (confidence?: number): string => {
    if (confidence === undefined) return '未知';
    return `${(confidence * 100).toFixed(1)}%`;
  };

  // Get confidence color
  const getConfidenceColor = (confidence?: number): string => {
    if (!confidence) return 'text-gray-500';
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-amber-600';
    return 'text-red-600';
  };

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col bg-white rounded-xl overflow-hidden border border-gray-300 shadow-lg">
      {/* Header */}
      <div className={`${theme.bgSoft} border-b px-6 py-4 flex justify-between items-center shrink-0`}>
        <div className="flex items-center gap-4">
          {onBack && (
            <button
              onClick={onBack}
              className="p-2 hover:bg-gray-100 rounded-full transition-colors"
            >
              <ExternalLink className="w-4 h-4 rotate-180" />
            </button>
          )}
          <div>
            <h1 className="font-bold text-gray-900 flex items-center gap-2">
              <MessageCircle className="w-5 h-5 text-blue-500" />
              测试对话 - {knowledgeBase.name}
            </h1>
            <div className="text-xs text-gray-500 mt-1">
              知识库ID: {knowledgeBase.ragflow_dataset_id} |
              文档数: {knowledgeBase.document_count}
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleExportConversation}
            disabled={messages.length === 0}
            className={`inline-flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
              messages.length === 0
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
            }`}
          >
            <Download size={14} />
            导出
          </button>
          <button
            onClick={handleClearHistory}
            disabled={messages.length === 0}
            className={`inline-flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
              messages.length === 0
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-red-50 border border-red-200 text-red-600 hover:bg-red-100'
            }`}
          >
            <Trash2 size={14} />
            清空
          </button>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 && !streamingMessage && (
          <div className="text-center text-gray-400 py-20">
            <MessageCircle className="w-16 h-16 mx-auto mb-4 opacity-50" />
            <p className="text-lg mb-2">开始测试对话</p>
            <p className="text-sm">输入您的问题来测试知识库的回答能力</p>
          </div>
        )}

        {/* Render messages */}
        {[...messages, ...(streamingMessage ? [streamingMessage] : [])].map((message) => (
          <div
            key={message.id}
            className={`flex gap-4 max-w-4xl ${message.type === 'user' ? 'ml-auto' : ''}`}
          >
            {message.type === 'assistant' && (
              <div className={`w-8 h-8 rounded-full ${theme.iconBg} flex items-center justify-center shrink-0`}>
                <MessageCircle className="w-4 h-4 text-white" />
              </div>
            )}

            <div className={`space-y-2 ${message.type === 'user' ? 'text-right' : ''}`}>
              <div className="flex items-center gap-2 text-xs text-gray-500">
                <span className="font-medium">
                  {message.type === 'user' ? '用户' : '知识库助手'}
                </span>
                <span>•</span>
                <span>{new Date(message.timestamp).toLocaleTimeString('zh-CN')}</span>
                {message.type === 'assistant' && message.confidence !== undefined && (
                  <>
                    <span>•</span>
                    <span className={`font-medium ${getConfidenceColor(message.confidence)}`}>
                      置信度: {formatConfidence(message.confidence)}
                    </span>
                  </>
                )}
              </div>

              <div
                className={`px-4 py-3 rounded-2xl shadow-sm max-w-3xl ${
                  message.type === 'user'
                    ? `${theme.bgSoft} ${theme.text} rounded-tr-none`
                    : 'bg-gray-50 text-gray-900 rounded-tl-none border border-gray-200'
                } ${message.isStreaming ? 'animate-pulse' : ''}`}
              >
                <div className="text-sm leading-relaxed whitespace-pre-wrap">
                  {message.content}
                  {message.isStreaming && <span className="inline-block w-2 h-4 bg-gray-400 animate-pulse ml-1" />}
                </div>
              </div>

              {/* Message Actions */}
              <div className={`flex items-center gap-2 ${message.type === 'user' ? 'justify-end' : ''}`}>
                <button
                  onClick={() => handleCopyMessage(message)}
                  className={`inline-flex items-center gap-1 text-xs ${theme.text} hover:opacity-80 transition-opacity`}
                >
                  {copiedMessageId === message.id ? (
                    <>
                      <CheckCircle size={12} />
                      已复制
                    </>
                  ) : (
                    <>
                      <Copy size={12} />
                      复制
                    </>
                  )}
                </button>

                {/* References for assistant messages */}
                {message.type === 'assistant' && message.references && message.references.length > 0 && (
                  <button
                    onClick={() => toggleReferences(message.id)}
                    className={`inline-flex items-center gap-1 text-xs ${theme.text} hover:opacity-80 transition-opacity`}
                  >
                    <FileText size={12} />
                    参考来源 ({message.references.length})
                    {showReferences[message.id] ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                  </button>
                )}
              </div>

              {/* References Section */}
              {message.type === 'assistant' && message.references && message.references.length > 0 && showReferences[message.id] && (
                <div className="mt-3 space-y-2 bg-amber-50 border border-amber-200 rounded-lg p-3">
                  <div className="flex items-center gap-2 text-sm font-medium text-amber-800">
                    <FileText size={14} />
                    参考来源
                  </div>
                  <div className="space-y-2">
                    {message.references.map((ref, index) => (
                      <div key={index} className="text-xs bg-white rounded border border-amber-100 p-2">
                        <div className="font-medium text-amber-900 mb-1">
                          {ref.document_title}
                          {ref.page_number && <span className="text-amber-600"> (第{ref.page_number}页)</span>}
                        </div>
                        <div className="text-amber-700 line-clamp-3">{ref.snippet}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {message.type === 'user' && (
              <div className="w-8 h-8 rounded-full bg-gray-400 flex items-center justify-center shrink-0">
                <span className="text-white text-sm font-medium">U</span>
              </div>
            )}
          </div>
        ))}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t bg-white p-4 shrink-0">
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              placeholder="输入您的问题..."
              disabled={isLoading || knowledgeBase.document_count === 0}
              rows={1}
              className={`w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg resize-none focus:outline-none ${theme.ring} transition-colors disabled:bg-gray-100 disabled:cursor-not-allowed`}
              style={{ minHeight: '48px', maxHeight: '120px' }}
            />
          </div>
          <button
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isLoading || knowledgeBase.document_count === 0}
            className={`px-6 py-3 text-sm font-medium text-white rounded-lg transition-colors flex items-center ${
              !inputValue.trim() || isLoading || knowledgeBase.document_count === 0
                ? 'bg-gray-300 cursor-not-allowed'
                : `${theme.primary} ${theme.primaryHover}`
            }`}
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                发送中...
              </>
            ) : (
              <>
                <Send className="w-4 h-4 mr-2" />
                发送
              </>
            )}
          </button>
        </div>

        {knowledgeBase.document_count === 0 && (
          <div className="mt-3 p-3 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-600 mt-0.5 shrink-0" />
            <p className="text-sm text-amber-700">
              知识库中没有已解析的文档，无法进行测试对话。请先在RAGFlow中上传并解析相关文档。
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default TestConversation;