"""CLI: python -m app.pipeline.run_extract <sync-dsn> [--model M] [--limit N] [--max-cost USD] [--estimate]
Spends API credits unless --estimate. Needs ANTHROPIC_API_KEY (or `ant auth login`)."""
import argparse, json

import psycopg

from app.llm.client import DEFAULT_MODEL
from .extract import estimate_cost, run_extract_stage

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("dsn")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--limit", type=int, default=25)
    ap.add_argument("--max-cost", type=float, default=None, help="stop once this many USD have been spent")
    ap.add_argument("--estimate", action="store_true", help="print a cost estimate and exit")
    a = ap.parse_args()
    with psycopg.connect(a.dsn) as conn:
        if a.estimate:
            print(json.dumps(estimate_cost(conn, a.model), indent=2))
        else:
            from app.llm.client import ClaudeExtractor
            print(json.dumps(run_extract_stage(conn, ClaudeExtractor(a.model), a.limit, a.max_cost), indent=2))
