"""Detects breakout patterns with volume confirmation."""

from __future__ import annotations

import pandas as pd

from config import (
	BREAKOUT_CONFIDENCE_BASE,
	BREAKOUT_CONFIDENCE_SLOPE,
	BREAKOUT_MAX_EXTENSION_MULTIPLIER,
	BREAKOUT_MIN_CLOSE_MULTIPLIER,
	BREAKOUT_VOLUME_RATIO,
)
from models.pattern import Pattern, PatternType


def detect(df: pd.DataFrame, resistance_levels: list) -> list[Pattern]:
	"""
	A valid breakout requires:
	1. Price closes above resistance level
	2. Volume on breakout day > 1.5x 20-day average volume
	3. Breakout happened in the last 5 trading days
	"""
	patterns: list[Pattern] = []
	if df.empty:
		return patterns

	current_price = float(df.iloc[-1]["close"])
	recent_df = df.tail(5)
	ticker = df.attrs.get("ticker", "Stock")

	for level in resistance_levels:
		if level.level_type != "resistance":
			continue

		for _, row in recent_df.iterrows():
			if row["close"] <= level.price * BREAKOUT_MIN_CLOSE_MULTIPLIER:
				continue

			if current_price > level.price * BREAKOUT_MAX_EXTENSION_MULTIPLIER:
				continue

			volume_sma = float(df["volume_sma20"].iloc[-1]) if "volume_sma20" in df.columns else 0.0
			volume_ratio = float(row["volume"] / volume_sma) if volume_sma > 0 else 1.0
			if volume_ratio < BREAKOUT_VOLUME_RATIO:
				continue

			patterns.append(
				Pattern(
					pattern_type=PatternType.BREAKOUT,
					name="Volume Breakout",
					detected_on=str(row["date"]),
					current_price=current_price,
					entry_price=round(level.price * 1.01, 2),
					stop_loss=round(level.price * 0.98, 2),
					target_price=round(current_price * 1.08, 2),
					confidence=min(0.95, BREAKOUT_CONFIDENCE_BASE + (volume_ratio - BREAKOUT_VOLUME_RATIO) * BREAKOUT_CONFIDENCE_SLOPE),
					description=(
						f"Price broke above {level.price} resistance with {volume_ratio:.1f}x volume"
					),
					plain_english=(
						f"{ticker} moved above a key resistance level with unusually high volume, "
						"which often signals strong buying interest."
					),
					key_levels={
						"resistance_broken": round(level.price, 2),
						"volume_ratio": round(volume_ratio, 2),
						"extension_pct": round((current_price / level.price - 1) * 100, 2),
					},
				)
			)

	return patterns
