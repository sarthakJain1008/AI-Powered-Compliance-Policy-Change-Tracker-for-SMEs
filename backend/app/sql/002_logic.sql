-- 002_logic.sql : functions, triggers, views, row level security, roles

-- ------------------------------------------------------------ helpers
CREATE OR REPLACE FUNCTION app_user_id() RETURNS INT LANGUAGE sql STABLE AS
$$ SELECT NULLIF(current_setting('app.user_id', true), '')::int $$;

CREATE OR REPLACE FUNCTION app_is_admin() RETURNS BOOLEAN LANGUAGE sql STABLE AS
$$ SELECT coalesce(current_setting('app.is_admin', true), '') = 'true' $$;

CREATE OR REPLACE FUNCTION app_company_ids() RETURNS INT[] LANGUAGE sql STABLE AS
$$ SELECT coalesce(string_to_array(NULLIF(current_setting('app.company_ids', true), ''), ',')::int[], '{}') $$;

-- ------------------------------------------------------------ risk score (single source of truth)
-- 0-100: penalty severity (40) + urgency (40) + frequency weight (20)
CREATE OR REPLACE FUNCTION compute_risk_score(
    p_severity SMALLINT, p_frequency TEXT, p_next_due DATE, p_status TEXT, p_today DATE DEFAULT current_date
) RETURNS NUMERIC LANGUAGE sql IMMUTABLE AS $$
    SELECT CASE
        WHEN p_status IN ('completed','waived') THEN 0
        ELSE round(
            (p_severity::numeric / 5) * 40
          + CASE
                WHEN p_next_due IS NULL THEN 10
                WHEN p_next_due < p_today THEN 40
                WHEN p_next_due <= p_today + 7  THEN 32
                WHEN p_next_due <= p_today + 30 THEN 20
                WHEN p_next_due <= p_today + 90 THEN 10
                ELSE 4 END
          + CASE p_frequency WHEN 'monthly' THEN 20 WHEN 'quarterly' THEN 16 WHEN 'annual' THEN 10
                             WHEN 'one-time' THEN 8 ELSE 5 END
        , 2)
    END
$$;

CREATE OR REPLACE FUNCTION next_period_due(p_frequency TEXT, p_from DATE) RETURNS DATE
LANGUAGE sql IMMUTABLE AS $$
    SELECT CASE p_frequency
        WHEN 'monthly'   THEN (p_from + interval '1 month')::date
        WHEN 'quarterly' THEN (p_from + interval '3 months')::date
        WHEN 'annual'    THEN (p_from + interval '1 year')::date
        ELSE NULL END
$$;

CREATE OR REPLACE FUNCTION trg_company_obligation_score() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE o RECORD;
BEGIN
    SELECT penalty_severity, frequency INTO o FROM obligation WHERE obligation_id = NEW.obligation_id;
    NEW.risk_score := compute_risk_score(o.penalty_severity, o.frequency, NEW.next_due_date, NEW.status);
    RETURN NEW;
END $$;
CREATE TRIGGER company_obligation_score
    BEFORE INSERT OR UPDATE ON company_obligation
    FOR EACH ROW EXECUTE FUNCTION trg_company_obligation_score();

-- completing a task rolls the obligation forward
CREATE OR REPLACE FUNCTION trg_task_completed_rollforward() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE freq TEXT; nxt DATE;
BEGIN
    IF NEW.status = 'completed' AND OLD.status <> 'completed' THEN
        SELECT o.frequency INTO freq
          FROM company_obligation co JOIN obligation o USING (obligation_id)
         WHERE co.company_obligation_id = NEW.company_obligation_id;
        nxt := next_period_due(freq, NEW.due_date);
        UPDATE company_obligation
           SET last_completed_date = current_date,
               next_due_date       = nxt,
               status              = CASE WHEN nxt IS NULL AND freq = 'one-time' THEN 'completed' ELSE status END
         WHERE company_obligation_id = NEW.company_obligation_id;
    END IF;
    RETURN NULL;
