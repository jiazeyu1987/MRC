#!/usr/bin/env python3
"""
Script to add enhanced features to the knowledge base system.
This migration adds new tables and fields for conversation history,
search analytics, API documentation cache, and extends the knowledge_base table.
"""

import sqlite3
import os
import sys
from datetime import datetime

def get_db_path():
    """Get the database path"""
    # Check if we're in backend directory
    if os.path.exists('instance/multi_role_chat.db'):
        return 'instance/multi_role_chat.db'
    elif os.path.exists('../backend/instance/multi_role_chat.db'):
        return '../backend/instance/multi_role_chat.db'
    else:
        # Default path
        return 'instance/multi_role_chat.db'

def check_table_exists(conn, table_name):
    """Check if a table exists in the database"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name=?
    """, (table_name,))
    return cursor.fetchone() is not None

def check_column_exists(conn, table_name, column_name):
    """Check if a column exists in a table"""
    cursor = conn.cursor()
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]
        return column_name in columns
    except sqlite3.OperationalError:
        return False

def log_step(step_name):
    """Log migration step"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {step_name}")

def create_backup(conn):
    """Create a backup before migration"""
    log_step("Creating database backup...")
    try:
        backup_path = f"instance/multi_role_chat_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        backup_conn = sqlite3.connect(backup_path)
        conn.backup(backup_conn)
        backup_conn.close()
        print(f"[OK] Backup created at {backup_path}")
        return True
    except Exception as e:
        print(f"[ERROR] Backup creation failed: {e}")
        return False

def add_knowledge_base_extensions(conn):
    """Add new columns to knowledge_base table"""
    log_step("Adding columns to knowledge_base table...")
    cursor = conn.cursor()

    try:
        # Check and add new columns
        columns_to_add = [
            ("last_activity", "DATETIME"),  # Add without default, then update existing rows
            ("settings", "TEXT")  # Use TEXT instead of JSON for SQLite compatibility
        ]

        for column_name, column_def in columns_to_add:
            if not check_column_exists(conn, 'knowledge_bases', column_name):
                sql = f"ALTER TABLE knowledge_bases ADD COLUMN {column_name} {column_def}"
                cursor.execute(sql)
                print(f"[OK] Added column {column_name} to knowledge_bases")

                # Set default values for existing rows
                if column_name == "last_activity":
                    cursor.execute("UPDATE knowledge_bases SET last_activity = created_at WHERE last_activity IS NULL")
                elif column_name == "settings":
                    cursor.execute("UPDATE knowledge_bases SET settings = '{}' WHERE settings IS NULL")

            else:
                print(f"[SKIP] Column {column_name} already exists in knowledge_bases")

        conn.commit()
        return True

    except Exception as e:
        print(f"[ERROR] Failed to add columns to knowledge_bases: {e}")
        conn.rollback()
        return False

def create_conversation_history_table(conn):
    """Create conversation_history table"""
    log_step("Creating conversation_history table...")
    cursor = conn.cursor()

    if check_table_exists(conn, 'conversation_history'):
        print("[OK] conversation_history table already exists")
        return True

    try:
        cursor.execute("""
            CREATE TABLE conversation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                knowledge_base_id INTEGER NOT NULL,
                user_id VARCHAR(100),
                title VARCHAR(200) NOT NULL,
                messages TEXT NOT NULL,
                tags TEXT DEFAULT '[]',
                template_id VARCHAR(100),
                conversation_metadata TEXT DEFAULT '{}',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_archived BOOLEAN DEFAULT 0,
                FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases (id)
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX idx_conversation_kb_created ON conversation_history(knowledge_base_id, created_at DESC)")
        cursor.execute("CREATE INDEX idx_conversation_user_created ON conversation_history(user_id, created_at DESC)")
        cursor.execute("CREATE INDEX idx_conversation_archived ON conversation_history(is_archived, created_at DESC)")

        conn.commit()
        print("[OK] conversation_history table created successfully")
        return True

    except Exception as e:
        print(f"[ERROR] Failed to create conversation_history table: {e}")
        conn.rollback()
        return False

