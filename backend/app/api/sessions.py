# 会话管理API模块（第四阶段实现）
from flask import request, current_app
from flask_restful import Resource
from app import db
from datetime import datetime
from app.services.session_service import SessionService, SessionError, SessionNotFoundError, InvalidSessionStateError
from app.services.flow_engine_service import FlowEngineService, FlowExecutionError
from app.schemas import SessionSchema, SessionListSchema, SessionRoleSchema
from app.schemas.session_request import (
    CreateSessionSchema, UpdateSessionSchema, SessionControlSchema,
    CreateBranchSessionSchema, SessionExecutionSchema
)
import json


class LLMDebugInfo(Resource):
    """LLM调试信息资源"""

    def get(self):
        """获取最新的LLM调试信息"""
        try:
            llm_debug_info = FlowEngineService.get_latest_llm_debug_info()

            if llm_debug_info is None:
                return {
                    'success': True,
                    'data': None,
                    'message': '当前没有LLM调试信息'
                }

            return {
                'success': True,
                'data': llm_debug_info,
                'message': 'LLM调试信息获取成功'
            }

        except Exception as e:
            current_app.logger.error(f"获取LLM调试信息失败: {str(e)}")
            return {
                'success': False,
                'error_code': 'INTERNAL_ERROR',
                'message': '获取LLM调试信息失败'
            }, 500


class SessionList(Resource):
    """会话列表资源"""

    def get(self):
        """获取会话列表"""
        try:
            # 查询参数
            page = request.args.get('page', 1, type=int)
            page_size = min(request.args.get('page_size', current_app.config['DEFAULT_PAGE_SIZE'], type=int),
                           current_app.config['MAX_PAGE_SIZE'])
            search = request.args.get('search', '', type=str)
            status = request.args.get('status', '', type=str)
            user_id = request.args.get('user_id', type=int)

            # 调用服务层获取数据
            result = SessionService.get_sessions_list(
                page=page,
                page_size=page_size,
                search=search,
                status=status,
                user_id=user_id
            )

            # 序列化结果
            session_schema = SessionSchema(many=True, exclude=('session_roles', 'flow_snapshot', 'roles_snapshot'))
            sessions_data = session_schema.dump(result['sessions'])

            return {
                'success': True,
                'data': {
                    'sessions': sessions_data,
                    'total': result['total'],
                    'page': result['page'],
                    'page_size': result['page_size'],
                    'pages': result['pages']
                }
            }

        except Exception as e:
            current_app.logger.error(f"获取会话列表失败: {str(e)}")
            return {
                'success': False,
                'error_code': 'INTERNAL_ERROR',
                'message': '获取会话列表失败'
            }, 500

    def post(self):
        """创建新会话或获取删除统计信息"""
        try:
            json_data = request.get_json()

            # 检查是否是获取删除统计信息的请求
            if json_data and json_data.get('action') == 'get_deletion_statistics':
                status_filter = json_data.get('status_filter', '')
                stats = SessionService.get_deletion_statistics(status_filter)
                return {
                    'success': True,
                    'data': stats,
                    'message': f'找到 {stats["total_sessions"]} 个会话，其中 {stats["deletable_sessions"]} 个可以删除'
                }

            # 原有的创建会话逻辑
            if not json_data:
                return {
                    'success': False,
                    'error_code': 'INVALID_REQUEST',
                    'message': '请求体不能为空'
                }, 400

            # 数据验证
            create_schema = CreateSessionSchema()
            try:
                data = create_schema.load(json_data)
            except Exception as e:
                return {
                    'success': False,
                    'error_code': 'VALIDATION_ERROR',
                    'message': '数据验证失败',
                    'details': str(e)
                }, 400

            # 调用服务层创建会话
            session = SessionService.create_session(json_data)

            # 返回创建的会话信息
            session_schema = SessionSchema()
            result = session_schema.dump(session)

            return {
                'success': True,
                'data': result,
                'message': '会话创建成功'
            }, 201

        except SessionError as e:
            return {
                'success': False,
                'error_code': 'SESSION_ERROR',
                'message': str(e)
            }, 400

        except Exception as e:
            current_app.logger.error(f"创建会话失败: {str(e)}")
            return {
                'success': False,
                'error_code': 'INTERNAL_ERROR',
                'message': '创建会话失败'
            }, 500

    def delete(self):
        """批量删除会话或强制批量删除会话"""
        try:
            # 检查action参数
            action = request.args.get('action', '')

            # 如果不是批量删除操作，返回方法不允许
            if action != 'bulk_delete':
                return {
                    'success': False,
                    'error_code': 'METHOD_NOT_ALLOWED',
                    'message': 'DELETE方法仅支持批量删除操作'
                }, 405

            # 获取查询参数
            status_filter = request.args.get('status', '', type=str)
            confirm = request.args.get('confirm', 'false', type=str).lower() == 'true'
            force = request.args.get('force', 'false', type=str).lower() == 'true'

            # 如果没有确认参数，返回需要确认的统计信息
            if not confirm:
                stats = SessionService.get_deletion_statistics(status_filter)
                return {
                    'success': True,
                    'data': {
                        'total_sessions': stats['total_sessions'],
                        'deletable_sessions': stats['deletable_sessions'],
                        'running_sessions': stats['running_sessions'],
                        'status_filter': status_filter,
                        'force_available': stats['running_sessions'] > 0
                    },
                    'message': f'找到 {stats["total_sessions"]} 个会话，其中 {stats["deletable_sessions"]} 个可以删除，{stats["running_sessions"]} 个正在运行' +
                               ('（可强制删除）' if force and stats['running_sessions'] > 0 else '')
                }

            # 确认删除，执行批量删除
            if force:
                result = SessionService.force_bulk_delete_sessions(status_filter)
                operation_type = "强制批量删除"
            else:
                result = SessionService.bulk_delete_sessions(status_filter)
                operation_type = "批量删除"

            return {
                'success': True,
                'data': {
                    'deleted_sessions': result['deleted_sessions'],
                    'skipped_sessions': result['skipped_sessions'],
                    'force_deleted_sessions': result.get('force_deleted_sessions', 0),
                    'errors': result.get('errors', [])
                },
                'message': f'{operation_type}完成：成功删除 {result["deleted_sessions"]} 个会话' +
                           (f'，强制删除 {result.get("force_deleted_sessions", 0)} 个运行中的会话' if force else '') +
                           f'，跳过 {result["skipped_sessions"]} 个会话'
            }

        except Exception as e:
            current_app.logger.error(f"批量删除会话失败: {str(e)}")
            db.session.rollback()
            return {
                'success': False,
                'error_code': 'INTERNAL_ERROR',
                'message': '批量删除会话失败'
            }, 500


