"""SQLAlchemy 2.x ORM model for the ``users`` table.

Uses the new ``Mapped``/``mapped_column`` annotation style introduced in
SQLAlchemy 2.0 — no ``Column()`` imports needed.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    """Represents an application user.

    Roles are enforced at the database level via a CHECK constraint so that
    even direct SQL inserts cannot introduce invalid values.
    """

    __tablename__ = "users"

    # Primary key
    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Credentials
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,  # Fast look-ups during login / duplicate-check
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # Profile
    full_name: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Role with an allowed-values guard at the DB level
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'viewer'"),
    )

    # Status flags
    is_active: Mapped[bool] = mapped_column(nullable=False, server_default=text("true"))
    is_verified: Mapped[bool] = mapped_column(nullable=False, server_default=text("false"))
    is_onboarded: Mapped[bool] = mapped_column(nullable=False, server_default=text("false"))

    # Timestamps (maintained by the database, not the ORM)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Nullable — only set after first successful login
    last_login: Mapped[datetime | None] = mapped_column(nullable=True)

    # Table-level constraints
    __table_args__ = (
        CheckConstraint(
            "role IN ('admin', 'manager', 'viewer', 'consultant')",
            name="ck_users_role",
        ),
    )

    def __repr__(self) -> str:
        return f"<User id={self.user_id} email={self.email!r} role={self.role!r}>"
