# Bug Report - Missing Character Names

## Bug Summary
Character/role names are not being displayed in the Session Theater dialogue panel. Messages show generic "?" avatars and missing or incorrect role names instead of the actual character names participating in the conversation.

## Bug Details

### Expected Behavior
- Messages in the Session Theater should display the correct character/role names for both speakers and targets
- Role avatars should show the first letter of the actual character name
- The system should properly resolve role names from the session role mappings

### Actual Behavior
- Messages show "?" as the avatar letter instead of the role name's first letter
- Some messages display "未知角色" (Unknown Role) instead of the actual character name
- The speaker_role_name and target_role_name fields are not being properly populated from the database relationships

### Steps to Reproduce
1. Start a new session in the Multi-Role Dialogue System
2. Execute several conversation steps
3. Observe the messages in the Session Theater dialogue panel
4. Notice that role names are missing or show "未知角色"
5. Avatar circles show "?" instead of role name initials

### Environment
- **Version**: Current MRC (Multi-Role Chat) system
- **Platform**: Web application (React frontend + Flask backend)
- **Configuration**: SQLite database with SessionRole and Message models

## Impact Assessment

### Severity
- [x] Medium - Feature impaired but workaround exists (users can see messages but not who sent them)

### Affected Users
- All users using the Session Theater to view conversations
- Developers debugging conversation flows
- Educational users monitoring role-based interactions

### Affected Features
- Session Theater message display
- Role identification in conversation flow
- Avatar generation for message speakers
- Target role information display

## Additional Context

### Error Messages
No explicit error messages are shown, but the console may show undefined values for role names.

### Screenshots/Media
Messages show "?" in avatar circles and may display "未知角色" instead of actual character names.

### Related Issues
This issue affects the core user experience of the dialogue system by making it difficult to follow who is speaking in conversations.

## Initial Analysis

### Suspected Root Cause
The MessageSchema is not properly configured to populate speaker_role_name and target_role_name fields from the Message model's relationship methods. The schema defines these as dump-only String fields but doesn't connect them to the model's get_speaker_role_name() method or similar logic.

### Affected Components
- **File**: `backend/app/schemas/message.py`
  - **Class**: `MessageSchema`
  - **Fields**: `speaker_role_name`, `target_role_name`
  - **Issue**: Fields defined but not populated from model methods

- **File**: `backend/app/models/message.py`
  - **Method**: `get_speaker_role_name()`
  - **Issue**: Method exists but not being used by schema
  - **Logic**: Has fallback to "未知角色" when relationships are missing