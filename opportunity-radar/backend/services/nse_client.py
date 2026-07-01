"""
services/nse_client.py
======================
NSE (National Stock Exchange) public API client with browser-like headers,
session-cookie management, and JSON fallback for blocked requests.

WHY THIS IS TRICKY:
    NSE's public APIs (nseindia.com) block non-browser HTTP requests.
    They use Cloudflare + cookie-based bot detection.

STRATEGY TO BYPASS (legally):
    1. Create a requests.Session() — maintains cookies across calls.
    2. First, hit the NSE homepage to obtain session cookies (critical step).
    3. Use browser-like headers (User-Agent, Referer, Accept-Language).
    4. Wrap every API call in try/except — on ANY failure (403, timeout,
       JSONDecodeError) → load the corresponding sample_*.json fallback.
    5. Cache responses with functools.lru_cache to avoid repeated hits.

FUNCTIONS EXPORTED:
    get_bulk_deals()              → list of bulk/block deal records
    get_quarterly_results(symbol) → quarterly financials dict for a ticker
    get_corporate_actions(symbol) → list of corporate actions (dividends, buybacks)
    get_insider_trades(symbol)    → list of SAST/promoter trade disclosures

FALLBACK FILES (in data/):
    data/sample_bulk_deals.json     → used if get_bulk_deals() NSE call fails
    data/sample_insider_trades.json → used if get_insider_trades() NSE call fails
    For quarterly_results and corporate_actions, we return empty dict/list on failure
    (caller handles gracefully; filing_scanner uses yfinance as secondary source).

NOTE ON CACHING:
    lru_cache on get_bulk_deals() caches for the process lifetime.
    This is intentional for hackathon: you call /scan once per demo session.
    In production, add a TTL or use a time-based cache key.
"""

import json
import time
from functools import lru_cache
from pathlib import Path

import requests

# ── Sample data paths ─────────────────────────────────────────────────────────
_DATA_DIR = Path(__file__).parent.parent / "data"
_SAMPLE_BULK_DEALS = _DATA_DIR / "sample_bulk_deals.json"
_SAMPLE_INSIDER = _DATA_DIR / "sample_insider_trades.json"

# ── NSE session setup ──────────────────────────────────────────────────────────
# A module-level Session so cookies persist across all calls in this process.
_session = requests.Session()

# Browser-like headers — NSE will reject requests without these
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.nseindia.com/",
    "Connection": "keep-alive",
}

_NSE_BASE = "https://www.nseindia.com"
_session_initialized = False


def _init_nse_session() -> None:
    """
    Prime the NSE session by hitting the homepage to get necessary cookies.

    WHY: NSE requires valid session cookies (nsit, nseappid, etc.) before
    it will respond to API calls. Without this step, every API call returns 403.

    This is called lazily on the FIRST NSE API call in a process run.
    If it fails (no internet), we continue — the individual API call will
    then also fail and fall back to sample data.
    """
    global _session_initialized
    if _session_initialized:
        return
    try:
        _session.get(_NSE_BASE, headers=_HEADERS, timeout=8)
        time.sleep(0.5)  # Brief pause — mimics human browser behavior
        _session_initialized = True
        print("[nse_client] NSE session initialized (cookies acquired).")
    except Exception as e:
        print(f"[nse_client] Could not reach NSE homepage: {e}. Will use fallback data.")
        _session_initialized = True  # Set True anyway to avoid repeated attempts


def _nse_get(url: str, timeout: int = 8) -> dict | list:
    """
    Internal helper: sends a authenticated GET request to NSE API.

    Args:
        url:     Full NSE API endpoint URL.
        timeout: Request timeout in seconds.

    Returns:
        Parsed JSON response (dict or list).

    Raises:
        Exception: On any HTTP/network/JSON error — caller catches and falls back.
    """
    _init_nse_session()
    resp = _session.get(url, headers=_HEADERS, timeout=timeout)
    resp.raise_for_status()  # Raises HTTPError for 4xx/5xx
    return resp.json()


# ── Public API functions ───────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def get_bulk_deals() -> list[dict]:
    """
    Fetches all bulk/block deals from NSE (today's data).

    Returns list of deal records. Each record has:
        symbol       : str  — NSE ticker symbol (e.g. "RELIANCE")
        client_name  : str  — Name of buyer/seller
        deal_type    : str  — "BUY" or "SELL"
        quantity     : int  — Number of shares traded
        price        : float — Deal price per share
        value_cr     : float — Total deal value in crores (computed as qty*price/1e7)

    Returns:
        list[dict]: Deal records, or sample data if NSE is unreachable.

    FALLBACK: Loads data/sample_bulk_deals.json
              This fallback has promoter buys and institutional deals
              pre-designed to trigger High and Medium signal alerts.
    """
    try:
        # NSE block deal endpoint — returns all block/bulk deals for the day
        url = f"{_NSE_BASE}/api/block-deal"
        raw_data = _nse_get(url)

        # NSE returns {"data": [...]} for this endpoint
        deals = raw_data.get("data", raw_data) if isinstance(raw_data, dict) else raw_data

        # Normalize value_cr if not already present
        normalized = []
        for d in deals:
            if "value_cr" not in d:
                qty = float(d.get("quantity", d.get("bdQty", 0)) or 0)
                price = float(d.get("price", d.get("bdTradePricepershare", 0)) or 0)
                d["value_cr"] = round(qty * price / 1e7, 2)
            # Normalize field names (NSE API uses different key names sometimes)
            normalized.append({
                "symbol": d.get("symbol", d.get("mktType", "")),
                "client_name": d.get("client_name", d.get("clientName", "")),
                "deal_type": d.get("deal_type", d.get("buySell", "")).upper(),
                "quantity": int(d.get("quantity", d.get("bdQty", 0)) or 0),
                "price": float(d.get("price", d.get("bdTradePricepershare", 0)) or 0),
                "value_cr": d["value_cr"],
                "date": d.get("date", d.get("tradeDate", "")),
            })
        print(f"[nse_client] Fetched {len(normalized)} bulk deals from NSE.")
        return normalized

    except Exception as e:
        print(f"[nse_client] get_bulk_deals failed: {e}. Using fallback data.")
        return json.loads(_SAMPLE_BULK_DEALS.read_text())


