"""Pydantic models for patterns and backtest results."""

from __future__ import annotations

from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel, Field


class PatternType(str, Enum):
	BREAKOUT = "breakout"
	SUPPORT_BOUNCE = "support_bounce"
	RSI_DIVERGENCE = "rsi_divergence"
	MACD_CROSSOVER = "macd_crossover"
	GOLDEN_CROSS = "golden_cross"
	DOUBLE_BOTTOM = "double_bottom"
	DOUBLE_TOP = "double_top"
	HEAD_SHOULDERS = "head_shoulders"
	HAMMER = "hammer"
	ENGULFING = "engulfing"


class Pattern(BaseModel):
	pattern_type: PatternType
	name: str
	detected_on: str
	current_price: float
	entry_price: float
	stop_loss: float
	target_price: float
	confidence: float
	description: str
	plain_english: str
	key_levels: Dict[str, float] = Field(default_factory=dict)


class BacktestResult(BaseModel):
	pattern_type: str
	ticker: str
	sample_count: int
	win_rate: Optional[float]
	avg_gain_pct: Optional[float]
	avg_loss_pct: Optional[float]
	rr_ratio: Optional[float]
	median_return_pct: Optional[float] = None
	holding_period_days: Optional[int] = None
	entry_mode: Optional[str] = None
	success_mode: Optional[str] = None
	note: str


class SupportResistanceLevel(BaseModel):
	level_type: str
	price: float
	touches: int
	strength: str
	date_first_seen: str
