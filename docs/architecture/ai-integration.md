# AI Integration

*Parent: [ARCHITECTURE.md](../ARCHITECTURE.md)*

Claude API integration for natural language project queries.

**Key Concepts**:
- Project context injected into system prompt
- RBAC enforced - AI only sees permitted data
- Default scope is current project
- Users can expand scope by asking

---

## Claude Service

```python
# src/services/claude_service.py

import anthropic
from dataclasses import dataclass

@dataclass
class ProjectContext:
    """Context data for AI prompts."""
    project: Project
    items: list[Item]
    budget_metrics: BudgetMetrics
    summary: str  # Formatted for AI


class ClaudeService(BaseService):
    """Integration with Claude API."""

    def __init__(self, config: ClaudeConfig):
        super().__init__(config)
        self.client = anthropic.Anthropic(api_key=config.api_key)
        self.model = "claude-sonnet-4-20250514"

    async def send_message(
        self,
        messages: list[dict],
        context: ProjectContext
    ) -> str:
        """Send message with project context."""
        system_prompt = self._build_system_prompt(context)

        response = await asyncio.to_thread(
            self.client.messages.create,
            model=self.model,
            system=system_prompt,
            messages=messages,
            max_tokens=4096
        )

        return response.content[0].text

    def _build_system_prompt(self, context: ProjectContext) -> str:
        """Build system prompt with project data."""
        return f"""You are an AI assistant for the braidMgr project management application.
You have access to the following project data:

PROJECT: {context.project.name}
CLIENT: {context.project.client_name or 'N/A'}
DATES: {context.project.project_start} to {context.project.project_end}

{context.summary}

Answer questions about this project data. Be concise and specific.
Reference item numbers (e.g., "Item #42") when discussing specific items.
If asked about data outside this project, explain that you only have access to the current project.
"""
```

---

## Context Building

```python
async def build_project_context(
    project_id: UUID,
    user_id: UUID
) -> ProjectContext:
    """Build AI context from project data."""
    # Get project (already permission-checked)
    project = await project_repo.get(project_id)

    # Get items (respects user's view permissions)
    items = await item_repo.get_by_project(project_id)

    # Calculate budget metrics
    budget = await budget_service.calculate(project_id)

    # Format for AI consumption
    summary = format_for_ai(project, items, budget)

    return ProjectContext(
        project=project,
        items=items,
        budget_metrics=budget,
        summary=summary
    )


def format_for_ai(
    project: Project,
    items: list[Item],
    budget: BudgetMetrics
) -> str:
    """Format project data for AI context."""
    sections = []

    # Summary counts
    counts = Counter(item.type for item in items)
    sections.append("ITEM COUNTS:")
    for item_type, count in counts.items():
        sections.append(f"  {item_type}: {count}")

    # Status summary
    open_items = [i for i in items if i.indicator != 'Completed']
    critical = [i for i in open_items if 'Late' in (i.indicator or '')]
    sections.append(f"\nOPEN ITEMS: {len(open_items)}")
    sections.append(f"CRITICAL (Late): {len(critical)}")

    # Budget summary
    if budget.total_budget:
        remaining = budget.total_budget - budget.actual_spend
        sections.append(f"\nBUDGET: ${budget.total_budget:,.0f}")
        sections.append(f"SPENT: ${budget.actual_spend:,.0f}")
        sections.append(f"REMAINING: ${remaining:,.0f}")

    # Active risks
    risks = [i for i in items if i.type == 'Risk' and i.indicator != 'Completed']
    if risks:
        sections.append("\nACTIVE RISKS:")
        for risk in risks[:5]:
            sections.append(f"  #{risk.item_num}: {risk.title}")

    # Overdue actions
    overdue = [i for i in items
               if i.type == 'Action Item'
               and 'Late' in (i.indicator or '')]
    if overdue:
        sections.append("\nOVERDUE ACTIONS:")
        for action in overdue[:5]:
            sections.append(f"  #{action.item_num}: {action.title}")

    return "\n".join(sections)
```

---

## RBAC Enforcement

AI only accesses data the user has permission to view:

```python
@router.post("/chat/sessions/{session_id}/messages")
async def send_chat_message(
    session_id: UUID,
    request: ChatMessageRequest,
    current_user: User = Depends(get_current_user)
):
    # Get session (validates ownership)
    session = await chat_repo.get_session(session_id, current_user.id)

    # Build context with user's permissions
    if session.project_id:
        # Verify user has access to project
        await check_permission(
            current_user.id,
            session.project_id,
            Permission.VIEW_ITEMS
        )
        context = await build_project_context(
            session.project_id,
            current_user.id
        )
    else:
        # Org-wide context - include all user's accessible projects
        context = await build_org_context(
            current_user.org_id,
            current_user.id
        )

    # Send to Claude
    response = await services.claude.send_message(
        messages=request.messages,
        context=context
    )

    return ChatMessageResponse(content=response)
```

---

## Scope Expansion

Default context is current project. Users can expand by asking:

| User Query | Scope |
|------------|-------|
| "What are the open risks?" | Current project |
| "Show me overdue items" | Current project |
| "Across all my projects, what's overdue?" | All accessible projects |
| "Compare budgets across projects" | All accessible projects |

```python
def detect_scope_expansion(message: str) -> bool:
    """Detect if user wants cross-project query."""
    patterns = [
        "across all",
        "all projects",
        "all my projects",
        "every project",
        "compare projects",
        "portfolio",
    ]
    message_lower = message.lower()
    return any(pattern in message_lower for pattern in patterns)
```

---

## Chat Session Storage

```python
# Store session and messages for continuity
@dataclass
class ChatSession:
    id: UUID
    user_id: UUID
    project_id: UUID | None  # None = org-wide
    title: str | None
    created_at: datetime
    updated_at: datetime

@dataclass
class ChatMessage:
    id: UUID
    session_id: UUID
    role: str  # user, assistant, system
    content: str
    context_refs: dict | None  # Referenced items
    token_count: int | None
    created_at: datetime
```

---

## Token Usage Tracking

```python
async def track_token_usage(
    session_id: UUID,
    input_tokens: int,
    output_tokens: int
):
    """Track API usage for cost monitoring."""
    await services.aurora.execute_returning(
        pool,
        """
        INSERT INTO token_usage (session_id, input_tokens, output_tokens, created_at)
        VALUES ($1, $2, $3, NOW())
        RETURNING id
        """,
        session_id, input_tokens, output_tokens
    )

# Monthly usage report
async def get_monthly_usage(org_id: UUID) -> TokenUsage:
    """Get token usage for billing."""
    ...
```
