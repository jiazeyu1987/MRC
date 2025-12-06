# 技术实现方案

## 实现策略

基于"简单实现"的原则，采用最直接的技术方案：
- 前端状态管理：简单的全局管理器类
- 组件通信：订阅者模式
- UI集成：直接在现有SessionTheater组件中添加面板

## 核心技术方案

### 1. 调试面板管理器实现

```typescript
// src/utils/debugPanelManager.ts
interface LLMDebugCall {
  id: string;
  timestamp: number;
  prompt: string;
  response: string;
  sessionId: string;
  model: string;
  duration?: number;
}

interface DebugPanelState {
  calls: LLMDebugCall[];
  isVisible: boolean;
}

class DebugPanelManager {
  private static instance: DebugPanelManager;
  private state: DebugPanelState = {
    calls: [],
    isVisible: true
  };
  private listeners: Set<() => void> = new Set();
  private maxRecords: number = 20;

  static getInstance(): DebugPanelManager {
    if (!DebugPanelManager.instance) {
      DebugPanelManager.instance = new DebugPanelManager();
    }
    return DebugPanelManager.instance;
  }

  // 添加新的LLM调用（开始时）
  addPendingCall(prompt: string, sessionId: string, model: string = 'claude'): string {
    const id = Date.now().toString() + Math.random().toString(36).substr(2, 9);
    const call: LLMDebugCall = {
      id,
      timestamp: Date.now(),
      prompt,
      response: '等待响应...',
      sessionId,
      model
    };

    this.state.calls.push(call);

    // 限制记录数量
    if (this.state.calls.length > this.maxRecords) {
      this.state.calls = this.state.calls.slice(-this.maxRecords);
    }

    this.notifyListeners();
    return id;
  }

  // 更新LLM调用结果（完成时）
  updateCall(id: string, response: string, duration?: number) {
    const call = this.state.calls.find(c => c.id === id);
    if (call) {
      call.response = response;
      if (duration !== undefined) {
        call.duration = duration;
      }
      this.notifyListeners();
    }
  }

  // 获取当前状态
  getState(): DebugPanelState {
    return { ...this.state };
  }

  // 订阅状态变化
  subscribe(listener: () => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  // 清空记录
  clearCalls() {
    this.state.calls = [];
    this.notifyListeners();
  }

  // 通知所有订阅者
  private notifyListeners() {
    this.listeners.forEach(listener => listener());
  }
}

export { DebugPanelManager, LLMDebugCall };
```

### 2. LLM调用拦截器

```typescript
// src/api/llmApiInterceptor.ts
import { DebugPanelManager } from '../utils/debugPanelManager';

// 原始LLM API函数（假设存在）
async function originalGenerateResponse(prompt: string, options?: any): Promise<string> {
  // 这里是实际的LLM调用逻辑
  const response = await fetch('/api/llm/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt, ...options })
  });
  const data = await response.json();
  return data.response;
}

// 带调试功能的LLM调用函数
export async function generateResponseWithDebug(
  prompt: string,
  sessionId: string,
  options?: any
): Promise<string> {
  const manager = DebugPanelManager.getInstance();

  // 记录调用开始
  const callId = manager.addPendingCall(prompt, sessionId);

  const startTime = Date.now();

  try {
    // 调用原始LLM函数
    const response = await originalGenerateResponse(prompt, options);
    const duration = Date.now() - startTime;

    // 更新调试信息
    manager.updateCall(callId, response, duration);

    return response;
  } catch (error) {
    const duration = Date.now() - startTime;
    const errorMessage = error instanceof Error ? error.message : '未知错误';

    // 记录错误信息
    manager.updateCall(callId, `错误: ${errorMessage}`, duration);

    throw error;
  }
}
```

### 3. LLM调试面板组件

