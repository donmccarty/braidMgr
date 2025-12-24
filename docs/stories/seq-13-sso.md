# Sequence 13: SSO

*Parent: [USER_STORIES.md](../USER_STORIES.md)*

Enterprise Single Sign-On integration. Allows organizations to use their corporate identity provider for authentication.

**Depends on**: Sequences 7 (Multi-User), 8 (Multi-Org)
**Stories**: 2
**Priority**: Post-MVP

**Key Concepts**:
- SAML 2.0 and OIDC supported
- Just-in-time user provisioning
- Per-org SSO configuration
- Can require SSO-only authentication

---

## S13-001: SSO Configuration

**Story**: As an org admin, I want to configure SSO, so that users can log in with their corporate credentials.

**Acceptance Criteria**:
- SSO settings in org admin panel
- Support SAML 2.0 and OIDC protocols
- Identity provider metadata upload
- Test connection before enabling
- Fallback to email/password if SSO fails

**Traces**: ENT-006

---

## S13-002: SSO Login Flow

**Story**: As a user, I want to log in via SSO, so that I use my work credentials.

**Acceptance Criteria**:
- Redirect to IdP login page
- Return with authenticated session
- Auto-provision user on first login
- Map IdP attributes to user profile
- SSO-only mode option per org

**Traces**: ENT-006
