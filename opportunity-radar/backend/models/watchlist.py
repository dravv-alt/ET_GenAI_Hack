"""
models/watchlist.py
===================
Pydantic models for the user's stock watchlist.

USAGE:
    from models.watchlist import Watchlist, WatchlistItem, WatchlistUpdateRequest

PURPOSE:
    The watchlist is the list of NSE stock tickers the user wants monitored.
    It's stored in the SQLite `watchlist` table and managed via:
        GET  /watchlist   → returns current list
        POST /watchlist   → replaces the entire list

    Default watchlist (seeded on first run in routes/watchlist.py):
        RELIANCE, INFY, HDFCBANK, TCS, WIPRO,
        ICICIBANK, AXISBANK, SBIN, TATAMOTORS, BAJFINANCE

MODELS DEFINED HERE:
    1. WatchlistItem          — Individual ticker with metadata
    2. Watchlist              — Full watchlist response (list of items + raw tickers)
    3. WatchlistUpdateRequest — Request body for POST /watchlist
"""

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field, validator


# ── Single watchlist entry ─────────────────────────────────────────────────────
class WatchlistItem(BaseModel):
    """
    One ticker in the watchlist.

    Fields:
        ticker    NSE ticker symbol, uppercase, without .NS suffix.
                  e.g. "RELIANCE", "INFY", "HDFCBANK"
        added_at  When this ticker was added to the watchlist.
    """
    ticker: str
    added_at: datetime = Field(default_factory=datetime.now)


# ── Full watchlist response ────────────────────────────────────────────────────
class Watchlist(BaseModel):
    """
    Full watchlist — returned by GET /watchlist.

    Fields:
        tickers   Flat list of ticker strings (for easy front-end use).
        items     Full list of WatchlistItem objects (includes added_at timestamps).
        count     Number of stocks being monitored.
    """
    tickers: List[str]
    items: List[WatchlistItem]
    count: int


# ── Update request body ────────────────────────────────────────────────────────
class WatchlistUpdateRequest(BaseModel):
    """
    Request body for POST /watchlist.

    Replaces the ENTIRE watchlist with the provided ticker list.
    All tickers are normalized to uppercase and .NS suffix is stripped.

    Example body:
        {"tickers": ["RELIANCE", "INFY", "TCS"]}

    Validation:
        - Must provide at least 1 ticker.
        - Max 50 tickers (NSE scan is sequential, too many = slow).
    """
    tickers: List[str] = Field(
        ...,
        min_items=1,
        max_items=50,
        description="List of NSE ticker symbols to monitor (without .NS suffix)"
    )

    @validator("tickers", each_item=True)
    def normalize_ticker(cls, v: str) -> str:
        """
        Normalize ticker: strip whitespace, uppercase, remove .NS suffix.
        E.g. " reliance.NS " → "RELIANCE"
        """
        return v.strip().upper().replace(".NS", "")
