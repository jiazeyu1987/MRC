#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Knowledge Base Unit Tests

Comprehensive unit tests for the knowledge base system including:
- KnowledgeBaseService tests with mock responses
- RAGFlowService tests with mock API responses
- Model operations tests
- API endpoint tests with error handling scenarios

Tests follow existing project patterns and include comprehensive database setup.
"""

import unittest
import json
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from flask import Flask

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import KnowledgeBase, RoleKnowledgeBase, Role
from app.services.knowledge_base_service import (
    KnowledgeBaseService,
    KnowledgeBaseValidationError,
    KnowledgeBaseNotFoundError,
    get_knowledge_base_service
)
from app.services.ragflow_service import (
    RAGFlowService,
    RAGFlowConfig,
    RAGFlowAPIError,
    RAGFlowConnectionError,
    DatasetInfo,
    ChatResponse,
    get_ragflow_service
)
from app.services.cache_service import get_cache_service


class TestKnowledgeBaseModel(unittest.TestCase):
    """Test KnowledgeBase model operations"""

    def setUp(self):
        """Set up test database"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Configure in-memory database
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['TESTING'] = True

        db.create_all()

    def tearDown(self):
        """Clean up test database"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_knowledge_base_creation(self):
        """Test KnowledgeBase model creation"""
        kb = KnowledgeBase(
            ragflow_dataset_id='test-dataset-123',
            name='Test Knowledge Base',
            description='Test description',
            document_count=10,
            total_size=1024,
            status='active'
        )

        db.session.add(kb)
        db.session.commit()

        retrieved_kb = KnowledgeBase.query.first()

        self.assertEqual(retrieved_kb.ragflow_dataset_id, 'test-dataset-123')
        self.assertEqual(retrieved_kb.name, 'Test Knowledge Base')
        self.assertEqual(retrieved_kb.description, 'Test description')
        self.assertEqual(retrieved_kb.document_count, 10)
        self.assertEqual(retrieved_kb.total_size, 1024)
        self.assertEqual(retrieved_kb.status, 'active')
        self.assertIsNotNone(retrieved_kb.created_at)
        self.assertIsNotNone(retrieved_kb.updated_at)

    def test_knowledge_base_to_dict(self):
        """Test KnowledgeBase to_dict method"""
        kb = KnowledgeBase(
            ragflow_dataset_id='test-dataset-456',
            name='Test KB',
            description='Test',
            document_count=5,
            total_size=512,
            status='inactive'
        )

        kb_dict = kb.to_dict()

        self.assertIsInstance(kb_dict, dict)
        self.assertEqual(kb_dict['ragflow_dataset_id'], 'test-dataset-456')
        self.assertEqual(kb_dict['name'], 'Test KB')
        self.assertEqual(kb_dict['document_count'], 5)
        self.assertEqual(kb_dict['status'], 'inactive')
        self.assertIn('created_at', kb_dict)
        self.assertIn('updated_at', kb_dict)

    def test_knowledge_base_repr(self):
        """Test KnowledgeBase __repr__ method"""
        kb = KnowledgeBase(
            ragflow_dataset_id='test-123',
            name='Test Knowledge Base',
            description='Test'
        )

        expected_repr = '<KnowledgeBase Test Knowledge Base>'
        self.assertEqual(repr(kb), expected_repr)

    def test_unique_ragflow_dataset_id(self):
        """Test unique constraint on ragflow_dataset_id"""
        kb1 = KnowledgeBase(
            ragflow_dataset_id='duplicate-dataset',
            name='KB 1',
            description='First'
        )

        kb2 = KnowledgeBase(
            ragflow_dataset_id='duplicate-dataset',  # Same ID
            name='KB 2',
            description='Second'
        )

        db.session.add(kb1)
        db.session.commit()

        db.session.add(kb2)
        with self.assertRaises(Exception):  # Should raise IntegrityError
            db.session.commit()


class TestRoleKnowledgeBaseModel(unittest.TestCase):
    """Test RoleKnowledgeBase model operations"""

    def setUp(self):
        """Set up test database"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()

        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['TESTING'] = True

        db.create_all()

        # Create test data
        self.role = Role(
            name='Test Role',
            type='teacher',
            description='Test role description',
            style_guidelines='Test guidelines',
            constraints='Test constraints',
            prompt_template='Test template'
        )

        self.kb = KnowledgeBase(
            ragflow_dataset_id='test-dataset',
            name='Test KB',
            description='Test'
        )

        db.session.add(self.role)
        db.session.add(self.kb)
        db.session.commit()

    def tearDown(self):
        """Clean up test database"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_role_knowledge_base_creation(self):
        """Test RoleKnowledgeBase creation"""
        role_kb = RoleKnowledgeBase(
            role_id=self.role.id,
            knowledge_base_id=self.kb.id,
            priority=1,
            retrieval_config='{"test": "config"}',
            is_active=True
        )

        db.session.add(role_kb)
        db.session.commit()

        retrieved = RoleKnowledgeBase.query.first()
        self.assertEqual(retrieved.role_id, self.role.id)
        self.assertEqual(retrieved.knowledge_base_id, self.kb.id)
        self.assertEqual(retrieved.priority, 1)
        self.assertTrue(retrieved.is_active)

    def test_retrieval_config_dict_property(self):
        """Test retrieval_config_dict property"""
        role_kb = RoleKnowledgeBase(
            role_id=self.role.id,
            knowledge_base_id=self.kb.id,
            retrieval_config='{"key": "value", "number": 123}'
        )

        config_dict = role_kb.retrieval_config_dict
        self.assertEqual(config_dict['key'], 'value')
        self.assertEqual(config_dict['number'], 123)

    def test_retrieval_config_dict_setter(self):
        """Test retrieval_config_dict setter"""
        role_kb = RoleKnowledgeBase(
            role_id=self.role.id,
            knowledge_base_id=self.kb.id
        )

        role_kb.retrieval_config_dict = {'new_key': 'new_value', 'count': 5}
        self.assertEqual(role_kb.retrieval_config_dict['new_key'], 'new_value')
        self.assertEqual(role_kb.retrieval_config_dict['count'], 5)

    def test_unique_role_knowledge_base_constraint(self):
        """Test unique constraint on role_id and knowledge_base_id"""
        role_kb1 = RoleKnowledgeBase(
            role_id=self.role.id,
            knowledge_base_id=self.kb.id
        )

        role_kb2 = RoleKnowledgeBase(
            role_id=self.role.id,  # Same role
            knowledge_base_id=self.kb.id  # Same knowledge base
        )

        db.session.add(role_kb1)
        db.session.commit()

        db.session.add(role_kb2)
        with self.assertRaises(Exception):  # Should raise IntegrityError
            db.session.commit()

    def test_to_dict_method(self):
        """Test RoleKnowledgeBase to_dict method"""
        role_kb = RoleKnowledgeBase(
            role_id=self.role.id,
            knowledge_base_id=self.kb.id,
            priority=2,
            is_active=True
        )

        role_kb_dict = role_kb.to_dict()

        self.assertIsInstance(role_kb_dict, dict)
        self.assertEqual(role_kb_dict['role_id'], self.role.id)
        self.assertEqual(role_kb_dict['knowledge_base_id'], self.kb.id)
        self.assertEqual(role_kb_dict['priority'], 2)
        self.assertTrue(role_kb_dict['is_active'])
        self.assertEqual(role_kb_dict['role_name'], self.role.name)
        self.assertEqual(role_kb_dict['knowledge_base_name'], self.kb.name)


class TestKnowledgeBaseService(unittest.TestCase):
    """Test KnowledgeBaseService operations"""

    def setUp(self):
        """Set up test environment"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()

        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['TESTING'] = True

        db.create_all()

        # Create test role
        self.test_role = Role(
            name='Test Teacher',
            type='teacher',
            description='Test teacher role',
            prompt_template='Test template'
        )
        db.session.add(self.test_role)
        db.session.commit()

    def tearDown(self):
        """Clean up test environment"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    @patch('app.services.knowledge_base_service.get_cache_service')
    def test_create_knowledge_base_success(self, mock_cache):
        """Test successful knowledge base creation"""
        mock_cache_instance = Mock()
        mock_cache.return_value = mock_cache_instance

        kb = KnowledgeBaseService.create_knowledge_base(
            ragflow_dataset_id='test-dataset-123',
            name='Test Knowledge Base',
            description='Test description',
            document_count=15,
            total_size=2048,
            status='active'
        )

        self.assertIsNotNone(kb)
        self.assertEqual(kb.ragflow_dataset_id, 'test-dataset-123')
        self.assertEqual(kb.name, 'Test Knowledge Base')
        self.assertEqual(kb.document_count, 15)
        self.assertEqual(kb.total_size, 2048)

        mock_cache_instance.clear.assert_called()

    def test_create_knowledge_base_validation_error(self):
        """Test knowledge base creation with validation errors"""
        with self.assertRaises(KnowledgeBaseValidationError):
            KnowledgeBaseService.create_knowledge_base(
                ragflow_dataset_id='',  # Empty dataset ID
                name='Test KB'
            )

        with self.assertRaises(KnowledgeBaseValidationError):
            KnowledgeBaseService.create_knowledge_base(
                ragflow_dataset_id='test-123',
                name=''  # Empty name
            )

    def test_create_knowledge_base_duplicate_dataset_id(self):
        """Test creation with duplicate RAGFlow dataset ID"""
        # Create first knowledge base
        KnowledgeBaseService.create_knowledge_base(
            ragflow_dataset_id='duplicate-123',
            name='First KB'
        )

        # Try to create second with same dataset ID
        with self.assertRaises(KnowledgeBaseValidationError):
            KnowledgeBaseService.create_knowledge_base(
                ragflow_dataset_id='duplicate-123',
                name='Second KB'
            )

    @patch('app.services.knowledge_base_service.get_cache_service')
    def test_get_knowledge_base_by_id(self, mock_cache):
        """Test get knowledge base by ID"""
        mock_cache_instance = Mock()
        mock_cache.return_value = mock_cache_instance
        mock_cache_instance.get.return_value = None  # No cache hit

        # Create test knowledge base
        kb = KnowledgeBaseService.create_knowledge_base(
            ragflow_dataset_id='test-123',
            name='Test KB'
        )

        # Retrieve by ID
        retrieved_kb = KnowledgeBaseService.get_knowledge_base_by_id(kb.id)

        self.assertIsNotNone(retrieved_kb)
        self.assertEqual(retrieved_kb.id, kb.id)
        self.assertEqual(retrieved_kb.name, 'Test KB')

        # Verify cache was called
        mock_cache_instance.get.assert_called()
        mock_cache_instance.set.assert_called()

    @patch('app.services.knowledge_base_service.get_cache_service')
    def test_get_knowledge_base_by_ragflow_id(self, mock_cache):
        """Test get knowledge base by RAGFlow dataset ID"""
        mock_cache_instance = Mock()
        mock_cache.return_value = mock_cache_instance
        mock_cache_instance.get.return_value = None

        # Create test knowledge base
        kb = KnowledgeBaseService.create_knowledge_base(
            ragflow_dataset_id='ragflow-test-456',
            name='Test KB'
        )

        # Retrieve by RAGFlow ID
        retrieved_kb = KnowledgeBaseService.get_knowledge_base_by_ragflow_id('ragflow-test-456')

        self.assertIsNotNone(retrieved_kb)
        self.assertEqual(retrieved_kb.ragflow_dataset_id, 'ragflow-test-456')

        mock_cache_instance.get.assert_called()
        mock_cache_instance.set.assert_called()

    def test_update_knowledge_base_success(self):
        """Test successful knowledge base update"""
        # Create knowledge base
        kb = KnowledgeBaseService.create_knowledge_base(
            ragflow_dataset_id='test-123',
            name='Original Name',
            description='Original description'
        )

        # Update knowledge base
        updated_kb = KnowledgeBaseService.update_knowledge_base(
            knowledge_base_id=kb.id,
            name='Updated Name',
            description='Updated description',
            status='inactive'
        )

        self.assertEqual(updated_kb.name, 'Updated Name')
        self.assertEqual(updated_kb.description, 'Updated description')
        self.assertEqual(updated_kb.status, 'inactive')

    def test_update_knowledge_base_not_found(self):
        """Test update non-existent knowledge base"""
        with self.assertRaises(KnowledgeBaseNotFoundError):
            KnowledgeBaseService.update_knowledge_base(
                knowledge_base_id=999,
                name='Updated Name'
            )

    def test_update_knowledge_base_validation_error(self):
        """Test update with validation error"""
        # Create knowledge base
        kb = KnowledgeBaseService.create_knowledge_base(
            ragflow_dataset_id='test-123',
            name='Original Name'
        )

        # Try to update with empty name
        with self.assertRaises(KnowledgeBaseValidationError):
            KnowledgeBaseService.update_knowledge_base(
                knowledge_base_id=kb.id,
                name=''  # Empty name
            )

    def test_delete_knowledge_base_success(self):
        """Test successful knowledge base deletion"""
        # Create knowledge base
        kb = KnowledgeBaseService.create_knowledge_base(
            ragflow_dataset_id='test-delete-123',
            name='To Delete'
        )

        # Delete knowledge base
        result = KnowledgeBaseService.delete_knowledge_base(kb.id)

        self.assertTrue(result)

        # Verify deletion
        deleted_kb = KnowledgeBase.query.get(kb.id)
        self.assertIsNone(deleted_kb)

    def test_delete_knowledge_base_not_found(self):
        """Test delete non-existent knowledge base"""
        with self.assertRaises(KnowledgeBaseNotFoundError):
            KnowledgeBaseService.delete_knowledge_base(999)

    def test_delete_knowledge_base_with_role_association(self):
        """Test delete knowledge base with role associations"""
        # Create knowledge base
        kb = KnowledgeBaseService.create_knowledge_base(
            ragflow_dataset_id='test-assoc-123',
            name='KB with associations'
        )

        # Create role association
        role_kb = RoleKnowledgeBase(
            role_id=self.test_role.id,
            knowledge_base_id=kb.id
        )
        db.session.add(role_kb)
        db.session.commit()

        # Try to delete - should fail
        with self.assertRaises(KnowledgeBaseValidationError):
            KnowledgeBaseService.delete_knowledge_base(kb.id)

    def test_get_knowledge_bases_list(self):
        """Test get knowledge bases list with pagination"""
        # Create test knowledge bases
        for i in range(5):
            KnowledgeBaseService.create_knowledge_base(
                ragflow_dataset_id=f'test-dataset-{i}',
                name=f'Test KB {i}'
            )

        # Get list with pagination
        kbs, total, pagination = KnowledgeBaseService.get_knowledge_bases_list(
            page=1,
            per_page=3
        )

        self.assertEqual(len(kbs), 3)
        self.assertEqual(total, 5)
        self.assertEqual(pagination['page'], 1)
        self.assertEqual(pagination['per_page'], 3)

    def test_get_knowledge_bases_list_with_filters(self):
        """Test get knowledge bases list with filters"""
        # Create knowledge bases with different statuses
        KnowledgeBaseService.create_knowledge_base(
            ragflow_dataset_id='active-1',
            name='Active KB',
            status='active'
        )
        KnowledgeBaseService.create_knowledge_base(
            ragflow_dataset_id='inactive-1',
            name='Inactive KB',
            status='inactive'
        )

        # Filter by status
        active_kbs, total, _ = KnowledgeBaseService.get_knowledge_bases_list(
            status='active'
        )

        self.assertEqual(len(active_kbs), 1)
        self.assertEqual(active_kbs[0].status, 'active')
        self.assertEqual(total, 1)

    def test_get_knowledge_bases_list_with_search(self):
        """Test get knowledge bases list with search"""
        # Create knowledge bases
        KnowledgeBaseService.create_knowledge_base(
            ragflow_dataset_id='search-1',
            name='Python Programming',
            description='Python tutorials'
        )
        KnowledgeBaseService.create_knowledge_base(
            ragflow_dataset_id='search-2',
            name='JavaScript Guide',
            description='JS tutorials'
        )

        # Search by name
        search_kbs, total, _ = KnowledgeBaseService.get_knowledge_bases_list(
            search='Python'
        )

        self.assertEqual(len(search_kbs), 1)
        self.assertIn('Python', search_kbs[0].name)

    @patch('app.services.knowledge_base_service.get_ragflow_service')
    def test_sync_datasets_from_ragflow(self, mock_ragflow):
        """Test sync datasets from RAGFlow"""
        # Mock RAGFlow service response
        mock_ragflow_instance = Mock()
        mock_ragflow.return_value = mock_ragflow_instance

        mock_datasets = [
            DatasetInfo(
                id='ragflow-1',
                name='Synced KB 1',
                description='First synced KB',
                document_count=20,
                size=4096,
                status='active'
            ),
            DatasetInfo(
                id='ragflow-2',
                name='Synced KB 2',
                description='Second synced KB',
                document_count=15,
                size=2048,
                status='active'
            )
        ]

        mock_ragflow_instance.get_datasets.return_value = mock_datasets

        # Perform sync
        sync_result = KnowledgeBaseService.sync_datasets_from_ragflow()

        # Verify results
        self.assertEqual(sync_result['total_datasets'], 2)
        self.assertEqual(sync_result['created'], 2)
        self.assertEqual(sync_result['updated'], 0)

        # Verify knowledge bases were created
        created_kbs = KnowledgeBase.query.all()
        self.assertEqual(len(created_kbs), 2)
        self.assertEqual(created_kbs[0].ragflow_dataset_id, 'ragflow-1')
        self.assertEqual(created_kbs[1].ragflow_dataset_id, 'ragflow-2')

    def test_assign_knowledge_base_to_role(self):
        """Test assign knowledge base to role"""
        # Create knowledge base
        kb = KnowledgeBaseService.create_knowledge_base(
            ragflow_dataset_id='assign-123',
            name='KB for role assignment'
        )

        # Assign to role
        role_kb = KnowledgeBaseService.assign_knowledge_base_to_role(
            role_id=self.test_role.id,
            knowledge_base_id=kb.id,
            priority=1,
            retrieval_config={'test': 'config'},
            is_active=True
        )

        self.assertIsNotNone(role_kb)
        self.assertEqual(role_kb.role_id, self.test_role.id)
        self.assertEqual(role_kb.knowledge_base_id, kb.id)
        self.assertEqual(role_kb.priority, 1)
        self.assertTrue(role_kb.is_active)
        self.assertEqual(role_kb.retrieval_config_dict['test'], 'config')

    def test_assign_knowledge_base_to_role_not_found(self):
        """Test assign knowledge base to non-existent role"""
        with self.assertRaises(KnowledgeBaseValidationError):
            KnowledgeBaseService.assign_knowledge_base_to_role(
                role_id=999,
                knowledge_base_id=1
            )

    def test_unassign_knowledge_base_from_role(self):
        """Test unassign knowledge base from role"""
        # Create and assign knowledge base
        kb = KnowledgeBaseService.create_knowledge_base(
            ragflow_dataset_id='unassign-123',
            name='KB for unassignment'
        )

        role_kb = KnowledgeBaseService.assign_knowledge_base_to_role(
            role_id=self.test_role.id,
            knowledge_base_id=kb.id
        )

        # Unassign
        result = KnowledgeBaseService.unassign_knowledge_base_from_role(
            role_id=self.test_role.id,
            knowledge_base_id=kb.id
        )

        self.assertTrue(result)

        # Verify unassignment
        deleted_role_kb = RoleKnowledgeBase.query.get(role_kb.id)
        self.assertIsNone(deleted_role_kb)

    def test_get_role_knowledge_bases(self):
        """Test get knowledge bases for a role"""
        # Create and assign multiple knowledge bases
        kb1 = KnowledgeBaseService.create_knowledge_base(
            ragflow_dataset_id='role-kb-1',
            name='Role KB 1'
        )
        kb2 = KnowledgeBaseService.create_knowledge_base(
            ragflow_dataset_id='role-kb-2',
            name='Role KB 2'
        )

        KnowledgeBaseService.assign_knowledge_base_to_role(
            role_id=self.test_role.id,
            knowledge_base_id=kb1.id,
            priority=1
        )
        KnowledgeBaseService.assign_knowledge_base_to_role(
            role_id=self.test_role.id,
            knowledge_base_id=kb2.id,
            priority=2
        )

        # Get role knowledge bases
        role_kbs = KnowledgeBaseService.get_role_knowledge_bases(self.test_role.id)

        self.assertEqual(len(role_kbs), 2)
        self.assertEqual(role_kbs[0]['priority'], 1)
        self.assertEqual(role_kbs[1]['priority'], 2)

    @patch('app.services.knowledge_base_service.get_cache_service')
    def test_get_knowledge_base_statistics(self, mock_cache):
        """Test get knowledge base statistics"""
        mock_cache_instance = Mock()
        mock_cache.return_value = mock_cache_instance
        mock_cache_instance.get.return_value = None

        # Create test knowledge bases
        KnowledgeBaseService.create_knowledge_base(
            ragflow_dataset_id='stats-1',
            name='Stats KB 1',
            document_count=10,
            total_size=1024,
            status='active'
        )
        KnowledgeBaseService.create_knowledge_base(
            ragflow_dataset_id='stats-2',
            name='Stats KB 2',
            document_count=20,
            total_size=2048,
            status='inactive'
        )

        # Get statistics
        stats = KnowledgeBaseService.get_knowledge_base_statistics()

        self.assertEqual(stats['knowledge_bases']['total'], 2)
        self.assertEqual(stats['knowledge_bases']['active'], 1)
        self.assertEqual(stats['knowledge_bases']['inactive'], 1)
        self.assertEqual(stats['documents']['total'], 30)
        self.assertEqual(stats['documents']['total_size'], 3072)

    def test_validate_status(self):
        """Test status validation"""
        # Valid status should not raise exception
        KnowledgeBaseService._validate_status('active')
        KnowledgeBaseService._validate_status('inactive')
        KnowledgeBaseService._validate_status('error')

        # Invalid status should raise exception
        with self.assertRaises(KnowledgeBaseValidationError):
            KnowledgeBaseService._validate_status('invalid_status')

    def test_format_size(self):
        """Test file size formatting"""
        self.assertEqual(KnowledgeBaseService._format_size(0), "0 B")
        self.assertEqual(KnowledgeBaseService._format_size(1024), "1.0 KB")
        self.assertEqual(KnowledgeBaseService._format_size(1048576), "1.0 MB")
        self.assertEqual(KnowledgeBaseService._format_size(1073741824), "1.0 GB")


class TestRAGFlowService(unittest.TestCase):
    """Test RAGFlowService operations"""

    def setUp(self):
        """Set up test environment"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Clean up test environment"""
        self.app_context.pop()

    @patch.dict(os.environ, {
        'RAGFLOW_API_BASE_URL': 'https://test.ragflow.com',
        'RAGFLOW_API_KEY': 'test-api-key-123'
    })
    def test_ragflow_config_creation_from_env(self):
        """Test RAGFlow config creation from environment variables"""
        # Create a dummy service instance to test the static method
        with patch('app.services.ragflow_service.RAGFlowService.__init__', return_value=None):
            service = RAGFlowService.__new__(RAGFlowService)
            config = service._load_config_from_env()

            self.assertEqual(config.api_base_url, 'https://test.ragflow.com')
            self.assertEqual(config.api_key, 'test-api-key-123')
            self.assertEqual(config.timeout, 30)
            self.assertEqual(config.max_retries, 3)

    @patch.dict(os.environ, {}, clear=True)
    def test_ragflow_config_missing_env_vars(self):
        """Test RAGFlow config with missing environment variables"""
        # Create a dummy service instance to test the static method
        with patch('app.services.ragflow_service.RAGFlowService.__init__', return_value=None):
            service = RAGFlowService.__new__(RAGFlowService)
            with self.assertRaises(RAGFlowConfigError):
                service._load_config_from_env()

    def test_ragflow_config_validation(self):
        """Test RAGFlow config validation"""
        # Valid config
        config = RAGFlowConfig(
            api_base_url='https://test.com',
            api_key='test-key'
        )
        self.assertEqual(config.api_base_url, 'https://test.com')

        # Invalid config - empty URL
        with self.assertRaises(ValueError):
            RAGFlowConfig(
                api_base_url='',
                api_key='test-key'
            )

        # Invalid config - empty API key
        with self.assertRaises(ValueError):
            RAGFlowConfig(
                api_base_url='https://test.com',
                api_key=''
            )

    def test_ragflow_config_url_normalization(self):
        """Test RAGFlow config URL normalization"""
        # URL with trailing slash should be normalized
        config = RAGFlowConfig(
            api_base_url='https://test.com/',
            api_key='test-key'
        )
        self.assertEqual(config.api_base_url, 'https://test.com')

    def test_dataset_info_from_dict(self):
        """Test DatasetInfo creation from dictionary"""
        data = {
            'id': 'dataset-123',
            'name': 'Test Dataset',
            'description': 'Test description',
            'document_count': 25,
            'size': 5120,
            'status': 'active',
            'created_at': '2023-01-01T00:00:00Z',
            'updated_at': '2023-01-02T00:00:00Z'
        }

        dataset_info = DatasetInfo.from_dict(data)

        self.assertEqual(dataset_info.id, 'dataset-123')
        self.assertEqual(dataset_info.name, 'Test Dataset')
        self.assertEqual(dataset_info.document_count, 25)
        self.assertEqual(dataset_info.size, 5120)
        self.assertEqual(dataset_info.status, 'active')
        self.assertIsNotNone(dataset_info.created_at)
        self.assertIsNotNone(dataset_info.updated_at)

    def test_chat_response_from_api_response(self):
        """Test ChatResponse creation from API response"""
        api_response = {
            'answer': 'This is the answer to your question.',
            'confidence_score': 0.85,
            'references': [{'doc_id': 'doc-1', 'content': 'Reference content'}],
            'metadata': {'model': 'test-model', 'tokens': 150}
        }

        chat_response = ChatResponse.from_api_response(
            api_response,
            query='Test question',
            dataset_id='dataset-123',
            response_time=1.5
        )

        self.assertEqual(chat_response.answer, 'This is the answer to your question.')
        self.assertEqual(chat_response.confidence_score, 0.85)
        self.assertEqual(chat_response.query, 'Test question')
        self.assertEqual(chat_response.dataset_id, 'dataset-123')
        self.assertEqual(chat_response.response_time, 1.5)
        self.assertEqual(len(chat_response.references), 1)

    @patch('requests.Session.get')
    @patch.dict(os.environ, {
        'RAGFLOW_API_BASE_URL': 'https://test.ragflow.com',
        'RAGFLOW_API_KEY': 'test-api-key'
    })
    def test_get_datasets_success(self, mock_get):
        """Test successful get datasets call"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {
                    'id': 'dataset-1',
                    'name': 'Dataset 1',
                    'description': 'First dataset',
                    'document_count': 10,
                    'size': 1024,
                    'status': 'active'
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Create service
        config = RAGFlowConfig(
            api_base_url='https://test.ragflow.com',
            api_key='test-api-key'
        )
        service = RAGFlowService(config)

        # Call get_datasets
        datasets = service.get_datasets()

        # Verify results
        self.assertEqual(len(datasets), 1)
        self.assertEqual(datasets[0].id, 'dataset-1')
        self.assertEqual(datasets[0].name, 'Dataset 1')
        self.assertEqual(datasets[0].document_count, 10)

    @patch('requests.Session.get')
    @patch.dict(os.environ, {
        'RAGFLOW_API_BASE_URL': 'https://test.ragflow.com',
        'RAGFLOW_API_KEY': 'test-api-key'
    })
    def test_get_datasets_api_error(self, mock_get):
        """Test get datasets with API error"""
        # Mock API error response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = Exception("Server Error")
        mock_get.return_value = mock_response

        config = RAGFlowConfig(
            api_base_url='https://test.ragflow.com',
            api_key='test-api-key'
        )
        service = RAGFlowService(config)

        with self.assertRaises(RAGFlowAPIError):
            service.get_datasets()

    @patch('requests.Session.post')
    @patch.dict(os.environ, {
        'RAGFLOW_API_BASE_URL': 'https://test.ragflow.com',
        'RAGFLOW_API_KEY': 'test-api-key'
    })
    def test_chat_success(self, mock_post):
        """Test successful chat call"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'answer': 'This is the answer.',
            'confidence_score': 0.9,
            'references': [],
            'metadata': {}
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        config = RAGFlowConfig(
            api_base_url='https://test.ragflow.com',
            api_key='test-api-key'
        )
        service = RAGFlowService(config)

        # Call chat
        response = service.chat(
            dataset_id='dataset-123',
            query='What is Python?'
        )

        # Verify results
        self.assertEqual(response.answer, 'This is the answer.')
        self.assertEqual(response.confidence_score, 0.9)
        self.assertEqual(response.dataset_id, 'dataset-123')
        self.assertEqual(response.query, 'What is Python?')

    @patch('requests.Session.post')
    @patch.dict(os.environ, {
        'RAGFLOW_API_BASE_URL': 'https://test.ragflow.com',
        'RAGFLOW_API_KEY': 'test-api-key'
    })
    def test_chat_api_error(self, mock_post):
        """Test chat with API error"""
        # Mock API error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = Exception("Bad Request")
        mock_post.return_value = mock_response

        config = RAGFlowConfig(
            api_base_url='https://test.ragflow.com',
            api_key='test-api-key'
        )
        service = RAGFlowService(config)

        with self.assertRaises(RAGFlowAPIError):
            service.chat(
                dataset_id='dataset-123',
                query='Test question'
            )

    @patch('requests.Session.get')
    @patch.dict(os.environ, {
        'RAGFLOW_API_BASE_URL': 'https://test.ragflow.com',
        'RAGFLOW_API_KEY': 'test-api-key'
    })
    def test_connection_test_success(self, mock_get):
        """Test successful connection test"""
        # Mock successful health check response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 'healthy'}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        config = RAGFlowConfig(
            api_base_url='https://test.ragflow.com',
            api_key='test-api-key'
        )
        service = RAGFlowService(config)

        # Test connection
        is_connected, message = service.test_connection()

        self.assertTrue(is_connected)
        self.assertIn('成功', message) or 'success' in message.lower()

    @patch('requests.Session.get')
    @patch.dict(os.environ, {
        'RAGFLOW_API_BASE_URL': 'https://test.ragflow.com',
        'RAGFLOW_API_KEY': 'test-api-key'
    })
    def test_connection_test_failure(self, mock_get):
        """Test connection test failure"""
        # Mock connection failure
        mock_get.side_effect = Exception("Connection failed")

        config = RAGFlowConfig(
            api_base_url='https://test.ragflow.com',
            api_key='test-api-key'
        )
        service = RAGFlowService(config)

        # Test connection
        is_connected, message = service.test_connection()

        self.assertFalse(is_connected)
        self.assertIn('失败', message) or 'failed' in message.lower()


