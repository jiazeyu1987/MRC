"""
Document Service - Manage document operations and RAGFlow integration.

This service provides document-level operations including retrieval, listing,
and management functionality for documents stored in RAGFlow datasets.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from app import db
from app.models.document import Document
from app.services.ragflow_service import RAGFlowService
from app.services.knowledge_base_service import KnowledgeBaseService

logger = logging.getLogger(__name__)


class DocumentService:
    def __init__(self):
        from app.services.ragflow_service import get_ragflow_service

        ragflow_service = get_ragflow_service()
        if not ragflow_service:
            from app.services.ragflow_service import RAGFlowConfigError
            raise RAGFlowConfigError("RAGFlow service not available")
        self.ragflow_service = ragflow_service

    def get_documents(self, knowledge_base_id: str, filters: Dict = None) -> List[Dict]:
        """
        Retrieve documents for a knowledge base from RAGFlow with optional filtering.

        Args:
            knowledge_base_id: ID of the knowledge base
            filters: Optional filters (search, status, file_type, sort_by, sort_order, page, limit)

        Returns:
            List of document dictionaries from RAGFlow
        """
        try:
            # Get knowledge base to find RAGFlow dataset ID
            from app.services.knowledge_base_service import get_knowledge_base_service
            kb_service = get_knowledge_base_service()
            knowledge_base = kb_service.get_knowledge_base_by_id(int(knowledge_base_id))
            if not knowledge_base or not knowledge_base.ragflow_dataset_id:
                logger.warning(f"Knowledge base {knowledge_base_id} not found or no RAGFlow dataset ID")
                return []

            # Prepare RAGFlow parameters
            ragflow_status = None
            ragflow_page = filters.get('page', 1) if filters else 1
            ragflow_size = filters.get('limit', 20) if filters else 20

            # Status filter (RAGFlow uses parsing_status)
            if filters and filters.get('status'):
                status_map = {
                    'uploaded': 'waiting',
                    'processing': 'parsing',
                    'completed': 'completed',
                    'failed': 'failed'
                }
                ragflow_status = status_map.get(filters['status'], filters['status'])

            # Get documents from RAGFlow with filters
            ragflow_documents = self.ragflow_service.get_dataset_documents(
                dataset_id=knowledge_base.ragflow_dataset_id,
                status=ragflow_status,
                page=ragflow_page,
                size=ragflow_size
            )

            # Defensive check - ensure we have a list of dictionaries
            if not isinstance(ragflow_documents, list):
                logger.warning(f"RAGFlow returned unexpected type: {type(ragflow_documents)}. Expected list.")
                ragflow_documents = []

            # Filter out any non-dict items
            ragflow_documents = [doc for doc in ragflow_documents if isinstance(doc, dict)]

            # Apply additional client-side filters if needed
            if filters:
                filtered_documents = ragflow_documents

                # Search filter (client-side since RAGFlow API might not support it)
                if filters.get('search'):
                    search_term = filters['search'].lower()
                    filtered_documents = [
                        doc for doc in filtered_documents
                        if search_term in doc.get('name', '').lower()
                    ]

                # File type filter
                if filters.get('file_type'):
                    filtered_documents = [
                        doc for doc in filtered_documents
                        if doc.get('suffix', '').lower() == filters['file_type'].lower()
                    ]

                ragflow_documents = filtered_documents

            # Transform RAGFlow documents to frontend-compatible format
            transformed_documents = []
            for doc in ragflow_documents:
                # Map RAGFlow status to frontend status
                run_status = doc.get('run', 'UNSTART')
                upload_status = 'uploaded'
                processing_status = 'pending'

                if run_status == 'DONE':
                    processing_status = 'completed'
                elif run_status == 'RUNNING':
                    processing_status = 'processing'
                elif run_status == 'FAIL':
                    processing_status = 'failed'

                transformed_doc = {
                    'id': doc.get('id', ''),
                    'knowledge_base_id': knowledge_base_id,
                    'ragflow_document_id': doc.get('id', ''),
                    'filename': doc.get('name', ''),
                    'original_filename': doc.get('name', ''),
                    'file_size': doc.get('size', 0),
                    'file_type': doc.get('suffix', '').lower(),
                    'mime_type': "application/" + doc.get('suffix', '').lower(),
                    'upload_status': upload_status,
                    'processing_status': processing_status,
                    'chunk_count': doc.get('chunk_count', 0),
                    'ragflow_metadata': doc,
                    'created_at': self._convert_timestamp(doc.get('create_time')),
                    'updated_at': self._convert_timestamp(doc.get('update_time')),
                }
                transformed_documents.append(transformed_doc)

            logger.info(f"Retrieved {len(transformed_documents)} documents from RAGFlow for knowledge base {knowledge_base_id}")
            return transformed_documents

        except Exception as e:
            logger.error(f"Error retrieving documents from RAGFlow for knowledge base {knowledge_base_id}: {e}")
            raise

    def get_document(self, document_id: str) -> Optional[Document]:
        """
        Get a single document by ID.

        Args:
            document_id: ID of the document

        Returns:
            Document object or None if not found
        """
        try:
            document = Document.query.get(document_id)
            if document:
                logger.debug(f"Found document {document_id}")
            else:
                logger.warning(f"Document {document_id} not found")
            return document
        except Exception as e:
            logger.error(f"Error retrieving document {document_id}: {e}")
            return None

    def _convert_timestamp(self, timestamp: Any) -> Optional[datetime]:
        """
        Convert RAGFlow timestamp to datetime object.

        Args:
            timestamp: RAGFlow timestamp (various formats possible)

        Returns:
            Datetime object or None
        """
        if not timestamp:
            return None

        try:
            if isinstance(timestamp, (int, float)):
                # Unix timestamp
                return datetime.fromtimestamp(timestamp)
            elif isinstance(timestamp, str):
                # Try to parse string timestamp
                # Handle common RAGFlow timestamp formats
                if timestamp.isdigit():
                    return datetime.fromtimestamp(int(timestamp))
                else:
                    # Try ISO format or other common formats
                    try:
                        return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    except ValueError:
                        # Fallback - try simple format
                        return datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
            elif isinstance(timestamp, datetime):
                return timestamp
        except Exception as e:
            logger.warning(f"Failed to convert timestamp {timestamp}: {e}")

        return None