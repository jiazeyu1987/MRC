# LLM 文件录制系统文档

## 概述

MRC 系统实现了完整的 LLM 交互录制系统，专门用于记录真实的提示词和响应数据，避免数据库 schema 变更，同时提供完整的 LLM 交互追踪能力。

## 设计目标

### 核心需求
- **真实提示词录制**: 记录实际发送给 LLM 的完整提示词，而非后期重构
- **临时数据存储**: 使用文件系统存储，避免数据库结构变更
- **高性能**: 支持并发写入，不影响主要业务流程
- **结构化组织**: 便于查询、分析和导出的文件组织方式

### 技术原则
- **无侵入性**: 不修改现有数据库结构
- **线程安全**: 支持多线程并发访问
- **自动管理**: 文件轮转、压缩、清理等自动化维护
- **易于集成**: 简单的 API 接口，便于业务代码调用

## 系统架构

### 服务架构

```python
class LLMFileRecordService:
    """LLM交互文件录制服务 - 单例模式"""

    def __init__(self):
        self.base_dir = Path("logs/llm_interactions")
        self.max_file_size = 100 * 1024 * 1024  # 100MB
        self.session_retention_days = 90
        self.error_retention_days = 30
        self.buffer_size = 100
        self.flush_interval = 30  # 秒
```

### 文件组织结构

```
logs/llm_interactions/
├── by_session/                    # 按会话分组存储
│   ├── session_1/
│   │   ├── 2025-12-07.json        # 按日期分割
│   │   └── 2025-12-08.json
│   ├── session_5/
│   │   └── 2025-12-07.json
│   └── session_12/
│       └── 2025-12-07.json
├── by_date/                       # 按日期汇总存储
│   ├── 2025-12-07_all_interactions.json
│   ├── 2025-12-08_all_interactions.json
│   └── 2025-12-09_all_interactions.json
├── errors/                         # 错误记录专用存储
│   ├── 2025-12-07_errors.json
│   └── 2025-12-08_errors.json
├── real_time/                      # 实时数据缓存
│   └── latest.json
└── archive/                        # 归档压缩文件
    ├── 2025-12-07_interactions.json.gz
    └── 2025-12-08_interactions.json.gz
```

## 核心功能

### 1. 交互录制

#### 录制时机
系统在 LLM 交互的三个关键时机进行录制：

1. **调用开始时**: 记录 LLM 调用的初始状态
2. **调用完成时**: 记录完整的响应数据
3. **消息确认时**: 补充 message_id 关联信息

#### 录制数据格式

```json
{
    "id": "3a17b8cf-500d-4f38-a231-aaf01244fa37",
    "timestamp": "2025-12-07T12:24:08.275173",
    "session_id": 1,
    "message_id": 12,              // 消息确认时补充
    "role_name": "产品专员",
    "step_id": 1,
    "round_index": 1,
    "provider": "claude",
    "model": "claude-3-5-sonnet-20241022",
    "prompt": "完整的原始提示词内容...",
    "response": "完整的LLM响应内容...",
    "success": true,
    "error_message": null,
    "performance_metrics": {
        "response_time_ms": 28909,
        "prompt_length": 451,
        "response_length": 2387,
        "history_messages_count": 0
    },
    "metadata": {
        "stage": "completed",        // started, completed, finalized
        "task_type": "ask_question",
        "session_topic": "选择一款泛血管介入产品...",
        "api_response_time": null,
        "model_used": "claude-3-5-sonnet-20241022",
        "finalized": true          // 最终确认标志
    }
}
```

### 2. 文件管理

#### 文件轮转
- **触发条件**: 单文件大小超过 100MB
- **处理方式**: 移动到 archive 目录并 gzip 压缩
- **文件命名**: `{原文件名}_{时间戳}.json.gz`

#### 自动清理
- **会话文件**: 保留 90 天
- **错误文件**: 保留 30 天
- **归档文件**: 压缩后长期保留

### 3. 性能优化

#### 缓冲机制
```python
# 实时缓冲区，减少磁盘I/O
self._real_time_buffer = []

# 批量写入，提高性能
def _flush_real_time_buffer(self):
    buffer_copy = self._real_time_buffer.copy()
    self._real_time_buffer.clear()
    # 批量写入文件
```

#### 后台线程
- **定时刷新**: 每 30 秒自动刷新缓冲区
- **异步处理**: 不阻塞主业务流程
- **错误恢复**: 异常情况下的数据保护

## API 接口

### 便捷函数

