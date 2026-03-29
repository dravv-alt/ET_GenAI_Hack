"""Detects candlestick patterns like doji/engulfing."""

from __future__ import annotations

import pandas as pd

from config import CANDLE_TREND_LOOKBACK
from models.pattern import Pattern, PatternType


def _is_hammer(row: pd.Series) -> bool:
	body = abs(row["close"] - row["open"])
	upper_wick = row["high"] - max(row["close"], row["open"])
	lower_wick = min(row["close"], row["open"]) - row["low"]
	return lower_wick > body * 2 and upper_wick <= body


def _is_bullish_engulfing(prev: pd.Series, curr: pd.Series) -> bool:
	prev_body = prev["close"] - prev["open"]
	curr_body = curr["close"] - curr["open"]
	return prev_body < 0 and curr_body > 0 and curr["close"] > prev["open"] and curr["open"] < prev["close"]


def detect(df: pd.DataFrame) -> list[Pattern]:
	patterns: list[Pattern] = []
	if len(df) < 2:
		return patterns

	current_price = float(df.iloc[-1]["close"])
	last = df.iloc[-1]
	prev = df.iloc[-2]
	prior_downtrend = False
	if len(df) >= CANDLE_TREND_LOOKBACK:
		recent_closes = df["close"].iloc[-CANDLE_TREND_LOOKBACK:]
		prior_downtrend = recent_closes.is_monotonic_decreasing

	if _is_hammer(last) and prior_downtrend:
		patterns.append(
			Pattern(
				pattern_type=PatternType.HAMMER,
				name="Hammer",
				detected_on=str(last["date"]),
				current_price=current_price,
				entry_price=round(current_price * 1.005, 2),
				stop_loss=round(float(last["low"]) * 0.98, 2),
				target_price=round(current_price * 1.04, 2),
				confidence=0.52,
				description="Hammer candle with a long lower wick after a dip.",
				plain_english="Buyers pushed price up after a sharp dip, which can hint at a short-term bounce.",
				key_levels={"low": round(float(last["low"]), 2)},
			)
		)

	if _is_bullish_engulfing(prev, last) and prior_downtrend:
		patterns.append(
			Pattern(
				pattern_type=PatternType.ENGULFING,
				name="Bullish Engulfing",
				detected_on=str(last["date"]),
				current_price=current_price,
				entry_price=round(current_price * 1.005, 2),
				stop_loss=round(float(prev["low"]) * 0.98, 2),
				target_price=round(current_price * 1.05, 2),
				confidence=0.53,
				description="A bullish candle fully engulfed the previous bearish candle.",
				plain_english="A strong up day reversed the prior down day, suggesting buyers stepped in.",
				key_levels={},
			)
		)

	return patterns
