import json
import asyncio
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
from app import db
from app.models import Session, SessionRole, Message, FlowTemplate, FlowStep, Role, RoleKnowledgeBase
from app.services.session_service import SessionService, SessionError, FlowExecutionError
from app.services.llm.conversation_service import conversation_llm_service
from app.services.llm.conversation_service import LLMError
from app.services.llm_file_record_service import record_llm_interaction
from app.services.knowledge_base_service import get_knowledge_base_service
from app.services.ragflow_service import get_ragflow_service, RAGFlowAPIError

# 全局变量存储最新的LLM调试信息
latest_llm_debug_info = None


class FlowEngineService:
    """流程引擎服务类 - 负责执行对话流程"""

    @staticmethod
    def execute_next_step(session_id: int) -> Tuple[Message, Dict[str, Any]]:
        """
        执行会话的下一步骤

        Args:
            session_id: 会话ID

        Returns:
            Tuple[Message, Dict[str, Any]]: (生成的消息, 执行状态信息)

        Raises:
            SessionError: 会话相关错误
            FlowExecutionError: 流程执行错误
        """
        # 获取会话
        session = Session.query.get(session_id)
        if not session:
            raise SessionError(f"会话ID {session_id} 不存在")

        if session.status != 'running':
            raise FlowExecutionError(f"会话状态为 {session.status}，无法执行步骤")

        try:
            # 获取当前步骤
            current_step = FlowStep.query.get(session.current_step_id)
            if not current_step:
                raise FlowExecutionError(f"当前步骤ID {session.current_step_id} 不存在")

            # 获取发言角色（支持有角色映射和无角色映射两种模式）
            role = SessionService.get_role_for_execution(session_id, current_step.speaker_role_ref)
            if not role:
                raise FlowExecutionError(f"发言角色 '{current_step.speaker_role_ref}' 未找到")

            # 如果有角色映射，获取session_role；否则创建虚拟的session_role对象
            speaker_session_role = SessionService.get_session_role_by_ref(session_id, current_step.speaker_role_ref)

            # 如果没有session_role，创建一个临时的SessionRole记录
            if not speaker_session_role:
                # 创建一个临时的SessionRole记录（仅用于无角色映射模式）
                temp_session_role = SessionRole(
                    session_id=session_id,
                    role_ref=current_step.speaker_role_ref,
                    role_id=role.id
                )
                db.session.add(temp_session_role)
                db.session.flush()  # 获取ID

                speaker_session_role = temp_session_role

            # 构建上下文
            context = FlowEngineService._build_context(session, current_step)

            # 使用LLM服务生成内容，同时获取提示词和响应
            prompt_content, llm_response = FlowEngineService._generate_llm_response_sync(
                role, current_step, context, session=session
            )

            # 构建LLM调试信息
            llm_debug_info = {
                'role_name': role.name if role else '未知角色',
                'step_description': current_step.description or '',
                'step_type': current_step.task_type or '',
                'prompt': prompt_content,
                'response': llm_response,
                'timestamp': datetime.utcnow().isoformat(),
                'context_summary': f"历史消息: {len(context.get('history_messages', []))}条",
                # 新增：知识库上下文信息
                'knowledge_base_context': {
                    'retrieved_items': len(context.get('knowledge_base', {}).get('retrieved_context', [])),
                    'fallback_used': context.get('knowledge_base', {}).get('fallback_used', False),
                    'error_message': context.get('knowledge_base', {}).get('error_message'),
                    'performance_metrics': context.get('knowledge_base', {}).get('performance_metrics', {})
                }
            }

            # 更新全局LLM调试信息变量
            global latest_llm_debug_info
            latest_llm_debug_info = llm_debug_info.copy()

            # 创建消息
            message = Message(
                session_id=session_id,
                speaker_session_role_id=speaker_session_role.id if speaker_session_role else None,
                target_session_role_id=FlowEngineService._get_target_session_role_id(
                    session_id, current_step.target_role_ref
                ),
                reply_to_message_id=FlowEngineService._get_reply_to_message_id(session, current_step),
                content=llm_response,
                content_summary=FlowEngineService._generate_content_summary(llm_response),
                round_index=session.current_round,
                section=FlowEngineService._determine_message_section(current_step)
            )

            db.session.add(message)
            db.session.flush()  # 获取消息ID

            # 更新会话状态
            FlowEngineService._update_session_after_step_execution(session, current_step)

            # 记录带有消息ID的LLM交互（补充信息）
            if hasattr(FlowEngineService, '_last_llm_interaction_data'):
                interaction_data = FlowEngineService._last_llm_interaction_data
                record_llm_interaction(
                    session_id=session.id,
                    message_id=message.id,
                    role_name=interaction_data.get('role_name'),
                    step_id=interaction_data.get('step_id'),
                    round_index=session.current_round,
                    prompt=interaction_data.get('prompt'),
                    response=interaction_data.get('response'),
                    provider=interaction_data.get('provider'),
                    success=interaction_data.get('success', True),
                    error_message=interaction_data.get('error_message'),
                    performance_metrics=interaction_data.get('performance_metrics'),
                    metadata={
                        **interaction_data.get('metadata', {}),
                        'message_id': message.id,
                        'finalized': True
                    }
                )
                # 清理临时数据
                delattr(FlowEngineService, '_last_llm_interaction_data')

            db.session.commit()

            # 构建执行状态信息
            execution_info = {
                'step_executed': True,
                'session_status': session.status,
                'current_round': session.current_round,
                'executed_steps_count': session.executed_steps_count,
                'next_step_id': session.current_step_id,
                'is_finished': session.status == 'finished',
                'llm_debug': llm_debug_info  # 添加LLM调试信息
            }

            return message, execution_info

        except Exception as e:
            db.session.rollback()
            if isinstance(e, (SessionError, FlowExecutionError)):
                raise
            raise FlowExecutionError(f"执行步骤失败: {str(e)}")

    @staticmethod
    def get_latest_llm_debug_info() -> Optional[Dict[str, Any]]:
        """
        获取最新的LLM调试信息

        Returns:
            Optional[Dict[str, Any]]: 最新的LLM调试信息，如果没有则返回None
        """
        global latest_llm_debug_info
        return latest_llm_debug_info

    @staticmethod
    def _retrieve_knowledge_base_context(
        session_id: int,
        role_ref: str,
        context_query: str,
        max_context_items: int = 5
    ) -> Dict[str, Any]:
        """
        为指定角色检索相关知识库上下文

        Args:
            session_id: 会话ID
            role_ref: 角色引用
            context_query: 上下文查询关键词
            max_context_items: 最大返回上下文条目数

        Returns:
            Dict[str, Any]: 包含知识库上下文的字典
        """
        start_time = datetime.utcnow()
        knowledge_context = {
            'retrieved_context': [],
            'fallback_used': False,
            'error_message': None,
            'performance_metrics': {}
        }

        try:
            # 获取角色对应的实际角色ID
            speaker_session_role = SessionService.get_session_role_by_ref(session_id, role_ref)
            if not speaker_session_role or not speaker_session_role.role_id:
                knowledge_context['fallback_used'] = True
                knowledge_context['error_message'] = f"角色 '{role_ref}' 未找到映射的实际角色"
                return knowledge_context

            role_id = speaker_session_role.role_id

            # 获取角色的关联知识库（按优先级排序）
            role_knowledge_bases = RoleKnowledgeBase.query.filter_by(
                role_id=role_id,
                is_active=True
            ).order_by(RoleKnowledgeBase.priority).all()

            if not role_knowledge_bases:
                knowledge_context['fallback_used'] = True
                knowledge_context['error_message'] = f"角色 '{role_ref}' 未关联任何知识库"
                return knowledge_context

            # 获取RAGFlow服务
            ragflow_service = get_ragflow_service()
            if not ragflow_service:
                knowledge_context['fallback_used'] = True
                knowledge_context['error_message'] = "RAGFlow服务不可用"
                return knowledge_context

            # 为每个知识库检索相关内容
            all_retrieved_items = []
            for role_kb in role_knowledge_bases:
                try:
                    # 获取知识库信息
                    kb_service = get_knowledge_base_service()
                    knowledge_base = kb_service.get_knowledge_base_by_id(role_kb.knowledge_base_id)

                    if not knowledge_base or knowledge_base.status != 'active':
                        continue

                    # 使用RAGFlow检索相关内容
                    retrieval_config = role_kb.retrieval_config_dict or {}
                    top_k = retrieval_config.get('top_k', 3)
                    similarity_threshold = retrieval_config.get('similarity_threshold', 0.7)

                    # 构建检索查询，结合会话上下文和当前步骤需求
                    retrieval_query = context_query[:500]  # 限制查询长度

                    chat_response = ragflow_service.chat_with_dataset(
                        dataset_id=knowledge_base.ragflow_dataset_id,
                        question=retrieval_query,
                        **{k: v for k, v in retrieval_config.items() if k in ['top_k', 'similarity_threshold']}
                    )

                    # 处理检索结果
                    if chat_response and chat_response.answer:
                        kb_context = {
                            'knowledge_base_id': knowledge_base.id,
                            'knowledge_base_name': knowledge_base.name,
                            'content': chat_response.answer,
                            'confidence_score': chat_response.confidence_score,
                            'references': chat_response.references,
                            'priority': role_kb.priority,
                            'retrieval_config': retrieval_config
                        }
                        all_retrieved_items.append(kb_context)

                except RAGFlowAPIError as e:
                    # 记录单个知识库检索失败，但继续尝试其他知识库
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(
                        f"知识库检索失败 (KB ID: {role_kb.knowledge_base_id}): {str(e)}"
                    )
                    continue
                except Exception as e:
                    # 记录其他错误，但继续尝试其他知识库
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(
                        f"知识库检索异常 (KB ID: {role_kb.knowledge_base_id}): {str(e)}"
                    )
                    continue

            # 按优先级和置信度排序检索结果
            all_retrieved_items.sort(key=lambda x: (x['priority'], -x['confidence_score']))

            # 限制返回的上下文条目数量
            knowledge_context['retrieved_context'] = all_retrieved_items[:max_context_items]

            # 计算性能指标
            end_time = datetime.utcnow()
            knowledge_context['performance_metrics'] = {
                'retrieval_time_ms': int((end_time - start_time).total_seconds() * 1000),
                'knowledge_bases_tried': len(role_knowledge_bases),
                'successful_retrievals': len(all_retrieved_items),
                'items_returned': len(knowledge_context['retrieved_context']),
                'query_length': len(context_query)
            }

            # 如果没有检索到任何内容，标记为使用fallback
            if not knowledge_context['retrieved_context']:
                knowledge_context['fallback_used'] = True
                knowledge_context['error_message'] = "未从任何知识库检索到相关内容"

            return knowledge_context

        except Exception as e:
            # 整体检索失败
            end_time = datetime.utcnow()
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"知识库上下文检索异常: {str(e)}")

            knowledge_context['fallback_used'] = True
            knowledge_context['error_message'] = f"知识库检索失败: {str(e)}"
            knowledge_context['performance_metrics'] = {
                'retrieval_time_ms': int((end_time - start_time).total_seconds() * 1000),
                'error': True,
                'error_type': type(e).__name__
            }

            return knowledge_context

    @staticmethod
    def _build_context(session: Session, current_step: FlowStep) -> Dict[str, Any]:
        """
        构建对话上下文

        Args:
            session: 会话对象
            current_step: 当前步骤

        Returns:
            Dict: 上下文字典
        """
        # 获取角色映射并添加防御性检查
        role_mapping = SessionService.get_role_mapping(session.id)
        if not isinstance(role_mapping, dict):
            role_mapping = {}  # 降级处理：如果不是字典，使用空字典

        context = {
            'session_topic': session.topic,
            'current_round': session.current_round,
            'step_count': session.executed_steps_count,
            'session_roles': role_mapping
        }

        # 根据上下文范围选择历史消息
        messages = FlowEngineService._select_context_messages(session, current_step)
        context['history_messages'] = [
            {
                'id': msg.id,
                'speaker_role': msg.speaker_role.role.name if msg.speaker_role and msg.speaker_role.role else None,
                'target_role': msg.target_role.role.name if msg.target_role and msg.target_role.role else None,
                'content': msg.content,
                'round_index': msg.round_index,
                'section': msg.section,
                'created_at': msg.created_at.isoformat() if msg.created_at else None
            }
            for msg in messages
        ]

        # 添加当前步骤信息
        context['current_step'] = {
            'task_type': current_step.task_type,
            'description': current_step.description,
            'target_role_ref': current_step.target_role_ref
        }

        # 新增：检索并添加知识库上下文
        knowledge_context = FlowEngineService._retrieve_knowledge_base_context(
            session_id=session.id,
            role_ref=current_step.speaker_role_ref,
            context_query=FlowEngineService._build_context_query(session, current_step, messages),
            max_context_items=5
        )

        context['knowledge_base'] = knowledge_context

        # 记录知识库检索性能指标到日志
        if knowledge_context.get('performance_metrics'):
            import logging
            logger = logging.getLogger(__name__)
            perf_metrics = knowledge_context['performance_metrics']

            if knowledge_context.get('fallback_used'):
                logger.warning(
                    f"知识库检索使用fallback (会话: {session.id}, 角色: {current_step.speaker_role_ref}): "
                    f"{knowledge_context.get('error_message', '未知错误')}"
                )
            else:
                logger.info(
                    f"知识库检索成功 (会话: {session.id}, 角色: {current_step.speaker_role_ref}): "
                    f"检索时间 {perf_metrics.get('retrieval_time_ms', 0)}ms, "
                    f"返回 {perf_metrics.get('items_returned', 0)} 条上下文"
                )

        return context

    @staticmethod
    def _build_context_query(session: Session, current_step: FlowStep, history_messages: List[Message]) -> str:
        """
        构建知识库检索的上下文查询

        Args:
            session: 会话对象
            current_step: 当前步骤
            history_messages: 历史消息列表

        Returns:
            str: 构建的上下文查询字符串
        """
        query_parts = []

        # 添加会话主题
        if session.topic:
            query_parts.append(f"主题: {session.topic}")

        # 添加当前步骤的描述
        if current_step.description:
            query_parts.append(f"任务: {current_step.description}")

        # 添加任务类型相关的关键词
        task_keywords = {
            'ask_question': '提问 问题 询问',
            'answer_question': '回答 解答 解释',
            'review_answer': '评价 审查 分析',
            'question': '质疑 反问 挑战',
            'summarize': '总结 概要 归纳',
            'evaluate': '评估 评价 判断',
            'suggest': '建议 推荐 方案',
            'challenge': '挑战 质疑 反驳',
            'support': '支持 论证 证据',
            'conclude': '结论 总结 结果'
        }

        if current_step.task_type in task_keywords:
            query_parts.append(f"类型: {task_keywords[current_step.task_type]}")

        # 添加最近的历史消息内容（最多2条）
        recent_messages = history_messages[-2:] if history_messages else []
        for msg in recent_messages:
            # 检查msg是否为字典类型
            if isinstance(msg, dict):
                content = msg.get('content', '')
                speaker = msg.get('speaker_role', '未知角色')
            elif hasattr(msg, 'content') and hasattr(msg, 'speaker_role'):
                # 如果是Message对象
                content = getattr(msg, 'content', '')
                speaker = getattr(msg, 'speaker_role', '未知角色')
            else:
                # 未知类型，跳过
                continue

            if content and len(content) > 10:
                # 截取消息的关键部分，避免查询过长
                content_preview = content[:200] + "..." if len(content) > 200 else content
                query_parts.append(f"{speaker}: {content_preview}")

        # 合并查询部分
        context_query = " ".join(query_parts)

        # 限制查询总长度，确保不超过RAGFlow API限制
        max_query_length = 800
        if len(context_query) > max_query_length:
            # 智能截取：优先保留主题和任务，截取历史消息部分
            topic_task_parts = []
            history_parts = []

            for part in query_parts:
                if part.startswith(('主题:', '任务:', '类型:')):
                    topic_task_parts.append(part)
                else:
                    history_parts.append(part)

            # 保留主题和任务部分
            context_query = " ".join(topic_task_parts)

            # 添加历史消息部分（截取到长度限制）
            remaining_length = max_query_length - len(context_query)
            if remaining_length > 100 and history_parts:  # 至少保留100字符给历史消息
                history_text = " ".join(history_parts)
                if len(history_text) > remaining_length:
                    history_text = history_text[:remaining_length - 3] + "..."
                context_query += " " + history_text

        return context_query.strip()

    @staticmethod
    def _select_context_messages(session: Session, current_step: FlowStep) -> List[Message]:
        """
        根据上下文范围选择历史消息

        Args:
            session: 会话对象
            current_step: 当前步骤

        Returns:
            List[Message]: 消息列表
        """
        # 基础查询
        base_query = Message.query.filter_by(session_id=session.id)

        # 获取会话角色映射用于角色筛选
        from app.services.session_service import SessionService
        role_mapping = SessionService.get_role_mapping(session.id)

        # 创建角色名称到session_role_id的映射
        role_name_to_session_ids = {}
        for role_ref, role_id in role_mapping.items():
            # 确保role_ref是字符串类型
            if not isinstance(role_ref, str):
                continue  # 跳过非字符串的键

            # 获取SessionRole对象以获取session_role_id
            session_role = SessionRole.query.filter_by(
                session_id=session.id,
                role_ref=role_ref
            ).first()
            if session_role:
                role_name = str(role_ref)  # 确保是字符串
                if role_name not in role_name_to_session_ids:
                    role_name_to_session_ids[role_name] = []
                role_name_to_session_ids[role_name].append(session_role.id)

        # 根据上下文范围获取消息（兼容字符串 / 列表 / 字典）
        scope = current_step.context_scope

        # 1) 字符串类型：处理基础范围 + 角色名 / JSON 字符串
        if isinstance(scope, str):
            if scope == 'none':
                return []

            elif scope == 'last_message':
                return base_query.order_by(Message.created_at.desc()).limit(1).all()

            elif scope == 'last_round':
                # 获取当前轮次的最后一条消息
                last_round_message = base_query.filter(
                    Message.round_index == session.current_round - 1
                ).order_by(Message.created_at.desc()).first()

                if last_round_message:
                    # 获取该轮次的所有消息
                    return base_query.filter(
                        and_(
                            Message.round_index == session.current_round - 1
                        )
                    ).order_by(Message.created_at.asc()).all()
                return []

            elif scope == 'last_n_messages':
                n = current_step.context_param.get('n', 5)
                return base_query.order_by(Message.created_at.desc()).limit(n).all()

            
            # 角色筛选：单个角色名或 JSON 字符串数组
            role_names = []

            # 单个角色名（向后兼容）
            if scope in role_name_to_session_ids:
                role_names = [scope]
            else:
                # JSON 字符串形式的多个角色名
                try:
                    parsed_scope = json.loads(scope) if scope else []
                    if isinstance(parsed_scope, list):
                        role_names = [
                            name for name in parsed_scope
                            if isinstance(name, str) and name in role_name_to_session_ids
                        ]
                except (json.JSONDecodeError, TypeError, ValueError):
                    # 不是 JSON 格式或类型不匹配，忽略
                    pass

            if role_names:
                all_session_role_ids = []
                for role_name in role_names:
                    all_session_role_ids.extend(role_name_to_session_ids[role_name])

                return base_query.filter(
                    Message.speaker_session_role_id.in_(all_session_role_ids)
                ).order_by(Message.created_at.asc()).all()

            return []

        # 2) 列表类型：直接视为角色名数组
        elif isinstance(scope, list):
            role_names = [
                name for name in scope
                if isinstance(name, str) and name in role_name_to_session_ids
            ]
            if role_names:
                all_session_role_ids = []
                for role_name in role_names:
                    all_session_role_ids.extend(role_name_to_session_ids[role_name])

                return base_query.filter(
                    Message.speaker_session_role_id.in_(all_session_role_ids)
                ).order_by(Message.created_at.asc()).all()

            return []

        # 3) 字典类型：使用 key 作为角色名列表（预留扩展）
        elif isinstance(scope, dict):
            role_names = [
                name for name in scope.keys()
                if isinstance(name, str) and name in role_name_to_session_ids
            ]
            if role_names:
                all_session_role_ids = []
                for role_name in role_names:
                    all_session_role_ids.extend(role_name_to_session_ids[role_name])

                return base_query.filter(
                    Message.speaker_session_role_id.in_(all_session_role_ids)
                ).order_by(Message.created_at.asc()).all()

            return []

        # 其他未知类型：不提供上下文
        return []

    @staticmethod
    def _build_prompt(role: Role, step: FlowStep, context: Dict[str, Any]) -> str:
        """
        构建LLM提示词（复杂版本，保留向后兼容）

        Args:
            role: 发言角色
            step: 当前步骤
            context: 上下文信息

        Returns:
            str: 提示词内容
        """
        # 角色信息
        role_info = f"""
你是{role.name}。
角色描述：{role.description}
发言风格：{role.style}
关注点：{', '.join(role.focus_points_list)}
""".strip()

        # 任务信息
        task_info = f"""
任务类型：{step.task_type}
任务描述：{step.description if step.description else '无'}
""".strip()

        # 上下文信息
        context_info = f"""
会话主题：{context['session_topic']}
当前轮次：{context['current_round']}
已执行步骤数：{context['step_count']}
""".strip()

        # 历史消息
        history_info = ""
        if context['history_messages']:
            history_info = "\n之前的对话：\n"
            for msg in context['history_messages']:
                # 检查msg是否为字典类型
                if isinstance(msg, dict):
                    speaker = msg.get('speaker_role') or '未知角色'
                    content = msg.get('content', '')
                elif hasattr(msg, 'speaker_role') and hasattr(msg, 'content'):
                    # 如果是Message对象
                    speaker = getattr(msg, 'speaker_role') or '未知角色'
                    content = getattr(msg, 'content', '')
                else:
                    # 未知类型，跳过
                    continue

                content = content[:100] + "..." if len(content) > 100 else content
                history_info += f"{speaker}: {content}\n"

        # 新增：知识库上下文
        knowledge_info = ""
        knowledge_context = context.get('knowledge_base', {})
        if knowledge_context and not knowledge_context.get('fallback_used', False):
            retrieved_context = knowledge_context.get('retrieved_context', [])
            if retrieved_context:
                knowledge_info = "\n相关知识库参考：\n"
                for idx, kb_item in enumerate(retrieved_context, 1):
                    kb_name = kb_item.get('knowledge_base_name', '未知知识库')
                    content = kb_item.get('content', '')[:300] + "..." if len(kb_item.get('content', '')) > 300 else kb_item.get('content', '')
                    confidence_score = kb_item.get('confidence_score', 0.0)

                    knowledge_info += f"[{idx}] {kb_name} (置信度: {confidence_score:.2f}): {content}\n"
        elif knowledge_context and knowledge_context.get('fallback_used', False):
            error_msg = knowledge_context.get('error_message', '知识库检索失败')
            knowledge_info = f"\n注：{error_msg}，请基于自身知识进行回答。\n"

        # 组合提示词
        prompt = f"""{role_info}

{task_info}

{context_info}

{history_info}

{knowledge_info}

请根据你的角色设定和当前任务，结合提供的知识库参考信息，发表你的观点。"""

        return prompt

    @staticmethod
    def _build_simple_prompt(role: Role, step: FlowStep, context: Dict[str, Any]) -> str:
        """
        构建简单的LLM提示词，类似LLM测试页面

        Args:
            role: 发言角色
            step: 当前步骤
            context: 上下文信息

        Returns:
            str: 简化的提示词内容
        """
        # 简单的角色和任务提示
        prompt_parts = []

        # 基本角色信息
        if role and hasattr(role, 'name'):
            role_desc = f""
            if hasattr(role, 'prompt') and role.prompt:
                role_desc += f"{role.prompt}"
            elif hasattr(role, 'description') and role.description:
                role_desc += f"描述：{role.description}"
            prompt_parts.append(role_desc)

        # 条件性会话主题：只有选择了__TOPIC__策略时才包含
        session_topic = context.get('session_topic', '').strip()
        if session_topic and FlowEngineService._has_topic_context(step):
            prompt_parts.append(f"会话主题：{session_topic}")


        # 添加上下文历史消息（如果有的话）
        history_messages = context.get('history_messages', [])
        if history_messages:
            context_section = FlowEngineService._format_context_for_prompt(history_messages)
            if context_section:
                prompt_parts.append(context_section)

        # 新增：添加知识库上下文
        knowledge_context = context.get('knowledge_base', {})
        if knowledge_context and not knowledge_context.get('fallback_used', False):
            retrieved_context = knowledge_context.get('retrieved_context', [])
            if retrieved_context:
                kb_section = FlowEngineService._format_knowledge_base_for_prompt(retrieved_context)
                if kb_section:
                    prompt_parts.append(kb_section)
        elif knowledge_context and knowledge_context.get('fallback_used', False):
            # 如果知识库检索失败，添加提示信息
            error_msg = knowledge_context.get('error_message', '知识库检索失败')
            prompt_parts.append(f"注：{error_msg}，请基于自身知识进行回答。")

        return " ".join(prompt_parts)

    @staticmethod
    def _format_context_for_prompt(history_messages: List[Dict[str, Any]]) -> str:
        """
        将历史消息格式化为适合LLM提示词的上下文字符串

        Args:
            history_messages: 历史消息列表，每个消息包含 speaker_role, content, round_index 等

        Returns:
            str: 格式化后的上下文字符串
        """
        if not history_messages:
            return ""

        context_parts = []
        context_parts.append("相关对话背景：")

        for msg in history_messages:
            # 检查msg是否为字典类型
            if isinstance(msg, dict):
                speaker = msg.get('speaker_role', '未知角色')
                content = msg.get('content', '')
                round_idx = msg.get('round_index', 1)
            elif hasattr(msg, 'speaker_role') and hasattr(msg, 'content'):
                # 如果是Message对象
                speaker = getattr(msg, 'speaker_role', '未知角色')
                content = getattr(msg, 'content', '')
                round_idx = getattr(msg, 'round_index', 1)
            else:
                # 未知类型，跳过
                continue

            if content:
                context_parts.append(f"{speaker}说：{content}")

        return " ".join(context_parts)

    @staticmethod
    def _format_knowledge_base_for_prompt(retrieved_context: List[Dict[str, Any]]) -> str:
        """
        将检索到的知识库上下文格式化为适合LLM提示词的字符串

        Args:
            retrieved_context: 检索到的知识库上下文列表

        Returns:
            str: 格式化后的知识库上下文字符串
        """
        if not retrieved_context:
            return ""

        context_parts = []
        context_parts.append("相关知识库参考：")

        for idx, kb_item in enumerate(retrieved_context, 1):
            kb_name = kb_item.get('knowledge_base_name', '未知知识库')
            content = kb_item.get('content', '')
            confidence_score = kb_item.get('confidence_score', 0.0)
            references = kb_item.get('references', [])

            if content:
                # 添加知识库标识和置信度
                context_parts.append(
                    f"[{idx}] 来源：{kb_name} (置信度: {confidence_score:.2f})\n"
                    f"内容：{content}"
                )

                # 添加引用信息（如果有）
                if references:
                    ref_texts = []
                    for ref in references[:3]:  # 最多显示3个引用
                        if isinstance(ref, dict):
                            title = ref.get('title', '') or ref.get('name', '')
                            if title:
                                ref_texts.append(title)
                        elif isinstance(ref, str):
                            ref_texts.append(ref[:50])  # 截取字符串引用

                    if ref_texts:
                        context_parts.append(f"参考：{', '.join(ref_texts)}")

                context_parts.append("")  # 添加空行分隔

        return "\n".join(context_parts).strip()

    @staticmethod
    def _has_topic_context(step: FlowStep) -> bool:
        """检查步骤是否选择了预设议题上下文策略"""
        if not step or not step.context_scope:
            return False

        context_scope = step.context_scope

        # 处理JSON数组格式
        if isinstance(context_scope, str):
            try:
                import json
                parsed = json.loads(context_scope)
                if isinstance(parsed, list):
                    context_scope = parsed
            except:
                # 如果不是JSON，保持原字符串
                pass

        # 检查是否包含__TOPIC__
        if isinstance(context_scope, list):
            return '__TOPIC__' in context_scope
        else:
            return context_scope == '__TOPIC__'

    @staticmethod
    def _get_target_session_role_id(session_id: int, target_role_ref: Optional[str]) -> Optional[int]:
        """
        获取目标角色的会话角色ID

        Args:
            session_id: 会话ID
            target_role_ref: 目标角色引用

        Returns:
            Optional[int]: 目标会话角色ID
        """
        if not target_role_ref:
            return None

        target_role = SessionService.get_session_role_by_ref(session_id, target_role_ref)
        return target_role.id if target_role else None

    @staticmethod
    def _get_reply_to_message_id(session: Session, current_step: FlowStep) -> Optional[int]:
        """
        获取回复消息ID

        Args:
            session: 会话对象
            current_step: 当前步骤

        Returns:
            Optional[int]: 回复消息ID
        """
        # 获取上一条消息作为回复目标
        last_message = Message.query.filter_by(session_id=session.id).order_by(Message.created_at.desc()).first()
        return last_message.id if last_message else None

    @staticmethod
    def _generate_content_summary(content: str) -> str:
        """
        生成内容摘要

        Args:
            content: 原始内容

        Returns:
            str: 摘要内容
        """
        # 简单的摘要逻辑，后续可以替换为更复杂的算法
        if len(content) <= 100:
            return content
        return content[:97] + "..."

    @staticmethod
    def _determine_message_section(step: FlowStep) -> str:
        """
        确定消息的阶段/小节

        Args:
            step: 当前步骤

        Returns:
            str: 阶段名称
        """
        task_type_to_section = {
            'ask_question': '提问阶段',
            'answer_question': '回答阶段',
            'review_answer': '点评阶段',
            'question': '质疑阶段',
            'summarize': '总结阶段',
            'evaluate': '评估阶段',
            'suggest': '建议阶段',
            'challenge': '挑战阶段',
            'support': '支持阶段',
            'conclude': '结论阶段'
        }
        return task_type_to_section.get(step.task_type, '讨论阶段')

    @staticmethod
    def _update_session_after_step_execution(session: Session, executed_step: FlowStep) -> None:
        """
        步骤执行后更新会话状态

        Args:
            session: 会话对象
            executed_step: 已执行的步骤
        """
        # 更新执行计数
        session.executed_steps_count += 1
        session.updated_at = datetime.utcnow()

        # 检查是否需要进入下一轮
        if FlowEngineService._should_start_new_round(session, executed_step):
            session.current_round += 1

        # 确定下一步骤
        next_step_id = FlowEngineService._determine_next_step(session, executed_step)
        if next_step_id:
            session.current_step_id = next_step_id
        else:
            # 没有下一步骤，结束会话
            session.status = 'finished'
            session.ended_at = datetime.utcnow()

    @staticmethod
    def _should_start_new_round(session: Session, step: FlowStep) -> bool:
        """
        判断是否应该开始新的轮次

        Args:
            session: 会话对象
            step: 当前步骤

        Returns:
            bool: 是否开始新轮次
        """
        # 简单的逻辑：当执行到总结类型的步骤时，开始新轮次
        return step.task_type in ['summarize', 'conclude']

    @staticmethod
    def _check_exit_condition(session: Session, current_step: FlowStep) -> bool:
        """
        检查当前步骤是否满足退出条件

        当前主要支持基于LLM结构化输出的退出条件：
        - type: 'llm_accept_flag'
          要求当前步骤对应的发言内容是JSON，并包含布尔字段 `accept`
          当 accept 为 True 时视为满足退出条件
        """
        logic_config = current_step.logic_config or {}
        exit_config = logic_config.get('exit_condition') if isinstance(logic_config, dict) else None

        if not exit_config or not isinstance(exit_config, dict):
            return False

        condition_type = exit_config.get('type')

        # 基于LLM输出的接受标志
        if condition_type == 'llm_accept_flag':
            # 找到当前步骤发言角色对应的会话角色
            speaker_role_ref = current_step.speaker_role_ref
            if not speaker_role_ref:
                return False

            speaker_session_role = SessionService.get_session_role_by_ref(session.id, speaker_role_ref)
            if not speaker_session_role:
                return False

            # 获取该角色在本会话中最新的一条消息（通常就是刚刚生成的这条）
            last_message = (
                Message.query
                .filter_by(session_id=session.id, speaker_session_role_id=speaker_session_role.id)
                .order_by(Message.created_at.desc())
                .first()
            )
            if not last_message or not last_message.content:
                return False

            # 尝试将消息内容解析为JSON，并读取accept字段
            try:
                data = json.loads(last_message.content)
                accept_value = data.get('accept')
                return bool(accept_value is True)
            except (json.JSONDecodeError, TypeError, ValueError):
                # 非JSON或没有accept字段，则认为未满足退出条件
                return False

        # 其他类型的退出条件可以在此扩展
        return False

    @staticmethod
    def _determine_next_step(session: Session, current_step: FlowStep) -> Optional[int]:
        """
        确定下一步骤ID

        Args:
            session: 会话对象
            current_step: 当前步骤

        Returns:
            Optional[int]: 下一步骤ID，如果没有则返回None
        """
        print(f"[DEBUG] 确定下一步骤 - 当前步骤ID: {current_step.id}, 当前轮次: {session.current_round}")

        # 1. 优先检查退出条件：若满足则直接结束会话
        exit_met = FlowEngineService._check_exit_condition(session, current_step)
        print(f"[DEBUG] 退出条件检查结果: {exit_met}")
        if exit_met:
            print("[DEBUG] 满足退出条件，结束会话")
            return None

        # 2. 获取流程模板的所有步骤
        flow_template = FlowTemplate.query.get(session.flow_template_id)
        if not flow_template:
            print("[DEBUG] 流程模板不存在")
            return None

        all_steps = flow_template.steps.order_by(FlowStep.order).all()
        print(f"[DEBUG] 流程模板共有 {len(all_steps)} 个步骤")

        # 3. 查找当前步骤在列表中的位置
        current_index = None
        for i, step in enumerate(all_steps):
            if step.id == current_step.id:
                current_index = i
                break

        if current_index is None:
            print(f"[DEBUG] 找不到当前步骤 {current_step.id}")
            return None

        print(f"[DEBUG] 当前步骤在列表中的位置: {current_index}")

        # 4. 检查是否有下一步骤（线性推进）
        if current_index < len(all_steps) - 1:
            next_step_id = all_steps[current_index + 1].id
            print(f"[DEBUG] 有下一步骤，返回步骤ID: {next_step_id}")
            return next_step_id

        print("[DEBUG] 当前是最后一步，检查循环配置")

        # 5. 检查循环配置（到达最后一步且未满足退出条件时，决定是否循环到前面）
        loop_config = current_step.loop_config_dict
        print(f"[DEBUG] 循环配置: {loop_config}")

        # 检查logic_config中的循环配置
        logic_config = current_step.logic_config_dict
        print(f"[DEBUG] 逻辑配置: {logic_config}")

        # 从logic_config中获取循环配置
        next_step_order = logic_config.get('next_step_order')
        max_loops = logic_config.get('max_loops', 1)
        exit_condition = logic_config.get('exit_condition')

        print(f"[DEBUG] 下一步顺序: {next_step_order}, 最大循环次数: {max_loops}, 退出条件: {exit_condition}")

        # 检查是否应该循环
        should_loop = (
            next_step_order is not None and
            session.current_round < max_loops and
            exit_condition != "有"  # 如果退出条件不是"有"，则应该循环
        )

        if should_loop:
            print(f"[DEBUG] 应该循环，当前轮次 {session.current_round} < {max_loops}")
            # 返回指定顺序的步骤
            if 1 <= next_step_order <= len(all_steps):
                loop_step_id = all_steps[next_step_order - 1].id
                print(f"[DEBUG] 循环到步骤顺序 {next_step_order}，ID: {loop_step_id}")
                return loop_step_id
            else:
                print(f"[DEBUG] 循环步骤顺序 {next_step_order} 超出范围，循环到第一步")
                return all_steps[0].id if all_steps else None
        else:
            print(f"[DEBUG] 不满足循环条件，结束会话")

        return None

    @staticmethod
    def get_execution_context(session_id: int) -> Dict[str, Any]:
        """
        获取会话执行上下文信息

        Args:
            session_id: 会话ID

        Returns:
            Dict: 执行上下文信息
        """
        session = Session.query.get(session_id)
        if not session:
            raise SessionError(f"会话ID {session_id} 不存在")

        current_step = None
        if session.current_step_id:
            current_step = FlowStep.query.get(session.current_step_id)

        # 获取角色映射
        role_mapping = SessionService.get_role_mapping(session_id)

        # 获取最近的几条消息
        recent_messages = Message.query.filter_by(session_id=session_id)\
            .order_by(Message.created_at.desc()).limit(5).all()

        return {
            'session': {
                'id': session.id,
                'topic': session.topic,
                'status': session.status,
                'current_round': session.current_round,
                'executed_steps_count': session.executed_steps_count
            },
            'current_step': {
                'id': current_step.id if current_step else None,
                'order': current_step.order if current_step else None,
                'speaker_role_ref': current_step.speaker_role_ref if current_step else None,
                'task_type': current_step.task_type if current_step else None,
                'description': current_step.description if current_step else None
            } if current_step else None,
            'role_mapping': role_mapping,
            'recent_messages': [
                {
                    'id': msg.id,
                    'speaker_role': msg.speaker_role.role_detail.name if msg.speaker_role else None,
                    'content': msg.content[:100] + "..." if len(msg.content) > 100 else msg.content,
                    'created_at': msg.created_at.isoformat() if msg.created_at else None
                }
                for msg in recent_messages
            ],
            'flow_template': {
                'id': session.flow_template_id,
                'name': session.flow_template.name if session.flow_template else None,
                'total_steps': len(session.flow_template.steps.all()) if session.flow_template else 0
            }
        }

    @staticmethod
    async def _generate_llm_response(
        role: Role,
        step: FlowStep,
        context: Dict[str, Any],
        llm_provider: str = None
    ) -> str:
        """
        使用LLM服务生成响应内容

        Args:
            role: 发言角色
            step: 当前步骤
            context: 上下文信息
            llm_provider: LLM提供商

        Returns:
            str: 生成的响应内容

        Raises:
            FlowExecutionError: LLM生成失败
        """
        try:
            # 构建角色信息
            role_info = {
                'name': role.name,
                'description': role.description,
                'style': role.style,
                'focus_points': role.focus_points_list if hasattr(role, 'focus_points_list') else []
            }

            # 构建任务信息
            task_info = {
                'task_type': step.task_type,
                'description': step.description or '',
                'session_topic': context.get('session_topic', ''),
                'current_round': context.get('current_round', 1),
                'step_count': context.get('step_count', 0)
            }

            # 获取目标角色信息
            target_role_ref = step.target_role_ref
            if target_role_ref and 'session_roles' in context:
                target_role_id = context['session_roles'].get(target_role_ref)
                if target_role_id:
                    # 通过role_id获取角色信息
                    target_role = Role.query.get(target_role_id)
                    if target_role:
                        task_info['target_role'] = target_role.name

            # 调用LLM服务生成响应
            response = await conversation_llm_service.generate_response_with_context(
                speaker_role=role_info,
                target_role=None,  # 已经在task_info中处理
                session_topic=context.get('session_topic', ''),
                task_type=step.task_type,
                task_description=step.description or '',
                history_messages=context.get('history_messages', []),
                current_round=context.get('current_round', 1),
                step_count=context.get('step_count', 0),
                provider=llm_provider
            )

            # 验证响应质量
            quality_check = await conversation_llm_service.validate_response_quality(
                response, role_info, task_info
            )

            # 如果质量分数过低，记录警告
            if quality_check['quality_score'] < 0.5:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"LLM响应质量较低 (分数: {quality_check['quality_score']}): "
                    f"{', '.join(quality_check['issues'])}"
                )

            return response.content

        except LLMError as e:
            raise FlowExecutionError(f"LLM生成失败: {str(e)}")
        except Exception as e:
            raise FlowExecutionError(f"生成LLM响应时发生错误: {str(e)}")

    @staticmethod
    def _generate_llm_response_sync(
        role: Role,
        step: FlowStep,
        context: Dict[str, Any],
        session: Optional[Session] = None,
        llm_provider: str = None
    ) -> Tuple[str, str]:
        """
        使用LLM服务生成响应内容（同步版本）
        修改为使用简单的CLI-style /api/llm/chat端点

        Args:
            role: 发言角色
            step: 当前步骤
            context: 上下文信息
            session: 会话对象（用于文件记录）
            llm_provider: LLM提供商

        Returns:
            Tuple[str, str]: (提示词, 生成的响应内容)

        Raises:
            FlowExecutionError: LLM生成失败
        """
        # 记录开始时间
        start_time = datetime.utcnow()
        llm_response = None
        error_message = None
        success = False

        try:
            import requests
            import json
            from flask import current_app

            # 构建简单的提示词，类似LLM测试页面
            prompt = FlowEngineService._build_simple_prompt(role, step, context)

            # 记录LLM交互开始
            if session:
                record_llm_interaction(
                    session_id=session.id,
                    role_name=role.name if role else '未知角色',
                    step_id=step.id if step else None,
                    round_index=session.current_round if session else None,
                    prompt=prompt,
                    response="",  # 初始为空，成功后更新
                    provider=llm_provider or 'claude-3-5-sonnet-20241022',
                    success=False,  # 初始为False，成功后更新
                    metadata={
                        'stage': 'started',
                        'task_type': step.task_type if step else None,
                        'session_topic': session.topic if session else None
                    }
                )

            # 构建历史消息
            history_messages = []
            history = context.get('history_messages', [])

            # 添加历史消息到history数组
            for msg in history[-10:]:  # 只取最近10条消息避免上下文过长
                # 检查msg是否为字典类型
                if isinstance(msg, dict):
                    role_name = msg.get('speaker_role', '用户')
                    content = msg.get('content', '')
                elif hasattr(msg, 'speaker_role') and hasattr(msg, 'content'):
                    # 如果是Message对象
                    role_name = getattr(msg, 'speaker_role', '用户')
                    content = getattr(msg, 'content', '')
                else:
                    # 未知类型，跳过
                    continue

                if content:
                    # 将角色名称转换为简单的user/assistant格式
                    msg_role = 'assistant' if role_name != '用户' else 'user'
                    history_messages.append({
                        'role': msg_role,
                        'content': f"{role_name}: {content}"
                    })

            # 调用简单的 /api/llm/chat 端点
            api_url = 'http://localhost:5010/api/llm/chat'

            payload = {
                'message': prompt,
                'history': history_messages,
                'provider': llm_provider
            }

            # 发送请求到LLM聊天端点
            response = requests.post(
                api_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=600
            )

            if response.status_code == 200:
                try:
                    result = response.json()
                    # 添加类型检查以确保result是字典
                    if isinstance(result, dict) and result.get('success') and 'data' in result:
                        llm_response = result['data']['response']
                        success = True

                        # 记录成功的LLM交互
                        if session:
                            end_time = datetime.utcnow()
                        performance_metrics = {
                            'response_time_ms': int((end_time - start_time).total_seconds() * 1000),
                            'history_messages_count': len(history_messages),
                            'prompt_length': len(prompt),
                            'response_length': len(llm_response)
                        }

                        # 保存交互数据供后续补充message_id使用
                        FlowEngineService._last_llm_interaction_data = {
                            'role_name': role.name if role else '未知角色',
                            'step_id': step.id if step else None,
                            'prompt': prompt,
                            'response': llm_response,
                            'provider': llm_provider or 'claude-3-5-sonnet-20241022',
                            'success': True,
                            'performance_metrics': performance_metrics,
                            'metadata': {
                                'stage': 'completed',
                                'task_type': step.task_type if step else None,
                                'session_topic': session.topic if session else None,
                                'api_response_time': result.get('response_time'),
                                'model_used': result.get('model', llm_provider or 'claude-3-5-sonnet-20241022')
                            }
                        }

                        # 先记录一次没有message_id的交互
                        record_llm_interaction(
                            session_id=session.id,
                            role_name=role.name if role else '未知角色',
                            step_id=step.id if step else None,
                            round_index=session.current_round if session else None,
                            prompt=prompt,
                            response=llm_response,
                            provider=llm_provider or 'claude-3-5-sonnet-20241022',
                            success=True,
                            performance_metrics=performance_metrics,
                            metadata={
                                'stage': 'completed',
                                'task_type': step.task_type if step else None,
                                'session_topic': session.topic if session else None,
                                'api_response_time': result.get('response_time'),
                                'model_used': result.get('model', llm_provider or 'claude-3-5-sonnet-20241022'),
                                'message_id_pending': True
                            }
                        )

                        return prompt, llm_response
                    else:
                        # 如果result不是字典或格式不正确，记录详细信息
                        current_app.logger.error(f"LLM API响应格式错误: {type(result)} - {result}")
                        error_message = f"LLM API返回格式错误: 期望字典，实际收到 {type(result)}"
                        raise FlowExecutionError(error_message)
                except (ValueError, json.JSONDecodeError) as e:
                    # JSON解析失败
                    current_app.logger.error(f"LLM API响应JSON解析失败: {e} - 原始响应: {response.text}")
                    error_message = f"LLM API响应JSON解析失败: {str(e)}"
                    raise FlowExecutionError(error_message)
            else:
                error_message = f"LLM API请求失败，状态码: {response.status_code}"
                raise FlowExecutionError(error_message)

        except requests.exceptions.RequestException as e:
            # 网络请求失败，记录错误并抛出异常
            error_message = f"LLM API请求失败: {str(e)}"

            # 记录失败的LLM交互
            if session:
                end_time = datetime.utcnow()
                performance_metrics = {
                    'response_time_ms': int((end_time - start_time).total_seconds() * 1000),
                    'error_type': 'RequestException',
                    'prompt_length': len(prompt) if 'prompt' in locals() else 0
                }

                record_llm_interaction(
                    session_id=session.id,
                    role_name=role.name if role else '未知角色',
                    step_id=step.id if step else None,
                    round_index=session.current_round if session else None,
                    prompt=prompt if 'prompt' in locals() else "",
                    response="",
                    provider=llm_provider or 'claude-3-5-sonnet-20241022',
                    success=False,
                    error_message=error_message,
                    performance_metrics=performance_metrics,
                    metadata={
                        'stage': 'failed',
                        'task_type': step.task_type if step else None,
                        'session_topic': session.topic if session else None,
                        'exception_type': 'RequestException'
                    }
                )

            import logging
            logger = logging.getLogger(__name__)
            logger.error(error_message)
            raise FlowExecutionError(error_message)

        except Exception as e:
            # 其他错误，记录错误并抛出异常
            error_message = f"LLM服务异常: {str(e)}"

            # 记录失败的LLM交互
            if session:
                end_time = datetime.utcnow()
                performance_metrics = {
                    'response_time_ms': int((end_time - start_time).total_seconds() * 1000),
                    'error_type': type(e).__name__,
                    'prompt_length': len(prompt) if 'prompt' in locals() else 0
                }

                record_llm_interaction(
                    session_id=session.id,
                    role_name=role.name if role else '未知角色',
                    step_id=step.id if step else None,
                    round_index=session.current_round if session else None,
                    prompt=prompt if 'prompt' in locals() else "",
                    response="",
                    provider=llm_provider or 'claude-3-5-sonnet-20241022',
                    success=False,
                    error_message=error_message,
                    performance_metrics=performance_metrics,
                    metadata={
                        'stage': 'failed',
                        'task_type': step.task_type if step else None,
                        'session_topic': session.topic if session else None,
                        'exception_type': type(e).__name__
                    }
                )

            import logging
            logger = logging.getLogger(__name__)
            logger.error(error_message)
            raise FlowExecutionError(error_message)

    @staticmethod
    def execute_next_step_sync(session_id: int) -> Tuple[Message, Dict[str, Any]]:
        """
        同步版本的执行下一步骤（用于向后兼容）

        Args:
            session_id: 会话ID

        Returns:
            Tuple[Message, Dict[str, Any]]: (生成的消息, 执行状态信息)
        """
        loop = None
        try:
            # 获取或创建事件循环
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 如果循环正在运行，我们需要在新线程中运行
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, FlowEngineService.execute_next_step(session_id))
                        return future.result()
                else:
                    # 如果循环存在但未运行，直接使用
                    return loop.run_until_complete(FlowEngineService.execute_next_step(session_id))
            except RuntimeError:
                # 没有事件循环，创建新的
                return asyncio.run(FlowEngineService.execute_next_step(session_id))

        except Exception as e:
            if isinstance(e, (SessionError, FlowExecutionError)):
                raise
            raise FlowExecutionError(f"执行步骤失败: {str(e)}")