END $$;
CREATE TRIGGER task_completed_rollforward
    AFTER UPDATE OF status ON task
    FOR EACH ROW EXECUTE FUNCTION trg_task_completed_rollforward();

-- ------------------------------------------------------------ audit
-- trigger arg 0 = pk column name, arg 1 = column holding company id (or '')
CREATE OR REPLACE FUNCTION trg_audit() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    pk TEXT := TG_ARGV[0];
    cc TEXT := TG_ARGV[1];
    rec JSONB := to_jsonb(CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END);
BEGIN
    INSERT INTO audit_log(entity_type, entity_id, company_id, action, user_id, old_values, new_values)
    VALUES (TG_TABLE_NAME, (rec ->> pk)::int,
            CASE WHEN cc <> '' THEN (rec ->> cc)::int END,
            lower(CASE TG_OP WHEN 'INSERT' THEN 'create' WHEN 'UPDATE' THEN 'update' ELSE 'delete' END),
            app_user_id(),
            CASE WHEN TG_OP <> 'INSERT' THEN to_jsonb(OLD) END,
            CASE WHEN TG_OP <> 'DELETE' THEN to_jsonb(NEW) END);
    RETURN NULL;
END $$;

CREATE TRIGGER audit_task AFTER INSERT OR UPDATE OR DELETE ON task
    FOR EACH ROW EXECUTE FUNCTION trg_audit('task_id', 'company_id');
CREATE TRIGGER audit_company_obligation AFTER INSERT OR UPDATE OR DELETE ON company_obligation
    FOR EACH ROW EXECUTE FUNCTION trg_audit('company_obligation_id', 'company_id');
CREATE TRIGGER audit_company AFTER INSERT OR UPDATE OR DELETE ON company
    FOR EACH ROW EXECUTE FUNCTION trg_audit('company_id', 'company_id');
CREATE TRIGGER audit_regulation_version AFTER INSERT OR UPDATE OR DELETE ON regulation_version
    FOR EACH ROW EXECUTE FUNCTION trg_audit('version_id', '');
CREATE TRIGGER audit_obligation AFTER INSERT OR UPDATE OR DELETE ON obligation
    FOR EACH ROW EXECUTE FUNCTION trg_audit('obligation_id', '');

-- append-only: nobody may edit or delete audit rows
CREATE OR REPLACE FUNCTION trg_audit_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'audit_log is append-only'; END $$;
CREATE TRIGGER audit_log_immutable BEFORE UPDATE OR DELETE ON audit_log
    FOR EACH ROW EXECUTE FUNCTION trg_audit_immutable();

-- ------------------------------------------------------------ temporal publish helper
-- Atomically closes the live version and inserts the new one (used by the pipeline "version" stage).
CREATE OR REPLACE FUNCTION publish_regulation_version(
    p_regulation_id INT, p_version_number TEXT, p_effective_from DATE, p_change_type TEXT,
    p_summary TEXT DEFAULT NULL, p_full_text TEXT DEFAULT NULL, p_document_url TEXT DEFAULT NULL,
    p_source_document_id INT DEFAULT NULL, p_confidence NUMERIC DEFAULT NULL,
    p_review_status TEXT DEFAULT 'approved'
) RETURNS INT LANGUAGE plpgsql AS $$
DECLARE new_id INT;
BEGIN
    -- only an approved version closes the previous one
    IF p_review_status = 'approved' THEN
        UPDATE regulation_version
           SET effective_to = p_effective_from - 1
         WHERE regulation_id = p_regulation_id
           AND effective_to IS NULL AND superseded_at IS NULL AND review_status = 'approved'
           AND effective_from < p_effective_from;
    END IF;
    INSERT INTO regulation_version(regulation_id, version_number, effective_from, change_type, summary_text,
                                   full_text, document_url, source_document_id, confidence_score, review_status)
    VALUES (p_regulation_id, p_version_number, p_effective_from, p_change_type, p_summary,
            p_full_text, p_document_url, p_source_document_id, p_confidence, p_review_status)
    RETURNING version_id INTO new_id;
    IF p_change_type = 'repeal' AND p_review_status = 'approved' THEN
        UPDATE regulation SET status = 'repealed' WHERE regulation_id = p_regulation_id;
    END IF;
    RETURN new_id;
