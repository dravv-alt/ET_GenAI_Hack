"""Backtest engine for pattern outcomes on historical data."""

from __future__ import annotations

from typing import Dict, List, Tuple

import pandas as pd

from backtester.stats import compute_backtest_stats
from config import (
	BACKTEST_ENTRY_MODE,
	BACKTEST_HOLDING_PERIOD_DAYS,
	BACKTEST_MIN_SAMPLES,
	BACKTEST_MIN_SAMPLES_WARNING,
	BACKTEST_PERIOD,
	BACKTEST_SUCCESS_MODE,
	BREAKOUT_CONFIRM_PCT,
	BREAKOUT_LOOKBACK_DAYS,
	BREAKOUT_MAX_EXTENSION_PCT,
	BREAKOUT_MIN_VOLUME_RATIO,
	DEFAULT_STOP_LOSS_PCT,
	DEFAULT_TARGET_PCT,
	DOUBLE_BOTTOM_MAX_GAP,
	DOUBLE_BOTTOM_MIN_GAP,
	DOUBLE_BOTTOM_PEAK_TOLERANCE_PCT,
	DOUBLE_BOTTOM_REBOUND_PCT,
	DOUBLE_BOTTOM_NECKLINE_CONFIRM_PCT,
	DOUBLE_BOTTOM_WINDOW,
	DOUBLE_TOP_MAX_GAP,
	DOUBLE_TOP_MIN_GAP,
	DOUBLE_TOP_TROUGH_TOLERANCE_PCT,
	DOUBLE_TOP_PULLBACK_PCT,
	DOUBLE_TOP_NECKLINE_CONFIRM_PCT,
	DOUBLE_TOP_WINDOW,
	ENGULFING_LOOKBACK_DOWNTREND,
	GOLDEN_CROSS_RECENT_LOOKBACK,
	HAMMER_LOOKBACK_DOWNTREND,
	HEAD_SHOULDERS_MAX_GAP,
	HEAD_SHOULDERS_MIN_GAP,
	HEAD_SHOULDERS_MIN_SHOULDER_DISTANCE,
	HEAD_SHOULDERS_HEAD_PROMINENCE_PCT,
	HEAD_SHOULDERS_NECKLINE_MULTIPLIER,
	HEAD_SHOULDERS_SHOULDER_TOLERANCE_PCT,
	HEAD_SHOULDERS_NECKLINE_BREAK_PCT,
	HEAD_SHOULDERS_WINDOW,
	MACD_RECENT_LOOKBACK,
	RSI_DIVERGENCE_LOOKBACK,
)
from models.pattern import BacktestResult


def _find_local_lows(series: pd.Series, left: int = 2, right: int = 2) -> List[int]:
	indices: List[int] = []
	for i in range(left, len(series) - right):
		window = series.iloc[i - left:i + right + 1]
		if series.iloc[i] == window.min():
			indices.append(i)
	return indices


def _find_local_highs(series: pd.Series, left: int = 2, right: int = 2) -> List[int]:
	indices: List[int] = []
	for i in range(left, len(series) - right):
		window = series.iloc[i - left:i + right + 1]
		if series.iloc[i] == window.max():
			indices.append(i)
	return indices


def _find_breakout_occurrences(df: pd.DataFrame) -> List[int]:
	prior_resistance = df["high"].rolling(BREAKOUT_LOOKBACK_DAYS).max().shift(1)
	volume_avg = df["volume"].rolling(20).mean().shift(1)
	occurrences: List[int] = []
	for i in range(BREAKOUT_LOOKBACK_DAYS, len(df)):
		if pd.isna(prior_resistance.iloc[i]) or pd.isna(volume_avg.iloc[i]):
			continue
		price = df["close"].iloc[i]
		if price <= prior_resistance.iloc[i] * (1 + BREAKOUT_CONFIRM_PCT):
			continue
		if df["volume"].iloc[i] <= volume_avg.iloc[i] * BREAKOUT_MIN_VOLUME_RATIO:
			continue
		extension = (price - prior_resistance.iloc[i]) / prior_resistance.iloc[i]
		if extension > BREAKOUT_MAX_EXTENSION_PCT:
			continue
		occurrences.append(i)
	return occurrences


def _find_macd_occurrences(df: pd.DataFrame) -> List[int]:
	if "macd" not in df.columns or "macd_signal" not in df.columns:
		return []
	occurrences: List[int] = []
	for i in range(1, len(df)):
		if df["macd"].iloc[i - 1] <= df["macd_signal"].iloc[i - 1] and df["macd"].iloc[i] > df["macd_signal"].iloc[i]:
			occurrences.append(i)
	return occurrences


