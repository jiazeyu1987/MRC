from datetime import datetime
from app import db
import uuid
import json

class ProcessingLog(db.Model):
    __tablename__ = 'processing_logs'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = db.Column(db.String(36), db.ForeignKey('documents.id'), nullable=False)
    step = db.Column(db.String(50), nullable=False)  # upload, parse, chunk, index
    status = db.Column(db.String(20), nullable=False)  # pending, running, completed, failed
    progress = db.Column(db.Integer, default=0)  # 0-100 percentage
    message = db.Column(db.Text, nullable=True)
    error_details = db.Column(db.JSON, nullable=True)

    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    # Constants for step and status values
    STEPS = ['upload', 'parse', 'chunk', 'index', 'sync']
    STATUSES = ['pending', 'running', 'completed', 'failed', 'cancelled']

    def to_dict(self):
        """Convert processing log to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'document_id': self.document_id,
            'step': self.step,
            'status': self.status,
            'progress': self.progress,
            'message': self.message,
            'error_details': self.error_details,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration_seconds': self.duration_seconds
        }

    @property
    def duration_seconds(self):
        """Calculate the duration of the processing step in seconds"""
        if self.completed_at and self.started_at:
            return int((self.completed_at - self.started_at).total_seconds())
        elif self.status == 'running':
            return int((datetime.utcnow() - self.started_at).total_seconds())
        return 0

    def update_progress(self, progress, message=None):
        """Update the progress of the current processing step"""
        if 0 <= progress <= 100:
            self.progress = progress
            if message:
                self.message = message

            if progress == 100 and self.status == 'running':
                self.status = 'completed'
                self.completed_at = datetime.utcnow()

            db.session.commit()

    def mark_running(self, message=None):
        """Mark the processing step as running"""
        self.status = 'running'
        if message:
            self.message = message
        self.progress = 0
        db.session.commit()

    def mark_completed(self, message=None):
        """Mark the processing step as completed"""
        self.status = 'completed'
        self.progress = 100
        if message:
            self.message = message
        self.completed_at = datetime.utcnow()
        db.session.commit()

    def mark_failed(self, error_message, error_details=None):
        """Mark the processing step as failed with error details"""
        self.status = 'failed'
        if error_message:
            self.message = error_message
        if error_details:
            self.error_details = error_details
        self.completed_at = datetime.utcnow()
        db.session.commit()

    def cancel(self):
        """Cancel the processing step"""
        self.status = 'cancelled'
        self.completed_at = datetime.utcnow()
        db.session.commit()

    @classmethod
    def start_step(cls, document_id, step, message=None):
        """Start a new processing step for a document"""
        # Check if there's already a running step for this document and step
        existing_log = cls.query.filter_by(
            document_id=document_id,
            step=step,
            status='running'
        ).first()

        if existing_log:
            return existing_log

        log = cls(
            document_id=document_id,
            step=step,
            status='pending',
            message=message or f"Starting {step} process"
        )
        db.session.add(log)
        db.session.commit()
        return log

    @classmethod
    def get_document_logs(cls, document_id):
        """Get all processing logs for a document, ordered by creation time"""
        return cls.query.filter_by(document_id=document_id).order_by(cls.started_at.desc()).all()

    @classmethod
    def get_current_step(cls, document_id):
        """Get the current running step for a document"""
        return cls.query.filter_by(
            document_id=document_id,
            status='running'
        ).first()

    @classmethod
    def has_failed_step(cls, document_id):
        """Check if any step has failed for a document"""
        return cls.query.filter_by(
            document_id=document_id,
            status='failed'
        ).first() is not None

    @classmethod
    def cleanup_old_logs(cls, days=30):
        """Clean up processing logs older than specified days"""
        cutoff_date = datetime.utcnow() - datetime.timedelta(days=days)
        old_logs = cls.query.filter(cls.started_at < cutoff_date).all()
        for log in old_logs:
            db.session.delete(log)
        db.session.commit()
        return len(old_logs)

    def __repr__(self):
        return f'<ProcessingLog {self.step} ({self.status}) - {self.progress}%'