END $$;

-- Reviewer approves a pending version: closes the predecessor, then marks it approved.
CREATE OR REPLACE FUNCTION approve_regulation_version(p_version INT, p_reviewer INT DEFAULT NULL) RETURNS VOID
LANGUAGE plpgsql AS $$
DECLARE v RECORD;
BEGIN
    SELECT * INTO v FROM regulation_version WHERE version_id = p_version FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'version % not found', p_version; END IF;
    UPDATE regulation_version SET effective_to = v.effective_from - 1
     WHERE regulation_id = v.regulation_id AND version_id <> p_version
       AND review_status = 'approved' AND superseded_at IS NULL
       AND effective_to IS NULL AND effective_from < v.effective_from;
    UPDATE regulation_version SET review_status = 'approved', reviewed_by = p_reviewer, reviewed_at = now()
     WHERE version_id = p_version;
    IF v.change_type = 'repeal' THEN
        UPDATE regulation SET status = 'repealed' WHERE regulation_id = v.regulation_id;
    END IF;
END $$;

-- ------------------------------------------------------------ applicability ("as of" any date)
CREATE OR REPLACE FUNCTION company_jurisdiction_set(p_company INT) RETURNS TABLE(jurisdiction_id INT)
LANGUAGE sql STABLE AS $$
    WITH RECURSIVE seeds AS (
        SELECT primary_jurisdiction_id AS j FROM company WHERE company_id = p_company AND primary_jurisdiction_id IS NOT NULL
        UNION
        SELECT jurisdiction_id FROM company_location WHERE company_id = p_company
    ), anc AS (
        SELECT j.jurisdiction_id, j.parent_jurisdiction_id FROM jurisdiction j JOIN seeds s ON s.j = j.jurisdiction_id
        UNION
        SELECT p.jurisdiction_id, p.parent_jurisdiction_id FROM jurisdiction p JOIN anc a ON a.parent_jurisdiction_id = p.jurisdiction_id
    )
    SELECT DISTINCT anc.jurisdiction_id FROM anc
$$;

CREATE OR REPLACE FUNCTION applicable_versions_on(p_company INT, p_date DATE)
RETURNS TABLE(regulation_id INT, version_id INT, title VARCHAR, version_number VARCHAR,
              effective_from DATE, effective_to DATE, jurisdiction_id INT)
LANGUAGE sql STABLE AS $$
    SELECT r.regulation_id, v.version_id, r.title, v.version_number, v.effective_from, v.effective_to, r.jurisdiction_id
      FROM regulation r
      JOIN regulation_version v ON v.regulation_id = r.regulation_id
      JOIN jurisdiction rj ON rj.jurisdiction_id = r.jurisdiction_id
     WHERE v.review_status = 'approved' AND v.superseded_at IS NULL
       AND v.change_type <> 'repeal'
       AND p_date BETWEEN v.effective_from AND coalesce(v.effective_to, 'infinity'::date)
       AND EXISTS (SELECT 1 FROM company_sector cs JOIN regulation_sector rs ON rs.sector_id = cs.sector_id
                    WHERE cs.company_id = p_company AND rs.regulation_id = r.regulation_id)
       AND ( r.jurisdiction_id IN (SELECT jurisdiction_id FROM company_jurisdiction_set(p_company))
          OR (rj.type = 'regulator' AND rj.parent_jurisdiction_id IN (SELECT jurisdiction_id FROM company_jurisdiction_set(p_company))) )
$$;

