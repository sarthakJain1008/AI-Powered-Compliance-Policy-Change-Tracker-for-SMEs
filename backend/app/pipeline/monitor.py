"""Stages 1-2: fetch pending documents, store raw bytes (L0), parse text, chunk (L1). Idempotent and restartable."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Callable, Protocol

import psycopg

from .rbi import canonical_url, chunk_text, parse_rbi_page

RAW_DIR = Path(os.environ.get("RAW_STORE_DIR", Path(__file__).resolve().parents[3] / "data" / "raw_store"))
MAX_RETRIES = 3


class FetcherLike(Protocol):
    def get(self, url: str): ...


def store_raw(body: bytes, suffix: str = "html") -> tuple[str, str]:
    h = hashlib.sha256(body).hexdigest()
    path = RAW_DIR / h[:2] / f"{h}.{suffix}"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
    return h, str(path.relative_to(RAW_DIR))


def _fail(cur, doc_id: int, msg: str, status: int | None = None) -> None:
    cur.execute("""UPDATE regulatory_document SET retry_count = retry_count + 1, error_text = %s, http_status = %s,
                   last_attempt_at = now(),
                   processed_status = CASE WHEN retry_count + 1 >= %s THEN 'failed' ELSE processed_status END
                   WHERE document_id = %s""", (msg[:500], status, MAX_RETRIES, doc_id))


def run_fetch_stage(conn: psycopg.Connection, fetcher: FetcherLike, limit: int = 50) -> dict:
    """Fetch + parse up to `limit` documents that are still at stage 'discovered'. Commits per document."""
    stats = {"fetched": 0, "failed": 0, "duplicates": 0, "warnings": 0}
    ids = [r[0] for r in conn.execute(
        """SELECT document_id FROM regulatory_document
            WHERE stage = 'discovered' AND processed_status = 'pending' AND retry_count < %s
            ORDER BY document_id LIMIT %s""", (MAX_RETRIES, limit)).fetchall()]
    conn.commit()
    for doc_id in ids:
        with conn.transaction():
            cur = conn.cursor()
            row = cur.execute("""SELECT url FROM regulatory_document WHERE document_id=%s AND stage='discovered'
                                  FOR UPDATE SKIP LOCKED""", (doc_id,)).fetchone()
            if row is None:                         # another worker has it
                continue
            url = canonical_url(row[0])
            dup = cur.execute("SELECT document_id FROM regulatory_document WHERE url=%s AND document_id<>%s", (url, doc_id)).fetchone()
            if dup:
                cur.execute("""UPDATE regulatory_document SET duplicate_of=%s, processed_status='processed', stage='extracted',
                               error_text='duplicate of canonical URL' WHERE document_id=%s""", (dup[0], doc_id))
                stats["duplicates"] += 1
                continue
            try:
                res = fetcher.get(url)
            except Exception as e:
                _fail(cur, doc_id, str(e)); stats["failed"] += 1
                continue
            if res.status != 200:
                _fail(cur, doc_id, f"HTTP {res.status}", res.status); stats["failed"] += 1
                continue
            try:
                parsed = parse_rbi_page(res.body.decode("utf-8", errors="replace"))
            except ValueError as e:
                _fail(cur, doc_id, f"parse: {e}", 200); stats["failed"] += 1
                continue
            digest, rel = store_raw(res.body)
            cur.execute("""UPDATE regulatory_document SET url=%s, content_hash=%s, raw_path=%s, raw_text=%s, reference_no=%s,
                              pdf_url=%s, published_date=%s, http_status=200, stage='parsed', error_text=NULL,
                              last_attempt_at=now(), title=CASE WHEN length(%s) > 5 THEN left(%s, 300) ELSE title END
                           WHERE document_id=%s""",
                        (url, digest, rel, parsed.text, parsed.reference_no, parsed.pdf_url, parsed.issued_on,
                         parsed.title, parsed.title, doc_id))
            cur.execute("DELETE FROM document_chunk WHERE document_id=%s", (doc_id,))
            for i, ch in enumerate(chunk_text(parsed.text)):
                cur.execute("INSERT INTO document_chunk(document_id, ordinal, text) VALUES (%s,%s,%s)", (doc_id, i, ch))
            cur.execute("""INSERT INTO agent_run(agent, document_id, input_hash, status, finished_at)
                           VALUES ('parse', %s, %s, 'ok', now()) ON CONFLICT DO NOTHING""", (doc_id, digest))
            stats["fetched"] += 1
            stats["warnings"] += len(parsed.warnings)
    return stats


# ------------------------------------------------------------ crawl health: silent empty crawls are failures
def record_crawl(conn: psycopg.Connection, source_id: int, doc_count: int) -> str | None:
    """Store the result of a source crawl. Returns an alert string if the crawl looks broken, else None."""
    row = conn.execute("SELECT is_active, last_doc_count FROM source WHERE source_id=%s FOR UPDATE", (source_id,)).fetchone()
    if row is None:
        raise ValueError(f"unknown source {source_id}")
    active, prev = row
    alert = None
    if active and doc_count == 0:
        alert = f"source {source_id} returned 0 documents"
    elif active and prev and doc_count < prev * 0.5:
        alert = f"source {source_id} dropped from {prev} to {doc_count} documents"
    conn.execute("UPDATE source SET last_crawled_at=now(), last_doc_count=%s WHERE source_id=%s", (doc_count, source_id))
    return alert
