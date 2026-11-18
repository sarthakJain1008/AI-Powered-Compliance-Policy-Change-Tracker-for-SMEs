import csv, datetime as dt, json
import psycopg
import pytest

from app.llm.client import ExtractResult
from app.llm.schemas import ExtractedInstrument, ExtractedObligation
from app.pipeline import extract as ex
from app.pipeline.extract import estimate_cost, final_confidence, prepare_text, run_extract_stage


def inst(**kw):
    base = dict(is_regulatory=True, instrument_type="circular", change_type="new", title="Circular X", issuing_authority="Reserve Bank of India",
                issued_on="2026-10-30", effective_from="2026-11-01", effective_date_quote="effective November 1, 2026",
                target_regulation="Reserve Bank of India (Test) Directions, 2026", affected_sectors=["Fintech"],
                summary_plain="Banks must do X.", obligations=[ExtractedObligation(description="File report monthly", frequency="monthly",
                deadline_text="by the 10th", responsible_role="Compliance Officer", penalty_severity=4)], confidence=0.93)
    base.update(kw)
    return ExtractedInstrument(**base)


class FakeLLM:
    model = "claude-opus-5-5"

    def __init__(self, result=None, exc=None):
        self.result, self.exc, self.calls = result, exc, 0

    def extract(self, system, user):
        self.calls += 1
        if self.exc:
            raise self.exc
        return self.result if isinstance(self.result, ExtractResult) else ExtractResult(self.result, 3000, 800)


@pytest.fixture()
def conn(dsn):
    def clean(c):
        for t in ("document_regulation_link", "obligation"):
            c.execute(f"DELETE FROM {t} WHERE " + ("document_id IN (SELECT document_id FROM regulatory_document WHERE source_id IN (SELECT source_id FROM source WHERE name='x-src'))" if t == "document_regulation_link"
                      else "regulation_version_id IN (SELECT version_id FROM regulation_version WHERE regulation_id IN (SELECT regulation_id FROM regulation WHERE title LIKE 'XTEST%%'))"))
        c.execute("DELETE FROM regulation_version WHERE regulation_id IN (SELECT regulation_id FROM regulation WHERE title LIKE 'XTEST%%')")
        c.execute("DELETE FROM regulation_sector WHERE regulation_id IN (SELECT regulation_id FROM regulation WHERE title LIKE 'XTEST%%')")
        c.execute("DELETE FROM regulation WHERE title LIKE 'XTEST%%'")
        c.execute("DELETE FROM agent_run WHERE document_id IN (SELECT document_id FROM regulatory_document WHERE source_id IN (SELECT source_id FROM source WHERE name='x-src'))")
        c.execute("DELETE FROM document_chunk WHERE document_id IN (SELECT document_id FROM regulatory_document WHERE source_id IN (SELECT source_id FROM source WHERE name='x-src'))")
        c.execute("DELETE FROM regulatory_document WHERE source_id IN (SELECT source_id FROM source WHERE name='x-src')")
        c.execute("DELETE FROM source WHERE name='x-src'")
        c.execute("DELETE FROM industry_sector WHERE name='Fintech' AND sector_id NOT IN (SELECT sector_id FROM regulation_sector UNION SELECT sector_id FROM company_sector)")
        c.execute("DELETE FROM jurisdiction WHERE name='RBI' AND jurisdiction_id NOT IN (SELECT jurisdiction_id FROM regulation)")
        c.execute("DELETE FROM jurisdiction WHERE name='India' AND jurisdiction_id NOT IN (SELECT coalesce(parent_jurisdiction_id,0) FROM jurisdiction)")
        c.commit()
    with psycopg.connect(dsn) as c:
        clean(c)
        c.execute("INSERT INTO industry_sector(name) VALUES ('Fintech') ON CONFLICT DO NOTHING")
        c.execute("INSERT INTO jurisdiction(name,type) VALUES ('India','country')")
        c.execute("INSERT INTO jurisdiction(name,type,parent_jurisdiction_id) SELECT 'RBI','regulator',jurisdiction_id FROM jurisdiction WHERE name='India'")
        c.execute("INSERT INTO source(name,url) VALUES ('x-src','http://x-src/' || gen_random_uuid())")
        c.commit()
        yield c
        c.rollback()
        clean(c)


