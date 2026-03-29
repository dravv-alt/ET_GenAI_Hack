"""
routes/scan.py
==============
FastAPI router for the scan trigger endpoint.

ENDPOINT:
    POST /scan   — Triggers a fresh scan for a given list of tickers.

DESIGN DECISION — SYNCHRONOUS:
    For the hackathon, POST /scan runs the full scan pipeline synchronously
    and returns the result in one response. The client waits for completion.
    This means:
        - Client sees the full result immediately after the request completes.
        - No polling needed.
        - Expected response time: 15–45 seconds for 10 stocks
          (mostly LLM calls for sentiment scanner + yfinance rate limiting).

    In production, this would become:
        POST /scan → immediately returns job_id
        GET /scan/status/{job_id} → polls for completion
        (Using Celery, RQ, or asyncio background tasks)

REQUEST BODY:
    List of NSE ticker strings: ["RELIANCE", "INFY", "HDFCBANK"]
    OR use default watchlist from GET /watchlist by sending an empty list: []

    Tickers are normalized (uppercase, .NS stripped) inside orchestrator.

RESPONSE:
    {
        "status": "complete",
        "alerts_found": 7,
        "tickers_scanned": ["RELIANCE", "INFY", "HDFCBANK"],
        "alerts": [...Alert objects...]   // Full ranked alert list
    }

ROUTER PREFIX:
    No prefix — mounted at / in main.py, so endpoint is POST /scan.

USAGE:
    curl -X POST http://localhost:8001/scan \\
         -H "Content-Type: application/json" \\
         -d '["RELIANCE", "INFY", "HDFCBANK", "TCS"]'
"""

from fastapi import APIRouter, HTTPException

from agents.orchestrator import DEFAULT_WATCHLIST, run_scan

router = APIRouter(tags=["scan"])


@router.post("/scan")
async def trigger_scan(watchlist: list[str] = None):
    """
    Trigger a fresh scan for the given list of NSE tickers.

    Runs all 4 scanners (bulk deal, insider, filing, sentiment) sequentially,
    deduplicates and ranks results, saves to SQLite, and returns the full list.

    Args:
        watchlist: JSON array of NSE ticker strings in the request body.
                   Example: ["RELIANCE", "INFY", "HDFCBANK"]
                   Use [] or omit body to scan the current watchlist from DB,
                   or falls back to DEFAULT_WATCHLIST if DB watchlist is also empty.

    Returns:
        JSON with:
            status:          "complete" (always, since we run synchronously)
            alerts_found:    Number of unique ranked alerts generated
            tickers_scanned: Normalized list of tickers that were scanned
            alerts:          Full list of ranked Alert objects

    HTTP Errors:
        500: If all scanners fail simultaneously (very unlikely due to fallbacks).

    NOTES:
        - Each scan fully refreshes the alert cache.
        - Stale alerts (>24h old) are auto-removed during save_alerts().
        - NSE fallback JSON files are used if NSE APIs are unreachable.
        - If LLM API key is not set, sentiment scanner is silently skipped.
    """
    # Use provided watchlist or fall back to reading from DB / default
    tickers_to_scan = []

    if watchlist:
        # Normalize: uppercase, strip .NS
        tickers_to_scan = [t.upper().replace(".NS", "").strip() for t in watchlist if t.strip()]
    else:
        # Try to load from SQLite watchlist table
        try:
            from routes.watchlist import get_watchlist_tickers
            tickers_to_scan = get_watchlist_tickers()
        except Exception:
            pass

    # Ultimate fallback
    if not tickers_to_scan:
        tickers_to_scan = DEFAULT_WATCHLIST

    try:
        ranked_alerts = await run_scan(tickers_to_scan)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Scan failed: {str(e)}"
        )

    return {
        "status": "complete",
        "alerts_found": len(ranked_alerts),
        "tickers_scanned": tickers_to_scan,
        "alerts": [a.dict() for a in ranked_alerts],
    }
