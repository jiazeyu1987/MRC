# MRC 代码结构文档

## 概述

MRC (Multi-Role Dialogue System) 是一个基于 Flask 后端和 React 前端的多角色对话系统，支持创建和管理虚拟角色间的结构化对话流程。

## 系统架构

### 技术栈

**后端技术栈:**
- **框架**: Flask 2.3.3 + SQLAlchemy ORM
- **数据库**: SQLite (开发环境), PostgreSQL/MySQL (生产环境)
- **LLM集成**: Anthropic Claude API
- **API设计**: RESTful + Flask-RESTful
- **认证**: 基础会话认证 (可扩展)
- **跨域**: Flask-CORS
- **数据库迁移**: Flask-Migrate

**前端技术栈:**
- **框架**: React 18.2.0 + TypeScript
- **构建工具**: Vite
- **样式**: Tailwind CSS 3.3.0
- **图标**: Lucide React
- **状态管理**: React Hooks + Context API
- **API集成**: Fetch API + TypeScript 类型定义

## 目录结构

### 后端目录结构 (backend/)

```
backend/
├── app/                     # 应用核心代码
│   ├── __init__.py         # Flask 应用工厂函数
│   ├── config.py           # 配置管理 (开发/测试/生产环境)
│   ├── models/             # SQLAlchemy 数据模型
│   │   ├── __init__.py     # 模型导出
│   │   ├── role.py         # 角色模型
│   │   ├── flow.py         # 流程模板和步骤模型
│   │   ├── session.py      # 会话模型
│   │   ├── message.py      # 消息模型
│   │   └── llm_interaction.py # LLM交互记录模型
│   ├── api/                # REST API 端点
│   │   ├── __init__.py     # API 注册
│   │   ├── roles.py        # 角色管理 API
│   │   ├── flows.py        # 流程模板管理 API
│   │   ├── sessions.py     # 会话管理 API
│   │   ├── messages.py     # 消息处理 API
│   │   ├── llm.py          # LLM 集成 API
│   │   └── monitoring.py   # 系统监控 API
│   ├── services/           # 业务逻辑服务
│   ├── schemas/            # 数据验证模式 (Marshmallow)
│   └── utils/              # 工具函数
│       ├── monitoring.py   # 系统监控工具
│       └── errors.py       # 错误处理工具
├── migrations/             # 数据库迁移文件
│   ├── versions/           # 迁移版本文件
│   └── env.py             # Alembic 环境配置
├── logs/                   # 应用日志目录
├── instance/               # 实例特定数据
├── requirements.txt        # Python 依赖
├── .env                    # 环境变量配置
└── run.py                  # 应用入口点
```

### 前端目录结构 (front/)

```
front/
├── src/                    # 源代码
│   ├── App.tsx             # 根组件
│   ├── main.tsx            # React 应用入口
│   ├── MultiRoleDialogSystem.tsx # 主应用界面 (63KB)
│   ├── LLMTestPage.tsx     # LLM 测试界面
│   ├── api/                # API 客户端模块
│   │   ├── roleApi.ts      # 角色管理 API 客户端
│   │   ├── flowApi.ts      # 流程模板 API 客户端
│   │   └── sessionApi.ts   # 会话管理 API 客户端
│   ├── components/         # 可复用组件
│   │   ├── SessionTheater.tsx # 会话剧场组件
│   │   ├── DebugPanel.tsx  # 调试面板组件
│   │   ├── StepProgressDisplay.tsx # 步骤进度显示
│   │   └── StepVisualization.tsx # 步骤可视化
│   ├── hooks/              # 自定义 React Hooks
│   │   ├── useStepProgress.ts # 步骤进度管理
│   │   ├── useLLMInteractions.ts # LLM 交互追踪
│   │   └── useWebSocket.ts # WebSocket 连接管理
│   ├── types/              # TypeScript 类型定义
│   ├── utils/              # 工具函数
│   └── theme.tsx           # 主题系统
├── public/                 # 静态资源
├── package.json            # Node.js 依赖
├── vite.config.ts          # Vite 配置 (API 代理)
└── tsconfig.json           # TypeScript 配置
```

## 核心组件说明

### 后端核心组件

#### 1. Flask 应用工厂 (app/__init__.py)
- **功能**: 创建和配置 Flask 应用实例
- **职责**:
  - 数据库和扩展初始化
  - API 路由注册
  - 错误处理器配置
  - 系统监控初始化

#### 2. 数据模型 (app/models/)
- **Role**: 角色定义模型 (name, prompt, style)
- **FlowTemplate**: 对话流程模板
- **FlowStep**: 流程步骤定义
- **Session**: 活动会话实例
- **Message**: 对话消息记录
- **LLMInteraction**: LLM API 调用日志

#### 3. API 端点 (app/api/)
- **RESTful 设计**: 使用 Flask-RESTful 框架
- **统一响应格式**: JSON 格式，包含 success、data、error 字段
- **分页支持**: 可配置的分页参数 (page, page_size)
- **错误处理**: 统一的 HTTP 错误状态码和消息

