"""Security utilities: password hashing, JWT creation/verification, and
password-reset token handling via itsdangerous.

Nothing in this module logs passwords or raw tokens.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Return the bcrypt hash of *password*."""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if *plain* matches *hashed*."""
    return pwd_context.verify(plain, hashed)


# ---------------------------------------------------------------------------
# JWT access / refresh tokens
# ---------------------------------------------------------------------------

def _build_token(data: dict[str, Any], expires_delta: timedelta) -> str:
    """Encode a JWT with an *exp* claim added to *data*."""
    payload = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    payload["exp"] = expire
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Create a short-lived JWT access token.

    Args:
        data: Arbitrary claims to embed (must include ``"sub"``).
        expires_delta: Override the default expiry from settings.

    Returns:
        Encoded JWT string.
    """
    delta = expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return _build_token(data, delta)


def create_refresh_token(data: dict[str, Any]) -> str:
    """Create a long-lived JWT refresh token.

    Args:
        data: Arbitrary claims to embed (must include ``"sub"``).

    Returns:
        Encoded JWT string.
    """
    delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return _build_token(data, delta)


def decode_token(token: str) -> dict[str, Any] | None:
    """Decode *token* and return its payload, or None on any error.

    Never raises — callers should check for None and raise HTTPException.
    """
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None


# ---------------------------------------------------------------------------
# Password-reset tokens (itsdangerous — not JWTs)
# ---------------------------------------------------------------------------

# Separate serialiser so its lifecycle is independent of JWT keys
_reset_serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
_RESET_SALT = "password-reset"


def create_password_reset_token(email: str) -> str:
    """Generate a time-limited, signed password-reset token for *email*.

    The token is URL-safe and can be passed as a query parameter.
    """
    return _reset_serializer.dumps(email, salt=_RESET_SALT)


def verify_password_reset_token(token: str) -> str | None:
    """Verify *token* and return the embedded email, or None if invalid/expired.

    The maximum age is taken from ``PASSWORD_RESET_TOKEN_EXPIRE_HOURS``.
    """
    max_age = settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS * 3600
    try:
        email: str = _reset_serializer.loads(token, salt=_RESET_SALT, max_age=max_age)
        return email
    except (SignatureExpired, BadSignature):
        # Token is either expired or tampered with — treat both as invalid
        return None
