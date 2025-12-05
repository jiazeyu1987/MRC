#!/usr/bin/env python3
"""
Database initialization script for Multi-Role Dialogue System
This script creates the necessary database tables and initial data.
"""

import os
import sys
from datetime import datetime

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Initialize the database with tables and basic data"""
    print("正在初始化数据库...")

    try:
        # Import Flask app and models
        from app import create_app, db
        from app.models import Role, FlowTemplate, FlowStep, Session, SessionRole, Message

        # Create Flask app
        app = create_app()

        with app.app_context():
            print("创建数据库表...")

            # Create all tables
            db.create_all()
            print("✅ 数据库表创建成功!")

            # Check if roles already exist
            role_count = Role.query.count()
            print(f"当前数据库中有 {role_count} 个角色")

            if role_count == 0:
                print("创建内置角色...")
                create_builtin_roles()
            else:
                print("角色已存在，跳过创建")

            # Check if flow templates exist
            flow_count = FlowTemplate.query.count()
            print(f"当前数据库中有 {flow_count} 个流程模板")

            if flow_count == 0:
                print("创建内置流程模板...")
                create_builtin_flows()
            else:
                print("流程模板已存在，跳过创建")

        print("\n🎉 数据库初始化完成!")
        print("现在可以启动后端服务器: python run.py")

    except Exception as e:
        print(f"❌ 数据库初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def create_builtin_roles():
    """创建系统预置角色"""
    from app.models import Role

    builtin_roles = [
        {
            'name': '老师',
            'prompt': '你是一位专业的教师，负责教学指导和知识传授。你的风格是鼓励式、引导式、耐心细致。请专注于学习效果、概念理解和实践应用，避免涉及超出教学范围的专业建议。'
        },
        {
            'name': '学生',
            'prompt': '你是一个积极学习的学生，代表学习者视角。你的风格是好奇、求知、有时会犯错误。请专注于知识点掌握、学习方法、实践练习，仅从学习者角度提问，不作专业判断。'
        },
        {
            'name': '专家',
            'prompt': '你是一位具有丰富专业知识和经验的领域专家。你的风格是严谨、专业、有说服力。请专注于专业性、可行性和风险评估，仅提供专业意见，不承担法律责任。'
        },
        {
            'name': '评审员',
            'prompt': '你是一位负责方案评审和质量把控的专业评审人员。你的风格是客观、公正、注重细节。请专注于合规性、质量标准和改进建议，仅提供评审意见，不做最终决策。'
        }
    ]

    for role_data in builtin_roles:
        role = Role(**role_data)
        db.session.add(role)

    db.session.commit()
    print("✅ 系统预置角色创建完成!")

def create_builtin_flows():
    """创建系统预置流程模板"""
    from app.models import FlowTemplate, FlowStep

    # 教学对话模板
    teaching_flow = FlowTemplate(
        name='教学对话模板',
        description='老师提出问题 -> 学生尝试回答 -> 老师点评 -> 老师总结',
        version='1.0.0',
        is_active=True,
        created_at=datetime.utcnow()
    )
    db.session.add(teaching_flow)
    db.session.flush()  # 获取teaching_flow.id

    teaching_steps = [
        {
            'order': 1,
            'speaker_role_ref': '老师',
            'task_type': 'ask_question',
            'context_scope': 'none',
            'description': '老师提出学习问题'
        },
        {
            'order': 2,
            'speaker_role_ref': '学生',
            'target_role_ref': '老师',
            'task_type': 'answer_question',
            'context_scope': 'last_message',
            'description': '学生回答问题'
        },
        {
            'order': 3,
            'speaker_role_ref': '老师',
            'target_role_ref': '学生',
            'task_type': 'review_answer',
            'context_scope': 'last_round',
            'description': '老师点评学生回答'
        },
        {
            'order': 4,
            'speaker_role_ref': '老师',
            'task_type': 'summarize',
            'context_scope': 'all',
            'description': '老师总结知识点'
        }
    ]

    for step_data in teaching_steps:
        step = FlowStep(
            flow_template_id=teaching_flow.id,
            **step_data
        )
        db.session.add(step)

    db.session.commit()
    print("✅ 系统预置流程模板创建完成!")

if __name__ == '__main__':
    main()