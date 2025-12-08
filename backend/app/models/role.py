from datetime import datetime
from app import db
from .role_knowledge_base import RoleKnowledgeBase


class Role(db.Model):
    """角色模型"""
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    prompt = db.Column(db.Text, nullable=False)  # 统一的字段，包含角色描述、风格等信息
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    session_roles = db.relationship('SessionRole', lazy='dynamic')
    role_knowledge_bases = db.relationship('RoleKnowledgeBase', back_populates='role', lazy='dynamic')

    # 知识库关系 - 通过关联表访问知识库
    knowledge_bases = db.relationship(
        'KnowledgeBase',
        secondary='role_knowledge_bases',
        primaryjoin='and_(Role.id == RoleKnowledgeBase.role_id, RoleKnowledgeBase.is_active == True)',
        secondaryjoin='KnowledgeBase.id == RoleKnowledgeBase.knowledge_base_id',
        order_by='RoleKnowledgeBase.priority.asc()',
        lazy='dynamic',
        viewonly=True
    )

    def to_dict(self, include_knowledge_bases=False):
        """转换为字典"""
        result = {
            'id': self.id,
            'name': self.name,
            'prompt': self.prompt,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

        if include_knowledge_bases:
            # 包含关联的知识库信息
            knowledge_bases = []
            for rkb in self.role_knowledge_bases.filter_by(is_active=True).order_by(RoleKnowledgeBase.priority.asc()):
                if rkb.knowledge_base:
                    kb_dict = rkb.knowledge_base.to_dict()
                    kb_dict.update({
                        'priority': rkb.priority,
                        'retrieval_config': rkb.retrieval_config_dict
                    })
                    knowledge_bases.append(kb_dict)
            result['knowledge_bases'] = knowledge_bases

        return result

    def get_active_knowledge_bases(self):
        """获取所有活跃的知识库关联"""
        return self.role_knowledge_bases.filter_by(is_active=True).order_by(RoleKnowledgeBase.priority.asc())

    def add_knowledge_base(self, knowledge_base, priority=1, retrieval_config=None):
        """添加知识库关联"""
        # 检查是否已存在关联
        existing = self.role_knowledge_bases.filter_by(
            knowledge_base_id=knowledge_base.id
        ).first()

        if existing:
            # 更新现有关联
            existing.priority = priority
            existing.retrieval_config_dict = retrieval_config or {}
            existing.is_active = True
            return existing
        else:
            # 创建新关联
            rkb = RoleKnowledgeBase(
                role_id=self.id,
                knowledge_base_id=knowledge_base.id,
                priority=priority,
                retrieval_config_dict=retrieval_config or {}
            )
            db.session.add(rkb)
            return rkb

    def remove_knowledge_base(self, knowledge_base):
        """移除知识库关联（设为非活跃）"""
        rkb = self.role_knowledge_bases.filter_by(
            knowledge_base_id=knowledge_base.id
        ).first()

        if rkb:
            rkb.is_active = False
            return rkb
        return None

    def get_knowledge_base_priority(self, knowledge_base):
        """获取知识库的优先级"""
        rkb = self.role_knowledge_bases.filter_by(
            knowledge_base_id=knowledge_base.id,
            is_active=True
        ).first()
        return rkb.priority if rkb else None

    def has_knowledge_base(self, knowledge_base):
        """检查是否关联了指定知识库"""
        return self.role_knowledge_bases.filter_by(
            knowledge_base_id=knowledge_base.id,
            is_active=True
        ).first() is not None

    def __repr__(self):
        return f'<Role {self.name}>'