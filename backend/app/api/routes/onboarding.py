"""FastAPI router for the onboarding wizard.

Endpoints:
  GET  /api/v1/onboarding/options   — all dropdown data for the UI
  GET  /api/v1/onboarding/status    — has this user completed onboarding?
  POST /api/v1/onboarding/submit    — save profile + mark is_onboarded=True
  GET  /api/v1/onboarding/profile   — retrieve existing profile (for edit)
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.db.base import get_db
from app.models.user import User
from app.schemas.onboarding import (
    EMPLOYEE_RANGES,
    ENTITY_TYPES,
    EXPORT_MARKETS,
    FUNDING_STAGES,
    INCORPORATION_YEARS,
    INDIAN_STATES,
    SECTOR_SUB_TYPES,
    SECTORS,
    STARTUP_STAGES,
    TURNOVER_RANGES,
    CompanyProfileResponse,
    OnboardingOptionsResponse,
    OnboardingStatusResponse,
    OnboardingSubmitRequest,
)
from app.services.onboarding_service import (
    get_company_profile,
    get_onboarding_status,
    submit_onboarding,
)

router = APIRouter(prefix="/api/v1/onboarding", tags=["Onboarding"])

# ─────────────────────────────────────────────────────────────────────────────
# GET /options  — static dropdown data (no auth required; call once at boot)
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/options",
    response_model=OnboardingOptionsResponse,
    summary="All dropdown options for the onboarding wizard",
)
async def get_options() -> OnboardingOptionsResponse:
    """
    Returns every dropdown list used by the 5-step onboarding UI.
    This endpoint is intentionally public so the frontend can call it
    before the user is authenticated (e.g., to pre-populate a register page).
    """
    return OnboardingOptionsResponse(
        entity_types=ENTITY_TYPES,
        sectors=SECTORS,
        sector_sub_types=SECTOR_SUB_TYPES,
        startup_stages=STARTUP_STAGES,
        employee_ranges=EMPLOYEE_RANGES,
        turnover_ranges=TURNOVER_RANGES,
        funding_stages=FUNDING_STAGES,
        indian_states=INDIAN_STATES,
        export_markets=EXPORT_MARKETS,
        incorporation_years=INCORPORATION_YEARS,
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET /status  — is the authenticated user already onboarded?
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/status",
    response_model=OnboardingStatusResponse,
    summary="Check if the current user has completed onboarding",
)
async def onboarding_status(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OnboardingStatusResponse:
    result = await get_onboarding_status(db, current_user.user_id)
    return OnboardingStatusResponse(**result)


# ─────────────────────────────────────────────────────────────────────────────
# POST /submit  — save the full 5-step profile + mark user as onboarded
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/submit",
    response_model=CompanyProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit and save the completed onboarding profile",
)
async def submit(
    body: OnboardingSubmitRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CompanyProfileResponse:
    """
    Saves all 4 steps of the onboarding wizard as one atomic transaction.
    Sets is_onboarded=True on the user record.
    Returns 201 Created with the saved company profile.
    """
    profile = await submit_onboarding(db, current_user.user_id, body)
    return CompanyProfileResponse.model_validate(profile)


# ─────────────────────────────────────────────────────────────────────────────
# GET /profile  — retrieve the saved profile (for review or re-edit)
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/profile",
    response_model=CompanyProfileResponse,
    summary="Retrieve the current user's onboarding profile",
)
async def get_profile(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CompanyProfileResponse:
    profile = await get_company_profile(db, current_user.user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No onboarding profile found. Please complete the onboarding wizard.",
        )
    return CompanyProfileResponse.model_validate(profile)
