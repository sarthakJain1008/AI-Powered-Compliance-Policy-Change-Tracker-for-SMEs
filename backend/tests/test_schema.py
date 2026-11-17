import datetime as dt
import psycopg
import pytest

D = dt.date


def new_reg(db, w, title="Test Act", jur=None, sectors=("it",)):
    rid = db.execute("INSERT INTO regulation(title,jurisdiction_id,status) VALUES(%s,%s,'active') RETURNING regulation_id",
                     (title, jur or w["india"])).fetchone()[0]
    for s in sectors:
        db.execute("INSERT INTO regulation_sector VALUES(%s,%s)", (rid, w[s]))
    return rid


def publish(db, rid, num, frm, ctype="new"):
    return db.execute("SELECT publish_regulation_version(%s,%s,%s,%s)", (rid, num, frm, ctype)).fetchone()[0]


def applicable(db, company, on):
    return {r[0] for r in db.execute("SELECT version_id FROM applicable_versions_on(%s,%s)", (company, on))}


def test_temporal_as_of_query(db, world):
    rid = new_reg(db, world)
    v1 = publish(db, rid, "1.0", D(2020, 1, 1))
    v2 = publish(db, rid, "Amendment 2025", D(2025, 6, 1), "amendment")
    a = world["co_a"]
    assert applicable(db, a, D(2019, 12, 31)) == set()
    assert applicable(db, a, D(2025, 1, 1)) == {v1}
    assert applicable(db, a, D(2025, 6, 1)) == {v2}
    assert applicable(db, a, D(2030, 1, 1)) == {v2}
    # previous version was closed the day before
    assert db.execute("SELECT effective_to FROM regulation_version WHERE version_id=%s", (v1,)).fetchone()[0] == D(2025, 5, 31)


def test_overlapping_versions_rejected(db, world):
    rid = new_reg(db, world)
    db.execute("INSERT INTO regulation_version(regulation_id,version_number,effective_from,effective_to,change_type) "
               "VALUES(%s,'1',%s,%s,'new')", (rid, D(2020, 1, 1), D(2021, 12, 31)))
    with pytest.raises(psycopg.errors.ExclusionViolation):
        db.execute("INSERT INTO regulation_version(regulation_id,version_number,effective_from,effective_to,change_type) "
                   "VALUES(%s,'2',%s,NULL,'amendment')", (rid, D(2021, 6, 1)))


def test_sector_and_jurisdiction_filtering(db, world):
    fin_only = new_reg(db, world, "Fintech Act", sectors=("fin",))
    state_ka = new_reg(db, world, "Karnataka Act", jur=world["ka"])
    rbi_c = new_reg(db, world, "RBI Direction", jur=world["rbi"], sectors=("fin",))
    vf, vk, vr = (publish(db, r, "1", D(2020, 1, 1)) for r in (fin_only, state_ka, rbi_c))
    on = D(2026, 1, 1)
    assert applicable(db, world["co_a"], on) == {vk}            # IT in Karnataka
    assert applicable(db, world["co_b"], on) == {vf, vr}        # fintech in Maharashtra: no Karnataka law
    

def test_repeal_removes_applicability(db, world):
    rid = new_reg(db, world)
    publish(db, rid, "1", D(2020, 1, 1))
    publish(db, rid, "repeal", D(2024, 1, 1), "repeal")
    assert applicable(db, world["co_a"], D(2023, 1, 1))
    assert not applicable(db, world["co_a"], D(2024, 6, 1))
    assert db.execute("SELECT status FROM regulation WHERE regulation_id=%s", (rid,)).fetchone()[0] == "repealed"


def test_unreviewed_version_does_not_apply_or_close_previous(db, world):
    rid = new_reg(db, world)
    v1 = publish(db, rid, "1", D(2020, 1, 1))
    db.execute("SELECT publish_regulation_version(%s,'2',%s,'amendment',NULL,NULL,NULL,NULL,0.4,'needs_review')", (rid, D(2025, 1, 1)))
    assert applicable(db, world["co_a"], D(2026, 1, 1)) == {v1}
    # approval closes the predecessor and makes the new version live
    v2 = db.execute("SELECT version_id FROM regulation_version WHERE review_status='needs_review' AND regulation_id=%s", (rid,)).fetchone()[0]
    db.execute("SELECT approve_regulation_version(%s)", (v2,))
    assert applicable(db, world["co_a"], D(2024, 12, 31)) == {v1}
    assert applicable(db, world["co_a"], D(2026, 1, 1)) == {v2}


def make_obligation(db, rid, freq="monthly", sev=3):
    v = publish(db, rid, "1", D(2020, 1, 1))
    return v, db.execute("INSERT INTO obligation(regulation_version_id,description,frequency,penalty_severity) "
                         "VALUES(%s,'File return',%s,%s) RETURNING obligation_id, obligation_key", (v, freq, sev)).fetchone()


def test_obligation_thresholds(db, world):
    rid = new_reg(db, world)
    v, (oid, _) = make_obligation(db, rid)
    db.execute("INSERT INTO obligation_applicability(obligation_id,min_employees) VALUES(%s,20)", (oid,))
    assert [r[0] for r in db.execute("SELECT * FROM applicable_obligations(%s,%s)", (world["co_a"], v))] == [oid]  # 50 employees
    assert [r[0] for r in db.execute("SELECT * FROM applicable_obligations(%s,%s)", (world["co_b"], v))] == []      # 5 employees


