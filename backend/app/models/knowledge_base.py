from datetime import datetime
from app import db


class KnowledgeBase(db.Model):
    """知识库模型 - RAGFlow集成支持"""
    __tablename__ = 'knowledge_bases'

    id = db.Column(db.Integer, primary_key=True)
    ragflow_dataset_id = db.Column(db.String(100), nullable=False, unique=True, index=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    document_count = db.Column(db.Integer, nullable=False, default=0)
    total_size = db.Column(db.BigInteger, nullable=False, default=0)  # 文件总大小（字节）
    status = db.Column(db.String(20), nullable=False, default='active', index=True)  # active, inactive, error
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    role_knowledge_bases = db.relationship('RoleKnowledgeBase', back_populates='knowledge_base', lazy='dynamic')

    # 索引
    __table_args__ = (
        db.Index('idx_knowledge_base_status_name', 'status', 'name'),
        db.Index('idx_knowledge_base_ragflow_name', 'ragflow_dataset_id', 'name'),
    )

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'ragflow_dataset_id': self.ragflow_dataset_id,
            'name': self.name,
            'description': self.description,
            'document_count': self.document_count,
            'total_size': self.total_size,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<KnowledgeBase {self.name}>'