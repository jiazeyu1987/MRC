import sqlite3
import os

def add_column():
    db_path = os.path.join(os.path.dirname(__file__), 'conversations.db')

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if column already exists
        cursor.execute("PRAGMA table_info(flow_steps)")
        columns = [row[1] for row in cursor.fetchall()]

        if '_knowledge_base_config' in columns:
            print("Column already exists")
            return True

        print(f"Current columns: {columns}")
        print("Adding _knowledge_base_config column...")

        cursor.execute("ALTER TABLE flow_steps ADD COLUMN _knowledge_base_config TEXT")
        conn.commit()

        print("Column added successfully!")

        # Verify
        cursor.execute("PRAGMA table_info(flow_steps)")
        new_columns = [row[1] for row in cursor.fetchall()]
        print(f"New columns: {new_columns}")

        return '_knowledge_base_config' in new_columns

    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    success = add_column()
    if success:
        print("Migration completed successfully!")
    else:
        print("Migration failed!")