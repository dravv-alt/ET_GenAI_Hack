"""
agents/signal_ranker.py
=======================
Deduplicates and ranks all alerts from all scanners into a final ordered list.

WHY DEDUPLICATION IS NEEDED:
    Multiple scanners can detect overlapping signals for the same ticker+type:
    - bulk_deal_scanner may detect RELIANCE INSIDER_BUY from block deal data.
    - insider_scanner may detect RELIANCE INSIDER_BUY from SAST filings.
    Both are valid signals but showing 2 INSIDER_BUY alerts for RELIANCE is
    confusing and noisy. We keep only the highest-strength version.

RANKING ALGORITHM:
    Input:  All alerts from all 4 scanners, potentially 20–50 items.
    Output: Deduplicated, sorted list ready for the UI.

    Step 1 — Deduplication:
        Key = f"{ticker}:{alert_type}"  (e.g. "RELIANCE:insider_buy")
        On key collision → keep the alert with HIGHER signal_strength.
        Tie-break: keep the one with the more recent created_at.

    Step 2 — Sorting:
        Primary:   signal_strength  (HIGH=3 > MEDIUM=2 > LOW=1)
        Secondary: created_at        (newer first)

SIGNAL WEIGHT MAP:
    HIGH   = 3
    MEDIUM = 2
    LOW    = 1
    (Used for both deduplication comparison and sorting)

USAGE:
    from agents.signal_ranker import rank
    ranked = rank(all_alerts)  # returns sorted, deduplicated list
"""

from models.alert import Alert, SignalStrength


# Numeric weights for comparison — higher = more important
_SIGNAL_WEIGHTS: dict[str, int] = {
    SignalStrength.HIGH: 3,
    SignalStrength.MEDIUM: 2,
    SignalStrength.LOW: 1,
    # Handle both enum and string values (config use_enum_values=True)
    "high": 3,
    "medium": 2,
    "low": 1,
}


def _weight(alert: Alert) -> int:
    """
    Get the numeric weight for an alert's signal_strength.

    Handles both enum values (SignalStrength.HIGH) and
    string values ("high") due to Pydantic Config use_enum_values=True.
    """
    strength = alert.signal_strength
    # May be enum or string depending on how Alert was constructed
    key = strength.value if hasattr(strength, "value") else str(strength)
    return _SIGNAL_WEIGHTS.get(key, 1)


def rank(alerts: list[Alert]) -> list[Alert]:
    """
    Deduplicate and rank a mixed list of alerts from all scanners.

    Args:
        alerts: Combined output from bulk_deal_scanner, insider_scanner,
                filing_scanner, and sentiment_scanner. May contain duplicates.

    Returns:
        Deduplicated list of Alert objects sorted by:
            1. Signal strength (HIGH first)
            2. Recency (newest first within same strength level)

    DEDUPLICATION KEY:
        f"{ticker}:{alert_type}"
        Examples:
            "RELIANCE:insider_buy"
            "INFY:sentiment_shift"
            "HDFCBANK:earnings_beat"

        Two alerts with the same key but different strengths → keep the stronger one.
        Two alerts with the same key AND same strength → keep the newer one.

    EXAMPLE:
        Input:  [RELIANCE INSIDER_BUY HIGH, RELIANCE INSIDER_BUY MEDIUM, INFY BULK_DEAL HIGH]
        Output: [RELIANCE INSIDER_BUY HIGH, INFY BULK_DEAL HIGH]
        (RELIANCE INSIDER_BUY MEDIUM was deduplicated because HIGH version exists)
    """
    if not alerts:
        return []

    # Step 1: Deduplication
    # seen dict: key → best Alert seen so far for that key
    seen: dict[str, Alert] = {}

    for alert in alerts:
        # Build the dedup key from ticker + alert_type
        alert_type_str = (
            alert.alert_type.value
            if hasattr(alert.alert_type, "value")
            else str(alert.alert_type)
        )
        key = f"{alert.ticker.upper()}:{alert_type_str}"

        if key not in seen:
            # First alert for this key → accept it
            seen[key] = alert
        else:
            existing = seen[key]
            existing_weight = _weight(existing)
            new_weight = _weight(alert)

            if new_weight > existing_weight:
                # New alert has stronger signal → replace
                seen[key] = alert
            elif new_weight == existing_weight:
                # Same strength → keep the more recent one
                if alert.created_at > existing.created_at:
                    seen[key] = alert
            # else: existing is stronger → keep existing (do nothing)

    # Step 2: Sort by weight descending, then recency descending
    ranked = sorted(
        seen.values(),
        key=lambda a: (_weight(a) * -1, a.created_at),  # -1 to reverse (highest first)
        reverse=False,
    )

    print(
        f"[signal_ranker] Ranked {len(alerts)} alerts → "
        f"{len(ranked)} unique after deduplication."
    )
    return ranked
