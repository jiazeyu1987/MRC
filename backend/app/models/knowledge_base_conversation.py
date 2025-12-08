from datetime import datetime
from app import db
import json


class KnowledgeBaseConversation(db.Model):
    """知识库测试对话模型 - 跟踪RAGFlow知识库测试会话"""
    __tablename__ = 'knowledge_base_conversations'

    id = db.Column(db.Integer, primary_key=True)
    knowledge_base_id = db.Column(db.Integer, db.ForeignKey('knowledge_bases.id'), nullable=False, index=True)
    title = db.Column(db.String(300), nullable=False)  # 对话标题
    user_question = db.Column(db.Text, nullable=False)  # 用户问题
    ragflow_response = db.Column(db.Text, nullable=True)  # RAGFlow生成的响应
    confidence_score = db.Column(db.Float, nullable=True)  # 置信度分数 (0-1)
    references = db.Column(db.Text, nullable=True)  # RAGFlow引用信息，JSON格式存储
    extra_data = db.Column(db.Text, nullable=True)  # 其他元数据，JSON格式存储
    status = db.Column(db.String(20), default='active', index=True)  # active, archived, error
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    knowledge_base = db.relationship('KnowledgeBase', backref='conversations')

    # 索引
    __table_args__ = (
        db.Index('idx_kb_conversation_status_created', 'status', 'created_at'),
        db.Index('idx_kb_conversation_kb_created', 'knowledge_base_id', 'created_at'),
    )

    @property
    def references_dict(self):
        """获取引用信息字典"""
        if self.references:
            try:
                return json.loads(self.references)
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}

    @references_dict.setter
    def references_dict(self, value):
        """设置引用信息"""
        if isinstance(value, dict):
            self.references = json.dumps(value, ensure_ascii=False)
        else:
            self.references = value

    @property
    def extra_data_dict(self):
        """获取元数据字典"""
        if self.extra_data:
            try:
                return json.loads(self.extra_data)
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}

    @extra_data_dict.setter
    def extra_data_dict(self, value):
        """设置元数据"""
        if isinstance(value, dict):
            self.extra_data = json.dumps(value, ensure_ascii=False)
        else:
            self.extra_data = value

    def add_reference(self, doc_id, doc_title, snippet, page_num=None, confidence=None):
        """添加引用信息"""
        current_refs = self.references_dict
        new_ref = {
            'document_id': doc_id,
            'document_title': doc_title,
            'snippet': snippet,
            'page_number': page_num,
            'confidence': confidence
        }
        # 移除None值
        new_ref = {k: v for k, v in new_ref.items() if v is not None}

        if 'references' not in current_refs:
            current_refs['references'] = []
        current_refs['references'].append(new_ref)
        self.references_dict = current_refs

    def get_reference_count(self):
        """获取引用数量"""
        refs = self.references_dict
        return len(refs.get('references', []))

    def is_high_confidence(self, threshold=0.8):
        """判断是否为高置信度响应"""
        return self.confidence_score is not None and self.confidence_score >= threshold

    def to_dict(self, include_references=False, include_metadata=False):
        """转换为字典"""
        result = {
            'id': self.id,
            'knowledge_base_id': self.knowledge_base_id,
            'knowledge_base_name': self.knowledge_base.name if self.knowledge_base else None,
            'title': self.title,
            'user_question': self.user_question,
            'ragflow_response': self.ragflow_response,
            'confidence_score': self.confidence_score,
            'status': self.status,
            'reference_count': self.get_reference_count(),
            'is_high_confidence': self.is_high_confidence(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

        if include_references:
            result['references'] = self.references_dict

        if include_metadata:
            result['metadata'] = self.extra_data_dict

        return result

    def __repr__(self):
        return f'<KnowledgeBaseConversation {self.id}:{self.title[:50]}>'