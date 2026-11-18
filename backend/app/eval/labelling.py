"""Accuracy measurement for stage 3.
  sample : python -m app.eval.labelling sample <dsn> labels.csv [--n 50]   -> CSV to hand-label
  score  : python -m app.eval.labelling score  <dsn> labels.csv            -> accuracy of stored extractions vs your labels
Fill ONLY the label_* columns (is_regulatory: yes/no, change_type: new|amendment|clarification|repeal|none,
effective_from: YYYY-MM-DD or blank when the document states none, target: the regulation's name or blank)."""
from __future__ import annotations

import csv, json, random, sys

import psycopg

COLS = ["document_id", "title", "url", "excerpt", "label_is_regulatory", "label_change_type", "label_effective_from", "label_target"]


def sample(dsn: str, out: str, n: int = 50, seed: int = 7) -> int:
    with psycopg.connect(dsn) as c:
        rows = c.execute("""SELECT document_id, title, url, left(raw_text, 700),
                                   CASE WHEN url ILIKE '%%PressRelease%%' THEN 'press' WHEN url ILIKE '%%MasDirections%%' THEN 'md' ELSE 'circular' END
                              FROM regulatory_document WHERE raw_text IS NOT NULL AND duplicate_of IS NULL""").fetchall()
    groups: dict[str, list] = {}
    for r in rows:
        groups.setdefault(r[4], []).append(r)
    rnd, picked = random.Random(seed), []
    per = max(1, n // max(1, len(groups)))
    for g in groups.values():              # stratified so each page type is represented
        rnd.shuffle(g)
        picked += g[:per]
    rnd.shuffle(rest := [r for g in groups.values() for r in g if r not in picked])
    picked += rest[: max(0, n - len(picked))]
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLS)
        for r in picked[:n]:
            w.writerow([r[0], r[1], r[2], r[3].replace("\n", " "), "", "", "", ""])
    return len(picked[:n])


def score(dsn: str, labels_csv: str) -> dict:
    labels = [r for r in csv.DictReader(open(labels_csv)) if r["label_is_regulatory"].strip()]
    m = {"labelled": len(labels), "extracted": 0, "regulatory_tp": 0, "regulatory_fp": 0, "regulatory_fn": 0, "regulatory_tn": 0,
         "change_type_ok": 0, "change_type_n": 0, "eff_date_ok": 0, "eff_date_n": 0, "false_date_invented": 0, "target_ok": 0, "target_n": 0}
    with psycopg.connect(dsn) as c:
        for r in labels:
            row = c.execute("SELECT output_json->'parsed' FROM agent_run WHERE agent='extract' AND status='ok' AND document_id=%s ORDER BY run_id DESC LIMIT 1",
                            (int(r["document_id"]),)).fetchone()
            if not row:
                continue
            m["extracted"] += 1
            p, truth = row[0], r["label_is_regulatory"].strip().lower().startswith("y")
            pred = bool(p["is_regulatory"])
            m["regulatory_tp" if pred and truth else "regulatory_fp" if pred else "regulatory_fn" if truth else "regulatory_tn"] += 1
            if truth:
                m["change_type_n"] += 1
                m["change_type_ok"] += p["change_type"] == r["label_change_type"].strip().lower()
                want = r["label_effective_from"].strip()
                m["eff_date_n"] += 1
                m["eff_date_ok"] += (p["effective_from"] or "") == want
                m["false_date_invented"] += bool(p["effective_from"]) and not want      # worst error: a date that is not in the document
                if r["label_target"].strip():
                    m["target_n"] += 1
                    m["target_ok"] += r["label_target"].strip().lower() in (p["target_regulation"] or "").lower()
    d = lambda a, b: round(a / b, 3) if b else None
    m["regulatory_precision"] = d(m["regulatory_tp"], m["regulatory_tp"] + m["regulatory_fp"])
    m["regulatory_recall"] = d(m["regulatory_tp"], m["regulatory_tp"] + m["regulatory_fn"])
    m["change_type_accuracy"], m["effective_date_accuracy"], m["target_accuracy"] = d(m["change_type_ok"], m["change_type_n"]), d(m["eff_date_ok"], m["eff_date_n"]), d(m["target_ok"], m["target_n"])
    return m


if __name__ == "__main__":
    cmd, dsn, path = sys.argv[1:4]
    if cmd == "sample":
        print(sample(dsn, path, int(sys.argv[5]) if len(sys.argv) > 5 and sys.argv[4] == "--n" else 50), "documents written to", path)
    else:
        print(json.dumps(score(dsn, path), indent=2))