def add_doc(c, text="Some regulatory text. " * 50, title="Test circular", url=None):
    sid = c.execute("SELECT source_id FROM source WHERE name='x-src'").fetchone()[0]
    d = c.execute("""INSERT INTO regulatory_document(source_id,title,url,raw_text,stage,published_date) VALUES (%s,%s,%s,%s,'parsed','2026-10-30')
                     RETURNING document_id""", (sid, title, url or f"http://x/{title}{id(text)}{dt.datetime.now().timestamp()}", text)).fetchone()[0]
    c.commit()
    return d


def version_of(c, doc_id):
    return c.execute("""SELECT v.review_status, v.change_type, v.effective_from, r.title, v.confidence_score, v.version_id, r.regulation_id
                          FROM document_regulation_link l JOIN regulation_version v ON v.version_id=l.regulation_version_id
                          JOIN regulation r USING (regulation_id) WHERE l.document_id=%s""", (doc_id,)).fetchone()


def test_confident_new_instrument_is_published(conn):
    d = add_doc(conn)
    s = run_extract_stage(conn, FakeLLM(inst(target_regulation="XTEST Directions 2026")))
    assert s["approved"] == 1 and s["processed"] == 1 and s["cost_usd"] > 0
    status, ctype, eff, title, conf, vid, rid = version_of(conn, d)
    assert (status, ctype, eff) == ("approved", "new", dt.date(2026, 11, 1))
    obl = conn.execute("SELECT frequency, review_status, penalty_severity, deadline_rule->>'text' FROM obligation WHERE regulation_version_id=%s", (vid,)).fetchall()
    assert obl == [("monthly", "approved", 4, "by the 10th")]
    assert conn.execute("SELECT stage, processed_status FROM regulatory_document WHERE document_id=%s", (d,)).fetchone() == ("extracted", "processed")
    assert conn.execute("SELECT count(*) FROM regulation_sector WHERE regulation_id=%s", (rid,)).fetchone()[0] == 1   # Fintech mapped
    assert conn.execute("SELECT jurisdiction_id FROM regulation WHERE regulation_id=%s", (rid,)).fetchone()[0] == conn.execute("SELECT jurisdiction_id FROM jurisdiction WHERE name='RBI'").fetchone()[0]     # RBI


def test_low_confidence_goes_to_review_queue(conn):
    d = add_doc(conn)
    run_extract_stage(conn, FakeLLM(inst(target_regulation="XTEST Low", confidence=0.5)))
    assert version_of(conn, d)[0] == "needs_review"
    assert conn.execute("SELECT count(*) FROM v_review_queue WHERE regulation_title='XTEST Low'").fetchone()[0] == 1
    vid = version_of(conn, d)[5]
    conn.execute("SELECT reject_regulation_version(%s)", (vid,))
    assert conn.execute("SELECT review_status FROM regulation_version WHERE version_id=%s", (vid,)).fetchone()[0] == "rejected"
    assert conn.execute("SELECT review_status FROM obligation WHERE regulation_version_id=%s", (vid,)).fetchone()[0] == "rejected"


def test_missing_effective_date_never_auto_publishes(conn):
    d = add_doc(conn)
    run_extract_stage(conn, FakeLLM(inst(target_regulation="XTEST NoDate", effective_from=None, effective_date_quote=None, confidence=0.99)))
    status, _, eff, *_ = version_of(conn, d)
    assert status == "needs_review" and eff == dt.date(2026, 10, 30)      # falls back to issue date, flagged for a human


def test_amendment_closes_previous_version(conn):
    d1, d2 = add_doc(conn, title="first"), add_doc(conn, title="second")
    run_extract_stage(conn, FakeLLM(inst(target_regulation="XTEST Amended Direction 2026", effective_from="2026-01-01")), limit=1)
    run_extract_stage(conn, FakeLLM(inst(target_regulation="XTEST Amended Direction 2026", change_type="amendment", effective_from="2026-08-01")), limit=1)
    rows = conn.execute("""SELECT v.change_type, v.effective_from, v.effective_to FROM regulation_version v JOIN regulation r USING (regulation_id)
                            WHERE r.title='XTEST Amended Direction 2026' ORDER BY v.effective_from""").fetchall()
    assert rows == [("new", dt.date(2026, 1, 1), dt.date(2026, 7, 31)), ("amendment", dt.date(2026, 8, 1), None)]


def test_amendment_to_unknown_base_is_held(conn):
    d = add_doc(conn)
    run_extract_stage(conn, FakeLLM(inst(target_regulation="XTEST Unknown Base", change_type="amendment", confidence=0.99)))
    assert version_of(conn, d)[0] == "needs_review"


