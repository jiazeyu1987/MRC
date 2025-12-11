#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
搜索分析视图

提供知识库的搜索分析、统计信息、热门术语等功能
"""

from flask import request, current_app
from .base import BaseKnowledgeBaseResource
from datetime import datetime, timedelta


class SearchAnalyticsView(BaseKnowledgeBaseResource):
    """搜索分析资源"""

    def get(self, knowledge_base_id):
        """获取知识库搜索分析"""
        try:
            # 验证知识库存在
            knowledge_base, error_response = self._validate_knowledge_base_exists(knowledge_base_id)
            if error_response:
                return error_response

            # 查询参数
            days = request.args.get('days', 30, type=int)
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            group_by = request.args.get('group_by', 'day')  # day, week, month

            # 处理日期范围
            if start_date:
                start_date = datetime.fromisoformat(start_date)
            else:
                start_date = datetime.utcnow() - timedelta(days=days)

            if end_date:
                end_date = datetime.fromisoformat(end_date)
            else:
                end_date = datetime.utcnow()

            # 获取搜索分析数据
            analytics_data = self.knowledge_base_service.get_search_analytics(
                knowledge_base_id=knowledge_base_id,
                start_date=start_date,
                end_date=end_date,
                group_by=group_by
            )

            return self._format_response(
                data=analytics_data
            )

        except Exception as e:
            return self._handle_service_error(e, "获取搜索分析")


class EnhancedSearchAnalyticsView(BaseKnowledgeBaseResource):
    """增强搜索分析资源"""

    def get(self, knowledge_base_id):
        """获取增强的搜索分析数据"""
        try:
            # 验证知识库存在
            knowledge_base, error_response = self._validate_knowledge_base_exists(knowledge_base_id)
            if error_response:
                return error_response

            # 获取多维度分析数据
            enhanced_data = self.knowledge_base_service.get_enhanced_analytics(
                knowledge_base_id=knowledge_base_id,
                include_user_behavior=True,
                include_performance_metrics=True,
                include_content_analysis=True
            )

            return self._format_response(
                data=enhanced_data
            )

        except Exception as e:
            return self._handle_service_error(e, "获取增强搜索分析")


class SearchInsightsView(BaseKnowledgeBaseResource):
    """搜索洞察资源"""

    def get(self, knowledge_base_id):
        """获取搜索洞察和建议"""
        try:
            # 验证知识库存在
            knowledge_base, error_response = self._validate_knowledge_base_exists(knowledge_base_id)
            if error_response:
                return error_response

            # 获取搜索洞察
            insights = self.knowledge_base_service.get_search_insights(knowledge_base_id)

            return self._format_response(
                data=insights
            )

        except Exception as e:
            return self._handle_service_error(e, "获取搜索洞察")


class PopularTermsView(BaseKnowledgeBaseResource):
    """热门术语资源"""

    def get(self, knowledge_base_id):
        """获取热门搜索术语"""
        try:
            # 验证知识库存在
            knowledge_base, error_response = self._validate_knowledge_base_exists(knowledge_base_id)
            if error_response:
                return error_response

            # 查询参数
            limit = min(request.args.get('limit', 50, type=int), 200)
            days = request.args.get('days', 30, type=int)
            term_type = request.args.get('type', 'all')  # all, successful, failed

            # 获取热门术语
            popular_terms = self.knowledge_base_service.get_popular_search_terms(
                knowledge_base_id=knowledge_base_id,
                limit=limit,
                days=days,
                term_type=term_type
            )

            return self._format_response(
                data={
                    'popular_terms': popular_terms,
                    'total_terms': len(popular_terms),
                    'analysis_period': days
                }
            )

        except Exception as e:
            return self._handle_service_error(e, "获取热门术语")


class EnhancedStatisticsView(BaseKnowledgeBaseResource):
    """增强统计信息资源"""

    def get(self, knowledge_base_id):
        """获取知识库增强统计信息"""
        try:
            # 验证知识库存在
            knowledge_base, error_response = self._validate_knowledge_base_exists(knowledge_base_id)
            if error_response:
                return error_response

            # 获取增强统计信息
            enhanced_stats = self.knowledge_base_service.get_enhanced_statistics(knowledge_base_id)

            return self._format_response(
                data=enhanced_stats
            )

        except Exception as e:
            return self._handle_service_error(e, "获取增强统计信息")


class TopActiveKnowledgeBasesView(BaseKnowledgeBaseResource):
    """活跃知识库排行资源"""

    def get(self):
        """获取最活跃的知识库排行"""
        try:
            # 查询参数
            limit = min(request.args.get('limit', 10, type=int), 50)
            days = request.args.get('days', 30, type=int)
            metric = request.args.get('metric', 'search_count')  # search_count, document_count, conversation_count

            # 获取活跃知识库排行
            top_knowledge_bases = self.knowledge_base_service.get_top_active_knowledge_bases(
                limit=limit,
                days=days,
                metric=metric
            )

            return self._format_response(
                data={
                    'top_knowledge_bases': top_knowledge_bases,
                    'metric': metric,
                    'analysis_period': days,
                    'total_count': len(top_knowledge_bases)
                }
            )

        except Exception as e:
            return self._handle_service_error(e, "获取活跃知识库排行")