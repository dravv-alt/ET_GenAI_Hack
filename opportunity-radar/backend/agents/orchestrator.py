"""
agents/orchestrator.py
======================
Master agent that coordinates all scanners, ranks signals, and caches results.

ROLE:
    The orchestrator is the single entry point called by the /scan route.
    It wires together all 4 scanners (bulk deal, insider, filing, sentiment),
    merges their outputs, ranks signals, and saves to SQLite.

EXECUTION ORDER:
    1. bulk_deal_scanner.scan(watchlist)    — NSE bulk deal data → alerts
    2. insider_scanner.scan(watchlist)      — SAST disclosures → alerts
    3. filing_scanner.scan(watchlist)       — Quarterly results + corpactions → alerts
    4. sentiment_scanner.scan_all(watchlist) — LLM sentiment analysis → alerts
    5. Merge all 4 lists into one combined list
    6. signal_ranker.rank(combined)         — Dedup + sort by strength
    7. alert_store.save_alerts(ranked)      — Persist to SQLite
    8. Return ranked list to the /scan route

WHY SYNCHRONOUS:
    For the hackathon, all scanners run sequentially in a single Python process.
    This is intentional — simpler, no async complexity, no job queues.
    Expected time for 10 tickers: 15–30 seconds (mostly LLM + yfinance latency).

    In production you'd use asyncio.gather() or a Celery task queue.

ERROR ISOLATION:
    Each scanner is wrapped in try/except so ONE failing scanner doesn't
    block all others. If the sentiment scanner's LLM call fails, bulk deal
    and filing alerts still get returned.

DEFAULT WATCHLIST:
    If an empty watchlist is provided, we use the DEFAULT_WATCHLIST (10 major NSE stocks).
    Can be overridden via POST /watchlist.

USAGE:
    from agents.orchestrator import run_scan
    alerts = await run_scan(["RELIANCE", "INFY", "HDFCBANK"])
"""

from agents import bulk_deal_scanner, filing_scanner, insider_scanner, sentiment_scanner
from agents.signal_ranker import rank
from models.alert import Alert
from services.alert_store import save_alerts

# Default watchlist — used if /scan is called with an empty list
DEFAULT_WATCHLIST = [
    "RELIANCE", "INFY", "HDFCBANK", "TCS", "WIPRO",
    "ICICIBANK", "AXISBANK", "SBIN", "TATAMOTORS", "BAJFINANCE",
]


async def run_scan(watchlist: list[str]) -> list[Alert]:
    """
    Run all scanners on the given watchlist and return ranked alerts.

    This is an async function (for FastAPI compatibility) but runs
    synchronous scanner code internally. All I/O is blocking.

    Args:
        watchlist: List of NSE tickers to scan (without .NS suffix).
                   If empty, uses DEFAULT_WATCHLIST.

    Returns:
        Ranked, deduplicated list of Alert objects.
        Also persists them to SQLite via alert_store.save_alerts().

    PARTIAL SUCCESS:
        If one or more scanners fail, the orchestrator logs the error
        and continues with results from the remaining scanners.
        This ensures a partial result is always returned rather than
        raising a 500 error to the client.
    """
    # Use default if no watchlist provided
    if not watchlist:
        watchlist = DEFAULT_WATCHLIST
        print(f"[orchestrator] No watchlist provided. Using default: {DEFAULT_WATCHLIST}")

    # Normalize tickers: uppercase, remove .NS suffix
    watchlist_clean = [t.upper().replace(".NS", "") for t in watchlist]
    print(f"[orchestrator] Starting scan for {len(watchlist_clean)} tickers: {watchlist_clean}")

    all_alerts: list[Alert] = []

    # ── Scanner 1: Bulk Deal Scanner ──────────────────────────────────────────
    # Detects: INSIDER_BUY (promoter), INSIDER_SELL, BULK_DEAL (institutional)
    try:
        bulk_alerts = bulk_deal_scanner.scan(watchlist_clean)
        print(f"[orchestrator] Bulk deal scanner: {len(bulk_alerts)} alerts.")
        all_alerts.extend(bulk_alerts)
    except Exception as e:
        print(f"[orchestrator] Bulk deal scanner FAILED: {e}")

    # ── Scanner 2: Insider/SAST Scanner ──────────────────────────────────────
    # Detects: INSIDER_BUY, INSIDER_SELL from SAST regulatory disclosures
    try:
        insider_alerts = insider_scanner.scan(watchlist_clean)
        print(f"[orchestrator] Insider scanner: {len(insider_alerts)} alerts.")
        all_alerts.extend(insider_alerts)
    except Exception as e:
        print(f"[orchestrator] Insider scanner FAILED: {e}")

    # ── Scanner 3: Filing Scanner ─────────────────────────────────────────────
    # Detects: EARNINGS_BEAT, EARNINGS_MISS, CAPEX_ANNOUNCEMENT, REGULATORY_APPROVAL
    try:
        filing_alerts = filing_scanner.scan(watchlist_clean)
        print(f"[orchestrator] Filing scanner: {len(filing_alerts)} alerts.")
        all_alerts.extend(filing_alerts)
    except Exception as e:
        print(f"[orchestrator] Filing scanner FAILED: {e}")

    # ── Scanner 4: Sentiment Scanner (LLM) ───────────────────────────────────
    # Detects: SENTIMENT_SHIFT — only for tickers with commentary data
    # This is the most likely to be slow (LLM API call per ticker).
    # If no API key is configured, this scanner returns [] gracefully.
    try:
        sentiment_alerts = sentiment_scanner.scan_all(watchlist_clean)
        print(f"[orchestrator] Sentiment scanner: {len(sentiment_alerts)} alerts.")
        all_alerts.extend(sentiment_alerts)
    except Exception as e:
        print(f"[orchestrator] Sentiment scanner FAILED: {e}")

    # ── Rank and deduplicate ──────────────────────────────────────────────────
    print(f"[orchestrator] Total raw alerts before ranking: {len(all_alerts)}")
    ranked_alerts = rank(all_alerts)
    print(f"[orchestrator] After deduplication: {len(ranked_alerts)} alerts.")

    # ── Persist to SQLite ─────────────────────────────────────────────────────
    # Saves ranked alerts so GET /alerts can return them without re-scanning.
    try:
        save_alerts(ranked_alerts)
    except Exception as e:
        print(f"[orchestrator] Failed to save alerts to SQLite: {e}")
        # Continue — at least return the in-memory results

    print(f"[orchestrator] Scan complete. Returning {len(ranked_alerts)} alerts.")
    return ranked_alerts