def _find_golden_cross_occurrences(df: pd.DataFrame) -> List[int]:
	if "sma50" not in df.columns or "sma200" not in df.columns:
		return []
	occurrences: List[int] = []
	for i in range(1, len(df)):
		if df["sma50"].iloc[i - 1] <= df["sma200"].iloc[i - 1] and df["sma50"].iloc[i] > df["sma200"].iloc[i]:
			occurrences.append(i)
	return occurrences


def _find_rsi_divergence_occurrences(df: pd.DataFrame) -> List[int]:
	if "rsi" not in df.columns:
		return []
	occurrences: List[int] = []
	for i in range(RSI_DIVERGENCE_LOOKBACK * 2, len(df)):
		window = df.iloc[i - RSI_DIVERGENCE_LOOKBACK * 2:i]
		low_indices = _find_local_lows(window["low"])
		if len(low_indices) < 2:
			continue
		first_idx = low_indices[-2]
		second_idx = low_indices[-1]
		first_price = float(window["low"].iloc[first_idx])
		second_price = float(window["low"].iloc[second_idx])
		first_rsi = float(window["rsi"].iloc[first_idx])
		second_rsi = float(window["rsi"].iloc[second_idx])
		if second_price < first_price and second_rsi > first_rsi:
			occurrences.append(i - RSI_DIVERGENCE_LOOKBACK * 2 + second_idx)
	return occurrences


def _is_downtrend(closes: pd.Series, lookback: int) -> bool:
	if len(closes) < lookback + 1:
		return False
	return closes.iloc[-1] < closes.iloc[-1 - lookback]


def _find_hammer_occurrences(df: pd.DataFrame) -> List[int]:
	occurrences: List[int] = []
	for i in range(1, len(df)):
		row = df.iloc[i]
		body = abs(row["close"] - row["open"])
		range_ = row["high"] - row["low"]
		if range_ == 0:
			continue
		lower_wick = min(row["open"], row["close"]) - row["low"]
		upper_wick = row["high"] - max(row["open"], row["close"])
		is_hammer = lower_wick >= body * 2 and upper_wick <= body and body / range_ <= 0.4
		if not is_hammer:
			continue
		if not _is_downtrend(df["close"].iloc[:i], HAMMER_LOOKBACK_DOWNTREND):
			continue
		occurrences.append(i)
	return occurrences


def _find_engulfing_occurrences(df: pd.DataFrame) -> List[int]:
	occurrences: List[int] = []
	for i in range(1, len(df)):
		prev = df.iloc[i - 1]
		curr = df.iloc[i]
		prev_bear = prev["close"] < prev["open"]
		curr_bull = curr["close"] > curr["open"]
		engulf = curr["open"] <= prev["close"] and curr["close"] >= prev["open"]
		if not (prev_bear and curr_bull and engulf):
			continue
		if not _is_downtrend(df["close"].iloc[:i], ENGULFING_LOOKBACK_DOWNTREND):
			continue
		occurrences.append(i)
	return occurrences


def _find_double_bottom_occurrences(df: pd.DataFrame) -> List[int]:
	occurrences: List[int] = []
	for i in range(DOUBLE_BOTTOM_WINDOW, len(df)):
		window = df.iloc[i - DOUBLE_BOTTOM_WINDOW:i]
		low_indices = _find_local_lows(window["low"])
		if len(low_indices) < 2:
			continue
		first_idx = low_indices[-2]
		second_idx = low_indices[-1]
		if second_idx - first_idx < DOUBLE_BOTTOM_MIN_GAP or second_idx - first_idx > DOUBLE_BOTTOM_MAX_GAP:
			continue
		first_low = float(window["low"].iloc[first_idx])
		second_low = float(window["low"].iloc[second_idx])
		if abs(second_low - first_low) / first_low > DOUBLE_BOTTOM_PEAK_TOLERANCE_PCT:
			continue
		mid_high = float(window["high"].iloc[first_idx:second_idx + 1].max())
		rebound_pct = (mid_high - first_low) / first_low if first_low else 0
		if rebound_pct < DOUBLE_BOTTOM_REBOUND_PCT:
			continue
		neckline_break = float(df.iloc[i]["close"]) >= mid_high * (1 + DOUBLE_BOTTOM_NECKLINE_CONFIRM_PCT)
		if not neckline_break:
			continue
		occurrences.append(i)
	return occurrences


