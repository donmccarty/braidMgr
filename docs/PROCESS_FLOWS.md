# braidMgr Process Flows

*Last updated: 2024-12-24*

This document defines state machines and process flows for braidMgr entities.

---

## Child Documents

| Document | Description |
|----------|-------------|
| [item-lifecycle.md](flows/item-lifecycle.md) | State machine, indicator calculation |
| [auth-flows.md](flows/auth-flows.md) | Login, OAuth, token refresh |
| [crud-flows.md](flows/crud-flows.md) | Item create, update, delete |
| [budget-flows.md](flows/budget-flows.md) | Budget metrics, burn rate |
| [chat-flows.md](flows/chat-flows.md) | AI chat, context building |
| [tenancy-flows.md](flows/tenancy-flows.md) | Multi-tenant request routing |
| [export-flows.md](flows/export-flows.md) | Markdown, CSV export |
| [permission-flows.md](flows/permission-flows.md) | RBAC permission checks |

---

## Flow Summary

### Item Lifecycle

Items transition through states based on dates and completion:

| State | Severity | Trigger |
|-------|----------|---------|
| Draft | - | draft=true |
| Not Started | upcoming | 0%, has dates |
| Starting Soon! | upcoming | Start within 2 weeks |
| Late Start!! | critical | Start passed, 0% |
| In Progress | active | 1-99% complete |
| Trending Late! | warning | Behind schedule |
| Finishing Soon! | active | Finish within 2 weeks |
| Late Finish!! | critical | Finish passed |
| Beyond Deadline!!! | critical | Deadline passed |
| Completed Recently | completed | 100%, within 2 weeks |
| Completed | done | 100%, > 2 weeks ago |

### Authentication

| Flow | Tokens | Expiry |
|------|--------|--------|
| Login/OAuth | Access + Refresh | 15min / 7days |
| Refresh | New Access | 15min |

### RBAC

| Role | Create | Edit | Delete | Manage |
|------|--------|------|--------|--------|
| Admin | Yes | Yes | Yes | Yes |
| PM | Yes | Yes | Yes | No |
| Team | Yes | Assigned | No | No |
| Viewer | No | No | No | No |

---

## Indicator Precedence

When multiple conditions apply, use this priority:

1. Beyond Deadline!!!
2. Late Finish!!
3. Late Start!!
4. Trending Late!
5. Finishing Soon!
6. Starting Soon!
7. In Progress
8. Not Started
9. Completed Recently
10. Completed

---

## Related Documentation

| Document | Purpose |
|----------|---------|
| [REQUIREMENTS.md](REQUIREMENTS.md) | Business requirements |
| [USER_STORIES.md](USER_STORIES.md) | Implementation stories |
| [DATA_MODEL.md](DATA_MODEL.md) | Database schema |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design |
| [PATTERNS.md](PATTERNS.md) | Code patterns |