```python
# 简化的录制接口
from app.services.llm_file_record_service import record_llm_interaction

interaction_id = record_llm_interaction(
    session_id=5,
    role_name="产品专员",
    prompt="完整的提示词内容",
    response="LLM响应内容",
    success=True,
    performance_metrics={"response_time_ms": 28909}
)
```

### 完整服务接口

```python
from app.services.llm_file_record_service import llm_file_record

# 获取会话交互记录
interactions = llm_file_record.get_session_interactions(session_id=5)

# 获取最新交互记录
latest = llm_file_record.get_latest_interactions(limit=50)

# 获取统计信息
stats = llm_file_record.get_statistics()

# 清理过期文件
llm_file_record.cleanup_old_files()
```

### REST API 端点

```bash
# 录制系统健康检查
GET /api/llm-file-records/health

# 获取会话LLM录制
GET /api/llm-file-records/session/{session_id}

# 获取最新录制记录
GET /api/llm-file-records/latest?limit=50

# 获取录制统计信息
GET /api/llm-file-records/statistics

# 清理过期录制文件
DELETE /api/llm-file-records/cleanup?dry_run=false&force=true
```

## 与业务系统集成

### FlowEngine 集成

```python
# 在 flow_engine_service.py 中的集成示例
class FlowEngineService:
    @staticmethod
    def _generate_llm_response_sync(session, role, step, context):
        # 1. 调用前录制
        record_llm_interaction(
            session_id=session.id,
            role_name=role.name,
            step_id=step.id,
            prompt=prompt,
            response="",  # 调用前为空
            success=False,  # 标记为进行中
            metadata={"stage": "started"}
        )

        # 2. 调用 LLM API
        llm_response = llm_service.generate_response(prompt, context)

        # 3. 调用后录制
        interaction_id = record_llm_interaction(
            session_id=session.id,
            role_name=role.name,
            step_id=step.id,
            prompt=prompt,
            response=llm_response.content,
            success=llm_response.success,
            performance_metrics=llm_response.metrics,
            metadata={"stage": "completed"}
        )

        # 4. 保存消息后补充 message_id
        record_llm_interaction(
            session_id=session.id,
            message_id=message.id,  # 补充消息ID
            role_name=role.name,
            step_id=step.id,
            prompt=prompt,
            response=llm_response.content,
            success=True,
            metadata={"stage": "finalized", "finalized": True}
        )
```

### 导出系统集成

```python
# 在 message_service.py 中的集成示例
def _export_to_json(session, messages):
    # 获取LLM交互录制
    try:
        from app.services.llm_file_record_service import get_session_llm_interactions
        llm_interactions = get_session_llm_interactions(session.id)

        # 创建消息ID到LLM交互的映射
        message_llm_map = {}
        for interaction in llm_interactions:
            msg_id = interaction.get('message_id')
            if msg_id is not None:
                message_llm_map[int(msg_id)] = interaction
    except Exception:
        message_llm_map = {}

    # 构建导出数据，包含原始LLM提示词
    for msg in messages:
        message_item = {
            'id': msg.id,
            'content': msg.content,
            # ... 其他字段
        }

        # 添加LLM交互信息
        if msg.id in message_llm_map:
            llm_interaction = message_llm_map[msg.id]
            message_item['llm_interaction'] = {
                'original_prompt': llm_interaction.get('prompt'),
                'provider': llm_interaction.get('provider'),
                'model': llm_interaction.get('model'),
                'performance_metrics': llm_interaction.get('performance_metrics'),
                'timestamp': llm_interaction.get('timestamp')
            }
```

## 数据查询和分析

### 按会话查询

```python
# 获取特定会话的所有LLM交互
interactions = llm_file_record.get_session_interactions(
    session_id=5,
    date="2025-12-07"  # 可选：指定日期
)
```

### 按时间查询

```python
# 获取特定日期的所有LLM交互
interactions = llm_file_record.get_date_interactions("2025-12-07")

# 获取错误记录
errors = llm_file_record.get_error_interactions(
    date="2025-12-07",
    days=7  # 最近7天
)
```

### 统计分析

```python
# 获取系统统计信息
stats = llm_file_record.get_statistics()
print(f"总交互数: {stats['total_interactions']}")
print(f"成功交互: {stats['successful_interactions']}")
print(f"失败交互: {stats['failed_interactions']}")
print(f"总会话数: {stats['total_sessions']}")
print(f"存储信息: {stats['storage_info']}")
```

## 维护和监控

### 文件清理

