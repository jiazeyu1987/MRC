from datetime import datetime
from app import db
import json


class RoleKnowledgeBase(db.Model):
    """角色知识库关联模型 - 多对多关系表"""
    __tablename__ = 'role_knowledge_bases'

    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    knowledge_base_id = db.Column(db.Integer, db.ForeignKey('knowledge_bases.id'), nullable=False)
    priority = db.Column(db.Integer, nullable=False, default=1)  # 优先级，数字越小优先级越高
    retrieval_config = db.Column(db.Text)  # 检索配置，JSON格式存储
    is_active = db.Column(db.Boolean, default=True, nullable=False)  # 是否启用
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 索引
    __table_args__ = (
        db.Index('idx_role_knowledge_base_role_priority', 'role_id', 'priority'),
        db.Index('idx_role_knowledge_base_kb_priority', 'knowledge_base_id', 'priority'),
        db.UniqueConstraint('role_id', 'knowledge_base_id', name='uq_role_knowledge_base'),
    )

    # 关系
    role = db.relationship('Role', back_populates='role_knowledge_bases')
    knowledge_base = db.relationship('KnowledgeBase', back_populates='role_knowledge_bases')

    @property
    def retrieval_config_dict(self):
        """获取检索配置字典"""
        if self.retrieval_config:
            try:
                return json.loads(self.retrieval_config)
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}

    @retrieval_config_dict.setter
    def retrieval_config_dict(self, value):
        """设置检索配置"""
        if isinstance(value, dict):
            self.retrieval_config = json.dumps(value, ensure_ascii=False)
        else:
            self.retrieval_config = value

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'role_id': self.role_id,
            'knowledge_base_id': self.knowledge_base_id,
            'priority': self.priority,
            'retrieval_config': self.retrieval_config_dict,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'role_name': self.role.name if self.role else None,
            'knowledge_base_name': self.knowledge_base.name if self.knowledge_base else None
        }

    def __repr__(self):
        return f'<RoleKnowledgeBase {self.role_id}:{self.knowledge_base_id}>'