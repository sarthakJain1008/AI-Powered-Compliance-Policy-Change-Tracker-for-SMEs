"""CLI: python -m app.pipeline.run_fetch <sync-dsn> [--limit N] [--delay S]"""
import argparse, json

import psycopg

from .fetch import Fetcher
from .monitor import run_fetch_stage

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("dsn")
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--delay", type=float, default=1.0)
    a = ap.parse_args()
    with psycopg.connect(a.dsn) as conn:
        print(json.dumps(run_fetch_stage(conn, Fetcher(delay=a.delay), a.limit), indent=2))
