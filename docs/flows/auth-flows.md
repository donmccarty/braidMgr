# Authentication Flows

*Parent: [PROCESS_FLOWS.md](../PROCESS_FLOWS.md)*

Login, OAuth, and token refresh flows.

**Key Concepts**:
- JWT access tokens (15 min) + refresh tokens (7 days)
- OAuth support for Google and Microsoft
- Refresh before access token expiry
- Redirect to login on refresh failure

---

## Email/Password Login

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as API
    participant D as Database

    U->>F: Enter email/password
    F->>A: POST /auth/login
    A->>D: Find user by email
    D-->>A: User record
    A->>A: Verify password (bcrypt)
    alt Password valid
        A->>A: Generate JWT access token
        A->>A: Generate refresh token
        A->>D: Store refresh token
        A-->>F: {access_token, refresh_token}
        F->>F: Store tokens
        F-->>U: Redirect to dashboard
    else Password invalid
        A-->>F: 401 Unauthorized
        F-->>U: Show error
    end
```

---

## OAuth Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as API
    participant O as OAuth Provider

    U->>F: Click "Sign in with Google"
    F->>O: Redirect to OAuth consent
    U->>O: Grant consent
    O->>F: Redirect with auth code
    F->>A: POST /auth/oauth/callback
    A->>O: Exchange code for tokens
    O-->>A: {access_token, id_token}
    A->>A: Validate id_token
    A->>D: Find or create user
    A->>A: Generate JWT tokens
    A-->>F: {access_token, refresh_token}
    F-->>U: Redirect to dashboard
```

**OAuth Providers**:
- Google: scopes = email, profile
- Microsoft: scopes = User.Read

---

## Token Refresh

```mermaid
sequenceDiagram
    participant F as Frontend
    participant A as API
    participant D as Database

    F->>F: Access token expiring
    F->>A: POST /auth/refresh
    A->>D: Validate refresh token
    alt Token valid
        A->>A: Generate new access token
        A-->>F: {access_token}
        F->>F: Update stored token
    else Token invalid/expired
        A-->>F: 401 Unauthorized
        F->>F: Clear tokens
        F-->>U: Redirect to login
    end
```

---

## Token Storage

| Token | Storage | Why |
|-------|---------|-----|
| Access token | Memory | Short-lived, XSS vulnerable but expires fast |
| Refresh token | httpOnly cookie | Not accessible to JavaScript |

---

## Frontend Token Management

```typescript
// Proactive refresh before expiry
const REFRESH_MARGIN_MS = 60 * 1000; // 1 minute before expiry

function scheduleTokenRefresh(expiresAt: number) {
    const refreshAt = expiresAt - REFRESH_MARGIN_MS;
    const delay = refreshAt - Date.now();

    if (delay > 0) {
        setTimeout(async () => {
            try {
                await refreshAccessToken();
            } catch {
                // Refresh failed, redirect to login
                window.location.href = '/login';
            }
        }, delay);
    }
}
```
