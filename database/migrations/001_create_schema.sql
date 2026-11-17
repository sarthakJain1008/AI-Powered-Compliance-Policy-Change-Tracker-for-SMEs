-- =============================================================================
-- AI-Powered Compliance & Policy Change Tracker for SMEs
-- Database Migration: 001_create_schema.sql
-- Description: Creates the complete 17-table 3NF relational schema
-- Author: Sarthak Jain (E23CSEU1494) & Kovid Chhabra (E23CSEU1491)
-- Course: Advanced Database Management Systems (ADBMS)
-- Run: psql -U postgres -d compliance_tracker -f 001_create_schema.sql
-- =============================================================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- for full-text fuzzy search on regulation titles

-- Set search path
SET search_path TO public;

-- =============================================================================
-- TABLE 1: jurisdiction
-- Self-referencing hierarchy: country -> state -> regulator
-- =============================================================================
CREATE TABLE IF NOT EXISTS jurisdiction (
    jurisdiction_id   SERIAL PRIMARY KEY,
    name              VARCHAR(100)  NOT NULL,
    type              VARCHAR(20)   NOT NULL CHECK (type IN ('country', 'state', 'regulator', 'city')),
    parent_jurisdiction_id INT       REFERENCES jurisdiction(jurisdiction_id) ON DELETE RESTRICT,
    created_at        TIMESTAMP     NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_jurisdiction_name_type UNIQUE (name, type)
);

COMMENT ON TABLE  jurisdiction                     IS 'Hierarchical registry of countries, states, cities and regulatory bodies.';
COMMENT ON COLUMN jurisdiction.type                IS 'Level in the hierarchy: country > state/city > regulator.';
COMMENT ON COLUMN jurisdiction.parent_jurisdiction_id IS 'NULL for top-level (India). Points to parent for state/city/regulator.';

