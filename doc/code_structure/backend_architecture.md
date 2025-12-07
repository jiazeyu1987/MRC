# 后端架构详细文档

## Flask 应用架构

### 应用工厂模式

MRC 后端采用 Flask 应用工厂模式，通过 `app/__init__.py` 中的 `create_app()` 函数创建应用实例：

```python
def create_app(config_name=None):
    """应用工厂函数"""
    app = Flask(__name__)
    # 加载配置
    # 初始化扩展
    # 注册路由和蓝图
    # 配置错误处理
    return app
```

**优势:**
- 支持多环境配置 (开发/测试/生产)
- 便于单元测试和集成测试
- 避免全局状态和循环依赖
- 支持应用实例的动态创建

### 配置管理

配置文件 `app/config.py` 实现分层配置管理：

```python
class Config:
    """基础配置类"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///dev.db'

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
```

## 数据库模型架构

### 模型设计原则

1. **单一职责原则**: 每个模型负责单一业务实体
2. **外键关系**: 明确的数据库关系定义
3. **索引优化**: 关键查询字段的数据库索引
4. **时间戳**: 统一的创建和更新时间戳

### 核心模型详解

#### 1. Role 模型 (`app/models/role.py`)

```python
class Role(db.Model):
    """角色模型 - 定义虚拟对话角色"""
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    prompt = db.Column(db.Text, nullable=False)  # 角色提示词
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**业务含义:**
- 定义 AI 虚拟角色的身份和特征
- `prompt` 字段包含完整的角色设定和行为指导
- 支持角色的版本管理和历史追踪

#### 2. FlowTemplate 模型 (`app/models/flow.py`)

```python
class FlowTemplate(db.Model):
    """流程模板模型 - 定义对话流程结构"""
    __tablename__ = 'flow_templates'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    version = db.Column(db.String(20), default='1.0.0')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    steps = db.relationship('FlowStep', backref='template',
                           lazy='dynamic', cascade='all, delete-orphan')
```

**设计特点:**
- 支持流程模板的版本管理
- 软删除机制 (`is_active` 字段)
- 级联删除相关步骤

#### 3. FlowStep 模型 (`app/models/flow.py`)

```python
class FlowStep(db.Model):
    """流程步骤模型 - 定义流程中的具体步骤"""
    __tablename__ = 'flow_steps'

    id = db.Column(db.Integer, primary_key=True)
    flow_template_id = db.Column(db.Integer, db.ForeignKey('flow_templates.id'))
    order = db.Column(db.Integer, nullable=False)  # 步骤顺序
    speaker_role_ref = db.Column(db.String(100))   # 发言角色引用
    target_role_ref = db.Column(db.String(100))    # 目标角色引用
    task_type = db.Column(db.String(50))           # 任务类型
    context_scope = db.Column(db.String(20))       # 上下文范围
    description = db.Column(db.Text)               # 步骤描述
    conditions = db.Column(db.JSON)                # 执行条件
    actions = db.Column(db.JSON)                   # 执行动作
```

**核心字段说明:**
- `task_type`: ask_question, answer_question, review_answer, summarize
- `context_scope`: none, last_message, last_round, all
- `conditions`: JSON 格式的执行条件
- `actions`: JSON 格式的执行动作

#### 4. Session 模型 (`app/models/session.py`)

```python
class Session(db.Model):
    """会话模型 - 基于模板的具体对话实例"""
    __tablename__ = 'sessions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    flow_template_id = db.Column(db.Integer, db.ForeignKey('flow_templates.id'))
    status = db.Column(db.String(20), default='created')  # created, running, completed, paused
    current_step = db.Column(db.Integer, default=0)
    flow_data = db.Column(db.JSON)  # 流程数据快照
    role_assignments = db.Column(db.JSON)  # 角色分配
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    messages = db.relationship('Message', backref='session',
                              lazy='dynamic', cascade='all, delete-orphan')
    session_roles = db.relationship('SessionRole', backref='session',
                                    lazy='dynamic', cascade='all, delete-orphan')
