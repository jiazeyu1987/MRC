"""
提示词优化工具

用于优化LLM提示词，确保获得更长的响应
"""

import logging
import re

logger = logging.getLogger(__name__)


class PromptOptimizer:
    """提示词优化器"""

    def __init__(self):
        self.character_requirements = {
            'short': 1000,      # 短文本
            'medium': 3000,     # 中等文本
            'long': 6000,       # 长文本
            'professional': 10000  # 专业文档
        }

    def optimize_prompt_for_length(self, original_prompt, target_length='professional'):
        """
        优化提示词以获得更长的响应

        Args:
            original_prompt (str): 原始提示词
            target_length (str): 目标长度类别

        Returns:
            str: 优化后的提示词
        """
        target_chars = self.character_requirements.get(target_length, 10000)

        # 检查原始提示词是否已经有字符数要求
        has_char_requirement = any(
            keyword in original_prompt.lower()
            for keyword in ['字', '字符', '长度', '至少', '不少于']
        )

        # 构建增强的提示词
        if has_char_requirement:
            # 优化现有的字符数要求
            enhanced_prompt = self._enhance_existing_requirements(original_prompt, target_chars)
        else:
            # 添加新的字符数要求
            enhanced_prompt = self._add_length_requirement(original_prompt, target_chars)

        # 添加结构化指导
        enhanced_prompt = self._add_structural_guidance(enhanced_prompt, target_length)

        # 添加质量控制
        enhanced_prompt = self._add_quality_requirements(enhanced_prompt)

        # 添加强制长度要求
        enhanced_prompt = self._add_enforcement_requirements(enhanced_prompt, target_chars)

        logger.info(f"提示词已优化，目标字符数: {target_chars}")

        return enhanced_prompt

    def _enhance_existing_requirements(self, prompt, target_chars):
        """增强现有的字符数要求"""
        # 替换模糊的字符数要求为具体的数字要求
        enhanced = prompt

        # 常见的模糊表述替换
        replacements = [
            (r'需要至少\d+字', f'需要至少{target_chars}字'),
            (r'不少于\d+字', f'不少于{target_chars}字'),
            (r'至少\d+字符', f'至少{target_chars}字符'),
            (r'不少于\d+字符', f'不少于{target_chars}字符'),
            (r'\d+字以上', f'{target_chars}字以上'),
            (r'详细的', f'详细的，确保达到{target_chars}字的篇幅要求'),
        ]

        for pattern, replacement in replacements:
            enhanced = re.sub(pattern, replacement, enhanced)

        # 如果没有找到具体的数字，添加明确要求
        if not re.search(r'\d+', enhanced):
            enhanced = self._add_length_requirement(enhanced, target_chars)

        return enhanced

    def _add_length_requirement(self, prompt, target_chars):
        """添加明确的字符数要求"""
        length_instruction = f"""
**重要长度要求：**
- 必须生成至少{target_chars}汉字的内容
- 内容要详尽、充实，避免简短回答
- 如果需要，可以从多个角度展开论述
- 每个章节都要有足够的细节和深度"""

        return f"{prompt}\n\n{length_instruction}"

    def _add_structural_guidance(self, prompt, target_length):
        """添加结构化指导"""
        if target_length >= 6000:  # 长文档结构指导
            structure_guidance = """
**内容结构指导：**
- 使用清晰的标题和子标题组织内容
- 每个主要部分都要有充分展开（建议300-500字）
- 使用项目符号、编号列表提高可读性
- 包含具体的数据、案例或分析
- 添加总结或结论部分"""
        elif target_length >= 3000:  # 中等文档结构指导
            structure_guidance = """
**内容结构指导：**
- 合理分段，每段150-300字
- 使用小标题分隔不同主题
- 提供具体的信息和例子
- 确保逻辑清晰，层次分明"""
        else:  # 短文档结构指导
            structure_guidance = """
**内容结构指导：**
- 清晰分段，每段100-150字
- 直接回应问题要求
- 提供有用的具体信息"""

        return f"{prompt}\n\n{structure_guidance}"

    def _add_quality_requirements(self, prompt, target_length):
        """添加质量控制要求"""
        quality_requirements = """
**质量要求：**
- 内容准确、专业、有价值
- 避免重复和冗余表达
- 语言流畅，逻辑清晰
- 符合专业文档标准
- 提供切实可行的建议或分析"""

        return f"{prompt}\n\n{quality_requirements}"

    def _add_enforcement_requirements(self, prompt, target_chars):
        """添加强制长度要求"""
        enforcement = f"""
**强制执行要求：**
- 最终输出必须达到或超过{target_chars}字
- 如果内容不足，请自动扩展相关部分
- 绝对不要因为长度限制而牺牲内容质量
- 宁可稍长一些，也不要过短"""

        return f"{prompt}\n\n{enforcement}"

    def create_enhanced_system_prompt(self, role_name, task_type, target_length='professional'):
        """创建增强的系统提示词"""
        target_chars = self.character_requirements.get(target_length, 10000)

        system_prompt = f"""你是{role_name}，专业的{task_type}专家。

**核心要求：**
1. 你的回复必须达到{target_chars}字以上的详细程度
2. 内容要专业、准确、有深度
3. 结构清晰，逻辑严密
4. 提供具体的数据、分析和建议
5. 使用规范的中文表达，避免口语化

**执行标准：**
- 如果用户要求长文档，请创建详尽的专业内容
- 每个部分都要充分展开，提供细节
- 使用标题、子标题组织内容结构
- 确保内容实用性强，能够指导实际工作

**特别注意：**
不要因为追求简洁而牺牲内容的完整性。用户需要详尽的专业内容，请确保每一条信息都有足够的展开和说明。"""

        return system_prompt

    def analyze_prompt_effectiveness(self, prompt):
        """分析提示词的有效性"""
        analysis = {
            'has_length_requirement': False,
            'has_structural_guidance': False,
            'has_quality_requirements': False,
            'estimated_effectiveness': 0.0,
            'suggestions': []
        }

        # 检查字符数要求
        length_keywords = ['字', '字符', '长度', '至少', '不少于', '以上']
        analysis['has_length_requirement'] = any(
            keyword in prompt.lower() for keyword in length_keywords
        )

        # 检查结构指导
        structure_keywords = ['结构', '标题', '分段', '章节', '层次']
        analysis['has_structural_guidance'] = any(
            keyword in prompt.lower() for keyword in structure_keywords
        )

        # 检查质量要求
        quality_keywords = ['质量', '专业', '准确', '逻辑', '标准']
        analysis['has_quality_requirements'] = any(
            keyword in prompt.lower() for keyword in quality_keywords
        )

        # 计算预估效果
        score = 0
        if analysis['has_length_requirement']:
            score += 40
            analysis['suggestions'].append("✅ 包含长度要求")
        else:
            analysis['suggestions'].append("❌ 缺少明确的字符数要求")

        if analysis['has_structural_guidance']:
            score += 30
            analysis['suggestions'].append("✅ 包含结构指导")
        else:
            analysis['suggestions'].append("❌ 缺少内容结构指导")

        if analysis['has_quality_requirements']:
            score += 30
            analysis['suggestions'].append("✅ 包含质量要求")
        else:
            analysis['suggestions'].append("❌ 缺少质量控制要求")

        analysis['estimated_effectiveness'] = score / 100

        return analysis


