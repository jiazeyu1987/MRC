#!/usr/bin/env python3
"""
字数监控工具

用于在后台监控LLM响应的字符统计
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def analyze_character_count(text, max_tokens=8192, context=""):
    """
    分析文本字符统计并打印详细信息

    Args:
        text (str): 要分析的文本
        max_tokens (int): 最大token限制
        context (str): 上下文信息（如角色名称、步骤等）
    """
    if not text:
        return

    char_count = len(text)
    line_count = len(text.split('\n'))
    word_count = len(text.split())

    # 计算中文字符数量
    chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
    chinese_ratio = chinese_chars / char_count * 100 if char_count > 0 else 0

    # 打印统计信息
    print("\n" + "="*60)
    print("Character Count Monitor")
    print("="*60)

    if context:
        print(f"Context: {context}")

    print(f"Characters: {char_count:,}")
    print(f"Lines: {line_count:,}")
    print(f"Words: {word_count:,}")
    print(f"Chinese Characters: {chinese_chars:,} ({chinese_ratio:.1f}%)")
    print(f"Max Tokens: {max_tokens:,}")

    # 字数评估
    if char_count < 1000:
        assessment = "SHORT - Need optimization"
        suggestion = "Consider optimizing prompt for longer response"
    elif char_count < 3000:
        assessment = "MODERATE - Basic needs met"
        suggestion = "Good for general use"
    elif char_count < 6000:
        assessment = "GOOD - Detailed content"
        suggestion = "Satisfies most requirements"
    else:
        assessment = "EXCELLENT - Professional content"
        suggestion = "High quality detailed response"

    print(f"Assessment: {assessment}")
    print(f"Suggestion: {suggestion}")

    # 效率分析
    if max_tokens > 0:
        efficiency = char_count / max_tokens
        print(f"Token Efficiency: {efficiency:.2f} chars/token")

        if efficiency > 0.8:
            print("Efficiency: HIGH - Good token utilization")
        elif efficiency > 0.5:
            print("Efficiency: NORMAL - Expected utilization")
        else:
            print("Efficiency: LOW - Could be optimized")

    # 内容预览
    preview_length = min(200, char_count)
    preview = text[:preview_length] + ("..." if char_count > preview_length else "")
    print(f"Preview: {preview}")

    print("="*60)
    print()

    return {
        'char_count': char_count,
        'line_count': line_count,
        'word_count': word_count,
        'chinese_chars': chinese_chars,
        'chinese_ratio': chinese_ratio,
        'assessment': assessment
    }


def test_monitor():
    """测试监控工具"""
    print("Testing Character Count Monitor...")

    # 测试不同长度的文本
    test_texts = [
        ("Short text", "你好世界"),
        ("Medium text", "这是一段中等长度的中文文本，用来测试字符统计功能。" * 5),
        ("Long text", "这是一个很长的中文文本，" * 100),
    ]

    for context, text in test_texts:
        result = analyze_character_count(text, context=context)
        print(f"Analysis result for {context}: {result['char_count']} characters")


if __name__ == "__main__":
    test_monitor()