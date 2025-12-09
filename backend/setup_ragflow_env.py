#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RAGFlow 环境配置辅助脚本

帮助用户快速配置 RAGFlow API 连接参数
"""

import os
import sys
from pathlib import Path

def create_env_file():
    """创建或更新 .env 文件"""
    env_file = Path('.env')

    print("🔧 RAGFlow 环境配置")
    print("=" * 40)

    # 检查是否已存在 .env 文件
    if env_file.exists():
        print("📁 发现现有的 .env 文件")
        with open(env_file, 'r', encoding='utf-8') as f:
            existing_content = f.read()
        print("现有内容:")
        print("-" * 30)
        print(existing_content)
        print("-" * 30)

        choice = input("是否要更新 RAGFlow 配置? (y/n): ").strip().lower()
        if choice != 'y':
            print("❌ 用户选择不更新配置")
            return False
    else:
        print("📝 创建新的 .env 文件")

    # 获取 RAGFlow 配置
    print("\n📝 请输入 RAGFlow 配置信息:")
    print("-" * 30)

    # API Key
    existing_api_key = os.getenv('RAGFLOW_API_KEY', '')
    api_key_prompt = f"RAGFlow API Key [{'str(existing_api_key[:20]) if existing_api_key else '尚未设置'}]: "
    api_key = input(api_key_prompt).strip()

    # Base URL
    existing_base_url = os.getenv('RAGFLOW_BASE_URL', 'https://api.ragflow.io')
    base_url_prompt = f"RAGFlow Base URL [{existing_base_url}]: "
    base_url = input(base_url_prompt).strip()

    if not base_url:
        base_url = 'https://api.ragflow.io'

    # 验证配置
    print("\n🔍 配置验证:")
    print("-" * 30)
    print(f"API Key: {'*' * (len(api_key) - 4) + api_key[-4:] if len(api_key) > 4 else api_key}")
    print(f"Base URL: {base_url}")

    confirm = input("\n确认配置正确吗? (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ 用户取消配置")
        return False

    # 写入 .env 文件
    try:
        # 读取现有内容
        existing_lines = []
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                existing_lines = f.readlines()

        # 过滤掉现有的 RAGFlow 配置
        filtered_lines = []
        skip_ragflow_vars = True
        for line in existing_lines:
            if line.strip().startswith(('RAGFLOW_', '#')):
                if not line.strip().startswith('#'):
                    skip_ragflow_vars = True
                    continue
            if not skip_ragflow_vars:
                filtered_lines.append(line)

        # 添加 RAGFlow 配置
        ragflow_config = [
            "# RAGFlow Configuration\n",
            f"RAGFLOW_API_KEY={api_key}\n",
            f"RAGFLOW_BASE_URL={base_url}\n",
            "# RAGFlow API Settings\n",
            "RAGFLOW_TIMEOUT=30\n",
            "RAGFLOW_MAX_RETRIES=3\n",
            "RAGFLOW_RETRY_DELAY=1.0\n",
            "RAGFLOW_VERIFY_SSL=true\n",
            "\n"
        ]

        # 写入文件
        with open(env_file, 'w', encoding='utf-8') as f:
            f.writelines(filtered_lines)
            f.writelines(ragflow_config)

        print(f"\n✅ 配置已保存到 {env_file}")
        print(f"📍 配置文件位置: {env_file.absolute()}")

        return True

    except Exception as e:
        print(f"❌ 配置保存失败: {e}")
        return False

def show_env_info():
    """显示当前环境配置"""
    print("🌍 当前 RAGFlow 环境配置:")
    print("-" * 40)

    ragflow_vars = [
        ('RAGFLOW_API_KEY', os.getenv('RAGFLOW_API_KEY')),
        ('RAGFLOW_BASE_URL', os.getenv('RAGFLOW_BASE_URL')),
        ('RAGFLOW_TIMEOUT', os.getenv('RAGFLOW_TIMEOUT')),
        ('RAGFLOW_MAX_RETRIES', os.getenv('RAGFLOW_MAX_RETRIES')),
        ('RAGFLOW_RETRY_DELAY', os.getenv('RAGFLOW_RETRY_DELAY')),
        ('RAGFLOW_VERIFY_SSL', os.getenv('RAGFLOW_VERIFY_SSL'))
    ]

    has_config = False
    for var_name, var_value in ragflow_vars:
        if var_value:
            if var_name == 'RAGFLOW_API_KEY':
                masked_value = '*' * (len(var_value) - 4) + var_value[-4:] if len(var_value) > 4 else var_value
                print(f"  {var_name}: {masked_value}")
            else:
                print(f"  {var_name}: {var_value}")
            has_config = True

    if not has_config:
        print("  ❌ 未配置 RAGFlow 环境变量")
        return False

    print("  ✅ 已配置 RAGFlow 环境变量")
    return True

def main():
    """主函数"""
    print("🛠️ RAGFlow 环境配置工具")
    print("=" * 50)

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == 'show':
            show_env_info()
        elif command == 'create':
            create_env_file()
        elif command == 'test':
            # 配置验证后运行测试
            if show_env_info():
                print("\n🧪 运行 RAGFlow API 测试...")
                import subprocess
                result = subprocess.run([
                    sys.executable, 'test_ragflow_chat.py'
                ], capture_output=True, text=True)

                print("测试输出:")
                print("-" * 30)
                print(result.stdout)
                if result.stderr:
                    print("错误信息:")
                    print("-" * 30)
                    print(result.stderr)
            else:
                print("❌ 请先配置 RAGFlow 环境变量")
        else:
            print(f"未知命令: {command}")
            print("可用命令: show, create, test")
    else:
        print("可用命令:")
        print("  python setup_ragflow_env.py show  - 显示当前配置")
        print("  python setup_ragflow_env.py create - 创建配置文件")
        print("  python setup_ragflow_env.py test   - 配置验证后测试")
        print("\n或者直接运行:")
        print("  python setup_ragflow_env.py  - 交互式配置")

if __name__ == "__main__":
    main()