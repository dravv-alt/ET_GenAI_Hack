"""
agents/sentiment_scanner.py
===========================
LLM-powered management commentary tone shift detector.

CONCEPT:
    A company's management commentary (in earnings calls/annual reports) often
    changes tone before price action follows. A shift from "cautious" to "confident"
    language can foreshadow earnings upgrades. A retail investor almost never
    reads these lengthy documents — this scanner does it for them in ~2 seconds.

HOW IT WORKS:
    1. Loads prev and curr quarter commentary from data/sample_commentaries.json
       (or from actual NSE filings in a production system).
    2. Passes both to the LLM via llm_analyzer.analyze_sentiment().
    3. LLM returns a structured JSON analysis of the tone shift.
    4. If shift is detected with ≥55% confidence → creates an Alert.

LLM OUTPUT → ALERT MAPPING:
    shift_magnitude: "high"   → SignalStrength.HIGH
    shift_magnitude: "medium" → SignalStrength.MEDIUM
    shift_magnitude: "low"    → SignalStrength.LOW

    shift_direction:
        "positive" → AlertType.SENTIMENT_SHIFT (bullish)
        "negative" → AlertType.SENTIMENT_SHIFT (bearish — but same type for filtering)

COMMENTARIES SOURCE:
    For the hackathon demo, we use pre-loaded sample commentaries from:
        data/sample_commentaries.json
    Structure: {"RELIANCE": {"prev": "...", "curr": "..."}, ...}

    In a real system, these would come from:
        1. NSE quarterly results PDFs (parsed with pdfplumber)
        2. Screener.in API (cons sensus commentary)
        3. Tavily news search for analyst quotes

WHY THIS SCANNER IS VALUABLE:
    - 99% of retail investors never read management commentary.
    - A shift from "headwinds" to "tailwinds" language is a reliable early indicator.
    - This scanner reads it and flags the shift automatically.

USAGE:
    from agents.sentiment_scanner import scan_all, scan_ticker
    alerts = scan_all(["RELIANCE", "INFY", "TCS"])
"""

import json
from pathlib import Path

from models.alert import Alert, AlertType, SignalStrength
from services.llm_analyzer import analyze_sentiment

# Path to sample commentaries fallback data
_COMMENTARIES_PATH = (
    Path(__file__).parent.parent / "data" / "sample_commentaries.json"
)

# Map LLM shift_magnitude → SignalStrength enum
_MAGNITUDE_MAP = {
    "high": SignalStrength.HIGH,
    "medium": SignalStrength.MEDIUM,
    "low": SignalStrength.LOW,
}


def get_commentaries(ticker: str) -> tuple[str, str] | tuple[None, None]:
    """
    Load prev and curr management commentaries for a ticker.

    First checks sample_commentaries.json. In a production system, this
    would be replaced by a call to NSE PDF parser or news API.

    Args:
        ticker: NSE ticker without .NS (e.g. "RELIANCE").

    Returns:
        (prev_commentary, curr_commentary) strings if found.
        (None, None) if this ticker has no commentary data.
    """
    if not _COMMENTARIES_PATH.exists():
        print(f"[sentiment_scanner] sample_commentaries.json not found at {_COMMENTARIES_PATH}.")
        return None, None

    try:
        all_commentaries = json.loads(_COMMENTARIES_PATH.read_text(encoding="utf-8"))
        ticker_data = all_commentaries.get(ticker.upper())

        if not ticker_data:
            return None, None

        prev = ticker_data.get("prev", "")
        curr = ticker_data.get("curr", "")

        if prev and curr:
            return prev, curr
        return None, None

    except Exception as e:
        print(f"[sentiment_scanner] Failed to load commentaries: {e}")
        return None, None


def scan_ticker(ticker: str) -> Alert | None:
    """
    Run sentiment analysis for a single ticker.

    Args:
        ticker: NSE ticker without .NS suffix (e.g. "RELIANCE").

    Returns:
        Alert object if a meaningful sentiment shift is detected.
        None if:
            - No commentary data for this ticker
            - LLM detects no significant shift
            - LLM API unavailable

    FLOW:
        1. Load prev/curr commentaries for this ticker.
        2. Send to LLM via analyze_sentiment().
        3. If shift detected + confidence ≥ 0.55 → create Alert.
        4. Return Alert or None.
    """
    prev_commentary, curr_commentary = get_commentaries(ticker)

    if not prev_commentary or not curr_commentary:
        print(f"[sentiment_scanner] No commentary data for {ticker}. Skipping.")
        return None

    print(f"[sentiment_scanner] Analyzing sentiment shift for {ticker}...")

    # analyze_sentiment returns None if no confident shift detected
    result = analyze_sentiment(ticker, prev_commentary, curr_commentary)

    if not result:
        return None

    # Map LLM output → Alert fields
    direction = result.get("shift_direction", "neutral")
    magnitude = result.get("shift_magnitude", "low")
    key_change = result.get("key_change", "Management tone has shifted.")
    why = result.get("why_it_matters", "Sentiment shift may affect near-term price.")
    confidence = result.get("confidence", 0.0)

    # Choose signal strength from magnitude
    signal_strength = _MAGNITUDE_MAP.get(magnitude, SignalStrength.LOW)

    # Build the alert title with direction indicator
    direction_emoji = "📈" if direction == "positive" else "📉" if direction == "negative" else "↔️"
    title = (
        f"{direction_emoji} {ticker} management tone shift — "
        f"{direction.capitalize()} ({magnitude} magnitude)"
    )

    # Truncate if title is too long
    if len(title) > 80:
        title = title[:77] + "..."

    alert = Alert(
        ticker=ticker,
        alert_type=AlertType.SENTIMENT_SHIFT,
        signal_strength=signal_strength,
        title=title,
        why_it_matters=why,
        action_hint=(
            "Read the full management commentary before acting. "
            f"LLM confidence: {confidence:.0%}. Verify with price and volume action."
        ),
        source_url=(
            "https://www.nseindia.com/companies-listing/corporate-filings/"
            "quarterly-results"
        ),
        source_label="NSE Quarterly Results (LLM Analysis)",
        raw_data={
            "llm_result": result,
            "prev_excerpt": prev_commentary[:200],
            "curr_excerpt": curr_commentary[:200],
        },
    )

    print(
        f"[sentiment_scanner] {ticker} → {direction} shift, "
        f"{magnitude} magnitude, {confidence:.0%} confidence."
    )
    return alert


def scan_all(watchlist: list[str]) -> list[Alert]:
    """
    Run sentiment analysis for all tickers in the watchlist that have commentary data.

    Args:
        watchlist: List of NSE tickers (without .NS suffix).

    Returns:
        List of Alert objects (one per ticker with a detected shift).
        Empty list if no shifts found or LLM unavailable.

    NOTE:
        This makes one LLM API call per ticker that has commentary data.
        With Gemini free tier (15 RPM), 10 tickers = ~10 calls = fine.
    """
    alerts = []
    for ticker in watchlist:
        alert = scan_ticker(ticker.upper().replace(".NS", ""))
        if alert:
            alerts.append(alert)

    print(f"[sentiment_scanner] Generated {len(alerts)} sentiment alerts.")
    return alerts