def _find_double_top_occurrences(df: pd.DataFrame) -> List[int]:
	occurrences: List[int] = []
	for i in range(DOUBLE_TOP_WINDOW, len(df)):
		window = df.iloc[i - DOUBLE_TOP_WINDOW:i]
		high_indices = _find_local_highs(window["high"])
		if len(high_indices) < 2:
			continue
		first_idx = high_indices[-2]
		second_idx = high_indices[-1]
		if second_idx - first_idx < DOUBLE_TOP_MIN_GAP or second_idx - first_idx > DOUBLE_TOP_MAX_GAP:
			continue
		first_high = float(window["high"].iloc[first_idx])
		second_high = float(window["high"].iloc[second_idx])
		if abs(second_high - first_high) / first_high > DOUBLE_TOP_TROUGH_TOLERANCE_PCT:
			continue
		mid_low = float(window["low"].iloc[first_idx:second_idx + 1].min())
		pullback_pct = (first_high - mid_low) / first_high if first_high else 0
		if pullback_pct < DOUBLE_TOP_PULLBACK_PCT:
			continue
		neckline_break = float(df.iloc[i]["close"]) <= mid_low * (1 - DOUBLE_TOP_NECKLINE_CONFIRM_PCT)
		if not neckline_break:
			continue
		occurrences.append(i)
	return occurrences


def _find_head_shoulders_occurrences(df: pd.DataFrame) -> List[int]:
	occurrences: List[int] = []
	for i in range(HEAD_SHOULDERS_WINDOW, len(df)):
		window = df.iloc[i - HEAD_SHOULDERS_WINDOW:i]
		high_indices = _find_local_highs(window["high"])
		if len(high_indices) < 3:
			continue
		left_idx = high_indices[-3]
		head_idx = high_indices[-2]
		right_idx = high_indices[-1]
		if right_idx - left_idx < HEAD_SHOULDERS_MIN_SHOULDER_DISTANCE:
			continue
		if head_idx - left_idx < HEAD_SHOULDERS_MIN_GAP or right_idx - head_idx < HEAD_SHOULDERS_MIN_GAP:
			continue
		if head_idx - left_idx > HEAD_SHOULDERS_MAX_GAP or right_idx - head_idx > HEAD_SHOULDERS_MAX_GAP:
			continue
		left_high = float(window["high"].iloc[left_idx])
		head_high = float(window["high"].iloc[head_idx])
		right_high = float(window["high"].iloc[right_idx])
		if head_high <= left_high or head_high <= right_high:
			continue
		shoulder_peak = max(left_high, right_high)
		if head_high < shoulder_peak * (1 + HEAD_SHOULDERS_HEAD_PROMINENCE_PCT):
			continue
		if abs(left_high - right_high) / left_high > HEAD_SHOULDERS_SHOULDER_TOLERANCE_PCT:
			continue
		left_low = float(window["low"].iloc[left_idx:head_idx + 1].min())
		right_low = float(window["low"].iloc[head_idx:right_idx + 1].min())
		neckline = (left_low + right_low) / 2
		if float(df.iloc[i]["close"]) <= neckline * (1 - HEAD_SHOULDERS_NECKLINE_BREAK_PCT):
			occurrences.append(i)
	return occurrences


def find_historical_occurrences(df: pd.DataFrame, pattern_type: str) -> List[int]:
	pattern_type = pattern_type.lower()
	if pattern_type == "breakout":
		return _find_breakout_occurrences(df)
	if pattern_type == "macd_crossover":
		return _find_macd_occurrences(df)
	if pattern_type == "golden_cross":
		return _find_golden_cross_occurrences(df)
	if pattern_type == "rsi_divergence":
		return _find_rsi_divergence_occurrences(df)
	if pattern_type == "hammer":
		return _find_hammer_occurrences(df)
	if pattern_type == "engulfing":
		return _find_engulfing_occurrences(df)
	if pattern_type == "double_bottom":
		return _find_double_bottom_occurrences(df)
	if pattern_type == "double_top":
		return _find_double_top_occurrences(df)
	if pattern_type == "head_shoulders":
		return _find_head_shoulders_occurrences(df)
	return []


def _directional_multiplier(pattern_type: str) -> int:
	return -1 if pattern_type in {"double_top", "head_shoulders"} else 1


def _get_backtest_levels(entry_price: float, signal_row: pd.Series, pattern_type: str) -> Tuple[float, float]:
	if pattern_type in {"breakout", "macd_crossover", "golden_cross", "rsi_divergence"}:
		stop = entry_price * (1 - DEFAULT_STOP_LOSS_PCT)
		target = entry_price * (1 + DEFAULT_TARGET_PCT)
		return stop, target
	if pattern_type in {"hammer", "engulfing", "double_bottom"}:
		stop = float(signal_row["low"])
		target = entry_price + 2 * (entry_price - stop)
		return stop, target
	if pattern_type in {"double_top", "head_shoulders"}:
		stop = entry_price * (1 + DEFAULT_STOP_LOSS_PCT)
		target = entry_price * (1 - DEFAULT_TARGET_PCT)
		return stop, target
	stop = entry_price * (1 - DEFAULT_STOP_LOSS_PCT)
	target = entry_price * (1 + DEFAULT_TARGET_PCT)
	return stop, target


