"""
agents/filing_scanner.py
========================
Scans quarterly results and corporate action filings for earnings and capex signals.

DATA SOURCES (in priority order):
    1. NSE API (nse_client.get_quarterly_results) — preferred, often blocked
    2. yfinance quarterly financials — reliable fallback for earnings data
    3. NSE corporate actions API (nse_client.get_corporate_actions) — for capex/buyback

WHAT IT DETECTS:
    1. EARNINGS BEAT  — PAT (Profit After Tax) grew >15% YoY → HIGH signal
    2. EARNINGS MISS  — PAT fell >10% YoY → MEDIUM signal (bearish, but still surfaced)
    3. CAPEX / Buyback — Corporate action with buyback/capex keywords → MEDIUM signal
    4. REGULATORY APPROVAL — Corporate action with approval keywords → MEDIUM signal

WHY YFINANCE:
    yfinance fetches from Yahoo Finance which aggregates NSE data reliably.
    For Indian stocks, use ticker format: "RELIANCE.NS"
    The quarterly_financials DataFrame has net income, total revenue, etc.

YOY CALCULATION:
    yfinance returns quarterly_financials as a DataFrame:
        - Columns are datetime periods (Q4 FY26, Q3 FY26, Q2 FY26...)
        - Rows are financial metrics (Net Income, Total Revenue, etc.)
    We compare column[0] (latest quarter) vs column[4] (same quarter last year).

CAPEX DETECTION:
    NSE corporate actions subjects are free-text. We scan for keywords:
        Capex, Capital expenditure, expansion, buyback, repurchase, approval
    This is a simple keyword match — good enough for a hackathon demo.

USAGE:
    from agents.filing_scanner import scan
    alerts = scan(["RELIANCE", "INFY", "HDFCBANK"])
"""

import time

from models.alert import Alert, AlertType, SignalStrength
from services.nse_client import get_corporate_actions, get_quarterly_results

# yfinance is imported inside the function to avoid crashing if not installed
# (graceful degradation — just won't generate earnings alerts)


def scan(watchlist: list[str]) -> list[Alert]:
    """
    Scan quarterly results and corporate actions for each ticker in the watchlist.

    Args:
        watchlist: List of NSE tickers (without .NS suffix).

    Returns:
        List of Alert objects. May include EARNINGS_BEAT, EARNINGS_MISS,
        CAPEX_ANNOUNCEMENT, and REGULATORY_APPROVAL alerts.

    FLOW:
        For each ticker:
            1. Try NSE quarterly results → fallback to yfinance
            2. Compute YoY PAT growth → generate earnings alert if significant
            3. Fetch corporate actions → scan subjects for capex/buyback keywords
            4. Collect and return all alerts
    """
    alerts = []
    watchlist_upper = [t.upper().replace(".NS", "") for t in watchlist]

    for ticker in watchlist_upper:
        print(f"[filing_scanner] Scanning {ticker}...")

        # ── Step 1: Get earnings data ─────────────────────────────────────────
        yoy_growth_pct = _get_yoy_pat_growth(ticker)

        if yoy_growth_pct is not None:
            # ── Rule 1: Earnings Beat (>15% YoY PAT growth) ──────────────────
            if yoy_growth_pct > 15:
                alerts.append(Alert(
                    ticker=ticker,
                    alert_type=AlertType.EARNINGS_BEAT,
                    signal_strength=SignalStrength.HIGH,
                    title=f"{ticker} Q results: PAT grew {yoy_growth_pct:.1f}% YoY — beat",
                    why_it_matters=(
                        f"Strong earnings momentum with {yoy_growth_pct:.1f}% profit growth. "
                        "This typically triggers analyst upgrades and institutional buying."
                    ),
                    action_hint=(
                        "Earnings beats often sustain price momentum for 2–4 weeks. "
                        "Watch for analyst revision triggers."
                    ),
                    source_url=(
                        "https://www.nseindia.com/companies-listing/corporate-filings/"
                        "quarterly-results"
                    ),
                    source_label="NSE Quarterly Results",
                    raw_data={"yoy_growth_pct": yoy_growth_pct, "ticker": ticker},
                ))

            # ── Rule 2: Earnings Miss (>10% YoY PAT decline) ─────────────────
            elif yoy_growth_pct < -10:
                alerts.append(Alert(
                    ticker=ticker,
                    alert_type=AlertType.EARNINGS_MISS,
                    signal_strength=SignalStrength.MEDIUM,
                    title=f"{ticker} Q results: PAT declined {abs(yoy_growth_pct):.1f}% YoY",
                    why_it_matters=(
                        f"Profit fell {abs(yoy_growth_pct):.1f}% vs same quarter last year. "
                        "Likely to trigger analyst downgrades."
                    ),
                    action_hint=(
                        "Review the reasons for the miss. "
                        "One-time items vs structural decline makes a big difference."
                    ),
                    source_url=(
                        "https://www.nseindia.com/companies-listing/corporate-filings/"
                        "quarterly-results"
                    ),
                    source_label="NSE Quarterly Results",
                    raw_data={"yoy_growth_pct": yoy_growth_pct, "ticker": ticker},
                ))

        # ── Step 2: Scan corporate actions ────────────────────────────────────
        corp_alerts = _scan_corporate_actions(ticker)
        alerts.extend(corp_alerts)

    print(f"[filing_scanner] Generated {len(alerts)} alerts from filings.")
    return alerts


# ── Internal Helpers ──────────────────────────────────────────────────────────

