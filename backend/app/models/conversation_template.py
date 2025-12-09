from datetime import datetime
from app import db


class ConversationTemplate(db.Model):
    """对话模板模型 - 可重用的对话模板"""
    __tablename__ = 'conversation_templates'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    category = db.Column(db.String(50), nullable=False)  # technical, qa, analysis, custom
    prompt = db.Column(db.Text, nullable=False)
    parameters = db.Column(db.JSON, default=[])  # 模板参数
    is_system = db.Column(db.Boolean, default=False)  # 系统模板 vs 用户模板
    usage_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 索引
    __table_args__ = (
        db.Index('idx_template_category', 'category'),
        db.Index('idx_template_system', 'is_system', 'name'),
        db.Index('idx_template_usage', 'usage_count'),
    )

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'prompt': self.prompt,
            'parameters': self.parameters,
            'is_system': self.is_system,
            'usage_count': self.usage_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def increment_usage(self):
        """增加使用次数"""
        self.usage_count += 1
        self.updated_at = datetime.utcnow()
        db.session.commit()

    def __repr__(self):
        return f'<ConversationTemplate {self.name}>'