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
	recency: Optional[float] = None
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
	profit_factor: Optional[float] = None
	expectancy: Optional[float] = None
	sharpe_ratio: Optional[float] = None
	sortino_ratio: Optional[float] = None
	max_drawdown_pct: Optional[float] = None
	calmar_ratio: Optional[float] = None
	exposure_pct: Optional[float] = None
	avg_time_in_trade_bars: Optional[float] = None
	avg_bars_to_target: Optional[float] = None
	avg_bars_to_stop: Optional[float] = None
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
