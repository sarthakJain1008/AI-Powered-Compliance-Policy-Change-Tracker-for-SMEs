from pathlib import Path

import psycopg
import pytest

from app.pipeline import monitor
from app.pipeline.fetch import Fetched
from app.pipeline.monitor import record_crawl, run_fetch_stage

FX = Path(__file__).parent / "fixtures"
NOTIF = (FX / "rbi_notification.html").read_bytes()


class FakeFetcher:
    def __init__(self, routes):
        self.routes, self.calls = routes, []

    def get(self, url):
        self.calls.append(url)
        r = self.routes.get(url)
        if isinstance(r, Exception):
            raise r
        return r or Fetched(404, b"", url)


def _cleanup(c):
    """run_fetch_stage commits, so rollback cannot undo test data: delete it explicitly."""
    c.execute("""DELETE FROM agent_run WHERE document_id IN
                 (SELECT document_id FROM regulatory_document WHERE source_id IN (SELECT source_id FROM source WHERE name='t-src'))""")
    c.execute("DELETE FROM regulatory_document WHERE source_id IN (SELECT source_id FROM source WHERE name='t-src')")
    c.execute("DELETE FROM source WHERE name='t-src'")
    c.commit()


@pytest.fixture()
def conn(dsn, tmp_path, monkeypatch):
    monkeypatch.setattr(monitor, "RAW_DIR", tmp_path)
    with psycopg.connect(dsn) as c:
        _cleanup(c)
        c.execute("INSERT INTO source(name,url) VALUES ('t-src','http://t-src/' || gen_random_uuid()) ")
        c.commit()
        yield c
        c.rollback()
        _cleanup(c)


def add_doc(c, url, title="x"):
    sid = c.execute("SELECT source_id FROM source WHERE name='t-src'").fetchone()[0]
    return c.execute("INSERT INTO regulatory_document(source_id,title,url) VALUES (%s,%s,%s) RETURNING document_id", (sid, title, url)).fetchone()[0]


GOOD = "https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=13749&Mode=0"


def test_fetch_parse_store_chunk(conn, tmp_path):
    d = add_doc(conn, "https://www.rbi.org.in/BS_CircularIndexDisplay.aspx?Id=13749", "RBI/2026-2027/303DoR")
    f = FakeFetcher({GOOD: Fetched(200, NOTIF, GOOD)})
    stats = run_fetch_stage(conn, f)
    assert stats["fetched"] == 1 and f.calls == [GOOD]
    url, stage, text, ref, pub, h, path, title = conn.execute(
        "SELECT url,stage,raw_text,reference_no,published_date,content_hash,raw_path,title FROM regulatory_document WHERE document_id=%s", (d,)).fetchone()
    assert url == GOOD and stage == "parsed" and ref == "RBI/2026-27/303" and str(pub) == "2026-10-30"
    assert len(text) > 5000 and title.startswith("Implementation of Section 51A")
    assert (tmp_path / path).read_bytes() == NOTIF and len(h) == 64
    assert conn.execute("SELECT count(*) FROM document_chunk WHERE document_id=%s", (d,)).fetchone()[0] >= 3
    assert conn.execute("SELECT count(*) FROM agent_run WHERE document_id=%s AND agent='parse'", (d,)).fetchone()[0] == 1


def test_rerun_is_idempotent(conn):
    add_doc(conn, GOOD)
    f = FakeFetcher({GOOD: Fetched(200, NOTIF, GOOD)})
    run_fetch_stage(conn, f)
    again = run_fetch_stage(conn, f)
    assert again["fetched"] == 0 and len(f.calls) == 1


def test_http_errors_retry_then_fail(conn):
    d = add_doc(conn, GOOD)
    f = FakeFetcher({})                                      # 404 everywhere
    for _ in range(5):
        run_fetch_stage(conn, f)
    rc, status, st, err = conn.execute("SELECT retry_count,processed_status,stage,error_text FROM regulatory_document WHERE document_id=%s", (d,)).fetchone()
    assert (rc, status, st) == (3, "failed", "discovered") and err == "HTTP 404"
    assert len(f.calls) == 3                                 # stops retrying


def test_network_exception_is_recorded_not_raised(conn):
    d = add_doc(conn, GOOD)
    stats = run_fetch_stage(conn, FakeFetcher({GOOD: RuntimeError("timeout")}))
    assert stats["failed"] == 1
    assert "timeout" in conn.execute("SELECT error_text FROM regulatory_document WHERE document_id=%s", (d,)).fetchone()[0]


def test_error_page_marks_parse_failure(conn):
    d = add_doc(conn, GOOD)
    bad = (FX / "rbi_error.html").read_bytes()
    run_fetch_stage(conn, FakeFetcher({GOOD: Fetched(200, bad, GOOD)}))
    assert conn.execute("SELECT stage,error_text FROM regulatory_document WHERE document_id=%s", (d,)).fetchone()[1].startswith("parse:")


def test_legacy_and_canonical_duplicates_collapse(conn):
    keep = add_doc(conn, GOOD)
    dup = add_doc(conn, "https://www.rbi.org.in/BS_CircularIndexDisplay.aspx?Id=13749")
    f = FakeFetcher({GOOD: Fetched(200, NOTIF, GOOD)})
    stats = run_fetch_stage(conn, f)
    assert stats["duplicates"] == 1 and stats["fetched"] == 1 and f.calls == [GOOD]
    assert conn.execute("SELECT duplicate_of FROM regulatory_document WHERE document_id=%s", (dup,)).fetchone()[0] == keep


def test_crawl_health_alerts(conn):
    sid = conn.execute("SELECT source_id FROM source WHERE name='t-src'").fetchone()[0]
    assert record_crawl(conn, sid, 40) is None
    assert "dropped" in record_crawl(conn, sid, 10)
    assert "0 documents" in record_crawl(conn, sid, 0)
    conn.execute("UPDATE source SET is_active=false WHERE source_id=%s", (sid,))
    assert record_crawl(conn, sid, 0) is None                # inactive sources are not alerted
    with pytest.raises(ValueError):
        record_crawl(conn, 999999, 1)