```

**状态管理:**
- `status`: created, running, completed, paused, error
- `current_step`: 当前执行步骤索引
- `flow_data`: 流程执行时的数据快照
- `role_assignments`: 角色分配配置

### 数据库关系图

```
Role (1) ───* SessionRole (*)
    │           │
    │           └───* Message
    │
FlowTemplate (1) ───* Session
    │
    └───* FlowStep
```

## API 架构设计

### Flask-RESTful 架构

MRC 后端采用 Flask-RESTful 框架实现 RESTful API：

```python
from flask_restful import Api, Resource

class RoleList(Resource):
    def get(self):
        """获取角色列表"""
        # 分页查询
        # 序列化数据
        # 返回响应

    def post(self):
        """创建新角色"""
        # 数据验证
        # 创建记录
        # 返回创建结果

api.add_resource(RoleList, '/api/roles')
api.add_resource(RoleDetail, '/api/roles/<int:role_id>')
```

### API 设计模式

#### 1. 统一响应格式

```json
{
    "success": true,
    "data": { ... },
    "message": "操作成功",
    "pagination": {
        "page": 1,
        "page_size": 20,
        "total": 100,
        "pages": 5
    }
}
```

#### 2. 错误处理机制

```python
@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error_code': 'BAD_REQUEST',
        'message': '请求参数错误'
    }), 400
```

#### 3. 分页查询

```python
def get_paginated_query(query, page=1, page_size=20):
    """分页查询辅助函数"""
    paginated = query.paginate(
        page=page, per_page=page_size, error_out=False
    )
    return {
        'items': [item.to_dict() for item in paginated.items],
        'total': paginated.total,
        'pages': paginated.pages,
        'current_page': page
    }
```

### API 端点架构

#### 角色管理 API (`app/api/roles.py`)

**端点列表:**
- `GET /api/roles` - 获取角色列表 (支持分页和搜索)
- `POST /api/roles` - 创建新角色
- `GET /api/roles/<int:id>` - 获取角色详情
- `PUT /api/roles/<int:id>` - 更新角色
- `DELETE /api/roles/<int:id>` - 删除角色

**核心功能:**
- 角色信息的 CRUD 操作
- 分页查询 (默认 20 条/页)
- 按名称搜索角色
- 输入数据验证和清理

#### 流程模板 API (`app/api/flows.py`)

**端点列表:**
- `GET /api/flows` - 获取流程模板列表
- `POST /api/flows` - 创建新流程模板
- `GET /api/flows/<int:id>` - 获取流程模板详情
- `PUT /api/flows/<int:id>` - 更新流程模板
- `DELETE /api/flows/<int:id>` - 删除流程模板
- `POST /api/flows/<int:id>/copy` - 复制流程模板

**核心功能:**
- 流程模板的完整生命周期管理
- 流程步骤的批量创建和更新
- 流程模板复制功能
- 流程统计和分析

#### 会话管理 API (`app/api/sessions.py`)

**端点列表:**
- `GET /api/sessions` - 获取会话列表
- `POST /api/sessions` - 创建新会话
- `GET /api/sessions/<int:id>` - 获取会话详情
- `PUT /api/sessions/<int:id>` - 更新会话
- `DELETE /api/sessions/<int:id>` - 删除会话
- `POST /api/sessions/<int:id>/run-next-step` - 执行下一步
- `POST /api/sessions/<int:id>/control` - 会话控制 (暂停/继续/重置)

**核心功能:**
- 会话的创建和管理
- 流程步骤的顺序执行
- 会话状态控制
- 实时进度追踪

#### 消息处理 API (`app/api/messages.py`)

**端点列表:**
- `GET /api/sessions/<int:session_id>/messages` - 获取会话消息
- `POST /api/sessions/<int:session_id>/messages` - 发送新消息
- `GET /api/sessions/<int:session_id>/messages/<int:message_id>` - 获取消息详情
- `GET /api/sessions/<int:session_id>/messages/<int:message_id>/replies` - 获取回复
- `GET /api/sessions/<int:session_id>/export` - 导出会话数据

**核心功能:**
- 消息的 CRUD 操作
- 消息线程和回复管理
- **增强导出功能**: 包含原始LLM提示词的多格式导出
- 消息搜索和过滤

**导出功能增强:**
- **JSON格式**: 包含完整LLM交互数据（原始提示词、性能指标等）
- **Markdown格式**: 结构化文档输出
- **文本格式**: 纯文本对话记录
- **LLM数据集成**: 自动关联消息与对应的LLM录制记录

## 服务层架构

### LLM 文件录制系统

#### LLM 文件录制服务 (`app/services/llm_file_record_service.py`)

MRC 系统实现了完整的 LLM 交互录制系统，用于记录真实的提示词和响应数据。

**核心设计原则:**
- **文件系统存储**: 避免数据库 schema 变更，存储临时数据
- **结构化组织**: 按会话、日期等多维度组织文件
- **线程安全**: 支持并发写入和读取
- **自动清理**: 定期清理过期文件，控制存储空间

**服务架构:**
```python
class LLMFileRecordService:
    """LLM交互文件录制服务"""

    def __init__(self):
        self.base_dir = Path("logs/llm_interactions")
        self.max_file_size = 100 * 1024 * 1024  # 100MB
        self.session_retention_days = 90
        self.error_retention_days = 30
