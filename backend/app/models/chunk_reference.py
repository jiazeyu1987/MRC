from datetime import datetime
from app import db
import uuid

class ChunkReference(db.Model):
    __tablename__ = 'chunk_references'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    chunk_id = db.Column(db.String(36), db.ForeignKey('document_chunks.id'), nullable=False)
    conversation_id = db.Column(db.String(36), db.ForeignKey('sessions.id'), nullable=True)  # Optional reference to conversation
    message_id = db.Column(db.String(36), db.ForeignKey('messages.id'), nullable=True)  # Optional reference to message
    relevance_score = db.Column(db.Float, nullable=True)
    reference_count = db.Column(db.Integer, default=1)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Convert chunk reference to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'chunk_id': self.chunk_id,
            'conversation_id': self.conversation_id,
            'message_id': self.message_id,
            'relevance_score': self.relevance_score,
            'reference_count': self.reference_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def increment_reference(self):
        """Increment reference count"""
        self.reference_count += 1
        self.updated_at = datetime.utcnow()
        db.session.commit()

    def __repr__(self):
        return f'<ChunkReference {self.id} (Chunk: {self.chunk_id}, Count: {self.reference_count})>'