#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复flow_steps表缺少knowledge_base_config列的问题
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import FlowStep
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_flow_steps_table():
    """修复flow_steps表"""

    app = create_app()

    try:
        with app.app_context():
            logger.info("开始检查和修复flow_steps表...")

            # 检查列是否已存在
            inspector = db.inspect(db.engine)
            columns = inspector.get_columns('flow_steps')
            column_names = [col['name'] for col in columns]

            logger.info(f"当前flow_steps表的列: {column_names}")

            if 'knowledge_base_config' in column_names:
                logger.info("knowledge_base_config列已存在，跳过修复")
                return True

            if '_knowledge_base_config' in column_names:
                logger.info("_knowledge_base_config列已存在，跳过修复")
                return True

            # 添加新列
            logger.info("添加_knowledge_base_config列到flow_steps表...")

            with db.engine.connect() as conn:
                # 使用原始SQL添加列
                conn.execute(db.text("""
                    ALTER TABLE flow_steps
                    ADD COLUMN _knowledge_base_config TEXT
                """))
                conn.commit()

            logger.info("✅ flow_steps表修复完成")

            # 验证修复结果
            logger.info("验证修复结果...")
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
        logger.error(f"❌ 修复过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    logger.info("开始修复flow_steps表...")

    success = fix_flow_steps_table()

    if success:
        logger.info("🎉 flow_steps表修复完成")
        return 0
    else:
        logger.error("❌ flow_steps表修复失败")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)