class SessionDetail(Resource):
    """会话详情资源"""

    def get(self, session_id):
        """获取会话详情"""
        try:
            session = SessionService.get_session_by_id(session_id, include_roles=True)
            if not session:
                return {
                    'success': False,
                    'error_code': 'NOT_FOUND',
                    'message': '会话不存在'
                }, 404

            # 序列化结果
            session_schema = SessionSchema()
            result = session_schema.dump(session)

            return {
                'success': True,
                'data': result
            }

        except Exception as e:
            current_app.logger.error(f"获取会话详情失败: {str(e)}")
            return {
                'success': False,
                'error_code': 'INTERNAL_ERROR',
                'message': '获取会话详情失败'
            }, 500

    def put(self, session_id):
        """更新会话"""
        try:
            json_data = request.get_json()
            if not json_data:
                return {
                    'success': False,
                    'error_code': 'INVALID_REQUEST',
                    'message': '请求体不能为空'
                }, 400

            # 数据验证
            update_schema = UpdateSessionSchema()
            try:
                data = update_schema.load(json_data, partial=True)
            except Exception as e:
                return {
                    'success': False,
                    'error_code': 'VALIDATION_ERROR',
                    'message': '数据验证失败',
                    'details': str(e)
                }, 400

            # 检查会话是否存在
            session = SessionService.get_session_by_id(session_id)
            if not session:
                return {
                    'success': False,
                    'error_code': 'NOT_FOUND',
                    'message': '会话不存在'
                }, 404

            # 更新会话
            for field in ['topic', 'status']:
                if field in json_data:
                    setattr(session, field, json_data[field])

            session.updated_at = datetime.utcnow()
            db.session.commit()

            # 返回更新后的会话信息
            session_schema = SessionSchema()
            result = session_schema.dump(session)

            return {
                'success': True,
                'data': result,
                'message': '会话更新成功'
            }

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"更新会话失败: {str(e)}")
            return {
                'success': False,
                'error_code': 'INTERNAL_ERROR',
                'message': '更新会话失败'
            }, 500

    def delete(self, session_id):
        """删除会话或强制删除会话"""
        try:
            # 获取查询参数
            force = request.args.get('force', 'false', type=str).lower() == 'true'

            session = SessionService.get_session_by_id(session_id)
            if not session:
                return {
                    'success': False,
                    'error_code': 'NOT_FOUND',
                    'message': '会话不存在'
                }, 404

            # 检查会话状态
            if session.status == 'running' and not force:
                return {
                    'success': False,
                    'error_code': 'INVALID_STATE',
                    'message': '正在运行的会话不能删除，请先暂停或结束会话'
                }, 400

            # 如果是强制删除，记录操作并更新状态
            if force:
                current_app.logger.warning(f"强制删除运行中的会话 {session_id}: {session.topic}")
                # 更新会话状态为terminated
                session.status = 'terminated'
                session.ended_at = datetime.utcnow()
                session.error_reason = "Force deleted by user"
                db.session.commit()

            # 删除相关的消息和角色
            Message.query.filter_by(session_id=session_id).delete()
            SessionRole.query.filter_by(session_id=session_id).delete()

            # 删除会话
            db.session.delete(session)
            db.session.commit()

            action_type = "强制删除" if force else "删除"
            return {
                'success': True,
                'message': f'会话{action_type}成功',
                'data': {
                    'force_deleted': force,
                    'was_running': session.status == 'running' if not force else False
                }
            }

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"删除会话失败: {str(e)}")
            return {
                'success': False,
                'error_code': 'INTERNAL_ERROR',
                'message': '删除会话失败'
            }, 500


