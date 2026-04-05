"""Patterns API: returns detected patterns and S/R levels."""

from fastapi import APIRouter, HTTPException, Query

from detectors.orchestrator import build_ensemble, run_all
from config import MTF_INTERVALS, RANK_CONFIDENCE_WEIGHT, RANK_RECENCY_WEIGHT
from services.data_fetcher import get_ohlcv_with_indicators

router = APIRouter()


@router.get("/patterns/{ticker}")
def get_patterns(
	ticker: str,
	period: str = Query("1y"),
	market: str = Query("NSE"),
	mtf: bool = Query(False),
) -> dict:
	try:
		df = get_ohlcv_with_indicators(ticker, period=period, market=market)
	except ValueError as exc:
		raise HTTPException(status_code=404, detail=str(exc)) from exc

	patterns, levels = run_all(df)
	mtf_summary = None
	if mtf and patterns:
		confirmed_types = None
		for frame, cfg in MTF_INTERVALS.items():
			if frame == "1d":
				continue
			try:
				frame_df = get_ohlcv_with_indicators(
					ticker,
					period=cfg["period"],
					market=market,
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
		filtered = []
		for pattern in patterns:
			if pattern.pattern_type in confirmed_types:
				pattern.key_levels["mtf_confirmed"] = 1.0
				filtered.append(pattern)
		patterns = filtered
		mtf_summary = {
			"enabled": True,
			"confirmed_types": sorted(list(confirmed_types)),
			"count": len(patterns),
		}
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
	ensemble = build_ensemble(patterns, df) if patterns else {
		"score": 0,
		"direction": "neutral",
		"pattern_factors": [],
		"indicator_factors": [],
	}
	return {
		"ticker": df.attrs.get("ticker", ticker),
		"patterns": patterns,
		"levels": levels,
		"ensemble": ensemble,
		"mtf": mtf_summary,
	}
