"""
routes/alerts.py
================
FastAPI router for the alert feed endpoints.

ENDPOINTS:
    GET /alerts               → Returns ranked alert feed from SQLite cache.
    GET /alerts/{ticker}      → Returns all alerts for one specific NSE ticker.

THESE ENDPOINTS ARE READ-ONLY:
    - They read from the SQLite alerts table via alert_store.get_cached_alerts().
    - They do NOT trigger a fresh scan (that's POST /scan in routes/scan.py).
    - If no scan has been run yet, they return an empty list.

QUERY PARAMETERS (GET /alerts):
    limit  : int = 20        — Max alerts to return (1–100).
    signal : str = None      — Filter by signal strength: "high" | "medium" | "low".
    type   : str = None      — Filter by alert type: "insider_buy" | "bulk_deal" | etc.

RESPONSE FORMAT:
    {
        "alerts": [...Alert objects...],
        "total": 5,
        "filters_applied": {"signal": "high", "limit": 20}
    }

ROUTER PREFIX:
    This router is mounted at / in main.py (no prefix), so:
        GET /alerts
        GET /alerts/{ticker}

USAGE:
    import from main.py:
        from routes.alerts import router as alerts_router
        app.include_router(alerts_router)
"""

from fastapi import APIRouter, HTTPException, Query

from models.alert import AlertType
from services.alert_store import get_cached_alerts

# Router — no prefix here because main.py mounts it without a prefix
router = APIRouter(tags=["alerts"])


@router.get("/alerts")
async def get_all_alerts(
    limit: int = Query(default=20, ge=1, le=100, description="Max alerts to return"),
    signal: str = Query(
        default=None,
        description="Filter by signal strength: 'high' | 'medium' | 'low'"
    ),
    type: str = Query(
        default=None,
        description="Filter by alert type e.g. 'insider_buy' | 'bulk_deal' | 'sentiment_shift'"
    ),
):
    """
    Return the ranked alert feed from the SQLite cache.

    The cache is populated by POST /scan. If no scan has been run,
    this returns an empty list (not an error).

    Alerts are pre-sorted by signal strength (HIGH first) and recency.

    Args:
        limit:  Maximum number of alerts to return (1–100, default 20).
        signal: Optional filter — only return alerts with this signal_strength.
                Valid values: "high", "medium", "low".
        type:   Optional filter — only return alerts with this alert_type.
                Valid values: "insider_buy", "insider_sell", "bulk_deal",
                "earnings_beat", "earnings_miss", "sentiment_shift",
                "regulatory_approval", "capex_announcement".

    Returns:
        JSON with:
            alerts: List of alert objects.
            total:  Count of alerts returned.
            filters_applied: Echo of applied filters.

    HTTP Errors:
        400: Invalid signal value provided.
    """
    # Validate signal filter if provided
    valid_signals = {"high", "medium", "low"}
    if signal and signal.lower() not in valid_signals:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid signal value '{signal}'. Must be one of: {valid_signals}"
        )

    # Validate alert type filter if provided
    valid_types = {e.value for e in AlertType}
    if type and type.lower() not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid alert type '{type}'. Must be one of: {valid_types}"
        )

    # Fetch from SQLite
    alerts = get_cached_alerts(
        signal_filter=signal.lower() if signal else None,
        limit=limit,
    )

    # Apply type filter in Python (not in SQL to keep query simple)
    if type:
        alerts = [a for a in alerts if str(a.alert_type.value if hasattr(a.alert_type, 'value') else a.alert_type) == type.lower()]

    return {
        "alerts": [a.dict() for a in alerts],
        "total": len(alerts),
        "filters_applied": {
            "signal": signal,
            "type": type,
            "limit": limit,
        },
    }


@router.get("/alerts/{ticker}")
async def get_alerts_for_ticker(ticker: str):
    """
    Return all cached alerts for a single NSE ticker.

    Args:
        ticker: NSE symbol (case-insensitive, .NS suffix optional).
                Examples: "RELIANCE", "reliance", "RELIANCE.NS"

    Returns:
        JSON with:
            ticker:  Normalized ticker string (uppercase, no .NS).
            alerts:  All alerts for this ticker, sorted by signal strength.
            total:   Count of alerts for this ticker.

    HTTP Errors:
        404: Not raised — returns empty list if no alerts found for ticker.
             (Client can distinguish 'no alerts' from 'not found' via total=0.)
    """
    # Normalize: uppercase, strip .NS suffix
    normalized_ticker = ticker.upper().replace(".NS", "").strip()

    alerts = get_cached_alerts(ticker_filter=normalized_ticker, limit=100)

    return {
        "ticker": normalized_ticker,
        "alerts": [a.dict() for a in alerts],
        "total": len(alerts),
    }
