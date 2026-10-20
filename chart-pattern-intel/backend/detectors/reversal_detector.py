"""Detects reversal patterns like double tops/bottoms."""

from __future__ import annotations

import pandas as pd

from config import (
	DOUBLE_BOTTOM_CONFIRM_MULTIPLIER,
	DOUBLE_BOTTOM_MAX_GAP,
	DOUBLE_BOTTOM_MIN_GAP,
	DOUBLE_BOTTOM_TOLERANCE,
	DOUBLE_BOTTOM_WINDOW,
	DOUBLE_TOP_CONFIRM_MULTIPLIER,
	DOUBLE_TOP_MAX_GAP,
	DOUBLE_TOP_MIN_GAP,
	DOUBLE_TOP_TOLERANCE,
	DOUBLE_TOP_WINDOW,
	HEAD_SHOULDERS_MAX_GAP,
	HEAD_SHOULDERS_MIN_GAP,
	HEAD_SHOULDERS_NECKLINE_MULTIPLIER,
	HEAD_SHOULDERS_TOLERANCE,
	HEAD_SHOULDERS_WINDOW,
)
from models.pattern import Pattern, PatternType


def _find_double_bottom(df: pd.DataFrame) -> Pattern | None:
	if len(df) < DOUBLE_BOTTOM_WINDOW:
		return None

	window = df.tail(DOUBLE_BOTTOM_WINDOW).reset_index(drop=True)
	lows = window["low"]
	first_idx = int(lows.idxmin())
	first_low = float(lows.iloc[first_idx])

	search_start = max(0, first_idx + DOUBLE_BOTTOM_MIN_GAP)
	search_end = min(len(window), first_idx + DOUBLE_BOTTOM_MAX_GAP)
	if search_end - search_start < 5:
		return None

	second_segment = window.iloc[search_start:search_end]
	second_idx_local = int(second_segment["low"].idxmin())
	second_low = float(window.loc[second_idx_local, "low"])

	if abs(second_low - first_low) / first_low > DOUBLE_BOTTOM_TOLERANCE:
		return None

	midpoint = float(window.loc[first_idx:second_idx_local, "high"].max())
	current_price = float(df.iloc[-1]["close"])
	if current_price < midpoint * DOUBLE_BOTTOM_CONFIRM_MULTIPLIER:
		return None

	return Pattern(
		pattern_type=PatternType.DOUBLE_BOTTOM,
		name="Double Bottom",
		detected_on=str(df.iloc[-1]["date"]),
		current_price=current_price,
		entry_price=round(midpoint * 1.01, 2),
		stop_loss=round(min(first_low, second_low) * 0.97, 2),
		target_price=round(current_price * 1.08, 2),
		confidence=0.6,
		description="Two similar lows formed with a recovery above the midpoint.",
		plain_english="Price tested a low twice and then pushed above the middle level, suggesting buyers returned.",
		key_levels={"first_low": round(first_low, 2), "second_low": round(second_low, 2)},
	)


def _find_double_top(df: pd.DataFrame) -> Pattern | None:
	if len(df) < DOUBLE_TOP_WINDOW:
		return None

	window = df.tail(DOUBLE_TOP_WINDOW).reset_index(drop=True)
	highs = window["high"]
	first_idx = int(highs.idxmax())
	first_high = float(highs.iloc[first_idx])

	search_start = max(0, first_idx + DOUBLE_TOP_MIN_GAP)
	search_end = min(len(window), first_idx + DOUBLE_TOP_MAX_GAP)
	if search_end - search_start < 5:
		return None

	second_segment = window.iloc[search_start:search_end]
	second_idx_local = int(second_segment["high"].idxmax())
	second_high = float(window.loc[second_idx_local, "high"])

	if abs(second_high - first_high) / first_high > DOUBLE_TOP_TOLERANCE:
		return None

	midpoint = float(window.loc[first_idx:second_idx_local, "low"].min())
	current_price = float(df.iloc[-1]["close"])
	if current_price > midpoint * DOUBLE_TOP_CONFIRM_MULTIPLIER:
		return None

	return Pattern(
		pattern_type=PatternType.DOUBLE_TOP,
		name="Double Top",
		detected_on=str(df.iloc[-1]["date"]),
		current_price=current_price,
		entry_price=round(midpoint * 0.99, 2),
		stop_loss=round(max(first_high, second_high) * 1.02, 2),
		target_price=round(current_price * 0.92, 2),
		confidence=0.6,
		description="Two similar highs formed with a drop below the midpoint.",
		plain_english="Price failed twice near the same high and slipped below the middle zone, hinting at weakening demand.",
		key_levels={"first_high": round(first_high, 2), "second_high": round(second_high, 2)},
	)


def _find_head_shoulders(df: pd.DataFrame) -> Pattern | None:
	if len(df) < HEAD_SHOULDERS_WINDOW:
		return None

	window = df.tail(HEAD_SHOULDERS_WINDOW).reset_index(drop=True)
	highs = window["high"]
	peak_idx = int(highs.idxmax())
	peak_high = float(highs.iloc[peak_idx])

	left_start = max(0, peak_idx - HEAD_SHOULDERS_MAX_GAP)
	left_end = max(0, peak_idx - HEAD_SHOULDERS_MIN_GAP)
	right_start = min(len(window) - 1, peak_idx + HEAD_SHOULDERS_MIN_GAP)
	right_end = min(len(window), peak_idx + HEAD_SHOULDERS_MAX_GAP)
	if left_end - left_start < 3 or right_end - right_start < 3:
		return None

	left_segment = window.iloc[left_start:left_end]
	right_segment = window.iloc[right_start:right_end]
	left_idx = int(left_segment["high"].idxmax())
	right_idx = int(right_segment["high"].idxmax())
	left_high = float(window.loc[left_idx, "high"])
	right_high = float(window.loc[right_idx, "high"])

	if left_high >= peak_high or right_high >= peak_high:
		return None
	if abs(left_high - right_high) / left_high > HEAD_SHOULDERS_TOLERANCE:
		return None

	left_low = float(window.loc[left_idx:peak_idx, "low"].min())
	right_low = float(window.loc[peak_idx:right_idx, "low"].min())
	neckline = (left_low + right_low) / 2
	current_price = float(df.iloc[-1]["close"])
	if current_price > neckline * HEAD_SHOULDERS_NECKLINE_MULTIPLIER:
		return None

	return Pattern(
		pattern_type=PatternType.HEAD_SHOULDERS,
		name="Head and Shoulders",
		detected_on=str(df.iloc[-1]["date"]),
		current_price=current_price,
		entry_price=round(neckline * 0.99, 2),
		stop_loss=round(peak_high * 1.02, 2),
		target_price=round(current_price * 0.9, 2),
		confidence=0.58,
		description="A higher peak between two similar highs with a break below the neckline.",
		plain_english="Price formed a peak higher than the surrounding highs and then slipped below the neckline, often a bearish reversal cue.",
		key_levels={"left_high": round(left_high, 2), "head_high": round(peak_high, 2), "right_high": round(right_high, 2)},
	)


def detect(df: pd.DataFrame) -> list[Pattern]:
	patterns: list[Pattern] = []
	if df.empty:
		return patterns

	double_bottom = _find_double_bottom(df)
	if double_bottom:
		patterns.append(double_bottom)

	double_top = _find_double_top(df)
	if double_top:
		patterns.append(double_top)

	head_shoulders = _find_head_shoulders(df)
	if head_shoulders:
		patterns.append(head_shoulders)

	return patterns