def get_quarterly_results(symbol: str) -> dict:
    """
    Fetches the latest quarterly financial results for a given NSE ticker.

    Args:
        symbol: NSE ticker without .NS suffix (e.g. "RELIANCE")

    Returns:
        dict with financial data. Key fields (if available):
            revenue       : float — Total income in crores
            pat           : float — Profit After Tax in crores
            eps           : float — Earnings per share
            yoy_growth_pct: float — YoY PAT growth percentage
            beat_miss     : str   — "beat" | "miss" | "inline" | "unknown"

    Returns {} on failure — filing_scanner falls back to yfinance in that case.
    """
    try:
        # NSE financial endpoint
        url = f"{_NSE_BASE}/api/quote-equity?symbol={symbol}&section=financials"
        data = _nse_get(url)

        # Extract relevant fields — NSE nests data inside multiple levels
        financials = {}
        if isinstance(data, dict):
            # Try to find quarterly results in the response
            fin_data = data.get("data", data)
            if "financialsNew" in fin_data:
                q = fin_data["financialsNew"].get("data", {}).get("quarterly", [])
                if q:
                    latest = q[0]  # Most recent quarter is first
                    financials = {
                        "revenue": float(latest.get("totalRevenue", 0) or 0),
                        "pat": float(latest.get("profitAfterTax", 0) or 0),
                        "eps": float(latest.get("basicEPS", 0) or 0),
                    }
                    # YoY: compare with same quarter last year (index 4)
                    if len(q) > 4:
                        prev_pat = float(q[4].get("profitAfterTax", 0) or 0)
                        if prev_pat != 0:
                            financials["yoy_growth_pct"] = round(
                                (financials["pat"] - prev_pat) / abs(prev_pat) * 100, 2
                            )

        print(f"[nse_client] Quarterly results for {symbol}: {financials}")
        return financials

    except Exception as e:
        print(f"[nse_client] get_quarterly_results({symbol}) failed: {e}. Returning empty.")
        return {}


def get_corporate_actions(symbol: str) -> list[dict]:
    """
    Fetches corporate actions for a given NSE ticker.

    Corporate actions include:
        - Dividends (regular, special, interim)
        - Bonus shares
        - Stock splits
        - Rights issues
        - Buybacks
        - Capital expenditure announcements (if filed)

    Args:
        symbol: NSE ticker without .NS suffix (e.g. "RELIANCE")

    Returns:
        list of action dicts. Each has at minimum:
            subject: str — the action description
            exDate:  str — ex-date for the corporate action

    Returns [] on failure — filing_scanner skips capex check gracefully.
    """
    try:
        url = f"{_NSE_BASE}/api/corporateAction?index=equities&symbol={symbol}"
        data = _nse_get(url)
        actions = data if isinstance(data, list) else data.get("data", [])
        print(f"[nse_client] Got {len(actions)} corporate actions for {symbol}.")
        return actions

    except Exception as e:
        print(f"[nse_client] get_corporate_actions({symbol}) failed: {e}. Returning [].")
        return []


def get_insider_trades(symbol: str) -> list[dict]:
    """
    Fetches SAST (Substantial Acquisition of Shares and Takeovers) /
    promoter shareholding disclosures for a ticker.

    These are the Form-C / Form-D filings that promoters and directors
    must submit to NSE when they buy/sell shares.

    Args:
        symbol: NSE ticker without .NS suffix (e.g. "RELIANCE")

    Returns:
        list of trade records. Each has:
            symbol         : str   — ticker
            acquirer_name  : str   — name of promoter/director
            acquirer_type  : str   — "Promoter" | "Director" | "KMP"
            transaction_type: str — "Buy" | "Sell"
            shares         : int   — number of shares
            value_cr       : float — total value in crores
            date           : str   — transaction date ISO string

    FALLBACK: Returns all entries from sample_insider_trades.json that
              match the requested symbol.
    """
    try:
        # NSE SAST disclosure endpoint
        url = f"{_NSE_BASE}/api/corporate-pledgedata?symbol={symbol}&ind=sast"
        data = _nse_get(url)
        trades = data if isinstance(data, list) else data.get("data", [])
        print(f"[nse_client] Got {len(trades)} insider trades for {symbol}.")
        return trades

    except Exception as e:
        print(f"[nse_client] get_insider_trades({symbol}) failed: {e}. Using fallback.")
        # Filter sample data to only return records matching this symbol
        all_trades = json.loads(_SAMPLE_INSIDER.read_text())
        return [t for t in all_trades if t.get("symbol", "").upper() == symbol.upper()]
