#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RAGFlow HTTP API Examples
=========================

本文件将 https://ragflow.io/docs/dev/http_api_reference 中的常用接口，
以 Python 函数示例的形式实现，方便你在本地直接调用和二次封装。

特点：
- 统一使用 backend/.env 中的 RAGFlow 配置（RAGFLOW_API_KEY / RAGFLOW_API_BASE_URL 等）
- 使用 requests 库进行 HTTP 调用
- 涉及文件操作的接口，示例中会在本地创建临时文件进行上传 / 下载 / 删除

注意：这些函数都是“示例”，请根据你的业务需要做进一步封装或异常处理。
"""

import json
import os
import tempfile
from typing import Dict, Any, List, Optional, Tuple

import requests
from dotenv import load_dotenv


# ---------------------------------------------------------------------------
# 基础工具：环境与 HTTP Session
# ---------------------------------------------------------------------------

def load_env() -> None:
    """
    加载环境变量。

    优先 backend/.env，其次默认的 .env 解析逻辑。
    """
    backend_env = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(backend_env):
        load_dotenv(backend_env)
    else:
        load_dotenv()


def build_session() -> Tuple[requests.Session, Dict[str, Any]]:
    """
    基于环境变量创建带认证信息的 requests.Session。

    依赖的环境变量：
    - RAGFLOW_API_KEY
    - RAGFLOW_API_BASE_URL 或 RAGFLOW_BASE_URL
    - RAGFLOW_TIMEOUT（可选）
    - RAGFLOW_VERIFY_SSL（可选）
    """
    load_env()

    api_key = os.getenv("RAGFLOW_API_KEY")
    base_url = (
        os.getenv("RAGFLOW_API_BASE_URL")
        or os.getenv("RAGFLOW_BASE_URL")
        or "http://localhost:80"
    )
    timeout = int(os.getenv("RAGFLOW_TIMEOUT", "30"))
    verify_ssl = os.getenv("RAGFLOW_VERIFY_SSL", "true").lower() == "true"

    if not api_key:
        raise RuntimeError("RAGFLOW_API_KEY 未配置，请在 backend/.env 或环境变量中设置。")
    if not base_url:
        raise RuntimeError("RAGFLOW_API_BASE_URL 未配置。")

    session = requests.Session()
    session.headers.update(
        {
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "ragflow-http-examples/0.1",
        }
    )

    cfg = {
        "BASE_URL": base_url.rstrip("/"),
        "TIMEOUT": timeout,
        "VERIFY_SSL": verify_ssl,
    }
    return session, cfg


def _full_url(cfg: Dict[str, Any], path: str) -> str:
    path = path if path.startswith("/") else "/" + path
    return cfg["BASE_URL"] + path


def api_get(session: requests.Session, cfg: Dict[str, Any], path: str, params: Optional[Dict[str, Any]] = None) -> Any:
    url = _full_url(cfg, path)
    resp = session.get(url, params=params or {}, timeout=cfg["TIMEOUT"], verify=cfg["VERIFY_SSL"])
    resp.raise_for_status()
    return resp.json()


def api_post_json(
    session: requests.Session,
    cfg: Dict[str, Any],
    path: str,
    body: Dict[str, Any],
) -> Any:
    url = _full_url(cfg, path)
    resp = session.post(
        url,
        data=json.dumps(body, ensure_ascii=False),
        headers={"Content-Type": "application/json", **session.headers},
        timeout=cfg["TIMEOUT"],
        verify=cfg["VERIFY_SSL"],
    )
    resp.raise_for_status()
    return resp.json()


def api_post_form(
    session: requests.Session,
    cfg: Dict[str, Any],
    path: str,
    data: Dict[str, Any],
    files: Dict[str, Any],
) -> Any:
    url = _full_url(cfg, path)
    # 对文件上传接口不要强制 Content-Type: application/json
    headers = {k: v for k, v in session.headers.items() if k.lower() != "content-type"}
    resp = session.post(
        url,
        data=data,
        files=files,
        headers=headers,
        timeout=cfg["TIMEOUT"],
        verify=cfg["VERIFY_SSL"],
    )
    resp.raise_for_status()
    return resp.json()


def api_put_json(
    session: requests.Session,
    cfg: Dict[str, Any],
    path: str,
    body: Dict[str, Any],
) -> Any:
    url = _full_url(cfg, path)
    resp = session.put(
        url,
        data=json.dumps(body, ensure_ascii=False),
        headers={"Content-Type": "application/json", **session.headers},
        timeout=cfg["TIMEOUT"],
        verify=cfg["VERIFY_SSL"],
    )
    resp.raise_for_status()
    return resp.json()


def api_delete_json(
    session: requests.Session,
    cfg: Dict[str, Any],
    path: str,
    body: Optional[Dict[str, Any]] = None,
) -> Any:
    url = _full_url(cfg, path)
    if body is None:
        resp = session.delete(url, timeout=cfg["TIMEOUT"], verify=cfg["VERIFY_SSL"])
    else:
        resp = session.delete(
            url,
            data=json.dumps(body, ensure_ascii=False),
            headers={"Content-Type": "application/json", **session.headers},
            timeout=cfg["TIMEOUT"],
            verify=cfg["VERIFY_SSL"],
        )
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Dataset Management 示例
# ---------------------------------------------------------------------------

def example_list_datasets(session: requests.Session, cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    示例：列出数据集（知识库）
    GET /api/v1/datasets
    """
    resp = api_get(
        session,
        cfg,
        "/api/v1/datasets",
        params={"page": 1, "page_size": 30, "orderby": "create_time", "desc": True},
    )
    print("[example_list_datasets] response:", json.dumps(resp, ensure_ascii=False, indent=2))
    return resp.get("data", [])