def create_conversation_templates_table(conn):
    """Create conversation_templates table"""
    log_step("Creating conversation_templates table...")
    cursor = conn.cursor()

    if check_table_exists(conn, 'conversation_templates'):
        print("[OK] conversation_templates table already exists")
        return True

    try:
        cursor.execute("""
            CREATE TABLE conversation_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL UNIQUE,
                description TEXT,
                category VARCHAR(50) NOT NULL,
                prompt TEXT NOT NULL,
                parameters TEXT DEFAULT '[]',
                is_system BOOLEAN DEFAULT 0,
                usage_count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX idx_template_category ON conversation_templates(category)")
        cursor.execute("CREATE INDEX idx_template_system ON conversation_templates(is_system, name)")
        cursor.execute("CREATE INDEX idx_template_usage ON conversation_templates(usage_count DESC)")

        conn.commit()
        print("[OK] conversation_templates table created successfully")
        return True

    except Exception as e:
        print(f"[ERROR] Failed to create conversation_templates table: {e}")
        conn.rollback()
        return False

def create_search_analytics_table(conn):
    """Create search_analytics table"""
    log_step("Creating search_analytics table...")
    cursor = conn.cursor()

    if check_table_exists(conn, 'search_analytics'):
        print("[OK] search_analytics table already exists")
        return True

    try:
        cursor.execute("""
            CREATE TABLE search_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                knowledge_base_id INTEGER NOT NULL,
                user_id VARCHAR(100),
                search_query VARCHAR(500) NOT NULL,
                filters TEXT DEFAULT '{}',
                results_count INTEGER DEFAULT 0,
                response_time_ms INTEGER DEFAULT 0,
                clicked_documents TEXT DEFAULT '[]',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases (id)
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX idx_search_kb_date ON search_analytics(knowledge_base_id, created_at DESC)")
        cursor.execute("CREATE INDEX idx_search_user_date ON search_analytics(user_id, created_at DESC)")
        cursor.execute("CREATE INDEX idx_search_query ON search_analytics(search_query)")
        cursor.execute("CREATE INDEX idx_search_performance ON search_analytics(response_time_ms)")
        cursor.execute("CREATE INDEX idx_search_results ON search_analytics(results_count)")

        conn.commit()
        print("[OK] search_analytics table created successfully")
        return True

    except Exception as e:
        print(f"[ERROR] Failed to create search_analytics table: {e}")
        conn.rollback()
        return False

def create_api_documentation_cache_table(conn):
    """Create api_documentation_cache table"""
    log_step("Creating api_documentation_cache table...")
    cursor = conn.cursor()

    if check_table_exists(conn, 'api_documentation_cache'):
        print("[OK] api_documentation_cache table already exists")
        return True

    try:
        cursor.execute("""
            CREATE TABLE api_documentation_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint_path VARCHAR(200) NOT NULL UNIQUE,
                method VARCHAR(10) NOT NULL,
                category VARCHAR(50) NOT NULL,
                documentation TEXT NOT NULL,
                examples TEXT DEFAULT '[]',
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX idx_api_endpoint_method ON api_documentation_cache(endpoint_path, method)")
        cursor.execute("CREATE INDEX idx_api_category ON api_documentation_cache(category)")
        cursor.execute("CREATE INDEX idx_api_expires ON api_documentation_cache(expires_at)")
        cursor.execute("CREATE INDEX idx_api_active ON api_documentation_cache(is_active)")

        conn.commit()
        print("[OK] api_documentation_cache table created successfully")
        return True

    except Exception as e:
        print(f"[ERROR] Failed to create api_documentation_cache table: {e}")
        conn.rollback()
        return False

def insert_system_templates(conn):
    """Insert system conversation templates"""
    log_step("Inserting system conversation templates...")
    cursor = conn.cursor()

    templates = [
        {
            'name': '技术文档分析',
            'description': '用于分析技术文档和说明的模板',
            'category': 'technical',
            'prompt': '请详细分析以下技术文档内容，包括：\n1. 主要技术要点\n2. 实现方法和原理\n3. 潜在问题和解决方案\n4. 相关技术栈和依赖',
            'parameters': ['文档主题', '分析深度'],
            'is_system': 1
        },
        {
            'name': '知识问答',
            'description': '用于快速回答知识相关问题的模板',
            'category': 'qa',
            'prompt': '基于提供的知识库内容，请准确回答以下问题。如果信息不足，请明确说明需要哪些额外信息。',
            'parameters': ['问题主题', '详细程度'],
            'is_system': 1
        },
        {
            'name': '综合分析',
            'description': '用于综合性问题分析和解决方案制定的模板',
            'category': 'analysis',
            'prompt': '请对以下问题进行综合分析：\n1. 问题背景和现状\n2. 涉及的关键因素\n3. 可能的解决方案\n4. 推荐方案和实施步骤\n5. 风险评估和应对措施',
            'parameters': ['问题类型', '分析维度'],
            'is_system': 1
        }
    ]

    try:
        for template in templates:
            # Check if template already exists
            cursor.execute("SELECT id FROM conversation_templates WHERE name = ?", (template['name'],))
            if cursor.fetchone():
                print(f"[SKIP] Template '{template['name']}' already exists")
                continue

            cursor.execute("""
                INSERT INTO conversation_templates (
                    name, description, category, prompt, parameters, is_system
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                template['name'],
                template['description'],
                template['category'],
                template['prompt'],
                str(template['parameters']),
                template['is_system']
            ))

        conn.commit()
        print(f"[OK] Inserted {len(templates)} system templates")
        return True

    except Exception as e:
        print(f"[ERROR] Failed to insert system templates: {e}")
        conn.rollback()
        return False

def validate_migration(conn):
    """Validate the migration was successful"""
    log_step("Validating migration...")
    required_tables = [
        'conversation_history',
        'conversation_templates',
        'search_analytics',
        'api_documentation_cache'
    ]

    required_columns = [
        ('knowledge_bases', 'conversation_count'),
        ('knowledge_bases', 'search_count'),
        ('knowledge_bases', 'last_activity'),
        ('knowledge_bases', 'settings')
    ]

    success = True

    # Check tables
    for table in required_tables:
        if not check_table_exists(conn, table):
            print(f"[ERROR] Table {table} was not created")
            success = False
        else:
            print(f"[OK] Table {table} exists")

    # Check columns
    for table, column in required_columns:
        if not check_column_exists(conn, table, column):
            print(f"[ERROR] Column {column} was not added to {table}")
            success = False
        else:
            print(f"[OK] Column {column} exists in {table}")

    return success

def main():
    """Main migration function"""
    print("=" * 60)
    print("MRC Knowledge Base Enhanced Features Migration")
    print("=" * 60)

    # Get database path
    db_path = get_db_path()
    print(f"Database path: {db_path}")

    if not os.path.exists(db_path):
        print(f"[ERROR] Database file not found: {db_path}")
        print("Please ensure you're running this from the backend directory.")
        sys.exit(1)

    # Connect to database
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
        print(f"[OK] Connected to database")
    except Exception as e:
        print(f"[ERROR] Failed to connect to database: {e}")
        sys.exit(1)

    try:
        # Create backup
        if not create_backup(conn):
            print("[ERROR] Backup failed, aborting migration")
            sys.exit(1)

        # Run migration steps
        migration_steps = [
            ("Knowledge Base Extensions", add_knowledge_base_extensions),
            ("Conversation History Table", create_conversation_history_table),
            ("Conversation Templates Table", create_conversation_templates_table),
            ("Search Analytics Table", create_search_analytics_table),
            ("API Documentation Cache Table", create_api_documentation_cache_table),
            ("System Templates", insert_system_templates),
            ("Validation", validate_migration)
        ]

        for step_name, step_func in migration_steps:
            if not step_func(conn):
                print(f"[ERROR] Migration failed at step: {step_name}")
                conn.close()
                sys.exit(1)

        print("\n" + "=" * 60)
        print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\nNew features added:")
        print("- Persistent conversation history")
        print("- Conversation templates")
        print("- Search analytics and insights")
        print("- API documentation cache")
        print("- Enhanced knowledge base statistics")
        print("\nYou can now restart your application to use the new features.")

    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    main()