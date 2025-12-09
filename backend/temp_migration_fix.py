#!/usr/bin/env python3
"""
临时迁移修复脚本 - 使用Flask应用上下文
"""

import sqlite3
import os

def fix_database():
    """直接修复数据库"""
    db_path = os.path.join(os.path.dirname(__file__), 'conversations.db')

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查表结构
        cursor.execute("PRAGMA table_info(flow_steps)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"当前列: {columns}")

        if '_knowledge_base_config' not in columns:
            print("添加_knowledge_base_config列...")
            cursor.execute("ALTER TABLE flow_steps ADD COLUMN _knowledge_base_config TEXT")
            conn.commit()
            print("✅ 列添加成功")
        else:
            print("❌ 列已存在")

        # 验证
        cursor.execute("PRAGMA table_info(flow_steps)")
        new_columns = [row[1] for row in cursor.fetchall()]
        print(f"新列列表: {new_columns}")

        conn.close()
        return True

    except Exception as e:
        print(f"错误: {e}")
        return False

if __name__ == "__main__":
    fix_database()