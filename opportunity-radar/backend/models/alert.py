"""
models/alert.py
===============
Pydantic data models for ALL alert-related types in Opportunity Radar.

USAGE:
    from models.alert import Alert, AlertType, SignalStrength

WHY PYDANTIC:
    - FastAPI uses these models for request/response serialization automatically.
    - They also serve as the in-memory contract between agents and routes.
    - .dict() / .json() methods make SQLite serialization trivial.

MODELS DEFINED HERE:
    1. SignalStrength  — Enum: HIGH | MEDIUM | LOW
    2. AlertType       — Enum: 8 types of investment signals
    3. Alert           — Main data class; one alert object = one surfaced signal
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ── Signal Strength ────────────────────────────────────────────────────────────
class SignalStrength(str, Enum):
    """
    Strength/urgency level of an alert.

    Rules (enforced in signal_ranker.py):
        HIGH   → Promoter buying large, major earnings beat, institutional block deal
        MEDIUM → Insider selling, modest earnings beat, capex filing
        LOW    → Minor corporate action, weak sentiment shift
    """
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ── Alert Types ────────────────────────────────────────────────────────────────
class AlertType(str, Enum):
    """
    Category of signal detected. Used for filtering in the UI and the
    GET /alerts?type= query parameter.

    Mapping to scanners:
        INSIDER_BUY          → bulk_deal_scanner, insider_scanner
        INSIDER_SELL         → bulk_deal_scanner, insider_scanner
        BULK_DEAL            → bulk_deal_scanner (institutional, not promoter)
        EARNINGS_BEAT        → filing_scanner
        EARNINGS_MISS        → filing_scanner
        SENTIMENT_SHIFT      → sentiment_scanner (LLM-powered)
        REGULATORY_APPROVAL  → filing_scanner (corporate actions)
        CAPEX_ANNOUNCEMENT   → filing_scanner (corporate actions)
    """
    INSIDER_BUY = "insider_buy"
    INSIDER_SELL = "insider_sell"
    BULK_DEAL = "bulk_deal"
    EARNINGS_BEAT = "earnings_beat"
    EARNINGS_MISS = "earnings_miss"
    SENTIMENT_SHIFT = "sentiment_shift"
    REGULATORY_APPROVAL = "regulatory_approval"
    CAPEX_ANNOUNCEMENT = "capex_announcement"


# ── Alert (main model) ─────────────────────────────────────────────────────────
class Alert(BaseModel):
    """
    Represents a single surfaced investment signal/opportunity.

    Fields:
        id              Auto-generated UUID string. Used as SQLite primary key.
        ticker          NSE ticker symbol e.g. "RELIANCE" (without .NS suffix).
        alert_type      One of AlertType enum values.
        signal_strength One of SignalStrength enum values.
        title           Headline, max ~80 chars. Should be specific and factual.
                        ✓ "Promoter bought ₹52cr of RELIANCE in open market"
                        ✗ "Something happened at RELIANCE"
        why_it_matters  One sentence: the investment implication for a retail investor.
        action_hint     Suggested action — always hedged ("consider reviewing",
                        not "buy immediately").
        source_url      Clickable link to the data source (NSE page, BSE filing, etc.)
        source_label    Human-readable label for the source e.g. "NSE Block Deal Data"
        raw_data        Original API/scanner data dict — stored as JSON in SQLite.
                        Useful for debugging and display in alert detail view.
        created_at      Timestamp when this alert was generated.

    SQLite storage:
        Serialized via .dict() → JSON for raw_data, ISO string for created_at.
        See services/alert_store.py for read/write logic.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ticker: str
    alert_type: AlertType
    signal_strength: SignalStrength
    title: str                           # max ~80 chars, specific headline
    why_it_matters: str                  # one sentence investment implication
    action_hint: str                     # suggested investor action (hedged)
    source_url: str                      # link to original data source
    source_label: str                    # human-readable source name
    raw_data: dict = {}                  # original raw data from scanner
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        # Allow enum values to be compared and used as dict keys
        use_enum_values = True