class TestKnowledgeBaseAPI(unittest.TestCase):
    """Test Knowledge Base API endpoints"""

    def setUp(self):
        """Set up test environment"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()

        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        """Clean up test environment"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_get_knowledge_base_list_empty(self):
        """Test get empty knowledge base list"""
        response = self.client.get('/api/knowledge-bases')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['total'], 0)
        self.assertEqual(len(data['data']['knowledge_bases']), 0)

    def test_get_knowledge_base_list_with_data(self):
        """Test get knowledge base list with data"""
        # Create test knowledge base
        kb = KnowledgeBase(
            ragflow_dataset_id='test-api-123',
            name='API Test KB',
            description='Test description'
        )
        db.session.add(kb)
        db.session.commit()

        response = self.client.get('/api/knowledge-bases')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['total'], 1)
        self.assertEqual(len(data['data']['knowledge_bases']), 1)
        self.assertEqual(data['data']['knowledge_bases'][0]['name'], 'API Test KB')

    def test_get_knowledge_base_list_with_pagination(self):
        """Test get knowledge base list with pagination"""
        # Create multiple knowledge bases
        for i in range(5):
            kb = KnowledgeBase(
                ragflow_dataset_id=f'paginated-{i}',
                name=f'Paginated KB {i}'
            )
            db.session.add(kb)
        db.session.commit()

        # Get first page
        response = self.client.get('/api/knowledge-bases?page=1&page_size=2')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['total'], 5)
        self.assertEqual(len(data['data']['knowledge_bases']), 2)
        self.assertEqual(data['data']['page'], 1)
        self.assertEqual(data['data']['page_size'], 2)

    def test_get_knowledge_base_list_with_search(self):
        """Test get knowledge base list with search"""
        # Create test knowledge bases
        kb1 = KnowledgeBase(
            ragflow_dataset_id='searchable-1',
            name='Python Programming',
            description='Python tutorials'
        )
        kb2 = KnowledgeBase(
            ragflow_dataset_id='searchable-2',
            name='JavaScript Guide',
            description='JS tutorials'
        )
        db.session.add(kb1)
        db.session.add(kb2)
        db.session.commit()

        # Search for Python
        response = self.client.get('/api/knowledge-bases?search=Python')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['total'], 1)
        self.assertEqual(data['data']['knowledge_bases'][0]['name'], 'Python Programming')

    @patch('app.services.knowledge_base_service.get_ragflow_service')
    def test_post_refresh_all_success(self, mock_ragflow):
        """Test POST refresh all datasets with mocked RAGFlow"""
        # Mock RAGFlow service
        mock_ragflow_instance = Mock()
        mock_ragflow.return_value = mock_ragflow_instance

        mock_datasets = [
            DatasetInfo(
                id='refresh-1',
                name='Refresh KB 1',
                description='First refresh',
                document_count=10,
                size=1024,
                status='active'
            )
        ]
        mock_ragflow_instance.get_datasets.return_value = mock_datasets

        # Send refresh request
        response = self.client.post('/api/knowledge-bases',
                                   json={'action': 'refresh_all'},
                                   content_type='application/json')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('created', data['data'])
        self.assertIn('updated', data['data'])

    def test_post_invalid_action(self):
        """Test POST with invalid action"""
        response = self.client.post('/api/knowledge-bases',
                                   json={'action': 'invalid_action'},
                                   content_type='application/json')

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])

    def test_post_empty_request(self):
        """Test POST with empty request"""
        response = self.client.post('/api/knowledge-bases')

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])

    def test_get_knowledge_base_statistics(self):
        """Test get knowledge base statistics"""
        # Create test knowledge bases
        kb1 = KnowledgeBase(
            ragflow_dataset_id='stats-1',
            name='Stats KB 1',
            document_count=15,
            total_size=2048,
            status='active'
        )
        kb2 = KnowledgeBase(
            ragflow_dataset_id='stats-2',
            name='Stats KB 2',
            document_count=25,
            total_size=3072,
            status='inactive'
        )
        db.session.add(kb1)
        db.session.add(kb2)
        db.session.commit()

        response = self.client.get('/api/knowledge-bases/statistics')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['knowledge_bases']['total'], 2)
        self.assertEqual(data['data']['knowledge_bases']['active'], 1)
        self.assertEqual(data['data']['documents']['total'], 40)

    @patch('app.services.ragflow_service.get_ragflow_service')
    def test_post_knowledge_base_test_conversation_success(self, mock_ragflow):
        """Test POST knowledge base test conversation with mocked RAGFlow"""
        # Create test knowledge base
        kb = KnowledgeBase(
            ragflow_dataset_id='chat-test-123',
            name='Chat Test KB'
        )
        db.session.add(kb)
        db.session.commit()

        # Mock RAGFlow service response
        mock_ragflow_instance = Mock()
        mock_ragflow.return_value = mock_ragflow_instance

        mock_chat_response = Mock()
        mock_chat_response.response = 'This is a test answer.'
        mock_chat_response.confidence_score = 0.85
        mock_chat_response.references = []
        mock_ragflow_instance.chat_with_dataset.return_value = mock_chat_response

        # Send test conversation request
        response = self.client.post(f'/api/knowledge-bases/{kb.id}',
                                   json={
                                       'action': 'test_conversation',
                                       'question': 'What is Python?'
                                   },
                                   content_type='application/json')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['user_question'], 'What is Python?')

    @patch('app.services.ragflow_service.get_ragflow_service')
    def test_post_knowledge_base_test_conversation_ragflow_error(self, mock_ragflow):
        """Test POST knowledge base test conversation with RAGFlow error"""
        # Create test knowledge base
        kb = KnowledgeBase(
            ragflow_dataset_id='chat-error-123',
            name='Chat Error KB'
        )
        db.session.add(kb)
        db.session.commit()

        # Mock RAGFlow service error
        mock_ragflow_instance = Mock()
        mock_ragflow.return_value = mock_ragflow_instance
        mock_ragflow_instance.chat_with_dataset.side_effect = RAGFlowAPIError("RAGFlow API Error")

        # Send test conversation request
        response = self.client.post(f'/api/knowledge-bases/{kb.id}',
                                   json={
                                       'action': 'test_conversation',
                                       'question': 'Test question'
                                   },
                                   content_type='application/json')

        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('RAGFLOW_API_ERROR', data.get('error_code', ''))

    def test_post_knowledge_base_test_conversation_empty_question(self):
        """Test POST knowledge base test conversation with empty question"""
        # Create test knowledge base
        kb = KnowledgeBase(
            ragflow_dataset_id='empty-question-123',
            name='Empty Question KB'
        )
        db.session.add(kb)
        db.session.commit()

        # Send test conversation request with empty question
        response = self.client.post(f'/api/knowledge-bases/{kb.id}',
                                   json={
                                       'action': 'test_conversation',
                                       'question': '   '  # Empty whitespace
                                   },
                                   content_type='application/json')

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('测试问题不能为空', data.get('message', ''))


