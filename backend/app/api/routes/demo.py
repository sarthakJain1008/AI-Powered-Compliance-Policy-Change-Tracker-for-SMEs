"""Read/review API over the temporal compliance database (the Phase 0-3 schema).
Needs a login (same JWT as the rest of the app). Data lives in the `compliance` database (DEMO_DATABASE_URL)."""
from __future__ import annotations

import asyncio, json, os
from datetime import date
from typing import Annotated, Optional

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/v1/demo", tags=["demo"])
DSN = os.environ.get("DEMO_DATABASE_URL", "postgresql://localhost:5433/compliance")
_pool: asyncpg.Pool | None = None
_lock = asyncio.Lock()
CurrentUser = Annotated[User, Depends(get_current_user)]


async def pool() -> asyncpg.Pool:
    global _pool
    async with _lock:
        if _pool is None:
            try:
                _pool = await asyncpg.create_pool(DSN, min_size=1, max_size=4, timeout=5)
            except Exception as e:  # surface a readable message instead of a bare 500
                raise HTTPException(503, f"Compliance database not reachable at {DSN.split('@')[-1]}: {e}")
    return _pool


async def rows(sql: str, *args) -> list[dict]:
    async with (await pool()).acquire() as c:
        return [dict(r) for r in await c.fetch(sql, *args)]


@router.get("/overview")
async def overview(_: CurrentUser):
    q = """SELECT
      (SELECT count(*) FROM regulation) regulations,
      (SELECT count(*) FROM regulation_version WHERE review_status='approved') approved_versions,
      (SELECT count(*) FROM regulation_section) sections,
      (SELECT count(*) FROM obligation) obligations,
      (SELECT count(*) FROM regulatory_document) documents,
      (SELECT count(*) FROM regulatory_document WHERE stage IN ('parsed','extracted')) documents_parsed,
      (SELECT count(*) FROM regulatory_document WHERE processed_status='failed') documents_failed,
      (SELECT count(*) FROM regulation_version WHERE review_status='needs_review') review_queue,
      (SELECT count(*) FROM compliance_calendar_rule) calendar_rules,
      (SELECT count(*) FROM jurisdiction) jurisdictions, (SELECT count(*) FROM industry_sector) sectors"""
    return (await rows(q))[0]


@router.get("/regulations")
async def regulations(_: CurrentUser, on: Optional[date] = None, q: str = "", limit: int = Query(200, le=500)):
    """Time travel: which regulations are in force on a given date, and which had been repealed by then."""
    on = on or date.today()
    in_force = await rows("""
        SELECT r.regulation_id, r.title, r.category, r.instrument_type, j.name AS jurisdiction, v.version_id, v.version_number,
               v.effective_from, v.effective_to,
               (SELECT count(*) FROM regulation_section s WHERE s.version_id = v.version_id) AS sections,
               (SELECT count(*) FROM obligation o WHERE o.regulation_version_id = v.version_id) AS obligations
          FROM regulation r JOIN regulation_version v USING (regulation_id) JOIN jurisdiction j ON j.jurisdiction_id = r.jurisdiction_id
         WHERE v.review_status='approved' AND v.superseded_at IS NULL AND v.change_type <> 'repeal'
           AND $1::date BETWEEN v.effective_from AND coalesce(v.effective_to, 'infinity'::date)
           AND ($2 = '' OR r.title ILIKE '%' || $2 || '%')
         ORDER BY r.title LIMIT $3""", on, q, limit)
    repealed = await rows("""
        SELECT r.regulation_id, r.title, v.effective_from AS repealed_on
          FROM regulation r JOIN regulation_version v USING (regulation_id)
         WHERE v.change_type='repeal' AND v.review_status='approved' AND v.effective_from <= $1::date
           AND ($2 = '' OR r.title ILIKE '%' || $2 || '%') ORDER BY r.title""", on, q)
    return {"on": on, "count": len(in_force), "in_force": in_force, "repealed": repealed}


@router.get("/regulations/{regulation_id}/timeline")
async def timeline(regulation_id: int, _: CurrentUser):
    return await rows("""SELECT version_id, version_number, change_type, effective_from, effective_to, review_status, confidence_score, summary_text
                           FROM regulation_version WHERE regulation_id=$1 ORDER BY effective_from""", regulation_id)


@router.get("/regulations/{regulation_id}/sections")
async def sections(regulation_id: int, _: CurrentUser, limit: int = Query(15, le=100)):
    return await rows("""SELECT s.section_no, left(s.body, 600) AS body FROM regulation_section s
                           JOIN regulation_version v USING (version_id)
                          WHERE v.regulation_id=$1 AND v.review_status='approved' ORDER BY s.section_id LIMIT $2""", regulation_id, limit)


@router.get("/review-queue")
async def review_queue(_: CurrentUser):
    return await rows("""SELECT version_id, regulation_id, regulation_title, version_number, change_type, effective_from,
                                confidence_score, summary_text, obligation_count FROM v_review_queue LIMIT 100""")


@router.post("/review/{version_id}/{decision}")
async def review(version_id: int, decision: str, user: CurrentUser):
    if decision not in ("approve", "reject"):
        raise HTTPException(400, "decision must be approve or reject")
    fn = "approve_regulation_version" if decision == "approve" else "reject_regulation_version"
    async with (await pool()).acquire() as c:
        await c.execute(f"SELECT {fn}($1::int, NULL)", version_id)
    return {"version_id": version_id, "decision": decision, "by": user.email}


@router.post("/reset-transitions")
async def reset_transitions(_: CurrentUser):
    """Put the unverified Income-tax / Labour-Code transitions back to 'needs_review' so the demo can be repeated."""
    async with (await pool()).acquire() as c:
        async with c.transaction():
            regs = [r["regulation_id"] for r in await c.fetch("SELECT DISTINCT regulation_id FROM regulation_version WHERE version_number LIKE '%(unverified)%'")]
            await c.execute("UPDATE regulation_version SET review_status='needs_review', reviewed_at=NULL WHERE version_number LIKE '%(unverified)%'")
            await c.execute("""UPDATE regulation_version v SET effective_to = NULL
                                 WHERE v.regulation_id = ANY($1::int[]) AND v.version_number NOT LIKE '%(unverified)%'
                                   AND v.review_status='approved' AND v.effective_to IS NOT NULL""", regs)
            await c.execute("UPDATE regulation SET status='active' WHERE regulation_id = ANY($1::int[]) AND status='repealed'", regs)
    return {"reset": len(regs)}


@router.get("/documents")
async def documents(_: CurrentUser, q: str = "", limit: int = Query(30, le=200)):
    return await rows("""SELECT document_id, title, reference_no, published_date, url, stage, processed_status,
                                length(raw_text) AS chars, left(raw_text, 700) AS excerpt
                           FROM regulatory_document WHERE raw_text IS NOT NULL AND ($1='' OR title ILIKE '%'||$1||'%' OR raw_text ILIKE '%'||$1||'%')
                          ORDER BY published_date DESC NULLS LAST, document_id LIMIT $2""", q, limit)


@router.get("/calendar")
async def calendar(_: CurrentUser):
    out = await rows("SELECT filing, authority, form, frequency, deadline_rule FROM compliance_calendar_rule ORDER BY frequency, filing")
    for r in out:
        r["deadline_rule"] = json.loads(r["deadline_rule"]) if isinstance(r["deadline_rule"], str) else r["deadline_rule"]
    return out
