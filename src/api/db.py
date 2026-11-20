"""Database setup for the API: engine, sessions, and the append-only triggers.

SQLite is the only store (no external services). The path comes from the
LABELLENS_DB_URL environment variable. Tests use an in-memory database.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

DEFAULT_DB_URL = "sqlite:///data/api/labellens.db"


class Base(DeclarativeBase):
    """Base class of every table."""


def utcnow() -> str:
    """Return the current UTC time as an ISO 8601 string ending in Z (the API timestamp format)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def make_engine(url: str | None = None) -> Engine:
    """Create an engine. `None` reads LABELLENS_DB_URL, then falls back to a file under data/api/.

    `sqlite://` (no path) is an in-memory database shared by all connections of this engine.
    """
    url = url or os.environ.get("LABELLENS_DB_URL", DEFAULT_DB_URL)
    kwargs: dict = {}
    if url in ("sqlite://", "sqlite:///:memory:"):
        kwargs = {"connect_args": {"check_same_thread": False}, "poolclass": StaticPool}
    elif url.startswith("sqlite:///") and not url.startswith("sqlite:////:"):
        path = url.removeprefix("sqlite:///")
        folder = os.path.dirname(path)
        if folder:
            os.makedirs(folder, exist_ok=True)
    engine = create_engine(url, **kwargs)

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _record) -> None:  # noqa: ANN001
        # SQLite ignores foreign keys unless asked, per connection.
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    return engine


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Return a session factory bound to `engine`."""
    return sessionmaker(engine, expire_on_commit=False)


def init_db(engine: Engine) -> None:
    """Create all tables and install the append-only triggers (safe to call twice)."""
    from src.api import models  # noqa: F401  (importing registers the tables on Base)

    Base.metadata.create_all(engine)
    _add_missing_columns(engine)
    with engine.begin() as conn:
        for table in models.IMMUTABLE_TABLES:
            for action in ("UPDATE", "DELETE"):
                conn.exec_driver_sql(
                    f"CREATE TRIGGER IF NOT EXISTS {table}_no_{action.lower()} "
                    f"BEFORE {action} ON {table} "
                    f"BEGIN SELECT RAISE(ABORT, 'append-only table {table}: {action} is not allowed'); END;"
                )


# Columns added after Step 20 to tables that may already exist in a developer's database file.
ADDED_COLUMNS: dict[str, dict[str, str]] = {
    "check_results": {"needs_human_count": "INTEGER", "coverage": "JSON", "retrieval_config": "JSON"},
    "reviews": {"assessment_id": "VARCHAR"},
    "extractions": {"scan_id": "VARCHAR"},
}


def _add_missing_columns(engine: Engine) -> None:
    """ALTER TABLE ADD COLUMN for ADDED_COLUMNS that an older database file lacks (create_all never alters)."""
    with engine.begin() as conn:
        for table, columns in ADDED_COLUMNS.items():
            existing = {row[1] for row in conn.exec_driver_sql(f"PRAGMA table_info({table})")}
            if not existing:  # the table does not exist yet (create_all makes it with every column)
                continue
            for name, sql_type in columns.items():
                if name not in existing:
                    conn.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN {name} {sql_type}")
