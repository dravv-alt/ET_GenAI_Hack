"""Scan a list of tickers for top patterns."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter
from pydantic import BaseModel, Field

from config import MTF_INTERVALS, RANK_CONFIDENCE_WEIGHT, RANK_RECENCY_WEIGHT
from detectors.orchestrator import run_all
from services.cache_store import get_scan_cache, set_scan_cache
from services.data_fetcher import get_ohlcv_with_indicators

router = APIRouter()


class ScanRequest(BaseModel):
	tickers: List[str]
	period: str = "6mo"
	limit: int = Field(20, ge=1, le=200)
	market: str = "NSE"
	mtf: bool = False


@router.post("/scan")
def scan_universe(payload: ScanRequest) -> dict:
	cache_key = (payload.market, payload.period, payload.mtf, tuple(payload.tickers))
	cached = get_scan_cache(cache_key)
	if cached is not None:
		return cached

	results = []
	for raw_ticker in payload.tickers:
		try:
			df = get_ohlcv_with_indicators(raw_ticker, period=payload.period, market=payload.market)
		except ValueError:
			continue

		patterns, _ = run_all(df)
		if not patterns:
			continue

		if payload.mtf:
			confirmed_types = None
			for frame, cfg in MTF_INTERVALS.items():
				if frame == "1d":
					continue
				try:
					frame_df = get_ohlcv_with_indicators(
						raw_ticker,
						period=cfg["period"],
						market=payload.market,
						interval=cfg["interval"],
					)
				except ValueError:
					frame_df = None
				if frame_df is None or frame_df.empty:
					continue
				frame_patterns, _ = run_all(frame_df)
				frame_types = {p.pattern_type for p in frame_patterns}
				confirmed_types = frame_types if confirmed_types is None else confirmed_types.intersection(frame_types)
			if confirmed_types is None:
				confirmed_types = set()
			patterns = [p for p in patterns if p.pattern_type in confirmed_types]
			if not patterns:
				continue

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

		patterns.sort(key=rank_score, reverse=True)
		best = patterns[0]
		results.append({
			"ticker": df.attrs.get("ticker", raw_ticker),
			"pattern": best.model_dump(),
			"rank_score": best.key_levels.get("rank_score"),
		})

	results.sort(key=lambda item: item.get("rank_score") or 0, reverse=True)
	response = {
		"market": payload.market,
		"mtf": payload.mtf,
		"count": len(results),
		"results": results[:payload.limit],
	}
	set_scan_cache(cache_key, response)
	return response
