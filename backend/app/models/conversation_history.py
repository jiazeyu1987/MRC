from datetime import datetime
from app import db


class ConversationHistory(db.Model):
    """对话历史记录模型 - 持久化对话存储"""
    __tablename__ = 'conversation_history'

    id = db.Column(db.Integer, primary_key=True)
    knowledge_base_id = db.Column(db.Integer, db.ForeignKey('knowledge_bases.id'), nullable=False)
    user_id = db.Column(db.String(100))  # 用户标识符
    title = db.Column(db.String(200), nullable=False)
    messages = db.Column(db.JSON, nullable=False)  # 对话消息
    tags = db.Column(db.JSON, default=[])  # 对话标签
    template_id = db.Column(db.String(100))  # 使用的模板ID
    conversation_metadata = db.Column(db.JSON, default={})  # 额外元数据
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_archived = db.Column(db.Boolean, default=False, index=True)

    # 关系
    knowledge_base = db.relationship('KnowledgeBase', backref=db.backref('conversation_history_records', lazy='dynamic'))

    # 索引
    __table_args__ = (
        db.Index('idx_conversation_kb_created', 'knowledge_base_id', 'created_at'),
        db.Index('idx_conversation_user_created', 'user_id', 'created_at'),
        db.Index('idx_conversation_archived', 'is_archived', 'created_at'),
    )

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'knowledge_base_id': self.knowledge_base_id,
            'user_id': self.user_id,
            'title': self.title,
            'messages': self.messages,
            'tags': self.tags,
            'template_id': self.template_id,
            'metadata': self.conversation_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_archived': self.is_archived
        }

    def __repr__(self):
        return f'<ConversationHistory {self.title}>'