def example_create_dataset(session: requests.Session, cfg: Dict[str, Any], name: str) -> Dict[str, Any]:
    """
    示例：创建数据集
    POST /api/v1/datasets
    """
    body = {
        "name": name,
        "description": f"Demo dataset created from examples: {name}",
    }
    resp = api_post_json(session, cfg, "/api/v1/datasets", body)
    print("[example_create_dataset] response:", json.dumps(resp, ensure_ascii=False, indent=2))
    return resp


def example_get_dataset(session: requests.Session, cfg: Dict[str, Any], dataset_id: str) -> Dict[str, Any]:
    """
    示例：获取单个数据集详情
    GET /api/v1/datasets/{dataset_id}
    """
    resp = api_get(session, cfg, f"/api/v1/datasets/{dataset_id}")
    print("[example_get_dataset] response:", json.dumps(resp, ensure_ascii=False, indent=2))
    return resp


def example_update_dataset(
    session: requests.Session,
    cfg: Dict[str, Any],
    dataset_id: str,
    new_name: Optional[str] = None,
    new_description: Optional[str] = None,
) -> Dict[str, Any]:
    """
    示例：更新数据集元信息
    PUT /api/v1/datasets/{dataset_id}
    """
    body: Dict[str, Any] = {}
    if new_name is not None:
        body["name"] = new_name
    if new_description is not None:
        body["description"] = new_description

    resp = api_put_json(session, cfg, f"/api/v1/datasets/{dataset_id}", body)
    print("[example_update_dataset] response:", json.dumps(resp, ensure_ascii=False, indent=2))
    return resp


def example_delete_dataset(session: requests.Session, cfg: Dict[str, Any], dataset_id: str) -> Dict[str, Any]:
    """
    示例：删除数据集
    DELETE /api/v1/datasets/{dataset_id}
    """
    resp = api_delete_json(session, cfg, f"/api/v1/datasets/{dataset_id}")
    print("[example_delete_dataset] response:", json.dumps(resp, ensure_ascii=False, indent=2))
    return resp


# ---------------------------------------------------------------------------
# File / Document Management 示例
# ---------------------------------------------------------------------------

