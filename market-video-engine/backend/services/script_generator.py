"""Script generation for the combined market narrative video.

Generates TTS-ready text with proper pronunciation for ticker symbols.
Each sentence is calibrated to match the visual segment duration.
"""

from __future__ import annotations

from typing import Any


# ── Ticker → Human-readable name lookup ──────────────────────────
TICKER_NAMES: dict[str, str] = {
    "RELIANCE": "Reliance Industries",
    "TCS": "T C S",
    "HDFCBANK": "H D F C Bank",
    "INFY": "Infosys",
    "ICICIBANK": "I C I C I Bank",
    "HINDUNILVR": "Hindustan Unilever",
    "ITC": "I T C",
    "KOTAKBANK": "Kotak Mahindra Bank",
    "LT": "Larsen and Toubro",
    "BAJFINANCE": "Bajaj Finance",
    "SBIN": "State Bank of India",
    "WIPRO": "Wipro",
    "AXISBANK": "Axis Bank",
    "MARUTI": "Maruti Suzuki",
    "ULTRACEMCO": "Ultra Tech Cement",
    "TITAN": "Titan Company",
    "ASIANPAINT": "Asian Paints",
    "SUNPHARMA": "Sun Pharma",
    "TATAMOTORS": "Tata Motors",
    "ONGC": "O N G C",
    "NESTLEIND": "Nestle India",
    "BHARTIARTL": "Bharti Airtel",
    "POWERGRID": "Power Grid",
    "NTPC": "N T P C",
    "ADANIENT": "Adani Enterprises",
    "ADANIPORTS": "Adani Ports",
    "TATASTEEL": "Tata Steel",
    "JSWSTEEL": "J S W Steel",
    "BAJAJFINSV": "Bajaj Finserv",
    "TECHM": "Tech Mahindra",
    "HCLTECH": "H C L Tech",
    "DRREDDY": "Dr. Reddy's",
    "DIVISLAB": "Divis Laboratories",
    "BRITANNIA": "Britannia Industries",
    "ZOMATO": "Zomato",
    "APOLLOHOSP": "Apollo Hospitals",
    "HAL": "Hindustan Aeronautics",
    "TRENT": "Trent Limited",
}


def _readable_name(ticker: str) -> str:
    """Converts a raw ticker symbol to a TTS-friendly name."""
    clean = str(ticker).replace(".NS", "").strip().upper()
    return TICKER_NAMES.get(clean, _humanize_ticker(clean))


def _humanize_ticker(ticker: str) -> str:
    """Fallback: splits camelCase/allcaps into spaced words for TTS."""
    # If it's all caps and short, spell it out with spaces
    if len(ticker) <= 4 and ticker.isalpha():
        return " ".join(ticker)
    # Otherwise just return as-is (TTS does okay with real words)
    return ticker


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _format_pct(value: float) -> str:
    sign = "plus" if value >= 0 else "minus"
    return f"{sign} {abs(value):.2f} percent"


def generate_combined_script(snapshot: dict[str, Any]) -> str:
    """Generates a compact narration with correct pronunciation.

    Each sentence maps to one visual segment. Word count is calibrated
    so that at normal TTS speed (~150 wpm), each sentence fills roughly
    the same duration as the corresponding video segment.

    Segment durations (frames × frame_repeat / fps):
      market_overview: 18 × 8 / 12 = ~12.0s → ~28 words
      gainers:         12 × 8 / 12 = ~8.0s  → ~18 words
      losers:          12 × 8 / 12 = ~8.0s  → ~18 words
      sector_rotation: 12 × 8 / 12 = ~8.0s  → ~18 words
      race_chart:      12 × 8 / 12 = ~8.0s  → ~18 words
      fii_dii:         10 × 8 / 12 = ~6.7s  → ~16 words
      ipo_tracker:     16 × 8 / 12 = ~10.7s → ~25 words
      outro:            3 × 8 / 12 = ~2.0s  → ~5 words
    """
    nifty = dict(snapshot.get("nifty", {}))
    movers = dict(snapshot.get("movers", {}))
    sectors = list(snapshot.get("sectors", []))
    flows = dict(snapshot.get("fii_dii", {}))
    ipos = list(snapshot.get("ipos", []))

    close_val = _to_float(nifty.get("close", 0.0))
    change_pct = _to_float(nifty.get("change_pct", 0.0))
    direction = "higher" if change_pct >= 0 else "lower"

    gainers = list(movers.get("gainers", []))
    losers = list(movers.get("losers", []))
    lead_gainer = gainers[0] if gainers else {}
    lead_loser = losers[0] if losers else {}

    gainer_name = _readable_name(lead_gainer.get("ticker", "the top gainer"))
    loser_name = _readable_name(lead_loser.get("ticker", "the top loser"))

    lead_sector = sectors[0] if sectors else {}
    sector_name = str(lead_sector.get("sector", "the broader market"))
    sector_change = _to_float(lead_sector.get("change_pct", 0.0))

    fii = _to_float(flows.get("fii_net_cr", 0.0))
    dii = _to_float(flows.get("dii_net_cr", 0.0))
    fii_dir = "buying" if fii >= 0 else "selling"
    dii_dir = "buying" if dii >= 0 else "selling"

    lead_ipo = ipos[0] if ipos else {}
    ipo_name = str(lead_ipo.get("name", "the lead IPO"))

    parts = [
        # Market Overview (~28 words, 12s)
        f"Nifty closed at {close_val:,.0f}, ending the session {direction} by {_format_pct(change_pct)}. Broad-based participation drove the move across key sectors with strong volume support.",

        # Gainers (~18 words, 8s)
        f"Leading the rally, {gainer_name} gained {_format_pct(_to_float(lead_gainer.get('change_pct', 0.0)))} on strong institutional volume.",

        # Losers (~18 words, 8s)
        f"On the flip side, {loser_name} declined {_format_pct(abs(_to_float(lead_loser.get('change_pct', 0.0))))} amid broad profit booking pressure.",

        # Sector Rotation (~18 words, 8s)
        f"{sector_name} sector led the rotation, with capital momentum shifting across the sectoral pack.",

        # Race Chart (~18 words, 8s)
        f"The performance leaderboard shows where long-term leadership is concentrating through this session's move.",

        # FII/DII (~16 words, 6.7s)
        f"Foreign institutions showed net {fii_dir} of {abs(fii):.0f} crore, while domestic institutions continued {dii_dir}.",

        # IPO Tracker (~15 words, 10.7s)
        f"In the primary market, {ipo_name} is seeing strong subscription demand with healthy grey market premiums.",

        # Outro (~5 words, 3.3s)
        "Will be back with more updates.",
    ]

    return " ".join(parts)
