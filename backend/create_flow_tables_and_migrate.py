#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
创建flow相关表并添加知识库配置字段

这是一个一站式脚本，用于：
1. 创建所有数据库表（如果不存在）
2. 为flow_steps表添加knowledge_base_config字段（如果不存在）
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from app import db
from app.models import FlowTemplate, FlowStep, KnowledgeBase
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """创建Flask应用"""
    app = Flask(__name__)

    # 基本配置
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///conversations.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    return app

def setup_database():
    """设置数据库并添加必要的字段"""

    try:
        with app.app_context():
            logger.info("开始设置数据库...")

            # 1. 创建所有表（如果不存在）
            logger.info("创建数据库表...")
            db.create_all()
            logger.info("✅ 数据库表创建完成")

            # 2. 检查并添加knowledge_base_config字段
            logger.info("检查flow_steps表结构...")

            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()

            if 'flow_steps' not in tables:
                logger.warning("⚠️  flow_steps表不存在，但db.create_all()应该已创建它")
                return False

            columns = inspector.get_columns('flow_steps')
            column_names = [col['name'] for col in columns]

            logger.info(f"flow_steps表当前列: {column_names}")

            # 检查列是否已存在（检查两种可能的名称）
            if '_knowledge_base_config' in column_names:
                logger.info("✅ _knowledge_base_config列已存在")
                # 继续验证
            elif 'knowledge_base_config' in column_names:
                logger.info("✅ knowledge_base_config列已存在")
                # 继续验证
            else:
                # 添加新列
                logger.info("添加_knowledge_base_config列...")

                with db.engine.connect() as conn:
                    # 添加knowledge_base_config列
                    conn.execute(db.text("""
                        ALTER TABLE flow_steps
                        ADD COLUMN _knowledge_base_config TEXT
                    """))
                    # 使用session而不是conn.commit()
                    db.session.commit()

                logger.info("✅ _knowledge_base_config列添加成功")

            # 3. 验证表结构
            logger.info("验证表结构...")
            inspector = db.inspect(db.engine)
            columns = inspector.get_columns('flow_steps')
            column_names = [col['name'] for col in columns]

            if '_knowledge_base_config' in column_names:
                logger.info("✅ 表结构验证成功")

                # 测试FlowStep模型
                try:
                    # 测试创建一个FlowStep实例来验证模型
                    step = FlowStep()
                    step.knowledge_base_config = {'enabled': True, 'knowledge_base_ids': ['test']}
                    config = step.knowledge_base_config
                    logger.info(f"✅ FlowStep模型测试成功，配置: {config}")

                    # 清理测试实例
                    db.session.rollback()

                except Exception as e:
                    logger.error(f"❌ FlowStep模型测试失败: {str(e)}")
                    return False

                return True
            else:
                logger.error("❌ 表结构验证失败")
                return False

    except Exception as e:
        logger.error(f"❌ 数据库设置过程中发生错误: {str(e)}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        return False

def main():
    """主函数"""
    global app

    logger.info("初始化Flask应用...")
    app = create_app()

    logger.info("开始数据库设置...")

    success = setup_database()

    if success:
        logger.info("🎉 数据库设置完成")
        logger.info("FlowStep模型现在支持知识库配置功能:")
        logger.info("- knowledge_base_config: 存储知识库检索配置")
        logger.info("- is_knowledge_base_enabled(): 检查是否启用知识库")
        logger.info("- validate_knowledge_base_references(): 验证知识库引用")
        logger.info("- FlowTemplateService._validate_knowledge_base_config(): 验证配置")
        return 0
    else:
        logger.error("❌ 数据库设置失败")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)