def evaluate_occurrence(
	df: pd.DataFrame,
	signal_idx: int,
	pattern_type: str,
	holding_period_days: int,
) -> Dict[str, float] | None:
	entry_idx = signal_idx + 1
	if entry_idx >= len(df):
		return None
	entry_price = float(df.iloc[entry_idx]["open"]) if BACKTEST_ENTRY_MODE == "next_open" else float(df.iloc[signal_idx]["close"])
	stop_loss, target_price = _get_backtest_levels(entry_price, df.iloc[signal_idx], pattern_type)

	end_idx = min(len(df) - 1, entry_idx + holding_period_days)
	segment = df.iloc[entry_idx:end_idx + 1]
	if segment.empty:
		return None

	success = None
	for _, row in segment.iterrows():
		if pattern_type in {"double_top", "head_shoulders"}:
			if row["low"] <= target_price:
				success = True
				break
			if row["high"] >= stop_loss:
				success = False
				break
		else:
			if row["high"] >= target_price:
				success = True
				break
			if row["low"] <= stop_loss:
				success = False
				break

	exit_price = float(segment.iloc[-1]["close"])
	raw_return = (exit_price - entry_price) / entry_price * 100
	directional_return = raw_return * _directional_multiplier(pattern_type)
	if success is None:
		success = directional_return > 0

	return {
		"signal_idx": float(signal_idx),
		"entry_idx": float(entry_idx),
		"exit_idx": float(end_idx),
		"entry_price": entry_price,
		"exit_price": exit_price,
		"return_pct": raw_return,
		"directional_return_pct": directional_return,
		"success": 1.0 if success else 0.0,
	}


def _build_insufficient_result(
	ticker: str,
	pattern_type: str,
	sample_count: int,
	holding_period_days: int,
) -> BacktestResult:
	return BacktestResult(
		pattern_type=pattern_type,
		ticker=ticker,
		sample_count=sample_count,
		win_rate=None,
		avg_gain_pct=None,
		avg_loss_pct=None,
		rr_ratio=None,
		median_return_pct=None,
		holding_period_days=holding_period_days,
		entry_mode=BACKTEST_ENTRY_MODE,
		success_mode=BACKTEST_SUCCESS_MODE,
		note="Insufficient historical data - fewer than 3 occurrences found",
	)


def _run_backtest(
	ticker: str,
	pattern_type: str,
	df_5yr: pd.DataFrame,
	holding_period_days: int,
) -> Tuple[BacktestResult, List[Dict[str, float]]]:
	occurrences = find_historical_occurrences(df_5yr, pattern_type)
	if len(occurrences) < BACKTEST_MIN_SAMPLES_WARNING:
		return _build_insufficient_result(ticker, pattern_type, len(occurrences), holding_period_days), []

	evaluations: List[Dict[str, float]] = []
	for idx in occurrences:
		result = evaluate_occurrence(df_5yr, idx, pattern_type, holding_period_days)
		if result is not None:
			evaluations.append(result)

	sample_count = len(evaluations)
	if sample_count < BACKTEST_MIN_SAMPLES_WARNING:
		return _build_insufficient_result(ticker, pattern_type, sample_count, holding_period_days), evaluations

	outcomes = [e["directional_return_pct"] for e in evaluations]
	stats = compute_backtest_stats(outcomes)

	note = f"Based on {sample_count} historical occurrences over {BACKTEST_PERIOD}"
	if sample_count < BACKTEST_MIN_SAMPLES:
		note += " - low sample size, interpret cautiously"

	result = BacktestResult(
		pattern_type=pattern_type,
		ticker=ticker,
		sample_count=stats["sample_count"],
		win_rate=stats["win_rate"],
		avg_gain_pct=stats["avg_gain_pct"],
		avg_loss_pct=stats["avg_loss_pct"],
		rr_ratio=stats["rr_ratio"],
		median_return_pct=stats["median_return_pct"],
		holding_period_days=holding_period_days,
		entry_mode=BACKTEST_ENTRY_MODE,
		success_mode=BACKTEST_SUCCESS_MODE,
		note=note,
	)
	return result, evaluations


def backtest_pattern(
	ticker: str,
	pattern_type: str,
	df_5yr: pd.DataFrame,
	holding_period_days: int = BACKTEST_HOLDING_PERIOD_DAYS,
) -> BacktestResult:
	result, _ = _run_backtest(ticker, pattern_type, df_5yr, holding_period_days)
	return result


def backtest_pattern_debug(
	ticker: str,
	pattern_type: str,
	df_5yr: pd.DataFrame,
	holding_period_days: int = BACKTEST_HOLDING_PERIOD_DAYS,
) -> Tuple[BacktestResult, List[Dict[str, float]]]:
	return _run_backtest(ticker, pattern_type, df_5yr, holding_period_days)
