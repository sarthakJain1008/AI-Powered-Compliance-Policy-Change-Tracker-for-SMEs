# Database Setup Guide — ComplianceTracker

This directory contains the database setup scripts for the **ComplianceTracker** project.

---

## 🚀 Quick Setup (Automated)

Make sure local PostgreSQL is running, then simply execute:

```bash
chmod +x database/setup_postgres.sh
./database/setup_postgres.sh
```

This script will:
1. Verify `psql` is available in your PATH.
2. Check and automatically create the `compliance_tracker` database.
3. Apply `schema_auth.sql`.
4. Seed demo users for immediate testing.

---

## 🛠️ Manual Setup

If you prefer to run it manually using `psql`:

```bash
# 1. Create the database
createdb -U postgres compliance_tracker

# 2. Run the authentication feature schema
psql -U postgres -d compliance_tracker -f database/schema_auth.sql
```

---

## 📦 Tables in this Feature

### 1. `users` (`schema_auth.sql`)
* `user_id`: Primary Key (SERIAL)
* `email`: Unique login email (VARCHAR 255)
* `hashed_password`: Bcrypt salted and hashed password (VARCHAR 255)
* `full_name`: User display name (VARCHAR 200)
* `role`: RBAC role with DB-level `CHECK (role IN ('admin', 'manager', 'viewer', 'consultant'))`
* `is_active`: Account status flag (BOOLEAN)
* `is_verified`: Email verified flag (BOOLEAN)
* `is_onboarded`: Boolean flag (controls redirect to `/onboarding` vs `/dashboard`)
* `last_login`: Timestamp updated automatically upon successful login
* `created_at` & `updated_at`: Timestamps with database defaults

### 2. `company_profile` (`schema_onboarding.sql`)
* `id`: Primary Key (SERIAL)
* `user_id`: Foreign Key to `users.user_id` (UNIQUE, 1-to-1)
* **Step 1 Identity**: `company_name`, `entity_type`, `year_of_incorporation`, `cin_llpin`, `is_dpiit_startup`
* **Step 2 Category**: `primary_sector_id`, `primary_sector_name`, `business_sub_type`, `is_startup`, `startup_stage`
* **Step 3 Size**: `employee_range`, `turnover_range`, `funding_stage`
* **Step 4 Locations**: `primary_state`, `primary_jurisdiction_id`, `operating_states` (TEXT[]), `exports_business`, `export_markets` (TEXT[])
* **Timestamps**: `created_at`, `updated_at`

---

## 🔑 Demo Seed Accounts

After running the schema script, you can log in with:

| Email | Password | Role |
|---|---|---|
| `admin@compliancetracker.com` | `Compliance@2026` | `admin` |
| `demo@sme.com` | `Compliance@2026` | `manager` |