### 前端核心组件

#### 1. 主应用 (MultiRoleDialogSystem.tsx)
- **功能**: 完整的用户界面，包含角色管理、流程配置、会话执行
- **状态管理**: 使用 React Hooks 管理复杂状态
- **API 集成**: 集成所有后端 API 端点
- **实时更新**: 支持实时对话进度显示

#### 2. API 客户端 (src/api/)
- **类型安全**: 完整的 TypeScript 类型定义
- **错误处理**: 统一的错误处理和用户提示
- **请求拦截**: 自动添加认证头和处理分页

#### 3. 自定义 Hooks (src/hooks/)
- **useStepProgress**: 管理对话步骤进度
- **useLLMInteractions**: 追踪 LLM 交互状态
- **useWebSocket**: 处理实时 WebSocket 连接

## 数据库设计

### 实体关系图

```
Role (1) ───* SessionRole (*)
    │           │
    │           └───* Message
    │
FlowTemplate (1) ───* Session
    │
    └───* FlowStep
```

### 关系说明
- **Role**: 定义虚拟角色的属性和行为
- **FlowTemplate**: 可重用的对话流程模板
- **FlowStep**: 流程中的具体步骤，支持条件分支
- **Session**: 基于 FlowTemplate 的具体对话实例
- **Message**: 对话消息，支持线程化回复
- **SessionRole**: 会话中角色分配和配置

## API 设计

### RESTful 端点列表

#### 角色管理
- `GET /api/roles` - 获取角色列表
- `POST /api/roles` - 创建新角色
- `GET /api/roles/{id}` - 获取角色详情
- `PUT /api/roles/{id}` - 更新角色
- `DELETE /api/roles/{id}` - 删除角色

#### 流程模板管理
- `GET /api/flows` - 获取流程模板列表
- `POST /api/flows` - 创建新流程模板
- `GET /api/flows/{id}` - 获取流程模板详情
- `PUT /api/flows/{id}` - 更新流程模板
- `DELETE /api/flows/{id}` - 删除流程模板
- `POST /api/flows/{id}/copy` - 复制流程模板

#### 会话管理
- `GET /api/sessions` - 获取会话列表
- `POST /api/sessions` - 创建新会话
- `GET /api/sessions/{id}` - 获取会话详情
- `PUT /api/sessions/{id}` - 更新会话
- `DELETE /api/sessions/{id}` - 删除会话
- `POST /api/sessions/{id}/run-next-step` - 执行下一步

#### 消息处理
- `GET /api/sessions/{id}/messages` - 获取会话消息
- `POST /api/sessions/{id}/messages` - 发送新消息
- `GET /api/sessions/{id}/export` - 导出会话数据

### API 设计原则
- **RESTful 设计**: 遵循 REST 架构原则
- **统一响应**: 标准化的 JSON 响应格式
- **错误处理**: 清晰的错误码和消息
- **分页支持**: 大数据集的分页处理
- **版本控制**: API 版本管理策略

## 集成点

### 前端-后端集成
- **REST API**: 所有 CRUD 操作通过 REST API
- **WebSocket**: 实时对话更新
- **CORS**: 跨域请求配置
- **错误处理**: 统一的错误处理和用户提示
- **认证**: 可扩展的认证和授权系统

### 外部服务集成
- **Anthropic Claude**: LLM 能力集成
- **数据库**: 多数据库支持 (SQLite/PostgreSQL/MySQL)
- **监控**: 系统健康检查和性能监控
- **日志**: 结构化日志和多输出支持

## 性能和安全

### 性能优化
- **数据库索引**: 关键查询字段的索引优化
- **分页**: 大数据集的分页处理
- **缓存**: LLM 响应缓存策略
- **API 限流**: API 调用频率限制
- **前端优化**: Vite 构建优化和代码分割

### 安全特性
- **输入验证**: 全面的输入数据验证
- **SQL 注入防护**: SQLAlchemy ORM 保护
- **XSS 防护**: 前端 XSS 攻击防护
- **CORS 配置**: 跨域请求安全配置
- **认证授权**: 可扩展的认证和授权框架

## 开发和部署

### 开发环境
- **后端开发**: `python run.py` (端口 5010)
- **前端开发**: `npm run dev` (端口 3000)
- **API 代理**: Vite 代理后端 API 请求
- **热重载**: 前端代码热重载支持

### 生产部署
- **环境配置**: 多环境配置管理
- **数据库迁移**: Flask-Migrate 数据库版本控制
- **日志管理**: 结构化日志和错误追踪
- **监控**: 系统健康和性能监控
- **扩展性**: 水平扩展和负载均衡支持

## 当前问题和改进

### 已知问题
- 前端部分组件存在 TypeScript 编译错误
- ESLint 配置需要初始化
- 部分高级组件构建失败
- 认证系统需要实现

### 改进方向
- 数据库模式优化
- API 响应缓存实现
- 安全头增强
- 前端打包体积优化