from datetime import datetime
from app import db
import uuid

class Document(db.Model):
    __tablename__ = 'documents'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    knowledge_base_id = db.Column(db.String(36), db.ForeignKey('knowledge_bases.id'), nullable=False)
    ragflow_document_id = db.Column(db.String(255), nullable=True)  # RAGFlow document ID
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    upload_status = db.Column(db.String(20), default='uploading')  # uploading, uploaded, failed
    processing_status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    chunk_count = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text, nullable=True)
    ragflow_metadata = db.Column(db.JSON, nullable=True)  # RAGFlow response metadata

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    uploaded_at = db.Column(db.DateTime, nullable=True)
    processed_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    knowledge_base = db.relationship('KnowledgeBase', backref='documents')
    chunks = db.relationship('DocumentChunk', backref='document', cascade='all, delete-orphan')
    processing_logs = db.relationship('ProcessingLog', backref='document', cascade='all, delete-orphan')

    def to_dict(self):
        """Convert document to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'knowledge_base_id': self.knowledge_base_id,
            'ragflow_document_id': self.ragflow_document_id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'mime_type': self.mime_type,
            'upload_status': self.upload_status,
            'processing_status': self.processing_status,
            'chunk_count': self.chunk_count,
            'error_message': self.error_message,
            'ragflow_metadata': self.ragflow_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }

    @property
    def file_size_mb(self):
        """Return file size in megabytes"""
        return round(self.file_size / (1024 * 1024), 2)

    def update_status(self, upload_status=None, processing_status=None, error_message=None):
        """Update document status and timestamp"""
        if upload_status:
            self.upload_status = upload_status
            if upload_status == 'uploaded':
                self.uploaded_at = datetime.utcnow()

        if processing_status:
            self.processing_status = processing_status
            if processing_status == 'completed':
                self.processed_at = datetime.utcnow()

        if error_message:
            self.error_message = error_message

        self.updated_at = datetime.utcnow()
        db.session.commit()

    def increment_chunk_count(self):
        """Increment chunk count by 1"""
        self.chunk_count += 1
        self.updated_at = datetime.utcnow()
        db.session.commit()

    def __repr__(self):
        return f'<Document {self.filename} ({self.upload_status}/{self.processing_status})>'