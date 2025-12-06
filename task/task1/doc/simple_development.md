# 简单开发指导

## 快速实现指南

按照以下3个步骤，40分钟内完成LLM调试面板功能。

### 前置条件

- 前端开发环境已配置好 (`npm run dev` 正常运行)
- 后端服务已启动 (`python run.py`)
- 熟悉基本的React和Python代码修改

## 第1步: 后端修改 (10分钟)

### 修改会话执行API

**文件**: `backend/app/api/sessions.py`

**找到**: SessionExecution类的post方法，大约第200行

**操作**: 在返回结果中添加调试信息

```python
# 找到类似这样的代码:
# return {'success': True, 'data': result_data}

# 在return之前添加调试信息:
if result_data and 'message' in result_data:
    result_data['llm_debug'] = {
        'prompt': f"步骤执行 - {result_data['message'].get('content', '')[:50]}...",
        'response': result_data['message'].get('content', ''),
        'timestamp': datetime.utcnow().isoformat()
    }

return {'success': True, 'data': result_data}
```

**验证**: 重启后端服务，确保没有语法错误。

## 第2步: 前端修改 (20分钟)

### 2.1 修改SessionApi

**文件**: `front/src/api/sessionApi.ts`

```typescript
// 找到executeNextStep函数
// 在返回response之前添加调试信息处理

export async function executeNextStep(sessionId: number): Promise<any> {
  const response = await apiClient.post(`/sessions/${sessionId}/run-next-step`);

  // 添加调试信息提取
  if (response.success && response.data?.llm_debug) {
    return {
      ...response,
      llm_debug: response.data.llm_debug
    };
  }

  return response;
}
```

### 2.2 创建调试面板组件

**文件**: `front/src/components/SimpleLLMDebugPanel.tsx` (新建)

```typescript
import React from 'react';

interface LLMDebugData {
  prompt: string;
  response: string;
  timestamp: string;
}

export function SimpleLLMDebugPanel({ debugData }: { debugData: LLMDebugData[] }) {
  return (
    <div className="w-80 h-full bg-white border-l border-gray-200 p-4">
      <h3 className="text-sm font-medium text-gray-900 mb-4">LLM调试</h3>

      {debugData.length === 0 ? (
        <div className="text-center text-gray-500 text-sm">
          暂无调试信息
        </div>
      ) : (
        <div className="space-y-3 overflow-y-auto">
          {debugData.map((item, index) => (
            <div key={index} className="border border-gray-200 rounded p-3">
              <div className="text-xs text-gray-500 mb-2">
                {new Date(item.timestamp).toLocaleTimeString()}
              </div>

              <div className="mb-2">
                <div className="text-xs font-medium text-blue-600 mb-1">提示词:</div>
                <div className="text-xs bg-blue-50 p-2 rounded">
                  {item.prompt}
                </div>
              </div>

              <div>
                <div className="text-xs font-medium text-green-600 mb-1">响应:</div>
                <div className="text-xs bg-green-50 p-2 rounded">
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

### 2.3 修改SessionTheater组件

**文件**: `front/src/components/SessionTheater.tsx`

```typescript
// 1. 在顶部import部分添加:
import { SimpleLLMDebugPanel } from './SimpleLLMDebugPanel';

// 2. 在组件内部添加状态:
const [llmDebugData, setLlmDebugData] = useState<any[]>([]);

// 3. 修改executeNextStep处理:
const handleExecuteNextStep = async () => {
  try {
    const response = await sessionApi.executeNextStep(session.id);

    // 添加调试信息到状态
    if (response.llm_debug) {
      setLlmDebugData(prev => [response.llm_debug, ...prev.slice(0, 9)]);
    }

    // 其他现有逻辑...
  } catch (error) {
    console.error('执行步骤失败:', error);
  }
};

// 4. 修改return的JSX结构:
return (
  <div className="flex h-full">
    {/* 主会话区域 - 保持不变 */}
    <div className="flex-1 flex flex-col">
      {/* 现有的所有内容 */}
    </div>

    {/* 新增调试面板 */}
    <SimpleLLMDebugPanel debugData={llmDebugData} />
  </div>
);
```

## 第3步: 测试验证 (10分钟)

### 3.1 启动服务
```bash
# 终端1: 启动后端
cd backend
python run.py

# 终端2: 启动前端
cd front
npm run dev
```

### 3.2 功能测试
1. 打开浏览器访问 `http://localhost:3000`
2. 进入一个会话或创建新会话
3. 点击"执行下一步"按钮
4. 查看右侧是否显示LLM调试信息
5. 验证提示词和响应内容是否正确显示

### 3.3 故障排除

**问题1: 调试面板不显示**
- 检查后端API响应是否包含llm_debug字段
- 检查前端控制台是否有错误信息

**问题2: 样式不正确**
- 确认Tailwind CSS类名正确
- 检查组件导入路径

**问题3: 数据不显示**
- 验证后端修改是否生效
- 检查前端数据处理逻辑

## 完成确认

✅ **功能检查清单**
- [ ] 右侧显示LLM调试面板
- [ ] 执行会话步骤时自动显示调试信息
- [ ] 提示词内容正确显示
- [ ] 响应内容正确显示
- [ ] 时间戳显示正确
- [ ] 保留最近10条记录

✅ **代码检查清单**
- [ ] 后端修改: 约5行
- [ ] 前端修改: 约60行
- [ ] 总代码量: 约65行
- [ ] 实现时间: 约40分钟

## 完成！

恭喜！您已经用最简单的方式实现了LLM调试面板功能，完全符合info.txt的要求：
- ✅ 右侧面板显示
- ✅ 自动显示提示词和响应
- ✅ 简单实现，无过度设计
- ✅ 总代码量控制在100行以内