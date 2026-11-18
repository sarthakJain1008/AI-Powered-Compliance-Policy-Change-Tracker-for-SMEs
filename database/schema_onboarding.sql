-- =============================================================================
-- ComplianceTracker — Onboarding Schema
-- File: database/schema_onboarding.sql
-- Run AFTER schema_auth.sql:
--   psql -U postgres -d compliance_tracker -f database/schema_onboarding.sql
-- =============================================================================

\connect compliance_tracker

-- ─── Extend users: track onboarding completion ───────────────────────────────
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_onboarded BOOLEAN NOT NULL DEFAULT FALSE;

COMMENT ON COLUMN users.is_onboarded IS
  'TRUE once the user completes the 5-step onboarding wizard. '
  'Controls the post-login redirect: FALSE → /onboarding, TRUE → /dashboard.';

-- =============================================================================
-- TABLE: company_profile
-- One row per user. Created at the end of Step 5 (Review & Confirm).
-- =============================================================================
CREATE TABLE IF NOT EXISTS company_profile (
    id                      SERIAL PRIMARY KEY,

    -- Owner
    user_id                 INT          NOT NULL UNIQUE
                                         REFERENCES users(user_id) ON DELETE CASCADE,

    -- Step 1 — Business Identity
    company_name            VARCHAR(200) NOT NULL,
    entity_type             VARCHAR(50)  NOT NULL
                                CHECK (entity_type IN (
                                    'private_limited', 'llp', 'one_person_company',
                                    'sole_proprietorship', 'partnership', 'public_limited'
                                )),
    year_of_incorporation   SMALLINT     CHECK (year_of_incorporation BETWEEN 1900 AND 2030),
    cin_llpin               VARCHAR(30),          -- optional, Ministry of Corporate Affairs ID
    is_dpiit_startup        BOOLEAN      NOT NULL DEFAULT FALSE,

    -- Step 2 — Business Category
    primary_sector_id       SMALLINT     NOT NULL
                                CHECK (primary_sector_id BETWEEN 1 AND 15),
    -- Sector names stored for quick read without join
    primary_sector_name     VARCHAR(100) NOT NULL,
    business_sub_type       VARCHAR(100),         -- conditional on sector
    is_startup              BOOLEAN      NOT NULL DEFAULT FALSE,
    startup_stage           VARCHAR(30)
                                CHECK (startup_stage IN (
                                    'idea', 'pre_revenue', 'early_revenue',
                                    'series_a_plus', 'profitable'
                                ) OR startup_stage IS NULL),

    -- Step 3 — Size & Revenue
    employee_range          VARCHAR(20)  NOT NULL
                                CHECK (employee_range IN (
                                    '1_9', '10_19', '20_49',
                                    '50_99', '100_499', '500_plus'
                                )),
    turnover_range          VARCHAR(30)  NOT NULL
                                CHECK (turnover_range IN (
                                    'below_40l', '40l_1cr', '1cr_10cr',
                                    '10cr_100cr', 'above_100cr'
                                )),
    funding_stage           VARCHAR(30)
                                CHECK (funding_stage IN (
                                    'bootstrapped', 'pre_seed', 'seed',
                                    'series_a', 'series_b_plus', 'pe_backed'
                                ) OR funding_stage IS NULL),

    -- Step 4 — Locations
    primary_state           VARCHAR(100) NOT NULL,
    primary_jurisdiction_id SMALLINT,             -- FK-style ref to jurisdiction seed
    operating_states        TEXT[]       NOT NULL DEFAULT '{}',
    exports_business        BOOLEAN      NOT NULL DEFAULT FALSE,
    export_markets          TEXT[]       NOT NULL DEFAULT '{}',

    -- Timestamps
    created_at              TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cp_user        ON company_profile(user_id);
CREATE INDEX IF NOT EXISTS idx_cp_sector      ON company_profile(primary_sector_id);
CREATE INDEX IF NOT EXISTS idx_cp_entity      ON company_profile(entity_type);
CREATE INDEX IF NOT EXISTS idx_cp_state       ON company_profile(primary_state);
CREATE INDEX IF NOT EXISTS idx_cp_employees   ON company_profile(employee_range);

COMMENT ON TABLE  company_profile IS
  'Company profile collected during the 5-step onboarding wizard. '
  'Used by the AI pipeline to personalise compliance obligations.';

-- Verification
SELECT 'schema_onboarding.sql applied successfully' AS status;
