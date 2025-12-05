# Multi-Role Chat Backend - Migrated Version

## 项目说明

这是从原始项目 `D:\ProjectPackage\MultiRoleChat\backend` 迁移过来的后端服务。

## 迁移日期

2025-12-05

## 包含的功能

### 核心功能
- **角色管理** - 创建和管理对话角色
- **流程模板** - 定义对话流程和步骤
- **会话管理** - 管理对话会话和状态
- **消息处理** - 处理对话消息和历史

### LLM 集成
- **多种LLM支持** - OpenAI, Anthropic Claude等
- **智能对话引擎** - 基于流程模板的对话生成
- **性能监控** - LLM调用统计和监控

### 高级功能
- **实时通信** - WebSocket和Server-Sent Events
- **健康监控** - 系统状态和性能指标
- **数据库迁移** - 完整的版本控制数据库结构
- **缓存服务** - 提高性能的缓存机制

## 数据库

迁移包含完整的数据库文件：
- `conversations.db` - 主数据库，包含所有角色、流程、会话和消息数据
- `conversations.db.backup` - 数据库备份（如果存在）

## 安装和运行

### 1. 安装依赖
```bash
cd D:/ProjectPackage/MRC/backend
pip install -r requirements.txt
```

### 2. 环境配置
复制 `.env.example` 为 `.env` 并配置相关参数：
```bash
cp .env.example .env
```

### 3. 初始化数据库
```bash
python run.py init-db
```

### 4. 创建内置角色和流程
```bash
python run.py create-builtin-roles
python run.py create-builtin-flows
```

### 5. 运行服务器
```bash
python run.py
```

## API 端点

服务器启动后，可访问以下API端点：
- `http://localhost:5010/api/roles` - 角色管理
- `http://localhost:5010/api/flows` - 流程模板
- `http://localhost:5010/api/sessions` - 会话管理
- `http://localhost:5010/api/messages` - 消息处理
- `http://localhost:5010/api/health` - 健康检查

## 管理工具

项目包含以下实用工具：
- `check_db.py` - 检查数据库状态
- `clean_db.py` - 清理数据库
- `apply_migration.py` - 应用数据库迁移
- `clear_templates.py` - 清理流程模板
- `reset_templates.py` - 重置为内置模板

## 注意事项

1. **端口配置** - 默认运行在端口 5010
2. **数据库文件** - SQLite数据库位于项目根目录
3. **日志文件** - 日志存储在 `logs/` 目录
4. **环境变量** - 请根据实际情况配置 `.env` 文件

## 原始项目

原始项目位置：`D:\ProjectPackage\MultiRoleChat\backend`

此迁移保持了完整的数据库和功能结构，可以直接使用。