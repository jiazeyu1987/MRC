#!/usr/bin/env python3
"""
Script to add knowledge base tables to the SQLite database.
This migration creates the knowledge_bases, knowledge_base_conversations,
and role_knowledge_bases tables with proper constraints, indexes, and
foreign key relationships.
"""

import sqlite3
import os
import sys
from datetime import datetime

def check_table_exists(conn, table_name):
    """Check if a table exists in the database"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name=?
    """, (table_name,))
    return cursor.fetchone() is not None

def create_knowledge_bases_table(conn):
    """Create knowledge_bases table"""
    cursor = conn.cursor()

    if check_table_exists(conn, 'knowledge_bases'):
        print("[OK] knowledge_bases table already exists")
        return True

    print("Creating knowledge_bases table...")
    cursor.execute("""
        CREATE TABLE knowledge_bases (
            id INTEGER PRIMARY KEY,
            ragflow_dataset_id VARCHAR(100) NOT NULL UNIQUE,
            name VARCHAR(200) NOT NULL,
            description TEXT,
            document_count INTEGER NOT NULL DEFAULT 0,
            total_size BIGINT NOT NULL DEFAULT 0,
            status VARCHAR(20) NOT NULL DEFAULT 'active',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create indexes
    cursor.execute("CREATE INDEX idx_knowledge_bases_ragflow_dataset_id ON knowledge_bases(ragflow_dataset_id)")
    cursor.execute("CREATE INDEX idx_knowledge_bases_name ON knowledge_bases(name)")
    cursor.execute("CREATE INDEX idx_knowledge_bases_status ON knowledge_bases(status)")
    cursor.execute("CREATE INDEX idx_knowledge_bases_status_name ON knowledge_bases(status, name)")
    cursor.execute("CREATE INDEX idx_knowledge_bases_ragflow_name ON knowledge_bases(ragflow_dataset_id, name)")

    print("[OK] knowledge_bases table created successfully")
    return True

def create_knowledge_base_conversations_table(conn):
    """Create knowledge_base_conversations table"""
    cursor = conn.cursor()

    if check_table_exists(conn, 'knowledge_base_conversations'):
        print("[OK] knowledge_base_conversations table already exists")
        return True

    print("Creating knowledge_base_conversations table...")
    cursor.execute("""
        CREATE TABLE knowledge_base_conversations (
            id INTEGER PRIMARY KEY,
            knowledge_base_id INTEGER NOT NULL,
            title VARCHAR(300) NOT NULL,
            user_question TEXT NOT NULL,
            ragflow_response TEXT,
            confidence_score REAL,
            "references" TEXT,
            metadata TEXT,
            status VARCHAR(20) DEFAULT 'active',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases (id)
        )
    """)

    # Create indexes
    cursor.execute("CREATE INDEX idx_kb_conversations_knowledge_base_id ON knowledge_base_conversations(knowledge_base_id)")
    cursor.execute("CREATE INDEX idx_kb_conversations_status ON knowledge_base_conversations(status)")
    cursor.execute("CREATE INDEX idx_kb_conversations_created_at ON knowledge_base_conversations(created_at)")
    cursor.execute("CREATE INDEX idx_kb_conversations_status_created ON knowledge_base_conversations(status, created_at)")
    cursor.execute("CREATE INDEX idx_kb_conversations_kb_created ON knowledge_base_conversations(knowledge_base_id, created_at)")

    print("[OK] knowledge_base_conversations table created successfully")
    return True

def create_role_knowledge_bases_table(conn):
    """Create role_knowledge_bases table"""
    cursor = conn.cursor()

    if check_table_exists(conn, 'role_knowledge_bases'):
        print("[OK] role_knowledge_bases table already exists")
        return True

    print("Creating role_knowledge_bases table...")
    cursor.execute("""
        CREATE TABLE role_knowledge_bases (
            id INTEGER PRIMARY KEY,
            role_id INTEGER NOT NULL,
            knowledge_base_id INTEGER NOT NULL,
            priority INTEGER NOT NULL DEFAULT 1,
            retrieval_config TEXT,
            is_active BOOLEAN NOT NULL DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (role_id) REFERENCES roles (id),
            FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases (id),
            UNIQUE(role_id, knowledge_base_id)
        )
    """)

    # Create indexes
    cursor.execute("CREATE INDEX idx_role_knowledge_bases_role_id ON role_knowledge_bases(role_id)")
    cursor.execute("CREATE INDEX idx_role_knowledge_bases_knowledge_base_id ON role_knowledge_bases(knowledge_base_id)")
    cursor.execute("CREATE INDEX idx_role_knowledge_bases_priority ON role_knowledge_bases(priority)")
    cursor.execute("CREATE INDEX idx_role_knowledge_base_role_priority ON role_knowledge_bases(role_id, priority)")
    cursor.execute("CREATE INDEX idx_role_knowledge_base_kb_priority ON role_knowledge_bases(knowledge_base_id, priority)")

    print("[OK] role_knowledge_bases table created successfully")
    return True

def create_triggers(conn):
    """Create triggers for updated_at timestamps"""
    cursor = conn.cursor()

    print("Creating triggers for updated_at timestamps...")

    # Knowledge bases trigger
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_knowledge_bases_updated_at
        AFTER UPDATE ON knowledge_bases
        BEGIN
            UPDATE knowledge_bases
            SET updated_at = CURRENT_TIMESTAMP
            WHERE id = NEW.id;
        END
    """)

    # Knowledge base conversations trigger
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_knowledge_base_conversations_updated_at
        AFTER UPDATE ON knowledge_base_conversations
        BEGIN
            UPDATE knowledge_base_conversations
            SET updated_at = CURRENT_TIMESTAMP
            WHERE id = NEW.id;
        END
    """)

    # Role knowledge bases trigger
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_role_knowledge_bases_updated_at
        AFTER UPDATE ON role_knowledge_bases
        BEGIN
            UPDATE role_knowledge_bases
            SET updated_at = CURRENT_TIMESTAMP
            WHERE id = NEW.id;
        END
    """)

    print("[OK] Triggers created successfully")