```typescript
// src/components/LLMDebugPanel.tsx
import React, { useState, useEffect } from 'react';
import { DebugPanelManager, LLMDebugCall } from '../utils/debugPanelManager';

export function LLMDebugPanel() {
  const [state, setState] = useState(DebugPanelManager.getState());

  useEffect(() => {
    const manager = DebugPanelManager.getInstance();

    const updateState = () => {
      setState(manager.getState());
    };

    // 订阅状态变化
    const unsubscribe = manager.subscribe(updateState);

    // 初始化状态
    updateState();

    return unsubscribe;
  }, []);

  const handleClear = () => {
    DebugPanelManager.getInstance().clearCalls();
  };

  if (!state.isVisible) {
    return null;
  }

  return (
    <div className="llm-debug-panel bg-white border-l border-gray-200 h-full flex flex-col">
      {/* 面板头部 */}
      <div className="debug-header p-3 border-b border-gray-200 bg-gray-50">
        <div className="flex justify-between items-center">
          <h3 className="text-sm font-medium text-gray-900">LLM 调试</h3>
          <div className="flex gap-2">
            <span className="text-xs text-gray-500">
              {state.calls.length} 条记录
            </span>
            <button
              onClick={handleClear}
              className="text-xs text-gray-500 hover:text-gray-700"
            >
              清空
            </button>
          </div>
        </div>
      </div>

      {/* 调试内容 */}
      <div className="debug-content flex-1 overflow-y-auto">
        {state.calls.length === 0 ? (
          <div className="p-4 text-center text-gray-500 text-sm">
            暂无LLM调用记录
          </div>
        ) : (
          <div className="space-y-3 p-3">
            {state.calls.map((call) => (
              <DebugCallItem key={call.id} call={call} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function DebugCallItem({ call }: { call: LLMDebugCall }) {
  const [expanded, setExpanded] = useState(false);

  const formatTime = (timestamp: number) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  const getStatusColor = (response: string) => {
    if (response === '等待响应...') return 'text-yellow-600';
    if (response.startsWith('错误:')) return 'text-red-600';
    return 'text-green-600';
  };

  return (
    <div className="debug-call-item border border-gray-200 rounded-lg p-3">
      {/* 调用头部信息 */}
      <div className="flex justify-between items-center mb-2">
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">
            {formatTime(call.timestamp)}
          </span>
          <span className="text-xs bg-gray-100 px-2 py-1 rounded">
            {call.model}
          </span>
          {call.duration && (
            <span className="text-xs text-gray-500">
              {call.duration}ms
            </span>
          )}
        </div>
        <span className={`text-xs font-medium ${getStatusColor(call.response)}`}>
          {call.response === '等待响应...' ? '进行中' :
           call.response.startsWith('错误:') ? '失败' : '完成'}
        </span>
      </div>

      {/* 可折叠的内容 */}
      <div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-xs text-blue-600 hover:text-blue-800 mb-2"
        >
          {expanded ? '收起' : '展开'} 详情
        </button>

        {expanded && (
          <div className="space-y-2">
            {/* 提示词 */}
            <div>
              <h4 className="text-xs font-medium text-gray-700 mb-1">提示词:</h4>
              <div className="text-xs bg-gray-50 p-2 rounded border text-gray-800 max-h-32 overflow-y-auto">
                {call.prompt}
              </div>
            </div>

            {/* 响应 */}
            <div>
              <h4 className="text-xs font-medium text-gray-700 mb-1">响应:</h4>
              <div className={`text-xs p-2 rounded border max-h-32 overflow-y-auto ${
                call.response.startsWith('错误:') ? 'bg-red-50 text-red-800' : 'bg-green-50 text-gray-800'
              }`}>
                {call.response}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
```

### 4. 会话剧场集成

```typescript
// 修改 src/components/SessionTheater.tsx
import React from 'react';
import { LLMDebugPanel } from './LLMDebugPanel';

interface SessionTheaterProps {
  session: Session;
  messages: Message[];
  onSendMessage: (content: string) => void;
  isLoading?: boolean;
}

export function SessionTheater({
  session,
  messages,
  onSendMessage,
  isLoading
}: SessionTheaterProps) {
  return (
    <div className="flex h-full">
      {/* 左侧主会话区域 */}
      <div className="flex-1 flex flex-col">
        {/* 会话头部 */}
        <div className="bg-white border-b px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                {session.name}
              </h3>
              <p className="text-sm text-gray-500">
                状态: {getStatusText(session.status)}
              </p>
            </div>
            {/* 其他头部内容 */}
          </div>
        </div>

        {/* 消息列表 */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}
          {isLoading && <LoadingSpinner />}
        </div>

        {/* 消息输入框 */}
        <div className="bg-white border-t px-6 py-4">
          <MessageInput onSendMessage={onSendMessage} />
        </div>
      </div>

      {/* 右侧调试面板 - 新增 */}
      <div className="w-80 border-l border-gray-200">
        <LLMDebugPanel />
      </div>
    </div>
  );
}
```