-- =============================================================================
-- TABLE 2: industry_sector
-- NIC-aligned industry categories used to match regulations to companies.
-- =============================================================================
CREATE TABLE IF NOT EXISTS industry_sector (
    sector_id    SERIAL PRIMARY KEY,
    name         VARCHAR(100) NOT NULL UNIQUE,
    description  TEXT,
    created_at   TIMESTAMP    NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE industry_sector IS 'Industry categories (NIC-aligned) used to match regulations to companies.';

-- =============================================================================
-- TABLE 3: source
-- Monitored regulatory publication channels (portals, RSS, PDF repos).
-- =============================================================================
CREATE TABLE IF NOT EXISTS source (
    source_id       SERIAL PRIMARY KEY,
    name            VARCHAR(150) NOT NULL,
    url             VARCHAR(500) NOT NULL UNIQUE,
    source_type     VARCHAR(20)  NOT NULL CHECK (source_type IN ('website', 'rss', 'gazette', 'pdf_repo', 'api')),
    jurisdiction_id INT          REFERENCES jurisdiction(jurisdiction_id) ON DELETE SET NULL,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    crawl_frequency VARCHAR(20)  NOT NULL DEFAULT 'daily' CHECK (crawl_frequency IN ('hourly', 'daily', 'weekly', 'manual')),
    last_crawled_at TIMESTAMP,
    created_at      TIMESTAMP    NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE source IS 'Configured regulatory publication channels monitored by the ingestion pipeline.';

-- =============================================================================
-- TABLE 4: regulation
-- Master record of a law, rule or guideline.
-- =============================================================================
CREATE TABLE IF NOT EXISTS regulation (
    regulation_id       SERIAL PRIMARY KEY,
    title               VARCHAR(300) NOT NULL,
    short_name          VARCHAR(100),
    jurisdiction_id     INT          NOT NULL REFERENCES jurisdiction(jurisdiction_id) ON DELETE RESTRICT,
    status              VARCHAR(15)  NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'repealed', 'draft', 'suspended')),
    first_effective_date DATE,
    created_at          TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_regulation_jurisdiction ON regulation(jurisdiction_id);
CREATE INDEX IF NOT EXISTS idx_regulation_status       ON regulation(status);

COMMENT ON TABLE regulation IS 'Master record of each law, rule, or guideline (e.g., DPDP Act 2023, GST Act).';

-- =============================================================================
-- TABLE 5: regulation_sector  (bridge: Regulation <-> IndustrySector)
-- =============================================================================
CREATE TABLE IF NOT EXISTS regulation_sector (
    regulation_id INT NOT NULL REFERENCES regulation(regulation_id) ON DELETE CASCADE,
    sector_id     INT NOT NULL REFERENCES industry_sector(sector_id) ON DELETE CASCADE,
    PRIMARY KEY (regulation_id, sector_id)
);

COMMENT ON TABLE regulation_sector IS 'Many-to-many bridge: which industry sectors each regulation applies to.';

-- =============================================================================
-- TABLE 6: regulation_version
-- TEMPORAL TABLE — each row is a versioned snapshot with an effective period.
-- Core ADBMS concept: bi-temporal / valid-time modeling.
-- =============================================================================
CREATE TABLE IF NOT EXISTS regulation_version (
    version_id      SERIAL PRIMARY KEY,
    regulation_id   INT          NOT NULL REFERENCES regulation(regulation_id) ON DELETE CASCADE,
    version_number  VARCHAR(50)  NOT NULL,                           -- e.g. "1.0", "Amendment 2025"
    effective_from  DATE         NOT NULL,
    effective_to    DATE         CHECK (effective_to >= effective_from), -- NULL = currently active
    document_url    VARCHAR(500),
    summary_text    TEXT,                                             -- AI-generated plain-language summary
    full_text       TEXT,                                             -- Full legal text (or external ref)
    change_type     VARCHAR(20)  NOT NULL CHECK (change_type IN ('new', 'amendment', 'clarification', 'repeal')),
    ai_confidence   DECIMAL(5,2) CHECK (ai_confidence BETWEEN 0 AND 100), -- confidence of AI extraction
    created_at      TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- Temporal index — optimised for "what applied on date D" queries
CREATE INDEX IF NOT EXISTS idx_regver_temporal       ON regulation_version(effective_from, effective_to);
CREATE INDEX IF NOT EXISTS idx_regver_regulation     ON regulation_version(regulation_id);
CREATE INDEX IF NOT EXISTS idx_regver_change_type    ON regulation_version(change_type);

COMMENT ON TABLE  regulation_version             IS 'Temporal snapshots of each regulation. Central to the ADBMS design.';
COMMENT ON COLUMN regulation_version.effective_to IS 'NULL means this is the currently active version.';

-- =============================================================================
-- TABLE 7: regulatory_document
-- Raw ingested documents before AI processing.
-- =============================================================================
CREATE TABLE IF NOT EXISTS regulatory_document (
    document_id     SERIAL PRIMARY KEY,
    source_id       INT          REFERENCES source(source_id) ON DELETE SET NULL,
    title           VARCHAR(500),
    url             VARCHAR(500) NOT NULL UNIQUE,
    document_type   VARCHAR(20)  NOT NULL CHECK (document_type IN ('notification', 'circular', 'act', 'amendment', 'clarification', 'judgment', 'other')),
    published_date  DATE,
    raw_content     TEXT,                   -- HTML or extracted text
    file_path       VARCHAR(500),           -- local/S3 path for PDFs
    processing_status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'processed', 'failed', 'skipped')),
    created_at      TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_regdoc_source          ON regulatory_document(source_id);
CREATE INDEX IF NOT EXISTS idx_regdoc_processing      ON regulatory_document(processing_status);
CREATE INDEX IF NOT EXISTS idx_regdoc_published_date  ON regulatory_document(published_date);

COMMENT ON TABLE regulatory_document IS 'Raw documents ingested by the Monitoring Agent before AI extraction.';

-- =============================================================================
-- TABLE 8: document_regulation_link  (bridge: RegulatoryDocument <-> Regulation)
-- =============================================================================
CREATE TABLE IF NOT EXISTS document_regulation_link (
    document_id   INT NOT NULL REFERENCES regulatory_document(document_id) ON DELETE CASCADE,
    regulation_id INT NOT NULL REFERENCES regulation(regulation_id) ON DELETE CASCADE,
    version_id    INT REFERENCES regulation_version(version_id) ON DELETE SET NULL,
    PRIMARY KEY (document_id, regulation_id)
);

COMMENT ON TABLE document_regulation_link IS 'Links raw documents to the regulation versions they create or amend.';

-- =============================================================================
-- TABLE 9: users
-- System users across all roles and tenants.
-- =============================================================================
CREATE TABLE IF NOT EXISTS users (
    user_id         SERIAL PRIMARY KEY,
    email           VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    full_name       VARCHAR(200),
    role            VARCHAR(20)  NOT NULL DEFAULT 'viewer' CHECK (role IN ('admin', 'manager', 'viewer', 'consultant')),
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    is_verified     BOOLEAN      NOT NULL DEFAULT FALSE,
    last_login      TIMESTAMP,
    created_at      TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email  ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role   ON users(role);

COMMENT ON TABLE users IS 'All system users: founders, managers, employees, consultants, admins.';

-- =============================================================================
-- TABLE 10: company
-- SME tenant record.
-- =============================================================================
CREATE TABLE IF NOT EXISTS company (
    company_id              SERIAL PRIMARY KEY,
    name                    VARCHAR(200) NOT NULL,
    registration_number     VARCHAR(50)  UNIQUE,
    primary_jurisdiction_id INT          REFERENCES jurisdiction(jurisdiction_id) ON DELETE SET NULL,
    employee_count          INT          CHECK (employee_count >= 0),
    annual_turnover         DECIMAL(15,2) CHECK (annual_turnover >= 0),
    incorporation_date      DATE,
    is_active               BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at              TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMP    NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE company IS 'SME tenant. Employee count and turnover used for threshold-based applicability.';

-- =============================================================================
-- TABLE 11: company_sector  (bridge: Company <-> IndustrySector)
-- =============================================================================
CREATE TABLE IF NOT EXISTS company_sector (
    company_id INT NOT NULL REFERENCES company(company_id) ON DELETE CASCADE,
    sector_id  INT NOT NULL REFERENCES industry_sector(sector_id) ON DELETE CASCADE,
    PRIMARY KEY (company_id, sector_id)
);

COMMENT ON TABLE company_sector IS 'Sectors in which a company operates (many-to-many).';

-- =============================================================================
-- TABLE 12: company_location
-- Operating locations of an SME (determines which state laws apply).
-- =============================================================================
CREATE TABLE IF NOT EXISTS company_location (
    location_id     SERIAL PRIMARY KEY,
    company_id      INT          NOT NULL REFERENCES company(company_id) ON DELETE CASCADE,
    jurisdiction_id INT          NOT NULL REFERENCES jurisdiction(jurisdiction_id) ON DELETE RESTRICT,
    address         VARCHAR(300),
    is_headquarters BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_comploc_company ON company_location(company_id);

COMMENT ON TABLE company_location IS 'Locations where a company operates — determines applicable state laws.';

-- =============================================================================
-- TABLE 13: user_company_role
-- Multi-tenant: maps users to companies with per-company roles.
-- Allows consultants to manage multiple SME clients.
-- =============================================================================
CREATE TABLE IF NOT EXISTS user_company_role (
    user_id    INT         NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    company_id INT         NOT NULL REFERENCES company(company_id) ON DELETE CASCADE,
    role       VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'manager', 'viewer', 'consultant')),
    assigned_at TIMESTAMP  NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, company_id)
);

COMMENT ON TABLE user_company_role IS 'Multi-tenant mapping: one user can manage multiple SME companies with different roles.';

-- =============================================================================
-- TABLE 14: obligation
-- A specific compliance requirement derived from a regulation version.
-- e.g. "File annual return with MCA within 60 days of AGM"
-- =============================================================================
CREATE TABLE IF NOT EXISTS obligation (
    obligation_id               SERIAL PRIMARY KEY,
    regulation_version_id       INT         NOT NULL REFERENCES regulation_version(version_id) ON DELETE RESTRICT,
    description                 TEXT        NOT NULL,
    frequency                   VARCHAR(15) NOT NULL CHECK (frequency IN ('one_time', 'annual', 'quarterly', 'monthly', 'ad_hoc')),
    default_deadline_offset_days INT,       -- days from effective_from to first deadline
    responsible_role            VARCHAR(50),-- e.g. "CFO", "HR Manager", "Director"
    penalty_severity            VARCHAR(10) NOT NULL DEFAULT 'medium' CHECK (penalty_severity IN ('low', 'medium', 'high', 'critical')),
    created_at                  TIMESTAMP   NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_obligation_version ON obligation(regulation_version_id);

COMMENT ON TABLE obligation IS 'A specific compliance requirement derived from a regulation version.';

-- =============================================================================
-- TABLE 15: company_obligation
-- Central compliance register: applies an obligation to a specific company.
-- risk_score is auto-computed by a trigger.
-- =============================================================================
CREATE TABLE IF NOT EXISTS company_obligation (
    company_obligation_id SERIAL PRIMARY KEY,
    company_id            INT          NOT NULL REFERENCES company(company_id) ON DELETE CASCADE,
    obligation_id         INT          NOT NULL REFERENCES obligation(obligation_id) ON DELETE RESTRICT,
    status                VARCHAR(15)  NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'completed', 'waived', 'overdue')),
    next_due_date         DATE,
    last_completed_date   DATE,
    risk_score            DECIMAL(5,2) CHECK (risk_score BETWEEN 0 AND 100),
    assigned_to_user_id   INT          REFERENCES users(user_id) ON DELETE SET NULL,
    notes                 TEXT,
    created_at            TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMP    NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_company_obligation UNIQUE (company_id, obligation_id)
);

