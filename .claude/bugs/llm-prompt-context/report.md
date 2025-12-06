# Bug Report - LLM Prompt Context Not Applied

## Bug Summary
LLM prompts in the Session Theater dialogue panel are not including proper context strategies despite being configured in FlowStep templates. When context scope is set to specific roles like "打工人" (worker), the prompt sent to LLM should include that role's most recent reply, but currently the context is retrieved but discarded during prompt construction.

## Bug Details

### Expected Behavior
- When a FlowStep has context_scope set to "打工人" (worker role), the LLM prompt should include the worker's most recent LLM reply
- When multiple contexts are selected (e.g., ["打工人", "老师"]), all relevant context messages should be concatenated in the prompt
- Special contexts should work correctly:
  - "全部上下文" (all context): Include all conversation history
  - "预设议题" (preset topics): Include fixed preset topic information
- LLM responses should be contextually relevant based on the configured scope

### Actual Behavior
- FlowStep context_scope configurations are properly stored and retrieved
- Context messages are correctly filtered and retrieved by `_select_context_messages()` function
- **Critical Gap**: The `_build_simple_prompt()` function completely ignores these context messages
- LLM prompts are sent without role-specific context, resulting in generic, context-unaware responses
- LLM debug information shows context was retrieved but not included in the final prompt

### Steps to Reproduce
1. Create a FlowStep with context_scope set to a specific role (e.g., "打工人")
2. Execute a session that reaches this step
3. Check the LLM debug panel to see:
   - Context messages are retrieved correctly in the context building phase
   - Final prompt sent to LLM lacks the retrieved context information
4. Observe that the LLM response doesn't reference previous context from the specified role
5. Test with multiple role contexts and observe they are not concatenated in the prompt

### Environment
- **Version**: Current MRC (Multi-Role Chat) system
- **Platform**: Web application (React frontend + Flask backend)
- **Configuration**: Flow templates with context_scope settings in FlowStep model
- **LLM Integration**: OpenAI API integration via `/api/llm/chat` endpoint

## Impact Assessment

### Severity
- [x] High - Major functionality broken (context strategies not working)

### Affected Users
- All users creating flow templates with context strategies
- Educational users who rely on role-specific context for meaningful conversations
- Developers expecting consistent behavior between context configuration and LLM responses

### Affected Features
- FlowStep context_scope functionality
- LLM prompt construction in flow engine
- Role-specific conversation context
- LLM response quality and relevance
- Multi-role dialogue coherence

## Additional Context

### Error Messages
No explicit error messages are shown, but LLM debug information reveals the disconnect between context retrieval and prompt construction.

### Related Issues
This bug affects the core functionality of the multi-role dialogue system by making context strategies ineffective, reducing conversation quality and role coherence.

## Initial Analysis

### Suspected Root Cause
The bug is in the `_build_simple_prompt()` function in `backend/app/services/flow_engine_service.py`. While the system correctly retrieves context messages based on context_scope settings, the prompt building function completely ignores the `context['history_messages']` that contains the filtered context.

### Affected Components
- **File**: `backend/app/services/flow_engine_service.py`
  - **Function**: `_build_simple_prompt()` (lines ~385-427)
  - **Issue**: Ignores context['history_messages'] when constructing LLM prompts
  - **Impact**: Context strategies configured in FlowStep are not applied

- **File**: `backend/app/services/flow_engine_service.py`
  - **Function**: `_generate_llm_response_sync()` (lines ~827-917)
  - **Issue**: Calls `_build_simple_prompt()` but doesn't integrate retrieved context into final prompt
  - **Impact**: LLM receives generic prompts without role-specific context

- **File**: `backend/app/models/flow.py`
  - **Model**: `FlowStep`
  - **Field**: `context_scope`
  - **Status**: Configuration works correctly, but not utilized in prompt construction