import datetime as dt
import psycopg
import pytest
from app.loaders.seed_loader import load

D = dt.date


@pytest.fixture(scope="module")
def loaded(dsn):
    with psycopg.connect(dsn) as c:   # start clean in case other tests left data
        pass
    stats = load(dsn)
    return stats


def q(dsn, sql, *a):
    with psycopg.connect(dsn) as c:
        return c.execute(sql, a).fetchall()


def test_counts(dsn, loaded):
    assert loaded["sections_inserted"] == 2398 and loaded["sections_skipped_no_regulation"] == 30  # 30 = Constitution, intentionally not loaded
    assert q(dsn, "SELECT count(*) FROM regulation_section")[0][0] == loaded["sections_inserted"]
    assert q(dsn, "SELECT count(*) FROM jurisdiction")[0][0] == 28
    assert q(dsn, "SELECT count(*) FROM compliance_calendar_rule")[0][0] == 13
    assert q(dsn, "SELECT count(*) FROM regulatory_document WHERE processed_status='pending'")[0][0] == 485


def test_idempotent(dsn, loaded):
    again = load(dsn)
    assert again["sections_inserted"] == 0 and again["obligations_inserted"] == 0 and again["rbi_documents_staged"] == 0
    assert again["unverified_transition_versions"] == 0


def test_every_regulation_has_one_open_version_at_most(dsn, loaded):
    assert q(dsn, "SELECT count(*) FROM (SELECT regulation_id FROM regulation_version WHERE effective_to IS NULL AND review_status='approved' GROUP BY 1 HAVING count(*)>1) x")[0][0] == 0


def test_transitions_are_not_live_until_approved(dsn, loaded):
    with psycopg.connect(dsn) as c:
        co = c.execute("INSERT INTO company(name,primary_jurisdiction_id,employee_count) VALUES('T',3,50) RETURNING company_id").fetchone()[0]
        c.execute("INSERT INTO company_sector VALUES (%s,1)", (co,))
        ap = lambda d: {r[0] for r in c.execute("SELECT regulation_id FROM applicable_versions_on(%s,%s)", (co, d))}
        assert 11 in ap(D(2026, 5, 1)) and 120 not in ap(D(2026, 5, 1))       # 1961 Act still applies: unverified repeal not approved
        for reg in (120, 11):  # approve new Act then the repeal, as a reviewer would
            vid = c.execute("SELECT version_id FROM regulation_version WHERE regulation_id=%s AND review_status='needs_review'", (reg,)).fetchone()[0]
            c.execute("SELECT approve_regulation_version(%s)", (vid,))
        assert 11 in ap(D(2026, 3, 31)) and 120 not in ap(D(2026, 3, 31))
        assert 11 not in ap(D(2026, 4, 2)) and 120 in ap(D(2026, 4, 2))
        c.rollback()


def test_thresholds_loaded(dsn, loaded):
    n = q(dsn, "SELECT count(*) FROM obligation_applicability WHERE min_employees IS NOT NULL")[0][0]
    assert n >= 1