```bash
# 手动清理（开发环境）
python cleanup_llm_records.py --dry-run  # 预览模式
python cleanup_llm_records.py --force    # 强制清理

# 自动清理（生产环境）
# 通过定时任务调用 API 端点
curl -X DELETE "http://localhost:5010/api/llm-file-records/cleanup?force=true"
```

### 监控指标

```python
# 存储使用情况
storage_stats = stats['storage_info']
for storage_type, info in storage_stats.items():
    count = info['count']
    size_mb = info['size'] / (1024 * 1024)
    print(f"{storage_type}: {count} 文件, {size_mb:.2f} MB")
```

### 健康检查

```python
# 系统健康状态
health = llm_file_record.get_health_status()
print(f"系统状态: {health['status']}")
print(f"可用空间: {health['disk_space_available']}")
print(f"文件写入权限: {health['write_permissions']}")
```

## 配置参数

### 核心配置

```python
class LLMFileRecordService:
    def __init__(self):
        # 存储配置
        self.base_dir = Path("logs/llm_interactions")  # 基础目录
        self.max_file_size = 100 * 1024 * 1024         # 最大文件大小: 100MB

        # 保留期限
        self.session_retention_days = 90              # 会话文件保留天数
        self.error_retention_days = 30                # 错误文件保留天数

        # 缓冲配置
        self.buffer_size = 100                        # 缓冲区大小
        self.flush_interval = 30                       # 刷新间隔: 30秒
```

### 环境变量配置

```bash
# .env 文件配置
LLM_RECORDS_ENABLED=true          # 启用LLM录制
LLM_RECORDS_BASE_DIR=logs/llm_interactions  # 录制文件目录
LLM_RECORDS_MAX_FILE_SIZE=104857600  # 最大文件大小(字节)
LLM_RECORDS_RETENTION_DAYS=90      # 文件保留天数
```

## 最佳实践

### 性能优化
1. **批量写入**: 使用缓冲区减少磁盘I/O
2. **异步处理**: 后台线程处理文件操作
3. **文件轮转**: 避免单个文件过大
4. **定期清理**: 防止磁盘空间耗尽

### 数据安全
1. **权限控制**: 确保录制文件有适当的访问权限
2. **敏感信息**: 避免录制包含敏感信息的提示词
3. **备份策略**: 重要录制数据的定期备份
4. **加密存储**: 对敏感录制数据进行加密存储

### 错误处理
1. **优雅降级**: 录制失败不影响主业务流程
2. **错误日志**: 详细的错误信息记录
3. **重试机制**: 临时性错误的自动重试
4. **监控告警**: 异常情况的及时告警

## 故障排查

### 常见问题

#### 1. 录制文件未生成
**症状**: 执行会话后没有生成录制文件
**排查步骤**:
```bash
# 检查目录权限
ls -la logs/llm_interactions/

# 检查服务初始化
python -c "from app.services.llm_file_record_service import llm_file_record; print(llm_file_record)"

# 检查错误日志
tail -f logs/app.log | grep -i llm
```

#### 2. 文件写入失败
**症状**: 录制过程中出现写入错误
**排查步骤**:
```bash
# 检查磁盘空间
df -h

# 检查文件权限
ls -la logs/llm_interactions/by_session/

# 手动测试写入
python -c "
from app.services.llm_file_record_service import record_llm_interaction
record_llm_interaction(1, 'test', 'test', 'test')
print('录制测试完成')
"
```

#### 3. 导出功能异常
**症状**: 导出的JSON中缺少LLM提示词
**排查步骤**:
```bash
# 检查LLM录制数据
python -c "
from app.services.llm_file_record_service import get_session_llm_interactions
interactions = get_session_llm_interactions(5)
print(f'交互记录数: {len(interactions)}')
for i in interactions:
    print(f'message_id: {i.get(\"message_id\")}, finalized: {i.get(\"finalized\")}')
"

# 测试导出API
curl -s "http://localhost:5010/api/sessions/5/export?format=json" | jq '.data.messages[] | select(.id == 12) | .llm_interaction'
```

### 日志分析

```bash
# 查看录制相关日志
grep -i "llm\|record" logs/app.log

# 查看文件操作日志
grep -i "file\|write\|read" logs/app.log

# 查看错误日志
grep -i "error\|exception\|failed" logs/app.log
```

这个LLM文件录制系统为MRC项目提供了完整的LLM交互追踪能力，确保用户能够获取真实的提示词数据，同时保持系统的高性能和可维护性。