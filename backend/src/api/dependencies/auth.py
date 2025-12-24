"""
Authentication dependencies for FastAPI routes.

Provides get_current_user and related dependencies for protecting routes.

Usage:
    from src.api.dependencies.auth import get_current_user, RequireAuth

    @router.get("/protected")
    async def protected_route(user: RequireAuth):
        return {"user_id": str(user.id)}
"""

from typing import Annotated, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.domain.auth import CurrentUser, TokenPayload, OrgRole
from src.utils.jwt import decode_access_token
from src.utils.exceptions import AuthenticationError
from src.utils.logging import get_logger

logger = get_logger(__name__)

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[
        Optional[HTTPAuthorizationCredentials],
        Depends(security),
    ],
) -> CurrentUser:
    """
    Extract and validate current user from JWT token.

    Raises HTTP 401 if token is missing, invalid, or expired.

    Usage:
        @router.get("/me")
        async def get_me(user: CurrentUser = Depends(get_current_user)):
            return {"id": user.id}

    Args:
        credentials: Bearer token from Authorization header

    Returns:
        CurrentUser with authenticated user info

    Raises:
        HTTPException: 401 if not authenticated
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Decode and validate JWT
        payload = decode_access_token(credentials.credentials)

        # Build CurrentUser from token claims
        return CurrentUser(
            id=UUID(payload["sub"]),
            email=payload["email"],
            name=payload.get("name", ""),
            org_id=UUID(payload["org_id"]) if payload.get("org_id") else None,
            org_role=OrgRole(payload["org_role"]) if payload.get("org_role") else None,
        )

    except AuthenticationError as e:
        logger.debug("authentication_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(
    credentials: Annotated[
        Optional[HTTPAuthorizationCredentials],
        Depends(security),
    ],
) -> Optional[CurrentUser]:
    """
    Extract current user if token is present, otherwise return None.

    Does not raise if token is missing - returns None instead.
    Still raises if token is present but invalid.

    Usage:
        @router.get("/public")
        async def public_route(user: Optional[CurrentUser] = Depends(get_optional_user)):
            if user:
                return {"greeting": f"Hello {user.name}"}
            return {"greeting": "Hello guest"}

    Args:
        credentials: Bearer token from Authorization header (optional)

    Returns:
        CurrentUser if authenticated, None otherwise

    Raises:
        HTTPException: 401 if token present but invalid
    """
    if credentials is None:
        return None

    try:
        payload = decode_access_token(credentials.credentials)

        return CurrentUser(
            id=UUID(payload["sub"]),
            email=payload["email"],
            name=payload.get("name", ""),
            org_id=UUID(payload["org_id"]) if payload.get("org_id") else None,
            org_role=OrgRole(payload["org_role"]) if payload.get("org_role") else None,
        )

    except AuthenticationError as e:
        # Token present but invalid - still raise
        logger.debug("authentication_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


# Type aliases for cleaner route signatures
RequireAuth = Annotated[CurrentUser, Depends(get_current_user)]
OptionalAuth = Annotated[Optional[CurrentUser], Depends(get_optional_user)]


# =============================================================================
# ROLE-BASED DEPENDENCIES
# =============================================================================


def require_org_role(allowed_roles: list[OrgRole]):
    """
    Create dependency that requires specific organization roles.

    Usage:
        @router.delete("/org/{org_id}")
        async def delete_org(
            org_id: UUID,
            user: RequireAuth,
            _: None = Depends(require_org_role([OrgRole.OWNER])),
        ):
            ...

    Args:
        allowed_roles: List of allowed organization roles

    Returns:
        Dependency function
    """

    async def check_role(user: RequireAuth) -> None:
        if user.org_role is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No organization context",
            )
        if user.org_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

    return check_role


# Convenience role checkers
require_org_owner = require_org_role([OrgRole.OWNER])
require_org_admin = require_org_role([OrgRole.OWNER, OrgRole.ADMIN])
require_org_member = require_org_role([OrgRole.OWNER, OrgRole.ADMIN, OrgRole.MEMBER])