def _get_yoy_pat_growth(ticker: str) -> float | None:
    """
    Compute YoY PAT (Profit After Tax) growth percentage using best available source.

    Priority:
        1. NSE quarterly results API (get_quarterly_results)
           If it returns yoy_growth_pct directly, use it.
        2. yfinance quarterly_financials DataFrame
           Compare Net Income: latest quarter vs same quarter 1 year ago.

    Returns:
        float: YoY growth percentage (can be negative for a miss).
        None:  If no data available from either source.
    """
    # Try NSE API first
    nse_data = get_quarterly_results(ticker)
    if nse_data and "yoy_growth_pct" in nse_data:
        return nse_data["yoy_growth_pct"]

    # Fallback to yfinance
    try:
        import yfinance as yf
        time.sleep(0.3)  # Rate limit protection

        stock = yf.Ticker(f"{ticker}.NS")
        financials = stock.quarterly_financials

        if financials is None or financials.empty:
            return None

        # Look for Net Income row (yfinance uses "Net Income" as row label)
        # Get the available columns (sorted newest first by yfinance)
        cols = financials.columns.tolist()
        if len(cols) < 5:
            return None  # Need at least 5 quarters for YoY comparison

        # Find Net Income row — yfinance uses various key names
        net_income_row = None
        for key in ["Net Income", "Net Income Common Stockholders", "Net Income From Continuing Operations"]:
            if key in financials.index:
                net_income_row = financials.loc[key]
                break

        if net_income_row is None:
            return None

        latest_pat = float(net_income_row.iloc[0] or 0)   # Most recent quarter
        prev_pat = float(net_income_row.iloc[4] or 0)     # Same quarter 1 year ago

        if prev_pat == 0:
            return None  # Avoid division by zero

        growth = (latest_pat - prev_pat) / abs(prev_pat) * 100
        print(f"[filing_scanner] {ticker} YoY PAT growth: {growth:.1f}%")
        return round(growth, 2)

    except Exception as e:
        print(f"[filing_scanner] yfinance failed for {ticker}: {e}")
        return None


def _scan_corporate_actions(ticker: str) -> list[Alert]:
    """
    Scan corporate action filings for capex, buyback, and regulatory keywords.

    The 'subject' field of each corporate action is free-text from NSE.
    We do a simple keyword match to detect relevant announcements.

    Args:
        ticker: NSE ticker symbol (without .NS).

    Returns:
        List of Alert objects (0 or more).
    """
    alerts = []

    # Keyword sets for different alert types
    CAPEX_KEYWORDS = {"capex", "capital expenditure", "expansion", "plant", "capacity"}
    BUYBACK_KEYWORDS = {"buyback", "buy-back", "repurchase", "buy back"}
    APPROVAL_KEYWORDS = {"approval", "approved", "licence", "license", "clearance", "nod", "permit"}

    try:
        actions = get_corporate_actions(ticker)
    except Exception:
        return []

    for action in actions:
        subject = action.get("subject", action.get("series", "")).lower()
        ex_date = action.get("exDate", action.get("exDt", "N/A"))

        if not subject:
            continue

        # Check for capex/expansion
        if any(kw in subject for kw in CAPEX_KEYWORDS):
            alerts.append(Alert(
                ticker=ticker,
                alert_type=AlertType.CAPEX_ANNOUNCEMENT,
                signal_strength=SignalStrength.MEDIUM,
                title=f"{ticker} filed capex/expansion plan (ex-date: {ex_date})",
                why_it_matters=(
                    "Planned capital expenditure signals management confidence in "
                    "future demand. Capacity expansion often precedes revenue acceleration."
                ),
                action_hint=(
                    "Check the capex quantum and funding source (debt vs internal accruals). "
                    "Large debt-funded capex can pressure near-term margins."
                ),
                source_url=(
                    f"https://www.nseindia.com/companies-listing/corporate-filings/"
                    f"corporate-actions?symbol={ticker}"
                ),
                source_label="NSE Corporate Actions",
                raw_data=action,
            ))

        # Check for buyback
        elif any(kw in subject for kw in BUYBACK_KEYWORDS):
            alerts.append(Alert(
                ticker=ticker,
                alert_type=AlertType.CAPEX_ANNOUNCEMENT,
                signal_strength=SignalStrength.MEDIUM,
                title=f"{ticker} announced share buyback",
                why_it_matters=(
                    "Buybacks return cash to shareholders and signal management's view "
                    "that the stock is undervalued at current prices."
                ),
                action_hint=(
                    "Check buyback price vs current CMP. "
                    "Buybacks at a premium to market create an immediate price floor."
                ),
                source_url=(
                    f"https://www.nseindia.com/companies-listing/corporate-filings/"
                    f"corporate-actions?symbol={ticker}"
                ),
                source_label="NSE Corporate Actions",
                raw_data=action,
            ))

        # Check for regulatory approval
        elif any(kw in subject for kw in APPROVAL_KEYWORDS):
            alerts.append(Alert(
                ticker=ticker,
                alert_type=AlertType.REGULATORY_APPROVAL,
                signal_strength=SignalStrength.MEDIUM,
                title=f"{ticker}: Regulatory approval/clearance filed",
                why_it_matters=(
                    "Regulatory approvals unlock new markets or products. "
                    "They remove a key overhang that was suppressing the stock."
                ),
                action_hint=(
                    "Read the exact nature of the approval — "
                    "new drug approval is very different from a routine renewal."
                ),
                source_url=(
                    f"https://www.nseindia.com/companies-listing/corporate-filings/"
                    f"corporate-actions?symbol={ticker}"
                ),
                source_label="NSE Corporate Actions",
                raw_data=action,
            ))

    return alerts
