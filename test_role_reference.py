#!/usr/bin/env python3
"""
测试脚本：验证角色引用功能是否正常工作
"""
import sys
import os

# 添加后端路径到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from app import create_app, db
    from app.models import Message, SessionRole

    app = create_app()

    with app.app_context():
        # 测试最新的消息
        latest_message = db.session.query(Message).order_by(Message.id.desc()).first()
        if latest_message:
            print(f"✅ 最新消息 ID: {latest_message.id}")
            print(f"✅ Speaker Session Role ID: {latest_message.speaker_session_role_id}")

            # 测试关联的SessionRole
            if latest_message.speaker_session_role:
                session_role = db.session.query(SessionRole).get(latest_message.speaker_session_role_id)
                if session_role:
                    print(f"✅ SessionRole ID: {session_role.id}")
                    print(f"✅ Role Ref: {session_role.role_ref}")
                    print(f"✅ Role ID: {session_role.role_id}")

                    # 测试我们的新方法
                    speaker_role_ref = latest_message.get_speaker_role_ref()
                    target_role_ref = latest_message.get_target_role_ref()

                    print(f"✅ get_speaker_role_ref(): {speaker_role_ref}")
                    print(f"✅ get_target_role_ref(): {target_role_ref}")

                    # 测试to_dict方法
                    message_dict = latest_message.to_dict()
                    print(f"✅ to_dict() 包含 speaker_role_ref: {'speaker_role_ref' in message_dict}")
                    print(f"✅ to_dict() 包含 target_role_ref: {'target_role_ref' in message_dict}")

                    if message_dict.get('speaker_role_ref') == session_role.role_ref:
                        print("🎉 SUCCESS: 角色引用功能工作正常！")
                        print("📋 前端应该显示:", session_role.role_ref)
                    else:
                        print("❌ ERROR: to_dict()没有返回正确的角色引用")
                else:
                    print("❌ ERROR: SessionRole关联失败")
            else:
                print("❌ ERROR: 消息没有关联的SessionRole")

        else:
            print("❌ ERROR: 数据库中没有消息")

except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("请确保在包含backend目录的项目根目录下运行此脚本")
except Exception as e:
    print(f"❌ 测试失败: {e}")

print("\n🔍 如果测试失败，这表明后端需要重启以加载新的代码修改")