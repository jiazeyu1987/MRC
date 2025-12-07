# MRC 系统文档中心

## 文档导航

### 📁 代码结构文档 (Code Structure)

- **[README.md](code_structure/README.md)** - 系统架构概览
- **[backend_architecture.md](code_structure/backend_architecture.md)** - 后端架构详细说明
- **[llm_file_recording_system.md](code_structure/llm_file_recording_system.md)** - LLM文件录制系统文档
- **[frontend_architecture.md](code_structure/frontend_architecture.md)** - 前端架构详细说明

### 📁 业务文档 (Business)

- **[README.md](Business/README.md)** - 业务流程概览
- **[workflows.md](Business/workflows.md)** - 详细工作流程
- **[user_scenarios.md](Business/user_scenarios.md)** - 用户场景分析

## 文档使用指南

### 🎯 快速开始

如果您是新加入项目的开发人员，建议按以下顺序阅读：

1. **了解系统整体** → [代码结构概览](code_structure/README.md)
2. **理解业务价值** → [业务流程概览](Business/README.md)
3. **熟悉技术架构** → [后端架构](code_structure/backend_architecture.md) | [前端架构](code_structure/frontend_architecture.md)
4. **了解LLM录制** → [LLM文件录制系统](code_structure/llm_file_recording_system.md)
5. **掌握工作流程** → [详细工作流程](Business/workflows.md)
6. **了解用户需求** → [用户场景分析](Business/user_scenarios.md)

### 🔧 开发参考

#### 后端开发
- Flask 应用架构和设计模式
- 数据库模型关系和 API 设计
- LLM 集成和业务逻辑实现
- LLM 文件录制系统集成和配置
- 流程引擎和会话管理机制

#### 前端开发
- React + TypeScript 组件架构
- 状态管理和 API 集成
- UI 组件设计和主题系统

#### 业务功能
- 角色管理完整流程
- 流程模板设计规范
- 会话执行和监控机制

### 📊 业务参考

#### 产品管理
- 核心业务价值主张
- 目标用户画像分析
- 成功案例和最佳实践

#### 运营管理
- 用户使用场景详解
- 业务工作流程规范
- 性能指标和KPI定义

## 技术栈总览

### 后端技术
```
├── 框架: Flask 2.3.3
├── 数据库: SQLite (开发) / PostgreSQL (生产)
├── ORM: SQLAlchemy
├── API: Flask-RESTful
├── LLM: Anthropic Claude API
├── 监控: 自研监控系统
└── 部署: Gunicorn + Nginx
```

### 前端技术
```
├── 框架: React 18.2.0 + TypeScript
├── 构建: Vite 4.4.5
├── 样式: Tailwind CSS 3.3.0
├── 图标: Lucide React
├── 状态: React Hooks + Context
├── API: Fetch + TypeScript
└── 部署: Vite Static Build
```

## 项目结构速览

```
MRC/
├── backend/                 # Flask 后端服务
│   ├── app/                # 应用核心代码
│   │   ├── api/           # REST API 端点
│   │   ├── models/        # 数据库模型
│   │   ├── services/      # 业务服务层
│   │   │   ├── llm_file_record_service.py  # LLM文件录制服务
│   │   │   ├── flow_engine_service.py      # 流程引擎服务
│   │   │   ├── message_service.py          # 消息服务
│   │   │   └── ...                         # 其他服务
│   │   └── utils/         # 工具函数
│   ├── logs/              # 日志和录制文件
│   │   └── llm_interactions/  # LLM交互录制
│   ├── migrations/        # 数据库迁移
│   └── run.py            # 应用入口
├── front/                  # React 前端应用
│   ├── src/
│   │   ├── api/          # API 客户端
│   │   ├── components/   # UI 组件
│   │   └── hooks/        # 自定义 Hooks
│   └── package.json
├── doc/                    # 项目文档
│   ├── code_structure/   # 代码结构文档
│   └── Business/         # 业务流程文档
└── README.md              # 项目说明
```

## 核心功能模块

### 1. 角色管理系统
- **功能**: 创建、编辑、删除虚拟对话角色
- **特性**: 角色属性配置、行为约束、交互规则
- **技术**: Role Model + REST API + React 表单

### 2. 流程模板设计
- **功能**: 设计结构化对话流程模板
- **特性**: 步骤配置、条件分支、循环控制
- **技术**: FlowTemplate Model + 可视化编辑器

### 3. 会话执行引擎
- **功能**: 基于模板执行多角色对话
- **特性**: 实时执行、进度监控、异常处理
- **技术**: Session Model + WebSocket + 状态机

### 4. LLM 集成服务
- **功能**: 调用 Claude API 生成对话内容
- **特性**: 上下文管理、质量控制、性能监控、提示词录制
- **技术**: Claude API + 异步调用 + 缓存机制 + 文件录制系统

