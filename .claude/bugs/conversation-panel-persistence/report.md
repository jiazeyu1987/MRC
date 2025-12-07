# Bug Report - Conversation Panel Persistence

## Bug Summary

**Status**: Report Created
**Created**: 2025-12-06
**Bug Name**: conversation-panel-persistence

---

## Expected Behavior

The conversation panel in the Session Theater should maintain its state when navigating between browser tabs or pages. Specifically:

- If a user has the conversation panel open and hasn't clicked "结束对话" (End Conversation)
- When switching to other browser tabs or pages and then returning to the "对话剧场" (Session Theater)
- The conversation panel should remain open and display the same content
- Panel state should persist across navigation as long as the conversation hasn't been explicitly ended

## Actual Behavior

The conversation panel loses its state when navigating away from and back to the Session Theater:

- When a user has the conversation panel open
- Switching to other tabs/pages causes the panel to disappear
- Upon returning to the Session Theater, the conversation panel is closed
- User must manually reopen the panel even though the conversation is still active
- This happens regardless of whether "结束对话" was clicked

## Steps to Reproduce

1. Navigate to the Session Theater page (对话剧场)
2. Open an active conversation or start a new one
3. Open the conversation panel (if not already open)
4. **DO NOT** click "结束对话" (End Conversation)
5. Switch to a different browser tab or page
6. Switch back to the Session Theater tab
7. **Observe**: The conversation panel is now closed/disappeared
8. Expected: The conversation panel should still be open

## Environment

- **Platform**: Web application (React frontend + Flask backend)
- **Browser**: All modern browsers (Chrome, Firefox, Safari, Edge)
- **Frontend**: React with state management
- **Component**: Session Theater / Conversation Panel
- **Navigation**: Browser tab switching or internal navigation

## Impact Assessment

### Severity
- [x] Medium - Usability issue affecting user experience

### Affected Users
- All users using the Session Theater feature
- Users who frequently switch between browser tabs while monitoring conversations
- Educational users who need to reference other materials while following conversations

### Affected Features
- Session Theater conversation panel
- State persistence across navigation
- User experience continuity
- Multi-tab workflow efficiency

## Additional Context

### User Impact
This issue creates a disruptive user experience where:
- Users lose their conversation view context when switching tabs
- Multi-tasking workflows are interrupted
- Users must repeatedly reopen panels, reducing efficiency
- Educational scenarios suffer when referencing materials across tabs

### Specific Component Affected
- **File**: `src/components/SessionTheater.tsx`
- **Component**: SessionTheater component
- **Area**: Messages display section (lines 452-497) - the conversation message panel

### Potential Technical Areas
- React component state management for messages array
- Browser localStorage/sessionStorage usage for message persistence
- Component lifecycle management during tab switching
- API data loading and caching strategies
- Navigation event handling for visibility changes

### Related Components
- **SessionTheater.tsx**: Main component with conversation messages display
- **sessionApi**: API client for message loading
- **State Management**: `useState` hooks for messages and session data
- **Message Display**: The conversation panel showing message history

## Initial Analysis

### Current Implementation (from SessionTheater.tsx)

**Message State Management**:
```typescript
const [messages, setMessages] = useState<Message[]>([]);
const [session, setSession] = useState<Session | null>(null);

// Messages are loaded from API on component mount
const loadData = async () => {
  const sessionData = await sessionApi.getSession(sessionId);
  setSession(sessionData);
  const messagesData = await sessionApi.getMessages(sessionId, { page_size: 100 });
  setMessages(messagesData.items);
};
```

**Loading Behavior**:
- Messages are loaded fresh from API every time component mounts
- No local caching or persistence mechanism
- Data is lost when component unmounts during tab switching

### Suspected Root Cause
The issue is caused by React component state being reset when switching browser tabs:

1. **Component Unmounting**: When switching tabs, the SessionTheater component may unmount, losing all message state
2. **No Local Caching**: No localStorage/sessionStorage implementation for message persistence
3. **API Re-fetching**: Messages are reloaded from API on every component mount, causing delays
4. **State Reset**: All conversation state (messages, session data) is reset during tab switches

### Affected Components
- **File**: `src/components/SessionTheater.tsx`
- **Lines**: 18-19 (useState declarations), 59-71 (loadData function), 73 (useEffect for data loading)
- **Issue**: Component state not persisted across tab navigation

### Technical Investigation Needed
- Implement localStorage/sessionStorage for message caching
- Add state persistence for conversation data
- Optimize API loading to use cached data when available
- Handle component lifecycle events during tab switching