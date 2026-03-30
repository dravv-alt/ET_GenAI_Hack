"""Runs all detectors and merges results into a pattern report."""

from __future__ import annotations

import pandas as pd

from detectors import breakout_detector, candlestick_detector, momentum_detector, reversal_detector, support_resistance


def _indicator_contributions(df: pd.DataFrame) -> list[dict]:
	contribs: list[dict] = []
	if df.empty:
		return contribs

	last = df.iloc[-1]
	if "rsi" in df.columns:
		rsi = float(last["rsi"])
		if rsi <= 30:
			contribs.append({"feature": "RSI oversold", "score": 8})
		elif rsi >= 70:
			contribs.append({"feature": "RSI overbought", "score": -8})

	if "macd_hist" in df.columns:
		macd_hist = float(last["macd_hist"])
		contribs.append({"feature": "MACD momentum", "score": 6 if macd_hist > 0 else -6})

	if "sma50" in df.columns and "sma200" in df.columns:
		trend = float(last["sma50"]) - float(last["sma200"])
		contribs.append({"feature": "Trend (50>200)", "score": 5 if trend > 0 else -5})

	if "sma20" in df.columns:
		trend = float(last["close"]) - float(last["sma20"])
		contribs.append({"feature": "Price vs SMA20", "score": 3 if trend > 0 else -3})

	return contribs


def _pattern_contributions(patterns: list) -> list[dict]:
	contribs: list[dict] = []
	for pattern in patterns:
		score = round(float(pattern.confidence) * 100, 2)
		contribs.append({"feature": pattern.pattern_type.replace("_", " "), "score": score})
	return contribs


def build_ensemble(patterns: list, df: pd.DataFrame) -> dict:
	pattern_contribs = _pattern_contributions(patterns)
	indicator_contribs = _indicator_contributions(df)
	pattern_score = sum(item["score"] for item in pattern_contribs) / max(len(pattern_contribs), 1)
	indicator_score = sum(item["score"] for item in indicator_contribs)
	total = max(min(pattern_score + indicator_score, 100), -100)
	return {
		"score": round(total, 2),
		"direction": "bullish" if total >= 0 else "bearish",
		"pattern_factors": pattern_contribs,
		"indicator_factors": indicator_contribs,
	}


def run_all(df: pd.DataFrame) -> tuple[list, list]:
	levels = support_resistance.detect(df)
	patterns = []
	patterns.extend(breakout_detector.detect(df, levels))
	patterns.extend(momentum_detector.detect(df))
	patterns.extend(reversal_detector.detect(df))
	patterns.extend(candlestick_detector.detect(df))
	return patterns, levels