```

**文件组织结构:**
```
logs/llm_interactions/
├── by_session/           # 按会话分组
│   ├── session_1/
│   │   └── 2025-12-07.json
│   └── session_5/
│       └── 2025-12-07.json
├── by_date/             # 按日期汇总
│   └── 2025-12-07_all_interactions.json
├── errors/              # 错误记录
│   └── 2025-12-07_errors.json
├── real_time/           # 实时数据
│   └── latest.json
└── archive/             # 归档压缩文件
    └── 2025-12-07_interactions.json.gz
```

**录制数据格式:**
```json
{
    "id": "uuid-v4",
    "timestamp": "2025-12-07T12:28:14.718544",
    "session_id": 5,
    "message_id": 12,
    "role_name": "产品专员",
    "step_id": 1,
    "round_index": 1,
    "provider": "claude-3-5-sonnet-20241022",
    "prompt": "完整的原始提示词内容...",
    "response": "完整的LLM响应内容...",
    "success": true,
    "performance_metrics": {
        "response_time_ms": 28909,
        "prompt_length": 451,
        "response_length": 2387
    },
    "metadata": {
        "stage": "completed",
        "task_type": "ask_question",
        "finalized": true
    }
}
```

**核心功能:**
- **实时录制**: LLM 调用前后的完整数据录制
- **生命周期管理**: 记录开始、完成、最终确认三个阶段
- **性能监控**: 录制响应时间、token使用等性能指标
- **错误追踪**: 专门录制失败交互用于问题排查
- **文件轮转**: 自动文件分割和压缩归档

#### LLM 集成服务

#### Claude API 集成 (`app/services/llm_service.py`)

```python
class ClaudeService:
    """Claude LLM 服务集成"""

    def __init__(self, api_key, model='claude-3-sonnet-20240229'):
        self.api_key = api_key
        self.model = model
        self.client = anthropic.Anthropic(api_key=api_key)

    async def generate_response(self, prompt, context=None):
        """生成 LLM 响应"""
        # 构建完整提示词
        # 调用 Claude API
        # 处理响应和错误
        # 记录交互日志
```

**服务特性:**
- 异步 API 调用支持
- 上下文管理
- 错误重试机制
- 交互日志记录
- 性能监控

### 对话流程引擎

#### 流程执行服务 (`app/services/flow_engine.py`)

```python
class FlowEngine:
    """对话流程执行引擎"""

    def execute_step(self, session, step):
        """执行单个流程步骤"""
        # 检查执行条件
        # 执行步骤动作
        # 更新会话状态
        # 生成消息

    def run_flow(self, session):
        """运行完整流程"""
        # 获取流程模板
        # 按顺序执行步骤
        # 处理条件分支
        # 管理会话状态
