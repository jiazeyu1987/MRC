#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RAGFlow 对话 API 测试程序

测试 RAGFlow API 获取真实的聊天数据
基于 https://ragflow.io/docs/dev/http_api_reference
"""

import os
import requests
import json
import logging
from typing import Dict, Any, List, Optional

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RAGFlowAPIClient:
    """RAGFlow API 客户端"""

    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """发送 HTTP 请求"""
        url = f"{self.base_url}{endpoint}"

        try:
            logger.info(f"发送 {method} 请求到: {url}")
            if data:
                logger.info(f"请求数据: {json.dumps(data, indent=2, ensure_ascii=False)}")

            response = self.session.request(method, url, json=data)
            response.raise_for_status()

            result = response.json()
            logger.info(f"响应状态: {response.status_code}")
            logger.info(f"响应数据: {json.dumps(result, indent=2, ensure_ascii=False)}")

            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {e}")
            raise

    def get_chat_assistants(self) -> List[Dict[str, Any]]:
        """获取所有聊天助手"""
        return self._make_request('GET', '/api/v1/chats')

    def get_chat_assistant(self, chat_id: str) -> Dict[str, Any]:
        """获取特定聊天助手详情"""
        return self._make_request('GET', f'/api/v1/chats/{chat_id}')

    def get_chat_sessions(self, chat_id: str) -> List[Dict[str, Any]]:
        """获取聊天助手的会话列表"""
        return self._make_request('GET', f'/api/v1/chats/{chat_id}/sessions')

    def get_chat_session(self, chat_id: str, session_id: str) -> Dict[str, Any]:
        """获取特定会话详情"""
        return self._make_request('GET', f'/api/v1/chats/{chat_id}/sessions/{session_id}')

    def chat_completion(self, chat_id: str, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """执行对话完成"""
        return self._make_request('POST', f'/api/v1/chats/{chat_id}/completions', {
            'messages': messages
        })

    def get_chat_messages(self, chat_id: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """获取聊天消息（如果支持的话）"""
        # 这个端点可能不存在，先尝试常见的端点
        endpoints = [
            f'/api/v1/chats/{chat_id}/messages',
            f'/api/v1/chats/{chat_id}/sessions/{session_id}/messages' if session_id else None
        ]

        for endpoint in endpoints:
            if endpoint is None:
                continue
            try:
                return self._make_request('GET', endpoint)
            except:
                logger.warning(f"端点 {endpoint} 不存在，尝试下一个")
                continue

        logger.error("无法获取聊天消息")
        return {}


def test_ragflow_chat():
    """测试 RAGFlow 聊天功能"""

    # 从环境变量或配置文件中获取 RAGFlow 配置
    api_key = os.getenv('RAGFLOW_API_KEY')
    base_url = os.getenv('RAGFLOW_BASE_URL', 'https://api.ragflow.io')

    if not api_key:
        logger.error("请设置 RAGFLOW_API_KEY 环境变量")
        return False

    if not base_url:
        logger.error("请设置 RAGFLOW_BASE_URL 环境变量")
        return False

    logger.info("开始测试 RAGFlow 对话 API...")
    logger.info(f"API Key: {api_key[:10]}...")
    logger.info(f"Base URL: {base_url}")

    try:
        client = RAGFlowAPIClient(api_key, base_url)

        # 1. 获取所有聊天助手
        logger.info("\n=== 1. 获取所有聊天助手 ===")
        assistants = client.get_chat_assistants()
        logger.info(f"找到 {len(assistants)} 个聊天助手")

        # 显示所有助手的基本信息
        for i, assistant in enumerate(assistants):
            logger.info(f"\n助手 {i+1}:")
            logger.info(f"  ID: {assistant.get('id', 'N/A')}")
            logger.info(f"  名称: {assistant.get('name', 'N/A')}")
            logger.info(f"  描述: {assistant.get('description', 'N/A')}")
            logger.info(f"  创建时间: {assistant.get('create_time', 'N/A')}")

            dataset_ids = assistant.get('dataset_ids', [])
            if dataset_ids:
                logger.info(f"  关联数据集: {', '.join(dataset_ids)}")

        # 2. 查找名为 "sdf" 的聊天助手
        logger.info("\n=== 2. 查找名为 'sdf' 的聊天助手 ===")
        sdf_assistant = None

        for assistant in assistants:
            if assistant.get('name') == 'sdf':
                sdf_assistant = assistant
                break

        if sdf_assistant:
            logger.info("✅ 找到名为 'sdf' 的聊天助手!")
            logger.info(f"助手 ID: {sdf_assistant.get('id')}")

            # 3. 获取该助手的详细信息
            logger.info(f"\n=== 3. 获取助手 '{sdf_assistant.get('id')}' 的详细信息 ===")
            assistant_detail = client.get_chat_assistant(sdf_assistant['id'])
            logger.info("助手详细信息:")
            logger.info(json.dumps(assistant_detail, indent=2, ensure_ascii=False))

            # 4. 获取该助手的会话列表
            logger.info(f"\n=== 4. 获取助手 '{sdf_assistant.get('id')}' 的会话列表 ===")
            sessions = client.get_chat_sessions(sdf_assistant['id'])
            logger.info(f"找到 {len(sessions)} 个会话")

            for i, session in enumerate(sessions):
                logger.info(f"\n会话 {i+1}:")
                logger.info(f"  ID: {session.get('id', 'N/A')}")
                logger.info(f"  名称: {session.get('name', 'N/A')}")
                logger.info(f"  创建时间: {session.get('create_time', 'N/A')}")
                logger.info(f"  更新时间: {session.get('update_time', 'N/A')}")
                logger.info(f"  消息数量: {session.get('message_count', 'N/A')}")

            # 5. 如果有会话，获取第一个会话的消息
            if sessions:
                first_session = sessions[0]
                logger.info(f"\n=== 5. 获取会话 '{first_session.get('id')}' 的消息 ===")

                try:
                    messages = client.get_chat_messages(
                        sdf_assistant['id'],
                        first_session['id']
                    )
                    logger.info("会话消息:")
                    logger.info(json.dumps(messages, indent=2, ensure_ascii=False))

                    # 6. 如果有消息，尝试进行对话测试
                    if messages and 'data' in messages:
                        message_data = messages['data']
                        if isinstance(message_data, list) and len(message_data) > 0:
                            logger.info(f"\n=== 6. 发送测试消息 ===")

                            # 准备测试消息
                            test_message = {
                                "role": "user",
                                "content": "你好，这是一个测试消息"
                            }

                            logger.info(f"发送消息: {test_message['content']}")
                            try:
                                response = client.chat_completion(sdf_assistant['id'], [test_message])
                                logger.info("对话响应:")
                                logger.info(json.dumps(response, indent=2, ensure_ascii=False))

                                # 提取回复内容
                                if 'data' in response:
                                    answer = response['data'].get('answer', '')
                                    if answer:
                                        logger.info(f"\n💬 AI 回复: {answer}")

                            except Exception as e:
                                logger.error(f"对话测试失败: {e}")

                except Exception as e:
                    logger.warning(f"获取会话消息失败: {e}")

            # 7. 尝试创建新会话
            logger.info(f"\n=== 7. 创建新会话测试 ===")
            try:
                new_session_data = {
                    "name": f"测试会话_{int(__import__('time').time())}"
                }
                logger.info(f"创建会话数据: {new_session_data}")

                new_session = client._make_request('POST', f'/api/v1/chats/{sdf_assistant["id"]}/sessions', new_session_data)
                logger.info("新会话创建成功:")
                logger.info(json.dumps(new_session, indent=2, ensure_ascii=False))

            except Exception as e:
                logger.error(f"创建新会话失败: {e}")

        else:
            logger.error("❌ 未找到名为 'sdf' 的聊天助手")
            return False

        logger.info("\n✅ RAGFlow 对话 API 测试成功完成!")
        return True

    except Exception as e:
        logger.error(f"❌ RAGFlow 对话 API 测试失败: {e}")
        return False


def main():
    """主函数"""
    print("🚀 RAGFlow 对话 API 测试程序")
    print("=" * 50)

    # 检查环境变量
    if not os.getenv('RAGFLOW_API_KEY'):
        print("❌ 错误: 请设置 RAGFLOW_API_KEY 环境变量")
        print("示例: export RAGFLOW_API_KEY='your-api-key-here'")
        print("示例: export RAGFLOW_BASE_URL='https://your-ragflow-instance.com'")
        return False

    if not os.getenv('RAGFLOW_BASE_URL'):
        print("❌ 错误: 请设置 RAGFLOW_BASE_URL 环境变量")
        print("示例: export RAGFLOW_BASE_URL='https://your-ragflow-instance.com'")
        return False

    # 运行测试
    success = test_ragflow_chat()

    print("\n" + "=" * 50)
    if success:
        print("✅ 测试完成 - 请查看上方的详细日志")
    else:
        print("❌ 测试失败 - 请检查 RAGFlow 配置和网络连接")

    return success


if __name__ == "__main__":
    main()