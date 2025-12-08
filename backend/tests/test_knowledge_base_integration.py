#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Knowledge Base System Integration Tests

Comprehensive end-to-end tests for the knowledge base system including:
- Knowledge base discovery and sync from RAGFlow
- Test conversations with role integration
- Complete workflow validation from discovery to conversation
- Error scenarios and recovery mechanisms
- Performance requirements and configuration validation
- RAGFlow API failures and recovery mechanisms

Tests follow existing project patterns and provide comprehensive validation of the complete knowledge base system.
"""

import unittest
import json
import os
import sys
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from flask import Flask
import requests

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import (
    KnowledgeBase, RoleKnowledgeBase, Role, KnowledgeBaseConversation
)
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
    RAGFlowConfigError,
    RAGFlowConnectionError,
    DatasetInfo,
    ChatResponse,
    get_ragflow_service
)
from app.services.cache_service import get_cache_service


class TestKnowledgeBaseDiscoveryIntegration(unittest.TestCase):
    """Test knowledge base discovery and synchronization workflow"""

    def setUp(self):
        """Set up test environment"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()

        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['TESTING'] = True

        db.create_all()
        self.client = self.app.test_client()

        # Create test roles
        self.teacher_role = Role(
            name='Test Teacher',
            prompt='Test teacher role for knowledge base integration. Guidelines: Test teacher guidelines. Constraints: Test teacher constraints.'
        )

        self.student_role = Role(
            name='Test Student',
            prompt='Test student role for knowledge base integration. Guidelines: Test student guidelines. Constraints: Test student constraints.'
        )

        db.session.add(self.teacher_role)
        db.session.add(self.student_role)
        db.session.commit()

    def tearDown(self):
        """Clean up test environment"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    @patch('app.services.knowledge_base_service.get_ragflow_service')
    @patch('app.services.knowledge_base_service.get_cache_service')
    def test_complete_discovery_workflow(self, mock_cache, mock_ragflow):
        """Test complete knowledge base discovery workflow"""
        # Mock cache service
        mock_cache_instance = Mock()
        mock_cache.return_value = mock_cache_instance
        mock_cache_instance.get.return_value = None

        # Mock RAGFlow service with multiple datasets
        mock_ragflow_instance = Mock()
        mock_ragflow.return_value = mock_ragflow_instance

        mock_datasets = [
            DatasetInfo(
                id='discovery-math-001',
                name='高等数学知识库',
                description='涵盖微积分、线性代数等高等数学内容',
                document_count=150,
                size=5242880,  # 5MB
                status='active',
                created_at=datetime.utcnow() - timedelta(days=30),
                updated_at=datetime.utcnow() - timedelta(days=1)
            ),
            DatasetInfo(
                id='discovery-physics-002',
                name='物理学基础',
                description='经典力学、电磁学、量子物理基础',
                document_count=200,
                size=8388608,  # 8MB
                status='active',
                created_at=datetime.utcnow() - timedelta(days=25),
                updated_at=datetime.utcnow() - timedelta(hours=6)
            ),
            DatasetInfo(
                id='discovery-chemistry-003',
                name='化学知识库',
                description='有机化学、无机化学、物理化学',
                document_count=120,
                size=4194304,  # 4MB
                status='inactive',
                created_at=datetime.utcnow() - timedelta(days=20),
                updated_at=datetime.utcnow() - timedelta(days=2)
            )
        ]
        mock_ragflow_instance.get_datasets.return_value = mock_datasets

        # 1. Test API discovery endpoint
        response = self.client.post('/api/knowledge-bases',
                                   json={'action': 'refresh_all'},
                                   content_type='application/json')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['created'], 3)
        self.assertEqual(data['data']['updated'], 0)

        # 2. Verify knowledge bases were created in database
        created_kbs = KnowledgeBase.query.all()
        self.assertEqual(len(created_kbs), 3)

        math_kb = KnowledgeBase.query.filter_by(ragflow_dataset_id='discovery-math-001').first()
        self.assertIsNotNone(math_kb)
        self.assertEqual(math_kb.name, '高等数学知识库')
        self.assertEqual(math_kb.document_count, 150)
        self.assertEqual(math_kb.total_size, 5242880)
        self.assertEqual(math_kb.status, 'active')

        physics_kb = KnowledgeBase.query.filter_by(ragflow_dataset_id='discovery-physics-002').first()
        self.assertIsNotNone(physics_kb)
        self.assertEqual(physics_kb.name, '物理学基础')
        self.assertEqual(physics_kb.status, 'active')

        chemistry_kb = KnowledgeBase.query.filter_by(ragflow_dataset_id='discovery-chemistry-003').first()
        self.assertIsNotNone(chemistry_kb)
        self.assertEqual(chemistry_kb.status, 'inactive')

        # 3. Test API list endpoint with filters
        response = self.client.get('/api/knowledge-bases')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['data']['total'], 3)

        # Test status filter
        response = self.client.get('/api/knowledge-bases?status=active')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['data']['total'], 2)

        # Test search functionality
        response = self.client.get('/api/knowledge-bases?search=数学')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['data']['total'], 1)
        self.assertIn('数学', data['data']['knowledge_bases'][0]['name'])

    @patch('app.services.knowledge_base_service.get_ragflow_service')
    def test_discovery_with_ragflow_connection_error(self, mock_ragflow):
        """Test discovery workflow with RAGFlow connection errors"""
        # Mock RAGFlow service connection error
        mock_ragflow_instance = Mock()
        mock_ragflow.return_value = mock_ragflow_instance
        mock_ragflow_instance.get_datasets.side_effect = RAGFlowConnectionError("Connection timeout")

        # Test API discovery with connection error
        response = self.client.post('/api/knowledge-bases',
                                   json={'action': 'refresh_all'},
                                   content_type='application/json')

        # Should handle error gracefully
        self.assertIn(response.status_code, [500, 503])
        data = json.loads(response.data)
        self.assertFalse(data['success'])

    @patch('app.services.knowledge_base_service.get_ragflow_service')
    @patch('app.services.knowledge_base_service.get_cache_service')
    def test_discovery_with_partial_ragflow_failure(self, mock_cache, mock_ragflow):
        """Test discovery workflow with partial RAGFlow API failure"""
        # Mock cache service
        mock_cache_instance = Mock()
        mock_cache.return_value = mock_cache_instance
        mock_cache_instance.get.return_value = None

        # Mock RAGFlow service that fails after partial success
        mock_ragflow_instance = Mock()
        mock_ragflow.return_value = mock_ragflow_instance

        # First call succeeds, second call fails
        mock_ragflow_instance.get_datasets.side_effect = [
            [
                DatasetInfo(
                    id='partial-success-001',
                    name='部分成功知识库',
                    description='测试部分成功场景',
                    document_count=50,
                    size=1048576,
                    status='active'
                )
            ],
            RAGFlowAPIError("API rate limit exceeded")
        ]

        # First sync should succeed
        response = self.client.post('/api/knowledge-bases',
                                   json={'action': 'refresh_all'},
                                   content_type='application/json')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['created'], 1)

        # Verify knowledge base was created
        kb = KnowledgeBase.query.filter_by(ragflow_dataset_id='partial-success-001').first()
        self.assertIsNotNone(kb)

        # Second sync should fail gracefully
        response = self.client.post('/api/knowledge-bases',
                                   json={'action': 'refresh_all'},
                                   content_type='application/json')

        self.assertIn(response.status_code, [500, 503])
        data = json.loads(response.data)
        self.assertFalse(data['success'])


class TestKnowledgeBaseConversationIntegration(unittest.TestCase):
    """Test knowledge base conversation workflow with role integration"""

    def setUp(self):
        """Set up test environment"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()

        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['TESTING'] = True

        db.create_all()
        self.client = self.app.test_client()

        # Create test role
        self.teacher_role = Role(
            name='Math Teacher',
            prompt='Mathematics teacher specializing in calculus. Use clear examples and step-by-step explanations. Keep explanations concise and focused on key concepts. As a math teacher, explain: {topic}'
        )
        db.session.add(self.teacher_role)
        db.session.commit()

        # Create test knowledge base
        self.knowledge_base = KnowledgeBase(
            ragflow_dataset_id='conversation-math-001',
            name='微积分教程',
            description='高等数学微积分教程知识库',
            document_count=100,
            total_size=2097152,
            status='active'
        )
        db.session.add(self.knowledge_base)
        db.session.commit()

        # Assign knowledge base to role
        self.role_kb = RoleKnowledgeBase(
            role_id=self.teacher_role.id,
            knowledge_base_id=self.knowledge_base.id,
            priority=1,
            retrieval_config='{"max_results": 5, "similarity_threshold": 0.8}',
            is_active=True
        )
        db.session.add(self.role_kb)
        db.session.commit()

    def tearDown(self):
        """Clean up test environment"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    @patch('app.services.ragflow_service.get_ragflow_service')
    def test_complete_conversation_workflow(self, mock_ragflow):
        """Test complete conversation workflow from question to answer"""
        # Mock RAGFlow service
        mock_ragflow_instance = Mock()
        mock_ragflow.return_value = mock_ragflow_instance

        # Mock chat response
        mock_chat_response = Mock()
        mock_chat_response.response = '导数是微积分中的核心概念，表示函数在某一点的瞬时变化率。对于函数f(x)，其在点x处的导数定义为f\'(x) = lim(h→0) [f(x+h) - f(x)]/h。'
        mock_chat_response.confidence_score = 0.92
        mock_chat_response.references = [
            {
                'document_id': 'calc-chapter-3',
                'document_title': '导数与微分',
                'snippet': '导数的定义与几何意义',
                'page_number': 45,
                'confidence': 0.95
            },
            {
                'document_id': 'calc-examples-2',
                'document_title': '导数计算例题',
                'snippet': '常见函数的导数计算方法',
                'page_number': 67,
                'confidence': 0.88
            }
        ]
        mock_chat_response.metadata = {
            'model': 'ragflow-gpt-3.5',
            'tokens_used': 156,
            'response_time': 1.2
        }
        mock_ragflow_instance.chat_with_dataset.return_value = mock_chat_response

        # 1. Test API conversation endpoint
        response = self.client.post(f'/api/knowledge-bases/{self.knowledge_base.id}',
                                   json={
                                       'action': 'test_conversation',
                                       'question': '什么是导数？请用简单的方式解释一下。'
                                   },
                                   content_type='application/json')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['user_question'], '什么是导数？请用简单的方式解释一下。')
        self.assertIn('导数是微积分中的核心概念', data['data']['ragflow_response'])
        self.assertEqual(data['data']['confidence_score'], 0.92)
        self.assertEqual(data['data']['reference_count'], 2)
        self.assertTrue(data['data']['is_high_confidence'])

        # 2. Verify conversation was saved to database
        conversation = KnowledgeBaseConversation.query.filter_by(
            knowledge_base_id=self.knowledge_base.id
        ).first()

        self.assertIsNotNone(conversation)
        self.assertEqual(conversation.user_question, '什么是导数？请用简单的方式解释一下。')
        self.assertIn('导数是微积分中的核心概念', conversation.ragflow_response)
        self.assertEqual(conversation.confidence_score, 0.92)
        self.assertEqual(conversation.get_reference_count(), 2)
        self.assertTrue(conversation.is_high_confidence())

        # 3. Test conversation history API
        response = self.client.get(f'/api/knowledge-bases/{self.knowledge_base.id}/conversations')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']['conversations']), 1)

    @patch('app.services.ragflow_service.get_ragflow_service')
    def test_conversation_with_low_confidence_response(self, mock_ragflow):
        """Test conversation workflow with low confidence RAGFlow response"""
        # Mock RAGFlow service with low confidence response
        mock_ragflow_instance = Mock()
        mock_ragflow.return_value = mock_ragflow_instance

        mock_chat_response = Mock()
        mock_chat_response.response = '抱歉，我在知识库中没有找到关于这个问题的相关信息。'
        mock_chat_response.confidence_score = 0.35  # Low confidence
        mock_chat_response.references = []
        mock_chat_response.metadata = {
            'model': 'ragflow-gpt-3.5',
            'tokens_used': 45,
            'response_time': 0.8
        }
        mock_ragflow_instance.chat_with_dataset.return_value = mock_chat_response

        # Test conversation with low confidence
        response = self.client.post(f'/api/knowledge-bases/{self.knowledge_base.id}',
                                   json={
                                       'action': 'test_conversation',
                                       'question': '请问量子纠缠在日常生活中有什么应用？'
                                   },
                                   content_type='application/json')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['confidence_score'], 0.35)
        self.assertFalse(data['data']['is_high_confidence'])
        self.assertEqual(data['data']['reference_count'], 0)

        # Verify low confidence was properly saved
        conversation = KnowledgeBaseConversation.query.first()
        self.assertFalse(conversation.is_high_confidence())
        self.assertEqual(conversation.get_reference_count(), 0)

    @patch('app.services.ragflow_service.get_ragflow_service')
    def test_conversation_with_ragflow_api_error(self, mock_ragflow):
        """Test conversation workflow with RAGFlow API error"""
        # Mock RAGFlow service error
        mock_ragflow_instance = Mock()
        mock_ragflow.return_value = mock_ragflow_instance
        mock_ragflow_instance.chat_with_dataset.side_effect = RAGFlowAPIError("Service temporarily unavailable")

        # Test conversation with API error
        response = self.client.post(f'/api/knowledge-bases/{self.knowledge_base.id}',
                                   json={
                                       'action': 'test_conversation',
                                       'question': '请解释一下牛顿第二定律'
                                   },
                                   content_type='application/json')

        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('RAGFLOW_API_ERROR', data.get('error_code', ''))

        # Verify no conversation was saved due to error
        conversation = KnowledgeBaseConversation.query.filter_by(
            knowledge_base_id=self.knowledge_base.id
        ).first()
        self.assertIsNone(conversation)

    def test_conversation_validation_scenarios(self):
        """Test conversation input validation scenarios"""
        # Test with empty question
        response = self.client.post(f'/api/knowledge-bases/{self.knowledge_base.id}',
                                   json={
                                       'action': 'test_conversation',
                                       'question': '   '  # Whitespace only
                                   },
                                   content_type='application/json')

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('测试问题不能为空', data.get('message', ''))

        # Test with missing question field
        response = self.client.post(f'/api/knowledge-bases/{self.knowledge_base.id}',
                                   json={
                                       'action': 'test_conversation'
                                   },
                                   content_type='application/json')

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])

        # Test with non-existent knowledge base
        response = self.client.post('/api/knowledge-bases/99999',
                                   json={
                                       'action': 'test_conversation',
                                       'question': 'Test question'
                                   },
                                   content_type='application/json')

        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertFalse(data['success'])


class TestKnowledgeBaseRoleIntegration(unittest.TestCase):
    """Test knowledge base and role integration scenarios"""

    def setUp(self):
        """Set up test environment"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()

        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['TESTING'] = True

        db.create_all()
        self.client = self.app.test_client()

        # Create multiple test roles
        self.math_teacher = Role(
            name='Math Teacher',
            prompt='Mathematics teacher. Math teacher template.'
        )

        self.physics_teacher = Role(
            name='Physics Teacher',
            prompt='Physics teacher. Physics teacher template.'
        )

        self.student = Role(
            name='Student',
            prompt='Curious student. Student template.'
        )

        db.session.add_all([self.math_teacher, self.physics_teacher, self.student])
        db.session.commit()

        # Create multiple knowledge bases
        self.math_kb = KnowledgeBase(
            ragflow_dataset_id='role-integration-math',
            name='数学知识库',
            description='数学相关教程和例题',
            document_count=80,
            total_size=1572864,
            status='active'
        )

        self.physics_kb = KnowledgeBase(
            ragflow_dataset_id='role-integration-physics',
            name='物理知识库',
            description='物理理论和实验',
            document_count=60,
            total_size=1048576,
            status='active'
        )

        self.general_kb = KnowledgeBase(
            ragflow_dataset_id='role-integration-general',
            name='综合知识库',
            description='各学科基础知识',
            document_count=200,
            total_size=3145728,
            status='active'
        )

        db.session.add_all([self.math_kb, self.physics_kb, self.general_kb])
        db.session.commit()

    def tearDown(self):
        """Clean up test environment"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_multiple_role_knowledge_base_assignments(self):
        """Test assigning multiple knowledge bases to roles"""
        # Assign knowledge bases to roles
        assignments = [
            (self.math_teacher.id, self.math_kb.id, 1, {"max_results": 5}),
            (self.math_teacher.id, self.general_kb.id, 2, {"max_results": 3}),
            (self.physics_teacher.id, self.physics_kb.id, 1, {"max_results": 5}),
            (self.physics_teacher.id, self.general_kb.id, 2, {"max_results": 3}),
            (self.student.id, self.general_kb.id, 1, {"max_results": 3})
        ]

        for role_id, kb_id, priority, config in assignments:
            role_kb = KnowledgeBaseService.assign_knowledge_base_to_role(
                role_id=role_id,
                knowledge_base_id=kb_id,
                priority=priority,
                retrieval_config=config,
                is_active=True
            )
            self.assertIsNotNone(role_kb)

        # Verify assignments
        math_teacher_kbs = KnowledgeBaseService.get_role_knowledge_bases(self.math_teacher.id)
        self.assertEqual(len(math_teacher_kbs), 2)
        self.assertEqual(math_teacher_kbs[0]['priority'], 1)  # math_kb
        self.assertEqual(math_teacher_kbs[1]['priority'], 2)  # general_kb

        physics_teacher_kbs = KnowledgeBaseService.get_role_knowledge_bases(self.physics_teacher.id)
        self.assertEqual(len(physics_teacher_kbs), 2)

        student_kbs = KnowledgeBaseService.get_role_knowledge_bases(self.student.id)
        self.assertEqual(len(student_kbs), 1)
        self.assertEqual(student_kbs[0]['knowledge_base_name'], '综合知识库')

    @patch('app.services.ragflow_service.get_ragflow_service')
    def test_role_specific_conversation_workflow(self, mock_ragflow):
        """Test conversation workflow specific to role-knowledge base assignments"""
        # Assign math knowledge base to math teacher
        KnowledgeBaseService.assign_knowledge_base_to_role(
            role_id=self.math_teacher.id,
            knowledge_base_id=self.math_kb.id,
            priority=1
        )

        # Mock RAGFlow service
        mock_ragflow_instance = Mock()
        mock_ragflow.return_value = mock_ragflow_instance

        mock_chat_response = Mock()
        mock_chat_response.response = '二次函数的一般形式是f(x) = ax² + bx + c，其中a≠0。其图像是抛物线，具有顶点、对称轴等重要特征。'
        mock_chat_response.confidence_score = 0.95
        mock_chat_response.references = [{'document_id': 'math-quad-001', 'document_title': '二次函数'}]
        mock_ragflow_instance.chat_with_dataset.return_value = mock_chat_response

        # Test conversation through math teacher's assigned knowledge base
        response = self.client.post(f'/api/knowledge-bases/{self.math_kb.id}',
                                   json={
                                       'action': 'test_conversation',
                                       'question': '请解释二次函数的特点'
                                   },
                                   content_type='application/json')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('二次函数的一般形式', data['data']['ragflow_response'])

    def test_knowledge_base_unassignment_workflow(self):
        """Test knowledge base unassignment from roles"""
        # Initial assignment
        role_kb = KnowledgeBaseService.assign_knowledge_base_to_role(
            role_id=self.math_teacher.id,
            knowledge_base_id=self.math_kb.id
        )

        # Verify assignment
        kbs = KnowledgeBaseService.get_role_knowledge_bases(self.math_teacher.id)
        self.assertEqual(len(kbs), 1)

        # Unassign knowledge base
        result = KnowledgeBaseService.unassign_knowledge_base_from_role(
            role_id=self.math_teacher.id,
            knowledge_base_id=self.math_kb.id
        )
        self.assertTrue(result)

        # Verify unassignment
        kbs = KnowledgeBaseService.get_role_knowledge_bases(self.math_teacher.id)
        self.assertEqual(len(kbs), 0)

        # Verify role_kb was deleted
        deleted_role_kb = RoleKnowledgeBase.query.get(role_kb.id)
        self.assertIsNone(deleted_role_kb)


class TestKnowledgeBasePerformanceIntegration(unittest.TestCase):
    """Test performance requirements and configuration validation"""

    def setUp(self):
        """Set up test environment"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()

        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['TESTING'] = True

        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        """Clean up test environment"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    @patch('app.services.knowledge_base_service.get_ragflow_service')
    @patch('app.services.knowledge_base_service.get_cache_service')
    def test_performance_sync_large_datasets(self, mock_cache, mock_ragflow):
        """Test performance with large dataset synchronization"""
        # Mock cache service
        mock_cache_instance = Mock()
        mock_cache.return_value = mock_cache_instance
        mock_cache_instance.get.return_value = None

        # Mock RAGFlow service with many datasets (performance test)
        mock_ragflow_instance = Mock()
        mock_ragflow.return_value = mock_ragflow_instance

        # Create 100 datasets to test performance
        large_dataset_list = []
        for i in range(100):
            large_dataset_list.append(
                DatasetInfo(
                    id=f'perf-dataset-{i:03d}',
                    name=f'性能测试数据集 {i}',
                    description=f'第{i}个性能测试数据集',
                    document_count=50 + i,
                    size=1048576 * (1 + i // 10),  # Increasing sizes
                    status='active' if i % 10 != 0 else 'inactive'
                )
            )

        mock_ragflow_instance.get_datasets.return_value = large_dataset_list

        # Measure sync performance
        start_time = time.time()

        response = self.client.post('/api/knowledge-bases',
                                   json={'action': 'refresh_all'},
                                   content_type='application/json')

        end_time = time.time()
        sync_duration = end_time - start_time

        # Verify successful sync
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['created'], 100)

        # Performance requirement: sync should complete within 10 seconds
        self.assertLess(sync_duration, 10.0, f"Large dataset sync took {sync_duration:.2f}s, should be < 10s")

        # Verify all knowledge bases were created
        created_kbs = KnowledgeBase.query.all()
        self.assertEqual(len(created_kbs), 100)

    @patch('app.services.ragflow_service.get_ragflow_service')
    def test_performance_conversation_response_time(self, mock_ragflow):
        """Test conversation response time performance"""
        # Create test knowledge base
        kb = KnowledgeBase(
            ragflow_dataset_id='perf-conv-001',
            name='性能测试知识库',
            description='测试响应时间性能',
            document_count=1000,
            total_size=10485760,  # 10MB
            status='active'
        )
        db.session.add(kb)
        db.session.commit()

        # Mock RAGFlow service
        mock_ragflow_instance = Mock()
        mock_ragflow.return_value = mock_ragflow_instance

        # Mock response with realistic delay
        def mock_chat_with_delay(*args, **kwargs):
            time.sleep(0.5)  # Simulate 500ms RAGFlow processing time
            response = Mock()
            response.response = '这是一个性能测试的回答内容。'
            response.confidence_score = 0.88
            response.references = [{'document_id': 'perf-doc-001', 'document_title': '性能测试文档'}]
            return response

        mock_ragflow_instance.chat_with_dataset.side_effect = mock_chat_with_delay

        # Measure conversation performance
        start_time = time.time()

        response = self.client.post(f'/api/knowledge-bases/{kb.id}',
                                   json={
                                       'action': 'test_conversation',
                                       'question': '性能测试问题'
                                   },
                                   content_type='application/json')

        end_time = time.time()
        total_response_time = end_time - start_time

        # Verify successful response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])

        # Performance requirement: total response time should be under 5 seconds
        self.assertLess(total_response_time, 5.0,
                       f"Conversation took {total_response_time:.2f}s, should be < 5s")

    def test_pagination_performance(self):
        """Test pagination performance with large datasets"""
        # Create many knowledge bases for pagination test
        knowledge_bases = []
        for i in range(200):
            knowledge_bases.append(
                KnowledgeBase(
                    ragflow_dataset_id=f'paginated-dataset-{i:03d}',
                    name=f'分页测试知识库 {i}',
                    description=f'第{i}个分页测试知识库',
                    document_count=10 + i,
                    total_size=1024 * (1 + i),
                    status='active' if i % 5 != 0 else 'inactive'
                )
            )

        db.session.add_all(knowledge_bases)
        db.session.commit()

        # Test pagination performance
        start_time = time.time()

        response = self.client.get('/api/knowledge-bases?page=5&page_size=20')

        end_time = time.time()
        query_time = end_time - start_time

        # Verify successful pagination
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['total'], 200)
        self.assertEqual(data['data']['page'], 5)
        self.assertEqual(len(data['data']['knowledge_bases']), 20)

        # Performance requirement: pagination query should be under 1 second
        self.assertLess(query_time, 1.0, f"Pagination query took {query_time:.2f}s, should be < 1s")


class TestKnowledgeBaseConfigurationValidation(unittest.TestCase):
    """Test configuration validation and edge cases"""

    def setUp(self):
        """Set up test environment"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()

        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['TESTING'] = True

        db.create_all()
        self.client = self.app.test_client()

        # Create test role
        self.test_role = Role(
            name='Config Test Role',
            prompt='Role for configuration testing. Test template.'
        )
        db.session.add(self.test_role)
        db.session.commit()

    def tearDown(self):
        """Clean up test environment"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_knowledge_base_creation_validation(self):
        """Test knowledge base creation with various validation scenarios"""
        service = get_knowledge_base_service()

        # Test valid creation
        kb = service.create_knowledge_base(
            ragflow_dataset_id='validation-test-001',
            name='Valid Knowledge Base',
            description='Valid description',
            document_count=100,
            total_size=1048576,
            status='active'
        )
        self.assertIsNotNone(kb)

        # Test invalid dataset ID (empty)
        with self.assertRaises(KnowledgeBaseValidationError):
            service.create_knowledge_base(
                ragflow_dataset_id='',
                name='Invalid KB'
            )

        # Test invalid name (empty)
        with self.assertRaises(KnowledgeBaseValidationError):
            service.create_knowledge_base(
                ragflow_dataset_id='invalid-name-001',
                name=''
            )

        # Test invalid status
        with self.assertRaises(KnowledgeBaseValidationError):
            service.create_knowledge_base(
                ragflow_dataset_id='invalid-status-001',
                name='Invalid Status KB',
                status='invalid_status_value'
            )

        # Test duplicate dataset ID
        with self.assertRaises(KnowledgeBaseValidationError):
            service.create_knowledge_base(
                ragflow_dataset_id='validation-test-001',  # Same as first
                name='Duplicate KB'
            )

    def test_role_knowledge_base_assignment_validation(self):
        """Test role-knowledge base assignment validation"""
        # Create valid knowledge base
        kb = KnowledgeBaseService.create_knowledge_base(
            ragflow_dataset_id='assignment-validation-001',
            name='Assignment Validation KB'
        )

        # Test valid assignment
        role_kb = KnowledgeBaseService.assign_knowledge_base_to_role(
            role_id=self.test_role.id,
            knowledge_base_id=kb.id,
            priority=1,
            retrieval_config={'max_results': 5, 'similarity_threshold': 0.8},
            is_active=True
        )
        self.assertIsNotNone(role_kb)

        # Test invalid role ID
        with self.assertRaises(KnowledgeBaseValidationError):
            KnowledgeBaseService.assign_knowledge_base_to_role(
                role_id=99999,  # Non-existent role
                knowledge_base_id=kb.id
            )

        # Test invalid knowledge base ID
        with self.assertRaises(KnowledgeBaseValidationError):
            KnowledgeBaseService.assign_knowledge_base_to_role(
                role_id=self.test_role.id,
                knowledge_base_id=99999  # Non-existent knowledge base
            )

        # Test duplicate assignment
        with self.assertRaises(Exception):  # Should raise IntegrityError
            KnowledgeBaseService.assign_knowledge_base_to_role(
                role_id=self.test_role.id,
                knowledge_base_id=kb.id  # Same assignment
            )

    @patch.dict(os.environ, {
        'RAGFLOW_API_BASE_URL': 'https://invalid-url-that-does-not-exist.com',
        'RAGFLOW_API_KEY': 'invalid-key'
    })
    def test_ragflow_service_configuration_validation(self):
        """Test RAGFlow service configuration validation"""
        # Test configuration loading
        config = RAGFlowConfig(
            api_base_url='https://test.ragflow.com',
            api_key='test-key'
        )
        self.assertEqual(config.api_base_url, 'https://test.ragflow.com')
        self.assertEqual(config.api_key, 'test-key')

        # Test URL normalization
        config_with_slash = RAGFlowConfig(
            api_base_url='https://test.ragflow.com/',
            api_key='test-key'
        )
        self.assertEqual(config_with_slash.api_base_url, 'https://test.ragflow.com')

        # Test invalid configuration (empty URL)
        with self.assertRaises(ValueError):
            RAGFlowConfig(
                api_base_url='',
                api_key='test-key'
            )

        # Test invalid configuration (empty API key)
        with self.assertRaises(ValueError):
            RAGFlowConfig(
                api_base_url='https://test.com',
                api_key=''
            )

    def test_knowledge_base_statistics_accuracy(self):
        """Test knowledge base statistics calculation accuracy"""
        service = get_knowledge_base_service()

        # Create knowledge bases with different statuses and sizes
        kbs = [
            KnowledgeBaseService.create_knowledge_base(
                ragflow_dataset_id=f'stats-test-{i}',
                name=f'Stats Test KB {i}',
                document_count=10 * (i + 1),
                total_size=1024 * (i + 1),
                status='active' if i % 2 == 0 else 'inactive'
            )
            for i in range(5)
        ]

        # Assign some knowledge bases to roles
        for i, kb in enumerate(kbs[:3]):
            KnowledgeBaseService.assign_knowledge_base_to_role(
                role_id=self.test_role.id,
                knowledge_base_id=kb.id,
                priority=i + 1
            )

        # Get and verify statistics
        stats = service.get_knowledge_base_statistics()

        self.assertEqual(stats['knowledge_bases']['total'], 5)
        self.assertEqual(stats['knowledge_bases']['active'], 3)  # indices 0, 2, 4
        self.assertEqual(stats['knowledge_bases']['inactive'], 2)  # indices 1, 3

        expected_total_docs = sum(10 * (i + 1) for i in range(5))
        self.assertEqual(stats['documents']['total'], expected_total_docs)

        expected_total_size = sum(1024 * (i + 1) for i in range(5))
        self.assertEqual(stats['documents']['total_size'], expected_total_size)

        self.assertEqual(stats['associations']['total'], 3)


class TestKnowledgeBaseErrorRecovery(unittest.TestCase):
    """Test error scenarios and recovery mechanisms"""

    def setUp(self):
        """Set up test environment"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()

        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['TESTING'] = True

        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        """Clean up test environment"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    @patch('app.services.knowledge_base_service.get_ragflow_service')
    def test_ragflow_service_interruption_recovery(self, mock_ragflow):
        """Test recovery from RAGFlow service interruptions"""
        # Mock RAGFlow service that fails initially then succeeds
        mock_ragflow_instance = Mock()
        mock_ragflow.return_value = mock_ragflow_instance

        # First call fails, second call succeeds
        call_count = 0
        def mock_get_datasets():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RAGFlowConnectionError("Connection timeout")
            else:
                return [
                    DatasetInfo(
                        id='recovery-test-001',
                        name='恢复测试知识库',
                        description='测试中断恢复场景',
                        document_count=50,
                        size=1048576,
                        status='active'
                    )
                ]

        mock_ragflow_instance.get_datasets.side_effect = mock_get_datasets

        # First sync attempt should fail
        response = self.client.post('/api/knowledge-bases',
                                   json={'action': 'refresh_all'},
                                   content_type='application/json')

        self.assertIn(response.status_code, [500, 503])
        data = json.loads(response.data)
        self.assertFalse(data['success'])

        # Second sync attempt should succeed
        response = self.client.post('/api/knowledge-bases',
                                   json={'action': 'refresh_all'},
                                   content_type='application/json')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['created'], 1)

    @patch('app.services.knowledge_base_service.get_ragflow_service')
    def test_partial_sync_recovery_mechanism(self, mock_ragflow):
        """Test recovery from partial sync failures"""
        # Create initial knowledge base
        kb = KnowledgeBaseService.create_knowledge_base(
            ragflow_dataset_id='partial-sync-recovery-001',
            name='部分同步恢复测试',
            document_count=100,
            total_size=2097152,
            status='active'
        )

        # Mock RAGFlow service with updated information
        mock_ragflow_instance = Mock()
        mock_ragflow.return_value = mock_ragflow_instance

        mock_datasets = [
            DatasetInfo(
                id='partial-sync-recovery-001',  # Same ID
                name='更新后的部分同步恢复测试',  # Updated name
                description='更新后的描述',
                document_count=150,  # Updated count
                size=3145728,  # Updated size
                status='active'
            ),
            DatasetInfo(
                id='partial-sync-recovery-002',
                name='新增的知识库',
                description='部分同步时新增',
                document_count=75,
                size=1572864,
                status='active'
            )
        ]
        mock_ragflow_instance.get_datasets.return_value = mock_datasets

        # Perform sync that should update existing and create new
        response = self.client.post('/api/knowledge-bases',
                                   json={'action': 'refresh_all'},
                                   content_type='application/json')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['updated'], 1)
        self.assertEqual(data['data']['created'], 1)

        # Verify updates were applied
        updated_kb = KnowledgeBase.query.filter_by(
            ragflow_dataset_id='partial-sync-recovery-001'
        ).first()
        self.assertEqual(updated_kb.name, '更新后的部分同步恢复测试')
        self.assertEqual(updated_kb.document_count, 150)
        self.assertEqual(updated_kb.total_size, 3145728)

        # Verify new knowledge base was created
        new_kb = KnowledgeBase.query.filter_by(
            ragflow_dataset_id='partial-sync-recovery-002'
        ).first()
        self.assertIsNotNone(new_kb)
        self.assertEqual(new_kb.name, '新增的知识库')

    def test_database_transaction_rollback_on_errors(self):
        """Test database transaction rollback on sync errors"""
        initial_count = KnowledgeBase.query.count()

        # Test creation with invalid data that should trigger rollback
        try:
            # This should fail validation and trigger rollback
            KnowledgeBaseService.create_knowledge_base(
                ragflow_dataset_id='',  # Invalid: empty
                name='Should rollback'
            )
        except KnowledgeBaseValidationError:
            pass  # Expected

        # Verify no partial data was committed
        final_count = KnowledgeBase.query.count()
        self.assertEqual(initial_count, final_count)

        # Test another rollback scenario
        try:
            # Start a transaction that should fail
            kb1 = KnowledgeBaseService.create_knowledge_base(
                ragflow_dataset_id='rollback-test-1',
                name='First KB'
            )

            # This should fail and rollback the entire transaction
            KnowledgeBaseService.create_knowledge_base(
                ragflow_dataset_id='rollback-test-1',  # Duplicate
                name='Second KB'
            )
        except (KnowledgeBaseValidationError, Exception):
            pass  # Expected

        # Verify rollback worked correctly
        rollback_kb = KnowledgeBase.query.filter_by(
            ragflow_dataset_id='rollback-test-1'
        ).first()
        self.assertIsNone(rollback_kb)

    @patch('app.services.ragflow_service.get_ragflow_service')
    def test_conversation_error_isolation(self, mock_ragflow):
        """Test that conversation errors don't affect other operations"""
        # Create test knowledge base
        kb = KnowledgeBaseService.create_knowledge_base(
            ragflow_dataset_id='error-isolation-001',
            name='错误隔离测试'
        )

        # Mock RAGFlow service that fails for conversation
        mock_ragflow_instance = Mock()
        mock_ragflow.return_value = mock_ragflow_instance
        mock_ragflow_instance.chat_with_dataset.side_effect = RAGFlowAPIError("Service error")

        # Attempt conversation that should fail
        response = self.client.post(f'/api/knowledge-bases/{kb.id}',
                                   json={
                                       'action': 'test_conversation',
                                       'question': 'Test question'
                                   },
                                   content_type='application/json')

        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertFalse(data['success'])

        # Verify knowledge base is still accessible and functional
        response = self.client.get('/api/knowledge-bases')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['total'], 1)

        # Verify statistics are still working
        response = self.client.get('/api/knowledge-bases/statistics')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])


if __name__ == '__main__':
    # Run all integration tests
    unittest.main(verbosity=2)