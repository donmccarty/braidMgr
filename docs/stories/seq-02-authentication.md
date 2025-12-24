# Sequence 2: Authentication

*Parent: [USER_STORIES.md](../USER_STORIES.md)*

User authentication and session management.

**Depends on**: Sequence 1
**Stories**: 6
**Priority**: MVP

---

## S2-001: User Registration

**Story**: As a new user, I want to register with email and password, so that I can access the application.

**Acceptance Criteria**:
- Registration form (email, password, name)
- Password strength validation (8+ chars, mixed case, number)
- Email uniqueness check
- Confirmation email sent (optional for MVP)
- User created in database with hashed password

**Traces**: WEB-006

---

## S2-002: Email/Password Login

**Story**: As a registered user, I want to log in with email and password, so that I can access my data.

**Acceptance Criteria**:
- Login form (email, password)
- Password verification with bcrypt
- JWT access token issued (15 min expiry)
- Refresh token issued (7 day expiry)
- Tokens stored securely (httpOnly cookies or secure storage)

**Traces**: WEB-006

---

## S2-003: OAuth - Google

**Story**: As a user, I want to log in with Google, so that I don't need a separate password.

**Acceptance Criteria**:
- "Sign in with Google" button
- OAuth 2.0 flow implemented
- User created or linked on first OAuth login
- Email verified flag set from Google
- JWT tokens issued after OAuth success

**Traces**: WEB-006

---

## S2-004: OAuth - Microsoft

**Story**: As a user, I want to log in with Microsoft, so that I can use my work account.

**Acceptance Criteria**:
- "Sign in with Microsoft" button
- Azure AD OAuth 2.0 flow
- User created or linked on first login
- Works with personal and work accounts
- JWT tokens issued after OAuth success

**Traces**: WEB-006

---

## S2-005: Token Refresh

**Story**: As a logged-in user, I want my session to stay active, so that I don't have to log in repeatedly.

**Acceptance Criteria**:
- Refresh token endpoint
- Access token refreshed automatically before expiry
- Refresh token rotation (optional)
- Invalid refresh token requires re-login
- Logout invalidates refresh token

**Traces**: WEB-006

---

## S2-006: Password Reset

**Story**: As a user who forgot my password, I want to reset it, so that I can regain access.

**Acceptance Criteria**:
- "Forgot password" link on login
- Email sent with reset link (1 hour expiry)
- Reset form validates new password
- Old password invalidated
- User notified of password change

**Traces**: WEB-006