class SessionExecution(Resource):
    """会话执行资源"""

    def post(self, session_id):
        """执行会话下一步骤"""
        try:
            json_data = request.get_json() or {}

            # 数据验证
            execution_schema = SessionExecutionSchema()
            try:
                data = execution_schema.load(json_data, partial=True)
            except Exception as e:
                return {
                    'success': False,
                    'error_code': 'VALIDATION_ERROR',
                    'message': '数据验证失败',
                    'details': str(e)
                }, 400

            # 检查会话是否可执行
            if not SessionService.is_session_executable(session_id):
                return {
                    'success': False,
                    'error_code': 'NOT_EXECUTABLE',
                    'message': '会话当前状态不允许执行步骤'
                }, 400

            # 执行下一步骤
            message, execution_info = FlowEngineService.execute_next_step(session_id)

            # 序列化结果
            from app.schemas import MessageSchema
            message_schema = MessageSchema()
            message_data = message_schema.dump(message)

            # 添加LLM调试信息到响应中
            llm_debug_info = execution_info.get('llm_debug', {})
            if not llm_debug_info and hasattr(message, 'content'):
                # 如果没有调试信息，使用消息内容作为基本调试信息
                llm_debug_info = {
                    'prompt': f"角色: {execution_info.get('role_name', '未知角色')} - 任务: {execution_info.get('task_type', '对话')}",
                    'response': message.content,
                    'timestamp': datetime.utcnow().isoformat(),
                    'step_info': execution_info
                }

            return {
                'success': True,
                'data': {
                    'message': message_data,
                    'execution_info': execution_info,
                    'llm_debug': llm_debug_info
                },
                'message': '步骤执行成功'
            }

        except SessionNotFoundError as e:
            return {
                'success': False,
                'error_code': 'NOT_FOUND',
                'message': str(e)
            }, 404

        except FlowExecutionError as e:
            return {
                'success': False,
                'error_code': 'FLOW_EXECUTION_ERROR',
                'message': str(e)
            }, 400

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"执行会话步骤失败: {str(e)}")
            return {
                'success': False,
                'error_code': 'INTERNAL_ERROR',
                'message': '执行会话步骤失败'
            }, 500


