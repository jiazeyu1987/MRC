# New Backend - 主流程代码

## 概述

`new_backend` 目录包含了MRC（Multi-Role Dialogue System）项目的所有核心主流程代码，是从原始 `backend` 目录中提取出的纯净应用代码。

## 目录结构

```
new_backend/
├── run.py                          # 主应用入口点，包含CLI命令
├── requirements.txt                # Python依赖包
├── README.md                       # 后端文档
├── README_NEW_BACKEND.md           # 本文档
│
├── app/                            # Flask应用核心
│   ├── __init__.py                # Flask应用工厂，核心配置
│   ├── config.py                  # 应用配置（开发/生产环境）
│   ├── claudecli.py               # Claude CLI集成
│   │
│   ├── api/                       # REST API端点
│   │   ├── __init__.py
│   │   ├── roles.py               # 角色管理API
│   │   ├── flows.py               # 流程模板管理API
│   │   ├── sessions.py            # 会话管理API
│   │   ├── messages.py            # 消息管理API
│   │   ├── llm.py                 # LLM集成API
│   │   ├── monitoring.py          # 系统监控API
│   │   ├── knowledge_bases.py     # 知识库管理API
│   │   └── ...                    # 其他API模块
│   │
│   ├── models/                    # 数据库模型
│   │   ├── __init__.py
│   │   ├── role.py                # 角色模型
│   │   ├── flow.py                # 流程模板模型
│   │   ├── session.py             # 会话模型
│   │   ├── message.py             # 消息模型
│   │   ├── knowledge_base.py      # 知识库模型
│   │   ├── document.py            # 文档管理模型
│   │   └── ...                    # 其他数据模型
│   │
│   ├── services/                  # 业务逻辑服务
│   │   ├── __init__.py
│   │   ├── flow_engine_service.py # 核心对话执行引擎
│   │   ├── session_service.py     # 会话管理服务
│   │   ├── message_service.py     # 消息处理服务
│   │   ├── simple_llm.py          # LLM集成服务
│   │   ├── knowledge_base_service.py # 知识库管理服务
│   │   ├── ragflow_service.py     # RAGFlow集成服务
│   │   ├── document_service.py    # 文档管理服务
│   │   └── ...                    # 其他服务模块
│   │
│   ├── utils/                     # 工具类
│   │   ├── __init__.py
│   │   ├── llm_logger.py          # LLM日志记录
│   │   ├── monitoring.py          # 系统监控
│   │   ├── token_counter.py       # Token使用统计
│   │   └── ...                    # 其他工具模块
│   │
│   ├── schemas/                   # API数据验证模式
│   │   ├── __init__.py
│   │   ├── role.py                # 角色数据模式
│   │   ├── flow.py                # 流程数据模式
│   │   ├── session.py             # 会话数据模式
│   │   └── ...                    # 其他数据模式
│   │
│   └── middleware/                # 中间件
│       └── security.py            # 安全中间件
│
├── migrations/                    # 数据库迁移
│   ├── env.py                     # 迁移环境配置
│   └── versions/                  # 迁移版本文件
│
├── instance/                      # Flask实例目录（运行时）
├── logs/                          # 日志目录（运行时）
└── uploads/                       # 文件上传目录（运行时）
```

## 包含的核心功能

### 1. 多角色对话系统核心
- **角色管理**: 创建、配置和管理虚拟对话角色
- **流程模板**: 定义结构化对话流程和步骤
- **会话管理**: 管理对话会话状态和执行
- **消息处理**: 处理对话消息和线程

### 2. LLM集成
- **多Provider支持**: OpenAI、Anthropic Claude、Claude CLI
- **自动检测**: 智能选择可用的LLM Provider
- **交互日志**: 详细的LLM请求/响应记录
- **性能监控**: Token使用统计和性能追踪

### 3. 知识库系统 (RAGFlow集成)
- **数据集管理**: 与RAGFlow知识库集成
- **文档处理**: 上传、处理和文档分块
- **检索增强**: 基于知识库的对话增强
- **测试对话**: 知识库功能测试接口

### 4. 系统监控
- **健康检查**: 系统状态和连接监控
- **性能指标**: CPU、内存、请求率监控
- **实时追踪**: 会话执行进度可视化
- **错误处理**: 综合错误记录和报告

## 快速开始

### 1. 环境准备
```bash
cd new_backend
pip install -r requirements.txt
```

### 2. 环境配置
创建 `.env` 文件：
```bash
# Flask配置
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key

# 数据库
DATABASE_URL=sqlite:///multi_role_chat.db

# LLM配置
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# RAGFlow配置（知识库功能）
RAGFLOW_API_KEY=your-ragflow-key
RAGFLOW_BASE_URL=https://your-ragflow-instance.com
```

### 3. 初始化数据库
```bash
python run.py init-db
python run.py create-builtin-roles
python run.py create-builtin-flows
```

### 4. 启动应用
```bash
python run.py
```

应用将在 `http://localhost:5010` 启动。

## API端点

### 核心API
- `GET /api/health` - 系统健康检查
- `GET /api/roles` - 获取角色列表
- `POST /api/roles` - 创建新角色
- `GET /api/flows` - 获取流程模板
- `POST /api/sessions` - 创建新会话
- `GET /api/sessions/{id}/messages` - 获取会话消息

### 知识库API
- `GET /api/knowledge-bases` - 获取知识库列表
- `POST /api/knowledge-bases` - 知识库操作
- `POST /api/knowledge-bases/{id}/documents` - 上传文档

### 监控API
- `GET /api/monitoring/dashboard` - 监控面板数据
- `GET /api/monitoring/metrics` - 系统指标

## 架构特点

1. **模块化设计**: 清晰的分层架构（API → Service → Model）
2. **配置驱动**: 通过JSON配置实现复杂对话逻辑
3. **实时执行**: WebSocket和SSE支持的实时对话
4. **可扩展性**: 支持自定义LLM Provider和知识库
5. **监控完备**: 全面的性能和错误监控

## 与原backend的区别

### 包含的文件（✅）
- ✅ 所有核心应用代码
- ✅ API端点和业务逻辑
- ✅ 数据模型和迁移
- ✅ 配置文件和依赖

### 排除的文件（❌）
- ❌ 临时修复脚本 (`fix_*.py`, `temp_*.py`)
- ❌ 迁移工具脚本 (`add_*.py`, `apply_*.py`)
- ❌ 运行时数据 (`*.db`, `logs/`, `uploads/`)
- ❌ 开发工具 (`check_*.py`, `verify_*.py`)
- ❌ 文档和示例 (`demo_*.py`, `examples/`)

## 开发指南

1. **遵循现有模式**: 按照现有的Service层模式开发新功能
2. **API文档**: 使用Flask-RESTful的文档功能
3. **错误处理**: 使用统一的错误处理机制
4. **日志记录**: 重要操作要添加适当的日志
5. **测试**: 新功能需要包含相应的测试用例

## 许可证

本项目遵循与主项目相同的许可证。