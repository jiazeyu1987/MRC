#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
流程引擎核心

负责流程执行的核心逻辑和状态管理
"""

import logging
from typing import Tuple, Dict, Any, Optional
from datetime import datetime

from ...session_service import SessionService, SessionError, FlowExecutionError
from ..llm_integration.llm_service import LLMIntegrationService
from ..debug_manager.debug_service import DebugService

logger = logging.getLogger(__name__)


class FlowEngine:
    """流程引擎核心类"""

    def __init__(self, llm_service: LLMIntegrationService, debug_service: DebugService):
        self.llm_service = llm_service
        self.debug_service = debug_service

    def execute_step(self, session_id: int) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        执行流程步骤

        Args:
            session_id: 会话ID

        Returns:
            Tuple[Dict[str, Any], Dict[str, Any]]: (生成的消息, 执行状态信息)

        Raises:
            SessionError: 会话相关错误
            FlowExecutionError: 流程执行错误
        """
        try:
            # 验证会话状态
            session, current_step = self._validate_session_for_execution(session_id)

            # 获取发言角色
            role = self._get_speaker_role(session, current_step)

            # 构建执行上下文
            context = self._build_execution_context(session, current_step)

            # 生成LLM响应
            llm_result = self.llm_service.generate_response(
                role=role,
                step=current_step,
                context=context,
                session=session
            )

            # 构建调试信息
            debug_info = self.debug_service.create_debug_info(
                session=session,
                step=current_step,
                role=role,
                context=context,
                llm_result=llm_result
            )

            # 更新调试服务状态
            self.debug_service.update_latest_debug_info(debug_info)

            # 更新会话状态
            self._update_session_state(session, current_step, llm_result)

            logger.info(f"步骤执行成功: 会话{session_id}, 步骤{current_step.id}")
            return llm_result, debug_info

        except Exception as e:
            logger.error(f"步骤执行失败: 会话{session_id}, 错误: {str(e)}")
            self._handle_execution_error(session_id, e)
            raise

    def _validate_session_for_execution(self, session_id: int) -> Tuple[Any, Any]:
        """验证会话是否可以执行"""
        from app.models import Session, FlowStep

        # 获取会话
        session = Session.query.get(session_id)
        if not session:
            raise SessionError(f"会话ID {session_id} 不存在")

        if session.status != 'running':
            raise FlowExecutionError(f"会话状态为 {session.status}，无法执行步骤")

        # 获取当前步骤
        current_step = FlowStep.query.get(session.current_step_id)
        if not current_step:
            raise FlowExecutionError(f"当前步骤ID {session.current_step_id} 不存在")

        return session, current_step

    def _get_speaker_role(self, session: Any, step: Any) -> Any:
        """获取发言角色"""
        role = SessionService.get_role_for_execution(session.id, step.speaker_role_ref)
        if not role:
            raise FlowExecutionError(f"发言角色 '{step.speaker_role_ref}' 未找到")
        return role

    def _build_execution_context(self, session: Any, step: Any) -> Dict[str, Any]:
        """构建执行上下文"""
        from .context_builder import ContextBuilder

        context_builder = ContextBuilder()
        return context_builder.build_context(session, step)

    def _update_session_state(self, session: Any, step: Any, llm_result: Dict[str, Any]) -> None:
        """更新会话状态"""
        # 记录LLM交互
        self.llm_service.record_interaction(session, step, llm_result)

        # 更新会话进度
        self._advance_session(session, step)

        # 检查退出条件
        self._check_completion_conditions(session, step)

    def _advance_session(self, session: Any, current_step: Any) -> None:
        """推进会话到下一步"""
        next_step_id = self._determine_next_step(session, current_step)

        if next_step_id:
            session.current_step_id = next_step_id
            logger.debug(f"会话推进到下一步: {next_step_id}")
        else:
            # 检查是否需要开始新一轮
            if self._should_start_new_round(session, current_step):
                session.round_number += 1
                session.current_step_id = self._get_round_start_step(session)
                logger.info(f"开始新一轮对话: 第{session.round_number}轮")
            else:
                # 标记会话完成
                session.status = 'completed'
                session.completed_at = datetime.utcnow()
                logger.info(f"会话完成: {session.id}")

        # 更新最后活动时间
        session.last_activity_at = datetime.utcnow()

    def _determine_next_step(self, session: Any, current_step: Any) -> Optional[int]:
        """确定下一步骤"""
        if current_step.next_step_id:
            return current_step.next_step_id

        # 处理分支逻辑
        return self._handle_step_branching(session, current_step)

    def _handle_step_branching(self, session: Any, step: Any) -> Optional[int]:
        """处理步骤分支逻辑"""
        # 这里可以实现复杂的分支逻辑
        # 例如基于条件、概率、用户选择等
        logic_config = step.logic_config

        if not logic_config:
            return None

        # 示例：简单的条件分支
        if logic_config.get('type') == 'conditional':
            return self._evaluate_conditional_branch(session, step, logic_config)
        elif logic_config.get('type') == 'random':
            return self._evaluate_random_branch(session, step, logic_config)

        return None

    def _evaluate_conditional_branch(self, session: Any, step: Any, logic_config: Dict[str, Any]) -> Optional[int]:
        """评估条件分支"""
        # 实现条件评估逻辑
        conditions = logic_config.get('conditions', [])

        for condition in conditions:
            if self._evaluate_condition(session, condition):
                return condition.get('next_step_id')

        return logic_config.get('default_next_step_id')

    def _evaluate_random_branch(self, session: Any, step: Any, logic_config: Dict[str, Any]) -> Optional[int]:
        """评估随机分支"""
        import random

        branches = logic_config.get('branches', [])
        if not branches:
            return None

        weights = [branch.get('weight', 1) for branch in branches]
        selected_branch = random.choices(branches, weights=weights)[0]

        return selected_branch.get('next_step_id')

    def _evaluate_condition(self, session: Any, condition: Dict[str, Any]) -> bool:
        """评估单个条件"""
        # 实现条件评估逻辑
        condition_type = condition.get('type')

        if condition_type == 'message_count':
            return self._check_message_count_condition(session, condition)
        elif condition_type == 'time_elapsed':
            return self._check_time_elapsed_condition(session, condition)
        elif condition_type == 'user_input':
            return self._check_user_input_condition(session, condition)

        return False

    def _check_message_count_condition(self, session: Any, condition: Dict[str, Any]) -> bool:
        """检查消息数量条件"""
        from app.models import Message

        operator = condition.get('operator', '>')
        threshold = condition.get('threshold', 0)

        message_count = Message.query.filter_by(session_id=session.id).count()

        if operator == '>':
            return message_count > threshold
        elif operator == '>=':
            return message_count >= threshold
        elif operator == '<':
            return message_count < threshold
        elif operator == '<=':
            return message_count <= threshold
        elif operator == '==':
            return message_count == threshold

        return False

    def _check_time_elapsed_condition(self, session: Any, condition: Dict[str, Any]) -> bool:
        """检查时间条件"""
        import datetime

        operator = condition.get('operator', '>')
        threshold_minutes = condition.get('threshold_minutes', 0)

        if not session.created_at:
            return False

        elapsed = datetime.datetime.utcnow() - session.created_at
        elapsed_minutes = elapsed.total_seconds() / 60

        if operator == '>':
            return elapsed_minutes > threshold_minutes
        elif operator == '>=':
            return elapsed_minutes >= threshold_minutes
        elif operator == '<':
            return elapsed_minutes < threshold_minutes
        elif operator == '<=':
            return elapsed_minutes <= threshold_minutes

        return False

    def _check_user_input_condition(self, session: Any, condition: Dict[str, Any]) -> bool:
        """检查用户输入条件"""
        # 实现用户输入条件检查
        # 例如检查特定关键词、情感分析等
        return False

    def _should_start_new_round(self, session: Any, step: Any) -> bool:
        """判断是否应该开始新一轮"""
        # 检查是否达到最大轮数
        max_rounds = step.max_rounds or session.flow_template.max_rounds
        if session.round_number >= max_rounds:
            return False

        # 检查是否有循环结构
        return self._has_loop_structure(session, step)

    def _has_loop_structure(self, session: Any, step: Any) -> bool:
        """检查是否有循环结构"""
        # 实现循环结构检查逻辑
        return step.is_loop_start or step.is_loop_end

    def _get_round_start_step(self, session: Any) -> int:
        """获取新一轮的开始步骤"""
        # 获取流程的第一个步骤
        first_step = session.flow_template.steps.filter_by(is_start=True).first()
        if first_step:
            return first_step.id

        # 如果没有明确的开始步骤，使用第一个步骤
        first_step = session.flow_template.steps.order_by('id').first()
        return first_step.id if first_step else session.current_step_id

    def _check_completion_conditions(self, session: Any, step: Any) -> None:
        """检查完成条件"""
        # 检查最大步骤数
        max_steps = step.max_steps or session.flow_template.max_steps
        if session.step_count >= max_steps:
            session.status = 'completed'
            session.completed_at = datetime.utcnow()
            logger.info(f"会话达到最大步骤数: {session.id}")
            return

        # 检查用户手动停止
        if session.status == 'stopped':
            logger.info(f"会话被用户停止: {session.id}")
            return

    def _handle_execution_error(self, session_id: int, error: Exception) -> None:
        """处理执行错误"""
        from app.models import Session

        session = Session.query.get(session_id)
        if session:
            session.status = 'failed'
            session.error_message = str(error)
            session.failed_at = datetime.utcnow()

            # 记录错误到调试服务
            self.debug_service.record_error(session_id, error)

    def get_execution_status(self, session_id: int) -> Dict[str, Any]:
        """获取执行状态"""
        from app.models import Session

        session = Session.query.get(session_id)
        if not session:
            return {'error': '会话不存在'}

        return {
            'session_id': session_id,
            'status': session.status,
            'current_step_id': session.current_step_id,
            'round_number': session.round_number,
            'step_count': session.step_count,
            'created_at': session.created_at.isoformat() if session.created_at else None,
            'last_activity_at': session.last_activity_at.isoformat() if session.last_activity_at else None,
            'completed_at': session.completed_at.isoformat() if session.completed_at else None,
            'error_message': session.error_message
        }