from marshmallow import Schema, fields, validate


class MessageSchema(Schema):
    """消息模式"""
    id = fields.Integer(dump_only=True)
    session_id = fields.Integer(dump_only=True)
    speaker_session_role_id = fields.Integer(dump_only=True)
    speaker_role_name = fields.Method('get_speaker_role_name', dump_only=True)
    target_session_role_id = fields.Integer(dump_only=True)
    target_role_name = fields.Method('get_target_role_name', dump_only=True)
    reply_to_message_id = fields.Integer(dump_only=True)
    content = fields.String(required=True, validate=validate.Length(min=1))
    content_summary = fields.String(dump_only=True)
    round_index = fields.Integer(dump_only=True)
    section = fields.String(dump_only=True)
    created_at = fields.DateTime(dump_only=True)

    def get_speaker_role_name(self, obj):
        """获取发言角色名称，支持无角色映射模式"""
        if hasattr(obj, 'get_speaker_role_name'):
            return obj.get_speaker_role_name()
        # Fallback if method doesn't exist
        if hasattr(obj, 'speaker_role') and obj.speaker_role and hasattr(obj.speaker_role, 'role') and obj.speaker_role.role:
            return obj.speaker_role.role.name
        return "未知角色"

    def get_target_role_name(self, obj):
        """获取目标角色名称"""
        if hasattr(obj, 'target_role') and obj.target_role and hasattr(obj.target_role, 'role') and obj.target_role.role:
            return obj.target_role.role.name
        return None


class MessageListSchema(Schema):
    """消息列表模式"""
    messages = fields.List(fields.Nested(MessageSchema()))
    total = fields.Integer()
    page = fields.Integer()
    page_size = fields.Integer()


class MessageQuerySchema(Schema):
    """消息查询参数模式"""
    session_id = fields.Integer(required=True)
    speaker_role_id = fields.Integer()
    target_role_id = fields.Integer()
    round_index = fields.Integer()
    section = fields.String()
    keyword = fields.String()
    page = fields.Integer(missing=1, validate=validate.Range(min=1))
    page_size = fields.Integer(missing=20, validate=validate.Range(min=1, max=100))