### 5. 会话管理API修改

```typescript
// 修改 src/api/sessionApi.ts 或相关的LLM调用文件
import { generateResponseWithDebug } from './llmApiInterceptor';

// 在会话步骤执行函数中使用调试版本
export async function runNextStep(sessionId: number): Promise<ApiResponse<StepExecutionResult>> {
  try {
    // 获取当前步骤信息
    const sessionResponse = await apiClient.get<Session>(`/sessions/${sessionId}`);
    if (!sessionResponse.success) {
      throw new Error('获取会话信息失败');
    }

    const session = sessionResponse.data!;
    const currentStep = getCurrentStep(session); // 获取当前步骤

    // 构建LLM提示词
    const prompt = buildPrompt(session, currentStep);

    // 使用带调试功能的LLM调用
    const response = await generateResponseWithDebug(
      prompt,
      sessionId.toString(),
      'claude-3-sonnet'
    );

    // 处理响应并更新会话状态
    const result = await processLLMResponse(sessionId, response);

    return {
      success: true,
      data: result
    };

  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : '执行步骤失败'
    };
  }
}

function buildPrompt(session: Session, step: FlowStep): string {
  // 构建完整的提示词逻辑
  let prompt = `角色: ${step.speaker_role_ref}\n`;
  prompt += `任务: ${step.task_type}\n`;
  prompt += `描述: ${step.description}\n\n`;

  if (step.context_scope !== 'none') {
    prompt += `上下文:\n${getRelevantContext(session, step.context_scope)}\n\n`;
  }

  prompt += '请生成合适的回应:';

  return prompt;
}
```

## 实现步骤

### 第一步：创建调试管理器
1. 创建 `src/utils/debugPanelManager.ts`
2. 实现基础的调试数据管理逻辑

### 第二步：创建调试面板组件
1. 创建 `src/components/LLMDebugPanel.tsx`
2. 实现基础的UI组件和数据显示

### 第三步：集成到会话剧场
1. 修改 `src/components/SessionTheater.tsx`
2. 添加右侧面板布局

### 第四步：拦截LLM调用
1. 创建 `src/api/llmApiInterceptor.ts`
2. 修改现有的LLM调用逻辑

### 第五步：连接数据流
1. 在会话执行函数中使用拦截器
2. 测试数据显示是否正常

## CSS样式实现

```css
/* 添加到 src/index.css 或相关样式文件 */
.llm-debug-panel {
  min-width: 320px;
  max-width: 400px;
}

.debug-call-item {
  transition: all 0.2s ease;
}

.debug-call-item:hover {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.debug-content {
  scrollbar-width: thin;
  scrollbar-color: #e5e7eb transparent;
}

.debug-content::-webkit-scrollbar {
  width: 6px;
}

.debug-content::-webkit-scrollbar-track {
  background: transparent;
}

.debug-content::-webkit-scrollbar-thumb {
  background-color: #e5e7eb;
  border-radius: 3px;
}

.debug-content::-webkit-scrollbar-thumb:hover {
  background-color: #d1d5db;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .llm-debug-panel {
    position: fixed;
    right: 0;
    top: 0;
    height: 100vh;
    z-index: 50;
    transform: translateX(100%);
    transition: transform 0.3s ease;
  }

  .llm-debug-panel.visible {
    transform: translateX(0);
  }
}
```

## 测试验证

### 功能测试
1. 启动会话执行
2. 验证调试面板显示调用记录
3. 检查提示词和响应内容是否正确
4. 测试清空功能

### 性能测试
1. 连续执行多个步骤
2. 检查面板性能和内存使用
3. 验证记录数量限制是否生效

### 兼容性测试
1. 在不同浏览器中测试
2. 测试响应式布局
3. 验证现有功能是否受影响

这个实现方案遵循了"简单实现"的原则，同时保证了功能的完整性和可维护性。