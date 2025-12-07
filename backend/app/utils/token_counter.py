"""
Token计数和长度验证工具

用于LLM输入输出长度限制的验证和管理
"""

import logging
import tiktoken
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)


class TokenCounter:
    """
    Token计数器，用于验证和管理LLM输入输出长度
    """

    def __init__(self):
        """初始化Token计数器"""
        try:
            # 尝试加载Claude的token计算器（使用gpt-3.5-turbo作为近似）
            # 注意：这不是完全准确的Claude token计算，但作为合理的近似
            self.encoding = tiktoken.get_encoding("cl100k_base")  # 适用于多种模型
            self.approximation_note = "使用OpenAI cl100k_base编码进行近似计算"
            logger.info("Token计数器初始化成功，使用cl100k_base编码进行近似计算")
        except Exception as e:
            logger.warning(f"Token编码器初始化失败: {e}，将使用字符数作为近似")
            self.encoding = None
            self.approximation_note = "使用字符数进行近似计算（4字符≈1token）"

    def count_tokens(self, text: str) -> int:
        """
        计算文本的token数量

        Args:
            text: 要计算的文本

        Returns:
            int: token数量
        """
        if not text:
            return 0

        if self.encoding:
            try:
                return len(self.encoding.encode(text))
            except Exception as e:
                logger.warning(f"Token编码失败: {e}，使用字符数近似")

        # 如果编码器不可用，使用字符数近似（4字符≈1token）
        return len(text) // 4

    def count_messages_tokens(self, messages: List[Dict[str, str]]) -> int:
        """
        计算消息列表的总token数量

        Args:
            messages: 消息列表，每个消息包含role和content字段

        Returns:
            int: 总token数量
        """
        total_tokens = 0
        for msg in messages:
            # 计算每个消息的token，包括格式开销
            content = msg.get('content', '')
            role = msg.get('role', '')

            # 内容token
            content_tokens = self.count_tokens(content)
            # 角色和格式开销（每个消息大约有4-6个额外token）
            format_overhead = self.count_tokens(role) + 6

            total_tokens += content_tokens + format_overhead

        return total_tokens

    def validate_input_length(
        self,
        messages: List[Dict[str, str]],
        max_input_tokens: int,
        warning_threshold: int
    ) -> Tuple[bool, Dict[str, int]]:
        """
        验证输入长度是否在限制范围内

        Args:
            messages: 消息列表
            max_input_tokens: 最大输入token限制
            warning_threshold: 警告阈值

        Returns:
            Tuple[bool, Dict]: (是否通过验证, 详细信息)
        """
        token_count = self.count_messages_tokens(messages)

        details = {
            'input_tokens': token_count,
            'max_input_tokens': max_input_tokens,
            'warning_threshold': warning_threshold,
            'exceeds_limit': False,
            'exceeds_warning': False,
            'warning_message': None,
            'error_message': None
        }

        # 检查是否超过最大限制
        if token_count > max_input_tokens:
            details['exceeds_limit'] = True
            details['error_message'] = (
                f"输入token数量({token_count})超过最大限制({max_input_tokens})，"
                f"超出{token_count - max_input_tokens}个tokens。"
            )
            return False, details

        # 检查是否超过警告阈值
        if token_count > warning_threshold:
            details['exceeds_warning'] = True
            details['warning_message'] = (
                f"输入token数量({token_count})接近最大限制({max_input_tokens})，"
                f"建议减少输入内容以优化性能。"
            )

        return True, details

    def truncate_messages_to_fit(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int,
        preserve_system: bool = True
    ) -> Tuple[List[Dict[str, str]], Dict[str, int]]:
        """
        截断消息以适应token限制

        Args:
            messages: 原始消息列表
            max_tokens: 最大token限制
            preserve_system: 是否保留系统消息

        Returns:
            Tuple[List, Dict]: (截断后的消息列表, 截断信息)
        """
        if not messages:
            return [], {'original_tokens': 0, 'remaining_tokens': 0, 'truncated_count': 0}

        original_tokens = self.count_messages_tokens(messages)

        # 如果没有超限，直接返回
        if original_tokens <= max_tokens:
            return messages.copy(), {
                'original_tokens': original_tokens,
                'remaining_tokens': original_tokens,
                'truncated_count': 0
            }

        result_messages = []
        current_tokens = 0
        truncated_count = 0

        # 首先保留系统消息
        system_messages = []
        other_messages = []

        for msg in messages:
            if msg.get('role') == 'system' and preserve_system:
                system_messages.append(msg)
            else:
                other_messages.append(msg)

        # 计算系统消息的token数
        system_tokens = self.count_messages_tokens(system_messages)
        remaining_tokens = max_tokens - system_tokens

        # 处理非系统消息（从后向前保留最近的）
        if remaining_tokens > 0:
            other_messages.reverse()  # 倒序处理，保留最近的

            for msg in other_messages:
                msg_tokens = self.count_messages([msg])

                if current_tokens + msg_tokens <= remaining_tokens:
                    result_messages.append(msg)
                    current_tokens += msg_tokens
                else:
                    truncated_count += 1

            # 恢复原始顺序
            result_messages.reverse()

        # 合并系统消息和保留的其他消息
        final_messages = system_messages + result_messages

        actual_tokens = self.count_messages_tokens(final_messages)

        return final_messages, {
            'original_tokens': original_tokens,
            'remaining_tokens': actual_tokens,
            'truncated_count': truncated_count,
            'system_tokens': system_tokens,
            'other_tokens': actual_tokens - system_tokens
        }

    def get_token_estimate_summary(self, text: str) -> Dict[str, int]:
        """
        获取文本的token估算摘要

        Args:
            text: 要分析的文本

        Returns:
            Dict[str, int]: token估算详情
        """
        tokens = self.count_tokens(text)
        characters = len(text)

        return {
            'tokens': tokens,
            'characters': characters,
            'tokens_per_character': tokens / max(characters, 1),
            'characters_per_token': characters / max(tokens, 1),
            'approximation_note': self.approximation_note
        }

    def suggest_optimization(self, messages: List[Dict[str, str]], target_tokens: int) -> Dict[str, any]:
        """
        为长消息建议优化方案

        Args:
            messages: 消息列表
            target_tokens: 目标token数量

        Returns:
            Dict: 优化建议
        """
        current_tokens = self.count_messages_tokens(messages)

        if current_tokens <= target_tokens:
            return {
                'needs_optimization': False,
                'current_tokens': current_tokens,
                'target_tokens': target_tokens,
                'savings_needed': 0
            }

        savings_needed = current_tokens - target_tokens

        # 分析各消息的token使用情况
        message_analysis = []
        for i, msg in enumerate(messages):
            msg_tokens = self.count_messages([msg])
            message_analysis.append({
                'index': i,
                'role': msg.get('role', 'unknown'),
                'tokens': msg_tokens,
                'preview': msg.get('content', '')[:100] + "..." if len(msg.get('content', '')) > 100 else msg.get('content', '')
            })

        # 按token数量排序，找出最长的消息
        message_analysis.sort(key=lambda x: x['tokens'], reverse=True)

        # 建议删除或截断的策略
        suggestions = []
        remaining_savings = savings_needed

        for analysis in message_analysis:
            if remaining_savings <= 0:
                break

            if analysis['role'] == 'system':
                # 系统消息不建议删除，但可以简化
                if analysis['tokens'] > 500:
                    suggestions.append({
                        'type': 'simplify_system',
                        'index': analysis['index'],
                        'potential_savings': min(analysis['tokens'] // 2, remaining_savings),
                        'description': f"简化系统消息（当前{analysis['tokens']} tokens）"
                    })
                    remaining_savings -= min(analysis['tokens'] // 2, remaining_savings)
            else:
                # 非系统消息可以删除或截断
                if analysis['tokens'] > remaining_savings:
                    suggestions.append({
                        'type': 'truncate',
                        'index': analysis['index'],
                        'potential_savings': min(analysis['tokens'] - 100, remaining_savings),
                        'description': f"截断消息#{analysis['index']}（当前{analysis['tokens']} tokens）"
                    })
                    remaining_savings -= min(analysis['tokens'] - 100, remaining_savings)
                else:
                    suggestions.append({
                        'type': 'remove',
                        'index': analysis['index'],
                        'potential_savings': analysis['tokens'],
                        'description': f"删除消息#{analysis['index']}（当前{analysis['tokens']} tokens）"
                    })
                    remaining_savings -= analysis['tokens']

        return {
            'needs_optimization': True,
            'current_tokens': current_tokens,
            'target_tokens': target_tokens,
            'savings_needed': savings_needed,
            'message_analysis': message_analysis,
            'optimization_suggestions': suggestions,
            'estimated_achievable_savings': sum(s['potential_savings'] for s in suggestions)
        }


# 全局token计数器实例
token_counter = TokenCounter()


def get_token_counter() -> TokenCounter:
    """
    获取token计数器实例

    Returns:
        TokenCounter: token计数器实例
    """
    return token_counter


def count_text_tokens(text: str) -> int:
    """
    快捷函数：计算文本token数量

    Args:
        text: 要计算的文本

    Returns:
        int: token数量
    """
    return token_counter.count_tokens(text)


def count_messages_tokens(messages: List[Dict[str, str]]) -> int:
    """
    快捷函数：计算消息列表token数量

    Args:
        messages: 消息列表

    Returns:
        int: 总token数量
    """
    return token_counter.count_messages_tokens(messages)