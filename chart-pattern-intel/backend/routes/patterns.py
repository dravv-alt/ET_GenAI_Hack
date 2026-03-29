"""Patterns API: returns detected patterns and S/R levels."""

from fastapi import APIRouter, HTTPException

from detectors.orchestrator import run_all
from config import RANK_CONFIDENCE_WEIGHT, RANK_RECENCY_WEIGHT
from services.data_fetcher import get_ohlcv_with_indicators

router = APIRouter()


@router.get("/patterns/{ticker}")
def get_patterns(ticker: str) -> dict:
	try:
		df = get_ohlcv_with_indicators(ticker, period="6mo")
	except ValueError as exc:
		raise HTTPException(status_code=404, detail=str(exc)) from exc

	patterns, levels = run_all(df)
	date_index = {str(row["date"]): idx for idx, row in df.iterrows()}
	max_index = max(date_index.values()) if date_index else 0

	def rank_score(pattern) -> float:
		pattern_index = date_index.get(pattern.detected_on, max_index)
		days_ago = max_index - pattern_index
		recency_score = 1.0 - (days_ago / max_index) if max_index > 0 else 1.0
		score = (pattern.confidence * RANK_CONFIDENCE_WEIGHT) + (recency_score * RANK_RECENCY_WEIGHT)
		pattern.key_levels["rank_score"] = round(score, 3)
		return score

	patterns.sort(key=rank_score, reverse=True)
	return {
		"ticker": df.attrs.get("ticker", ticker),
		"patterns": patterns,
		"levels": levels,
	}
