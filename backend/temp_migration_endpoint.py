#!/usr/bin/env python3
"""
Temporary migration endpoint - run this to add the missing column
"""

import os
import sys

# Add the project path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_migration():
    """Run the migration directly using the app database"""

    try:
        from app import create_app, db

        app = create_app()

        with app.app_context():
            # Get database connection
            engine = db.engine

            # Check if column exists
            inspector = db.inspect(engine)
            columns = inspector.get_columns('flow_steps')
            column_names = [col['name'] for col in columns]

            print(f"Current flow_steps columns: {column_names}")

            if '_knowledge_base_config' in column_names:
                print("✅ Column _knowledge_base_config already exists!")
                return True

            # Add the column
            print("Adding _knowledge_base_config column...")
            with engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE flow_steps ADD COLUMN _knowledge_base_config TEXT"))
                conn.commit()

            # Verify
            inspector = db.inspect(engine)
            columns = inspector.get_columns('flow_steps')
            new_column_names = [col['name'] for col in columns]

            print(f"New flow_steps columns: {new_column_names}")

            if '_knowledge_base_config' in new_column_names:
                print("✅ Migration successful!")
                return True
            else:
                print("❌ Migration failed!")
                return False

    except Exception as e:
        print(f"❌ Migration error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting database migration...")
    success = run_migration()

    if success:
        print("🎉 Migration completed successfully!")
        exit(0)
    else:
        print("💥 Migration failed!")
        exit(1)