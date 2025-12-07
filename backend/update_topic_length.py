#!/usr/bin/env python3
"""
Script to update topic field length from 200 to 2000 characters in SQLite database.
This recreates the tables with the new schema while preserving existing data.
"""

import sqlite3
import os
import sys

def backup_table_data(db_path, table_name):
    """Backup table data to a temporary structure"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    if table_name == 'sessions':
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions_backup AS
            SELECT id, user_id, topic, flow_template_id, flow_snapshot,
                   roles_snapshot, status, current_step_id, current_round,
                   executed_steps_count, error_reason, created_at,
                   updated_at, ended_at
            FROM sessions
        """)
    elif table_name == 'flow_templates':
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS flow_templates_backup AS
            SELECT id, name, topic, type, description, version,
                   is_active, termination_config, created_at, updated_at
            FROM flow_templates
        """)

    conn.commit()
    conn.close()
    print(f"Backed up {table_name} data")

def recreate_table_with_new_schema(db_path, table_name):
    """Recreate table with new schema and restore data"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    if table_name == 'sessions':
        # Drop original table
        cursor.execute("DROP TABLE sessions")

        # Recreate with new schema
        cursor.execute("""
            CREATE TABLE sessions (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                topic VARCHAR(2000) NOT NULL,
                flow_template_id INTEGER NOT NULL,
                flow_snapshot TEXT,
                roles_snapshot TEXT,
                status VARCHAR(20) DEFAULT 'not_started',
                current_step_id INTEGER,
                current_round INTEGER DEFAULT 0,
                executed_steps_count INTEGER DEFAULT 0,
                error_reason VARCHAR(500),
                created_at DATETIME,
                updated_at DATETIME,
                ended_at DATETIME,
                FOREIGN KEY (flow_template_id) REFERENCES flow_templates (id)
            )
        """)

        # Restore data
        cursor.execute("""
            INSERT INTO sessions (
                id, user_id, topic, flow_template_id, flow_snapshot,
                roles_snapshot, status, current_step_id, current_round,
                executed_steps_count, error_reason, created_at,
                updated_at, ended_at
            )
            SELECT
                id, user_id, topic, flow_template_id, flow_snapshot,
                roles_snapshot, status, current_step_id, current_round,
                executed_steps_count, error_reason, created_at,
                updated_at, ended_at
            FROM sessions_backup
        """)

        # Drop backup table
        cursor.execute("DROP TABLE sessions_backup")

    elif table_name == 'flow_templates':
        # Drop original table
        cursor.execute("DROP TABLE flow_templates")

        # Recreate with new schema
        cursor.execute("""
            CREATE TABLE flow_templates (
                id INTEGER PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                topic VARCHAR(2000),
                type VARCHAR(50) NOT NULL,
                description TEXT,
                version VARCHAR(20),
                is_active BOOLEAN,
                termination_config TEXT,
                created_at DATETIME,
                updated_at DATETIME
            )
        """)

        # Restore data
        cursor.execute("""
            INSERT INTO flow_templates (
                id, name, topic, type, description, version,
                is_active, termination_config, created_at, updated_at
            )
            SELECT
                id, name, topic, type, description, version,
                is_active, termination_config, created_at, updated_at
            FROM flow_templates_backup
        """)

        # Drop backup table
        cursor.execute("DROP TABLE flow_templates_backup")

    conn.commit()
    conn.close()
    print(f"Recreated {table_name} with new schema")

def main():
    """Main function to update topic field lengths"""
    db_path = "conversations.db"

    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        sys.exit(1)

    print(f"Updating topic field lengths in {db_path}...")

    try:
        # Update sessions table
        backup_table_data(db_path, 'sessions')
        recreate_table_with_new_schema(db_path, 'sessions')

        # Update flow_templates table
        backup_table_data(db_path, 'flow_templates')
        recreate_table_with_new_schema(db_path, 'flow_templates')

        print("✅ Successfully updated topic field lengths from 200 to 2000 characters!")
        print("The following tables were updated:")
        print("- sessions.topic")
        print("- flow_templates.topic")

    except Exception as e:
        print(f"❌ Error updating database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()