### 5. LLM 文件录制系统
- **功能**: 录制实际LLM提示词和响应到文件系统
- **特性**: 结构化存储、实时记录、自动清理、导出集成
- **技术**: 文件系统存储 + JSON格式 + 多级索引 + 线程安全

### 6. 系统监控分析
- **功能**: 系统健康监控和业务数据分析
- **特性**: 实时监控、性能分析、使用统计
- **技术**: 自研监控 + 数据可视化

## 开发环境搭建

### 后端开发环境
```bash
# 1. 安装 Python 依赖
cd backend
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置数据库和API密钥

# 3. 初始化数据库
python run.py init-db
python run.py create-builtin-roles

# 4. 启动开发服务器
python run.py
```

### 前端开发环境
```bash
# 1. 安装 Node.js 依赖
cd front
npm install

# 2. 启动开发服务器
npm run dev
```

## 部署指南

### 生产环境部署
- **后端**: Gunicorn + Nginx + PostgreSQL
- **前端**: Vite Build + Nginx 静态服务
- **数据库**: PostgreSQL 主从复制
- **监控**: 系统监控 + 日志收集
- **安全**: HTTPS + 防火墙 + 访问控制

### Docker 部署
```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d
```

## API 文档

### 核心端点
- `GET /api/roles` - 获取角色列表
- `POST /api/roles` - 创建新角色
- `GET /api/flows` - 获取流程模板
- `POST /api/sessions` - 创建会话
- `POST /api/sessions/{id}/run-next-step` - 执行下一步

### LLM 文件录制端点
- `GET /api/llm-file-records/health` - 录制系统健康检查
- `GET /api/llm-file-records/session/{id}` - 获取会话LLM录制
- `GET /api/llm-file-records/latest` - 获取最新录制记录
- `GET /api/llm-file-records/statistics` - 获取录制统计信息
- `DELETE /api/llm-file-records/cleanup` - 清理过期录制文件

### 导出端点
- `GET /api/sessions/{id}/export?format=json` - 导出会话JSON（含原始LLM提示词）
- `GET /api/sessions/{id}/export?format=markdown` - 导出会话Markdown
- `GET /api/sessions/{id}/export?format=text` - 导出会话纯文本

### 认证方式
- 开发环境: 无需认证
- 生产环境: JWT Token 认证

## 性能指标

### 系统性能
- **API 响应时间**: < 200ms (95%分位)
- **LLM 调用延迟**: < 3s
- **系统可用性**: > 99.9%
- **并发用户**: > 1000

### 业务指标
- **角色创建成功率**: > 95%
- **流程完成率**: > 90%
- **用户满意度**: > 4.5/5
- **日活跃用户**: 持续增长

## 故障排查指南

### 常见问题

#### 1. 数据库连接失败
```
检查: 数据库配置、网络连接、权限设置
解决: 更新 .env 配置、检查防火墙、重置权限
```

#### 2. LLM API 调用失败
```
检查: API密钥、网络连接、余额充足
解决: 更新密钥、检查网络、充值账户
```

#### 3. 前端构建失败
```
检查: Node.js版本、依赖完整性、TypeScript错误
解决: 更新Node.js、重新安装依赖、修复类型错误
```

### 监控告警
- **系统监控**: CPU、内存、磁盘使用率
- **应用监控**: API错误率、响应时间
- **业务监控**: 会话成功率、用户活跃度

## 贡献指南

### 代码规范
- **Python**: PEP 8 + Black 格式化
- **TypeScript**: ESLint + Prettier
- **Git**: Conventional Commits

### 提交流程
1. Fork 项目到个人仓库
2. 创建功能分支 (`git checkout -b feature/xxx`)
3. 提交代码 (`git commit -m 'feat: add new feature'`)
4. 推送分支 (`git push origin feature/xxx`)
5. 创建 Pull Request

### 代码审查
- 必须通过所有自动化测试
- 至少需要一位维护者审核
- 代码覆盖率不低于 80%

## 版本管理

### 版本号规范
- 主版本号: 不兼容的API修改
- 次版本号: 向后兼容的功能性新增
- 修订号: 向后兼容的问题修正

### 发布流程
1. 功能开发和测试完成
2. 更新版本号和 CHANGELOG
3. 创建 Git 标签
4. 构建和发布部署包
5. 更新文档和通知

## 联系方式

### 技术支持
- **邮箱**: tech-support@mrc-system.com
- **文档**: https://docs.mrc-system.com
- **问题反馈**: GitHub Issues

### 商务合作
- **邮箱**: business@mrc-system.com
- **电话**: +86-xxx-xxxx-xxxx

---

**文档版本**: v1.0.0
**最后更新**: 2025-12-05
**维护者**: MRC 开发团队