#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
搜索分析服务模块

提供搜索使用情况跟踪和分析的业务逻辑层功能，包括：
- 搜索记录的创建和跟踪
- 搜索性能指标收集
- 热门搜索词分析
- 使用趋势统计
- 性能监控和优化建议

遵循MRC项目的现有模式，与其他服务保持一致的接口风格
"""

import logging
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
from flask import current_app
from sqlalchemy import func, desc, and_, or_
from sqlalchemy.orm import joinedload

from app import db
from app.models import KnowledgeBase, SearchAnalytics, ConversationHistory
from app.services.knowledge_base_service import get_knowledge_base_service
from app.services.cache_service import get_cache_service

logger = logging.getLogger(__name__)


class SearchAnalyticsError(Exception):
    """搜索分析服务错误基类"""
    pass


class SearchAnalyticsStorageError(SearchAnalyticsError):
    """搜索分析存储错误"""
    pass


class SearchAnalyticsService:
    """
    搜索分析服务类

    提供完整的搜索分析功能，包括：
    - 搜索记录跟踪和存储
    - 性能指标收集和分析
    - 热门搜索词统计
    - 使用趋势分析
    - 优化建议生成
    """

    def __init__(self):
        self.knowledge_base_service = get_knowledge_base_service()
        self.cache_service = get_cache_service()

    # 搜索记录跟踪
    def record_search(self, knowledge_base_id: int, search_query: str,
                     user_id: str = None, filters: Dict = None,
                     results_count: int = 0, response_time_ms: int = 0,
                     clicked_documents: List[str] = None) -> SearchAnalytics:
        """
        记录搜索事件

        Args:
            knowledge_base_id: 知识库ID
            search_query: 搜索查询
            user_id: 用户ID
            filters: 搜索过滤器
            results_count: 结果数量
            response_time_ms: 响应时间（毫秒）
            clicked_documents: 被点击的文档ID列表

        Returns:
            SearchAnalytics: 创建的搜索记录

        Raises:
            SearchAnalyticsStorageError: 存储失败
        """
        try:
            # 验证知识库存在
            knowledge_base = self.knowledge_base_service.get_knowledge_base(knowledge_base_id)

            # 清理查询词
            cleaned_query = self._clean_search_query(search_query)

            # 创建搜索记录
            search_record = SearchAnalytics(
                knowledge_base_id=knowledge_base_id,
                user_id=user_id,
                search_query=cleaned_query,
                filters=filters or {},
                results_count=results_count,
                response_time_ms=response_time_ms,
                clicked_documents=clicked_documents or []
            )

            db.session.add(search_record)

            # 更新知识库搜索计数
            knowledge_base.increment_search_count()

            db.session.commit()

            # 清除相关缓存
            self._clear_analytics_cache(knowledge_base_id)

            logger.info(f"Recorded search analytics for query: '{cleaned_query[:50]}...'")
            return search_record

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to record search analytics: {e}")
            raise SearchAnalyticsStorageError(f"Failed to record search analytics: {e}")

    def record_document_click(self, knowledge_base_id: int, search_query: str,
                             document_id: str, user_id: str = None) -> bool:
        """
        记录文档点击事件

        Args:
            knowledge_base_id: 知识库ID
            search_query: 搜索查询
            document_id: 文档ID
            user_id: 用户ID

        Returns:
            bool: 是否记录成功
        """
        try:
            # 查找最近的搜索记录
            recent_search = SearchAnalytics.query.filter(
                and_(
                    SearchAnalytics.knowledge_base_id == knowledge_base_id,
                    SearchAnalytics.search_query == self._clean_search_query(search_query),
                    SearchAnalytics.user_id == user_id if user_id else True,
                    SearchAnalytics.created_at >= datetime.utcnow() - timedelta(minutes=30)
                )
            ).order_by(desc(SearchAnalytics.created_at)).first()

            if recent_search:
                # 更新点击文档列表
                if document_id not in recent_search.clicked_documents:
                    recent_search.clicked_documents.append(document_id)
                    db.session.commit()

                logger.debug(f"Recorded document click: {document_id}")
                return True
            else:
                logger.warning(f"No recent search found for query: {search_query}")
                return False

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to record document click: {e}")
            return False

    # 搜索分析
    def get_search_analytics(self, knowledge_base_id: int, days: int = 30) -> Dict[str, Any]:
        """
        获取搜索分析数据

        Args:
            knowledge_base_id: 知识库ID
            days: 分析天数

        Returns:
            Dict[str, Any]: 搜索分析数据
        """
        try:
            # 检查缓存
            cache_key = f"search_analytics:{knowledge_base_id}:{days}"
            cached = self.cache_service.get(cache_key)
            if cached:
                return cached

            start_date = datetime.utcnow() - timedelta(days=days)

            # 基础统计
            total_searches = SearchAnalytics.query.filter(
                and_(
                    SearchAnalytics.knowledge_base_id == knowledge_base_id,
                    SearchAnalytics.created_at >= start_date
                )
            ).count()

            # 性能统计
            performance_stats = db.session.query(
                func.avg(SearchAnalytics.response_time_ms).label('avg_response_time'),
                func.max(SearchAnalytics.response_time_ms).label('max_response_time'),
                func.min(SearchAnalytics.response_time_ms).label('min_response_time'),
                func.avg(SearchAnalytics.results_count).label('avg_results')
            ).filter(
                and_(
                    SearchAnalytics.knowledge_base_id == knowledge_base_id,
                    SearchAnalytics.created_at >= start_date
                )
            ).first()

            # 获取热门搜索词
            popular_terms = self.get_popular_terms(knowledge_base_id, days)

            # 获取使用趋势
            usage_trends = self.get_usage_trends(knowledge_base_id, days)

            # 无结果搜索分析
            no_result_searches = SearchAnalytics.query.filter(
                and_(
                    SearchAnalytics.knowledge_base_id == knowledge_base_id,
                    SearchAnalytics.results_count == 0,
                    SearchAnalytics.created_at >= start_date
                )
            ).count()

            analytics_data = {
                'period_days': days,
                'total_searches': total_searches,
                'average_per_day': total_searches / max(days, 1),
                'performance': {
                    'avg_response_time_ms': round(performance_stats.avg_response_time or 0, 2),
                    'max_response_time_ms': performance_stats.max_response_time or 0,
                    'min_response_time_ms': performance_stats.min_response_time or 0,
                    'avg_results_count': round(performance_stats.avg_results or 0, 2)
                },
                'popular_terms': popular_terms,
                'usage_trends': usage_trends,
                'no_result_searches': no_result_searches,
                'success_rate': round((total_searches - no_result_searches) / max(total_searches, 1) * 100, 2),
                'click_through_rate': self._calculate_click_through_rate(knowledge_base_id, days)
            }

            # 缓存结果（15分钟）
            self.cache_service.set(cache_key, analytics_data, timeout=900)

            return analytics_data

        except Exception as e:
            logger.error(f"Failed to get search analytics: {e}")
            return self._get_empty_analytics(days)

    def get_popular_terms(self, knowledge_base_id: int, days: int = 30, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取热门搜索词

        Args:
            knowledge_base_id: 知识库ID
            days: 分析天数
            limit: 返回数量限制

        Returns:
            List[Dict[str, Any]]: 热门搜索词列表
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            popular_terms = db.session.query(
                SearchAnalytics.search_query,
                func.count(SearchAnalytics.id).label('count'),
                func.avg(SearchAnalytics.results_count).label('avg_results'),
                func.avg(SearchAnalytics.response_time_ms).label('avg_response_time')
            ).filter(
                and_(
                    SearchAnalytics.knowledge_base_id == knowledge_base_id,
                    SearchAnalytics.created_at >= start_date,
                    SearchAnalytics.search_query != ''
                )
            ).group_by(SearchAnalytics.search_query)\
             .order_by(desc(func.count(SearchAnalytics.id)))\
             .limit(limit)\
             .all()

            return [
                {
                    'term': term.search_query,
                    'count': term.count,
                    'avg_results': round(term.avg_results or 0, 2),
                    'avg_response_time_ms': round(term.avg_response_time or 0, 2)
                }
                for term in popular_terms
            ]

        except Exception as e:
            logger.error(f"Failed to get popular terms: {e}")
            return []

    def get_usage_trends(self, knowledge_base_id: int, days: int = 30) -> List[Dict[str, Any]]:
        """
        获取使用趋势数据

        Args:
            knowledge_base_id: 知识库ID
            days: 分析天数

        Returns:
            List[Dict[str, Any]]: 使用趋势数据
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            trends = db.session.query(
                func.date(SearchAnalytics.created_at).label('date'),
                func.count(SearchAnalytics.id).label('search_count'),
                func.avg(SearchAnalytics.response_time_ms).label('avg_response_time'),
                func.avg(SearchAnalytics.results_count).label('avg_results')
            ).filter(
                and_(
                    SearchAnalytics.knowledge_base_id == knowledge_base_id,
                    SearchAnalytics.created_at >= start_date
                )
            ).group_by(func.date(SearchAnalytics.created_at))\
             .order_by(func.date(SearchAnalytics.created_at))\
             .all()

            return [
                {
                    'date': str(trend.date),
                    'search_count': trend.search_count,
                    'avg_response_time_ms': round(trend.avg_response_time or 0, 2),
                    'avg_results': round(trend.avg_results or 0, 2)
                }
                for trend in trends
            ]

        except Exception as e:
            logger.error(f"Failed to get usage trends: {e}")
            return []

    def get_user_search_patterns(self, knowledge_base_id: int, days: int = 30,
                                limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取用户搜索模式分析

        Args:
            knowledge_base_id: 知识库ID
            days: 分析天数
            limit: 返回用户数量限制

        Returns:
            List[Dict[str, Any]]: 用户搜索模式数据
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            user_patterns = db.session.query(
                SearchAnalytics.user_id,
                func.count(SearchAnalytics.id).label('search_count'),
                func.count(func.distinct(SearchAnalytics.search_query)).label('unique_queries'),
                func.avg(SearchAnalytics.response_time_ms).label('avg_response_time')
            ).filter(
                and_(
                    SearchAnalytics.knowledge_base_id == knowledge_base_id,
                    SearchAnalytics.created_at >= start_date,
                    SearchAnalytics.user_id.isnot(None)
                )
            ).group_by(SearchAnalytics.user_id)\
             .order_by(desc(func.count(SearchAnalytics.id)))\
             .limit(limit)\
             .all()

            return [
                {
                    'user_id': pattern.user_id,
                    'search_count': pattern.search_count,
                    'unique_queries': pattern.unique_queries,
                    'avg_response_time_ms': round(pattern.avg_response_time or 0, 2)
                }
                for pattern in user_patterns
            ]

        except Exception as e:
            logger.error(f"Failed to get user search patterns: {e}")
            return []

    def get_performance_insights(self, knowledge_base_id: int, days: int = 30) -> Dict[str, Any]:
        """
        获取性能洞察和优化建议

        Args:
            knowledge_base_id: 知识库ID
            days: 分析天数

        Returns:
            Dict[str, Any]: 性能洞察数据
        """
        try:
            analytics = self.get_search_analytics(knowledge_base_id, days)

            # 性能分析
            avg_response_time = analytics['performance']['avg_response_time_ms']
            success_rate = analytics['success_rate']
            no_result_rate = (analytics['no_result_searches'] / max(analytics['total_searches'], 1)) * 100

            # 生成建议
            insights = {
                'performance_rating': self._calculate_performance_rating(avg_response_time, success_rate),
                'response_time_status': self._get_response_time_status(avg_response_time),
                'success_rate_status': self._get_success_rate_status(success_rate),
                'recommendations': [],
                'issues': [],
                'strengths': []
            }

            # 响应时间分析
            if avg_response_time > 5000:  # 超过5秒
                insights['issues'].append('搜索响应时间较慢')
                insights['recommendations'].append('考虑优化索引或增加缓存')
            elif avg_response_time < 1000:  # 少于1秒
                insights['strengths'].append('搜索响应速度优秀')

            # 成功率分析
            if success_rate < 80:
                insights['issues'].append('搜索成功率较低')
                insights['recommendations'].append('优化搜索算法或改进文档质量')
            elif success_rate > 95:
                insights['strengths'].append('搜索成功率很高')

            # 无结果搜索分析
            if no_result_rate > 20:
                insights['issues'].append('无结果搜索比例较高')
                insights['recommendations'].append('增加同义词支持或改进搜索匹配算法')

            return insights

        except Exception as e:
            logger.error(f"Failed to get performance insights: {e}")
            return self._get_empty_insights()

    # 数据清理和维护
    def cleanup_old_analytics(self, days: int = 365) -> int:
        """
        清理旧的搜索分析数据

        Args:
            days: 保留天数

        Returns:
            int: 清理的记录数量
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            deleted_count = SearchAnalytics.query.filter(
                SearchAnalytics.created_at < cutoff_date
            ).delete()

            db.session.commit()

            logger.info(f"Cleaned up {deleted_count} old search analytics records")
            return deleted_count

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to cleanup old analytics: {e}")
            return 0

    # 辅助方法
    def _clean_search_query(self, query: str) -> str:
        """清理搜索查询字符串"""
        if not query:
            return ""

        # 移除多余空格和特殊字符
        cleaned = ' '.join(query.strip().split())
        return cleaned.lower()[:500]  # 限制长度并转为小写

    def _clear_analytics_cache(self, knowledge_base_id: int):
        """清除分析相关缓存"""
        try:
            pattern = f"search_analytics:{knowledge_base_id}:*"
            self.cache_service.delete_pattern(pattern)
        except Exception as e:
            logger.warning(f"Failed to clear analytics cache: {e}")

    def _calculate_click_through_rate(self, knowledge_base_id: int, days: int) -> float:
        """计算点击率"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            total_searches = SearchAnalytics.query.filter(
                and_(
                    SearchAnalytics.knowledge_base_id == knowledge_base_id,
                    SearchAnalytics.created_at >= start_date,
                    SearchAnalytics.results_count > 0
                )
            ).count()

            searches_with_clicks = SearchAnalytics.query.filter(
                and_(
                    SearchAnalytics.knowledge_base_id == knowledge_base_id,
                    SearchAnalytics.created_at >= start_date,
                    SearchAnalytics.clicked_documents.isnot(None),
                    SearchAnalytics.clicked_documents != []
                )
            ).count()

            if total_searches == 0:
                return 0.0

            return round((searches_with_clicks / total_searches) * 100, 2)

        except Exception as e:
            logger.error(f"Failed to calculate click through rate: {e}")
            return 0.0

    def _calculate_performance_rating(self, avg_response_time: float, success_rate: float) -> str:
        """计算性能评级"""
        if avg_response_time < 2000 and success_rate > 90:
            return "excellent"
        elif avg_response_time < 3000 and success_rate > 80:
            return "good"
        elif avg_response_time < 5000 and success_rate > 70:
            return "fair"
        else:
            return "poor"

    def _get_response_time_status(self, avg_response_time: float) -> str:
        """获取响应时间状态"""
        if avg_response_time < 1000:
            return "fast"
        elif avg_response_time < 3000:
            return "normal"
        elif avg_response_time < 5000:
            return "slow"
        else:
            return "very_slow"

    def _get_success_rate_status(self, success_rate: float) -> str:
        """获取成功率状态"""
        if success_rate > 95:
            return "excellent"
        elif success_rate > 85:
            return "good"
        elif success_rate > 70:
            return "fair"
        else:
            return "poor"

    def _get_empty_analytics(self, days: int) -> Dict[str, Any]:
        """返回空的分析数据结构"""
        return {
            'period_days': days,
            'total_searches': 0,
            'average_per_day': 0,
            'performance': {
                'avg_response_time_ms': 0,
                'max_response_time_ms': 0,
                'min_response_time_ms': 0,
                'avg_results_count': 0
            },
            'popular_terms': [],
            'usage_trends': [],
            'no_result_searches': 0,
            'success_rate': 0,
            'click_through_rate': 0
        }

    def _get_empty_insights(self) -> Dict[str, Any]:
        """返回空的洞察数据结构"""
        return {
            'performance_rating': 'unknown',
            'response_time_status': 'unknown',
            'success_rate_status': 'unknown',
            'recommendations': [],
            'issues': [],
            'strengths': []
        }


# 全局服务实例
_search_analytics_service_instance = None


def get_search_analytics_service() -> SearchAnalyticsService:
    """获取搜索分析服务实例（单例模式）"""
    global _search_analytics_service_instance
    if _search_analytics_service_instance is None:
        _search_analytics_service_instance = SearchAnalyticsService()
    return _search_analytics_service_instance