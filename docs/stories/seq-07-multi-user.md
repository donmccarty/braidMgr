# Sequence 7: Multi-User

*Parent: [USER_STORIES.md](../USER_STORIES.md)*

User roles and permissions.

**Depends on**: Sequence 2
**Stories**: 6
**Priority**: MVP

---

## S7-001: User Profile

**Story**: As a user, I want to manage my profile, so that my information is current.

**Acceptance Criteria**:
- View/edit name, email
- Change password
- Profile picture (optional)
- Notification preferences

**Traces**: ENT-002

---

## S7-002: Role Definition

**Story**: As an admin, I want predefined roles, so that permissions are consistent.

**Acceptance Criteria**:
- Admin: Full access
- ProjectManager: Create/edit projects
- TeamMember: View/edit assigned items
- Viewer: Read-only
- Roles documented

**Traces**: ENT-002

---

## S7-003: Role Assignment

**Story**: As an admin, I want to assign roles to users, so that they have appropriate access.

**Acceptance Criteria**:
- Assign role per project
- Users can have different roles per project
- Role changes take effect immediately
- Audit log of role changes

**Traces**: ENT-002

---

## S7-004: Permission Enforcement

**Story**: As the system, I want to enforce permissions, so that users can only do what they're allowed.

**Acceptance Criteria**:
- API endpoints check permissions
- UI hides unauthorized actions
- 403 returned for denied requests
- Permission check on every request

**Traces**: ENT-002

---

## S7-005: User Invitation

**Story**: As an admin, I want to invite users, so that team members can join.

**Acceptance Criteria**:
- Invite by email
- Invitation email with link
- Role assigned on invitation
- Invitation expires after 7 days

**Traces**: ENT-002

---

## S7-006: Real-Time Collaboration

**Story**: As a team member, I want to see changes made by others, so that I work with current data.

**Acceptance Criteria**:
- Changes by others visible within 30 seconds
- Edit conflict detection and notification
- Data refresh on focus or via manual button
- Optional user presence indicators (Post-MVP)

**Traces**: ENT-009
