#!/usr/bin/env python3
"""
Quick database check script
"""

import sqlite3
import os

def check_database():
    # Check if the database file exists
    db_path = 'instance/multi_role_chat.db'
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return False

    print(f"✅ Database file found: {db_path}")
    print(f"📁 File size: {os.path.getsize(db_path)} bytes")

    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        print(f"\n📊 Found {len(tables)} tables:")
        for table in tables:
            table_name = table[0]
            print(f"  - {table_name}")

            # Get row count for each table
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"    Rows: {count}")

        # Specifically check for roles table
        role_tables = [t[0] for t in tables if 'role' in t[0].lower()]
        if role_tables:
            print(f"\n✅ Role-related tables found: {role_tables}")

            # Show sample roles data
            if 'roles' in role_tables:
                cursor.execute("SELECT id, name FROM roles LIMIT 5")
                roles = cursor.fetchall()
                print("📋 Sample roles:")
                for role in roles:
                    print(f"  ID: {role[0]}, Name: {role[1]}")
        else:
            print("\n❌ No role-related tables found!")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ Error checking database: {str(e)}")
        return False

if __name__ == '__main__':
    check_database()