-- Dashboard and company-wide compliance register indexes
CREATE INDEX IF NOT EXISTS idx_compob_company         ON company_obligation(company_id, status);
CREATE INDEX IF NOT EXISTS idx_compob_obligation      ON company_obligation(obligation_id);
CREATE INDEX IF NOT EXISTS idx_compob_next_due        ON company_obligation(next_due_date);
CREATE INDEX IF NOT EXISTS idx_compob_risk            ON company_obligation(risk_score DESC);

COMMENT ON TABLE company_obligation IS 'Central compliance register. Each row is one obligation applied to one company.';

-- =============================================================================
-- TABLE 16: task
-- Actionable work item generated from a company obligation.
-- =============================================================================
CREATE TABLE IF NOT EXISTS task (
    task_id               SERIAL PRIMARY KEY,
    company_obligation_id INT          NOT NULL REFERENCES company_obligation(company_obligation_id) ON DELETE CASCADE,
    title                 VARCHAR(200) NOT NULL,
    description           TEXT,
    due_date              DATE,
    status                VARCHAR(20)  NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'cancelled', 'blocked')),
    priority              VARCHAR(10)  NOT NULL DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    assigned_to_user_id   INT          REFERENCES users(user_id) ON DELETE SET NULL,
    completed_at          TIMESTAMP,
    created_by_user_id    INT          REFERENCES users(user_id) ON DELETE SET NULL,
    created_at            TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- Composite index for dashboard task lists
