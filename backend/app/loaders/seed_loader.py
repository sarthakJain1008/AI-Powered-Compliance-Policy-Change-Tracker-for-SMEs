"""Idempotent loader: seeds/ + curated/ + raw RBI crawl -> temporal schema.

Usage:  python -m app.loaders.seed_loader <sync-dsn>
        (DSN e.g. postgresql://postgres:postgres@localhost:5434/compliance)
Safe to re-run: reference rows are upserted by primary key, sections/obligations are skipped if present.
"""
from __future__ import annotations

import glob, hashlib, json, sys
from datetime import date
from pathlib import Path

import psycopg

DATA = Path(__file__).resolve().parents[3] / "data"

ACT_TO_REG = {  # curated act_title -> seeds regulation_id
    "Companies Act, 2013": 1, "Insolvency and Bankruptcy Code Act, 2016": 3, "Central Goods and Services Tax Act, 2017": 10,
    "Income-Tax Act, 1961": 11, "Employees Provident Funds and Miscellaneous Provisions Act, 1952": 20,
    "Employees State Insurance Act, 1948": 21, "Minimum Wages Act, 1948": 22, "Payment of Gratuity Act, 1972": 23,
    "Payment of Bonus Act, 1965": 24, "Maternity Benefit Act, 1961": 25, "Factories Act, 1948": 26,
    "Contract Labour (Regulation and Abolition) Act, 1970": 27, "Digital Personal Data Protection Act, 2023": 40,
    "Information Technology Act, 2000": 41, "Foreign Exchange Management Act, 1999": 52,
    "Food Safety and Standards Act, 2006": 60, "Patents Act, 1970": 90, "Trade Marks Act, 1999": 91, "Copyright Act, 1957": 92,
}
# acts in the curated corpus with no seeded regulation: created without sector mapping (applicable to nobody until mapped)
EXTRA_ACTS = {
    "Consumer Protection Act, 2019": (130, "Consumer Protection Act 2019", "consumer"),
    "Competition Act, 2002": (131, "Competition Act 2002", "competition"),
    "Arbitration and Conciliation Act, 1996": (132, "Arbitration Act 1996", "dispute"),
    "Indian Contract Act, 1872": (133, "Contract Act 1872", "contract"),
    "Securities and Exchange Board of India Act, 1992": (134, "SEBI Act 1992", "securities"),
    "Securities Contracts (Regulation) Act, 1956": (135, "SCRA 1956", "securities"),
}
FREQ = {"one_time": "one-time", "ad_hoc": "ad-hoc"}


def instrument_type(title: str) -> str:
    t = title.lower()
    for key, val in (("rules", "rule"), ("regulations", "regulation"), ("regs", "regulation"),
                     ("direction", "notification"), ("code", "act")):
        if key in t:
            return val
    return "act"


