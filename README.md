# AI-Powered Compliance & Policy Change Tracker for SMEs

> **A versioned, temporal regulatory-compliance database with AI-driven relevance filtering, obligation mapping, and automated task management for Small and Medium Enterprises.**

[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791.svg)](https://www.postgresql.org/)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📌 Table of Contents
- [Executive Overview](#-executive-overview)
- [The Problem We Solve](#-the-problem-we-solve)
- [Key Features & Capabilities](#-key-features--capabilities)
- [System Architecture](#-system-architecture)
- [Multi-Agent AI Pipeline](#-multi-agent-ai-pipeline)
- [Authoritative Legal Data Layer](#-authoritative-legal-data-layer)
- [Database Schema & Architecture (3NF)](#-database-schema--architecture-3nf)
- [Technology Stack](#-technology-stack)
- [Project Directory Structure](#-project-directory-structure)
- [Installation & Setup](#-installation--setup)
- [Execution & Crawlers](#-execution--crawlers)
- [Project Roadmap](#-project-roadmap)
- [Team & Academic Credits](#-team--academic-credits)

---

## 🏢 Executive Overview

Small and medium enterprises (SMEs) and early-stage startups in India operate in an increasingly complex and dynamic regulatory web. They must juggle **Corporate Law (MCA)**, **Taxation (GST, TDS, Income Tax)**, **Labour & Employment Acts (EPF, ESI, Gratuity, POSH, Minimum Wages)**, **Data Protection (DPDP Act 2023)**, and sector regulators like **RBI, SEBI, FSSAI, and DPIIT**.

Enterprise Governance, Risk, and Compliance (GRC) tools (such as RSA Archer, MetricStream, or ServiceNow GRC) are built for Fortune 500 companies with dedicated legal teams, costing tens of thousands of dollars annually. Conversely, free government websites and gazettes publish unstructured PDFs, circulars, and notifications without telling founders *what actions to take, by when, or who is responsible*.

**AI-Powered Compliance Tracker for SMEs** bridges this critical gap. It is an end-to-end, multi-tenant intelligence platform that crawls authoritative government sources, extracts versioned statutory changes using AI, personalizes relevance to each company's exact sector and threshold, and automatically produces an actionable compliance calendar with assigned tasks, deadlines, and risk scores.

---

## ⚠️ The Problem We Solve

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            THE SME COMPLIANCE TRAP                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. No In-House Legal Team    → Handled part-time by founders or accountants │
│ 2. Severe Penalties          → Late fees, license cancellations, director   │
│                                personal liabilities                        │
│ 3. Fragmented Sources        → MCA, RBI, GSTN, Gazette, EPFO all publish    │
│                                differently                                  │
│ 4. Unstructured Content      → Scanned PDFs, legal jargon, no clear checklist│
│ 5. Threshold Ignorance       → Unaware when hiring the 10th or 20th person  │
│                                triggers ESI, POSH, or EPF liabilities       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Key Features & Capabilities

### 1. Authoritative Multi-Source Ingestion
- Crawls and monitors primary government portals (**India Code**, **eGazette**, **MCA**, **RBI**, **CBIC/GST**, **EPFO**, **MeitY**, **SEBI**, **DPIIT**).
- Idempotent document ingestion with SHA-256 deduplication and change tracking.

### 2. Temporal & Versioned Legal Database
- Regulations are explicitly modelled with valid-time ranges (`effective_from` and `effective_to`).
- Preserves complete legislative history to answer temporal queries like *"What was the exact compliance status and applicable labour law on January 1, 2024?"*

### 3. SME-First Personalization & Threshold Engine
- Matches generic statutory changes to a company's specific profile:
  - **Industry Sector** (e.g., IT, Fintech, Food & Beverage, Manufacturing)
  - **Jurisdiction & Locations** (Central + State specifics e.g., Karnataka, Maharashtra)
  - **Employee Headcount** (1, 10, 20, 50, 100 employee regulatory trigger points)
  - **Annual Turnover & Capital** (e.g., ₹20L/₹40L GST thresholds, ₹2Cr audit thresholds)

### 4. Plain-Language AI Summarization & Obligation Mapping
- Automatically translates dense legal gazette notifications into plain English:
  - *What changed?*
  - *Does this affect my business?*
  - *What specific action is required?*

### 5. Automated Workflow & Task Management
- Derives concrete tasks from statutory obligations with rolling deadlines:
  - Examples: *"File Form INC-20A within 180 days of incorporation"*, *"Constitute POSH ICC Committee (10+ employees)"*, *"Deposit monthly EPF by 15th"*.
- Automatic recurrence roll-forward (monthly, quarterly, half-yearly, annual).

### 6. Dynamic Risk Scoring Engine
- Computes risk scores (0–100) based on statutory penalty severity, overdue probability, and issuing regulator authority.

### 7. Immutable Audit Trail
- Automated PostgreSQL database triggers that capture before-and-after JSON snapshots of all task and obligation state changes for audit evidence during inspections.

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    subgraph Sources["📡 Layer 1: Authoritative Government Sources"]
        S1["India Code\n(All Central Acts)"]
        S2["eGazette of India\n(Official Notifications)"]
        S3["MCA21\n(Companies Act & Rules)"]
        S4["RBI Portal\n(Master Directions & Circulars)"]
        S5["CBIC & GSTN\n(Tax & Rate Schedules)"]
        S6["Labour Ministries\n(EPFO, ESIC, State Depts)"]
        S7["MeitY / DPBI\n(DPDP Act & IT Rules)"]
        S8["CGPDTM / DPIIT\n(Patents, Trademarks, Startups)"]
    end

    subgraph Ingestion["🔄 Ingestion & Extraction Engine"]
        I1["Scheduled Crawlers\n(Daily / Weekly / Monthly)"]
        I2["Deduplication & Hashing\n(SHA-256)"]
        I3["RegulatoryDocument Store\n(Pending / Processed / Failed)"]
    end

    subgraph Agents["🤖 Multi-Agent AI Pipeline"]
        A1["Extraction Agent\n(Gemini 1.5 Pro / Flash)"]
        A2["Classification & Mapping Agent\n(Sector & Threshold Matcher)"]
        A3["Task & Obligation Agent\n(Deadline & Role Generator)"]
        A4["Natural Language Query Agent\n(Context-Aware Chat)"]
    end

    subgraph Database["🗄️ PostgreSQL Database (3NF Relational Store)"]
        DB1["Jurisdictions & IndustrySectors"]
        DB2["Regulations & RegulationVersions (Temporal)"]
        DB3["Company Profiles, Locations & Thresholds"]
        DB4["CompanyObligations & Actionable Tasks"]
        DB5["Partitioned AuditLog & Triggers"]
    end

    subgraph Frontend["💻 User Experience (Next.js 14)"]
        UI1["Founder & Executive Dashboard"]
        UI2["Actionable Compliance Task Board"]
        UI3["Temporal Regulation Explorer"]
        UI4["Patent & Startup Incorporation Hub"]
        UI5["AI Compliance Assistant (RAG Chat)"]
    end

    Sources --> Ingestion
    Ingestion --> Agents
    Agents --> Database
    Database --> Frontend
```

---

## 🤖 Multi-Agent AI Pipeline

Rather than relying on an untraceable monolithic chatbot, the system utilizes specialized cooperating agents writing to strictly typed database tables:

| Agent | Responsibility | Primary Tables Written | LLM / Tech |
|---|---|---|---|
| **Monitoring Agent** | Scans configured government portals, checks RSS/HTML/PDFs, enforces idempotency. | `RegulatoryDocument` | Python, BeautifulSoup, Requests |
| **Extraction Agent** | Parses raw legal gazettes, extracts issuing authority, effective date, change type (new/amendment/repeal), and affected sectors. | `Regulation`, `RegulationVersion` | Gemini API, Structured JSON output |
| **Classification Agent** | Evaluates company profile against legislation applicability criteria (headcount, turnover, sector, location). | `RegulationSector`, `CompanyObligation`, `DocumentRegulationLink` | Gemini API, Pydantic |
| **Task Generation Agent** | Converts obligations into discrete tasks with responsible roles (CFO, CS, HR), statutory deadlines, and risk scores. | `Task`, `CompanyObligation` | Rule Engine + Gemini |
| **Natural Language Query Agent** | Answers conversational queries (*"What filings are due for my SaaS startup this month?"*). | Read-only | RAG with pgvector / Full-Text Search |

---

## 📚 Authoritative Legal Data Layer

Our legal data layer is built on a **two-layer architecture**:
1. **Layer 1 (Authoritative Corpus)**: Official primary sources only (Statutes, Gazette notifications, Regulator circulars).
2. **Layer 2 (Discovery & Enrichment)**: Explanatory notes, law firm analyses, and court precedents.

### Curated Datasets Included in the Repository
Located in the `data/` directory:

- **Central Acts & Statutes Corpus** (`data/datasets/indian_laws/`):
  - **1,021 Indian Acts** and **34,244 sections** containing the complete statutory legal text.
- **Curated Business Statutes** (`data/curated/business_acts_sections.json`):
  - **2,428 indexed sections** across 26 business-critical acts including:
    - *Companies Act, 2013* (470 sections)
    - *Central Goods and Services Tax Act, 2017* (174 sections)
    - *Income-Tax Act, 1961* (283 sections)
    - *Digital Personal Data Protection Act, 2023* (All 44 sections)
    - *Patents Act, 1970* & *Patent Rules, 2024*
    - *Trade Marks Act, 1999* (144 sections)
    - *Copyright Act, 1957* (79 sections)
    - *Information Technology Act, 2000* (94 sections)
    - *Insolvency and Bankruptcy Code, 2016* (255 sections)
    - *Employees Provident Funds Act, 1952*, *ESI Act, 1948*, *POSH Act, 2013*, *Factories Act, 1948*, *Gratuity Act, 1972*, *Bonus Act, 1965*, *Maternity Benefit Act, 1961*.
- **Startup Lifecycle & Incorporation Engine** (`data/curated/startup_lifecycle_stages.json`):
  - Step-by-step guidance from Idea $\to$ SPICe+ (INC-32) $\to$ INC-20A (Commencement of Business) $\to$ DPIIT Startup Recognition $\to$ IP Filing $\to$ Tax Holiday (80-IAC).
- **Comprehensive Patent & IP Guide** (`data/curated/patent_and_ip_guide.json`):
  - Statutory forms (Forms 1, 2, 3, 5, 9, 18, 18A for Startups), fee schedules, Nice classifications, and the **80% fee rebate & expedited examination (Form 18A)** for startups.
- **Threshold-Based Applicability Matrix** (`data/curated/threshold_applicability_matrix.json`):
  - Maps legal obligations dynamically across headcount thresholds (1, 10, 20, 50, 100 employees) and financial thresholds (₹20L, ₹40L, ₹2Cr, ₹500Cr).
- **Master Compliance Calendar** (`data/curated/statutory_compliance_calendar.json`):
  - Canonical recurring deadlines for MCA (AOC-4, MGT-7/7A, DIR-3 KYC), GST (GSTR-1, GSTR-3B, GSTR-9), TDS (Form 24Q, 26Q), PF & ESI, Advance Tax installments.
- **Live Regulatory Corpus** (`data/raw/`):
  - **485+ live documents** crawled directly from the Reserve Bank of India (RBI Master Directions, Circulars, Notifications).

---

## 🗄️ Database Schema & Architecture (3NF)

The database schema is fully normalized to **Third Normal Form (3NF)** across **17 interconnected tables**:

```mermaid
erDiagram
    Jurisdiction ||--o{ Jurisdiction : "parent_hierarchy"
    Jurisdiction ||--o{ Source : "monitors"
    Jurisdiction ||--o{ Regulation : "enacts"
    Jurisdiction ||--o{ Company : "headquarters"
    Jurisdiction ||--o{ CompanyLocation : "operates_in"

    Regulation ||--o{ RegulationVersion : "versioned_as"
    Regulation }o--o{ IndustrySector : "RegulationSector"

    RegulationVersion ||--o{ Obligation : "imposes"
    RegulationVersion }o--o{ RegulatoryDocument : "DocumentRegulationLink"

    Company }o--o{ IndustrySector : "CompanySector"
    Company ||--o{ CompanyLocation : "branches"
    Company }o--o{ Obligation : "CompanyObligation"
    Company }o--o{ User : "UserCompanyRole"

    CompanyObligation ||--o{ Task : "triggers"

    User ||--o{ Task : "assigned_to"
    User ||--o{ AuditLog : "performed_by"
    Source ||--o{ RegulatoryDocument : "publishes"
```

### Table Dictionary (Summary)
1. `Jurisdiction`: Country, state, or regulatory body (self-referencing hierarchy).
2. `IndustrySector`: Categories of business (NIC code alignment).
3. `Source`: Monitored publication channels (MCA, RBI, Gazette, etc.).
4. `Regulation`: Master records of laws, acts, and guidelines.
5. `RegulationSector`: Bridge table resolving M:N relationship between regulations and sectors.
6. `RegulationVersion`: **Temporal table** tracking version validity periods (`effective_from`, `effective_to`, `change_type`).
7. `Company`: SME profile (incorporation number, headcount, turnover, primary jurisdiction).
8. `CompanySector`: Bridge table for multi-sector enterprises.
9. `CompanyLocation`: Operating branch locations and state-level jurisdictions.
10. `Obligation`: Specific compliance requirements derived from a regulation version.
11. `CompanyObligation`: Company-specific compliance register with risk scores and next due dates.
12. `Task`: Actionable items assigned to users with statuses (`pending`, `in_progress`, `completed`, `overdue`).
13. `User`: Role-based user accounts (`admin`, `manager`, `employee`, `consultant`).
14. `UserCompanyRole`: Multi-tenant bridge allowing consultants to manage multiple client SMEs.
15. `RegulatoryDocument`: Ingested raw documents, URLs, publication dates, and processing states.
16. `DocumentRegulationLink`: Bridge connecting ingested documents to versions with AI confidence scores.
17. `AuditLog`: Immutable, date-partitioned audit trail populated by database triggers.

---

## 🛠️ Technology Stack

| Layer | Technology | Justification |
|---|---|---|
| **Backend Framework** | **FastAPI (Python 3.11)** | High-performance asynchronous REST API, native Pydantic validation, seamless integration with AI libraries. |
| **Relational Database** | **PostgreSQL 15+** | Robust ACID compliance, native table partitioning, date-range types for temporal queries, trigger procedures. |
| **Database ORM** | **SQLAlchemy 2.0 + Alembic** | Type-safe query building, version-controlled schema migrations. |
| **AI & LLM Orchestration** | **Google Gemini API (1.5 Flash / Pro)** | Exceptional context window for processing long gazette texts, structured JSON mode, cost-effective inference. |
| **Data Ingestion** | **BeautifulSoup4, Requests, LXML** | Robust web scraping, PDF parsing, automated OGD and portal harvesting. |
| **Frontend Framework** | **Next.js 14 (React & TypeScript)** | Server-side rendering (SSR), responsive interactive dashboards, Tailwind CSS. |
| **Authentication** | **JWT & Passlib (Bcrypt)** | Stateless token-based security supporting multi-tenant role-based access control. |
| **Task Scheduling** | **APScheduler / Celery + Redis** | Tiered scheduled crawler jobs (Daily, Weekly, Monthly) and asynchronous pipeline execution. |

---

## 📁 Project Directory Structure

```
AI-Powered-Compliance-Policy-Change-Tracker-for-SMEs/
├── backend/                         # FastAPI Application (Phase 1)
│   ├── app/
│   │   ├── main.py                  # API entry point & routes
│   │   ├── config.py                # Environment & settings
│   │   ├── db.py                    # Database connection session
│   │   ├── models/                  # 17 SQLAlchemy ORM models
│   │   ├── schemas/                 # Pydantic request/response schemas
│   │   ├── routers/                 # Modular API endpoints
│   │   │   ├── auth.py              # Login, register, JWT
│   │   │   ├── companies.py         # Onboarding & profiles
│   │   │   ├── regulations.py       # Versioned legal browser
│   │   │   ├── obligations.py       # Compliance registers
│   │   │   └── tasks.py             # Workflow management
│   │   └── agents/                  # AI Pipeline Agents
│   │       ├── extraction.py        # Gazette structured parser
│   │       ├── classifier.py        # Relevance & mapping engine
│   │       └── task_generator.py    # Deadline & risk calculator
│   ├── alembic/                     # Database migrations
│   └── requirements.txt             # Backend dependencies
├── data/                            # Comprehensive Legal Data Layer
│   ├── curated/                     # Synthesized Datasets
│   │   ├── business_acts_sections.json     # 2,428 sections of core acts
│   │   ├── patent_and_ip_guide.json        # Forms, fees, startup rebates
│   │   ├── startup_lifecycle_stages.json   # Idea to annual filing roadmap
│   │   ├── statutory_compliance_calendar.json # Monthly & annual due dates
│   │   └── threshold_applicability_matrix.json # Headcount/turnover matrix
│   ├── datasets/                    # Large-Scale Open Legal Corpora
│   │   └── indian_laws/             # 34,244 sections across 1,021 Central Acts
│   ├── raw/                         # Live Crawled Data
│   │   ├── rbi/                     # 485 RBI master directions & circulars
│   │   ├── indiacode/               # India Code indexed handles
│   │   ├── egazette/                # Gazette notifications
│   │   └── gst/                     # GST circulars
│   ├── seeds/                       # Seed JSONs for Database Bootstrap
│   │   ├── jurisdictions.json       # 28 central & state jurisdictions
│   │   ├── industry_sectors.json    # 16 industrial categories (NIC aligned)
│   │   ├── sources.json             # 20 monitored official portals
│   │   ├── regulations.json         # 35 foundation statutes
│   │   ├── obligations.json         # 45 recurring compliance templates
│   │   └── regulation_sector_mappings.json # 262 mapping entries
│   ├── layer1_crawler.py            # Primary authoritative crawler
│   ├── build_startup_legal_corpus.py# Dataset builder and synthesizer
│   └── generate_seeds.py            # Seed data generator
├── frontend/                        # Next.js 14 Dashboard (Phase 4)
├── docker-compose.yml               # Local orchestration (Postgres, API)
├── README.md                        # Complete project documentation
└── .gitignore                       # Git ignore rules
```

---

## 💻 Installation & Setup

### Prerequisites
- **Python 3.11+** installed
- **PostgreSQL 15+** installed and running
- **Node.js 18+** (for frontend)
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/sarthakJain1008/AI-Powered-Compliance-Policy-Change-Tracker-for-SMEs.git
cd AI-Powered-Compliance-Policy-Change-Tracker-for-SMEs
```

### 2. Environment Configuration
Create a `.env` file in the root directory:
```env
# Database Settings
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/compliance_tracker
DB_HOST=localhost
DB_PORT=5432
DB_NAME=compliance_tracker
DB_USER=postgres
DB_PASSWORD=postgres

# Security & JWT
SECRET_KEY=your_super_secret_jwt_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# AI Configuration
GEMINI_API_KEY=your_google_gemini_api_key_here
```

### 3. Install Python Dependencies
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

---

## ⚡ Execution & Crawlers

### Re-Generate Curated Legal Datasets
To re-build the synthesized legal corpus from raw data:
```bash
python3.11 data/build_startup_legal_corpus.py
```

### Run Authoritative Source Crawlers
To trigger a live crawl of official regulatory portals (RBI, eGazette, GSTN):
```bash
python3.11 data/layer1_crawler.py
```

### Seed Database
Once PostgreSQL is configured, load the baseline reference data:
```bash
python3.11 data/generate_seeds.py
```

---

## 🗺️ Project Roadmap

- [x] **Phase 0: Legal Corpus & Data Engineering**
  - Download and index 34,244 sections of Central Acts from India Code.
  - Curate 2,428 sections across 26 business-critical acts (Companies Act, GST, DPDP, IT Act, Labour).
  - Build patent filing guides, startup lifecycle roadmaps, and threshold applicability matrices.
  - Deploy Layer 1 live crawler for RBI, eGazette, and CBIC.
- [ ] **Phase 1: Database & Backend Foundation**
  - Implement all 17 SQLAlchemy models with exact constraints and 3NF integrity.
  - Setup Alembic migrations and database triggers for `AuditLog`.
  - Build JWT authentication and company onboarding endpoints.
- [ ] **Phase 2: Core Business Logic & Temporal Queries**
  - Implement versioned regulation retrieval (`effective_from`, `effective_to`).
  - Automated threshold-matching engine for company profiles.
  - Obligation and task management REST endpoints.
- [ ] **Phase 3: Multi-Agent AI Pipeline Integration**
  - Ingest pending gazettes via Extraction Agent.
  - Connect Gemini 1.5 for plain-language summaries and risk scores.
  - Implement human-in-the-loop review queue for low-confidence extractions.
- [ ] **Phase 4: Next.js Frontend Dashboard**
  - Executive compliance dashboard with risk dials and impending deadlines.
  - Interactive calendar and task assignment board.
  - Temporal law comparison viewer.
- [ ] **Phase 5: RAG Chat Assistant & Multi-Tenant Consultant Portals**
  - Conversational legal assistant for contextual compliance inquiries.
  - Multi-company management console for Chartered Accountants and legal advisors.

---

## 👥 Team & Academic Credits

- **Sarthak Jain** (E23CSEU1494) — *Team Leader*
- **Kovid Chhabra** (E23CSEU1491) — *Team Member*

**Course**: Advanced Database Management Systems (ADBMS)  
**Program**: B.Tech CSE — Seventh Semester, Fourth Year  
**Faculty Guide**: Amit Chandramuni Tyagi  
**Academic Submission Date**: 29 September 2026

---

## 📜 License
Distributed under the MIT License. See `LICENSE` for more information.
