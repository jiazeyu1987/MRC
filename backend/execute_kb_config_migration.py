#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
手动执行知识库配置数据库迁移的脚本
由于Python环境问题，使用此脚本替代flask db upgrade
"""

import sqlite3
import os
import sys
from pathlib import Path

def execute_migration():
    """执行知识库配置数据库迁移"""

    # 数据库文件路径
    db_path = 'multi_role_chat.db'

    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return False

    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查是否已存在 _knowledge_base_config 字段
        cursor.execute("PRAGMA table_info(flow_steps)")
        columns = [column[1] for column in cursor.fetchall()]

        if '_knowledge_base_config' in columns:
            print("✅ _knowledge_base_config 字段已存在，跳过迁移")
            return True

        print("📝 开始添加 _knowledge_base_config 字段到 flow_steps 表...")

        # 添加字段
        cursor.execute("""
            ALTER TABLE flow_steps
            ADD COLUMN _knowledge_base_config TEXT
        """)

        # 创建索引（可选）
        try:
            cursor.execute("""
                CREATE INDEX idx_flow_steps_knowledge_base_config
                ON flow_steps (_knowledge_base_config)
            """)
            print("✅ 索引创建成功")
        except Exception as e:
            print(f"⚠️  索引创建失败（可能已存在）: {e}")

        # 提交更改
        conn.commit()
        print("✅ _knowledge_base_config 字段添加成功")

        # 验证字段是否添加成功
        cursor.execute("PRAGMA table_info(flow_steps)")
        columns = [column[1] for column in cursor.fetchall()]

        if '_knowledge_base_config' in columns:
            print("✅ 字段验证成功")
            return True
        else:
            print("❌ 字段验证失败")
            return False

    except Exception as e:
        print(f"❌ 迁移执行失败: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def check_migration_status():
    """检查迁移状态"""
    db_path = 'multi_role_chat.db'

    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查表结构
        cursor.execute("PRAGMA table_info(flow_steps)")
        columns = cursor.fetchall()

        print("📋 flow_steps 表结构:")
        for col in columns:
            field_type = "TEXT" if col[2].upper() == "TEXT" else col[2].upper()
            nullable = "NULL" if col[3] == 0 else "NOT NULL"
            print(f"  - {col[1]} ({field_type}) {nullable}")

        # 检查是否有 _knowledge_base_config 字段
        column_names = [col[1] for col in columns]
        has_kb_config = '_knowledge_base_config' in column_names

        if has_kb_config:
            print("✅ _knowledge_base_config 字段已存在")

            # 检查现有数据
            cursor.execute("""
                SELECT COUNT(*) FROM flow_steps
                WHERE _knowledge_base_config IS NOT NULL AND _knowledge_base_config != ''
            """)
            count = cursor.fetchone()[0]
            print(f"📊 已有知识库配置的步骤数量: {count}")

        else:
            print("❌ _knowledge_base_config 字段不存在")

        return has_kb_config

    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    print("🚀 开始知识库配置数据库迁移...")

    # 检查当前状态
    print("\n📊 检查迁移前状态:")
    check_migration_status()

    print("\n🔧 执行迁移...")
    success = execute_migration()

    print("\n📊 检查迁移后状态:")
    check_migration_status()

    if success:
        print("\n✅ 迁移执行成功！")
        sys.exit(0)
    else:
        print("\n❌ 迁移执行失败！")
        sys.exit(1)