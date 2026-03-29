"""Detects RSI/MACD momentum signals."""

from __future__ import annotations

import pandas as pd

from config import (
	GOLDEN_CROSS_LOOKBACK,
	MACD_CROSS_LOOKBACK,
	RSI_DIVERGENCE_EARLIER_WINDOW,
	RSI_DIVERGENCE_RECENT_WINDOW,
)
from models.pattern import Pattern, PatternType


def _crossed_above_recent(series_a: pd.Series, series_b: pd.Series, lookback: int = 5) -> bool:
	if len(series_a) < lookback + 1 or len(series_b) < lookback + 1:
		return False
	for i in range(-lookback, 0):
		if series_a.iloc[i - 1] <= series_b.iloc[i - 1] and series_a.iloc[i] > series_b.iloc[i]:
			return True
	return False


def _find_rsi_divergence(df: pd.DataFrame) -> Pattern | None:
	total_window = RSI_DIVERGENCE_RECENT_WINDOW + RSI_DIVERGENCE_EARLIER_WINDOW
	if "rsi" not in df.columns or len(df) < total_window:
		return None

	recent = df.tail(RSI_DIVERGENCE_RECENT_WINDOW)
	earlier = df.iloc[-total_window:-RSI_DIVERGENCE_RECENT_WINDOW]
	recent_low_idx = recent["low"].idxmin()
	earlier_low_idx = earlier["low"].idxmin()

	recent_low = float(df.loc[recent_low_idx, "low"])
	earlier_low = float(df.loc[earlier_low_idx, "low"])
	recent_rsi = float(df.loc[recent_low_idx, "rsi"])
	earlier_rsi = float(df.loc[earlier_low_idx, "rsi"])

	if recent_low < earlier_low and recent_rsi > earlier_rsi:
		current_price = float(df.iloc[-1]["close"])
		return Pattern(
			pattern_type=PatternType.RSI_DIVERGENCE,
			name="RSI Bullish Divergence",
			detected_on=str(df.iloc[-1]["date"]),
			current_price=current_price,
			entry_price=round(current_price * 1.01, 2),
			stop_loss=round(recent_low * 0.98, 2),
			target_price=round(current_price * 1.06, 2),
			confidence=0.62,
			description="Price made a lower low while RSI made a higher low.",
			plain_english="Momentum improved even as price dipped, which can hint at a rebound.",
			key_levels={"recent_low": round(recent_low, 2), "earlier_low": round(earlier_low, 2)},
		)
	return None


def detect(df: pd.DataFrame) -> list[Pattern]:
	patterns: list[Pattern] = []
	if df.empty:
		return patterns

	current_price = float(df.iloc[-1]["close"])

	if "macd" in df.columns and "macd_signal" in df.columns:
		if _crossed_above_recent(df["macd"], df["macd_signal"], lookback=MACD_CROSS_LOOKBACK):
			patterns.append(
				Pattern(
					pattern_type=PatternType.MACD_CROSSOVER,
					name="MACD Bullish Crossover",
					detected_on=str(df.iloc[-1]["date"]),
					current_price=current_price,
					entry_price=round(current_price * 1.005, 2),
					stop_loss=round(current_price * 0.97, 2),
					target_price=round(current_price * 1.05, 2),
					confidence=0.58,
					description="MACD crossed above its signal line.",
					plain_english="Momentum shifted upward as the MACD line crossed its signal.",
					key_levels={},
				)
			)

	if "sma50" in df.columns and "sma200" in df.columns:
		if _crossed_above_recent(df["sma50"], df["sma200"], lookback=GOLDEN_CROSS_LOOKBACK):
			patterns.append(
				Pattern(
					pattern_type=PatternType.GOLDEN_CROSS,
					name="Golden Cross",
					detected_on=str(df.iloc[-1]["date"]),
					current_price=current_price,
					entry_price=round(current_price * 1.01, 2),
					stop_loss=round(current_price * 0.95, 2),
					target_price=round(current_price * 1.1, 2),
					confidence=0.66,
					description="50-day SMA crossed above 200-day SMA.",
					plain_english="The shorter-term trend rose above the long-term trend, a bullish sign.",
					key_levels={},
				)
			)

	divergence = _find_rsi_divergence(df)
	if divergence:
		patterns.append(divergence)

	return patterns
