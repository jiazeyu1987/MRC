from datetime import datetime
from app import db
import uuid

class DocumentChunk(db.Model):
    __tablename__ = 'document_chunks'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = db.Column(db.String(36), db.ForeignKey('documents.id'), nullable=False)
    ragflow_chunk_id = db.Column(db.String(255), nullable=True)  # RAGFlow chunk ID
    chunk_index = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    content_preview = db.Column(db.String(500), nullable=True)  # Preview for list views
    word_count = db.Column(db.Integer, default=0)
    character_count = db.Column(db.Integer, default=0)

    # Metadata from RAGFlow
    ragflow_metadata = db.Column(db.JSON, nullable=True)  # RAGFlow chunk metadata
    embedding_vector_id = db.Column(db.String(255), nullable=True)  # RAGFlow embedding reference
    position_start = db.Column(db.Integer, nullable=True)  # Position in document
    position_end = db.Column(db.Integer, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    references = db.relationship('ChunkReference', backref='chunk', cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        super(DocumentChunk, self).__init__(**kwargs)
        self.calculate_stats()
        self.generate_preview()

    def to_dict(self):
        """Convert chunk to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'document_id': self.document_id,
            'ragflow_chunk_id': self.ragflow_chunk_id,
            'chunk_index': self.chunk_index,
            'content': self.content,
            'content_preview': self.content_preview,
            'word_count': self.word_count,
            'character_count': self.character_count,
            'ragflow_metadata': self.ragflow_metadata,
            'embedding_vector_id': self.embedding_vector_id,
            'position_start': self.position_start,
            'position_end': self.position_end,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def calculate_stats(self):
        """Calculate word and character count from content"""
        if self.content:
            self.character_count = len(self.content)
            # Count words (simplified - split by whitespace)
            self.word_count = len(self.content.split())

    def generate_preview(self):
        """Generate a preview of the content for list views"""
        if self.content:
            # Remove extra whitespace and create a preview
            cleaned_content = ' '.join(self.content.split())
            if len(cleaned_content) > 450:  # Leave room for ellipsis
                self.content_preview = cleaned_content[:450] + "..."
            else:
                self.content_preview = cleaned_content
        else:
            self.content_preview = ""

    def update_from_ragflow(self, ragflow_data):
        """Update chunk metadata from RAGFlow response"""
        if ragflow_data:
            self.ragflow_metadata = ragflow_data
            if 'chunk_id' in ragflow_data:
                self.ragflow_chunk_id = ragflow_data['chunk_id']
            if 'embedding_vector_id' in ragflow_data:
                self.embedding_vector_id = ragflow_data['embedding_vector_id']
            if 'position' in ragflow_data:
                position = ragflow_data['position']
                if isinstance(position, dict):
                    self.position_start = position.get('start')
                    self.position_end = position.get('end')
        self.updated_at = datetime.utcnow()
        db.session.commit()

    @classmethod
    def create_from_content(cls, document_id, content, chunk_index, ragflow_data=None):
        """Create a new chunk from content"""
        chunk = cls(
            document_id=document_id,
            content=content,
            chunk_index=chunk_index,
            ragflow_metadata=ragflow_data or {}
        )

        if ragflow_data:
            chunk.update_from_ragflow(ragflow_data)

        db.session.add(chunk)
        db.session.commit()
        return chunk

    def __repr__(self):
        return f'<DocumentChunk {self.id} (Index: {self.chunk_index}, Words: {self.word_count})>'