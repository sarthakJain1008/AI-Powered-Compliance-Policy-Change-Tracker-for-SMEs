"""pipeline stage tracking on regulatory_document"""
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

SQL = """
ALTER TABLE regulatory_document
    ADD COLUMN stage           VARCHAR(12) NOT NULL DEFAULT 'discovered'
        CHECK (stage IN ('discovered','fetched','parsed','extracted')),
    ADD COLUMN reference_no    VARCHAR(120),
    ADD COLUMN pdf_url         VARCHAR(500),
    ADD COLUMN http_status     INT,
    ADD COLUMN last_attempt_at TIMESTAMPTZ,
    ADD COLUMN duplicate_of    INT REFERENCES regulatory_document(document_id);
CREATE INDEX ix_doc_stage ON regulatory_document(stage, retry_count) WHERE processed_status <> 'processed';
UPDATE regulatory_document SET stage = 'parsed' WHERE raw_text IS NOT NULL AND length(raw_text) > 0;
"""


def _run(sql):
    conn = op.get_bind()
    if conn.dialect.driver == "asyncpg":
        from sqlalchemy.util import await_only
        await_only(conn.connection.driver_connection.execute(sql))
    else:
        conn.exec_driver_sql(sql.replace("%", "%%"))


def upgrade():
    _run(SQL)


def downgrade():
    _run("""DROP INDEX IF EXISTS ix_doc_stage;
            ALTER TABLE regulatory_document DROP COLUMN stage, DROP COLUMN reference_no, DROP COLUMN pdf_url,
              DROP COLUMN http_status, DROP COLUMN last_attempt_at, DROP COLUMN duplicate_of;""")
