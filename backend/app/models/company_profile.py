"""SQLAlchemy 2.x ORM model for the ``company_profile`` table.

Created at the end of the 5-step onboarding wizard.
One row per user (enforced via UNIQUE constraint on user_id).
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    ARRAY,
    Boolean,
    CheckConstraint,
    ForeignKey,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CompanyProfile(Base):
    """Stores the SME company profile collected during onboarding."""

    __tablename__ = "company_profile"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Owner — one-to-one with users
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # ── Step 1: Business Identity ─────────────────────────────────────────────
    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    year_of_incorporation: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    cin_llpin: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    is_dpiit_startup: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # ── Step 2: Business Category ─────────────────────────────────────────────
    primary_sector_id: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    primary_sector_name: Mapped[str] = mapped_column(String(100), nullable=False)
    business_sub_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_startup: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    startup_stage: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    # ── Step 3: Team & Revenue Size ───────────────────────────────────────────
    employee_range: Mapped[str] = mapped_column(String(20), nullable=False)
    turnover_range: Mapped[str] = mapped_column(String(30), nullable=False)
    funding_stage: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    # ── Step 4: Locations ─────────────────────────────────────────────────────
    primary_state: Mapped[str] = mapped_column(String(100), nullable=False)
    primary_jurisdiction_id: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    operating_states: Mapped[List[str]] = mapped_column(
        ARRAY(Text), nullable=False, default=list
    )
    exports_business: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    export_markets: Mapped[List[str]] = mapped_column(
        ARRAY(Text), nullable=False, default=list
    )

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "entity_type IN ('private_limited','llp','one_person_company',"
            "'sole_proprietorship','partnership','public_limited')",
            name="ck_cp_entity_type",
        ),
        CheckConstraint(
            "employee_range IN ('1_9','10_19','20_49','50_99','100_499','500_plus')",
            name="ck_cp_employee_range",
        ),
        CheckConstraint(
            "turnover_range IN ('below_40l','40l_1cr','1cr_10cr','10cr_100cr','above_100cr')",
            name="ck_cp_turnover_range",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<CompanyProfile id={self.id} user_id={self.user_id} "
            f"company={self.company_name!r} sector={self.primary_sector_name!r}>"
        )
