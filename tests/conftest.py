import os
import glob
from pathlib import Path

import mariadb
import pytest
from dotenv import load_dotenv

# Load .env from repo root (one level above /tests)
ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")  # ← підтягує змінні в os.environ

DB_NAME = os.getenv("TEST_DATABASE_NAME")
DB_HOST = os.getenv("TEST_DATABASE_HOST")
DB_PORT = int(os.getenv("TEST_DATABASE_PORT"))
DB_USER = os.getenv("TEST_DATABASE_USER")
DB_PASS = os.getenv("TEST_DATABASE_PASS")

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "db", "migrations")

def _connect(db: str | None = None):
    """Create a MariaDB connection to given database (or server-level if db=None)."""
    kwargs = dict(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
    )
    if db:
        kwargs["database"] = db

    conn = mariadb.connect(**kwargs)

    cur = conn.cursor()
    # Sets client, connection, results charsets; одразу з колацією:
    cur.execute("SET NAMES utf8mb4 COLLATE utf8mb4_general_ci")
    cur.close()

    return conn

def _apply_sql_file(cur, path: str):
    """Apply a .sql file by splitting on semicolons. Keep it simple."""
    with open(path, "r", encoding="utf-8") as f:
        sql = f.read()
    # naive split by ';' is ok for simple DDL without procedures
    for stmt in [s.strip() for s in sql.split(";") if s.strip()]:
        cur.execute(stmt)

def _apply_migrations(conn):
    """Run all migrations in lexical order."""
    cur = conn.cursor()
    #cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    #cur.execute(f"USE {DB_NAME}")
    for path in sorted(glob.glob(os.path.join(MIGRATIONS_DIR, "*.sql"))):
        _apply_sql_file(cur, path)
    conn.commit()
    cur.close()

def _drop_all_tables(conn):
    """Drop all tables in the test DB (disable FKs during deleting)."""
    cur = conn.cursor()
    cur.execute("SELECT TABLE_NAME FROM information_schema.tables WHERE table_schema=%s", (DB_NAME,))
    tables = [row[0] for row in cur.fetchall()]
    cur.execute("SET FOREIGN_KEY_CHECKS=0")
    for t in tables:
        cur.execute(f"DROP TABLE IF EXISTS `{t}`")
    cur.execute("SET FOREIGN_KEY_CHECKS=1")
    conn.commit()
    cur.close()

def _truncate_all_tables(conn):
    """Truncate all tables in the test DB (disable FKs during cleanup)."""
    cur = conn.cursor()
    cur.execute("SELECT TABLE_NAME FROM information_schema.tables WHERE table_schema=%s", (DB_NAME,))
    tables = [row[0] for row in cur.fetchall()]
    cur.execute("SET FOREIGN_KEY_CHECKS=0")
    for t in tables:
        cur.execute(f"TRUNCATE TABLE `{t}`")
    cur.execute("SET FOREIGN_KEY_CHECKS=1")
    conn.commit()
    cur.close()

@pytest.fixture(scope="session")
def db_session_conn():
    """Session-scoped DB connection; creates DB and applies migrations once."""
    # connect to server (no DB), create/use test DB, apply migrations
    server_conn = _connect(db=None)
    _drop_all_tables(server_conn)
    _apply_migrations(server_conn)
    server_conn.close()

    # now connect directly to test DB for the session
    conn = _connect(db=DB_NAME)
    yield conn
    conn.close()

@pytest.fixture(autouse=True)
def db_clean(db_session_conn):
    """Function-scoped cleanup: truncate all tables before each test."""
    _truncate_all_tables(db_session_conn)
    yield
