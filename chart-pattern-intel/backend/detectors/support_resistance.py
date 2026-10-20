"""Detects support/resistance levels using pivot points."""

from __future__ import annotations

import pandas as pd

from config import SR_MAX_LEVELS, SR_MIN_TOUCHES, SR_SENSITIVITY
from models.pattern import SupportResistanceLevel


def _merge_levels(levels: list[SupportResistanceLevel], sensitivity: float) -> list[SupportResistanceLevel]:
	merged: list[SupportResistanceLevel] = []
	for level in sorted(levels, key=lambda item: item.price):
		if not merged:
			merged.append(level)
			continue
		last = merged[-1]
		if abs(level.price - last.price) / last.price <= sensitivity:
			total_touches = last.touches + level.touches
			weighted_price = (last.price * last.touches + level.price * level.touches) / total_touches
			merged[-1] = SupportResistanceLevel(
				level_type=last.level_type,
				price=round(weighted_price, 2),
				touches=total_touches,
				strength="strong" if total_touches >= 3 else "moderate" if total_touches == 2 else "weak",
				date_first_seen=min(last.date_first_seen, level.date_first_seen),
			)
		else:
			merged.append(level)
	return merged


def detect(df: pd.DataFrame) -> list[SupportResistanceLevel]:
	"""
	Finds S/R levels using pivot points.
	A level is valid if price touched it at least 2 times in the last 6 months.
	Returns levels sorted by strength (touch count).
	"""
	levels: list[SupportResistanceLevel] = []
	sensitivity = SR_SENSITIVITY

	for i in range(2, len(df) - 2):
		row = df.iloc[i]
		prev2_low, prev1_low = df.iloc[i - 2]["low"], df.iloc[i - 1]["low"]
		next1_low, next2_low = df.iloc[i + 1]["low"], df.iloc[i + 2]["low"]

		if row["low"] < prev1_low and row["low"] < prev2_low and row["low"] < next1_low and row["low"] < next2_low:
			level_price = float(row["low"])
			touches = int(((df["low"] - level_price).abs() / level_price < sensitivity).sum())
			if touches >= SR_MIN_TOUCHES:
				levels.append(
					SupportResistanceLevel(
						level_type="support",
						price=round(level_price, 2),
						touches=touches,
						strength="strong" if touches >= 3 else "moderate",
						date_first_seen=str(row["date"]),
					)
				)

		prev2_high, prev1_high = df.iloc[i - 2]["high"], df.iloc[i - 1]["high"]
		next1_high, next2_high = df.iloc[i + 1]["high"], df.iloc[i + 2]["high"]

		if row["high"] > prev1_high and row["high"] > prev2_high and row["high"] > next1_high and row["high"] > next2_high:
			level_price = float(row["high"])
			touches = int(((df["high"] - level_price).abs() / level_price < sensitivity).sum())
			if touches >= SR_MIN_TOUCHES:
				levels.append(
					SupportResistanceLevel(
						level_type="resistance",
						price=round(level_price, 2),
						touches=touches,
						strength="strong" if touches >= 3 else "moderate",
						date_first_seen=str(row["date"]),
					)
				)

	levels = _merge_levels(levels, sensitivity)
	levels = sorted(levels, key=lambda level: level.touches, reverse=True)
	return levels[:SR_MAX_LEVELS]
