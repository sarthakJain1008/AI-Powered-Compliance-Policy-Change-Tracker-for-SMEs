"""Pydantic v2 schemas for authentication endpoints.

All schemas are immutable (``model_config`` default) unless explicitly noted.
Password strength is validated via a field validator so the same rule is
re-used in both ``UserRegister`` and ``ResetPasswordRequest``.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

# ---------------------------------------------------------------------------
# Shared password strength validator
# ---------------------------------------------------------------------------

_PASSWORD_PATTERN = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$"
)


def _validate_password_strength(value: str) -> str:
    """Enforce: ≥ 8 chars, at least one upper, one lower, one digit."""
    if not _PASSWORD_PATTERN.match(value):
        raise ValueError(
            "Password must be at least 8 characters and contain at least one "
            "uppercase letter, one lowercase letter, and one digit."
        )
    return value


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class UserRegister(BaseModel):
    """Payload for the POST /register endpoint."""

    email: EmailStr
    password: Annotated[str, Field(min_length=8)]
    full_name: Optional[str] = None
    role: Optional[str] = "viewer"

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return _validate_password_strength(v)


class UserLogin(BaseModel):
    """Payload for the POST /login endpoint (JSON body variant)."""

    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    """Payload for the POST /refresh endpoint."""

    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    """Payload for the POST /forgot-password endpoint."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Payload for the POST /reset-password endpoint."""

    token: str
    new_password: Annotated[str, Field(min_length=8)]

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return _validate_password_strength(v)


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class Token(BaseModel):
    """JWT token pair returned on successful authentication."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Claims embedded inside a JWT (used for decoding, not serialisation)."""

    sub: str   # Subject — typically the user_id as a string
    exp: int   # Expiry timestamp (Unix epoch)


class UserResponse(BaseModel):
    """Public user representation returned from API endpoints."""

    model_config = ConfigDict(from_attributes=True)

    user_id: int
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool
    is_verified: bool
    is_onboarded: bool = False
    created_at: datetime


class MessageResponse(BaseModel):
    """Generic message envelope for simple acknowledgement responses."""

    message: str
