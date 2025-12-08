# RAGFlow Python API 参考文档

## 概述

RAGFlow 是一个领先的开源 RAG（检索增强生成）引擎，将先进的 RAG 技术与 Agent 能力相结合，为 LLM 创建优越的上下文层。RAGFlow 基于深度文档理解，提供完整的 Python SDK 用于程序化访问所有功能。

## 安装和设置

### 安装 SDK
```bash
pip install ragflow-sdk
```

### 基础配置
```python
from ragflow import RAGFlow

# 初始化客户端
client = RAGFlow(
    api_key="your_api_key",
    base_url="https://your-ragflow-instance.com"  # 可选
)
```

## 核心 API 组件

### 1. 数据集管理 (Dataset Management)

#### 创建数据集
```python
# 创建新数据集
dataset = client.create_dataset(
    name="my_dataset",
    description="我的数据集描述"
)

# 或者使用更详细的配置
dataset = client.create_dataset(
    name="knowledge_base",
    description="知识库数据集",
    metadata={
        "category": "documentation",
        "language": "zh-CN"
    }
)
```

#### 获取数据集列表
```python
# 获取所有数据集
datasets = client.get_datasets()

# 带分页的数据集列表
datasets = client.get_datasets(page=1, size=10)

# 提取数据集名称集合
dataset_names = [dataset.name for dataset in datasets]
print("数据集名称集合:", dataset_names)

# 遍历数据集信息
for dataset in datasets:
    print(f"ID: {dataset.id}")
    print(f"名称: {dataset.name}")
    print(f"描述: {dataset.description}")
    print(f"创建时间: {dataset.created_at}")
    print(f"文档数量: {dataset.document_count}")
    print("---")
```

#### 获取特定数据集
```python
# 根据 ID 获取数据集
dataset = client.get_dataset(dataset_id="your_dataset_id")

# 检查数据集是否存在
if dataset:
    print(f"数据集 {dataset.name} 存在")
else:
    print("数据集不存在")
```

#### 删除数据集
```python
# 删除数据集
client.delete_dataset(dataset_id="dataset_id_to_delete")

# 或者使用数据集对象
dataset.delete()
```

### 2. 文档管理 (Document Management)

#### 上传文档
```python
# 上传单个文件
with open("document.pdf", "rb") as f:
    document = dataset.upload_file(
        file=f,
        name="my_document.pdf",
        description="重要文档"
    )

# 上传多个文件
files = ["doc1.pdf", "doc2.txt", "doc3.docx"]
for file_path in files:
    with open(file_path, "rb") as f:
        dataset.upload_file(file=f, name=file_path)

# 带参数的上传
document = dataset.upload_file(
    file=file_content,
    name="manual.pdf",
    description="用户手册",
    metadata={
        "category": "manual",
        "version": "1.0",
        "author": "技术团队"
    }
)
```

#### 解析文档
```python
# 解析已上传的文档
document.parse()

# 异步解析
document.parse_async()

# 检查解析状态
if document.parsing_status == "completed":
    print("文档解析完成")
elif document.parsing_status == "failed":
    print(f"解析失败: {document.parsing_error}")
elif document.parsing_status == "processing":
    print("正在解析中...")
```

#### 获取文档列表
```python
# 获取数据集中的所有文档
documents = dataset.get_documents()

# 带过滤的文档列表
documents = dataset.get_documents(
    status="completed",  # 按解析状态过滤
    page=1,
    size=20
)

# 遍历文档信息
for doc in documents:
    print(f"文档名称: {doc.name}")
    print(f"文件大小: {doc.size} bytes")
    print(f"解析状态: {doc.parsing_status}")
    print(f"块数量: {doc.chunk_count}")
    print(f"上传时间: {doc.created_at}")
```

#### 删除文档
```python
# 删除文档
document.delete()

# 或者通过数据集删除
dataset.delete_document(document_id="doc_id")
```

### 3. 块处理 (Chunk Management)

#### 检索文档块
```python
# 基本检索
chunks = dataset.retrieve(
    query="什么是人工智能？",
    top_k=5
)

# 带过滤的检索
chunks = dataset.retrieve(
    query="机器学习算法",
    top_k=10,
    document_ids=["doc1_id", "doc2_id"],
    similarity_threshold=0.7
)

# 遍历检索结果
for chunk in chunks:
    print(f"内容: {chunk.content[:100]}...")
    print(f"相似度: {chunk.similarity_score}")
    print(f"文档来源: {chunk.document_name}")
    print(f"页码: {chunk.page_number}")
    print("---")
```

#### 获取文档块
```python
# 获取文档的所有块
chunks = document.get_chunks()

# 分页获取块
chunks = document.get_chunks(page=1, size=50)

# 获取特定块
chunk = document.get_chunk(chunk_id="chunk_id")
```

