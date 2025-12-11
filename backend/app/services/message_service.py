import json
from datetime import datetime
from typing import List, Dict, Optional, Any
from sqlalchemy import or_, and_, desc
from app import db
from app.models import Message, Session, SessionRole, Role


class MessageService:
    """消息服务类"""

    @staticmethod
    def get_session_messages(session_id: int, page: int = 1, page_size: int = 20,
                            speaker_role_id: Optional[int] = None,
                            target_role_id: Optional[int] = None,
                            round_index: Optional[int] = None,
                            section: Optional[str] = None,
                            keyword: Optional[str] = None,
                            order_by: str = 'created_at') -> Dict[str, Any]:
        """
        获取会话消息列表

        Args:
            session_id: 会话ID
            page: 页码
            page_size: 每页大小
            speaker_role_id: 发言角色ID筛选
            target_role_id: 目标角色ID筛选
            round_index: 轮次筛选
            section: 阶段筛选
            keyword: 关键词搜索
            order_by: 排序方式

        Returns:
            Dict: 包含消息列表和分页信息的字典
        """
        query = Message.query.filter_by(session_id=session_id)

        # 角色筛选
        if speaker_role_id:
            query = query.filter(Message.speaker_session_role_id == speaker_role_id)

        if target_role_id:
            query = query.filter(Message.target_session_role_id == target_role_id)

        # 轮次筛选
        if round_index:
            query = query.filter(Message.round_index == round_index)

        # 阶段筛选
        if section:
            query = query.filter(Message.section == section)

        # 关键词搜索
        if keyword:
            query = query.filter(
                or_(
                    Message.content.contains(keyword),
                    Message.content_summary.contains(keyword)
                )
            )

        # 排序
        if order_by == 'created_at':
            query = query.order_by(Message.created_at.desc())
        elif order_by == 'created_at_asc':
            query = query.order_by(Message.created_at.asc())
        elif order_by == 'round_index':
            query = query.order_by(Message.round_index.desc(), Message.created_at.desc())

        # 分页查询
        pagination = query.paginate(page=page, per_page=page_size, error_out=False)

        return {
            'messages': pagination.items,
            'total': pagination.total,
            'page': page,
            'page_size': page_size,
            'pages': pagination.pages
        }

    @staticmethod
    def get_message_by_id(message_id: int) -> Optional[Message]:
        """
        根据ID获取消息

        Args:
            message_id: 消息ID

        Returns:
            Optional[Message]: 消息对象
        """
        return Message.query.get(message_id)

    @staticmethod
    def get_message_replies(message_id: int) -> List[Message]:
        """
        获取消息的回复

        Args:
            message_id: 消息ID

        Returns:
            List[Message]: 回复消息列表
        """
        return Message.query.filter_by(reply_to_message_id=message_id)\
            .order_by(Message.created_at.asc()).all()

    @staticmethod
    def get_session_rounds(session_id: int) -> List[Dict[str, Any]]:
        """
        获取会话的轮次信息

        Args:
            session_id: 会话ID

        Returns:
            List[Dict]: 轮次信息列表
        """
        # 按轮次分组统计消息
        round_stats = db.session.query(
            Message.round_index,
            db.func.count(Message.id).label('message_count'),
            db.func.min(Message.created_at).label('start_time'),
            db.func.max(Message.created_at).label('end_time')
        ).filter_by(session_id=session_id)\
         .group_by(Message.round_index)\
         .order_by(Message.round_index).all()

        rounds = []
        for stat in round_stats:
            # 获取该轮次的角色参与情况
            roles_in_round = db.session.query(
                SessionRole.role_id,
                Role.name,
                db.func.count(Message.id).label('message_count')
            ).join(Message, Message.speaker_session_role_id == SessionRole.id)\
             .join(Role, Role.id == SessionRole.role_id)\
             .filter(Message.session_id == session_id)\
             .filter(Message.round_index == stat.round_index)\
             .group_by(SessionRole.role_id, Role.name)\
             .all()

            rounds.append({
                'round_index': stat.round_index,
                'message_count': stat.message_count,
                'start_time': stat.start_time.isoformat() if stat.start_time else None,
                'end_time': stat.end_time.isoformat() if stat.end_time else None,
                'participants': [
                    {
                        'role_id': role_stat.role_id,
                        'role_name': role_stat.name,
                        'message_count': role_stat.message_count
                    }
                    for role_stat in roles_in_round
                ]
            })

        return rounds

    @staticmethod
    def get_session_conversation_flow(session_id: int) -> List[Dict[str, Any]]:
        """
        获取会话的对话流程

        Args:
            session_id: 会话ID

        Returns:
            List[Dict]: 对话流程信息
        """
        messages = Message.query.filter_by(session_id=session_id)\
            .order_by(Message.created_at.asc()).all()

        flow = []
        for message in messages:
            speaker_name = (
                message.speaker_role.role.name
                if message.speaker_role and message.speaker_role.role
                else '未知角色'
            )
            target_name = (
                message.target_role.role.name
                if message.target_role and message.target_role.role
                else None
            )

            flow.append({
                'id': message.id,
                'speaker_role': speaker_name,
                'target_role': target_name,
                'content': message.content,
                'content_summary': message.content_summary,
                'round_index': message.round_index,
                'section': message.section,
                'created_at': message.created_at.isoformat() if message.created_at else None,
                'reply_to_message_id': message.reply_to_message_id
            })

        return flow

    @staticmethod
    def search_messages(query_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        搜索消息

        Args:
            query_params: 查询参数

        Returns:
            Dict: 搜索结果
        """
        # 构建查询
        query = Message.query

        # 会话筛选
        if query_params.get('session_id'):
            query = query.filter(Message.session_id == query_params['session_id'])

        # 角色筛选
        if query_params.get('speaker_role_id'):
            query = query.filter(Message.speaker_session_role_id == query_params['speaker_role_id'])

        # 时间范围筛选
        if query_params.get('start_date'):
            query = query.filter(Message.created_at >= query_params['start_date'])

        if query_params.get('end_date'):
            query = query.filter(Message.created_at <= query_params['end_date'])

        # 关键词搜索
        keyword = query_params.get('keyword', '')
        if keyword:
            query = query.filter(
                or_(
                    Message.content.contains(keyword),
                    Message.content_summary.contains(keyword),
                    Message.section.contains(keyword)
                )
            )

        # 排序
        order_by = query_params.get('order_by', 'created_at')
        if order_by == 'created_at':
            query = query.order_by(Message.created_at.desc())
        elif order_by == 'created_at_asc':
            query = query.order_by(Message.created_at.asc())

        # 分页
        page = query_params.get('page', 1)
        page_size = min(query_params.get('page_size', 20), 100)

        pagination = query.paginate(page=page, per_page=page_size, error_out=False)

        return {
            'messages': pagination.items,
            'total': pagination.total,
            'page': page,
            'page_size': page_size,
            'pages': pagination.pages
        }

    @staticmethod
    def get_message_statistics(session_id: Optional[int] = None) -> Dict[str, Any]:
        """
        获取消息统计信息

        Args:
            session_id: 会话ID，如果为None则统计所有消息

        Returns:
            Dict: 统计信息
        """
        query = db.session.query(Message)

        if session_id:
            query = query.filter(Message.session_id == session_id)

        total_messages = query.count()

        # 按轮次统计
        round_stats = db.session.query(
            Message.round_index,
            db.func.count(Message.id).label('count')
        ).filter_by(session_id=session_id if session_id else Message.session_id)\
         .group_by(Message.round_index)\
         .all() if session_id else []

        # 按阶段统计
        section_stats = db.session.query(
            Message.section,
            db.func.count(Message.id).label('count')
        ).filter_by(session_id=session_id if session_id else Message.session_id)\
         .group_by(Message.section)\
         .all() if session_id else []

        # 按角色统计
        role_stats = db.session.query(
            SessionRole.role_id,
            Role.name,
            db.func.count(Message.id).label('message_count')
        ).join(Message, Message.speaker_session_role_id == SessionRole.id)\
         .join(Role, Role.id == SessionRole.role_id)\
         .filter(Message.session_id == session_id if session_id else True)\
         .group_by(SessionRole.role_id, Role.name)\
         .all()

        return {
            'total_messages': total_messages,
            'round_distribution': {stat.round_index: stat.count for stat in round_stats},
            'section_distribution': {stat.section: stat.count for stat in section_stats},
            'role_distribution': {
                stat.name: stat.message_count for stat in role_stats
            }
        }

    @staticmethod
    def export_conversation(session_id: int, format: str = 'json') -> Dict[str, Any]:
        """
        导出对话记录

        Args:
            session_id: 会话ID
            format: 导出格式 ('json', 'markdown', 'text')

        Returns:
            Dict: 导出结果
        """
        session = Session.query.get(session_id)
        if not session:
            raise ValueError(f"会话ID {session_id} 不存在")

        messages = Message.query.filter_by(session_id=session_id)\
            .order_by(Message.created_at.asc()).all()

        if format == 'json':
            return MessageService._export_to_json(session, messages)
        elif format == 'markdown':
            return MessageService._export_to_markdown(session, messages)
        elif format == 'text':
            return MessageService._export_to_text(session, messages)
        else:
            raise ValueError(f"不支持的导出格式: {format}")

    @staticmethod
    def _export_to_json(session: Session, messages: List[Message]) -> Dict[str, Any]:
        """导出为JSON格式"""
        # 获取会话的LLM交互记录
        try:
            from app.services.llm_file_record_service import get_session_llm_interactions
            llm_interactions = get_session_llm_interactions(session.id)

            # 创建消息ID到LLM交互的映射
            message_llm_map = {}
            for interaction in llm_interactions:
                msg_id = interaction.get('message_id')
                # 处理数字类型的message_id，确保匹配
                if msg_id is not None:  # 使用任何有message_id的记录（不再强制要求finalized标记）
                    # 尝试将message_id转换为整数以确保匹配
                    try:
                        msg_id_int = int(msg_id)
                        message_llm_map[msg_id_int] = interaction
                    except (ValueError, TypeError):
                        # 如果转换失败，使用原始值
                        message_llm_map[msg_id] = interaction
        except Exception:
            # 如果获取LLM记录失败，使用空映射
            message_llm_map = {}

        # 构建消息列表，包含LLM提示词信息
        message_data = []
        for msg in messages:
            message_item = {
                'id': msg.id,
                'speaker_role': msg.speaker_role.role.name if msg.speaker_role and msg.speaker_role.role else None,
                'target_role': msg.target_role.role.name if msg.target_role and msg.target_role.role else None,
                'content': msg.content,
                'content_summary': msg.content_summary,
                'round_index': msg.round_index,
                'section': msg.section,
                'created_at': msg.created_at.isoformat() if msg.created_at else None
            }

            # 添加LLM提示词信息（如果存在）
            if msg.id in message_llm_map:
                llm_interaction = message_llm_map[msg.id]
                message_item['llm_interaction'] = {
                    'original_prompt': llm_interaction.get('prompt', ''),
                    'provider': llm_interaction.get('provider', ''),
                    'model': llm_interaction.get('metadata', {}).get('model_used', ''),
                    'success': llm_interaction.get('success', True),
                    'error_message': llm_interaction.get('error_message'),
                    'performance_metrics': llm_interaction.get('performance_metrics', {}),
                    'timestamp': llm_interaction.get('timestamp', ''),
                    'metadata': llm_interaction.get('metadata', {})
                }

                # 添加提示词重构信息
                message_item['prompt_info'] = {
                    'reconstructed': False,
                    'prompt_type': 'original_llm_prompt',
                    'prompt': llm_interaction.get('prompt', ''),
                    'note': '对话执行时实际发送给LLM的原始提示词'
                }
            else:
                # 如果没有原始提示词，进行重构（保持向后兼容）
                reconstructed_prompt = MessageService._reconstruct_prompt_for_message(msg, session)
                message_item['prompt_info'] = {
                    'reconstructed': True,
                    'prompt_type': 'reconstructed_prompt',
                    'prompt': reconstructed_prompt,
                    'note': '基于上下文重构的提示词（原始记录不可用）'
                }

            message_data.append(message_item)

        return {
            'session': {
                'id': session.id,
                'topic': session.topic,
                'flow_template_id': session.flow_template_id,
                'status': session.status,
                'current_step_id': session.current_step_id,
                'current_round': session.current_round,
                'executed_steps_count': session.executed_steps_count,
                'created_at': session.created_at.isoformat() if session.created_at else None,
                'ended_at': session.ended_at.isoformat() if session.ended_at else None
            },
            'messages': message_data,
            'llm_interactions_summary': {
                'total_interactions': len(llm_interactions),
                'with_message_id': len([i for i in llm_interactions if i.get('message_id') and i.get('finalized')]),
                'successful_interactions': len([i for i in llm_interactions if i.get('success', True)]),
                'failed_interactions': len([i for i in llm_interactions if not i.get('success', True)])
            }
        }

    @staticmethod
    def _export_to_markdown(session: Session, messages: List[Message]) -> Dict[str, Any]:
        """导出为Markdown格式"""
        content = f"# {session.topic}\n\n"
        content += f"**会话ID**: {session.id}\n"
        content += f"**状态**: {session.status}\n"
        content += f"**创建时间**: {session.created_at.strftime('%Y-%m-%d %H:%M:%S') if session.created_at else 'N/A'}\n\n"

        content += "## 对话记录\n\n"

        current_round = None
        for msg in messages:
            if msg.round_index != current_round:
                current_round = msg.round_index
                content += f"\n### 第 {current_round} 轮对话\n\n"

            # SessionRole 上只有 role 关系，没有 role_detail
            speaker = msg.speaker_role.role.name if msg.speaker_role and msg.speaker_role.role else '未知角色'
            target = f" (回复: {msg.target_role.role.name})" if msg.target_role and msg.target_role.role else ""

            content += f"**{speaker}{target}**: {msg.content}\n\n"

        return {
            'content': content,
            'filename': f"conversation_{session.id}_{session.topic.replace(' ', '_')}.md"
        }

    @staticmethod
    def _export_to_text(session: Session, messages: List[Message]) -> Dict[str, Any]:
        """导出为纯文本格式"""
        content = f"对话主题: {session.topic}\n"
        content += f"会话ID: {session.id}\n"
        content += f"状态: {session.status}\n"
        content += f"创建时间: {session.created_at.strftime('%Y-%m-%d %H:%M:%S') if session.created_at else 'N/A'}\n"
        content += "=" * 50 + "\n\n"

        for msg in messages:
            # SessionRole 上只有 role 关系，没有 role_detail
            speaker = msg.speaker_role.role.name if msg.speaker_role and msg.speaker_role.role else '未知角色'
            target = f" (回复: {msg.target_role.role.name})" if msg.target_role and msg.target_role.role else ""
            timestamp = msg.created_at.strftime('%H:%M:%S') if msg.created_at else 'N/A'

            content += f"[{timestamp}] 第{msg.round_index}轮 {speaker}{target}:\n"
            content += f"{msg.content}\n\n"

        return {
            'content': content,
            'filename': f"conversation_{session.id}_{session.topic.replace(' ', '_')}.txt"
        }

    @staticmethod
    def delete_message(message_id: int, soft_delete: bool = True) -> bool:
        """
        删除消息

        Args:
            message_id: 消息ID
            soft_delete: 是否软删除

        Returns:
            bool: 删除是否成功
        """
        message = Message.query.get(message_id)
        if not message:
            return False

        try:
            if soft_delete:
                # 软删除：将内容标记为已删除
                message.content = "[消息已删除]"
                message.content_summary = "[消息已删除]"
                db.session.commit()
            else:
                # 硬删除：直接删除
                db.session.delete(message)
                db.session.commit()
            return True

        except Exception:
            db.session.rollback()
            return False

    @staticmethod
    def update_message(message_id: int, content: str) -> Optional[Message]:
        """
        更新消息内容

        Args:
            message_id: 消息ID
            content: 新内容

        Returns:
            Optional[Message]: 更新后的消息对象
        """
        message = Message.query.get(message_id)
        if not message:
            return None

        try:
            message.content = content
            message.content_summary = MessageService._generate_content_summary(content)
            db.session.commit()
            return message

        except Exception:
            db.session.rollback()
            return None

    @staticmethod
    def _reconstruct_prompt_for_message(msg: Message, session: Session) -> str:
        """重构消息的提示词（向后兼容）"""
        try:
            # 获取角色信息
            role_name = msg.speaker_role.role.name if msg.speaker_role and msg.speaker_role.role else '未知角色'
            role_prompt = msg.speaker_role.role.prompt if msg.speaker_role and msg.speaker_role.role else ''

            # 基础提示词
            prompt_parts = [
                f"角色：{role_name}",
                f"角色设定：{role_prompt}",
                f"会话主题：{session.topic}",
                f"当前轮次：{msg.round_index}"
            ]

            # 如果有步骤信息，添加步骤描述
            if hasattr(session, 'current_step_id') and session.current_step_id:
                from app.models import FlowStep
                step = FlowStep.query.get(session.current_step_id)
                if step:
                    prompt_parts.append(f"任务：{step.description or step.task_type}")

            prompt_parts.append("请根据你的角色设定和当前任务进行回应。")

            return "\n\n".join(filter(None, prompt_parts))

        except Exception:
            # 如果重构失败，返回简单的提示词
            return f"作为{msg.speaker_role.role.name if msg.speaker_role and msg.speaker_role.role else '角色'}，请根据当前会话主题进行回应。"

    @staticmethod
    def _generate_content_summary(content: str) -> str:
        """生成内容摘要"""
        if len(content) <= 100:
            return content
        return content[:97] + "..."