def load(dsn: str) -> dict:
    stats: dict = {}
    seeds = lambda n: json.loads((DATA / "seeds" / f"{n}.json").read_text())
    with psycopg.connect(dsn) as c:
        cur = c.cursor()
        ident = lambda t, col: cur.execute(
            f"SELECT setval(pg_get_serial_sequence('{t}','{col}'), greatest((SELECT max({col}) FROM {t}),1))")

        # ---- reference data (explicit ids kept; parents inserted first)
        for j in sorted(seeds("jurisdictions"), key=lambda x: (x["parent_jurisdiction_id"] or 0, x["jurisdiction_id"])):
            cur.execute("""INSERT INTO jurisdiction(jurisdiction_id,name,type,parent_jurisdiction_id) OVERRIDING SYSTEM VALUE
                           VALUES (%(jurisdiction_id)s,%(name)s,%(type)s,%(parent_jurisdiction_id)s)
                           ON CONFLICT (jurisdiction_id) DO UPDATE SET name=EXCLUDED.name,type=EXCLUDED.type,
                           parent_jurisdiction_id=EXCLUDED.parent_jurisdiction_id""", j)
        for s in seeds("industry_sectors"):
            cur.execute("""INSERT INTO industry_sector(sector_id,name,nic_code,description) OVERRIDING SYSTEM VALUE
                           VALUES (%(sector_id)s,%(name)s,%(nic_code)s,%(description)s)
                           ON CONFLICT (sector_id) DO UPDATE SET name=EXCLUDED.name,nic_code=EXCLUDED.nic_code,description=EXCLUDED.description""", s)
        for s in seeds("sources"):
            cur.execute("""INSERT INTO source(source_id,name,url,jurisdiction_id,crawl_frequency,file_type,is_active) OVERRIDING SYSTEM VALUE
                           VALUES (%(source_id)s,%(name)s,%(url)s,%(jurisdiction_id)s,%(crawl_frequency)s,%(file_type)s,%(is_active)s)
                           ON CONFLICT (source_id) DO UPDATE SET name=EXCLUDED.name,url=EXCLUDED.url,is_active=EXCLUDED.is_active""", s)

        # ---- regulations
        regs = seeds("regulations")
        for r in regs:
            cur.execute("""INSERT INTO regulation(regulation_id,title,short_name,jurisdiction_id,instrument_type,category,status,first_effective_date)
                           OVERRIDING SYSTEM VALUE VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                           ON CONFLICT (regulation_id) DO UPDATE SET title=EXCLUDED.title,status=EXCLUDED.status""",
                        (r["regulation_id"], r["title"], r["short_name"], r["jurisdiction_id"], instrument_type(r["title"]),
                         r["category"], r["status"], r["first_effective_date"]))
        for title, (rid, short, cat) in EXTRA_ACTS.items():
            cur.execute("""INSERT INTO regulation(regulation_id,title,short_name,jurisdiction_id,instrument_type,category,status)
                           OVERRIDING SYSTEM VALUE VALUES (%s,%s,%s,1,'act',%s,'active') ON CONFLICT DO NOTHING""",
                        (rid, title, short, cat))
        known = {r["regulation_id"] for r in regs}
        orphans: dict[int, int] = {}
        for m in seeds("regulation_sector_mappings"):
            if m["regulation_id"] not in known:     # seed defect: mapping for a regulation that was never defined
                orphans[m["regulation_id"]] = orphans.get(m["regulation_id"], 0) + 1
                continue
            cur.execute("INSERT INTO regulation_sector(regulation_id,sector_id,note) VALUES (%(regulation_id)s,%(sector_id)s,%(note)s) ON CONFLICT DO NOTHING", m)
        stats["orphan_sector_mappings_skipped"] = orphans

        # ---- version 1 of each active regulation with a known start date
        v1: dict[int, int] = {}
        for r in regs:
            if r["status"] == "draft" or not r["first_effective_date"]:
                continue
            row = cur.execute("SELECT version_id FROM regulation_version WHERE regulation_id=%s AND version_number='1.0'", (r["regulation_id"],)).fetchone()
            if not row:
                row = cur.execute("""INSERT INTO regulation_version(regulation_id,version_number,effective_from,change_type,review_status)
                                     VALUES (%s,'1.0',%s,'new','approved') RETURNING version_id""",
                                  (r["regulation_id"], r["first_effective_date"])).fetchone()
            v1[r["regulation_id"]] = row[0]
        for title, (rid, _, _) in EXTRA_ACTS.items():
            row = cur.execute("SELECT version_id FROM regulation_version WHERE regulation_id=%s AND version_number='1.0'", (rid,)).fetchone() \
                or cur.execute("INSERT INTO regulation_version(regulation_id,version_number,effective_from,change_type) VALUES (%s,'1.0','1900-01-01','new') RETURNING version_id", (rid,)).fetchone()
            v1[rid] = row[0]

        # ---- curated sections -> version 1 of the matching act
        sections = json.loads((DATA / "curated" / "business_acts_sections.json").read_text())
        n_sec = skipped = 0
        for s in sections:
            rid = ACT_TO_REG.get(s["act_title"]) or (EXTRA_ACTS.get(s["act_title"]) or (None,))[0]
            if rid is None or rid not in v1:
                skipped += 1
                continue
            body = s["full_text"]
            cur.execute("""INSERT INTO regulation_section(version_id,section_no,body,body_hash) VALUES (%s,%s,%s,%s)
                           ON CONFLICT (version_id,section_no) DO NOTHING""",
                        (v1[rid], str(s["section"])[:40], body, hashlib.sha256(body.encode()).hexdigest()))
            n_sec += cur.rowcount
        stats["sections_inserted"], stats["sections_skipped_no_regulation"] = n_sec, skipped

        # ---- obligations (+ thresholds); drafts get attached after transitions below
        pending_oblig = []
        for o in seeds("obligations"):
            pending_oblig.append(o)

        # ---- unverified transitions: needs_review versions only
        tr = json.loads((DATA / "seeds" / "transitions.json").read_text())
        for r in tr["new_regulations"]:
            cur.execute("""INSERT INTO regulation(regulation_id,title,short_name,jurisdiction_id,instrument_type,category,status)
                           OVERRIDING SYSTEM VALUE VALUES (%s,%s,%s,%s,'act',%s,'active') ON CONFLICT DO NOTHING""",
                        (r["regulation_id"], r["title"], r["short_name"], r["jurisdiction_id"], r["category"]))
            # same sector coverage as the regulation it parallels
            cur.execute("""INSERT INTO regulation_sector(regulation_id,sector_id,note)
                           SELECT %s, sector_id, 'copied from parallel regulation (unverified)' FROM regulation_sector WHERE regulation_id=%s
                           ON CONFLICT DO NOTHING""", (r["regulation_id"], r["sector_like"]))
        # sectors for draft codes already seeded (29, 30) come from the mappings file
        n_tr = 0
        for t in tr["transitions"]:
            cur.execute("""INSERT INTO regulation_version(regulation_id,version_number,effective_from,change_type,review_status,summary_text)
                           SELECT %s,'1.0 (unverified)',%s,'new','needs_review',%s
                            WHERE NOT EXISTS (SELECT 1 FROM regulation_version WHERE regulation_id=%s AND version_number='1.0 (unverified)')""",
                        (t["new"], t["effective_from"], t["label"], t["new"]))
            n_tr += cur.rowcount
            for old in t["replaces"]:
                cur.execute("""INSERT INTO regulation_version(regulation_id,version_number,effective_from,change_type,review_status,summary_text)
                               SELECT %s,'repeal (unverified)',%s,'repeal','needs_review',%s
                                WHERE NOT EXISTS (SELECT 1 FROM regulation_version WHERE regulation_id=%s AND version_number='repeal (unverified)')""",
                            (old, t["effective_from"], t["label"], old))
                n_tr += cur.rowcount
        stats["unverified_transition_versions"] = n_tr

        # ---- obligations: attach to v1 (or the unverified v1 for the new codes)
        n_ob = n_skip_ob = 0
        for o in pending_oblig:
            rid = o["regulation_id"]
            vid = v1.get(rid) or (cur.execute("SELECT version_id FROM regulation_version WHERE regulation_id=%s ORDER BY effective_from LIMIT 1", (rid,)).fetchone() or (None,))[0]
            if vid is None:
                n_skip_ob += 1
                continue
            exists = cur.execute("SELECT 1 FROM obligation WHERE regulation_version_id=%s AND description=%s", (vid, o["description"])).fetchone()
            if exists:
                continue
            rule = {"type": "offset_days", "days": o["default_deadline_offset_days"]} if o["default_deadline_offset_days"] is not None else None
            oid = cur.execute("""INSERT INTO obligation(regulation_version_id,description,frequency,deadline_rule,responsible_role)
                                 VALUES (%s,%s,%s,%s,%s) RETURNING obligation_id""",
                              (vid, o["description"], FREQ.get(o["frequency"], o["frequency"]), json.dumps(rule) if rule else None,
                               o["responsible_role"])).fetchone()[0]
            if o["applies_to_min_employees"] is not None or o["applies_to_min_turnover"] is not None:
                cur.execute("INSERT INTO obligation_applicability(obligation_id,min_employees,min_turnover) VALUES (%s,%s,%s)",
                            (oid, o["applies_to_min_employees"], o["applies_to_min_turnover"]))
            n_ob += 1
        stats["obligations_inserted"], stats["obligations_skipped_no_version"] = n_ob, n_skip_ob

        # ---- compliance calendar rules
        n_cal = 0
        for r in json.loads((DATA / "seeds" / "calendar_rules.json").read_text()):
            cur.execute("""INSERT INTO compliance_calendar_rule(filing,authority,form,frequency,deadline_rule,valid_from)
                           SELECT %s,%s,%s,%s,%s,'2025-04-01' WHERE NOT EXISTS (SELECT 1 FROM compliance_calendar_rule WHERE filing=%s)""",
                        (r["filing"], r["authority"], r["form"], r["frequency"], json.dumps(r["deadline_rule"]), r["filing"]))
            n_cal += cur.rowcount
        stats["calendar_rules"] = n_cal

        # ---- RBI crawl -> staging (text still missing; Phase 2 fetches it)
        rbi_src = cur.execute("SELECT source_id FROM source WHERE name='RBI Circulars Index'").fetchone()[0]
        n_doc = 0
        for f in sorted(glob.glob(str(DATA / "raw" / "rbi" / "*.json"))):
            for d in json.loads(Path(f).read_text()):
                cur.execute("""INSERT INTO regulatory_document(source_id,title,url,file_type,raw_text,processed_status)
                               VALUES (%s,%s,%s,'HTML',NULLIF(%s,''),'pending') ON CONFLICT (url) DO NOTHING""",
                            (rbi_src, d["title"][:300], d["source_url"], d["full_text"]))
                n_doc += cur.rowcount
        stats["rbi_documents_staged"] = n_doc

        for t, col in (("jurisdiction", "jurisdiction_id"), ("industry_sector", "sector_id"), ("source", "source_id"), ("regulation", "regulation_id")):
            ident(t, col)
        c.commit()
    return stats


if __name__ == "__main__":
    print(json.dumps(load(sys.argv[1]), indent=2))
