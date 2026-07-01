"""
agents/insider_scanner.py
=========================
Scans SAST (Substantial Acquisition of Shares and Takeovers) filings for
promoter and key management personnel (KMP) trading signals.

DIFFERENCE FROM BULK DEAL SCANNER:
    bulk_deal_scanner → Monitors the NSE block deal window (same-day trades).
    insider_scanner   → Monitors SAST Form-C/D filings (regulatory disclosures).

    SAST disclosures are required when promoters cross 2% threshold.
    These are richer data points because they include:
        - Pre/post holding percentages (shows the intent to accumulate)
        - Acquirer type (Promoter vs Director vs KMP)
        - Mode of acquisition (market purchase vs off-market vs ESOP)

SIGNAL GENERATION RULES:
    ┌──────────────────────────────────────────────────────────────────────┐
    │ Condition                              │ Alert Type   │ Strength     │
    ├──────────────────────────────────────────────────────────────────────┤
    │ Promoter BUY > ₹10 crore             │ INSIDER_BUY  │ HIGH         │
    │ Promoter BUY ₹2–10 crore            │ INSIDER_BUY  │ MEDIUM       │
    │ Director/KMP BUY > ₹2 crore          │ INSIDER_BUY  │ MEDIUM       │
    │ Promoter SELL > ₹15 crore            │ INSIDER_SELL │ MEDIUM       │
    └──────────────────────────────────────────────────────────────────────┘

DEDUPLICATION NOTE:
    Insider scanner and bulk deal scanner can both generate INSIDER_BUY alerts
    for the same ticker. The signal_ranker handles deduplication — keeping
    the highest-strength alert per ticker+type combination.

USAGE:
    from agents.insider_scanner import scan
    alerts = scan(["RELIANCE", "INFY", "WIPRO"])
"""

from models.alert import Alert, AlertType, SignalStrength
from services.nse_client import get_insider_trades


