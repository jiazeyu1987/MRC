#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
知识库CRUD操作视图

提供知识库的创建、读取、更新、删除操作
"""

from flask import request, current_app
from .base import BaseKnowledgeBaseResource


class KnowledgeBaseListView(BaseKnowledgeBaseResource):
    """知识库列表资源"""

    def get(self):
        """获取知识库列表"""
        try:
            # 查询参数
            page, per_page = self._get_page_params()
            search = request.args.get('search', '', type=str)
            status = request.args.get('status', '', type=str)
            sort_by, sort_order = self._get_sort_params()

            # 使用知识库服务获取列表
            knowledge_bases, total, pagination_info = self.knowledge_base_service.get_knowledge_bases_list(
                page=page,
                per_page=per_page,
                status=status if status else None,
                search=search if search else None,
                sort_by=sort_by,
                sort_order=sort_order
            )

            # 转换为字典格式
            knowledge_bases_data = [kb.to_dict() for kb in knowledge_bases]

            # 注意：前端类型中字段名为 page_size，这里同时返回 per_page 和 page_size 以保持兼容
            return self._format_response({
                'knowledge_bases': knowledge_bases_data,
                'total': total,
                'page': page,
                'per_page': per_page,
                'page_size': per_page,
                'pages': pagination_info.get('pages', 0),
                'has_prev': pagination_info.get('has_prev', False),
                'has_next': pagination_info.get('has_next', False)
            })

        except Exception as e:
            return self._handle_service_error(e, "获取知识库列表")

    def post(self):
        """执行知识库相关操作：刷新数据集"""
        try:
            json_data = request.get_json()
            if not json_data:
                return self._format_response(
                    error="请求体不能为空",
                    status=400
                )

            action = json_data.get('action', '')

            if action == 'refresh_all':
                # 刷新所有数据集
                sync_result = self.knowledge_base_service.sync_datasets_from_ragflow()

                return self._format_response(
                    data=sync_result,
                    message=f'数据集刷新完成：创建 {sync_result["created"]} 个，更新 {sync_result["updated"]} 个'
                )

            elif action == 'refresh_single':
                # 刷新单个数据集
                knowledge_base_id = json_data.get('knowledge_base_id')
                if not knowledge_base_id:
                    return self._format_response(
                        error="缺少知识库ID参数",
                        status=400
                    )

                refresh_result = self.knowledge_base_service.refresh_dataset_from_ragflow(knowledge_base_id)

                return self._format_response(
                    data=refresh_result,
                    message=f'知识库刷新成功：{refresh_result["new_info"]["name"]}'
                )

            else:
                return self._format_response(
                    error=f'不支持的操作: {action}',
                    status=400
                )

        except Exception as e:
            db.session.rollback()
            return self._handle_service_error(e, "知识库操作")


class KnowledgeBaseDetailView(BaseKnowledgeBaseResource):
    """知识库详情资源"""

    def get(self, knowledge_base_id):
        """获取知识库详情"""
        try:
            knowledge_base = self.knowledge_base_service.get_knowledge_base_by_id(knowledge_base_id)

            if not knowledge_base:
                return self._format_response(
                    error=f"知识库 {knowledge_base_id} 不存在",
                    status=404
                )

            # 获取统计数据
            stats = self.knowledge_base_service.get_knowledge_base_statistics(knowledge_base_id)

            return self._format_response({
                'knowledge_base': knowledge_base.to_dict(),
                'statistics': stats
            })

        except Exception as e:
            return self._handle_service_error(e, "获取知识库详情")

    def post(self, knowledge_base_id):
        """测试知识库对话"""
        try:
            knowledge_base, error_response = self._validate_knowledge_base_exists(knowledge_base_id)
            if error_response:
                return error_response

            json_data = request.get_json()
            if not json_data:
                return self._format_response(
                    error="请求体不能为空",
                    status=400
                )

            question = json_data.get('question')
            if not question:
                return self._format_response(
                    error="缺少问题参数",
                    status=400
                )

            # 执行测试对话
            test_result = self.knowledge_base_service.test_knowledge_base_conversation(
                knowledge_base_id, question
            )

            return self._format_response(
                data=test_result,
                message="测试对话完成"
            )

        except Exception as e:
            return self._handle_service_error(e, "测试知识库对话")

    def delete(self, knowledge_base_id):
        """删除知识库"""
        try:
            knowledge_base, error_response = self._validate_knowledge_base_exists(knowledge_base_id)
            if error_response:
                return error_response

            # 检查是否有关联的文档或对话
            doc_count = Document.query.filter_by(knowledge_base_id=knowledge_base_id).count()
            conv_count = KnowledgeBaseConversation.query.filter_by(knowledge_base_id=knowledge_base_id).count()

            if doc_count > 0 or conv_count > 0:
                return self._format_response(
                    error=f"知识库存在关联数据（{doc_count}个文档，{conv_count}个对话），无法删除",
                    status=409
                )

            # 执行删除
            self.knowledge_base_service.delete_knowledge_base(knowledge_base_id)

            return self._format_response(
                message=f"知识库 {knowledge_base_id} 删除成功"
            )

        except Exception as e:
            db.session.rollback()
            return self._handle_service_error(e, "删除知识库")


class KnowledgeBaseStatisticsView(BaseKnowledgeBaseResource):
    """知识库统计信息资源"""

    def get(self, knowledge_base_id):
        """获取知识库统计信息"""
        try:
            knowledge_base, error_response = self._validate_knowledge_base_exists(knowledge_base_id)
            if error_response:
                return error_response

            # 获取详细统计信息
            stats = self.knowledge_base_service.get_detailed_statistics(knowledge_base_id)

            return self._format_response(
                data=stats
            )

        except Exception as e:
            return self._handle_service_error(e, "获取知识库统计信息")
