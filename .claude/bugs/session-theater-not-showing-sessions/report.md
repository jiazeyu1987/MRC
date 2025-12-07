# Bug Report

## Bug Summary
会话剧场里没有显示已经创建的会话 (Session theater not showing created sessions)

## Bug Details

### Expected Behavior
当用户创建会话后，会话应该出现在"会话管理"页面的会话列表中，用户可以点击进入会话剧场进行对话。

### Actual Behavior
会话管理页面显示空的会话列表，即使已经创建了会话也不会显示。代码中使用 `setSessions([])` 硬编码设置为空数组，导致会话无法显示。

### Steps to Reproduce
1. 启动应用程序：`cd front && npm run dev` 和 `cd backend && python run.py`
2. 导航到"会话管理"页面
3. 点击"新建会话"创建一个新的会话
4. 填写会话信息并提交
5. 会话创建成功，但返回会话管理页面时列表为空
6. 已创建的会话无法在列表中看到，无法进入会话剧场

### Environment
- **Version**: MRC (Multi-Role Dialogue System)
- **Platform**: Windows 10, Node.js + React frontend, Python Flask backend
- **Configuration**: Development environment with Vite dev server

## Impact Assessment

### Severity
- [x] High - Major functionality broken

### Affected Users
所有使用系统的用户无法看到已创建的会话，严重影响核心功能的使用。

### Affected Features
- 会话管理功能
- 会话剧场访问
- 多角色对话流程执行
- 历史记录查看

## Additional Context

### Error Messages
没有明确的错误消息，但会话列表始终为空。

### Screenshots/Media
会话管理页面显示空列表，没有数据展示。

### Related Issues
历史记录页面也存在相同问题（同样使用 `setSessions([])` 硬编码空数组）。

## Initial Analysis

### Suspected Root Cause
在 `MultiRoleDialogSystem.tsx` 文件中，`SessionManagement` 组件和 `HistoryPage` 组件都使用了硬编码的空数组来设置会话状态：

```typescript
// Line 1125 in SessionManagement
setSessions([]); // Temporary empty sessions

// Line 1376 in HistoryPage
setSessions([]); // Temporary empty sessions
```

这导致即使用户创建了会话，前端也不会显示任何会话数据。

### Affected Components
- **File**: `front/src/MultiRoleDialogSystem.tsx`
  - **Function**: `SessionManagement` component (lines 1112-1127)
  - **Function**: `HistoryPage` component (lines 1372-1377)
  - **Issue**: 临时硬编码空数组，未调用真实的API获取会话列表
- **File**: `front/src/api/sessionApi.ts`
  - **Available**: API client functions exist for fetching sessions
  - **Issue**: 已实现的API函数未被使用