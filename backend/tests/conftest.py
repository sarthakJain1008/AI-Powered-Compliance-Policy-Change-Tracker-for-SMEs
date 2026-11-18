import os, subprocess, sys
from pathlib import Path
import psycopg, pytest

HOSTPORT = os.environ.get("DB_HOSTPORT", "localhost:5434")
ADMIN = f"postgresql://postgres:postgres@{HOSTPORT}/postgres"
TEST_DB = "compliance_test"
BACKEND = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def dsn():
    with psycopg.connect(ADMIN, autocommit=True) as c:
        c.execute(f"DROP DATABASE IF EXISTS {TEST_DB} WITH (FORCE)")
        c.execute(f"CREATE DATABASE {TEST_DB}")
    url = f"postgresql+asyncpg://postgres:postgres@{HOSTPORT}/{TEST_DB}"
    env = {**os.environ, "DATABASE_URL": url}
    r = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=BACKEND, env=env,
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return ADMIN.rsplit("/", 1)[0] + f"/{TEST_DB}"


@pytest.fixture()
def db(dsn):
    """Superuser connection inside a transaction that is rolled back after each test."""
    with psycopg.connect(dsn) as conn:
        yield conn
        conn.rollback()


@pytest.fixture()
def world(db):
    """Minimal reference + tenant data."""
    q = lambda sql, *a: db.execute(sql, a).fetchone()[0]
    w = {}
    w["india"] = q("INSERT INTO jurisdiction(name,type) VALUES('India','country') RETURNING jurisdiction_id")
    w["ka"] = q("INSERT INTO jurisdiction(name,type,parent_jurisdiction_id) VALUES('Karnataka','state',%s) RETURNING jurisdiction_id", w["india"])
    w["mh"] = q("INSERT INTO jurisdiction(name,type,parent_jurisdiction_id) VALUES('Maharashtra','state',%s) RETURNING jurisdiction_id", w["india"])
    w["rbi"] = q("INSERT INTO jurisdiction(name,type,parent_jurisdiction_id) VALUES('RBI','regulator',%s) RETURNING jurisdiction_id", w["india"])
    w["it"] = q("INSERT INTO industry_sector(name) VALUES('IT Services') RETURNING sector_id")
    w["fin"] = q("INSERT INTO industry_sector(name) VALUES('Fintech') RETURNING sector_id")
    w["co_a"] = q("INSERT INTO company(name,primary_jurisdiction_id,employee_count,annual_turnover) VALUES('A Ltd',%s,50,1e7) RETURNING company_id", w["ka"])
    w["co_b"] = q("INSERT INTO company(name,primary_jurisdiction_id,employee_count,annual_turnover) VALUES('B Ltd',%s,5,1e6) RETURNING company_id", w["mh"])
    for c, s in ((w["co_a"], w["it"]), (w["co_b"], w["it"]), (w["co_b"], w["fin"])):
        db.execute("INSERT INTO company_sector VALUES (%s,%s)", (c, s))
    return w
