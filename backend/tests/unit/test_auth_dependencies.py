"""
Unit tests for src/api/dependencies/auth.py

Tests authentication dependencies:
- get_current_user extraction and validation
- get_optional_user behavior
- Role-based access control
"""

import pytest
from datetime import timedelta
from unittest.mock import MagicMock
from uuid import UUID

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from src.api.dependencies.auth import (
    get_current_user,
    get_optional_user,
    require_org_role,
    require_org_owner,
    require_org_admin,
    require_org_member,
)
from src.domain.auth import CurrentUser, OrgRole
from src.utils.jwt import create_access_token


class TestGetCurrentUser:
    """Tests for get_current_user dependency."""

    @pytest.mark.asyncio
    async def test_returns_user_from_valid_token(self):
        """Valid token returns CurrentUser with correct claims."""
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        token = create_access_token(
            user_id=user_id,
            email="test@example.com",
            name="Test User",
        )
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token,
        )

        user = await get_current_user(credentials)

        assert isinstance(user, CurrentUser)
        assert str(user.id) == user_id
        assert user.email == "test@example.com"
        assert user.name == "Test User"

    @pytest.mark.asyncio
    async def test_returns_user_with_org_context(self):
        """Token with org claims returns user with org context."""
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        org_id = "660e8400-e29b-41d4-a716-446655440000"
        token = create_access_token(
            user_id=user_id,
            email="test@example.com",
            name="Test User",
            org_id=org_id,
            org_role="admin",
        )
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token,
        )

        user = await get_current_user(credentials)

        assert str(user.org_id) == org_id
        assert user.org_role == OrgRole.ADMIN

    @pytest.mark.asyncio
    async def test_raises_401_when_no_credentials(self):
        """Missing credentials raises 401."""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(None)

        assert exc_info.value.status_code == 401
        assert "Not authenticated" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_raises_401_on_expired_token(self):
        """Expired token raises 401."""
        token = create_access_token(
            user_id="test-uuid",
            email="test@example.com",
            name="Test",
            expires_delta=timedelta(seconds=-1),
        )
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token,
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)

        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_raises_401_on_invalid_token(self):
        """Invalid token raises 401."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid-token",
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)

        assert exc_info.value.status_code == 401


class TestGetOptionalUser:
    """Tests for get_optional_user dependency."""

    @pytest.mark.asyncio
    async def test_returns_user_from_valid_token(self):
        """Valid token returns CurrentUser."""
        token = create_access_token(
            user_id="550e8400-e29b-41d4-a716-446655440000",
            email="test@example.com",
            name="Test User",
        )
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token,
        )

        user = await get_optional_user(credentials)

        assert isinstance(user, CurrentUser)
        assert user.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_returns_none_when_no_credentials(self):
        """Missing credentials returns None (not 401)."""
        user = await get_optional_user(None)
        assert user is None

    @pytest.mark.asyncio
    async def test_raises_401_on_invalid_token(self):
        """Invalid token still raises 401."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid-token",
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_optional_user(credentials)

        assert exc_info.value.status_code == 401


class TestRequireOrgRole:
    """Tests for role-based access control."""

    @pytest.mark.asyncio
    async def test_allows_matching_role(self):
        """User with allowed role passes check."""
        user = CurrentUser(
            id=UUID("550e8400-e29b-41d4-a716-446655440000"),
            email="test@example.com",
            name="Test User",
            org_id=UUID("660e8400-e29b-41d4-a716-446655440000"),
            org_role=OrgRole.ADMIN,
        )

        check_role = require_org_role([OrgRole.ADMIN, OrgRole.OWNER])
        # Should not raise
        await check_role(user)

    @pytest.mark.asyncio
    async def test_raises_403_for_wrong_role(self):
        """User with non-allowed role gets 403."""
        user = CurrentUser(
            id=UUID("550e8400-e29b-41d4-a716-446655440000"),
            email="test@example.com",
            name="Test User",
            org_id=UUID("660e8400-e29b-41d4-a716-446655440000"),
            org_role=OrgRole.MEMBER,
        )

        check_role = require_org_role([OrgRole.OWNER])

        with pytest.raises(HTTPException) as exc_info:
            await check_role(user)

        assert exc_info.value.status_code == 403
        assert "Insufficient permissions" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_raises_403_when_no_org_context(self):
        """User without org context gets 403."""
        user = CurrentUser(
            id=UUID("550e8400-e29b-41d4-a716-446655440000"),
            email="test@example.com",
            name="Test User",
            org_id=None,
            org_role=None,
        )

        check_role = require_org_role([OrgRole.ADMIN])

        with pytest.raises(HTTPException) as exc_info:
            await check_role(user)

        assert exc_info.value.status_code == 403
        assert "No organization context" in exc_info.value.detail


class TestConvenienceRoleCheckers:
    """Tests for pre-defined role checkers."""

    @pytest.mark.asyncio
    async def test_require_org_owner_allows_owner(self):
        """require_org_owner allows owners."""
        user = CurrentUser(
            id=UUID("550e8400-e29b-41d4-a716-446655440000"),
            email="test@example.com",
            name="Test User",
            org_id=UUID("660e8400-e29b-41d4-a716-446655440000"),
            org_role=OrgRole.OWNER,
        )
        await require_org_owner(user)  # Should not raise

    @pytest.mark.asyncio
    async def test_require_org_owner_rejects_admin(self):
        """require_org_owner rejects admins."""
        user = CurrentUser(
            id=UUID("550e8400-e29b-41d4-a716-446655440000"),
            email="test@example.com",
            name="Test User",
            org_id=UUID("660e8400-e29b-41d4-a716-446655440000"),
            org_role=OrgRole.ADMIN,
        )
        with pytest.raises(HTTPException) as exc_info:
            await require_org_owner(user)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_require_org_admin_allows_owner_and_admin(self):
        """require_org_admin allows owners and admins."""
        for role in [OrgRole.OWNER, OrgRole.ADMIN]:
            user = CurrentUser(
                id=UUID("550e8400-e29b-41d4-a716-446655440000"),
                email="test@example.com",
                name="Test User",
                org_id=UUID("660e8400-e29b-41d4-a716-446655440000"),
                org_role=role,
            )
            await require_org_admin(user)  # Should not raise

    @pytest.mark.asyncio
    async def test_require_org_admin_rejects_member(self):
        """require_org_admin rejects members."""
        user = CurrentUser(
            id=UUID("550e8400-e29b-41d4-a716-446655440000"),
            email="test@example.com",
            name="Test User",
            org_id=UUID("660e8400-e29b-41d4-a716-446655440000"),
            org_role=OrgRole.MEMBER,
        )
        with pytest.raises(HTTPException) as exc_info:
            await require_org_admin(user)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_require_org_member_allows_all_roles(self):
        """require_org_member allows all org roles."""
        for role in [OrgRole.OWNER, OrgRole.ADMIN, OrgRole.MEMBER]:
            user = CurrentUser(
                id=UUID("550e8400-e29b-41d4-a716-446655440000"),
                email="test@example.com",
                name="Test User",
                org_id=UUID("660e8400-e29b-41d4-a716-446655440000"),
                org_role=role,
            )
            await require_org_member(user)  # Should not raise
