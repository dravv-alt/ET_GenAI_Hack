"""
db/db.py
========
SQLite connection helper for the Opportunity Radar backend.

WHY SQLITE:
    Lightweight, zero-configuration, file-based. Perfect for hackathon demos.
    No server to start, no connection pooling, no migrations. Just a file.

DB FILE LOCATION:
    Stored at: db/radar.db  (relative to THIS file's directory)
    Auto-created on first run. Destroyed by deleting that file.

EXPORTS:
    get_conn()    → Returns a sqlite3.Connection with row_factory set.
                    Use for all reads and writes. Close after use or use
                    a 'with' context (for auto-commit/rollback on DML).

    init_schema() → Called ONCE on FastAPI startup (see main.py).
                    Reads schema.sql and executes all CREATE TABLE / CREATE INDEX
                    statements. Safe to call multiple times (uses IF NOT EXISTS).

USAGE PATTERN:
    from db.db import get_conn

    conn = get_conn()
    try:
        rows = conn.execute("SELECT * FROM alerts").fetchall()
        conn.commit()
    finally:
        conn.close()

    # Or for writes that might fail:
    with get_conn() as conn:
        conn.execute("INSERT INTO alerts VALUES (?, ?)", (id, ticker))
        # auto-commits on __exit__ if no exception, rolls back on exception
"""

import sqlite3
from pathlib import Path

# Resolve the path to radar.db relative to this file's directory.
# This means db/radar.db regardless of where uvicorn is launched from.
_DB_PATH = Path(__file__).parent / "radar.db"
_SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_conn() -> sqlite3.Connection:
    """
    Open and return a new SQLite connection to radar.db.

    Why row_factory = sqlite3.Row:
        Allows columns to be accessed by name, not just index.
        e.g.  row["ticker"]  instead of  row[0]
        Makes the code much more readable and less fragile.

    Why check_same_thread=False:
        FastAPI uses async workers that may call this from different threads.
        SQLite is safe here because we open/close connections per request
        rather than sharing a long-lived connection across threads.

    Returns:
        sqlite3.Connection ready to use.
    """
    conn = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_schema() -> None:
    """
    Initialize the database schema by executing schema.sql.

    Called ONCE from main.py on application startup via:
        @app.on_event("startup")
        def on_startup():
            init_schema()

    This function:
        1. Reads the SQL from db/schema.sql
        2. Executes all statements (CREATE TABLE IF NOT EXISTS, CREATE INDEX IF NOT EXISTS)
        3. Commits and closes the connection

    Safe to call multiple times — IF NOT EXISTS clauses prevent duplicate creation.
    """
    schema_sql = _SCHEMA_PATH.read_text(encoding="utf-8")

    conn = get_conn()
    try:
        # executescript handles multiple semicolon-separated statements at once
        conn.executescript(schema_sql)
        conn.commit()
        print(f"[db] Schema initialized. DB at: {_DB_PATH}")
    finally:
        conn.close()
