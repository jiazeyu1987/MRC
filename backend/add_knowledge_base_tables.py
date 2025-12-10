#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
添加知识库相关数据表

此脚本用于向现有数据库添加知识库系统所需的数据表：
- knowledge_bases: 知识库主表
- knowledge_base_conversations: 知识库测试对话记录
- role_knowledge_bases: 角色与知识库关联表
- documents: 文档管理表
- document_chunks: 文档块表
- processing_logs: 处理日志表
- chunk_references: 文档块引用表
- conversation_history: 对话历史表
- conversation_templates: 对话模板表
- search_analytics: 搜索分析表
- api_documentation_cache: API文档缓存表

使用方法:
    python add_knowledge_base_tables.py
"""

import os
import sys
import logging
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import (
    KnowledgeBase, KnowledgeBaseConversation, RoleKnowledgeBase,
    Document, DocumentChunk, ProcessingLog, ChunkReference,
    ConversationHistory, ConversationTemplate, SearchAnalytics,
    APIDocumentationCache
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def create_knowledge_base_tables():
    """
    创建知识库相关的数据表
    """
    app = create_app()

    with app.app_context():
        try:
            logger.info("开始创建知识库相关数据表...")

            # 检查表是否已存在
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()

            # 定义需要创建的表
            tables_to_create = [
                ('knowledge_bases', KnowledgeBase),
                ('knowledge_base_conversations', KnowledgeBaseConversation),
                ('role_knowledge_bases', RoleKnowledgeBase),
                ('documents', Document),
                ('document_chunks', DocumentChunk),
                ('processing_logs', ProcessingLog),
                ('chunk_references', ChunkReference),
                ('conversation_history', ConversationHistory),
                ('conversation_templates', ConversationTemplate),
                ('search_analytics', SearchAnalytics),
                ('api_documentation_cache', APIDocumentationCache)
            ]

            created_tables = []
            skipped_tables = []

            for table_name, model_class in tables_to_create:
                if table_name in existing_tables:
                    logger.info(f"表 '{table_name}' 已存在，跳过创建")
                    skipped_tables.append(table_name)
                else:
                    try:
                        model_class.__table__.create(db.engine, checkfirst=True)
                        logger.info(f"成功创建表: {table_name}")
                        created_tables.append(table_name)
                    except Exception as e:
                        logger.error(f"创建表 '{table_name}' 失败: {str(e)}")
                        raise

            logger.info(f"知识库表创建完成!")
            logger.info(f"成功创建 {len(created_tables)} 个表: {', '.join(created_tables)}")
            logger.info(f"跳过 {len(skipped_tables)} 个已存在的表: {', '.join(skipped_tables)}")

            # 验证表创建
            logger.info("验证表创建结果...")
            inspector = db.inspect(db.engine)
            new_tables = inspector.get_table_names()

            missing_tables = []
            for table_name, _ in tables_to_create:
                if table_name not in new_tables:
                    missing_tables.append(table_name)

            if missing_tables:
                logger.error(f"以下表创建失败: {', '.join(missing_tables)}")
                return False
            else:
                logger.info("所有表创建成功!")
                return True

        except Exception as e:
            logger.error(f"创建知识库表时发生错误: {str(e)}")
            db.session.rollback()
            return False


def verify_database_structure():
    """
    验证数据库结构
    """
    app = create_app()

    with app.app_context():
        try:
            logger.info("验证数据库结构...")

            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()

            # 检查必需的表
            required_tables = [
                'knowledge_bases', 'knowledge_base_conversations', 'role_knowledge_bases',
                'documents', 'document_chunks', 'processing_logs', 'chunk_references',
                'conversation_history', 'conversation_templates', 'search_analytics',
                'api_documentation_cache'
            ]

            missing_tables = [table for table in required_tables if table not in tables]

            if missing_tables:
                logger.error(f"缺少以下表: {', '.join(missing_tables)}")
                return False
            else:
                logger.info("所有必需的表都存在!")

                # 显示表结构信息
                for table in required_tables:
                    if table in tables:
                        columns = inspector.get_columns(table)
                        logger.info(f"表 '{table}' 包含 {len(columns)} 个字段")

                return True

        except Exception as e:
            logger.error(f"验证数据库结构时发生错误: {str(e)}")
            return False


def main():
    """
    主函数
    """
    logger.info("=" * 60)
    logger.info("知识库数据表创建脚本")
    logger.info("=" * 60)

    # 创建知识库表
    if create_knowledge_base_tables():
        logger.info("✅ 知识库表创建成功!")

        # 验证数据库结构
        if verify_database_structure():
            logger.info("✅ 数据库结构验证通过!")
            logger.info("知识库系统已准备就绪，可以开始使用!")
        else:
            logger.error("❌ 数据库结构验证失败!")
            sys.exit(1)
    else:
        logger.error("❌ 知识库表创建失败!")
        sys.exit(1)


if __name__ == '__main__':
    main()