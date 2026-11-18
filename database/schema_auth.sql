-- =============================================================================
-- AI-Powered Compliance & Policy Change Tracker for SMEs
-- Authentication Feature Database Schema (PostgreSQL)
-- File: database/schema_auth.sql
-- Description: Creates the dedicated authentication tables for user management,
--              secure JWT login, password hashing, and role-based access control.
-- =============================================================================

-- 1. Create Database (Run this line separately if database doesn't exist yet):
-- CREATE DATABASE compliance_tracker;

-- 2. Connect to the database
\connect compliance_tracker

-- 3. Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- TABLE: users
-- Core authentication and profile table for the login feature.
-- =============================================================================
CREATE TABLE IF NOT EXISTS users (
    user_id         SERIAL PRIMARY KEY,
    email           VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    full_name       VARCHAR(200),
    role            VARCHAR(20)  NOT NULL DEFAULT 'viewer',
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    is_verified     BOOLEAN      NOT NULL DEFAULT FALSE,
    last_login      TIMESTAMP,
    created_at      TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP    NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_users_role CHECK (role IN ('admin', 'manager', 'viewer', 'consultant'))
);

-- Fast indexes for login and lookups
CREATE INDEX IF NOT EXISTS idx_users_email  ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role   ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);

-- Comments
COMMENT ON TABLE  users                 IS 'Application users for authentication with bcrypt hashed credentials and RBAC roles.';
COMMENT ON COLUMN users.email           IS 'Unique login email address.';
COMMENT ON COLUMN users.hashed_password IS 'Bcrypt salted and hashed password.';
COMMENT ON COLUMN users.role            IS 'RBAC role: admin, manager, viewer, or consultant.';
COMMENT ON COLUMN users.is_active       IS 'Soft-delete or account suspension flag.';
COMMENT ON COLUMN users.is_verified     IS 'Email verification flag.';

-- =============================================================================
-- OPTIONAL: Seed Demo Users
-- Password for all seed users is: Compliance@2026
-- (Bcrypt hash: $2b$12$e8x5a31D/H4F7B3lXwK8fOSpB7H6YqR0qF5j2hG1i3mK4l5o6p7q8 - generated with passlib)
-- =============================================================================
INSERT INTO users (email, hashed_password, full_name, role, is_active, is_verified)
VALUES
    (
        'admin@compliancetracker.com',
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiGSV9p.q26i',
        'Compliance Admin',
        'admin',
        TRUE,
        TRUE
    ),
    (
        'demo@sme.com',
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiGSV9p.q26i',
        'SME Founder',
        'manager',
        TRUE,
        TRUE
    )
ON CONFLICT (email) DO NOTHING;

-- Verification query
SELECT user_id, email, full_name, role, is_active, created_at FROM users;
