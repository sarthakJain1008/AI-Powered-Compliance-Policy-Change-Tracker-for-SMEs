"""Stages 3-4: LLM extraction -> resolve target regulation -> version / obligations / link, gated by confidence.

The LLM only fills `ExtractedInstrument`. Whether a version goes live is decided here by explicit rules.
"""
from __future__ import annotations

import hashlib
import json
from datetime import date

import psycopg

from app.llm.client import Extractor, cost_usd
from app.llm.schemas import ExtractedInstrument

PROMPT_VERSION = "extract-v1"
AUTO_APPROVE = 0.85          # at or above this (after caps) a version is published without human review
MATCH_THRESHOLD = 0.55       # pg_trgm similarity to treat target_regulation as an existing regulation
HEAD_CHARS, TAIL_CHARS = 40_000, 12_000
AUTHORITY_TO_JURISDICTION = {"reserve bank of india": "RBI", "rbi": "RBI", "sebi": "SEBI", "mca": "MCA", "ministry of corporate": "MCA",
                             "epfo": "EPFO", "esic": "ESIC", "fssai": "FSSAI", "meity": "MeitY", "cbic": "CBIC", "gstn": "GSTN"}

SYSTEM = """You extract structured facts from Indian regulatory documents for a compliance tracker used by small businesses.
Rules:
- Use only what the document says. Never guess a date. If an effective date is not stated or directly computable, return null.
- is_regulatory is false for auction results, market operations, rate announcements, speeches and other items that impose no rule or obligation.
- change_type: new (creates a rule/instrument), amendment (changes an existing one), clarification, repeal, or none (not regulatory).
- target_regulation is the full formal name of the Act, Direction or regulation the document creates, amends, clarifies or repeals.
- affected_sectors: choose only from the provided sector list. Use the empty list if the document applies to all entities generally.
- obligations: only concrete requirements on regulated entities (filings, reports, policies, thresholds). Do not invent any.
- Be conservative with confidence: lower it when the text is truncated, ambiguous, or an effective date is missing."""


def prepare_text(text: str) -> tuple[str, bool]:
    """Head + tail of long documents (operative provisions are at the start, repeals/annexures at the end). Never silent: returns truncated flag."""
    if len(text) <= HEAD_CHARS + TAIL_CHARS:
        return text, False
    return f"{text[:HEAD_CHARS]}\n\n[... {len(text) - HEAD_CHARS - TAIL_CHARS} characters omitted ...]\n\n{text[-TAIL_CHARS:]}", True


def build_user(title: str, issued: date | None, url: str, text: str, sectors: list[str]) -> str:
    return (f"Document title: {title}\nSource URL: {url}\nIssue date (from page): {issued or 'unknown'}\n"
            f"Sector list: {json.dumps(sectors)}\n\n--- DOCUMENT TEXT ---\n{text}")


def final_confidence(x: ExtractedInstrument, truncated: bool, target_resolved: bool) -> float:
    c = x.confidence
    if not x.effective_from:
        c = min(c, 0.6)
    if x.change_type in ("amendment", "clarification", "repeal") and not target_resolved:
        c = min(c, 0.6)                      # cannot attach an amendment to an unknown base regulation
    if truncated:
        c *= 0.95
    return round(c, 3)


def _iso(s: str | None) -> date | None:
    try:
        return date.fromisoformat(s) if s else None
    except ValueError:
        return None


def resolve_regulation(cur, name: str | None) -> int | None:
    if not name:
        return None
    row = cur.execute("""SELECT regulation_id, greatest(similarity(title, %(n)s), similarity(coalesce(short_name,''), %(n)s)) s
                           FROM regulation ORDER BY s DESC LIMIT 1""", {"n": name}).fetchone()
    return row[0] if row and row[1] >= MATCH_THRESHOLD else None


def _jurisdiction(cur, authority: str | None) -> int:
    """Look the issuing body up by name (ids differ between databases); fall back to the country row."""
    a = (authority or "").lower()
    for k, name in AUTHORITY_TO_JURISDICTION.items():
        if k in a:
            row = cur.execute("SELECT jurisdiction_id FROM jurisdiction WHERE name=%s LIMIT 1", (name,)).fetchone()
            if row:
                return row[0]
    row = cur.execute("SELECT jurisdiction_id FROM jurisdiction WHERE name='India' LIMIT 1").fetchone()
    if row is None:
        raise RuntimeError("reference data missing: no 'India' jurisdiction (run the seed loader)")
    return row[0]


