"""
services/alert_store.py
=======================
SQLite-backed persistence layer for Alert objects.

PURPOSE:
    Acts as a cache between scan runs. When POST /scan completes, alerts are
    saved here. When GET /alerts is called, alerts are read from here.
    This means the UI loads instantly (no re-scan on every page refresh).

DATA FORMAT:
    Alerts are stored with most fields as TEXT columns.
    `raw_data` is stored as a JSON string (serialized dict).
    `created_at` is stored as ISO 8601 string ("2026-03-29T10:30:00.123456").

FUNCTIONS:
    save_alerts(alerts)                     → upsert all alerts, clear stale ones
    get_cached_alerts(signal_filter, limit) → read sorted alerts from SQLite
    clear_alerts()                          → wipe all cached alerts

ORDERING LOGIC:
    Alerts are returned ordered by:
        1. signal_strength priority: high=1, medium=2, low=3  (HIGH first)
        2. created_at DESC (newer alerts first within same strength)

    This is achieved using a CASE WHEN expression in the ORDER BY clause.

STALENESS:
    Alerts older than 24 hours are deleted on each save_alerts() call.
    This keeps the cache fresh and prevents old data from surfacing.

UPSERT:
    Uses INSERT OR REPLACE INTO so re-running a scan updates existing alerts
    rather than creating duplicates (same alert ID → same row replacement).
"""

import json
from datetime import datetime, timedelta

from db.db import get_conn
from models.alert import Alert, AlertType, SignalStrength


def save_alerts(alerts: list[Alert]) -> None:
    """
    Persist a list of Alert objects to the SQLite alerts table.

    Steps:
        1. Delete alerts older than 24 hours (stale data removal).
        2. Upsert each alert using INSERT OR REPLACE (idempotent on re-scan).

    Args:
        alerts: List of Alert objects from the orchestrator/ranker.

    NOTE:
        We do NOT clear all alerts before inserting — we upsert by ID.
        This preserves alerts from previous scans that are still fresh.
    """
    if not alerts:
        return

    conn = get_conn()
    try:
        # Step 1: Remove alerts older than 24 hours
        cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
        conn.execute("DELETE FROM alerts WHERE created_at < ?", (cutoff,))

        # Step 2: Upsert each alert
        # INSERT OR REPLACE replaces the row if the primary key (id) already exists.
        insert_sql = """
        INSERT OR REPLACE INTO alerts
            (id, ticker, alert_type, signal_strength, title, why_it_matters,
             action_hint, source_url, source_label, raw_data, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        for alert in alerts:
            conn.execute(insert_sql, (
                alert.id,
                alert.ticker,
                str(alert.alert_type.value) if hasattr(alert.alert_type, 'value') else str(alert.alert_type),
                str(alert.signal_strength.value) if hasattr(alert.signal_strength, 'value') else str(alert.signal_strength),
                alert.title,
                alert.why_it_matters,
                alert.action_hint,
                alert.source_url,
                alert.source_label,
                json.dumps(alert.raw_data),              # dict → JSON string
                alert.created_at.isoformat(),           # datetime → ISO string
            ))

        conn.commit()
        print(f"[alert_store] Saved {len(alerts)} alerts to SQLite.")

    finally:
        conn.close()


def get_cached_alerts(
    signal_filter: str = None,
    ticker_filter: str = None,
    limit: int = 50,
) -> list[Alert]:
    """
    Read cached alerts from SQLite, sorted by signal priority and recency.

    Args:
        signal_filter: Optional. Filter to one signal level: "high" | "medium" | "low".
        ticker_filter: Optional. Filter to a specific NSE ticker e.g. "RELIANCE".
        limit:         Maximum number of alerts to return (default 50).

    Returns:
        List of Alert objects, sorted:
            - HIGH signals first
            - Within same strength: newest first
            - Filtered by signal_filter and/or ticker_filter if provided.

    SQL ORDERING TRICK:
        Standard ORDER BY on signal_strength (text) would sort alphabetically:
        "high", "low", "medium" — which is wrong.
        Instead we use CASE WHEN to map to numeric priority:
            high=1, medium=2, low=3
        This gives us the correct HIGH → MEDIUM → LOW order.
    """
    conn = get_conn()
    try:
        # Build WHERE clause dynamically based on optional filters
        conditions = []
        params = []

        if signal_filter:
            conditions.append("signal_strength = ?")
            params.append(signal_filter.lower())

        if ticker_filter:
            conditions.append("UPPER(ticker) = ?")
            params.append(ticker_filter.upper())

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        # Uses CASE WHEN for correct signal_strength ordering (HIGH first)
        query = f"""
        SELECT * FROM alerts
        {where_clause}
        ORDER BY
            CASE signal_strength
                WHEN 'high'   THEN 1
                WHEN 'medium' THEN 2
                ELSE               3
            END ASC,
            created_at DESC
        LIMIT ?
        """
        params.append(limit)

        rows = conn.execute(query, params).fetchall()
        alerts = [_row_to_alert(row) for row in rows]
        print(f"[alert_store] Loaded {len(alerts)} alerts from cache.")
        return alerts

    finally:
        conn.close()


def clear_alerts() -> None:
    """
    Delete ALL alerts from the cache table.

    Called before a fresh full scan if you want a clean slate.
    Currently NOT called by orchestrator (upsert handles deduplication),
    but exposed here for manual use or testing.
    """
    conn = get_conn()
    try:
        conn.execute("DELETE FROM alerts")
        conn.commit()
        print("[alert_store] Cleared all cached alerts.")
    finally:
        conn.close()


# ── Internal helper ────────────────────────────────────────────────────────────

def _row_to_alert(row) -> Alert:
    """
    Convert a sqlite3.Row (dict-like) back into an Alert Pydantic model.

    Handles:
        - raw_data: JSON string → dict
        - created_at: ISO string → datetime
        - alert_type: string → AlertType enum
        - signal_strength: string → SignalStrength enum
    """
    return Alert(
        id=row["id"],
        ticker=row["ticker"],
        alert_type=AlertType(row["alert_type"]),
        signal_strength=SignalStrength(row["signal_strength"]),
        title=row["title"],
        why_it_matters=row["why_it_matters"],
        action_hint=row["action_hint"],
        source_url=row["source_url"],
        source_label=row["source_label"],
        raw_data=json.loads(row["raw_data"]),
        created_at=datetime.fromisoformat(row["created_at"]),
    )
