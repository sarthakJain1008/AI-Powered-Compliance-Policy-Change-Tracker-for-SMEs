"""Business logic for the onboarding wizard.

Keeps route handlers thin — all DB interactions live here.
"""

from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company_profile import CompanyProfile
from app.models.user import User
from app.schemas.onboarding import OnboardingSubmitRequest


async def get_onboarding_status(db: AsyncSession, user_id: int) -> dict:
    """Return whether the user has completed onboarding."""
    user_result = await db.execute(select(User).where(User.user_id == user_id))
    user: User | None = user_result.scalar_one_or_none()

    profile_result = await db.execute(
        select(CompanyProfile).where(CompanyProfile.user_id == user_id)
    )
    profile = profile_result.scalar_one_or_none()

    return {
        "is_onboarded": user.is_onboarded if user else False,
        "has_profile": profile is not None,
    }


async def get_company_profile(db: AsyncSession, user_id: int) -> CompanyProfile | None:
    """Fetch the existing company profile for a user."""
    result = await db.execute(
        select(CompanyProfile).where(CompanyProfile.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def submit_onboarding(
    db: AsyncSession,
    user_id: int,
    data: OnboardingSubmitRequest,
) -> CompanyProfile:
    """
    Save or update the company profile and mark the user as onboarded.

    Uses upsert logic: if a profile already exists (user re-doing onboarding),
    it is overwritten; otherwise a new record is created.
    """
    existing = await get_company_profile(db, user_id)

    profile_fields = {
        # Step 1
        "company_name":          data.step1.company_name,
        "entity_type":           data.step1.entity_type,
        "year_of_incorporation": data.step1.year_of_incorporation,
        "cin_llpin":             data.step1.cin_llpin,
        "is_dpiit_startup":      data.step1.is_dpiit_startup,
        # Step 2
        "primary_sector_id":     data.step2.primary_sector_id,
        "primary_sector_name":   data.step2.primary_sector_name,
        "business_sub_type":     data.step2.business_sub_type,
        "is_startup":            data.step2.is_startup,
        "startup_stage":         data.step2.startup_stage,
        # Step 3
        "employee_range":        data.step3.employee_range,
        "turnover_range":        data.step3.turnover_range,
        "funding_stage":         data.step3.funding_stage,
        # Step 4
        "primary_state":         data.step4.primary_state,
        "primary_jurisdiction_id": data.step4.primary_jurisdiction_id,
        "operating_states":      data.step4.operating_states,
        "exports_business":      data.step4.exports_business,
        "export_markets":        data.step4.export_markets,
    }

    if existing:
        # Update all fields on existing profile
        for key, value in profile_fields.items():
            setattr(existing, key, value)
        profile = existing
    else:
        profile = CompanyProfile(user_id=user_id, **profile_fields)
        db.add(profile)

    # Mark user as fully onboarded
    await db.execute(
        update(User)
        .where(User.user_id == user_id)
        .values(is_onboarded=True)
    )

    await db.commit()
    await db.refresh(profile)
    return profile
