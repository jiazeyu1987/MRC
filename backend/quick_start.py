#!/usr/bin/env python3
"""
快速启动脚本 - MRC Backend
用于快速设置和启动后端服务
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python():
    """检查Python版本"""
    if sys.version_info < (3, 8):
        print("❌ 需要Python 3.8或更高版本")
        return False
    print(f"✅ Python版本: {sys.version}")
    return True

def check_dependencies():
    """检查依赖是否安装"""
    try:
        with open('requirements.txt', 'r') as f:
            requirements = f.read().splitlines()

        missing = []
        for req in requirements:
            if req.strip() and not req.startswith('#'):
                package = req.split('==')[0].split('>=')[0].split('<=')[0]
                try:
                    __import__(package.replace('-', '_'))
                except ImportError:
                    missing.append(req)

        if missing:
            print(f"❌ 缺少依赖: {', '.join(missing)}")
            print("📦 请运行: pip install -r requirements.txt")
            return False

        print("✅ 所有依赖已安装")
        return True
    except FileNotFoundError:
        print("❌ requirements.txt文件不存在")
        return False

def check_database():
    """检查数据库文件"""
    if not Path('conversations.db').exists():
        print("❌ 数据库文件不存在")
        return False

    try:
        import sqlite3
        conn = sqlite3.connect('conversations.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        conn.close()
        print(f"✅ 数据库正常，包含 {len(tables)} 个表")
        return True
    except Exception as e:
        print(f"❌ 数据库错误: {e}")
        return False

def check_environment():
    """检查环境配置"""
    if not Path('.env').exists():
        print("⚠️  .env文件不存在，将使用默认配置")
        if Path('.env.example').exists():
            print("💡 建议复制 .env.example 为 .env")
        return True

    print("✅ 环境配置文件存在")
    return True

def main():
    """主函数"""
    print("🚀 MRC Backend 启动检查\n")

    # 检查各项
    checks = [
        ("Python环境", check_python),
        ("依赖包", check_dependencies),
        ("数据库", check_database),
        ("环境配置", check_environment)
    ]

    all_passed = True
    for name, check_func in checks:
        print(f"检查 {name}...")
        if not check_func():
            all_passed = False
        print()

    if not all_passed:
        print("❌ 启动检查失败，请先解决上述问题")
        return 1

    print("✅ 所有检查通过！")

    # 启动服务器
    print("\n🎯 启动后端服务器...")
    try:
        subprocess.run([sys.executable, 'run.py'], check=True)
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"❌ 启动失败: {e}")
        return 1
    except FileNotFoundError:
        print("❌ run.py文件不存在")
        return 1

if __name__ == '__main__':
    sys.exit(main())