def verify_tables(conn):
    """Verify that all tables were created successfully"""
    cursor = conn.cursor()

    print("\nVerifying created tables...")

    tables = ['knowledge_bases', 'knowledge_base_conversations', 'role_knowledge_bases']

    for table in tables:
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?", (table,))
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"[OK] {table} table exists")

            # Check indexes for this table
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='index' AND tbl_name=? AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """, (table,))
            indexes = cursor.fetchall()
            if indexes:
                print(f"  - Indexes: {', '.join([idx[0] for idx in indexes])}")
            else:
                print(f"  - No custom indexes found")
        else:
            print(f"[ERROR] {table} table missing!")
            return False

    return True

def main():
    """Main function to add knowledge base tables"""
    db_path = "multi_role_chat.db"

    if not os.path.exists(db_path):
        print(f"[ERROR] Database file {db_path} not found!")
        print("Please ensure the database exists by running the application first.")
        sys.exit(1)

    print(f"Adding knowledge base tables to {db_path}...")

    try:
        # Connect to database
        conn = sqlite3.connect(db_path)

        # Enable foreign key constraints
        conn.execute("PRAGMA foreign_keys = ON")

        # Create tables
        success = True
        success &= create_knowledge_bases_table(conn)
        success &= create_knowledge_base_conversations_table(conn)
        success &= create_role_knowledge_bases_table(conn)

        # Create triggers
        if success:
            create_triggers(conn)

        # Commit changes
        conn.commit()

        # Verify tables
        if success and verify_tables(conn):
            print("\n[SUCCESS] Knowledge base tables migration completed successfully!")
            print("\nCreated tables:")
            print("- knowledge_bases (RAGFlow dataset management)")
            print("- knowledge_base_conversations (test conversation tracking)")
            print("- role_knowledge_bases (role-knowledge base associations)")
            print("\nAll tables include proper:")
            print("- Foreign key constraints")
            print("- Performance indexes")
            print("- Timestamp triggers")
            print("- Data integrity constraints")
        else:
            print("\n[ERROR] Migration verification failed!")
            sys.exit(1)

    except sqlite3.Error as e:
        print(f"\n[ERROR] SQLite error during migration: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error during migration: {e}")
        sys.exit(1)
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()