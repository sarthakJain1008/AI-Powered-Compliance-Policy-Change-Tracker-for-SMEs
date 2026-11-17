"""initial schema, logic, RLS"""
from pathlib import Path
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

SQL = Path(__file__).resolve().parents[2] / "app" / "sql"

def upgrade():
    for name in ("001_schema.sql", "002_logic.sql"):
        op.get_bind().exec_driver_sql((SQL / name).read_text().replace("%", "%%"))

def downgrade():
    op.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
