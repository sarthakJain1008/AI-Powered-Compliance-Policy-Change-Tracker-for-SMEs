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

## 📦 Tables in this Feature (`schema_auth.sql`)

* **`users`**:
  * `user_id`: Primary Key (SERIAL)
  * `email`: Unique login email (VARCHAR 255)
  * `hashed_password`: Bcrypt salted and hashed password (VARCHAR 255)
  * `full_name`: User display name (VARCHAR 200)
  * `role`: RBAC role with DB-level `CHECK (role IN ('admin', 'manager', 'viewer', 'consultant'))`
  * `is_active`: Account status flag (BOOLEAN)
  * `is_verified`: Email verified flag (BOOLEAN)
  * `last_login`: Timestamp updated automatically upon successful login
  * `created_at` & `updated_at`: Timestamps with database defaults

---

## 🔑 Demo Seed Accounts

After running the schema script, you can log in with:

| Email | Password | Role |
|---|---|---|
| `admin@compliancetracker.com` | `Compliance@2026` | `admin` |
| `demo@sme.com` | `Compliance@2026` | `manager` |
