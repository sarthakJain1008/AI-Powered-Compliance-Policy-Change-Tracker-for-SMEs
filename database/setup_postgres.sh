#!/usr/bin/env bash
# ==============================================================================
# Script: database/setup_postgres.sh
# Description: Automates local PostgreSQL database creation and schema setup
#              for the ComplianceTracker Authentication system.
# Usage: ./database/setup_postgres.sh
# ==============================================================================

set -euo pipefail

DB_NAME="compliance_tracker"
DB_USER="${POSTGRES_USER:-postgres}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_HOST="${POSTGRES_HOST:-localhost}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCHEMA_FILE="${SCRIPT_DIR}/schema_auth.sql"

echo "=========================================================="
echo "🛡️  ComplianceTracker - Auth Database Setup"
echo "=========================================================="
echo "Host:     ${DB_HOST}:${DB_PORT}"
echo "User:     ${DB_USER}"
echo "Database: ${DB_NAME}"
echo "Schema:   ${SCHEMA_FILE}"
echo "----------------------------------------------------------"

# Check if psql is available
if ! command -v psql &> /dev/null; then
    echo "❌ Error: 'psql' is not installed or not in PATH."
    echo "Please ensure PostgreSQL is installed and psql is in your PATH."
    exit 1
fi

# Create database if it does not exist
echo "Checking if database '${DB_NAME}' exists..."
if psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -lqt | cut -d \| -f 1 | grep -qw "${DB_NAME}"; then
    echo "✅ Database '${DB_NAME}' already exists."
else
    echo "Creating database '${DB_NAME}'..."
    createdb -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" "${DB_NAME}" || true
    echo "✅ Database '${DB_NAME}' created."
fi

# Run the authentication schema script
echo "Running authentication schema..."
psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -f "${SCHEMA_FILE}"

echo "----------------------------------------------------------"
echo "🎉 Authentication Database Setup Complete!"
echo "Seed accounts created:"
echo " - admin@compliancetracker.com (Role: admin)"
echo " - demo@sme.com (Role: manager)"
echo " Password for demo accounts: Compliance@2026"
echo "=========================================================="
