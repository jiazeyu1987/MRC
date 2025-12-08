#!/usr/bin/env python3
"""
Add document management tables to existing database.

This script follows the existing migration pattern from add_knowledge_base_tables.py
and creates the necessary tables for document management functionality.
"""

import os
import sys

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.knowledge_base import KnowledgeBase

def add_document_management_tables():
    """Add document management tables to existing database"""
    app = create_app()

    with app.app_context():
        print("Starting document management tables creation...")

        try:
            # Create documents table
            print("Creating documents table...")
            db.engine.execute('''
                CREATE TABLE IF NOT EXISTS documents (
                    id VARCHAR(36) PRIMARY KEY,
                    knowledge_base_id VARCHAR(36) NOT NULL,
                    ragflow_document_id VARCHAR(255),
                    filename VARCHAR(255) NOT NULL,
                    original_filename VARCHAR(255) NOT NULL,
                    file_size INTEGER NOT NULL,
                    file_type VARCHAR(50) NOT NULL,
                    mime_type VARCHAR(100) NOT NULL,
                    upload_status VARCHAR(20) DEFAULT 'uploading',
                    processing_status VARCHAR(20) DEFAULT 'pending',
                    chunk_count INTEGER DEFAULT 0,
                    error_message TEXT,
                    ragflow_metadata JSON,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    uploaded_at DATETIME,
                    processed_at DATETIME,
                    FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases(id) ON DELETE CASCADE
                )
            ''')
            print("✓ Documents table created successfully")

            # Create document_chunks table
            print("Creating document_chunks table...")
            db.engine.execute('''
                CREATE TABLE IF NOT EXISTS document_chunks (
                    id VARCHAR(36) PRIMARY KEY,
                    document_id VARCHAR(36) NOT NULL,
                    ragflow_chunk_id VARCHAR(255),
                    chunk_index INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    content_preview VARCHAR(500),
                    word_count INTEGER DEFAULT 0,
                    character_count INTEGER DEFAULT 0,
                    ragflow_metadata JSON,
                    embedding_vector_id VARCHAR(255),
                    position_start INTEGER,
                    position_end INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
                )
            ''')
            print("✓ Document chunks table created successfully")

            # Create processing_logs table
            print("Creating processing_logs table...")
            db.engine.execute('''
                CREATE TABLE IF NOT EXISTS processing_logs (
                    id VARCHAR(36) PRIMARY KEY,
                    document_id VARCHAR(36) NOT NULL,
                    step VARCHAR(50) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    progress INTEGER DEFAULT 0,
                    message TEXT,
                    error_details JSON,
                    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    completed_at DATETIME,
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
                )
            ''')
            print("✓ Processing logs table created successfully")

            # Create chunk_references table
            print("Creating chunk_references table...")
            db.engine.execute('''
                CREATE TABLE IF NOT EXISTS chunk_references (
                    id VARCHAR(36) PRIMARY KEY,
                    chunk_id VARCHAR(36) NOT NULL,
                    conversation_id VARCHAR(36),
                    message_id VARCHAR(36),
                    relevance_score REAL,
                    reference_count INTEGER DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (chunk_id) REFERENCES document_chunks(id) ON DELETE CASCADE
                )
            ''')
            print("✓ Chunk references table created successfully")

            # Add indexes for performance optimization
            print("Creating indexes...")

            # Documents table indexes
            db.engine.execute('CREATE INDEX IF NOT EXISTS idx_documents_kb_id ON documents(knowledge_base_id)')
            db.engine.execute('CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(processing_status)')
            db.engine.execute('CREATE INDEX IF NOT EXISTS idx_documents_upload_status ON documents(upload_status)')
            db.engine.execute('CREATE INDEX IF NOT EXISTS idx_documents_ragflow_id ON documents(ragflow_document_id)')
            db.engine.execute('CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at)')

            # Document chunks table indexes
            db.engine.execute('CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON document_chunks(document_id)')
            db.engine.execute('CREATE INDEX IF NOT EXISTS idx_chunks_index ON document_chunks(chunk_index)')
            db.engine.execute('CREATE INDEX IF NOT EXISTS idx_chunks_ragflow_id ON document_chunks(ragflow_chunk_id)')

            # Processing logs table indexes
            db.engine.execute('CREATE INDEX IF NOT EXISTS idx_logs_doc_id ON processing_logs(document_id)')
            db.engine.execute('CREATE INDEX IF NOT EXISTS idx_logs_step ON processing_logs(step)')
            db.engine.execute('CREATE INDEX IF NOT EXISTS idx_logs_status ON processing_logs(status)')
            db.engine.execute('CREATE INDEX IF NOT EXISTS idx_logs_started_at ON processing_logs(started_at)')

            # Chunk references table indexes
            db.engine.execute('CREATE INDEX IF NOT EXISTS idx_refs_chunk_id ON chunk_references(chunk_id)')
            db.engine.execute('CREATE INDEX IF NOT EXISTS idx_refs_conversation_id ON chunk_references(conversation_id)')
            db.engine.execute('CREATE INDEX IF NOT EXISTS idx_refs_message_id ON chunk_references(message_id)')

            print("✓ All indexes created successfully")

            # Verify table creation
            print("\nVerifying table creation...")

            # Check if tables exist
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()

            required_tables = ['documents', 'document_chunks', 'processing_logs']
            for table in required_tables:
                if table in tables:
                    print(f"✓ Table '{table}' exists")
                else:
                    print(f"✗ Table '{table}' missing")
                    return False

            print("\n✅ Document management tables created successfully!")
            print("\nCreated tables:")
            print("- documents: Stores document metadata and status")
            print("- document_chunks: Stores processed document chunks")
            print("- processing_logs: Tracks document processing progress")
            print("- chunk_references: Tracks chunk usage in conversations")

            # Display table counts
            try:
                doc_count = db.engine.execute('SELECT COUNT(*) FROM documents').scalar()
                chunk_count = db.engine.execute('SELECT COUNT(*) FROM document_chunks').scalar()
                log_count = db.engine.execute('SELECT COUNT(*) FROM processing_logs').scalar()

                print(f"\nCurrent record counts:")
                print(f"- Documents: {doc_count}")
                print(f"- Document chunks: {chunk_count}")
                print(f"- Processing logs: {log_count}")

            except Exception as e:
                print(f"Warning: Could not retrieve record counts: {e}")

            return True

        except Exception as e:
            print(f"❌ Error creating document management tables: {e}")
            return False

def verify_migration():
    """Verify that the migration was successful"""
    app = create_app()

    with app.app_context():
        try:
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()

            required_tables = ['documents', 'document_chunks', 'processing_logs']

            print("\n📋 Migration Verification:")
            all_exist = True
            for table in required_tables:
                if table in tables:
                    columns = inspector.get_columns(table)
                    print(f"✓ {table} ({len(columns)} columns)")
                else:
                    print(f"✗ {table} (missing)")
                    all_exist = False

            return all_exist

        except Exception as e:
            print(f"❌ Verification error: {e}")
            return False

if __name__ == "__main__":
    print("🔧 Knowledge Base Document Management - Database Migration")
    print("=" * 60)

    success = add_document_management_tables()

    if success:
        print("\n🔍 Running verification...")
        verify_migration()
        print("\n🎉 Migration completed successfully!")
        print("\nNext steps:")
        print("1. Restart the backend application")
        print("2. Test the document management functionality")
        print("3. Verify RAGFlow integration is working")
    else:
        print("\n❌ Migration failed. Please check the error messages above.")
        sys.exit(1)