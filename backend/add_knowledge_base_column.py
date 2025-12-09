#!/usr/bin/env python3
"""
添加knowledge_base_config字段到flow_steps表
"""

import os
import sys
import sqlite3

# 添加项目路径到sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def add_knowledge_base_column():
    """添加knowledge_base_config列"""

    db_path = 'conversations.db'

    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("检查flow_steps表结构...")

        # 检查列是否已存在
        cursor.execute("PRAGMA table_info(flow_steps)")
        columns = [row[1] for row in cursor.fetchall()]

        print(f"当前列: {columns}")

        if '_knowledge_base_config' in columns:
            print("_knowledge_base_config列已存在，跳过添加")
            return True

        if 'knowledge_base_config' in columns:
            print("knowledge_base_config列已存在，跳过添加")
            return True

        print("添加_knowledge_base_config列到flow_steps表...")

        # SQLite支持直接添加列
        cursor.execute("""
            ALTER TABLE flow_steps
            ADD COLUMN _knowledge_base_config TEXT
        """)

        # 提交更改
        conn.commit()
        print("✅ _knowledge_base_config列添加成功！")

        # 验证列已添加
        cursor.execute("PRAGMA table_info(flow_steps)")
        new_columns = [row[1] for row in cursor.fetchall()]

        if '_knowledge_base_config' in new_columns:
            print("✅ 验证成功：_knowledge_base_config列已存在")
            return True
        else:
            print("❌ 验证失败：_knowledge_base_config列未找到")
            return False

    except Exception as e:
        print(f"❌ 添加列失败: {e}")
        if conn:
            conn.rollback()
        return False

    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("开始添加knowledge_base_config列...")

    success = add_knowledge_base_column()

    if success:
        print("🎉 knowledge_base_config列添加完成！")
    else:
        print("❌ knowledge_base_config列添加失败！")