```

**核心功能:**
- 步骤顺序执行
- 条件分支处理
- 上下文管理
- 异常处理和恢复
- **LLM录制集成**: 自动录制每个步骤的LLM交互过程

**LLM录制集成:**
- **录制时机**: LLM调用前、调用后、消息确认三个阶段
- **数据关联**: 通过message_id关联LLM录制与数据库消息
- **生命周期管理**: 完整的LLM交互生命周期跟踪
- **错误处理**: LLM调用失败的完整错误信息录制

**集成示例:**
```python
# FlowEngine中的LLM录制调用
record_llm_interaction(
    session_id=session.id,
    role_name=role.name,
    prompt=actual_prompt,  # 发送给LLM的原始提示词
    response=llm_response,  # LLM的完整响应
    step_id=step.id,
    round_index=session.current_round,
    performance_metrics=metrics
)
```

## 系统监控和日志

### 性能监控服务 (`app/utils/monitoring.py`)

```python
class SystemMonitor:
    """系统性能监控"""

    def track_api_call(self, endpoint, duration, status_code):
        """追踪 API 调用"""
        # 记录调用指标
        # 更新性能统计

    def track_llm_call(self, model, tokens, duration, cost):
        """追踪 LLM 调用"""
        # 记录使用情况
        # 更新成本统计
```

**监控指标:**
- API 响应时间和状态
- LLM 调用次数和成本
- 数据库查询性能
- 系统资源使用情况

### 日志系统

**日志配置:**
- 控制台日志 (开发环境)
- 文件日志 (所有环境)
- 结构化日志格式
- 日志轮转和归档
- 错误级别分级

## 安全和认证

### 输入验证

**Marshmallow 模式验证:**
```python
class RoleSchema(ma.Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    prompt = fields.Str(required=True, validate=validate.Length(min=1))

    @validates('name')
    def validate_name(self, value):
        if Role.query.filter_by(name=value).first():
            raise ValidationError('角色名称已存在')
```

### 数据安全

**安全特性:**
- SQL 注入防护 (SQLAlchemy ORM)
- XSS 攻击防护 (输入验证)
- CSRF 保护 (Flask-WTF)
- 安全头配置
- 敏感数据加密

### 认证授权框架

**可扩展的认证系统:**
- 基于会话的认证
- JWT Token 支持
- 角色权限管理
- API 访问控制

## 数据库优化

### 索引策略

**关键索引:**
```sql
-- 角色查询优化
CREATE INDEX idx_roles_name ON roles(name);
CREATE INDEX idx_roles_created_at ON roles(created_at);

-- 会话查询优化
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_sessions_flow_template_id ON sessions(flow_template_id);

-- 消息查询优化
CREATE INDEX idx_messages_session_id ON messages(session_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);
```

### 查询优化

**优化策略:**
- 懒加载关联数据
- 批量查询优化
- 分页查询
- 数据库连接池
- 查询缓存

## 部署和扩展

### 环境配置

**多环境支持:**
- 开发环境 (Development)
- 测试环境 (Testing)
- 生产环境 (Production)
- 自定义环境

### 扩展性设计

**水平扩展支持:**
- 无状态应用设计
- 数据库连接池
- 缓存层集成
- 负载均衡兼容
- 微服务架构就绪

### 部署架构

**推荐部署方案:**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │────│   App Server 1  │    │   App Server 2  │
│    (Nginx)      │    │    (Flask)      │    │    (Flask)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                └──────────┬─────────────┘
                                           │
                                  ┌─────────────────┐
                                  │     Database    │
                                  │ (PostgreSQL)    │
                                  └─────────────────┘
```

这个后端架构设计确保了系统的可扩展性、可维护性和高性能，同时提供了丰富的业务功能和良好的开发体验。