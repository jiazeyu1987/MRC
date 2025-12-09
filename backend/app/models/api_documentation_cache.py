from datetime import datetime, timedelta
from app import db


class APIDocumentationCache(db.Model):
    """API文档缓存模型 - 缓存RAGFlow API文档"""
    __tablename__ = 'api_documentation_cache'

    id = db.Column(db.Integer, primary_key=True)
    endpoint_path = db.Column(db.String(200), nullable=False, unique=True)
    method = db.Column(db.String(10), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    documentation = db.Column(db.JSON, nullable=False)  # 缓存的文档内容
    examples = db.Column(db.JSON, default=[])  # 示例请求和响应
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(hours=24))
    is_active = db.Column(db.Boolean, default=True)

    # 索引
    __table_args__ = (
        db.Index('idx_api_endpoint_method', 'endpoint_path', 'method'),
        db.Index('idx_api_category', 'category'),
        db.Index('idx_api_expires', 'expires_at'),
        db.Index('idx_api_active', 'is_active'),
    )

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'endpoint_path': self.endpoint_path,
            'method': self.method,
            'category': self.category,
            'documentation': self.documentation,
            'examples': self.examples,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_active': self.is_active
        }

    @classmethod
    def get_cached_endpoint(cls, endpoint_path, method):
        """获取缓存的端点文档"""
        return cls.query.filter(
            cls.endpoint_path == endpoint_path,
            cls.method == method.upper(),
            cls.is_active == True,
            cls.expires_at > datetime.utcnow()
        ).first()

    @classmethod
    def cache_endpoint(cls, endpoint_path, method, category, documentation, examples=None):
        """缓存端点文档"""
        # 查找现有记录
        cached = cls.query.filter(
            cls.endpoint_path == endpoint_path,
            cls.method == method.upper()
        ).first()

        if cached:
            # 更新现有记录
            cached.category = category
            cached.documentation = documentation
            cached.examples = examples or []
            cached.last_updated = datetime.utcnow()
            cached.expires_at = datetime.utcnow() + timedelta(hours=24)
            cached.is_active = True
        else:
            # 创建新记录
            cached = cls(
                endpoint_path=endpoint_path,
                method=method.upper(),
                category=category,
                documentation=documentation,
                examples=examples or []
            )
            db.session.add(cached)

        db.session.commit()
        return cached

    @classmethod
    def get_by_category(cls, category):
        """按类别获取缓存的文档"""
        return cls.query.filter(
            cls.category == category,
            cls.is_active == True,
            cls.expires_at > datetime.utcnow()
        ).all()

    @classmethod
    def cleanup_expired(cls):
        """清理过期的缓存"""
        expired_count = cls.query.filter(cls.expires_at <= datetime.utcnow()).count()
        cls.query.filter(cls.expires_at <= datetime.utcnow()).delete()
        db.session.commit()
        return expired_count

    def is_expired(self):
        """检查缓存是否过期"""
        return datetime.utcnow() > self.expires_at

    def refresh(self, new_expires_hours=24):
        """刷新缓存过期时间"""
        self.expires_at = datetime.utcnow() + timedelta(hours=new_expires_hours)
        self.last_updated = datetime.utcnow()
        db.session.commit()

    def __repr__(self):
        return f'<APIDocumentationCache {self.method} {self.endpoint_path}>'