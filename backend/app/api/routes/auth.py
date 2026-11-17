"""Authentication routes.

All routes delegate business logic to ``auth_service``; handlers only
validate inputs, call services, and format responses.
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.db.base import get_db
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    MessageResponse,
    RefreshTokenRequest,
    ResetPasswordRequest,
    Token,
    UserRegister,
    UserResponse,
)
from app.services import auth_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


# ---------------------------------------------------------------------------
# POST /register
# ---------------------------------------------------------------------------


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(
    data: UserRegister,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    """Create a new user account.

    Returns the created user's public profile.
    Raises **409** if the email is already registered.
    """
    user = await auth_service.register_user(db, data)
    return UserResponse.model_validate(user)


# ---------------------------------------------------------------------------
# POST /login
# ---------------------------------------------------------------------------


@router.post(
    "/login",
    response_model=Token,
    summary="Obtain access and refresh tokens",
)
async def login(
    db: Annotated[AsyncSession, Depends(get_db)],
    # OAuth2PasswordRequestForm is used so Swagger's "Authorize" button works
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    """Authenticate with *username* (email) and *password*.

    Compatible with OAuth2 password-flow clients.  Returns a JWT access token
    and a refresh token.  Raises **401** on bad credentials.
    """
    user = await auth_service.authenticate_user(
        db, form_data.username, form_data.password
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Embed user_id as subject so we never need to decode the email from the token
    token_data = {"sub": str(user.user_id)}
    return Token(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


# ---------------------------------------------------------------------------
# POST /refresh
# ---------------------------------------------------------------------------


@router.post(
    "/refresh",
    response_model=Token,
    summary="Refresh access token",
)
async def refresh_token(
    body: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Token:
    """Exchange a valid refresh token for a new access + refresh token pair.

    Raises **401** if the refresh token is missing, malformed, or expired.
    """
    payload = decode_token(body.refresh_token)
    if payload is None or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Confirm the user still exists and is not deleted
    try:
        user_id = int(payload["sub"])
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject.",
        )

    user = await auth_service.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    token_data = {"sub": str(user.user_id)}
    return Token(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


# ---------------------------------------------------------------------------
# POST /forgot-password
# ---------------------------------------------------------------------------


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Request a password-reset email",
)
async def forgot_password(
    body: ForgotPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    """Trigger a password-reset email.

    Always responds with **200** to prevent email-enumeration attacks.
    """
    # Service handles both known and unknown emails gracefully
    await auth_service.initiate_password_reset(db, body.email)
    return MessageResponse(
        message="If that email is registered you will receive a reset link shortly."
    )


# ---------------------------------------------------------------------------
# POST /reset-password
# ---------------------------------------------------------------------------


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Apply a new password using a reset token",
)
async def reset_password(
    body: ResetPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    """Set a new password using the signed token from the reset email.

    Raises **400** if the token is invalid, expired, or the account is gone.
    """
    success = await auth_service.reset_user_password(db, body.token, body.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset link is invalid or has expired.",
        )
    return MessageResponse(message="Your password has been updated successfully.")


# ---------------------------------------------------------------------------
# GET /me
# ---------------------------------------------------------------------------


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the current user's profile",
)
async def get_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> UserResponse:
    """Return the authenticated user's public profile."""
    return UserResponse.model_validate(current_user)


# ---------------------------------------------------------------------------
# POST /logout
# ---------------------------------------------------------------------------


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout (client-side token invalidation)",
)
async def logout(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> MessageResponse:
    """Logout the current user.

    JWTs are stateless so true server-side invalidation requires a token
    denylist (Redis or DB).  For now the client must discard both tokens.
    Implement a denylist to prevent token reuse within the remaining TTL.
    """
    logger.info("User id=%s logged out", current_user.user_id)
    return MessageResponse(
        message=(
            "Logged out successfully.  "
            "Please discard your access and refresh tokens on the client."
        )
    )
