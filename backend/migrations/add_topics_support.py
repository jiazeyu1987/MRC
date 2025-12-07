#!/usr/bin/env python3
"""
数据库迁移脚本：为流程模板和会话表添加多议题支持

此脚本添加以下字段：
- flow_templates._topics (TEXT) - 存储多议题JSON数组
- sessions._topics (TEXT) - 存储多议题JSON数组

迁移策略：
1. 保持原有topic字段不变，确保向后兼容
2. 为现有的单topic数据迁移到新的topics字段
3. 新的topics字段优先级高于原有topic字段
"""

import sqlite3
import json
import sys
import os

def get_db_path():
    """获取数据库路径"""
    # 默认数据库文件路径
    db_path = os.path.join(os.path.dirname(__file__), '..', 'conversations.db')
    return db_path

def check_column_exists(cursor, table_name, column_name):
    """检查列是否存在"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [column[1] for column in cursor.fetchall()]
    return column_name in columns

def migrate_flow_templates(cursor):
    """迁移flow_templates表"""
    table_name = 'flow_templates'
    new_column = '_topics'

    if not check_column_exists(cursor, table_name, new_column):
        print(f"正在为 {table_name} 表添加 {new_column} 列...")
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {new_column} TEXT")

        # 将现有的topic数据迁移到新的topics字段
        print("正在迁移现有的topic数据到topics字段...")
        cursor.execute(f"SELECT id, topic FROM {table_name} WHERE topic IS NOT NULL AND topic != ''")
        rows = cursor.fetchall()

        for row in rows:
            template_id, topic = row
            if topic and topic.strip():
                topics_array = json.dumps([topic.strip()], ensure_ascii=False)
                cursor.execute(
                    f"UPDATE {table_name} SET {new_column} = ? WHERE id = ?",
                    (topics_array, template_id)
                )

        print(f"成功迁移 {len(rows)} 个模板的topic数据")
    else:
        print(f"{table_name} 表的 {new_column} 列已存在，跳过")

def migrate_sessions(cursor):
    """迁移sessions表"""
    table_name = 'sessions'
    new_column = '_topics'

    if not check_column_exists(cursor, table_name, new_column):
        print(f"正在为 {table_name} 表添加 {new_column} 列...")
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {new_column} TEXT")

        # 将现有的topic数据迁移到新的topics字段
        print("正在迁移现有的topic数据到topics字段...")
        cursor.execute(f"SELECT id, topic FROM {table_name} WHERE topic IS NOT NULL AND topic != ''")
        rows = cursor.fetchall()

        for row in rows:
            session_id, topic = row
            if topic and topic.strip():
                topics_array = json.dumps([topic.strip()], ensure_ascii=False)
                cursor.execute(
                    f"UPDATE {table_name} SET {new_column} = ? WHERE id = ?",
                    (topics_array, session_id)
                )

        print(f"成功迁移 {len(rows)} 个会话的topic数据")
    else:
        print(f"{table_name} 表的 {new_column} 列已存在，跳过")

def verify_migration(cursor):
    """验证迁移结果"""
    print("\n=== 迁移验证 ===")

    # 验证flow_templates
    cursor.execute("SELECT COUNT(*) FROM flow_templates")
    total_templates = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM flow_templates WHERE _topics IS NOT NULL")
    templates_with_topics = cursor.fetchone()[0]
    print(f"Flow Templates: {templates_with_topics}/{total_templates} 包含topics数据")

    # 验证sessions
    cursor.execute("SELECT COUNT(*) FROM sessions")
    total_sessions = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM sessions WHERE _topics IS NOT NULL")
    sessions_with_topics = cursor.fetchone()[0]
    print(f"Sessions: {sessions_with_topics}/{total_sessions} 包含topics数据")

    # 显示示例数据
    cursor.execute("SELECT id, name, topic, _topics FROM flow_templates WHERE _topics IS NOT NULL LIMIT 3")
    sample_templates = cursor.fetchall()
    if sample_templates:
        print("\n示例模板数据:")
        for template in sample_templates:
            print(f"  ID: {template[0]}, Name: {template[1]}")
            print(f"    Topic: {template[2]}")
            print(f"    Topics: {template[3]}")

def main():
    """主函数"""
    db_path = get_db_path()

    if not os.path.exists(db_path):
        print(f"错误: 数据库文件不存在: {db_path}")
        sys.exit(1)

    try:
        print(f"正在连接数据库: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("开始数据库迁移...")

        # 启用外键约束
        cursor.execute("PRAGMA foreign_keys = ON")

        # 执行迁移
        migrate_flow_templates(cursor)
        migrate_sessions(cursor)

        # 提交更改
        conn.commit()
        print("数据库迁移完成!")

        # 验证迁移
        verify_migration(cursor)

        conn.close()
        print("迁移脚本执行完成!")

    except Exception as e:
        print(f"迁移过程中发生错误: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        sys.exit(1)

if __name__ == "__main__":
    main()