# 全局提示词优化器实例
prompt_optimizer = PromptOptimizer()


def get_prompt_optimizer():
    """获取提示词优化器实例"""
    return prompt_optimizer


def optimize_prompt_for_long_content(prompt, role_name=None, task_type=None):
    """
    便捷函数：为长内容优化提示词

    Args:
        prompt (str): 原始提示词
        role_name (str): 角色名称
        task_type (str): 任务类型

    Returns:
        str: 优化后的提示词
    """
    optimizer = get_prompt_optimizer()

    # 如果提供了角色和任务类型，创建完整的增强提示词
    if role_name and task_type:
        # 创建增强的系统提示词
        enhanced_system = optimizer.create_enhanced_system_prompt(role_name, task_type)

        # 优化用户提示词
        enhanced_user = optimizer.optimize_prompt_for_length(prompt, 'professional')

        return f"{enhanced_system}\n\n用户要求：\n{enhanced_user}"
    else:
        # 只优化现有提示词
        return optimizer.optimize_prompt_for_length(prompt, 'professional')


def analyze_prompt(prompt):
    """
    便捷函数：分析提示词有效性

    Args:
        prompt (str): 要分析的提示词

    Returns:
        dict: 分析结果
    """
    optimizer = get_prompt_optimizer()
    return optimizer.analyze_prompt_effectiveness(prompt)