### 4. 聊天助手 (Chat Assistant)

#### 创建聊天助手
```python
# 创建基础聊天助手
assistant = client.create_assistant(
    name="客服助手",
    dataset_ids=["dataset1_id", "dataset2_id"],
    llm_config={
        "model": "gpt-3.5-turbo",
        "temperature": 0.7,
        "max_tokens": 1000
    }
)

# 创建高级聊天助手
assistant = client.create_assistant(
    name="技术支持助手",
    description="专门处理技术问题的AI助手",
    dataset_ids=["tech_docs_id"],
    system_prompt="你是一个专业的技术支持助手...",
    llm_config={
        "model": "gpt-4",
        "temperature": 0.3,
        "max_tokens": 2000,
        "top_p": 0.9
    },
    retrieval_config={
        "top_k": 5,
        "similarity_threshold": 0.6,
        "rerank": True
    }
)
```

#### 聊天会话管理
```python
# 创建聊天会话
session = assistant.create_session()

# 发送消息
response = session.send_message(
    query="如何安装Python？",
    stream=False  # 设置为 True 启用流式响应
)

# 处理响应
if response.success:
    print(f"回答: {response.answer}")
    print(f"引用的文档: {response.references}")
else:
    print(f"错误: {response.error}")

# 流式响应
for chunk in session.send_message("解释机器学习", stream=True):
    print(chunk.content, end="", flush=True)
print()
```

#### 会话历史
```python
# 获取会话历史
messages = session.get_messages()

# 遍历历史消息
for msg in messages:
    print(f"{msg.role}: {msg.content}")
    if msg.references:
        print("引用:", msg.references)
    print("---")
```

### 5. Agent 功能

#### 创建 DSL Agent
```python
# 定义 Agent DSL 配置
agent_dsl = {
    "name": "研究助手",
    "description": "协助进行研究和分析",
    "tools": [
        {
            "type": "retrieval",
            "dataset_ids": ["research_papers_id"],
            "config": {"top_k": 10}
        },
        {
            "type": "web_search",
            "config": {"max_results": 5}
        }
    ],
    "workflow": [
        {"step": "retrieval", "action": "search"},
        {"step": "analysis", "action": "analyze_results"},
        {"step": "summary", "action": "generate_summary"}
    ]
}

# 创建 Agent
agent = client.create_agent(
    name="研究助手",
    dsl_config=agent_dsl,
    llm_config={
        "model": "gpt-4",
        "temperature": 0.5
    }
)
```

#### 执行 Agent 任务
```python
# 执行 Agent 任务
task = agent.execute(
    input="分析人工智能在医疗领域的最新进展",
    context="需要重点关注2023-2024年的研究"
)

# 获取任务结果
if task.status == "completed":
    print("任务完成!")
    print("结果:", task.result)
    print("使用的数据源:", task.data_sources)
elif task.status == "failed":
    print("任务失败:", task.error)
elif task.status == "running":
    print("任务执行中...")
```

## 高级功能

### 1. 批量操作
```python
# 批量上传文档
documents = []
for file_path in document_list:
    with open(file_path, "rb") as f:
        doc = dataset.upload_file(file=f, name=os.path.basename(file_path))
        documents.append(doc)

# 批量解析
for doc in documents:
    doc.parse_async()

# 等待所有文档解析完成
for doc in documents:
    doc.wait_for_parsing(timeout=300)  # 5分钟超时
```

### 2. 异步操作
```python
import asyncio

async def process_documents():
    # 异步上传文档
    upload_tasks = []
    for file_path in document_list:
        task = asyncio.create_task(
            dataset.upload_file_async(file_path)
        )
        upload_tasks.append(task)

    documents = await asyncio.gather(*upload_tasks)

    # 异步解析
    parse_tasks = [doc.parse_async() for doc in documents]
    await asyncio.gather(*parse_tasks)

# 运行异步任务
asyncio.run(process_documents())
```

### 3. 自定义检索配置
```python
# 高级检索配置
retrieval_config = {
    "method": "semantic_search",  # 语义搜索
    "top_k": 20,
    "similarity_threshold": 0.75,
    "rerank": True,
    "rerank_model": "bge-reranker-large",
    "filters": {
        "document_type": ["pdf", "docx"],
        "date_range": {
            "start": "2023-01-01",
            "end": "2024-12-31"
        }
    }
}

# 使用自定义配置检索
chunks = dataset.retrieve(
    query="深度学习最新进展",
    config=retrieval_config
)
```

## 错误处理和最佳实践

