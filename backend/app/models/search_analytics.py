from datetime import datetime
from app import db


class SearchAnalytics(db.Model):
    """搜索分析模型 - 搜索使用情况跟踪"""
    __tablename__ = 'search_analytics'

    id = db.Column(db.Integer, primary_key=True)
    knowledge_base_id = db.Column(db.Integer, db.ForeignKey('knowledge_bases.id'), nullable=False)
    user_id = db.Column(db.String(100))
    search_query = db.Column(db.String(500), nullable=False)
    filters = db.Column(db.JSON, default={})
    results_count = db.Column(db.Integer, default=0)
    response_time_ms = db.Column(db.Integer, default=0)
    clicked_documents = db.Column(db.JSON, default=[])  # 被点击的文档ID列表
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # 关系
    knowledge_base = db.relationship('KnowledgeBase', backref=db.backref('search_analytics_records', lazy='dynamic'))

    # 索引
    __table_args__ = (
        db.Index('idx_search_kb_date', 'knowledge_base_id', 'created_at'),
        db.Index('idx_search_user_date', 'user_id', 'created_at'),
        db.Index('idx_search_query', 'search_query'),
        db.Index('idx_search_performance', 'response_time_ms'),
        db.Index('idx_search_results', 'results_count'),
    )

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'knowledge_base_id': self.knowledge_base_id,
            'user_id': self.user_id,
            'search_query': self.search_query,
            'filters': self.filters,
            'results_count': self.results_count,
            'response_time_ms': self.response_time_ms,
            'clicked_documents': self.clicked_documents,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    @classmethod
    def get_popular_terms(cls, knowledge_base_id=None, days=30, limit=10):
        """获取热门搜索词"""
        from datetime import timedelta

        start_date = datetime.utcnow() - timedelta(days=days)
        query = db.session.query(
            cls.search_query,
            db.func.count(cls.id).label('count')
        ).filter(cls.created_at >= start_date)

        if knowledge_base_id:
            query = query.filter(cls.knowledge_base_id == knowledge_base_id)

        return query.group_by(cls.search_query)\
                   .order_by(db.desc('count'))\
                   .limit(limit)\
                   .all()

    @classmethod
    def get_usage_trends(cls, knowledge_base_id=None, days=30):
        """获取使用趋势数据"""
        from datetime import timedelta

        start_date = datetime.utcnow() - timedelta(days=days)
        query = db.session.query(
            db.func.date(cls.created_at).label('date'),
            db.func.count(cls.id).label('count'),
            db.func.avg(cls.response_time_ms).label('avg_response_time')
        ).filter(cls.created_at >= start_date)

        if knowledge_base_id:
            query = query.filter(cls.knowledge_base_id == knowledge_base_id)

        return query.group_by(db.func.date(cls.created_at))\
                   .order_by(db.func.date(cls.created_at))\
                   .all()

    def __repr__(self):
        return f'<SearchAnalytics {self.search_query[:50]}...>'