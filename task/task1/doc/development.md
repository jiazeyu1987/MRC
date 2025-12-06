# 开发指导文档

## 快速开始

### 前置条件
- 熟悉React和TypeScript
- 了解MRC项目的基本结构
- 确保前端开发环境已配置好

### 开发环境检查
```bash
# 确保在项目根目录
cd D:\ProjectPackage\MRC

# 检查前端是否可以正常启动
cd front
npm run dev
```

## 开发步骤详解

### 步骤1: 创建调试管理器

**文件路径**: `front/src/utils/debugPanelManager.ts`

```typescript
// 完整实现代码，直接复制即可
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
    if (this.state.calls.length > this.maxRecords) {
      this.state.calls = this.state.calls.slice(-this.maxRecords);
    }
    this.notifyListeners();
    return id;
  }

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

  getState(): DebugPanelState {
    return { ...this.state };
  }

  subscribe(listener: () => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  clearCalls() {
    this.state.calls = [];
    this.notifyListeners();
  }

  private notifyListeners() {
    this.listeners.forEach(listener => listener());
  }
}

export { DebugPanelManager, LLMDebugCall };
```

### 步骤2: 创建LLM调试面板组件

**文件路径**: `front/src/components/LLMDebugPanel.tsx`

```typescript
import React, { useState, useEffect } from 'react';
import { DebugPanelManager, LLMDebugCall } from '../utils/debugPanelManager';

export function LLMDebugPanel() {
  const [state, setState] = useState(DebugPanelManager.getState());

  useEffect(() => {
    const manager = DebugPanelManager.getInstance();
    const updateState = () => setState(manager.getState());
    const unsubscribe = manager.subscribe(updateState);
    updateState();
    return unsubscribe;
  }, []);

  const handleClear = () => {
    DebugPanelManager.getInstance().clearCalls();
  };

  return (
    <div className="bg-white border-l border-gray-200 h-full flex flex-col">
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
    <div className="border border-gray-200 rounded-lg p-3">
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

      <div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-xs text-blue-600 hover:text-blue-800 mb-2"
        >
          {expanded ? '收起' : '展开'} 详情
        </button>

        {expanded && (
          <div className="space-y-2">
            <div>
              <h4 className="text-xs font-medium text-gray-700 mb-1">提示词:</h4>
              <div className="text-xs bg-gray-50 p-2 rounded border text-gray-800 max-h-32 overflow-y-auto">
                {call.prompt}
              </div>
            </div>

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

### 步骤3: 修改SessionTheater组件

**文件路径**: `front/src/components/SessionTheater.tsx`

找到现有的SessionTheater组件，修改布局：

```typescript
// 在import部分添加
import { LLMDebugPanel } from './LLMDebugPanel';

// 修改主布局部分
export function SessionTheater({
  session,
  messages,
  onSendMessage,
  isLoading
}: SessionTheaterProps) {
  return (
    <div className="flex h-full">
      {/* 原有的主会话区域 */}
      <div className="flex-1 flex flex-col">
        {/* 保持原有的所有内容不变 */}
        <div className="bg-white border-b px-6 py-4">
          {/* 原有头部内容 */}
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {/* 原有消息列表 */}
        </div>

        <div className="bg-white border-t px-6 py-4">
          {/* 原有输入框 */}
        </div>
      </div>

      {/* 新增的右侧调试面板 */}
      <div className="w-80 border-l border-gray-200">
        <LLMDebugPanel />
      </div>
    </div>
  );
}
```

### 步骤4: 创建LLM调用拦截器

**文件路径**: `front/src/api/llmInterceptor.ts`

```typescript
import { DebugPanelManager } from '../utils/debugPanelManager';

