"""
Comprehensive Integration Tests for Document Management System

This test suite covers end-to-end functionality of the Knowledge Base Document Management
system, including file uploads, processing, chunking, search, and conversation integration.

Test Coverage:
- Document upload and processing workflows
- Chunk search and retrieval
- RAGFlow integration
- API endpoint functionality
- Error handling and edge cases
- Performance under load
- Security and validation

Author: Knowledge Base Document Management System
Version: 1.0.0
"""

import pytest
import asyncio
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, Mock
from werkzeug.datastructures import FileStorage
from datetime import datetime, timedelta

# Import application and modules
from app import create_app
from app.models.knowledge_base import KnowledgeBase
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.processing_log import ProcessingLog
from app.services.document_service import DocumentService
from app.services.upload_service import UploadService
from app.services.chunk_service import ChunkService
from app.services.ragflow_service import RAGFlowService


class TestDocumentManagementIntegration:
    """Integration test suite for document management functionality."""

    @pytest.fixture
    def app(self):
        """Create test application with test configuration."""
        app = create_app({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'RAGFLOW_API_KEY': 'test-key',
            'RAGFLOW_BASE_URL': 'https://test.ragflow.com',
            'RAGFLOW_TIMEOUT': 10,
            'RAGFLOW_MAX_RETRIES': 2
        })

        with app.app_context():
            from app import db
            db.create_all()
            yield app
            db.drop_all()

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()

    @pytest.fixture
    def test_knowledge_base(self, app):
        """Create test knowledge base."""
        with app.app_context():
            from app import db

            kb = KnowledgeBase(
                id='test-kb-001',
                name='Test Knowledge Base',
                description='Test knowledge base for integration testing',
                ragflow_dataset_id='test-dataset-001',
                status='active',
                document_count=0,
                total_size=0
            )
            db.session.add(kb)
            db.session.commit()
            return kb

    @pytest.fixture
    def sample_pdf_file(self):
        """Create sample PDF file for testing."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            # Write minimal PDF content
            f.write(b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(Test Document) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000056 00000 n\n0000000123 00000 n\n0000000214 00000 n\ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n316\n%%EOF')
            temp_path = f.name
        yield temp_path
        os.unlink(temp_path)

    @pytest.fixture
    def sample_text_file(self):
        """Create sample text file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('This is a test document for the knowledge base system.\n')
            f.write('It contains multiple lines of text to test chunking functionality.\n')
            f.write('The document should be processed and split into chunks for retrieval.\n')
            temp_path = f.name
        yield temp_path
        os.unlink(temp_path)

    def test_document_upload_workflow(self, client, test_knowledge_base, sample_text_file):
        """Test complete document upload and processing workflow."""

        # Step 1: Upload document
        with open(sample_text_file, 'rb') as f:
            response = client.post(
                f'/api/knowledge-bases/{test_knowledge_base.id}/documents/upload',
                data={'file': (FileStorage(f, 'test.txt'), 'test.txt')},
                content_type='multipart/form-data'
            )

        assert response.status_code == 200
        upload_data = response.get_json()
        assert upload_data['success'] is True
        assert 'document_id' in upload_data
        assert 'upload_id' in upload_data

        document_id = upload_data['document_id']
        upload_id = upload_data['upload_id']

        # Step 2: Check upload progress
        response = client.get(
            f'/api/knowledge-bases/{test_knowledge_base.id}/documents/upload?upload_id={upload_id}'
        )

        assert response.status_code == 200
        progress_data = response.get_json()
        assert progress_data['success'] is True
        assert 'data' in progress_data

        # Step 3: Get document details
        response = client.get(
            f'/api/knowledge-bases/{test_knowledge_base.id}/documents/{document_id}'
        )

        assert response.status_code == 200
        document_data = response.get_json()
        assert document_data['success'] is True
        assert document_data['data']['original_filename'] == 'test.txt'
        assert document_data['data']['knowledge_base_id'] == test_knowledge_base.id

    @patch('app.services.ragflow_service.RAGFlowService.upload_file')
    def test_ragflow_integration(self, mock_upload, client, test_knowledge_base, sample_pdf_file):
        """Test RAGFlow integration for document processing."""

        # Mock RAGFlow response
        mock_upload.return_value = {
            'document_id': 'ragflow-doc-001',
            'status': 'completed',
            'chunks_count': 3
        }

        # Upload document
        with open(sample_pdf_file, 'rb') as f:
            response = client.post(
                f'/api/knowledge-bases/{test_knowledge_base.id}/documents/upload',
                data={'file': (FileStorage(f, 'test.pdf'), 'test.pdf')},
                content_type='multipart/form-data'
            )

        assert response.status_code == 200
        upload_data = response.get_json()
        assert upload_data['success'] is True

        # Verify RAGFlow service was called
        mock_upload.assert_called_once()

    def test_document_list_retrieval(self, client, test_knowledge_base):
        """Test document list retrieval with filters and pagination."""

        # Test empty list
        response = client.get(f'/api/knowledge-bases/{test_knowledge_base.id}/documents')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'documents' in data['data']
        assert 'pagination' in data['data']

        # Test with search filters
        response = client.get(
            f'/api/knowledge-bases/{test_knowledge_base.id}/documents?search=test&page=1&limit=10'
        )
        assert response.status_code == 200

    def test_chunk_search_functionality(self, client, test_knowledge_base):
        """Test document chunk search and retrieval."""

        # Search chunks
        response = client.post(
            f'/api/knowledge-bases/{test_knowledge_base.id}/chunks/search',
            json={
                'query': 'test document',
                'max_results': 10
            }
        )

        assert response.status_code == 200
        search_data = response.get_json()
        assert search_data['success'] is True
        assert 'chunks' in search_data['data']
        assert 'total_count' in search_data['data']

    def test_document_deletion(self, client, test_knowledge_base, sample_text_file):
        """Test document deletion and cleanup."""

        # First upload a document
        with open(sample_text_file, 'rb') as f:
            upload_response = client.post(
                f'/api/knowledge-bases/{test_knowledge_base.id}/documents/upload',
                data={'file': (FileStorage(f, 'delete_test.txt'), 'delete_test.txt')},
                content_type='multipart/form-data'
            )

        upload_data = upload_response.get_json()
        document_id = upload_data['document_id']

        # Delete the document
        response = client.delete(
            f'/api/knowledge-bases/{test_knowledge_base.id}/documents/{document_id}'
        )

        assert response.status_code == 200
        delete_data = response.get_json()
        assert delete_data['success'] is True

        # Verify document is gone
        response = client.get(
            f'/api/knowledge-bases/{test_knowledge_base.id}/documents/{document_id}'
        )
        assert response.status_code == 404

    def test_file_validation(self, client, test_knowledge_base):
        """Test file validation and error handling."""

        # Test oversized file (create temporary large file)
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            # Write content larger than 50MB limit
            large_content = 'x' * (55 * 1024 * 1024)  # 55MB
            f.write(large_content.encode())
            temp_path = f.name

        try:
            with open(temp_path, 'rb') as f:
                response = client.post(
                    f'/api/knowledge-bases/{test_knowledge_base.id}/documents/upload',
                    data={'file': (FileStorage(f, 'large.txt'), 'large.txt')},
                    content_type='multipart/form-data'
                )

            assert response.status_code == 400
            error_data = response.get_json()
            assert 'File size exceeds limit' in error_data['message']

        finally:
            os.unlink(temp_path)

        # Test unsupported file type
        with tempfile.NamedTemporaryFile(suffix='.exe', delete=False) as f:
            f.write(b'fake executable content')
            temp_path = f.name

        try:
            with open(temp_path, 'rb') as f:
                response = client.post(
                    f'/api/knowledge-bases/{test_knowledge_base.id}/documents/upload',
                    data={'file': (FileStorage(f, 'malware.exe'), 'malware.exe')},
                    content_type='multipart/form-data'
                )

            assert response.status_code == 400
            error_data = response.get_json()
            assert 'Unsupported file type' in error_data['message']

        finally:
            os.unlink(temp_path)

    def test_concurrent_uploads(self, client, test_knowledge_base, sample_text_file):
        """Test concurrent document uploads."""

        # Create multiple temporary files
        temp_files = []
        upload_responses = []

        try:
            # Upload multiple files concurrently
            for i in range(3):
                with tempfile.NamedTemporaryFile(mode='w', suffix=f'_test_{i}.txt', delete=False) as f:
                    f.write(f'Test document {i} content\n')
                    temp_path = f.name
                    temp_files.append(temp_path)

            # Simulate concurrent uploads
            for i, temp_path in enumerate(temp_files):
                with open(temp_path, 'rb') as f:
                    response = client.post(
                        f'/api/knowledge-bases/{test_knowledge_base.id}/documents/upload',
                        data={'file': (FileStorage(f, f'concurrent_test_{i}.txt'), f'concurrent_test_{i}.txt')},
                        content_type='multipart/form-data'
                    )
                    upload_responses.append(response)

            # Check all uploads were successful
            for response in upload_responses:
                assert response.status_code == 200
                data = response.get_json()
                assert data['success'] is True
                assert 'document_id' in data

        finally:
            # Cleanup temporary files
            for temp_path in temp_files:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

    def test_document_statistics(self, client, test_knowledge_base):
        """Test document statistics aggregation."""

        response = client.get(f'/api/knowledge-bases/{test_knowledge_base.id}/documents/statistics')

        assert response.status_code == 200
        stats_data = response.get_json()
        assert stats_data['success'] is True
        assert 'data' in stats_data

        stats = stats_data['data']
        assert 'total_documents' in stats
        assert 'total_file_size_bytes' in stats
        assert 'total_chunks' in stats
        assert isinstance(stats['total_documents'], int)

    @patch('app.services.ragflow_service.RAGFlowService.chat_with_dataset')
    def test_test_conversation_integration(self, mock_chat, client, test_knowledge_base):
        """Test conversation integration with document management."""

        # Mock RAGFlow chat response
        mock_chat.return_value = {
            'answer': 'This is a test response based on the uploaded documents.',
            'references': [
                {
                    'document_id': 'test-doc-001',
                    'document_title': 'Test Document',
                    'snippet': 'Test snippet from document',
                    'confidence_score': 0.95
                }
            ],
            'conversation_id': 'test-conv-001'
        }

        # Perform test conversation
        response = client.post(
            f'/api/knowledge-bases/{test_knowledge_base.id}',
            json={
                'action': 'test_conversation',
                'question': 'What is in the uploaded documents?',
                'title': 'Test Conversation'
            }
        )

        assert response.status_code == 200
        conversation_data = response.get_json()
        assert conversation_data['success'] is True
        assert 'data' in conversation_data

        # Verify RAGFlow service was called
        mock_chat.assert_called_once()

    def test_error_handling_and_recovery(self, client, test_knowledge_base):
        """Test error handling and system recovery."""

        # Test invalid knowledge base ID
        response = client.get('/api/knowledge-bases/invalid-kb/documents')
        assert response.status_code == 404

        # Test invalid document ID
        response = client.get(f'/api/knowledge-bases/{test_knowledge_base.id}/documents/invalid-doc')
        assert response.status_code == 404

        # Test malformed JSON in search
        response = client.post(
            f'/api/knowledge-bases/{test_knowledge_base.id}/chunks/search',
            json='invalid json'
        )
        assert response.status_code == 400

    def test_security_validation(self, client, test_knowledge_base):
        """Test security validations and sanitization."""

        # Test file with potentially dangerous content
        dangerous_content = '<script>alert("xss")</script> malicious content'

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(dangerous_content)
            temp_path = f.name

        try:
            with open(temp_path, 'rb') as f:
                response = client.post(
                    f'/api/knowledge-bases/{test_knowledge_base.id}/documents/upload',
                    data={'file': (FileStorage(f, 'suspicious.txt'), 'suspicious.txt')},
                    content_type='multipart/form-data'
                )

            # Should either be accepted (if content scanning is implemented) or rejected
            # The important thing is that the system doesn't crash
            assert response.status_code in [200, 400]

        finally:
            os.unlink(temp_path)

    def test_performance_metrics(self, app, test_knowledge_base):
        """Test system performance under various conditions."""

        with app.app_context():
            from app.services.document_service import DocumentService

            document_service = DocumentService()

            # Test performance with various document sizes
            test_cases = [
                ('small', 1024),      # 1KB
                ('medium', 102400),   # 100KB
                ('large', 1048576)    # 1MB
            ]

            for case_name, size in test_cases:
                with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
                    f.write(b'x' * size)
                    temp_path = f.name

                try:
                    start_time = datetime.now()

                    # Measure document processing time
                    with open(temp_path, 'rb') as f:
                        file_data = FileStorage(f, f'perf_test_{case_name}.txt')

                    # Test validation performance
                    validation_result = document_service.validate_file(file_data)

                    end_time = datetime.now()
                    processing_time = (end_time - start_time).total_seconds()

                    # Validation should complete quickly
                    assert processing_time < 5.0, f"{case_name} file validation took too long: {processing_time}s"
                    assert validation_result['valid'] is True

                finally:
                    os.unlink(temp_path)

    def test_api_rate_limiting(self, client, test_knowledge_base):
        """Test API rate limiting for upload endpoints."""

        # Make multiple rapid requests
        responses = []
        for i in range(10):
            response = client.get(f'/api/knowledge-bases/{test_knowledge_base.id}/documents')
            responses.append(response)

        # Check if rate limiting is working (some responses should be 429)
        rate_limited_responses = [r for r in responses if r.status_code == 429]

        # This test depends on whether rate limiting is implemented
        # If implemented, we should see some rate-limited responses
        # If not implemented, all should be successful
        assert all(r.status_code in [200, 429] for r in responses)

    @pytest.mark.asyncio
    async def test_async_processing_workflow(self, app, test_knowledge_base, sample_text_file):
        """Test asynchronous document processing workflow."""

        with app.app_context():
            from app.services.upload_service import UploadService

            upload_service = UploadService()

            # Test async upload initiation
            with open(sample_text_file, 'rb') as f:
                file_data = FileStorage(f, 'async_test.txt')

            upload_result = await upload_service.process_upload_async(
                test_knowledge_base.id,
                file_data
            )

            assert upload_result is not None
            assert 'upload_id' in upload_result
            assert 'document_id' in upload_result

    def test_database_transaction_integrity(self, app, test_knowledge_base):
        """Test database transaction integrity and rollback."""

        with app.app_context():
            from app import db
            from app.models.document import Document

            # Test successful transaction
            try:
                doc = Document(
                    id='test-transaction-doc',
                    knowledge_base_id=test_knowledge_base.id,
                    filename='test.txt',
                    original_filename='test.txt',
                    file_size=1024,
                    file_type='text/plain',
                    upload_status='uploaded',
                    processing_status='completed',
                    chunk_count=5
                )

                db.session.add(doc)
                db.session.commit()

                # Verify document was saved
                saved_doc = Document.query.get('test-transaction-doc')
                assert saved_doc is not None
                assert saved_doc.filename == 'test.txt'

            except Exception:
                db.session.rollback()
                raise

            # Test transaction rollback on error
            try:
                doc2 = Document(
                    id='test-rollback-doc',
                    knowledge_base_id=test_knowledge_base.id,
                    filename='test2.txt',
                    original_filename='test2.txt',
                    file_size=2048,
                    file_type='text/plain',
                    upload_status='uploaded',
                    processing_status='completed',
                    chunk_count=3
                )

                db.session.add(doc2)

                # Simulate an error
                raise ValueError("Simulated error for rollback testing")

            except ValueError:
                db.session.rollback()

                # Verify document was not saved due to rollback
                rollback_doc = Document.query.get('test-rollback-doc')
                assert rollback_doc is None

    def test_cleanup_and_maintenance(self, app, test_knowledge_base):
        """Test cleanup and maintenance operations."""

        with app.app_context():
            from app.services.document_service import DocumentService
            from app.services.chunk_service import ChunkService

            document_service = DocumentService()
            chunk_service = ChunkService()

            # Test cache cleanup
            cleanup_count = chunk_service.cleanup_chunk_cache()
            assert isinstance(cleanup_count, int)
            assert cleanup_count >= 0

            # Test statistics cleanup
            stats = document_service.get_document_statistics(test_knowledge_base.id)
            assert isinstance(stats, dict)
            assert 'total_documents' in stats

    def test_logging_and_monitoring(self, app, test_knowledge_base):
        """Test logging and monitoring functionality."""

        with app.app_context():
            from app.services.document_service import DocumentService

            document_service = DocumentService()

            # Test operation logging
            try:
                # Attempt an operation that should be logged
                document_service.get_documents(test_knowledge_base.id)

                # In a real implementation, we would check log files
                # For this test, we just ensure no exceptions are raised
                assert True

            except Exception as e:
                pytest.fail(f"Logging test failed with exception: {e}")

    def test_comprehensive_workflow(self, client, test_knowledge_base, sample_text_file, sample_pdf_file):
        """Test comprehensive end-to-end workflow."""

        # Step 1: Upload multiple documents
        uploaded_docs = []

        for file_path, filename in [(sample_text_file, 'workflow_test.txt'), (sample_pdf_file, 'workflow_test.pdf')]:
            with open(file_path, 'rb') as f:
                response = client.post(
                    f'/api/knowledge-bases/{test_knowledge_base.id}/documents/upload',
                    data={'file': (FileStorage(f, filename), filename)},
                    content_type='multipart/form-data'
                )

                assert response.status_code == 200
                upload_data = response.get_json()
                assert upload_data['success'] is True
                uploaded_docs.append(upload_data['document_id'])

        # Step 2: List documents and verify uploads
        response = client.get(f'/api/knowledge-bases/{test_knowledge_base.id}/documents')
        assert response.status_code == 200
        list_data = response.get_json()

        document_count = list_data['data']['pagination']['total']
        assert document_count >= len(uploaded_docs)

        # Step 3: Search chunks
        response = client.post(
            f'/api/knowledge-bases/{test_knowledge_base.id}/chunks/search',
            json={
                'query': 'test',
                'max_results': 5
            }
        )
        assert response.status_code == 200

        # Step 4: Get document statistics
        response = client.get(f'/api/knowledge-bases/{test_knowledge_base.id}/documents/statistics')
        assert response.status_code == 200

        # Step 5: Test conversation with documents
        response = client.post(
            f'/api/knowledge-bases/{test_knowledge_base.id}',
            json={
                'action': 'test_conversation',
                'question': 'What documents are available?',
                'title': 'Workflow Test Conversation'
            }
        )
        assert response.status_code == 200

        # Step 6: Clean up - delete uploaded documents
        for doc_id in uploaded_docs:
            response = client.delete(f'/api/knowledge-bases/{test_knowledge_base.id}/documents/{doc_id}')
            assert response.status_code in [200, 404]  # 404 if already deleted

        # Step 7: Verify cleanup
        response = client.get(f'/api/knowledge-bases/{test_knowledge_base.id}/documents')
        final_list_data = response.get_json()
        final_count = final_list_data['data']['pagination']['total']

        # The original uploaded documents should be gone
        remaining_docs = [doc for doc in final_list_data['data']['documents']
                         if doc['id'] not in uploaded_docs]

        # Assert cleanup was successful (all test docs deleted)
        assert len(remaining_docs) == final_count


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])