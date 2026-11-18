"""review queue view + reject helper"""
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

SQL = """
CREATE VIEW v_review_queue AS
SELECT v.version_id, r.regulation_id, r.title AS regulation_title, v.version_number, v.change_type,
       v.effective_from, v.confidence_score, v.summary_text, v.recorded_at,
       d.document_id, d.url AS document_url, left(d.raw_text, 1500) AS source_excerpt,
       (SELECT count(*) FROM obligation o WHERE o.regulation_version_id = v.version_id) AS obligation_count
  FROM regulation_version v
  JOIN regulation r USING (regulation_id)
  LEFT JOIN regulatory_document d ON d.document_id = v.source_document_id
 WHERE v.review_status = 'needs_review'
 ORDER BY v.confidence_score NULLS FIRST, v.recorded_at;

CREATE FUNCTION reject_regulation_version(p_version INT, p_reviewer INT DEFAULT NULL) RETURNS VOID
LANGUAGE sql AS $$
    UPDATE regulation_version SET review_status = 'rejected', reviewed_by = p_reviewer, reviewed_at = now()
     WHERE version_id = p_version AND review_status = 'needs_review';
    UPDATE obligation SET review_status = 'rejected'
     WHERE regulation_version_id = p_version AND review_status = 'needs_review';
$$;
GRANT SELECT ON v_review_queue TO app_rw;
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
    _run("DROP FUNCTION IF EXISTS reject_regulation_version(INT, INT); DROP VIEW IF EXISTS v_review_queue;")
