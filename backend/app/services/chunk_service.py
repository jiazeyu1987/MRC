"""
Chunk Service - Manage document chunk retrieval and search operations.

This service provides specialized chunk-level operations including search, retrieval,
and management functionality for document chunks processed by RAGFlow.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy import and_, or_, desc, asc, func
from app import db
from app.models.document_chunk import DocumentChunk
from app.models.document import Document
from app.services.ragflow_service import RAGFlowService
from app.services.cache_service import CacheService
import logging

logger = logging.getLogger(__name__)

class ChunkService:
    def __init__(self):
        from app.services.ragflow_service import get_ragflow_service

        ragflow_service = get_ragflow_service()
        if not ragflow_service:
            from app.services.ragflow_service import RAGFlowConfigError
            raise RAGFlowConfigError("RAGFlow service not available")
        self.ragflow_service = ragflow_service
        self.cache_service = CacheService()

    def search_chunks(self, knowledge_base_id: str, query: str, filters: Dict = None) -> Dict[str, Any]:
        """
        Search for chunks in a knowledge base.

        Args:
            knowledge_base_id: ID of the knowledge base
            query: Search query string
            filters: Optional filters (document_id, min_relevance_score, max_results)

        Returns:
            Dictionary with search results and metadata
        """
        try:
            # Use RAGFlow for search if available
            search_results = self.ragflow_service.search_chunks_in_dataset(
                knowledge_base_id, query,
                top_k=filters.get('max_results', 10) if filters else 10
            )

            # Process and format results
            chunks = []
            for result in search_results:
                # Convert RAGFlow result to local chunk format
                chunk_data = self._convert_ragflow_chunk(result, knowledge_base_id)
                if chunk_data:
                    chunks.append(chunk_data)

            # Apply additional filtering if needed
            if filters:
                chunks = self._apply_local_filters(chunks, filters)

            # Cache search results
            cache_key = f"chunks:search:{knowledge_base_id}:{hash(query)}"
            self.cache_service.set(cache_key, chunks, timeout=300)  # 5 minutes

            search_time = len(search_results) * 0.1  # Estimate search time

            return {
                'chunks': chunks,
                'total_count': len(chunks),
                'query': query,
                'search_time': search_time,
                'filters_applied': filters or {}
            }

        except Exception as e:
            logger.error(f"Error searching chunks for knowledge base {knowledge_base_id}: {e}")
            return {
                'chunks': [],
                'total_count': 0,
                'query': query,
                'search_time': 0,
                'error': str(e)
            }

    def get_document_chunks(self, document_id: str, filters: Dict = None) -> List[Dict[str, Any]]:
        """
        Get all chunks for a specific document.

        Args:
            document_id: ID of the document
            filters: Optional filters (chunk_index range, sort order)

        Returns:
            List of chunk dictionaries
        """
        try:
            # Check cache first
            cache_key = f"chunks:document:{document_id}"
            cached_chunks = self.cache_service.get(cache_key)
            if cached_chunks:
                logger.debug(f"Retrieved {len(cached_chunks)} chunks from cache for document {document_id}")
                return cached_chunks

            # Query from database
            query = DocumentChunk.query.filter_by(document_id=document_id)

            # Apply filters
            if filters:
                # Chunk index range filter
                if 'chunk_index_min' in filters:
                    query = query.filter(DocumentChunk.chunk_index >= filters['chunk_index_min'])
                if 'chunk_index_max' in filters:
                    query = query.filter(DocumentChunk.chunk_index <= filters['chunk_index_max'])

                # Sorting
                sort_by = filters.get('sort_by', 'chunk_index')
                sort_order = filters.get('sort_order', 'asc')
                if hasattr(DocumentChunk, sort_by):
                    if sort_order == 'desc':
                        query = query.order_by(desc(getattr(DocumentChunk, sort_by)))
                    else:
                        query = query.order_by(asc(getattr(DocumentChunk, sort_by)))

            chunks = query.all()

            # Convert to dictionaries
            chunk_dicts = [chunk.to_dict() for chunk in chunks]

            # Cache results
            self.cache_service.set(cache_key, chunk_dicts, timeout=600)  # 10 minutes

            logger.info(f"Retrieved {len(chunk_dicts)} chunks for document {document_id}")
            return chunk_dicts

        except Exception as e:
            logger.error(f"Error getting chunks for document {document_id}: {e}")
            return []

    def get_chunk_details(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific chunk.

        Args:
            chunk_id: ID of the chunk

        Returns:
            Chunk details dictionary or None if not found
        """
        try:
            chunk = DocumentChunk.query.get(chunk_id)
            if not chunk:
                logger.warning(f"Chunk {chunk_id} not found")
                return None

            # Get additional details from RAGFlow if available
            ragflow_details = None
            if chunk.ragflow_chunk_id and chunk.document:
                try:
                    # Get dataset_id from the document's knowledge base
                    dataset_id = None
                    if chunk.document.knowledge_base:
                        dataset_id = chunk.document.knowledge_base.ragflow_dataset_id

                    ragflow_chunks = self.ragflow_service.get_document_chunks(
                        chunk.document.ragflow_document_id,
                        dataset_id
                    )
                    # Find matching chunk by ID
                    ragflow_details = next(
                        (rc for rc in ragflow_chunks if rc.get('id') == chunk.ragflow_chunk_id),
                        None
                    )
                except Exception as e:
                    logger.warning(f"Failed to get RAGFlow details for chunk {chunk_id}: {e}")

            chunk_details = chunk.to_dict()
            if ragflow_details:
                chunk_details['ragflow_details'] = ragflow_details

            logger.debug(f"Retrieved details for chunk {chunk_id}")
            return chunk_details

        except Exception as e:
            logger.error(f"Error getting chunk details for {chunk_id}: {e}")
            return None

    def update_chunk_metadata(self, chunk_id: str, metadata: Dict[str, Any]) -> bool:
        """
        Update metadata for a chunk.

        Args:
            chunk_id: ID of the chunk
            metadata: Metadata to update

        Returns:
            True if successful, False otherwise
        """
        try:
            chunk = DocumentChunk.query.get(chunk_id)
            if not chunk:
                logger.warning(f"Chunk {chunk_id} not found for metadata update")
                return False

            # Update RAGFlow metadata
            if chunk.ragflow_metadata:
                chunk.ragflow_metadata.update(metadata)
            else:
                chunk.ragflow_metadata = metadata

            db.session.commit()

            # Clear cache for this document
            cache_key = f"chunks:document:{chunk.document_id}"
            self.cache_service.delete(cache_key)

            logger.info(f"Updated metadata for chunk {chunk_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating metadata for chunk {chunk_id}: {e}")
            db.session.rollback()
            return False

    def exclude_chunk_from_retrieval(self, chunk_id: str) -> bool:
        """
        Exclude a chunk from future retrieval operations.

        Args:
            chunk_id: ID of the chunk to exclude

        Returns:
            True if successful, False otherwise
        """
        try:
            return self.update_chunk_metadata(chunk_id, {
                'excluded_from_retrieval': True,
                'exclusion_reason': 'Manually excluded by user',
                'excluded_at': db.func.now().isoformat()
            })

        except Exception as e:
            logger.error(f"Error excluding chunk {chunk_id} from retrieval: {e}")
            return False

    def include_chunk_in_retrieval(self, chunk_id: str) -> bool:
        """
        Re-include a previously excluded chunk in retrieval operations.

        Args:
            chunk_id: ID of the chunk to include

        Returns:
            True if successful, False otherwise
        """
        try:
            return self.update_chunk_metadata(chunk_id, {
                'excluded_from_retrieval': False,
                'inclusion_reason': 'Manually re-included by user',
                'included_at': db.func.now().isoformat()
            })

        except Exception as e:
            logger.error(f"Error including chunk {chunk_id} in retrieval: {e}")
            return False

    def get_chunk_statistics(self, knowledge_base_id: str) -> Dict[str, Any]:
        """
        Get statistics for chunks in a knowledge base.

        Args:
            knowledge_base_id: ID of the knowledge base

        Returns:
            Dictionary with chunk statistics
        """
        try:
            # Use cache first
            cache_key = f"chunks:statistics:{knowledge_base_id}"
            cached_stats = self.cache_service.get(cache_key)
            if cached_stats:
                return cached_stats

            # Query database for statistics
            total_chunks = db.session.query(
                func.count(DocumentChunk.id)
            ).join(Document).filter(Document.knowledge_base_id == knowledge_base_id).scalar() or 0

            # Word count statistics
            total_words = db.session.query(
                func.sum(DocumentChunk.word_count)
            ).join(Document).filter(Document.knowledge_base_id == knowledge_base_id).scalar() or 0

            # Character count statistics
            total_chars = db.session.query(
                func.sum(DocumentChunk.character_count)
            ).join(Document).filter(Document.knowledge_base_id == knowledge_base_id).scalar() or 0

            # Average chunk length
            avg_chunk_length = total_chars / total_chunks if total_chunks > 0 else 0

            # Chunk count by document
            doc_chunk_counts = db.session.query(
                Document.id,
                Document.original_filename,
                func.count(DocumentChunk.id).label('chunk_count'),
                func.sum(DocumentChunk.word_count).label('total_words')
            ).join(DocumentChunk).filter(
                Document.knowledge_base_id == knowledge_base_id
            ).group_by(Document.id, Document.original_filename).all()

            statistics = {
                'total_chunks': total_chunks,
                'total_word_count': total_words,
                'total_character_count': total_chars,
                'average_chunk_length': round(avg_chunk_length, 2),
                'documents_with_chunks': len(doc_chunk_counts),
                'document_breakdown': [
                    {
                        'document_id': doc[0],
                        'filename': doc[1],
                        'chunk_count': doc[2],
                        'total_words': doc[3]
                    }
                    for doc in doc_chunk_counts
                ],
                'updated_at': db.func.now().isoformat()
            }

            # Cache for 5 minutes
            self.cache_service.set(cache_key, statistics, timeout=300)

            return statistics

        except Exception as e:
            logger.error(f"Error getting chunk statistics for knowledge base {knowledge_base_id}: {e}")
            return {}

    def _convert_ragflow_chunk(self, ragflow_chunk: Dict[str, Any], knowledge_base_id: str) -> Optional[Dict[str, Any]]:
        """Convert RAGFlow chunk result to local chunk format."""
        try:
            # Try to find existing local chunk
            ragflow_chunk_id = ragflow_chunk.get('id')
            if not ragflow_chunk_id:
                return None

            existing_chunk = DocumentChunk.query.filter_by(
                ragflow_chunk_id=ragflow_chunk_id
            ).first()

            if existing_chunk:
                # Update existing chunk with latest data
                existing_chunk.update_from_ragflow(ragflow_chunk)
                return existing_chunk.to_dict()
            else:
                # Create new local chunk record if we can identify the document
                content = ragflow_chunk.get('content', '')
                if not content:
                    return None

                # Try to find a document that might own this chunk
                # This is a simplified approach - in production, you'd want better matching logic
                doc_chunks = DocumentChunk.query.join(Document).filter(
                    Document.knowledge_base_id == knowledge_base_id
                ).all()

                if doc_chunks:
                    # Use the first document as owner (simplified approach)
                    sample_chunk = doc_chunks[0]
                    new_chunk = DocumentChunk.create_from_content(
                        document_id=sample_chunk.document_id,
                        content=content,
                        chunk_index=ragflow_chunk.get('chunk_index', 0),
                        ragflow_data=ragflow_chunk
                    )
                    return new_chunk.to_dict()

            return None

        except Exception as e:
            logger.warning(f"Error converting RAGFlow chunk: {e}")
            return None

    def _apply_local_filters(self, chunks: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply local filters to chunk results."""
        try:
            filtered_chunks = chunks

            # Filter by minimum relevance score
            if filters.get('min_relevance_score'):
                min_score = filters['min_relevance_score']
                filtered_chunks = [
                    chunk for chunk in filtered_chunks
                    if chunk.get('relevance_score', 0) >= min_score
                ]

            # Filter by document ID
            if filters.get('document_id'):
                doc_id = filters['document_id']
                filtered_chunks = [
                    chunk for chunk in filtered_chunks
                    if chunk.get('document_id') == doc_id
                ]

            return filtered_chunks

        except Exception as e:
            logger.warning(f"Error applying local filters: {e}")
            return chunks

    def cleanup_chunk_cache(self, document_id: str = None) -> int:
        """
        Clean up cached chunk data.

        Args:
            document_id: Optional document ID to limit cleanup to specific document

        Returns:
            Number of cache entries cleaned up
        """
        try:
            cleaned_count = 0

            if document_id:
                # Clean up specific document cache
                cache_key = f"chunks:document:{document_id}"
                if self.cache_service.delete(cache_key):
                    cleaned_count += 1
            else:
                # Clean up all chunk-related cache
                pattern = "chunks:*"
                cleaned_count = self.cache_service.delete_pattern(pattern)

            logger.info(f"Cleaned up {cleaned_count} chunk cache entries")
            return cleaned_count

        except Exception as e:
            logger.error(f"Error cleaning up chunk cache: {e}")
            return 0