def seed_task(db, w, freq="monthly"):
    rid = new_reg(db, w)
    v, (oid, key) = make_obligation(db, rid, freq)
    co = db.execute("INSERT INTO company_obligation(company_id,obligation_key,obligation_id,next_due_date) "
                    "VALUES(%s,%s,%s,%s) RETURNING company_obligation_id", (w["co_a"], key, oid, D(2026, 1, 15))).fetchone()[0]
    t = db.execute("INSERT INTO task(company_obligation_id,company_id,title,period_start,due_date) "
                   "VALUES(%s,%s,'GSTR-3B',%s,%s) RETURNING task_id", (co, w["co_a"], D(2026, 1, 1), D(2026, 1, 15))).fetchone()[0]
    return co, t


def test_risk_score_set_by_trigger(db, world):
    co, _ = seed_task(db, world)
    score = db.execute("SELECT risk_score FROM company_obligation WHERE company_obligation_id=%s", (co,)).fetchone()[0]
    assert score is not None and 0 < score <= 100
    # past due scores higher than far future
    db.execute("UPDATE company_obligation SET next_due_date=current_date - 5 WHERE company_obligation_id=%s", (co,))
    late = db.execute("SELECT risk_score FROM company_obligation WHERE company_obligation_id=%s", (co,)).fetchone()[0]
    db.execute("UPDATE company_obligation SET next_due_date=current_date + 200 WHERE company_obligation_id=%s", (co,))
    far = db.execute("SELECT risk_score FROM company_obligation WHERE company_obligation_id=%s", (co,)).fetchone()[0]
    assert late > far


def test_completing_task_rolls_obligation_forward(db, world):
    co, t = seed_task(db, world, "monthly")
    db.execute("UPDATE task SET status='completed', completed_at=now() WHERE task_id=%s", (t,))
    nd, lc = db.execute("SELECT next_due_date,last_completed_date FROM company_obligation WHERE company_obligation_id=%s", (co,)).fetchone()
    assert nd == D(2026, 2, 15) and lc == dt.date.today()


def test_one_time_obligation_completes(db, world):
    co, t = seed_task(db, world, "one-time")
    db.execute("UPDATE task SET status='completed', completed_at=now() WHERE task_id=%s", (t,))
    assert db.execute("SELECT status FROM company_obligation WHERE company_obligation_id=%s", (co,)).fetchone()[0] == "completed"


def test_period_uniqueness(db, world):
    co, _ = seed_task(db, world)
    with pytest.raises(psycopg.errors.UniqueViolation):
        db.execute("INSERT INTO task(company_obligation_id,company_id,title,period_start,due_date) VALUES(%s,%s,'dup',%s,%s)",
                   (co, world["co_a"], D(2026, 1, 1), D(2026, 1, 20)))


def test_overdue_is_derived_not_stored(db, world):
    _, t = seed_task(db, world)
    db.execute("UPDATE task SET due_date=current_date-3 WHERE task_id=%s", (t,))
    assert db.execute("SELECT effective_status FROM v_task_status WHERE task_id=%s", (t,)).fetchone()[0] == "overdue"
    with pytest.raises(psycopg.errors.CheckViolation):
        db.execute("UPDATE task SET status='overdue' WHERE task_id=%s", (t,))


def test_audit_trail_with_user_and_immutability(db, world):
    uid = db.execute("INSERT INTO app_user(name,email,password_hash) VALUES('U','u@x.in','h') RETURNING user_id").fetchone()[0]
    db.execute("SELECT set_config('app.user_id', %s, true)", (str(uid),))
    _, t = seed_task(db, world)
    db.execute("UPDATE task SET status='in_progress' WHERE task_id=%s", (t,))
    rows = db.execute("SELECT action,user_id,old_values->>'status',new_values->>'status' FROM audit_log "
                      "WHERE entity_type='task' AND entity_id=%s ORDER BY log_id", (t,)).fetchall()
    assert [r[0] for r in rows] == ["create", "update"]
    assert rows[1][1:] == (uid, "pending", "in_progress")
    with pytest.raises(psycopg.errors.RaiseException):
        db.execute("UPDATE audit_log SET action='delete'")


def test_row_level_security_isolates_tenants(db, world):
    seed_task(db, world)   # belongs to company A
    db.execute("SET LOCAL ROLE app_rw")
    db.execute("SELECT set_config('app.company_ids', %s, true)", (str(world["co_b"]),))
    assert db.execute("SELECT count(*) FROM task").fetchone()[0] == 0
    assert [r[0] for r in db.execute("SELECT company_id FROM company")] == [world["co_b"]]
    db.execute("SELECT set_config('app.company_ids', %s, true)", (f"{world['co_a']},{world['co_b']}",))
    assert db.execute("SELECT count(*) FROM task").fetchone()[0] == 1
    db.execute("SELECT set_config('app.company_ids', '', true)")
    assert db.execute("SELECT count(*) FROM task").fetchone()[0] == 0
    db.execute("SELECT set_config('app.is_admin', 'true', true)")
    assert db.execute("SELECT count(*) FROM task").fetchone()[0] == 1


def test_app_role_cannot_tamper_audit(db, world):
    seed_task(db, world)
    db.execute("SET LOCAL ROLE app_rw")
    db.execute("SELECT set_config('app.is_admin','true',true)")
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        db.execute("DELETE FROM audit_log")


def test_document_dedupe_by_url(db, world):
    sid = db.execute("INSERT INTO source(name,url) VALUES('RBI','http://rbi') RETURNING source_id").fetchone()[0]
    db.execute("INSERT INTO regulatory_document(source_id,title,url) VALUES(%s,'a','http://x/1')", (sid,))
    with pytest.raises(psycopg.errors.UniqueViolation):
        db.execute("INSERT INTO regulatory_document(source_id,title,url) VALUES(%s,'b','http://x/1')", (sid,))
