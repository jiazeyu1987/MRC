# 简单数据流设计

## 数据流概述

采用最简单的直线数据流：API调用 → 响应包含调试信息 → 前端显示。

```mermaid
flowchart TD
    A[用户点击"执行下一步"] --> B[前端调用会话API]
    B --> C[后端执行LLM调用]
    C --> D[后端返回API响应]
    D --> E[响应包含llm_debug字段]
    E --> F[前端提取调试数据]
    F --> G[更新调试面板状态]
    G --> H[UI重新渲染显示]
```

## 核心数据结构

### 后端API响应格式
```json
{
  "success": true,
  "data": {
    "message": {
      "id": 123,
      "content": "AI生成的响应内容"
    },
    "llm_debug": {
      "prompt": "发送给LLM的提示词",
      "response": "LLM返回的响应内容",
      "timestamp": "2024-01-01T12:00:00Z"
    }
  }
}
```

### 前端调试数据格式
```typescript
interface LLMDebugData {
  prompt: string;
  response: string;
  timestamp: string;
}
```

## 详细实现流程

### 1. 用户操作触发
- 用户在会话剧场点击"执行下一步"按钮
- 前端调用 `sessionApi.executeNextStep(sessionId)`
- 等待后端响应

### 2. 后端LLM调用
- 后端接收到 `/api/sessions/{id}/run-next-step` 请求
- 构建提示词并调用LLM API
- 生成响应消息

### 3. 调试信息生成
- 在LLM调用完成后，生成调试信息
- 包含：提示词、响应内容、时间戳
- 将调试信息添加到API响应中

### 4. 前端数据处理
- 前端接收到API响应
- 检查是否有 `llm_debug` 字段
- 提取调试数据

### 5. UI更新
- 将调试数据添加到调试面板状态
- React组件自动重新渲染
- 在右侧面板显示新的调试信息

## 数据流优势

### 简单性
- 无需复杂的实时通信
- 无需状态管理器
- 无需消息队列
- 无需WebSocket连接

### 可靠性
- 依赖现有API调用流程
- 数据传递可靠
- 容易调试和测试

### 性能
- 无额外网络请求
- 内存占用低
- CPU开销小

## 文件修改点

### 后端文件
```
backend/app/api/sessions.py (约10行修改)
- 在run-next-step API响应中添加llm_debug字段
```

### 前端文件
```
front/src/api/sessionApi.ts (约5行修改)
- 在executeNextStep响应处理中提取llm_debug

front/src/components/SessionTheater.tsx (约20行修改)
- 添加右侧调试面板布局

front/src/components/SimpleLLMDebugPanel.tsx (新建, 约30行)
- 简单的调试面板组件
```

## 总代码量预估

- 后端修改: 10行
- 前端修改: 55行
- **总计: ~65行** (符合100行以内要求)

## 实现复杂度

- **后端**: 简单的API响应修改
- **前端**: 基础的React组件开发
- **集成**: 简单的布局调整
- **测试**: 基本的功能验证

完全符合"简单任务，简单实现"的要求。