def scan(watchlist: list[str]) -> list[Alert]:
    """
    Scan SAST disclosure records for each ticker in the watchlist.

    Args:
        watchlist: List of NSE tickers (without .NS suffix).

    Returns:
        List of Alert objects for any meaningful insider trading patterns found.

    FLOW:
        For each ticker:
            1. Call nse_client.get_insider_trades(ticker)
            2. Classify each trade record into an alert (or skip if below threshold)
            3. Collect all alerts across all tickers
        Return the full list.
    """
    alerts = []
    watchlist_upper = [t.upper().replace(".NS", "") for t in watchlist]

    for ticker in watchlist_upper:
        trades = get_insider_trades(ticker)

        if not trades:
            continue  # No disclosures for this ticker → skip

        print(f"[insider_scanner] Processing {len(trades)} SAST records for {ticker}.")

        for trade in trades:
            # Normalize field names — NSE API uses inconsistent naming
            acquirer_name = trade.get("acquirer_name", trade.get("acquirerName", "Unknown"))
            acquirer_type = trade.get("acquirer_type", trade.get("acquirerType", "Unknown"))
            txn_type = trade.get("transaction_type", trade.get("transactionType", "")).strip().title()
            value_cr = float(trade.get("value_cr", 0) or 0)
            shares = int(trade.get("shares", trade.get("noOfSecAcq", 0)) or 0)
            pre_pct = float(trade.get("pre_holding_pct", trade.get("beforeAcqSharesPerc", 0)) or 0)
            post_pct = float(trade.get("post_holding_pct", trade.get("afterAcqSharesPerc", 0)) or 0)
            holding_change = round(post_pct - pre_pct, 3)

            is_promoter = "Promoter" in acquirer_type or "promoter" in acquirer_type.lower()
            is_buy = txn_type == "Buy"
            is_sell = txn_type == "Sell"

            # ── Rule 1: Promoter Large Buy → HIGH ────────────────────────────
            if is_promoter and is_buy and value_cr > 10:
                alerts.append(Alert(
                    ticker=ticker,
                    alert_type=AlertType.INSIDER_BUY,
                    signal_strength=SignalStrength.HIGH,
                    title=f"{acquirer_name} (Promoter) bought ₹{value_cr:.0f}cr of {ticker}",
                    why_it_matters=(
                        f"Promoter increased holding from {pre_pct:.2f}% to {post_pct:.2f}% "
                        f"(+{holding_change:.3f}%). This is a strong vote of confidence "
                        "from someone with the deepest knowledge of the company."
                    ),
                    action_hint=(
                        "Promoter accumulation is one of the most reliable bullish signals. "
                        "Review price levels and consider position sizing carefully."
                    ),
                    source_url=(
                        f"https://www.nseindia.com/companies-listing/corporate-filings/"
                        f"insider-trading/{ticker}"
                    ),
                    source_label="NSE SAST Disclosures",
                    raw_data=trade,
                ))

            # ── Rule 2: Promoter Moderate Buy → MEDIUM ────────────────────────
            elif is_promoter and is_buy and 2 <= value_cr <= 10:
                alerts.append(Alert(
                    ticker=ticker,
                    alert_type=AlertType.INSIDER_BUY,
                    signal_strength=SignalStrength.MEDIUM,
                    title=f"Promoter added ₹{value_cr:.0f}cr of {ticker} shares",
                    why_it_matters=(
                        "Moderate promoter accumulation — suggests conviction "
                        "but at a measured pace. May indicate a gradual re-rating thesis."
                    ),
                    action_hint="Watch for follow-up purchases to confirm this as a sustained trend.",
                    source_url=(
                        f"https://www.nseindia.com/companies-listing/corporate-filings/"
                        f"insider-trading/{ticker}"
                    ),
                    source_label="NSE SAST Disclosures",
                    raw_data=trade,
                ))

            # ── Rule 3: Director/KMP Buy → MEDIUM ────────────────────────────
            elif not is_promoter and is_buy and value_cr > 2:
                alerts.append(Alert(
                    ticker=ticker,
                    alert_type=AlertType.INSIDER_BUY,
                    signal_strength=SignalStrength.MEDIUM,
                    title=f"{acquirer_name} (Board member) bought ₹{value_cr:.0f}cr of {ticker}",
                    why_it_matters=(
                        "Board member buying their own stock with personal money "
                        "signals confidence in upcoming results or business momentum."
                    ),
                    action_hint="Board member buys are worth tracking — especially near result dates.",
                    source_url=(
                        f"https://www.nseindia.com/companies-listing/corporate-filings/"
                        f"insider-trading/{ticker}"
                    ),
                    source_label="NSE SAST Disclosures",
                    raw_data=trade,
                ))

            # ── Rule 4: Promoter Large Sell → MEDIUM ─────────────────────────
            elif is_promoter and is_sell and value_cr > 15:
                alerts.append(Alert(
                    ticker=ticker,
                    alert_type=AlertType.INSIDER_SELL,
                    signal_strength=SignalStrength.MEDIUM,
                    title=f"Promoter sold ₹{value_cr:.0f}cr of {ticker} (SAST filing)",
                    why_it_matters=(
                        f"Promoter reduced stake from {pre_pct:.2f}% to {post_pct:.2f}% "
                        f"({holding_change:.3f}% change). Track if this is part of a "
                        "larger divestiture pattern."
                    ),
                    action_hint=(
                        "Could be personal liquidity, estate planning, or charitable transfer. "
                        "Check for any pledge promoter if selling is frequent."
                    ),
                    source_url=(
                        f"https://www.nseindia.com/companies-listing/corporate-filings/"
                        f"insider-trading/{ticker}"
                    ),
                    source_label="NSE SAST Disclosures",
                    raw_data=trade,
                ))

    print(f"[insider_scanner] Generated {len(alerts)} alerts from SAST disclosures.")
    return alerts