### 1. 错误处理
```python
from ragflow.exceptions import RAGFlowError, APIError, ValidationError

try:
    dataset = client.create_dataset(name="test")
except ValidationError as e:
    print(f"验证错误: {e}")
except APIError as e:
    print(f"API错误: {e.status_code} - {e.message}")
except RAGFlowError as e:
    print(f"RAGFlow错误: {e}")
```

### 2. 重试机制
```python
import time
from ragflow.exceptions import APIError

def upload_with_retry(dataset, file_path, max_retries=3):
    for attempt in range(max_retries):
        try:
            with open(file_path, "rb") as f:
                return dataset.upload_file(file=f)
        except APIError as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 指数退避
                continue
            raise
```

### 3. 性能优化
```python
# 使用连接池
client = RAGFlow(
    api_key="your_key",
    base_url="https://your-instance.com",
    max_connections=20,
    timeout=30
)

# 批量处理
def process_batch(documents, batch_size=10):
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        # 处理批次
        yield process_document_batch(batch)
```

## 监控和日志

### 1. API 调用监控
```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 自定义日志处理
logger = logging.getLogger("ragflow")
handler = logging.FileHandler("ragflow.log")
logger.addHandler(handler)
```

### 2. 使用情况统计
```python
# 获取使用统计
stats = client.get_usage_stats(
    start_date="2024-01-01",
    end_date="2024-12-31"
)

print(f"API调用次数: {stats.api_calls}")
print(f"处理的文档数量: {stats.documents_processed}")
print(f"存储使用量: {stats.storage_used} MB")
```

## 配置选项

### 环境变量配置
```bash
# .env 文件
RAGFLOW_API_KEY=your_api_key
RAGFLOW_BASE_URL=https://your-instance.com
RAGFLOW_TIMEOUT=30
RAGFLOW_MAX_RETRIES=3
```

### 代码配置
```python
import os
from dotenv import load_dotenv

load_dotenv()

client = RAGFlow(
    api_key=os.getenv("RAGFLOW_API_KEY"),
    base_url=os.getenv("RAGFLOW_BASE_URL"),
    timeout=int(os.getenv("RAGFLOW_TIMEOUT", 30)),
    max_retries=int(os.getenv("RAGFLOW_MAX_RETRIES", 3))
)
```

## 完整示例

### 知识库问答系统
```python
from ragflow import RAGFlow
import time

class KnowledgeBaseQA:
    def __init__(self, api_key, base_url):
        self.client = RAGFlow(api_key=api_key, base_url=base_url)
        self.assistant = None
        self.session = None

    def setup(self, dataset_name, documents):
        """创建知识库和助手"""
        # 创建数据集
        dataset = self.client.create_dataset(name=dataset_name)

        # 上传文档
        for doc_path in documents:
            with open(doc_path, "rb") as f:
                dataset.upload_file(file=f, name=doc_path)

        # 等待文档解析完成
        print("等待文档解析完成...")
        for doc in dataset.get_documents():
            doc.wait_for_parsing(timeout=300)

        # 创建聊天助手
        self.assistant = self.client.create_assistant(
            name=f"{dataset_name}助手",
            dataset_ids=[dataset.id],
            system_prompt=f"你是基于{dataset_name}知识库的专业助手。"
        )

        # 创建会话
        self.session = self.assistant.create_session()
        print("知识库设置完成!")

    def ask(self, question):
        """提问并获取回答"""
        if not self.session:
            raise ValueError("请先调用 setup() 方法")

        response = self.session.send_message(question)

        if response.success:
            return {
                "answer": response.answer,
                "references": response.references,
                "confidence": response.confidence
            }
        else:
            return {
                "error": response.error,
                "success": False
            }

# 使用示例
qa_system = KnowledgeBaseQA(
    api_key="your_api_key",
    base_url="https://your-instance.com"
)

# 设置知识库
qa_system.setup(
    dataset_name="技术文档",
    documents=["api_guide.pdf", "manual.docx", "faq.txt"]
)

# 开始问答
while True:
    question = input("\n请输入问题 (输入 'quit' 退出): ")
    if question.lower() == 'quit':
        break

    result = qa_system.ask(question)

    if result.get("success"):
        print(f"\n回答: {result['answer']}")
        if result['references']:
            print(f"参考来源: {result['references']}")
        print(f"置信度: {result['confidence']}")
    else:
        print(f"错误: {result['error']}")
```

## 参考资源

- **官方 GitHub 仓库**: https://github.com/infiniflow/ragflow
- **Python SDK 文档**: https://ragflow.io/docs/python-sdk
- **API 参考**: https://ragflow.io/docs/api-reference
- **示例代码**: https://github.com/infiniflow/ragflow/tree/main/sdk/python
- **官方网站**: https://ragflow.io

## 版本更新

本文档基于 RAGFlow 2024-2025 版本的 Python API。最新功能和 API 更新请参考官方文档和 GitHub 仓库的更新日志。