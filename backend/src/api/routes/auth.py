"""
Authentication API routes.

Handles user registration, login, token refresh, password reset, and OAuth.

Endpoints:
    POST /auth/register - Create new account
    POST /auth/login - Email/password login
    POST /auth/refresh - Refresh access token
    POST /auth/logout - Revoke refresh token
    POST /auth/forgot-password - Request password reset
    POST /auth/reset-password - Reset password with token
    GET /auth/me - Get current user info
"""

from fastapi import APIRouter, Request, Response, HTTPException, status

from src.api.dependencies.auth import RequireAuth
from src.api.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    AuthResponse,
    TokenResponse,
    MessageResponse,
    UserResponse,
    CurrentUserResponse,
)
from src.config import get_config
from src.services import services
from src.services.auth_service import AuthService
from src.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _get_auth_service() -> AuthService:
    """Get auth service instance."""
    return AuthService(services.aurora)


def _get_client_info(request: Request) -> tuple[str | None, str | None]:
    """Extract client IP and user agent from request."""
    # Get real IP from X-Forwarded-For or client host
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip_address = forwarded.split(",")[0].strip()
    else:
        ip_address = request.client.host if request.client else None

    user_agent = request.headers.get("User-Agent")
    return ip_address, user_agent


# =============================================================================
# REGISTRATION
# =============================================================================


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new account",
    description="Create a new user account with email and password.",
)
async def register(
    request: Request,
    body: RegisterRequest,
    response: Response,
):
    """
    Register a new user account.

    Returns JWT tokens on success. Refresh token is also set as httpOnly cookie.
    """
    ip_address, user_agent = _get_client_info(request)

    auth_service = _get_auth_service()
    result = await auth_service.register(
        email=body.email,
        password=body.password,
        name=body.name,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error,
        )

    # Set refresh token as httpOnly cookie
    _set_refresh_cookie(response, result.refresh_token)

    config = get_config()
    return AuthResponse(
        access_token=result.access_token,
        token_type="bearer",
        expires_in=config.application.auth.access_token_expiry_minutes * 60,
        user=UserResponse(
            id=result.user.id,
            email=result.user.email,
            name=result.user.name,
            avatar_url=result.user.avatar_url,
            email_verified=result.user.email_verified,
            created_at=result.user.created_at,
        ),
    )


# =============================================================================
# LOGIN
# =============================================================================


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Login with email/password",
    description="Authenticate with email and password to get JWT tokens.",
)
async def login(
    request: Request,
    body: LoginRequest,
    response: Response,
):
    """
    Authenticate user with email and password.

    Returns JWT tokens on success. Refresh token is also set as httpOnly cookie.
    Rate limited after failed attempts.
    """
    ip_address, user_agent = _get_client_info(request)

    auth_service = _get_auth_service()
    result = await auth_service.login(
        email=body.email,
        password=body.password,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result.error,
        )

    # Set refresh token as httpOnly cookie
    _set_refresh_cookie(response, result.refresh_token)

    config = get_config()
    return AuthResponse(
        access_token=result.access_token,
        token_type="bearer",
        expires_in=config.application.auth.access_token_expiry_minutes * 60,
        user=UserResponse(
            id=result.user.id,
            email=result.user.email,
            name=result.user.name,
            avatar_url=result.user.avatar_url,
            email_verified=result.user.email_verified,
            created_at=result.user.created_at,
        ),
    )


# =============================================================================
# TOKEN REFRESH
# =============================================================================


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Get a new access token using refresh token from cookie.",
)
async def refresh_token(
    request: Request,
    response: Response,
):
    """
    Refresh the access token.

    Reads refresh token from httpOnly cookie.
    Returns new access token.
    """
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found",
        )

    ip_address, user_agent = _get_client_info(request)

    auth_service = _get_auth_service()
    result = await auth_service.refresh_access_token(
        refresh_token=refresh_token,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    if not result.success:
        # Clear invalid cookie
        _clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result.error,
        )

    # Update refresh token cookie if rotated
    if result.refresh_token:
        _set_refresh_cookie(response, result.refresh_token)

    config = get_config()
    return TokenResponse(
        access_token=result.access_token,
        token_type="bearer",
        expires_in=config.application.auth.access_token_expiry_minutes * 60,
    )


# =============================================================================
# LOGOUT
# =============================================================================


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout",
    description="Revoke refresh token and clear session.",
)
async def logout(
    request: Request,
    response: Response,
    user: RequireAuth,
):
    """
    Log out the current user.

    Revokes all refresh tokens and clears the refresh cookie.
    """
    refresh_token = request.cookies.get("refresh_token")

    auth_service = _get_auth_service()
    await auth_service.logout(
        user_id=user.id,
        refresh_token=refresh_token,
    )

    _clear_refresh_cookie(response)

    return MessageResponse(message="Logged out successfully")


# =============================================================================
# PASSWORD RESET
# =============================================================================


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Request password reset",
    description="Send password reset email to the user.",
)
async def forgot_password(body: ForgotPasswordRequest):
    """
    Request a password reset email.

    Always returns success to prevent email enumeration.
    """
    auth_service = _get_auth_service()
    success, token = await auth_service.request_password_reset(body.email)

    # TODO: In MVP, token is logged. In production, send email.
    if token:
        logger.info(
            "password_reset_token_for_testing",
            email=body.email,
            token=token,  # Only in development!
        )

    return MessageResponse(
        message="If an account with that email exists, a reset link has been sent."
    )


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Reset password",
    description="Reset password using token from email.",
)
async def reset_password(body: ResetPasswordRequest):
    """
    Reset password using reset token.

    User should login after successful reset.
    """
    auth_service = _get_auth_service()
    result = await auth_service.reset_password(
        email=body.email,
        token=body.token,
        new_password=body.new_password,
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error,
        )

    return MessageResponse(message="Password reset successfully. Please login.")


# =============================================================================
# CURRENT USER
# =============================================================================


@router.get(
    "/me",
    response_model=CurrentUserResponse,
    summary="Get current user",
    description="Get information about the authenticated user.",
)
async def get_me(user: RequireAuth):
    """
    Get current user information.

    Returns user profile from JWT token.
    """
    return CurrentUserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        avatar_url=None,  # Not in token - would need DB lookup
        email_verified=True,  # Assume verified if logged in
        org_id=user.org_id,
        org_role=user.org_role.value if user.org_role else None,
    )


# =============================================================================
# HELPERS
# =============================================================================


def _set_refresh_cookie(response: Response, token: str) -> None:
    """Set refresh token as httpOnly cookie."""
    config = get_config()
    max_age = config.application.auth.refresh_token_expiry_days * 24 * 60 * 60

    response.set_cookie(
        key="refresh_token",
        value=token,
        max_age=max_age,
        httponly=True,
        secure=config.environment != "development",  # HTTPS only in production
        samesite="lax",
        path="/auth",  # Only sent to /auth endpoints
    )


def _clear_refresh_cookie(response: Response) -> None:
    """Clear refresh token cookie."""
    response.delete_cookie(
        key="refresh_token",
        path="/auth",
    )
