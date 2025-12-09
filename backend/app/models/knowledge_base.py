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

    # 新增字段用于增强功能
    conversation_count = db.Column(db.Integer, default=0)
    search_count = db.Column(db.Integer, default=0)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    settings = db.Column(db.JSON, default={})  # 存储功能偏好设置

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
            'conversation_count': self.conversation_count,
            'search_count': self.search_count,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'settings': self.settings,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def update_activity(self):
        """更新活动时间"""
        self.last_activity = datetime.utcnow()
        db.session.commit()

    def increment_conversation_count(self):
        """增加对话计数"""
        self.conversation_count += 1
        self.update_activity()

    def increment_search_count(self):
        """增加搜索计数"""
        self.search_count += 1
        self.update_activity()

    def get_setting(self, key, default=None):
        """获取设置值"""
        return self.settings.get(key, default)

    def set_setting(self, key, value):
        """设置配置值"""
        if not self.settings:
            self.settings = {}
        self.settings[key] = value
        self.updated_at = datetime.utcnow()
        db.session.commit()

    def __repr__(self):
        return f'<KnowledgeBase {self.name}>'