class SessionControl(Resource):
    """会话控制资源"""

    def post(self, session_id):
        """控制会话状态（开始、暂停、恢复、结束）"""
        try:
            json_data = request.get_json()
            if not json_data or 'action' not in json_data:
                return {
                    'success': False,
                    'error_code': 'INVALID_REQUEST',
                    'message': '请求体必须包含action字段'
                }, 400

            # 数据验证
            control_schema = SessionControlSchema()
            try:
                data = control_schema.load(json_data)
            except Exception as e:
                return {
                    'success': False,
                    'error_code': 'VALIDATION_ERROR',
                    'message': '数据验证失败',
                    'details': str(e)
                }, 400

            action = data['action']
            reason = data.get('reason')

            # 执行相应的控制操作
            if action == 'start':
                session = SessionService.start_session(session_id)
                message = '会话开始成功'

            elif action == 'pause':
                session = SessionService.pause_session(session_id)
                message = '会话暂停成功'

            elif action == 'resume':
                session = SessionService.resume_session(session_id)
                message = '会话恢复成功'

            elif action == 'finish':
                session = SessionService.finish_session(session_id, reason)
                message = '会话结束成功'

            else:
                return {
                    'success': False,
                    'error_code': 'INVALID_ACTION',
                    'message': f'不支持的操作: {action}'
                }, 400

            # 返回更新后的会话信息
            session_schema = SessionSchema()
            result = session_schema.dump(session)

            return {
                'success': True,
                'data': result,
                'message': message
            }

        except SessionNotFoundError as e:
            return {
                'success': False,
                'error_code': 'NOT_FOUND',
                'message': str(e)
            }, 404

        except InvalidSessionStateError as e:
            return {
                'success': False,
                'error_code': 'INVALID_STATE',
                'message': str(e)
            }, 400

        except Exception as e:
            current_app.logger.error(f"控制会话失败: {str(e)}")
            return {
                'success': False,
                'error_code': 'INTERNAL_ERROR',
                'message': '控制会话失败'
            }, 500


class SessionBranch(Resource):
    """会话分支资源"""

    def post(self, session_id):
        """创建分支会话"""
        try:
            json_data = request.get_json()
            if not json_data:
                return {
                    'success': False,
                    'error_code': 'INVALID_REQUEST',
                    'message': '请求体不能为空'
                }, 400

            # 数据验证
            branch_schema = CreateBranchSessionSchema()
            try:
                data = branch_schema.load(json_data)
            except Exception as e:
                return {
                    'success': False,
                    'error_code': 'VALIDATION_ERROR',
                    'message': '数据验证失败',
                    'details': str(e)
                }, 400

            # 创建分支会话
            branch_session = SessionService.create_branch_session(
                session_id,
                data['branch_point_message_id'],
                data.get('new_topic')
            )

            # 返回分支会话信息
            session_schema = SessionSchema()
            result = session_schema.dump(branch_session)

            return {
                'success': True,
                'data': result,
                'message': '分支会话创建成功'
            }, 201

        except SessionNotFoundError as e:
            return {
                'success': False,
                'error_code': 'NOT_FOUND',
                'message': str(e)
            }, 404

        except Exception as e:
            current_app.logger.error(f"创建分支会话失败: {str(e)}")
            return {
                'success': False,
                'error_code': 'INTERNAL_ERROR',
                'message': '创建分支会话失败'
            }, 500


class SessionStatistics(Resource):
    """会话统计资源"""

    def get(self):
        """获取会话统计信息"""
        try:
            stats = SessionService.get_session_statistics()

            return {
                'success': True,
                'data': stats
            }

        except Exception as e:
            current_app.logger.error(f"获取会话统计失败: {str(e)}")
            return {
                'success': False,
                'error_code': 'INTERNAL_ERROR',
                'message': '获取会话统计失败'
            }, 500