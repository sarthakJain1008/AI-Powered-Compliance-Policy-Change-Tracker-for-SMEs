import os
from alembic import context
from sqlalchemy import create_engine

url = os.environ.get("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5434/compliance")

def run_migrations_online():
    engine = create_engine(url)
    with engine.connect() as conn:
        context.configure(connection=conn, target_metadata=None)
        with context.begin_transaction():
            context.run_migrations()

run_migrations_online()
