"""Background precompute for scans and backtests."""

from __future__ import annotations

import asyncio
from typing import List

from backtester.engine import backtest_pattern
from config import (
	BACKTEST_PERIOD,
	PRECOMPUTE_ENABLED,
	PRECOMPUTE_INTERVAL_SECONDS,
	PRECOMPUTE_PATTERNS,
	PRECOMPUTE_UNIVERSE,
	RANK_CONFIDENCE_WEIGHT,
	RANK_RECENCY_WEIGHT,
)
from detectors.orchestrator import run_all
from services.cache_store import set_backtest_cache, set_scan_cache
from services.data_fetcher import get_ohlcv_with_indicators


def _rank_patterns(df, patterns: list) -> list:
	date_index = {str(row["date"]): idx for idx, row in df.iterrows()}
	max_index = max(date_index.values()) if date_index else 0

	def rank_score(pattern) -> float:
		pattern_index = date_index.get(pattern.detected_on, max_index)
		days_ago = max_index - pattern_index
		recency_score = 1.0 - (days_ago / max_index) if max_index > 0 else 1.0
		pattern.recency = round(recency_score, 3)
		score = (pattern.confidence * RANK_CONFIDENCE_WEIGHT) + (recency_score * RANK_RECENCY_WEIGHT)
		pattern.key_levels["rank_score"] = round(score, 3)
		return score

	return sorted(patterns, key=rank_score, reverse=True)


def _precompute_scan(market: str, tickers: List[str], period: str = "6mo") -> None:
	results = []
	for raw_ticker in tickers:
		try:
			df = get_ohlcv_with_indicators(raw_ticker, period=period, market=market)
		except ValueError:
			continue

		patterns, _ = run_all(df)
		if not patterns:
			continue
		patterns = _rank_patterns(df, patterns)
		best = patterns[0]
		results.append({
			"ticker": df.attrs.get("ticker", raw_ticker),
			"pattern": best.model_dump(),
			"rank_score": best.key_levels.get("rank_score"),
		})

	results.sort(key=lambda item: item.get("rank_score") or 0, reverse=True)
	payload = {
		"market": market,
		"mtf": False,
		"count": len(results),
		"results": results,
	}
	cache_key = (market, period, False, tuple(tickers))
	set_scan_cache(cache_key, payload)


def _precompute_backtests(market: str, tickers: List[str]) -> None:
	for raw_ticker in tickers:
		try:
			df = get_ohlcv_with_indicators(raw_ticker, period=BACKTEST_PERIOD, market=market)
		except ValueError:
			continue
		for pattern_type in PRECOMPUTE_PATTERNS:
			result = backtest_pattern(df.attrs.get("ticker", raw_ticker), pattern_type, df)
			cache_key = (market, df.attrs.get("ticker", raw_ticker), pattern_type, result.holding_period_days)
			set_backtest_cache(cache_key, result.model_dump())


def precompute_once() -> None:
	for market, tickers in PRECOMPUTE_UNIVERSE.items():
		if not tickers:
			continue
		_precompute_scan(market, tickers)
		_precompute_backtests(market, tickers)


async def _precompute_loop() -> None:
	await asyncio.sleep(1)
	while True:
		try:
			await asyncio.to_thread(precompute_once)
		except Exception as exc:
			print(f"Precompute failed: {exc}")
		await asyncio.sleep(PRECOMPUTE_INTERVAL_SECONDS)


def start_precompute_jobs() -> None:
	if not PRECOMPUTE_ENABLED:
		return
	asyncio.create_task(_precompute_loop())
