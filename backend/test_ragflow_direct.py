#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
直接测试RAGFlow集成的脚本
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置环境变量
os.environ['RAGFLOW_API_BASE_URL'] = 'http://localhost:80'
os.environ['RAGFLOW_API_KEY'] = 'ragflow-lmBmCb-T_yV1D8gaV65ThoTLPLWsAr4zKUh72XKFFBs'

from app.services.ragflow_service import RAGFlowService, RAGFlowConfig

def test_ragflow_integration():
    """测试RAGFlow集成"""
    print("Starting RAGFlow integration test...")

    try:
        # 创建配置
        config = RAGFlowConfig(
            api_base_url="http://localhost:80",
            api_key="ragflow-lmBmCb-T_yV1D8gaV65ThoTLPLWsAr4zKUh72XKFFBs",
            timeout=30,
            max_retries=3
        )

        print(f"Config created successfully: {config.api_base_url}")

        # 创建服务
        service = RAGFlowService(config)
        print("RAGFlow service created successfully")

        # 测试连接
        print("Testing connection...")
        is_connected = service.test_connection()
        print(f"Connection result: {is_connected}")

        if is_connected:
            print("Connection test successful")

            # 测试获取数据集
            print("Getting dataset list...")
            datasets = service.get_datasets()
            print(f"Found {len(datasets)} datasets")

            for dataset in datasets:
                print(f"   - {dataset.name}")
                print(f"     ID: {dataset.id}")
                print(f"     Document count: {dataset.document_count}")
                print(f"     Status: {dataset.status}")
                print(f"     Created at: {dataset.created_at}")
                print()

            return True
        else:
            print("Connection test failed")
            return False

    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_ragflow_integration()
    if success:
        print("\nRAGFlow integration test successful!")
    else:
        print("\nRAGFlow integration test failed!")

    sys.exit(0 if success else 1)