class TestIntegrationScenarios(unittest.TestCase):
    """Test integration scenarios between components"""

    def setUp(self):
        """Set up test environment"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()

        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        """Clean up test environment"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    @patch('app.services.knowledge_base_service.get_ragflow_service')
    @patch('app.services.knowledge_base_service.get_cache_service')
    def test_full_knowledge_base_workflow(self, mock_cache, mock_ragflow):
        """Test complete knowledge base workflow"""
        # Mock cache service
        mock_cache_instance = Mock()
        mock_cache.return_value = mock_cache_instance
        mock_cache_instance.get.return_value = None

        # Mock RAGFlow service
        mock_ragflow_instance = Mock()
        mock_ragflow.return_value = mock_ragflow_instance

        mock_datasets = [
            DatasetInfo(
                id='workflow-1',
                name='Workflow Test KB',
                description='Complete workflow test',
                document_count=20,
                size=4096,
                status='active'
            )
        ]
        mock_ragflow_instance.get_datasets.return_value = mock_datasets

        # 1. Sync datasets from RAGFlow
        sync_result = KnowledgeBaseService.sync_datasets_from_ragflow()
        self.assertEqual(sync_result['created'], 1)

        # 2. Verify knowledge base was created
        kb = KnowledgeBase.query.filter_by(ragflow_dataset_id='workflow-1').first()
        self.assertIsNotNone(kb)
        self.assertEqual(kb.name, 'Workflow Test KB')

        # 3. Create role and assign knowledge base
        role = Role(
            name='Test Teacher',
            type='teacher',
            description='Test teacher for workflow',
            prompt_template='Test template'
        )
        db.session.add(role)
        db.session.commit()

        role_kb = KnowledgeBaseService.assign_knowledge_base_to_role(
            role_id=role.id,
            knowledge_base_id=kb.id
        )
        self.assertIsNotNone(role_kb)

        # 4. Test API endpoint for getting role knowledge bases
        role_kbs = KnowledgeBaseService.get_role_knowledge_bases(role.id)
        self.assertEqual(len(role_kbs), 1)
        self.assertEqual(role_kbs[0]['knowledge_base_name'], 'Workflow Test KB')

        # 5. Test statistics
        stats = KnowledgeBaseService.get_knowledge_base_statistics()
        self.assertEqual(stats['knowledge_bases']['total'], 1)
        self.assertEqual(stats['associations']['total'], 1)

    def test_error_handling_and_recovery(self):
        """Test error handling and recovery scenarios"""
        # Test with invalid data
        with self.assertRaises(KnowledgeBaseValidationError):
            KnowledgeBaseService.create_knowledge_base(
                ragflow_dataset_id='',
                name='Test'
            )

        # Test with non-existent knowledge base
        with self.assertRaises(KnowledgeBaseNotFoundError):
            KnowledgeBaseService.get_knowledge_base_by_id(999)

        # Test database rollback on errors
        initial_count = KnowledgeBase.query.count()

        try:
            # This should fail and rollback
            KnowledgeBaseService.create_knowledge_base(
                ragflow_dataset_id='rollback-test',
                name='Rollback Test'
            )
            # Simulate database error
            db.session.rollback()
        except Exception:
            pass

        # Verify count didn't change
        final_count = KnowledgeBase.query.count()
        self.assertEqual(initial_count, final_count)


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)