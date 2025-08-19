import os
import glob
from pathlib import Path
from typing import Any
import matplotlib.pyplot as plt

import mariadb
import pytest
from binance import Client
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
from peewee import MySQLDatabase

from cryptobot.components import TelegramComponent, ServiceComponent, BinanceClientAdapter, BinanceApiAdapter, \
    BinanceGateway
from cryptobot.components.settings import SettingsComponent
from cryptobot.components.telegram_http_transport import TelegramHttpTransportComponent
from cryptobot.helpers import get_project_root, init_settings_component
from cryptobot.ports.binance_api_adapter import BinanceApiAdapterPort
from cryptobot.ports.binance_client_adapter import BinanceClientAdapterPort
from cryptobot.ports.binance_gateway import BinanceGatewayPort
from cryptobot.views import view_helper
from cryptobot.views.view import View
from tests.components.telegram_http_transport_mock import TelegramHttpTransportMockComponent
from tests.config import get_config
from cryptobot.models import database_proxy

# Load .env from repo root (one level above /tests)
ROOT = Path(__file__).resolve().parents[1]
SEEDS_DIR = Path(__file__).parent / "db" / "seeds"
load_dotenv(ROOT / ".env")

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

def _apply_migrations(conn):
    """Run all migrations in lexical order."""
    cur = conn.cursor()
    #cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    #cur.execute(f"USE {DB_NAME}")
    for path in sorted(glob.glob(os.path.join(MIGRATIONS_DIR, "*.sql"))):
        _apply_sql_file(cur, Path(path))
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

def _apply_sql_file(cur, path: Path):
    sql = path.read_text(encoding="utf-8")
    for stmt in [s.strip() for s in sql.split(";") if s.strip()]:
        cur.execute(stmt)

@pytest.fixture
def apply_seed_fixture(db_session_conn):
    def run(seed_name: str, files: list[str] | None = None):
        apply_seed(db_session_conn, seed_name, files)
    #return run
    yield run
    _truncate_all_tables(db_session_conn)

def apply_seed(conn, seed_name: str|None, files: str | list[str] | None = None):
    cur = conn.cursor()
    cur.execute("SET FOREIGN_KEY_CHECKS=0")
    seed_path = SEEDS_DIR / seed_name if seed_name else SEEDS_DIR
    #seed_path = SEEDS_DIR / seed_name
    files = [files] if type(files) is str else files
    paths = [seed_path / f for f in files] if files else sorted(seed_path.glob("*.sql"))
    for p in paths:
        _apply_sql_file(cur, Path(p))
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

@pytest.fixture
def make_config() -> dict[str, Any]:
    return get_config()

@pytest.fixture
def make_di(make_config) -> dict[str, Any]:

    config = make_config

    environment = Environment(
        loader = FileSystemLoader(
            get_project_root() + os.sep + config["view"]["views_folder"]
        )
    )

    environment.globals.update(view_helper.get_globals())

    default_vars = {}

    db = MySQLDatabase(
        config["db"]["name"], # database name
        user = config["db"]["user"], # database username
        password = config["db"]["pass"], # database password
        host = config["db"]["host"],  # database host
        port = config["db"]["port"]  # database port
    )
    database_proxy.initialize(db)
    if not db.connect():
        print(f'ERROR: Cannot connect to database {config["db"]["host"]}')

    view = View(environment, default_vars)

    settings_component = SettingsComponent.create(db)

    telegram_component = TelegramComponent.create(config["telegram"], TelegramHttpTransportMockComponent())
    #telegram_component = TelegramComponent.create(config["telegram"], TelegramHttpTransportComponent())

    binance_client: Client = Client(config['binance']['api']['key'], config['binance']['api']['secret'])
    binance_client_adapter: BinanceClientAdapterPort = BinanceClientAdapter.create(binance_client=binance_client)

    binance_api_adapter: BinanceApiAdapterPort = BinanceApiAdapter.create(
        base_url=config['binance']['api']['base_url'],
        binance_api_key=config['binance']['api']['key'],
        binance_api_secret=config['binance']['api']['secret'],
    )

    binance_gateway: BinanceGatewayPort = BinanceGateway.create(
        binance_client_adapter=binance_client_adapter,
        binance_api_adapter=binance_api_adapter,
    )

    di = { # fuck that Python...
        'config': config,
        'view': view,
        'plt': plt,
        'db': db,
        'service_component': ServiceComponent.create(
            db=db,
            view=view,
            telegram_component=telegram_component,
            binance_gateway=binance_gateway,
        ),
        'settings_component': settings_component,
    }

    init_settings_component(di['settings_component'])

    return di