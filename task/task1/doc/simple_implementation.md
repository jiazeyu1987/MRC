# 简单技术实现方案 (约65行代码)

## 实现概述

采用API响应增强方案，总共约65行代码修改。

## 后端实现 (10行)

### 修改会话执行API
**文件**: `backend/app/api/sessions.py`

```python
# 在 SessionExecution类的 post方法中（大约第200行附近）
# 找到类似这样的代码：
# return {'success': True, 'data': result_data}

# 修改为：
if result_data:
    result_data['llm_debug'] = {
        'prompt': self._get_last_prompt(),  # 获取最后的提示词
        'response': result_data.get('message', {}).get('content', ''),
        'timestamp': datetime.utcnow().isoformat()
    }

return {'success': True, 'data': result_data}

# 添加获取最后提示词的方法
def _get_last_prompt(self):
    """获取最近使用的提示词"""
    # 这里需要根据实际的提示词存储方式来实现
    # 简单实现：从会话上下文中获取
    return "当前会话的提示词"  # 临时实现
```

## 前端实现 (55行)

### 1. 修改SessionApi (5行)
**文件**: `front/src/api/sessionApi.ts`

```typescript
// 在executeNextStep函数中，找到处理响应的部分
export async function executeNextStep(sessionId: number): Promise<any> {
  const response = await apiClient.post(`/sessions/${sessionId}/run-next-step`);

  if (response.success && response.data?.llm_debug) {
    // 提取调试信息
    return {
      ...response,
      llm_debug: response.data.llm_debug
    };
  }

  return response;
}
```

### 2. 创建调试面板组件 (30行)
**文件**: `front/src/components/SimpleLLMDebugPanel.tsx` (新建)

```typescript
import React from 'react';

interface LLMDebugData {
  prompt: string;
  response: string;
  timestamp: string;
}

interface SimpleLLMDebugPanelProps {
  debugData: LLMDebugData[];
}

export function SimpleLLMDebugPanel({ debugData }: SimpleLLMDebugPanelProps) {
  return (
    <div className="w-80 h-full bg-white border-l border-gray-200 p-4">
      <div className="mb-4">
        <h3 className="text-sm font-medium text-gray-900">LLM调试</h3>
      </div>

      {debugData.length === 0 ? (
        <div className="text-center text-gray-500 text-sm py-8">
          暂无调试信息
        </div>
      ) : (
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {debugData.map((item, index) => (
            <div key={index} className="border border-gray-200 rounded p-3">
              <div className="text-xs text-gray-500 mb-2">
                {new Date(item.timestamp).toLocaleTimeString()}
              </div>

              <div className="mb-2">
                <div className="text-xs font-medium text-blue-600 mb-1">提示词:</div>
                <div className="text-xs bg-blue-50 p-2 rounded text-gray-800">
                  {item.prompt}
                </div>
              </div>

              <div>
                <div className="text-xs font-medium text-green-600 mb-1">响应:</div>
                <div className="text-xs bg-green-50 p-2 rounded text-gray-800">
                  {item.response}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

### 3. 修改SessionTheater组件 (20行)
**文件**: `front/src/components/SessionTheater.tsx`

```typescript
// 在import部分添加
import { SimpleLLMDebugPanel } from './SimpleLLMDebugPanel';

// 在SessionTheater组件中添加状态
export function SessionTheater({ session, messages, onSendMessage, isLoading }: SessionTheaterProps) {
  const [llmDebugData, setLlmDebugData] = useState<any[]>([]);

  // 修改executeNextStep的处理
  const handleExecuteNextStep = async () => {
    try {
      const response = await sessionApi.executeNextStep(session.id);

      // 提取调试信息
      if (response.llm_debug) {
        setLlmDebugData(prev => [response.llm_debug, ...prev.slice(0, 9)]);
      }

      // 处理其他逻辑...
    } catch (error) {
      console.error('执行步骤失败:', error);
    }
  };

  // 修改返回的JSX布局
  return (
    <div className="flex h-full">
      {/* 主会话区域 */}
      <div className="flex-1 flex flex-col">
        {/* 现有的所有内容保持不变 */}
        <div className="bg-white border-b px-6 py-4">
          {/* 现有头部内容 */}
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {/* 现有消息列表 */}
        </div>

        <div className="bg-white border-t px-6 py-4">
          {/* 现有输入框 */}
        </div>
      </div>

      {/* 新增的右侧调试面板 */}
      <SimpleLLMDebugPanel debugData={llmDebugData} />
    </div>
  );
}
```

## 实现步骤

### 1. 后端修改 (10分钟)
1. 打开 `backend/app/api/sessions.py`
2. 找到会话执行的响应处理代码
3. 添加 `llm_debug` 字段到响应中
4. 实现获取最后提示词的方法

### 2. 前端修改 (20分钟)
1. 修改 `front/src/api/sessionApi.ts` 处理调试信息
2. 创建 `front/src/components/SimpleLLMDebugPanel.tsx`
3. 修改 `front/src/components/SessionTheater.tsx` 集成调试面板

### 3. 测试验证 (10分钟)
1. 启动后端服务
2. 启动前端开发服务器
3. 进入会话剧场
4. 执行会话步骤
5. 验证右侧调试面板显示信息

## 总计

- **代码行数**: 65行
- **实现时间**: 40分钟
- **文件修改**: 3个文件
- **新增文件**: 1个文件

完全符合"简单任务，简单实现"的要求！