def example_upload_document(
    session: requests.Session,
    cfg: Dict[str, Any],
    dataset_id: str,
    file_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    示例：上传文档到数据集
    参考接口：POST /api/v1/datasets/{dataset_id}/documents

    - 如果未提供 file_path，则在本地创建一个临时 txt 文件进行上传。
    """
    if file_path is None:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".txt", prefix="ragflow_demo_upload_", mode="w", encoding="utf-8")
        tmp.write("This is a demo document uploaded to RAGFlow.\nIt is safe to delete.")
        tmp.close()
        file_path = tmp.name
        auto_delete = True
    else:
        auto_delete = False

    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f)}
        data = {}  # 也可以加 name/description 等字段
        resp = api_post_form(session, cfg, f"/api/v1/datasets/{dataset_id}/documents", data, files)

    if auto_delete:
        try:
            os.remove(file_path)
        except OSError:
            pass

    print("[example_upload_document] response:", json.dumps(resp, ensure_ascii=False, indent=2))
    return resp


def example_list_documents(
    session: requests.Session,
    cfg: Dict[str, Any],
    dataset_id: str,
) -> Dict[str, Any]:
    """
    示例：列出数据集中的文档
    GET /api/v1/datasets/{dataset_id}/documents
    """
    resp = api_get(
        session,
        cfg,
        f"/api/v1/datasets/{dataset_id}/documents",
        params={"page": 1, "size": 20},
    )
    print("[example_list_documents] response:", json.dumps(resp, ensure_ascii=False, indent=2))
    return resp


def example_download_document(
    session: requests.Session,
    cfg: Dict[str, Any],
    dataset_id: str,
    document_id: str,
    dest_path: Optional[str] = None,
) -> str:
    """
    示例：下载文档内容到本地临时文件
    参考接口：GET /api/v1/datasets/{dataset_id}/documents/{document_id}/download

    返回：保存到本地的路径。
    """
    url = _full_url(cfg, f"/api/v1/datasets/{dataset_id}/documents/{document_id}/download")
    resp = session.get(url, timeout=cfg["TIMEOUT"], verify=cfg["VERIFY_SSL"], stream=True)
    resp.raise_for_status()

    if dest_path is None:
        fd, dest_path = tempfile.mkstemp(prefix="ragflow_demo_download_", suffix=".bin")
        os.close(fd)

    with open(dest_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    print(f"[example_download_document] 保存到本地: {dest_path}")
    return dest_path


def example_delete_document(
    session: requests.Session,
    cfg: Dict[str, Any],
    dataset_id: str,
    document_id: str,
) -> Dict[str, Any]:
    """
    示例：删除数据集中的单个文档
    DELETE /api/v1/datasets/{dataset_id}/documents/{document_id}
    """
    resp = api_delete_json(session, cfg, f"/api/v1/datasets/{dataset_id}/documents/{document_id}")
    print("[example_delete_document] response:", json.dumps(resp, ensure_ascii=False, indent=2))
    return resp


# ---------------------------------------------------------------------------
# Chunk Management & Retrieval 示例
# ---------------------------------------------------------------------------

def example_list_chunks(
    session: requests.Session,
    cfg: Dict[str, Any],
    dataset_id: str,
    document_id: str,
) -> Dict[str, Any]:
    """
    示例：列出文档的 chunks
    GET /api/v1/datasets/{dataset_id}/documents/{document_id}/chunks
    """
    resp = api_get(session, cfg, f"/api/v1/datasets/{dataset_id}/documents/{document_id}/chunks")
    print("[example_list_chunks] response:", json.dumps(resp, ensure_ascii=False, indent=2))
    return resp


def example_retrieve_chunks(
    session: requests.Session,
    cfg: Dict[str, Any],
    question: str,
    dataset_ids: Optional[List[str]] = None,
    document_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    示例：“搜索 / 检索”接口
    POST /api/v1/retrieval
    """
    body: Dict[str, Any] = {
        "question": question,
        "page": 1,
        "page_size": 10,
    }
    if dataset_ids:
        body["dataset_ids"] = dataset_ids
    if document_ids:
        body["document_ids"] = document_ids

    resp = api_post_json(session, cfg, "/api/v1/retrieval", body)
    print("[example_retrieve_chunks] response:", json.dumps(resp, ensure_ascii=False, indent=2))
    return resp


# ---------------------------------------------------------------------------
# Chat Assistant Management & Conversation 示例
# ---------------------------------------------------------------------------

def example_list_chat_assistants(session: requests.Session, cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    示例：列出 Chat Assistants
    GET /api/v1/chats
    """
    resp = api_get(
        session,
        cfg,
        "/api/v1/chats",
        params={"page": 1, "page_size": 30, "orderby": "create_time", "desc": True},
    )
    print("[example_list_chat_assistants] response:", json.dumps(resp, ensure_ascii=False, indent=2))
    return resp.get("data", [])


def example_converse_with_chat_assistant(
    session: requests.Session,
    cfg: Dict[str, Any],
    chat_id: str,
    question: str = "Hello, please introduce yourself.",
    stream: bool = False,
) -> Dict[str, Any]:
    """
    示例：与 Chat Assistant 对话
    POST /api/v1/chats/{chat_id}/completions
    """
    body = {
        "question": question,
        "stream": stream,
    }
    resp = api_post_json(session, cfg, f"/api/v1/chats/{chat_id}/completions", body)
    print("[example_converse_with_chat_assistant] response:", json.dumps(resp, ensure_ascii=False, indent=2))
    return resp


# ---------------------------------------------------------------------------
# Agent Management & Conversation 示例
# ---------------------------------------------------------------------------

def example_list_agents(session: requests.Session, cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    示例：列出 Agents
    GET /api/v1/agents
    """
    resp = api_get(
        session,
        cfg,
        "/api/v1/agents",
        params={"page": 1, "page_size": 30, "orderby": "create_time", "desc": True},
    )
    print("[example_list_agents] response:", json.dumps(resp, ensure_ascii=False, indent=2))
    return resp.get("data", [])


def example_converse_with_agent(
    session: requests.Session,
    cfg: Dict[str, Any],
    agent_id: str,
    question: str = "Hello, what can you do?",
    stream: bool = False,
) -> Dict[str, Any]:
    """
    示例：与 Agent 对话
    POST /api/v1/agents/{agent_id}/completions
    """
    body = {
        "question": question,
        "stream": stream,
    }
    resp = api_post_json(session, cfg, f"/api/v1/agents/{agent_id}/completions", body)
    print("[example_converse_with_agent] response:", json.dumps(resp, ensure_ascii=False, indent=2))
    return resp


# ---------------------------------------------------------------------------
# OpenAI-Compatible Chat Completion 示例
# ---------------------------------------------------------------------------

def example_openai_compatible_chat_completion(
    session: requests.Session,
    cfg: Dict[str, Any],
    chat_id: str,
) -> Dict[str, Any]:
    """
    示例：OpenAI 兼容接口
    POST /api/v1/chats_openai/{chat_id}/chat/completions
    """
    body = {
        "model": "demo-model",
        "messages": [
            {"role": "user", "content": "Say this is a test!"},
        ],
        "stream": False,
    }
    resp = api_post_json(session, cfg, f"/api/v1/chats_openai/{chat_id}/chat/completions", body)
    print("[example_openai_compatible_chat_completion] response:", json.dumps(resp, ensure_ascii=False, indent=2))
    return resp


# ---------------------------------------------------------------------------
# 简单 main：演示如何串联调用上述示例函数
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    s, conf = build_session()
    print("RAGFlow base URL:", conf["BASE_URL"])

    # 1. 列出数据集
    datasets = example_list_datasets(s, conf)
    if not datasets:
        print("当前无数据集，可使用 example_create_dataset 创建一个。")
    else:
        ds_id = datasets[0].get("id")
        print("使用第一个数据集进行后续示例，dataset_id =", ds_id)

        # 2. 文档上传 / 列表 / 检索
        example_upload_document(s, conf, ds_id)
        docs_resp = example_list_documents(s, conf, ds_id)

        # 兼容多种返回结构：data.documents(list) 或 data(list/dict)
        data = docs_resp.get("data", {})
        docs: List[Dict[str, Any]] = []
        if isinstance(data, dict):
            if isinstance(data.get("documents"), list):
                docs = data["documents"]
            elif isinstance(data.get("data"), list):
                docs = data["data"]
        elif isinstance(data, list):
            docs = data

        if isinstance(docs, dict):
            # 如果是 dict（可能是 { "0": {...}, ... }），转成列表
            docs = list(docs.values())

        if docs:
            doc_id = docs[0].get("id")
            if doc_id:
                example_list_chunks(s, conf, ds_id, doc_id)
                example_retrieve_chunks(s, conf, "What is advantage of RAGFlow?", [ds_id])
            else:
                print("警告：第一条文档记录中未找到 id 字段，跳过 chunk 示例。")
        else:
            print("未能从文档列表响应中解析出文档数组，跳过 chunk / 检索示例。")

    # 3. Chat assistants & agents 仅作为调用示例，不保证实例已存在
    chats = example_list_chat_assistants(s, conf)
    if chats:
        example_converse_with_chat_assistant(s, conf, chats[0]["id"])

    agents = example_list_agents(s, conf)
    if agents:
        example_converse_with_agent(s, conf, agents[0]["id"])
