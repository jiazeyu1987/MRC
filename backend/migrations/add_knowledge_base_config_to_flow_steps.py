#!/usr/bin/env python3
"""
数据库迁移脚本：为流程步骤表添加知识库配置支持

此脚本添加以下字段：
- flow_steps._knowledge_base_config (TEXT) - 存储知识库检索配置JSON

迁移策略：
1. 添加新字段到flow_steps表
2. 为现有步骤设置默认的知识库配置（禁用状态）
3. 确保向后兼容性
"""

import sqlite3
import json
import sys
import os

def get_db_path():
    """获取数据库路径"""
    # 从环境变量读取数据库配置
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

    database_url = os.getenv('DATABASE_URL', 'sqlite:///multi_role_chat.db')

    # 解析SQLite路径
    if database_url.startswith('sqlite:///'):
        db_path = database_url[10:]  # 移除 'sqlite:///' 前缀

        # 如果是相对路径，转换为绝对路径
        if not os.path.isabs(db_path):
            db_path = os.path.join(os.path.dirname(__file__), '..', db_path)
    else:
        # 默认路径
        db_path = os.path.join(os.path.dirname(__file__), '..', 'multi_role_chat.db')

    return db_path

def check_column_exists(cursor, table_name, column_name):
    """检查列是否存在"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [column[1] for column in cursor.fetchall()]
    return column_name in columns

def add_knowledge_base_config_column(cursor):
    """添加知识库配置列"""
    if not check_column_exists(cursor, 'flow_steps', '_knowledge_base_config'):
        print("Adding _knowledge_base_config column to flow_steps table...")
        cursor.execute("""
            ALTER TABLE flow_steps
            ADD COLUMN _knowledge_base_config TEXT
        """)
        print("SUCCESS: _knowledge_base_config column added successfully")
        return True
    else:
        print("INFO: _knowledge_base_config column already exists, skipping")
        return False

def migrate_existing_steps(cursor):
    """Set default knowledge base config for existing steps"""
    print("Checking existing steps for knowledge base config...")

    # Query steps without knowledge base config
    cursor.execute("""
        SELECT id FROM flow_steps
        WHERE _knowledge_base_config IS NULL OR _knowledge_base_config = ''
    """)

    steps_without_config = cursor.fetchall()

    if steps_without_config:
        print(f"Setting default knowledge base config for {len(steps_without_config)} existing steps...")

        default_config = {
            "enabled": False,
            "knowledge_base_ids": [],
            "retrieval_params": {
                "top_k": 5,
                "similarity_threshold": 0.7,
                "max_context_length": 2000
            }
        }

        default_config_json = json.dumps(default_config, ensure_ascii=False)

        cursor.execute("""
            UPDATE flow_steps
            SET _knowledge_base_config = ?
            WHERE _knowledge_base_config IS NULL OR _knowledge_base_config = ''
        """, (default_config_json,))

        print(f"SUCCESS: Default knowledge base config set for {len(steps_without_config)} steps")
    else:
        print("INFO: All steps already have knowledge base config")

def verify_migration(cursor):
    """Verify migration results"""
    print("Verifying migration results...")

    # Check if column exists
    if not check_column_exists(cursor, 'flow_steps', '_knowledge_base_config'):
        print("ERROR: Migration failed - _knowledge_base_config column does not exist")
        return False

    # Check data integrity
    cursor.execute("""
        SELECT COUNT(*) FROM flow_steps
        WHERE _knowledge_base_config IS NULL OR _knowledge_base_config = ''
    """)
    null_count = cursor.fetchone()[0]

    if null_count > 0:
        print(f"ERROR: Migration failed - {null_count} steps still missing knowledge base config")
        return False

    # Check JSON format
    cursor.execute("SELECT _knowledge_base_config FROM flow_steps LIMIT 5")
    configs = cursor.fetchall()

    for config_tuple in configs:
        config_str = config_tuple[0]
        if config_str:
            try:
                config = json.loads(config_str)
                if not isinstance(config, dict):
                    print(f"ERROR: Invalid config format - not a dictionary - {config_str}")
                    return False
            except json.JSONDecodeError as e:
                print(f"ERROR: Invalid JSON format - {config_str}, error: {e}")
                return False

    print("SUCCESS: Migration verification completed")
    return True

def main():
    """主迁移函数"""
    print("=" * 60)
    print("开始知识库配置数据库迁移")
    print("=" * 60)

    db_path = get_db_path()

    if not os.path.exists(db_path):
        print(f"ERROR: 数据库文件不存在：{db_path}")
        sys.exit(1)

    print(f"数据库路径：{db_path}")

    try:
        with sqlite3.connect(db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            cursor = conn.cursor()

            # 1. 添加知识库配置列
            column_added = add_knowledge_base_config_column(cursor)

            # 2. 为现有步骤设置默认配置
            migrate_existing_steps(cursor)

            # 3. 验证迁移
            if verify_migration(cursor):
                conn.commit()
                print("\n" + "=" * 60)
                print("SUCCESS: Knowledge base config database migration completed successfully!")
                print("=" * 60)

                if column_added:
                    print("\nMigration Summary:")
                    print("- Added _knowledge_base_config column to flow_steps table")
                    print("- Set default disabled config for existing steps")
                    print("- Config format: JSON with enabled, knowledge_base_ids, retrieval_params")
                    print("\nIMPORTANT:")
                    print("- Please update FlowStep model to support knowledge base config")
                    print("- Please restart application to apply model changes")
            else:
                conn.rollback()
                print("\n" + "=" * 60)
                print("ERROR: Knowledge base config database migration failed!")
                print("=" * 60)
                sys.exit(1)

    except sqlite3.Error as e:
        print(f"ERROR: 数据库操作失败：{e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: 迁移过程中发生错误：{e}")
        sys.exit(1)

if __name__ == "__main__":
    main()