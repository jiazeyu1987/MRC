#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
添加知识库配置字段的数据库迁移脚本

为flow_steps表添加_knowledge_base_config字段，用于支持知识库检索配置
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from app import db
from app.models import FlowStep
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

def migrate_flow_steps():
    """执行flow_steps表迁移"""

    try:
        with app.app_context():
            logger.info("开始执行flow_steps表的迁移...")

            # 检查列是否已存在
            inspector = db.inspect(db.engine)
            columns = inspector.get_columns('flow_steps')
            column_names = [col['name'] for col in columns]

            if 'knowledge_base_config' in column_names:
                logger.info("knowledge_base_config列已存在，跳过迁移")
                return True

            if '_knowledge_base_config' in column_names:
                logger.info("_knowledge_base_config列已存在，跳过迁移")
                return True

            # 添加新列
            logger.info("添加_knowledge_base_config列到flow_steps表...")

            with db.engine.connect() as conn:
                # 添加knowledge_base_config列
                conn.execute(db.text("""
                    ALTER TABLE flow_steps
                    ADD COLUMN _knowledge_base_config TEXT
                """))

                conn.commit()

            logger.info("✅ flow_steps表迁移完成")

            # 验证迁移结果
            logger.info("验证迁移结果...")
            inspector = db.inspect(db.engine)
            columns = inspector.get_columns('flow_steps')
            column_names = [col['name'] for col in columns]

            if '_knowledge_base_config' in column_names:
                logger.info("✅ _knowledge_base_config列已成功添加")

                # 统计现有步骤数量
                step_count = FlowStep.query.count()
                logger.info(f"现有flow_steps记录数: {step_count}")

                return True
            else:
                logger.error("❌ _knowledge_base_config列添加失败")
                return False

    except Exception as e:
        logger.error(f"❌ 迁移过程中发生错误: {str(e)}")
        return False

def main():
    """主函数"""
    global app

    logger.info("初始化Flask应用...")
    app = create_app()

    logger.info("开始知识库配置字段迁移...")

    success = migrate_flow_steps()

    if success:
        logger.info("🎉 知识库配置字段迁移完成")
        return 0
    else:
        logger.error("❌ 知识库配置字段迁移失败")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)