def test_backdated_version_is_held_not_crashing(conn):
    add_doc(conn, title="a"); add_doc(conn, title="b")
    run_extract_stage(conn, FakeLLM(inst(target_regulation="XTEST Backdate", effective_from="2026-06-01")), limit=1)
    s = run_extract_stage(conn, FakeLLM(inst(target_regulation="XTEST Backdate", change_type="amendment", effective_from="2026-03-01")), limit=1)
    assert s["processed"] == 1 and s["failed"] == 0
    assert conn.execute("SELECT count(*) FROM regulation_version v JOIN regulation r USING (regulation_id) WHERE r.title='XTEST Backdate' AND v.review_status='needs_review'").fetchone()[0] == 1


def test_non_regulatory_creates_nothing(conn):
    d = add_doc(conn, title="auction")
    s = run_extract_stage(conn, FakeLLM(inst(is_regulatory=False, change_type="none", obligations=[])))
    assert s["not_regulatory"] == 1 and version_of(conn, d) is None
    assert conn.execute("SELECT processed_status FROM regulatory_document WHERE document_id=%s", (d,)).fetchone()[0] == "processed"


def test_identical_input_is_not_paid_for_twice(conn):
    text = "same text " * 80
    d = add_doc(conn, text=text, title="same")
    llm = FakeLLM(inst(target_regulation="XTEST Idem"))
    run_extract_stage(conn, llm)
    conn.execute("UPDATE regulatory_document SET stage='parsed', processed_status='pending' WHERE document_id=%s", (d,)); conn.commit()
    s = run_extract_stage(conn, llm)
    assert llm.calls == 1 and s["reused"] == 1


def test_api_errors_retry_then_fail_and_budget_stops(conn):
    d = add_doc(conn)
    llm = FakeLLM(exc=RuntimeError("overloaded"))
    for _ in range(4):
        run_extract_stage(conn, llm)
    assert conn.execute("SELECT retry_count, processed_status FROM regulatory_document WHERE document_id=%s", (d,)).fetchone() == (3, "failed")
    assert llm.calls == 3
    add_doc(conn, title="b1"); add_doc(conn, title="b2")
    s = run_extract_stage(conn, FakeLLM(inst(target_regulation="XTEST Budget")), max_cost_usd=0.0001)
    assert s["processed"] == 1 and s["stopped_on_budget"] is True


def test_refusal_is_recorded_not_retried(conn):
    d = add_doc(conn)
    run_extract_stage(conn, FakeLLM(ExtractResult(None, 100, 0, refusal="cyber")))
    assert conn.execute("SELECT processed_status, error_text FROM regulatory_document WHERE document_id=%s", (d,)).fetchone() == ("failed", "extract refused: cyber")


def test_truncation_is_explicit_and_confidence_capped():
    t, trunc = prepare_text("x" * 100_000)
    assert trunc and "characters omitted" in t and len(t) < 54_000
    assert prepare_text("short") == ("short", False)
    assert final_confidence(inst(confidence=0.99, effective_from=None), False, True) == 0.6
    assert final_confidence(inst(confidence=0.9), True, True) == 0.855
    assert final_confidence(inst(confidence=0.99, change_type="amendment"), False, False) == 0.6


def test_cost_estimate_and_scoring(conn, tmp_path):
    d = add_doc(conn, text="y" * 8000)
    est = estimate_cost(conn, "claude-opus-5-5")
    assert est["documents"] >= 1 and est["estimated_usd"] > 0
    from app.eval import labelling
    run_extract_stage(conn, FakeLLM(inst(target_regulation="XTEST Scored", effective_from="2026-11-01")))
    p = tmp_path / "l.csv"
    with open(p, "w", newline="") as f:
        w = csv.writer(f); w.writerow(labelling.COLS)
        w.writerow([d, "t", "u", "e", "yes", "new", "2026-11-01", "XTEST Scored"])
    dsn = conn.info.dsn.replace("password=", "password=")
    sc = labelling.score(f"postgresql://postgres:postgres@{conn.info.host}:{conn.info.port}/{conn.info.dbname}", str(p))
    assert sc["regulatory_precision"] == 1.0 and sc["change_type_accuracy"] == 1.0 and sc["effective_date_accuracy"] == 1.0 and sc["target_accuracy"] == 1.0
