"""
routes/watchlist.py
===================
FastAPI router for managing the user's stock watchlist.

ENDPOINTS:
    GET  /watchlist                → Return current watchlist from SQLite.
    POST /watchlist                → Replace entire watchlist with new list.

STORAGE:
    The watchlist is stored in the SQLite `watchlist` table (see db/schema.sql).
    Each row: ticker TEXT PRIMARY KEY, added_at TEXT.
    POST /watchlist replaces the entire table contents (delete + re-insert).

WHY REPLACE (not append):
    For a hackathon demo, full replacement is simpler:
        - User can set exactly what they want in one call.
        - No need to manage add/remove individual tickers separately.
        - UI sends the full new list each time the user updates.

DEFAULT WATCHLIST:
    If the watchlist table is empty (e.g., first run), GET /watchlist
    returns DEFAULT_WATCHLIST from orchestrator and seeds the DB with it.

REQUEST/RESPONSE:
    POST body: {"tickers": ["RELIANCE", "INFY", "TCS"]}
    GET response:
        {
            "tickers": ["RELIANCE", "INFY"],
            "items": [{"ticker": "RELIANCE", "added_at": "..."}, ...],
            "count": 2
        }

USAGE:
    curl http://localhost:8001/watchlist
    curl -X POST http://localhost:8001/watchlist \\
         -H "Content-Type: application/json" \\
         -d '{"tickers": ["RELIANCE", "INFY", "HDFCBANK"]}'
"""

from datetime import datetime

from fastapi import APIRouter, HTTPException

from agents.orchestrator import DEFAULT_WATCHLIST
from db.db import get_conn
from models.watchlist import Watchlist, WatchlistItem, WatchlistUpdateRequest

router = APIRouter(tags=["watchlist"])


@router.get("/watchlist", response_model=Watchlist)
async def get_watchlist():
    """
    Return the current watchlist from SQLite.

    If the watchlist table is empty (first run), automatically seeds
    the DB with DEFAULT_WATCHLIST and returns it.

    Returns:
        Watchlist model with:
            tickers: ["RELIANCE", "INFY", ...]
            items:   [{ticker, added_at}, ...]
            count:   number of tickers
    """
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT ticker, added_at FROM watchlist ORDER BY added_at ASC"
        ).fetchall()

        if not rows:
            # First run — seed with default watchlist
            now = datetime.now().isoformat()
            for ticker in DEFAULT_WATCHLIST:
                conn.execute(
                    "INSERT OR IGNORE INTO watchlist (ticker, added_at) VALUES (?, ?)",
                    (ticker, now)
                )
            conn.commit()

            # Re-fetch after seeding
            rows = conn.execute(
                "SELECT ticker, added_at FROM watchlist ORDER BY added_at ASC"
            ).fetchall()

        items = [
            WatchlistItem(
                ticker=row["ticker"],
                added_at=datetime.fromisoformat(row["added_at"])
            )
            for row in rows
        ]

        return Watchlist(
            tickers=[item.ticker for item in items],
            items=items,
            count=len(items),
        )

    finally:
        conn.close()


@router.post("/watchlist", response_model=Watchlist)
async def update_watchlist(request: WatchlistUpdateRequest):
    """
    Replace the entire watchlist with a new list of tickers.

    ALL existing watchlist entries are deleted and replaced.
    Tickers are normalized (uppercase, .NS stripped) by the Pydantic validator
    in WatchlistUpdateRequest before reaching this function.

    Args:
        request: WatchlistUpdateRequest with:
            tickers: List of 1–50 NSE ticker strings.
                     Example: {"tickers": ["RELIANCE", "INFY", "TCS"]}

    Returns:
        New Watchlist with the updated tickers.

    HTTP Errors:
        400: If validation fails (empty list, >50 tickers, invalid format).
             Pydantic handles this automatically.

    EXAMPLE:
        POST /watchlist
        Body: {"tickers": ["RELIANCE", "INFY", "HDFCBANK", "TCS"]}

        Response: {"tickers": ["RELIANCE", "INFY", "HDFCBANK", "TCS"], "count": 4, ...}
    """
    if not request.tickers:
        raise HTTPException(status_code=400, detail="Watchlist cannot be empty.")

    now = datetime.now().isoformat()
    normalized_tickers = list(dict.fromkeys(request.tickers))  # deduplicate, preserve order

    conn = get_conn()
    try:
        # Delete existing watchlist (full replacement strategy)
        conn.execute("DELETE FROM watchlist")

        # Insert all new tickers
        for ticker in normalized_tickers:
            conn.execute(
                "INSERT INTO watchlist (ticker, added_at) VALUES (?, ?)",
                (ticker, now)
            )

        conn.commit()

        items = [
            WatchlistItem(ticker=t, added_at=datetime.fromisoformat(now))
            for t in normalized_tickers
        ]

        return Watchlist(
            tickers=normalized_tickers,
            items=items,
            count=len(items),
        )

    finally:
        conn.close()


# ── Internal helper (used by scan.py) ─────────────────────────────────────────

def get_watchlist_tickers() -> list[str]:
    """
    Helper used by routes/scan.py to read current watchlist tickers from DB.

    Returns:
        List of ticker strings from the DB watchlist table.
        Empty list if table is empty.
    """
    conn = get_conn()
    try:
        rows = conn.execute("SELECT ticker FROM watchlist ORDER BY added_at ASC").fetchall()
        return [row["ticker"] for row in rows]
    finally:
        conn.close()
