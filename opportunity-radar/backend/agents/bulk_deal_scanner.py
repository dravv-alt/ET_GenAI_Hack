"""
agents/bulk_deal_scanner.py
===========================
Scans NSE bulk/block deal data for high-signal promoter and institutional trades.

WHAT IT DETECTS:
    Bulk deals are large trades executed through the NSE block window.
    When a PROMOTER buys in the open market, it's one of the strongest
    bullish signals — they have far more inside knowledge than any analyst.

SIGNAL GENERATION RULES:
    ┌──────────────────────────────────────────────────────────────────────┐
    │ Condition                              │ Alert Type   │ Strength     │
    ├──────────────────────────────────────────────────────────────────────┤
    │ Promoter BUY > ₹10 crore             │ INSIDER_BUY  │ HIGH         │
    │ Promoter SELL (any size > ₹5cr)       │ INSIDER_SELL │ MEDIUM       │
    │ Institutional buy > ₹50 crore        │ BULK_DEAL    │ HIGH         │
    │ Institutional buy ₹10–50 crore       │ BULK_DEAL    │ MEDIUM       │
    └──────────────────────────────────────────────────────────────────────┘

PROMOTER DETECTION:
    We detect promoters by checking if "PROMOTER" appears anywhere in the
    client_name string. This catches:
        "RELIANCE INDUSTRIES PROMOTER GROUP"
        "AZIM PREMJI TRUST (PROMOTER)"
        "PROMOTER - NANDAN NILEKANI"

    This is a heuristic — perfect accuracy isn't critical for a hackathon demo.
    In production, you'd cross-reference with the NSE shareholding pattern table.

USAGE:
    from agents.bulk_deal_scanner import scan
    alerts = scan(["RELIANCE", "INFY", "HDFCBANK"])
"""

from models.alert import Alert, AlertType, SignalStrength
from services.nse_client import get_bulk_deals


def scan(watchlist: list[str]) -> list[Alert]:
    """
    Scan today's bulk/block deals for signals in the given watchlist.

    Args:
        watchlist: List of NSE tickers to check (without .NS suffix).
                   e.g. ["RELIANCE", "INFY", "HDFCBANK"]

    Returns:
        List of Alert objects. May be empty if no deals matched the watchlist
        or no qualifying deals were found.

    FLOW:
        1. Fetch all bulk deals from NSE (or sample fallback).
        2. Filter to only deals where symbol is in the watchlist.
        3. For each qualifying deal, classify it and generate an Alert.
        4. Return all alerts (deduplication handled by signal_ranker).
    """
    alerts = []

    # Fetch all deals — uses LRU cache so repeated calls don't hit NSE again
    all_deals = get_bulk_deals()
    print(f"[bulk_deal_scanner] Checking {len(all_deals)} deals for {len(watchlist)} watchlist stocks.")

    # Normalize watchlist to uppercase for case-insensitive matching
    watchlist_upper = {t.upper().replace(".NS", "") for t in watchlist}

    for deal in all_deals:
        symbol = deal.get("symbol", "").upper().replace(".NS", "")
        if symbol not in watchlist_upper:
            continue  # Not in our watchlist, skip

        value_cr = float(deal.get("value_cr", 0) or 0)
        deal_type = deal.get("deal_type", "").upper()
        client_name = deal.get("client_name", "").upper()
        price = float(deal.get("price", 0) or 0)
        quantity = int(deal.get("quantity", 0) or 0)

        is_promoter = "PROMOTER" in client_name

        # ── Rule 1: Promoter Buy > ₹10 crore → HIGH signal ───────────────────
        if is_promoter and deal_type == "BUY" and value_cr > 10:
            alerts.append(Alert(
                ticker=symbol,
                alert_type=AlertType.INSIDER_BUY,
                signal_strength=SignalStrength.HIGH,
                title=f"Promoter bought ₹{value_cr:.0f}cr of {symbol} in open market",
                why_it_matters=(
                    "Promoter open-market purchases signal strong insider conviction. "
                    "They have more information than any external analyst."
                ),
                action_hint=(
                    "Consider reviewing your position. "
                    "Wait for price confirmation before adding exposure."
                ),
                source_url="https://www.nseindia.com/market-data/block-deal-archives",
                source_label="NSE Block Deal Archives",
                raw_data=deal,
            ))

        # ── Rule 2: Promoter Sell > ₹5 crore → MEDIUM signal ─────────────────
        elif is_promoter and deal_type == "SELL" and value_cr > 5:
            alerts.append(Alert(
                ticker=symbol,
                alert_type=AlertType.INSIDER_SELL,
                signal_strength=SignalStrength.MEDIUM,
                title=f"Promoter sold ₹{value_cr:.0f}cr of {symbol}",
                why_it_matters=(
                    "Promoter selling reduces their skin-in-game. "
                    "Watch for follow-through selling in coming sessions."
                ),
                action_hint=(
                    "Not necessarily bearish — could be personal liquidity needs. "
                    "Track the volume and frequency of sales."
                ),
                source_url="https://www.nseindia.com/market-data/block-deal-archives",
                source_label="NSE Block Deal Archives",
                raw_data=deal,
            ))

        # ── Rule 3: Institutional buy > ₹50 crore → HIGH signal ──────────────
        elif not is_promoter and deal_type == "BUY" and value_cr > 50:
            alerts.append(Alert(
                ticker=symbol,
                alert_type=AlertType.BULK_DEAL,
                signal_strength=SignalStrength.HIGH,
                title=f"Institutional block buy of ₹{value_cr:.0f}cr in {symbol}",
                why_it_matters=(
                    f"Large institutional accumulation (₹{value_cr:.0f}cr) signals "
                    "that smart money is building a significant position."
                ),
                action_hint=(
                    "Institutional interest is a strong validation signal. "
                    "Review fundamentals before following."
                ),
                source_url="https://www.nseindia.com/market-data/block-deal-archives",
                source_label="NSE Block Deal Archives",
                raw_data=deal,
            ))

        # ── Rule 4: Institutional buy ₹10–50 crore → MEDIUM signal ───────────
        elif not is_promoter and deal_type == "BUY" and 10 < value_cr <= 50:
            alerts.append(Alert(
                ticker=symbol,
                alert_type=AlertType.BULK_DEAL,
                signal_strength=SignalStrength.MEDIUM,
                title=f"Block deal: ₹{value_cr:.0f}cr buy in {symbol}",
                why_it_matters=(
                    "Mid-size block trades often precede larger institutional moves. "
                    "Worth tracking for follow-up volume."
                ),
                action_hint="Monitor for follow-up institutional activity in next 5 sessions.",
                source_url="https://www.nseindia.com/market-data/block-deal-archives",
                source_label="NSE Block Deal Archives",
                raw_data=deal,
            ))

    print(f"[bulk_deal_scanner] Generated {len(alerts)} alerts from bulk deals.")
    return alerts
