"""Authentication service layer.

All database interactions and business-logic decisions live here so that
route handlers remain thin orchestrators.  No passwords or tokens are ever
logged.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.email import send_reset_password_email
from app.core.security import (
    create_password_reset_token,
    hash_password,
    verify_password,
    verify_password_reset_token,
)
from app.models.user import User
from app.schemas.auth import UserRegister

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# User retrieval helpers
# ---------------------------------------------------------------------------


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Fetch a single user by *email*, or return None if not found."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    """Fetch a single user by primary key, or return None if not found."""
    result = await db.execute(select(User).where(User.user_id == user_id))
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


async def register_user(db: AsyncSession, data: UserRegister) -> User:
    """Create a new user record from *data*.

    Raises:
        HTTPException 409: if the email address is already registered.
    """
    existing = await get_user_by_email(db, data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email address already exists.",
        )

    # Validate role value before persisting
    allowed_roles = {"admin", "manager", "viewer", "consultant"}
    role = (data.role or "viewer").lower()
    if role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role '{role}'. Allowed: {sorted(allowed_roles)}.",
        )

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),  # never store plain text
        full_name=data.full_name,
        role=role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    logger.info("New user registered: id=%s email=%s", user.user_id, user.email)
    return user


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------


async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str,
) -> User | None:
    """Verify credentials and update ``last_login``.

    Returns the User on success, or None if credentials are invalid.
    Deliberately avoids leaking whether the email exists.
    """
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None

    # Update last_login timestamp on successful authentication
    user.last_login = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# Password reset flow
# ---------------------------------------------------------------------------


async def initiate_password_reset(db: AsyncSession, email: str) -> str:
    """Generate a password-reset token for *email* and send the email.

    Always returns a token string (even if the user does not exist) so
    callers can respond with HTTP 200 without leaking whether the email
    is registered (the email simply won't arrive).

    Returns:
        The signed reset token.
    """
    user = await get_user_by_email(db, email)
    token = create_password_reset_token(email)

    if user:
        # Fire-and-forget: errors are caught inside send_reset_password_email
        await send_reset_password_email(
            email_to=email,
            token=token,
            username=user.full_name or email,
        )
    else:
        # Log at debug level only — do not expose via HTTP response
        logger.debug("Password reset requested for unknown email: %s", email)

    return token


async def reset_user_password(
    db: AsyncSession,
    token: str,
    new_password: str,
) -> bool:
    """Apply a new password using a valid reset *token*.

    Args:
        token:        Signed password-reset token from the email link.
        new_password: The new plain-text password (will be hashed here).

    Returns:
        True on success, False if the token is invalid or expired.

    Raises:
        HTTPException 400: if the user associated with the token no longer
            exists (e.g. deleted account).
    """
    email = verify_password_reset_token(token)
    if email is None:
        # Token is expired or tampered with
        return False

    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account not found.",
        )

    user.hashed_password = hash_password(new_password)
    await db.commit()
    logger.info("Password reset completed for user id=%s", user.user_id)
    return True