// 原始API调用函数（需要根据实际项目调整）
async function originalLLMCall(endpoint: string, data: any): Promise<any> {
  const response = await fetch(`/api${endpoint}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  return response.json();
}

// 拦截器函数
export async function llmCallWithDebug(
  endpoint: string,
  prompt: string,
  sessionId: string,
  additionalData?: any
): Promise<any> {
  const manager = DebugPanelManager.getInstance();

  // 记录调用开始
  const callId = manager.addPendingCall(prompt, sessionId);

  const startTime = Date.now();

  try {
    // 调用原始LLM API
    const response = await originalLLMCall(endpoint, {
      prompt,
      ...additionalData
    });

    const duration = Date.now() - startTime;

    // 提取响应内容
    const responseText = response.response || response.message || JSON.stringify(response);

    // 更新调试信息
    manager.updateCall(callId, responseText, duration);

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

### 步骤5: 修改会话执行逻辑

需要找到实际调用LLM的地方并进行修改。根据项目结构，可能在以下位置：

**可能的位置1**: `front/src/api/sessionApi.ts`
**可能的位置2**: `front/src/MultiRoleDialogSystem.tsx`
**可能的位置3**: 其他会话相关文件

```typescript
// 在会话执行函数中替换LLM调用
import { llmCallWithDebug } from './llmInterceptor';

// 找到类似这样的代码：
// const response = await fetch('/api/llm/generate', { ... });

// 替换为：
const response = await llmCallWithDebug(
  '/llm/generate',
  prompt,  // 提示词
  sessionId.toString(),  // 会话ID
  {  // 其他参数
    model: 'claude-3-sonnet',
    temperature: 0.7
  }
);
```

## 测试验证

### 功能测试步骤

1. **启动开发服务器**
```bash
cd front
npm run dev
```

2. **进入会话剧场**
- 访问 http://localhost:3000
- 进入一个会话或创建新会话
- 确认右侧显示LLM调试面板

3. **触发LLM调用**
- 在会话中执行下一步
- 观察调试面板是否显示新的记录

4. **验证数据显示**
- 检查时间戳是否正确
- 验证提示词内容
- 确认响应消息显示
- 测试展开/收起功能

5. **测试清空功能**
- 点击"清空"按钮
- 确认记录被清空

### 调试技巧

#### 1. 检查组件渲染
```typescript
// 在LLMDebugPanel组件中添加调试信息
useEffect(() => {
  console.log('DebugPanel state:', state);
}, [state]);
```

#### 2. 验证拦截器工作
```typescript
// 在拦截器中添加日志
export async function llmCallWithDebug(...) {
  console.log('LLM Call intercepted:', { prompt, sessionId });
  // ... 原有代码
}
```

#### 3. 检查状态管理
```typescript
// 在DebugPanelManager中添加调试方法
debugLog(message: string) {
  console.log(`DebugPanel: ${message}`, this.state);
}
```

## 常见问题解决

### 问题1: 调试面板不显示
**可能原因**: 组件导入错误或路径问题
**解决方案**:
- 检查import路径是否正确
- 确认文件是否存在
- 查看浏览器控制台错误信息

### 问题2: 没有LLM调用记录
**可能原因**: 拦截器没有正确集成
**解决方案**:
- 确认LLM调用函数被正确替换
- 检查会话执行逻辑
- 验证拦截器函数被调用

### 问题3: 数据不更新
**可能原因**: 状态管理订阅失效
**解决方案**:
- 检查useEffect依赖
- 验证订阅/取消订阅逻辑
- 确认状态更新函数被调用

### 问题4: 布局问题
**可能原因**: CSS样式冲突
**解决方案**:
- 检查Tailwind CSS类名
- 调整flex布局参数
- 验证响应式设计

## 性能优化建议

### 1. 限制记录数量
```typescript
// 在DebugPanelManager中
private maxRecords: number = 10; // 从20改为10
```

### 2. 添加防抖更新
```typescript
// 在LLMDebugPanel中
const [debouncedState, setDebouncedState] = useState(state);

useEffect(() => {
  const timer = setTimeout(() => {
    setDebouncedState(state);
  }, 100); // 100ms防抖

  return () => clearTimeout(timer);
}, [state]);
```

### 3. 虚拟滚动（大量数据时）
考虑使用`react-window`库实现虚拟滚动。

## 代码提交建议

### Git提交信息
```
feat: 添加LLM调试面板功能

- 在会话剧场右侧添加调试面板
- 实现LLM调用拦截和数据记录
- 添加实时数据显示和清空功能
- 支持展开/收起详细信息
```

### 文件变更清单
- 新增: `src/utils/debugPanelManager.ts`
- 新增: `src/components/LLMDebugPanel.tsx`
- 新增: `src/api/llmInterceptor.ts`
- 修改: `src/components/SessionTheater.tsx`
- 修改: 会话执行相关文件

通过这个开发指南，您应该能够顺利完成LLM调试面板的实现。如果遇到问题，请参考调试技巧部分或检查相关文档。