-- obligations of a version that apply to a company given thresholds in obligation_applicability
CREATE OR REPLACE FUNCTION applicable_obligations(p_company INT, p_version INT)
RETURNS TABLE(obligation_id INT) LANGUAGE sql STABLE AS $$
    SELECT o.obligation_id
      FROM obligation o, company c
     WHERE o.regulation_version_id = p_version AND c.company_id = p_company AND o.review_status = 'approved'
       AND ( NOT EXISTS (SELECT 1 FROM obligation_applicability a WHERE a.obligation_id = o.obligation_id)
          OR EXISTS (SELECT 1 FROM obligation_applicability a
                      WHERE a.obligation_id = o.obligation_id
                        AND (a.min_employees IS NULL OR coalesce(c.employee_count,0) >= a.min_employees)
                        AND (a.max_employees IS NULL OR coalesce(c.employee_count,0) <= a.max_employees)
                        AND (a.min_turnover  IS NULL OR coalesce(c.annual_turnover,0) >= a.min_turnover)
                        AND (a.max_turnover  IS NULL OR coalesce(c.annual_turnover,0) <= a.max_turnover)
                        AND (a.sector_id IS NULL OR EXISTS (SELECT 1 FROM company_sector cs WHERE cs.company_id = c.company_id AND cs.sector_id = a.sector_id))
                        AND (a.condition_json IS NULL
                             OR NOT (a.condition_json ? 'handles_personal_data')
                             OR (a.condition_json ->> 'handles_personal_data')::boolean = c.handles_personal_data)) )
$$;

-- ------------------------------------------------------------ views
CREATE VIEW v_current_applicable_regulations AS
SELECT c.company_id, a.*
  FROM company c, LATERAL applicable_versions_on(c.company_id, current_date) a;

CREATE VIEW v_task_status AS
SELECT t.*,
       CASE WHEN t.status <> 'completed' AND t.due_date < current_date THEN 'overdue' ELSE t.status END AS effective_status
  FROM task t;

CREATE VIEW v_overdue_tasks AS
SELECT t.company_id, c.name AS company_name, count(*) AS overdue_count, min(t.due_date) AS oldest_due
  FROM task t JOIN company c USING (company_id)
 WHERE t.status <> 'completed' AND t.due_date < current_date
 GROUP BY t.company_id, c.name;

CREATE VIEW v_regulation_task_volume AS
SELECT r.regulation_id, r.title, date_trunc('quarter', t.created_at)::date AS quarter, count(*) AS tasks
  FROM task t
  JOIN company_obligation co ON co.company_obligation_id = t.company_obligation_id
  JOIN obligation o ON o.obligation_id = co.obligation_id
  JOIN regulation_version v ON v.version_id = o.regulation_version_id
  JOIN regulation r ON r.regulation_id = v.regulation_id
 GROUP BY r.regulation_id, r.title, date_trunc('quarter', t.created_at);

-- ------------------------------------------------------------ roles + row level security
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_rw') THEN
        CREATE ROLE app_rw NOLOGIN;
    END IF;
END $$;

GRANT USAGE ON SCHEMA public TO app_rw;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_rw;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_rw;
REVOKE UPDATE, DELETE, TRUNCATE ON audit_log FROM app_rw;

-- tenant tables: visible only to members of the company (or platform admin)
DO $$
DECLARE t TEXT;
BEGIN
    FOREACH t IN ARRAY ARRAY['company_sector','company_location','company_obligation','task',
                             'company_impact','notification','user_company_role','audit_log']
    LOOP
        EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', t);
        EXECUTE format('CREATE POLICY tenant_isolation ON %I USING (app_is_admin() OR company_id = ANY(app_company_ids()))', t);
    END LOOP;
END $$;
ALTER TABLE company ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON company USING (app_is_admin() OR company_id = ANY(app_company_ids()));
-- a new company must be insertable by any authenticated session
CREATE POLICY company_insert ON company FOR INSERT WITH CHECK (true);
-- audit rows may be written by triggers running as the invoking role
CREATE POLICY audit_insert ON audit_log FOR INSERT WITH CHECK (true);
