#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RAGFlow HTTP API demo

功能：
1. 获取所有知识库（数据集）
2. 使用指定知识库做检索（/api/v1/retrieval）
3. 获取所有聊天助手（chat assistants），并和第一个助手对话
4. 获取所有智能体（agents），并和第一个智能体对话

参考文档：
https://ragflow.io/docs/dev/http_api_reference
"""

import os
import json

import requests
from dotenv import load_dotenv


def load_env():
    """
    加载环境变量

    优先使用 backend/.env（与你当前项目结构匹配），
    如果调用前已经在其他地方 load_dotenv 也不会冲突。
    """
    # 如果从项目根目录运行，则 backend/.env 存在
    backend_env = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(backend_env):
        load_dotenv(backend_env)
    else:
        # 回退到默认查找（当前目录及父目录）
        load_dotenv()


def build_session():
    """基于环境变量构建 requests 会话"""
    load_env()

    api_key = os.getenv("RAGFLOW_API_KEY")
    base_url = (
        os.getenv("RAGFLOW_API_BASE_URL")
        or os.getenv("RAGFLOW_BASE_URL")
        or "http://localhost:80"
    )
    timeout = int(os.getenv("RAGFLOW_TIMEOUT", "30"))
    verify_ssl = os.getenv("RAGFLOW_VERIFY_SSL", "true").lower() == "true"

    if not api_key or not base_url:
        raise RuntimeError(
            "请先在环境变量或 backend/.env 中配置 RAGFLOW_API_KEY 和 RAGFLOW_API_BASE_URL"
        )

    session = requests.Session()
    session.headers.update(
        {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "ragflow-http-demo/0.1",
        }
    )

    config = {
        "BASE_URL": base_url.rstrip("/"),
        "TIMEOUT": timeout,
        "VERIFY_SSL": verify_ssl,
        "API_KEY": api_key,
    }
    return session, config


def api_get(session, cfg, path: str, params=None):
    url = cfg["BASE_URL"] + path
    resp = session.get(
        url, params=params or {}, timeout=cfg["TIMEOUT"], verify=cfg["VERIFY_SSL"]
    )
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, dict) and data.get("code") not in (None, 0):
        raise RuntimeError(f"API GET {path} 返回错误: {data}")
    return data


def api_post(session, cfg, path: str, body: dict):
    url = cfg["BASE_URL"] + path
    resp = session.post(
        url,
        data=json.dumps(body, ensure_ascii=False),
        timeout=cfg["TIMEOUT"],
        verify=cfg["VERIFY_SSL"],
    )
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, dict) and data.get("code") not in (None, 0):
        raise RuntimeError(f"API POST {path} 返回错误: {data}")
    return data


def list_datasets(session, cfg):
    """列出所有知识库（数据集）: GET /api/v1/datasets"""
    print("\n==== 1. 获取数据集（知识库） ====")
    data = api_get(
        session,
        cfg,
        "/api/v1/datasets",
        params={"page": 1, "page_size": 50, "orderby": "create_time", "desc": True},
    )

    items = data.get("data", [])
    total = data.get("total", len(items))
    print(f"共找到数据集 {total} 个")
    for ds in items:
        print(f"- {ds['id']} | {ds['name']} | 文档数: {ds.get('document_count', 0)}")

    return items


def retrieve_from_dataset(session, cfg, dataset_id: str):
    """检索（搜索）: POST /api/v1/retrieval"""
    print("\n==== 2. 在知识库中检索（/api/v1/retrieval） ====")
    body = {
        "question": "What is advantage of RAGFlow?",
        "dataset_ids": [dataset_id],
        "page": 1,
        "page_size": 5,
    }
    data = api_post(session, cfg, "/api/v1/retrieval", body)

    print("检索结果：")
    raw_data = data.get("data", {})

    # RAGFlow 文档里 retrieval 的返回有两种常见结构：
    # 1) data.chunks 是一个 list
    # 2) data.chunks 是一个 dict，key 为字符串/索引
    chunks = raw_data.get("chunks", raw_data)
    items = []
    if isinstance(chunks, list):
        items = chunks
    elif isinstance(chunks, dict):
        # 转成按 key 排序后的列表，方便展示
        items = [chunks[k] for k in sorted(chunks.keys())]

    print(f"- 返回 chunks 数量: {len(items)}")

    if items:
        print("首条 chunk 内容预览：")
        first = items[0]
        print(json.dumps(first, ensure_ascii=False, indent=2))
    else:
        print("没有检索到任何 chunk，原始 data 如下：")
        print(json.dumps(raw_data, ensure_ascii=False, indent=2))
    return data


def list_chats(session, cfg):
    """列出所有聊天助手: GET /api/v1/chats"""
    print("\n==== 3. 获取 Chat Assistants（/api/v1/chats） ====")
    data = api_get(
        session,
        cfg,
        "/api/v1/chats",
        params={"page": 1, "page_size": 50, "orderby": "create_time", "desc": True},
    )
    items = data.get("data", [])
    total = data.get("total", len(items))
    print(f"共找到 Chat Assistant {total} 个")
    for chat in items:
        print(f"- {chat['id']} | {chat['name']} | 描述: {chat.get('description')}")
    return items


def chat_with_assistant(session, cfg, chat_id: str):
    """和指定聊天助手对话: POST /api/v1/chats/{chat_id}/completions"""
    print("\n==== 4. 和第一个 Chat Assistant 聊天（/api/v1/chats/{chat_id}/completions） ====")
    body = {
        # 使用纯 ASCII，避免某些部署下的编码问题
        "question": "Hello, please introduce yourself.",
        "stream": False,
    }
    try:
        data = api_post(session, cfg, f"/api/v1/chats/{chat_id}/completions", body)
        print("聊天助手返回：")
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return data
    except RuntimeError as e:
        print(f"聊天助手 API 调用失败：{e}")
        return None


def list_agents(session, cfg):
    """列出所有智能体: GET /api/v1/agents"""
    print("\n==== 5. 获取 Agents（智能体）（/api/v1/agents） ====")
    data = api_get(
        session,
        cfg,
        "/api/v1/agents",
        params={"page": 1, "page_size": 50, "orderby": "create_time", "desc": True},
    )
    items = data.get("data", [])
    total = data.get("total", len(items))
    print(f"共找到 Agent {total} 个")
    for agent in items:
        title = agent.get("title") or agent.get("name")
        print(f"- {agent['id']} | {title} | 描述: {agent.get('description')}")
    return items


def chat_with_agent(session, cfg, agent_id: str):
    """和指定智能体对话: POST /api/v1/agents/{agent_id}/completions"""
    print("\n==== 6. 和第一个 Agent 聊天（/api/v1/agents/{agent_id}/completions） ====")
    body = {
        "question": "Hello, what can you do?",
        "stream": False,
    }
    try:
        data = api_post(session, cfg, f"/api/v1/agents/{agent_id}/completions", body)
        print("Agent 返回：")
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return data
    except RuntimeError as e:
        print(f"Agent API 调用失败：{e}")
        return None


def main():
    session, cfg = build_session()

    print("使用的 RAGFlow 配置：")
    print(f"- BASE_URL = {cfg['BASE_URL']}")
    print(f"- API_KEY (前 8 位) = {cfg['API_KEY'][:8]}...")

    # 1. 知识库（数据集）
    datasets = list_datasets(session, cfg)
    if not datasets:
        print("当前没有任何数据集，后续检索步骤会跳过。")
    else:
        first_ds_id = datasets[0]["id"]
        retrieve_from_dataset(session, cfg, first_ds_id)

    # 2. Chat Assistants
    chats = list_chats(session, cfg)
    if chats:
        first_chat_id = chats[0]["id"]
        chat_with_assistant(session, cfg, first_chat_id)
    else:
        print("没有找到任何 Chat Assistant，跳过聊天示例。")

    # 3. Agents
    agents = list_agents(session, cfg)
    if agents:
        first_agent_id = agents[0]["id"]
        chat_with_agent(session, cfg, first_agent_id)
    else:
        print("没有找到任何 Agent，跳过智能体聊天示例。")


if __name__ == "__main__":
    main()
