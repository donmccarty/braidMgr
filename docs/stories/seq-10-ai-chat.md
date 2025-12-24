# Sequence 10: AI Chat

*Parent: [USER_STORIES.md](../USER_STORIES.md)*

Claude integration for natural language project queries. Users can ask questions about their project data in plain English and get AI-powered insights, summaries, and analysis.

**Depends on**: Sequences 3 (Core Data), 7 (Multi-User)
**Stories**: 5
**Priority**: MVP

**Key Concepts**:
- Default context is current project (focused, accurate responses)
- Users can expand scope by asking ("across all my projects...")
- RBAC enforced - AI only sees data user has permission to access
- Conversation history persisted per user

---

## S10-001: Chat Interface

**Story**: As a user, I want a chat interface, so that I can ask questions naturally.

**Acceptance Criteria**:
- Chat panel embedded in app (side panel or modal)
- Send messages with Enter
- Message history displayed
- Typing indicator during response

**Traces**: ENT-004

---

## S10-002: Claude Integration

**Story**: As the system, I want to call Claude API, so that chat requests get AI responses.

**Acceptance Criteria**:
- Claude API integration via Anthropic SDK
- Context from current project included in system prompt
- Token usage tracked for billing
- Rate limiting applied per user/org

**Traces**: ENT-004

---

## S10-003: Context Scoping

**Story**: As a user, I want the AI to understand my project context, so that responses are relevant.

**Acceptance Criteria**:
- Default context: current project
- Can expand scope by asking ("what about all projects?")
- RBAC enforced (only query accessible data)
- Context scope indicated in UI

**Traces**: ENT-004

---

## S10-004: Chat History

**Story**: As a user, I want chat history saved, so that I can refer to past conversations.

**Acceptance Criteria**:
- Conversations persisted per user
- Retrieve recent conversations
- Delete conversations
- Search history (optional)

**Traces**: ENT-004

---

## S10-005: AI Data Access

**Story**: As the AI, I want access to project data, so that I can answer questions accurately.

**Acceptance Criteria**:
- Items queryable (can reference by number)
- Budget data accessible
- AI can cite specific items in responses
- Data formatted for AI consumption (not raw SQL)

**Traces**: ENT-004