CREATE INDEX IF NOT EXISTS idx_task_due_status    ON task(due_date, status);
CREATE INDEX IF NOT EXISTS idx_task_obligation    ON task(company_obligation_id, status);
CREATE INDEX IF NOT EXISTS idx_task_assignee      ON task(assigned_to_user_id, status);

COMMENT ON TABLE task IS 'Actionable work items auto-generated from company obligations with deadlines and priorities.';

-- =============================================================================
-- TABLE 17: audit_log
-- Immutable audit trail for all changes to critical tables.
-- PARTITIONED BY date range for scalability.
-- =============================================================================
CREATE TABLE IF NOT EXISTS audit_log (
    audit_id    BIGSERIAL,
    table_name  VARCHAR(100) NOT NULL,
    record_id   INT          NOT NULL,
    action      VARCHAR(10)  NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
    old_values  JSONB,
    new_values  JSONB,
    changed_by  INT          REFERENCES users(user_id) ON DELETE SET NULL,
    changed_at  TIMESTAMP    NOT NULL DEFAULT NOW(),
    ip_address  INET,
    PRIMARY KEY (audit_id, changed_at)
) PARTITION BY RANGE (changed_at);

-- Create yearly partitions (add more as needed)
CREATE TABLE IF NOT EXISTS audit_log_2026 PARTITION OF audit_log
    FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');

CREATE TABLE IF NOT EXISTS audit_log_2027 PARTITION OF audit_log
    FOR VALUES FROM ('2027-01-01') TO ('2028-01-01');

CREATE TABLE IF NOT EXISTS audit_log_2028 PARTITION OF audit_log
    FOR VALUES FROM ('2028-01-01') TO ('2029-01-01');

CREATE INDEX IF NOT EXISTS idx_audit_table_record  ON audit_log(table_name, record_id);
CREATE INDEX IF NOT EXISTS idx_audit_changed_by    ON audit_log(changed_by);
CREATE INDEX IF NOT EXISTS idx_audit_changed_at    ON audit_log(changed_at DESC);

COMMENT ON TABLE audit_log IS 'Partitioned immutable audit trail. Populated by triggers on critical tables.';
