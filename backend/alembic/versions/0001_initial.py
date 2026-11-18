"""initial schema, logic, RLS (temporal compliance database)"""
from pathlib import Path
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

SQL = Path(__file__).resolve().parents[2] / "app" / "sql"


def _run_script(sql: str) -> None:
    conn = op.get_bind()
    raw = conn.connection.driver_connection
    if hasattr(raw, "execute") and conn.dialect.driver == "asyncpg":
        # asyncpg's Connection.execute runs a multi-statement script via the simple protocol
        from sqlalchemy.util import await_only
        await_only(raw.execute(sql))
    else:
        conn.exec_driver_sql(sql.replace("%", "%%"))


def upgrade():
    for name in ("001_schema.sql", "002_logic.sql"):
        _run_script((SQL / name).read_text())


def downgrade():
    op.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
