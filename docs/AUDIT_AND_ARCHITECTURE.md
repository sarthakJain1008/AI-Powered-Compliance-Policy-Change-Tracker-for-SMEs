# Report Audit and Backend Architecture

Source: `ADBMS_Project_Report.pdf` (18 pages), plus the data currently in `data/`.
Date of audit: 2026-11-17.

---

## Part 1 - Audit

### 1.1 What the report does well
- Clear problem, clear users, and a defensible gap (SME-first, affordable, AI + audit trail).
- 17 tables, 3NF, bridge tables resolve every M:N correctly, and a temporal `RegulationVersion` is the right centre of gravity.
- Covers the ADBMS topics a grader looks for: temporal queries, views, triggers, composite indexes, partitioning, audit.
- "LLM extracts, database stores" framing is sound.

### 1.2 Schema defects (fix before writing any code)

| # | Issue | Why it matters | Fix |
|---|-------|----------------|-----|
| S1 | **No place to store applicability thresholds.** Report promises threshold-based applicability (employees, turnover) but `Obligation` has no such columns. Your own `seeds/obligations.json` already has `applies_to_min_employees/turnover`. | Relevance engine cannot be done in SQL. | Add `ObligationApplicability(obligation_id, min_employees, max_employees, min_turnover, max_turnover, sector_id?, jurisdiction_id?, condition_json)` or put columns on `Obligation`. |
| S2 | **Obligations hang off a version, so every amendment clones them.** `CompanyObligation` then points at a dead obligation row; roll-forward and history break. | Core feature (amendment -> tasks update) is undefined. | Add stable `obligation_key` and `supersedes_obligation_id`; `CompanyObligation` references the key and a current `obligation_id`. |
| S3 | **Recurring tasks have no period.** One `Task` per obligation cannot represent "GSTR-3B for Oct" vs "for Nov". | Duplicates, no per-period evidence. | Add `period_start`, `period_end` to `Task`; `UNIQUE(company_obligation_id, period_start)`. |
| S4 | **`Task.status = overdue` is stored but derivable.** | Goes stale at midnight; trigger or cron needed just to stay correct. | Remove from the CHECK. Compute `overdue` in the view (`due_date < today AND status <> completed`). |
| S5 | **Valid-time only, no transaction-time.** Report cannot answer "what did we *believe* applied on 1 Jan, as of 15 Jan?" | An extraction mistake that is later corrected silently rewrites history. | Add `recorded_at`, `superseded_at` (or keep a `RegulationVersion` history table). |
| S6 | **Overlapping versions are allowed.** Only `effective_to >= effective_from` is checked. | Two "current" versions of one regulation. | PostgreSQL `EXCLUDE USING gist (regulation_id WITH =, daterange(effective_from, effective_to, '[]') WITH &&)`. This also rules out MySQL. |
| S7 | **Regulation is flat, data is not.** You hold 34,244 *sections* (`indian_laws`) and RBI *circulars*. Schema has nowhere for sections, and a circular is an instrument that amends or implements an Act, not a Regulation. | Cannot say "Section 135 of Companies Act changed". | Add `RegulationSection(section_id, version_id, section_no, heading, text)`; add `instrument_type` and `parent_regulation_id` (Act -> Rules -> Circular). |
| S8 | **No relevance record.** "Relevance score" is promised in 1.2, 2.2 and req #5, but the only score column is `CompanyObligation.risk_score`. | No explanation, no per-change feed per company. | Add `CompanyImpact(company_id, version_id, relevance_score, reason_json, status: new/seen/dismissed/actioned)`. This is the table behind the Change Feed screen. |
| S9 | **Human review is promised, not modelled.** Only `confidence_score` on the link table. | Review queue screen has nothing to read. | Add `review_status`, `reviewed_by`, `reviewed_at` on `RegulationVersion`, `Obligation`, `DocumentRegulationLink`. |
| S10 | **AI is not auditable.** Section 2.4 sells "auditable, restartable" agents, but there is no run table. | Cannot replay or compare model/prompt versions. | Add `AgentRun(run_id, agent, document_id, model, prompt_version, input_hash, output_json, status, cost, started_at, finished_at)`. |
| S11 | **NL query (req #10) has no storage.** | No retrieval possible. | `pgvector` column on `RegulationSection` and `RegulationVersion.summary_text`. |
| S12 | **`Control` is a domain entity (4.2) but absent from the schema.** | Inconsistent report. | Either add `Control` + `ObligationControl` or delete it from 4.2. Recommend deleting for scope. |
| S13 | **`User.company_id` and `UserCompanyRole` overlap**, and role exists twice. | Two sources of truth for permissions. | Drop `User.company_id`; keep `UserCompanyRole` only. Keep a global `is_platform_admin`. |
| S14 | **No tenant isolation.** Multi-tenancy is a requirement (#13) but nothing enforces it. | One missing `WHERE company_id` leaks another client's data. | PostgreSQL Row Level Security keyed on `app.current_company_ids`. |
| S15 | **Audit trigger cannot know the user.** DB triggers only see the DB role. | `AuditLog.user_id` ends up null. | App sets `SET LOCAL app.user_id` per transaction; trigger reads it. Revoke `UPDATE/DELETE` on `AuditLog` to make it truly immutable. |
| S16 | **Partitioned `AuditLog` PK.** `log_id BIGINT PK` is not valid on a range-partitioned table unless the partition key is in the PK. | DDL will fail. | `PRIMARY KEY (timestamp, log_id)`. |
| S17 | **Risk-score trigger.** Recomputing derived scores in triggers on the table they read from risks recursion and hides logic. | Hard to test. | Put scoring in one SQL function, called from the pipeline and from a status-change trigger, with a unit-test table of expected scores. |
| S18 | **Missing indexes/constraints:** `RegulatoryDocument.content_hash` (dedupe on content, not just URL), GIN on `Regulation` text search, partial index on `Task WHERE status <> 'completed'`. | URL-only dedupe misses re-posted PDFs. | Add them. |

### 1.3 Report/prose issues
- Section 5.3 leaves the stack open ("Node.js, Django or FastAPI", "PostgreSQL or MySQL"). Commit: **FastAPI + PostgreSQL 16 + pgvector**. MySQL cannot do S6.
- Non-functional requirements (4.4) have no numbers. Add targets, e.g. dashboard < 300 ms at 500 companies x 2,000 tasks, document-to-alert latency < 24 h, extraction precision measured on a labelled set.
- No evaluation plan for the AI. Add a 50-100 document labelled set and report precision/recall for change-type, sector mapping, effective date.
- Section 5.1 omits India-specific incumbents (compliance-calendar and filing-service products such as ClearTax, Vakilsearch, Zolvit). Name them and say how you differ. Verify each claim before citing.
- Several "Supported by existing systems?" cells are unsourced assertions. Add references or soften.
- Requirements #3, #4, #11, #12 are marked "not novel"; that is honest but weakens the pitch. Frame the temporal/transaction-time design (S5/S6) as the novelty for #3.
- Obligation `default_deadline_offset_days` assumes "days from effective date", but most Indian filings are *calendar-anchored* ("11th of next month", "30 Sept"). Needs a `deadline_rule` (type + params), not a single integer. The statutory calendar you built already shows this.

### 1.4 Data audit (what is actually in `data/`)

| Asset | State | Problem |
|-------|-------|---------|
| `datasets/indian_laws` | 34,244 sections, 2,408 in the 25 target acts, +20 for DPDP | Static snapshot, no dates or amendment history. Good as baseline text, **not** as a change feed. |
| `seeds/*` | 35 regulations, 45 obligations, 262 sector mappings, 16 sectors, 28 jurisdictions, 20 sources | Obligations reference `regulation_id` not `version_id` (does not match the report's schema). No versions. Hand-numbered IDs. Only 11 labour regulations in 35. |
| `raw/rbi` | 485 circulars | **0 of 485 have `full_text`**, 0 have `effective_on`, 102 have the title copy-pasted into `issued_on`. So nothing can be extracted from them yet. |
| `raw/` other sources | India Code, MCA, EPFO, MeitY, SEBI = 0 docs each, yet reported "OK" | Crawler reports success on zero results. Needs a failure condition. |
| `curated/statutory_compliance_calendar.json` | 13 hardcoded rows | Dates are rules that change by year/notification; must be rows with validity, not constants. |
| Content currency | Corpus includes Income-tax Act 1961 and pre-labour-code wage/PF acts | The Income-tax Act 2025 and the four Labour Codes have superseded or are superseding these. Verify effective dates against official sources, then model them as real repeal/replace versions. This is your best demo of the temporal design. |
| `HF kanoonhq/open-laws`, `dotzcode/...v2` | Failed (error / gated) | Not usable yet. |

**Bottom line:** the schema is close; the data is the real risk. Fetching the *text* of circulars (PDF) is the first blocker for the whole pipeline.

---

## Part 2 - Data architecture

### 2.1 Layers (medallion style, all in one PostgreSQL + object store)

```
 L0  RAW (immutable)         object store: raw HTML/PDF, content-hash named
 L1  STAGING                 RegulatoryDocument (+ parsed text, chunks)
 L2  CANONICAL (temporal)    Regulation, RegulationVersion, RegulationSection, Obligation
 L3  TENANT                  Company*, CompanyImpact, CompanyObligation, Task
 L4  SERVING                 views / materialised views, vector index, search index
 --  CROSS-CUTTING           AgentRun, AuditLog, review queues
```

Rules: a layer only reads from the layer above it; L0 is never edited; every L2 row points to the L1 document and `AgentRun` that produced it; L3 is the only layer with tenant data and the only one under RLS.

### 2.2 Additions to the report's 17 tables
`RegulationSection`, `ObligationApplicability`, `CompanyImpact`, `AgentRun`, `Notification`, `ComplianceCalendarRule` (replaces hardcoded calendar), `DocumentChunk` (embeddings). Total ~24 tables.

### 2.3 Key queries the schema must serve
1. Applicable regulations on date D: `Company -> CompanySector -> RegulationSector -> RegulationVersion WHERE D BETWEEN effective_from AND COALESCE(effective_to, 'infinity')`, with jurisdiction resolved by a recursive CTE over company locations.
2. Diff of version N vs N-1 at section level.
3. Change feed per company ordered by relevance and recency.
4. Next 30 days of due tasks, per company and per consultant portfolio.
5. Regulations that generated most tasks last quarter (analytics view).

---

## Part 3 - Pipeline

Principle: **the LLM extracts and explains; SQL decides.** Applicability is a deterministic query. The LLM is used only where text must be interpreted, and every output carries a confidence and lands in a review state.

```
 Sources --> [1 Monitor] --> [2 Parse] --> [3 Extract] --> [4 Resolve+Version]
                                                                 |
 Notify <-- [7 Task gen] <-- [6 Obligation link] <-- [5 Impact map]
```

| Stage | Input -> Output | Detail |
|-------|-----------------|--------|
| 1 Monitor | `Source` -> `RegulatoryDocument(pending)` | Scheduler per `crawl_frequency`. Conditional GET, `content_hash`, store raw blob. Dedupe on URL **and** hash. Zero results on an active source = alert, not success. |
| 2 Parse | raw blob -> `raw_text`, `DocumentChunk` | HTML via readability, text PDF via pdftotext, scanned PDF via OCR fallback. Chunk by section/heading. |
| 3 Extract (LLM) | text -> structured JSON | Title, issuer, instrument type, issue/effective date, change type, target regulation, affected sectors, obligations. JSON-schema constrained output, per-field confidence, `AgentRun` row. |
| 4 Resolve + Version | JSON -> `RegulationVersion` | Match target regulation (exact short-name, then trigram, then embedding). In **one transaction**: close prior version (`effective_to`), insert new, build section diff. Confidence < threshold -> `review_status = needs_review`, nothing published. |
| 5 Impact map | version -> `CompanyImpact` | SQL: sector + jurisdiction hierarchy + thresholds -> relevance score. LLM only writes the plain-language "why it affects you" text. |
| 6 Obligation link | version -> `Obligation` (+ applicability) | New or superseding obligations via `obligation_key`; `CompanyObligation` created or re-pointed. |
| 7 Task gen | `CompanyObligation` -> `Task` | One task per period from `ComplianceCalendarRule`; assign by `responsible_role`; risk score via the single scoring function. |
| 8 Notify | `CompanyImpact`/`Task` -> email/in-app | Outbox pattern so retries never double-send. |

Operational design:
- **Queue:** Postgres `SELECT ... FOR UPDATE SKIP LOCKED` job table. No Redis/Celery needed at this scale, and jobs are transactional with the data.
- **Idempotency:** every stage keyed on `(document_id, stage, input_hash)`; reruns are safe.
- **Failure:** `processed_status = failed` with error text and retry count; admin screen can requeue.
- **Cost control:** extraction only runs for new content hashes; small model for classification, larger one for extraction; cache by `input_hash`.
- **Bootstrap (one-off):** load `seeds/` -> reference tables; load 2,428 curated sections -> `RegulationSection` as version 1 of each Act; load the calendar as `ComplianceCalendarRule`. Then the live pipeline only handles *changes*.

---

## Part 4 - System

```
 React/Next.js  --->  FastAPI (REST, JWT)  --->  PostgreSQL 16 (+pgvector, RLS)
                           |                        ^
                           +--> Worker(s) ----------+---> Object store (raw files)
                                  |
                                  +--> LLM API, source fetchers
```

Backend layout (`backend/`):
```
app/api/        routers: auth, companies, regulations, impacts, obligations, tasks, ask, admin
app/core/       config, security, db session (sets app.user_id / tenant for RLS)
app/models/     SQLAlchemy models        alembic/   migrations
app/pipeline/   monitor.py parse.py extract.py version.py impact.py tasks.py notify.py
app/llm/        client, prompts (versioned), JSON schemas
app/sql/        views, functions (risk score, applicability), triggers
tests/          schema tests, pipeline tests on fixture documents, scoring table tests
```

### API surface (v1)
- Auth: `POST /auth/login`, `GET /me`
- Company: `POST/GET/PATCH /companies`, `/companies/{id}/profile`, `/companies/{id}/members`
- Knowledge: `GET /regulations?on=YYYY-MM-DD&q=`, `GET /regulations/{id}/versions`, `GET /versions/{id}/diff?against=`
- Impact: `GET /companies/{id}/impacts`, `PATCH /impacts/{id}` (seen/dismiss/action)
- Obligations/tasks: `GET /companies/{id}/obligations`, `GET/POST/PATCH /tasks`, `GET /companies/{id}/calendar`
- Dashboard: `GET /companies/{id}/dashboard`, `GET /portfolio` (consultant)
- Ask: `POST /companies/{id}/ask`
- Admin: `GET/POST /admin/sources`, `/admin/documents?status=`, `/admin/review-queue`, `POST /admin/documents/{id}/reprocess`
- Audit: `GET /companies/{id}/audit`

### NL query (req #10)
Two modes behind one endpoint: (a) **retrieval** over `DocumentChunk` embeddings for "what does X say", (b) **restricted SQL** over the serving views only (read-only role, row limit, company-scoped RLS) for "what is due this quarter". Never give the model write access or raw tables.

---

## Part 5 - Screens

**Company user (founder / manager / employee)**
1. **Onboarding wizard** - name, registration no., sectors, locations, headcount, turnover. Ends with "we found N applicable regulations and M obligations."
2. **Dashboard** - risk score, overdue count, due in 7/30 days, newest changes, tasks by owner.
3. **Change feed** - cards: plain-language summary, change type badge, effective date, relevance, [View] [Create tasks] [Dismiss].
4. **Change detail** - summary, "why this affects you", section-level diff, source link, derived obligations, confidence.
5. **Regulation library** - search/filter by sector, authority, jurisdiction; **"as of" date picker** (time travel).
6. **Regulation timeline** - versions on a time axis with amendments and repeals.
7. **Obligation register** - table: obligation, frequency, next due, owner, risk, status.
8. **Tasks** - list / board / calendar; assign, comment, attach evidence, complete.
9. **Compliance calendar** - month view of statutory deadlines for this company.
10. **Ask** - chat with cited sources and linked records.
11. **Audit log** - filterable, exportable (inspection evidence).
12. **Settings** - profile, members and roles, notification preferences.

**Consultant / CA / incubator**
13. **Portfolio** - all client companies, overdue and risk heat-map, switch tenant.

**Admin / curator**
14. **Sources** - add/edit sources, last crawl, health.
15. **Ingestion monitor** - documents by status, failures, requeue.
16. **Review queue** - low-confidence extractions side-by-side with source text; approve / edit / reject.
17. **Reference data** - sectors, jurisdictions, applicability rules.

Build order for demo value: 1 -> 2 -> 3/4 -> 8 -> 5/6 -> 16 -> rest.

---

## Part 6 - Build plan

| Phase | Deliverable | Exit test |
|-------|-------------|-----------|
| 0 | Fix report schema (S1-S18), write DDL + Alembic migration, RLS, triggers, views | Schema tests pass; temporal "as of" query returns right version on fixtures |
| 1 | Load seeds + curated data; fix seed IDs/versions; Income-tax Act 1961 -> 2025 and labour-code transitions as real versioned data | Query "applicable on 2026-03-31 vs 2026-04-02" differs correctly |
| 2 | Fix crawler: get circular **text** (RBI PDFs), fail on zero results; Monitor + Parse stages | 100% of RBI docs have `raw_text` |
| 3 | Extract + Resolve/Version with review queue; labelled eval set | Reported precision/recall on eval set |
| 4 | Impact map, obligation link, task gen, notify | Company profile -> feed + tasks end to end |
| 5 | API + auth + audit; then frontend screens in the order above | Demo script runs |
| 6 | NL query, portfolio view, analytics views, partitioning benchmark | Report's query/index claims backed by `EXPLAIN` numbers |

## Decisions I have assumed (change any)
FastAPI + PostgreSQL 16 + pgvector, SQLAlchemy + Alembic, Postgres-backed job queue, Next.js frontend, Claude API for extraction, raw files on local disk first then S3-compatible.