def persist(conn: psycopg.Connection, doc: dict, x: ExtractedInstrument, truncated: bool, run_id: int) -> dict:
    """Write regulation/version/obligations/link for one extraction. Returns a small outcome dict."""
    cur = conn.cursor()
    if not x.is_regulatory or x.change_type == "none":
        return {"outcome": "not_regulatory"}

    target_id = resolve_regulation(cur, x.target_regulation)
    created_regulation = False
    if target_id is None:
        itype = x.instrument_type if x.instrument_type != "other" else "notification"
        target_id = cur.execute("""INSERT INTO regulation(title, jurisdiction_id, instrument_type, status)
                                   VALUES (%s,%s,%s,'active') RETURNING regulation_id""",
                                (((x.target_regulation or x.title))[:300], _jurisdiction(cur, x.issuing_authority), itype)).fetchone()[0]
        created_regulation = True
        names = [n.lower() for n in x.affected_sectors]
        if names:
            cur.execute("""INSERT INTO regulation_sector(regulation_id, sector_id, note)
                           SELECT %s, sector_id, 'extracted' FROM industry_sector WHERE lower(name) = ANY(%s) ON CONFLICT DO NOTHING""",
                        (target_id, names))

    conf = final_confidence(x, truncated, target_resolved=not created_regulation)
    issued = _iso(x.issued_on) or doc["published_date"]
    eff = _iso(x.effective_from) or issued
    if eff is None:
        return {"outcome": "no_date", "regulation_id": target_id}
    status = "approved" if conf >= AUTO_APPROVE and x.effective_from else "needs_review"
    ctype = "new" if (created_regulation and x.change_type != "repeal") else x.change_type
    n = cur.execute("SELECT count(*) FROM regulation_version WHERE regulation_id=%s", (target_id,)).fetchone()[0]
    vnum = f"{ctype} {issued or eff}" if n else "1.0"

    def publish(review: str) -> int:
        with conn.transaction():     # savepoint: an overlap error must not poison the outer transaction
            return cur.execute("SELECT publish_regulation_version(%s::int,%s::text,%s::date,%s::text,%s::text,%s::text,%s::text,%s::int,%s::numeric,%s::text)",
                               (target_id, vnum, eff, ctype, x.summary_plain, doc["raw_text"], doc["url"], doc["document_id"], conf, review)).fetchone()[0]
    try:
        vid = publish(status)
    except psycopg.errors.ExclusionViolation:       # backdated or overlapping: a human decides
        status = "needs_review"
        vid = publish("needs_review")

    cur.execute("UPDATE regulation_version SET created_by_run_id=%s WHERE version_id=%s", (run_id, vid))
    for o in x.obligations:
        cur.execute("""INSERT INTO obligation(regulation_version_id, description, frequency, deadline_rule, responsible_role,
                                              penalty_severity, review_status, confidence_score)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (vid, o.description, o.frequency, json.dumps({"type": "text", "text": o.deadline_text}) if o.deadline_text else None,
                     o.responsible_role, o.penalty_severity, status, conf))
    rel = {"new": "creates", "amendment": "amends", "clarification": "clarifies", "repeal": "repeals"}[ctype]
    cur.execute("""INSERT INTO document_regulation_link(document_id, regulation_version_id, relation_type, confidence_score, review_status)
                   VALUES (%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""", (doc["document_id"], vid, rel, conf, status))
    return {"outcome": status, "version_id": vid, "regulation_id": target_id, "confidence": conf, "created_regulation": created_regulation}


def run_extract_stage(conn: psycopg.Connection, extractor: Extractor, limit: int = 25, max_cost_usd: float | None = None) -> dict:
    stats = {"processed": 0, "approved": 0, "needs_review": 0, "not_regulatory": 0, "failed": 0, "reused": 0, "cost_usd": 0.0, "stopped_on_budget": False}
    sectors = [r[0] for r in conn.execute("SELECT name FROM industry_sector ORDER BY name")]
    ids = [r[0] for r in conn.execute("""SELECT document_id FROM regulatory_document
                                         WHERE stage='parsed' AND processed_status='pending' AND retry_count < 3
                                         ORDER BY document_id LIMIT %s""", (limit,))]
    conn.commit()
    for doc_id in ids:
        if max_cost_usd is not None and stats["cost_usd"] >= max_cost_usd:
            stats["stopped_on_budget"] = True
            break
        with conn.transaction():
            cur = conn.cursor()
            row = cur.execute("""SELECT document_id,title,published_date,url,raw_text FROM regulatory_document
                                  WHERE document_id=%s AND stage='parsed' FOR UPDATE SKIP LOCKED""", (doc_id,)).fetchone()
            if row is None:
                continue
            doc = dict(zip(("document_id", "title", "published_date", "url", "raw_text"), row))
            text, truncated = prepare_text(doc["raw_text"] or "")
            user = build_user(doc["title"], doc["published_date"], doc["url"], text, sectors)
            h = hashlib.sha256(f"{extractor.model}|{PROMPT_VERSION}|{SYSTEM}|{user}".encode()).hexdigest()
            prev = cur.execute("SELECT run_id, output_json FROM agent_run WHERE agent='extract' AND input_hash=%s AND status='ok'", (h,)).fetchone()
            if prev:                                    # identical input already paid for: replay, no API call
                run_id, parsed, refusal = prev[0], ExtractedInstrument.model_validate(prev[1]["parsed"]), None
                stats["reused"] += 1
            else:
                try:
                    res = extractor.extract(SYSTEM, user)
                except Exception as e:
                    cur.execute("""UPDATE regulatory_document SET retry_count=retry_count+1, error_text=%s, last_attempt_at=now(),
                                   processed_status=CASE WHEN retry_count+1>=3 THEN 'failed' ELSE processed_status END WHERE document_id=%s""",
                                (f"extract: {e}"[:500], doc_id))
                    stats["failed"] += 1
                    continue
                cost = cost_usd(extractor.model, res.input_tokens, res.output_tokens)
                stats["cost_usd"] = round(stats["cost_usd"] + cost, 5)
                if res.parsed is None:                  # model declined
                    cur.execute("""INSERT INTO agent_run(agent,document_id,model,prompt_version,input_hash,status,error_text,cost_usd,finished_at)
                                   VALUES ('extract',%s,%s,%s,NULL,'failed',%s,%s,now())""",
                                (doc_id, extractor.model, PROMPT_VERSION, f"refusal: {res.refusal}", cost))
                    cur.execute("UPDATE regulatory_document SET retry_count=3, processed_status='failed', error_text=%s WHERE document_id=%s",
                                (f"extract refused: {res.refusal}", doc_id))
                    stats["failed"] += 1
                    continue
                run_id = cur.execute("""INSERT INTO agent_run(agent,document_id,model,prompt_version,input_hash,output_json,status,cost_usd,finished_at)
                                        VALUES ('extract',%s,%s,%s,%s,%s,'ok',%s,now()) RETURNING run_id""",
                                     (doc_id, extractor.model, PROMPT_VERSION, h,
                                      json.dumps({"parsed": res.parsed.model_dump(), "truncated": truncated,
                                                  "input_tokens": res.input_tokens, "output_tokens": res.output_tokens}), cost)).fetchone()[0]
                parsed = res.parsed
            out = persist(conn, doc, parsed, truncated, run_id)
            cur.execute("UPDATE regulatory_document SET stage='extracted', processed_status='processed', error_text=NULL WHERE document_id=%s", (doc_id,))
            stats["processed"] += 1
            key = {"approved": "approved", "needs_review": "needs_review", "not_regulatory": "not_regulatory", "no_date": "needs_review"}[out["outcome"]]
            stats[key] += 1
    return stats


def estimate_cost(conn: psycopg.Connection, model: str, expected_output_tokens: int = 1500) -> dict:
    """Dry-run estimate before spending anything: ~4 characters per token."""
    from app.llm.client import PRICES
    rows = conn.execute("""SELECT length(raw_text) FROM regulatory_document WHERE stage='parsed' AND processed_status='pending'""").fetchall()
    toks = sum(min(r[0], HEAD_CHARS + TAIL_CHARS) // 4 + 1200 for r in rows)      # +1200 for system prompt and sector list
    pin, pout = PRICES[model]
    return {"documents": len(rows), "input_tokens": toks, "model": model,
            "estimated_usd": round((toks * pin + len(rows) * expected_output_tokens * pout) / 1_000_000, 2)}
