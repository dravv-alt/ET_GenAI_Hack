"""Backtest API: returns historical stats for a pattern."""

from fastapi import APIRouter, HTTPException, Query

from backtester.engine import backtest_pattern, backtest_pattern_debug
from config import BACKTEST_HOLDING_PERIOD_DAYS, BACKTEST_PERIOD
from services.data_fetcher import get_ohlcv_with_indicators

router = APIRouter()

SUPPORTED_PATTERNS = {
	"breakout",
	"macd_crossover",
	"golden_cross",
	"rsi_divergence",
	"hammer",
	"engulfing",
	"double_bottom",
	"double_top",
	"head_shoulders",
}


@router.get("/backtest/{ticker}/{pattern_type}")
def get_backtest(
	ticker: str,
	pattern_type: str,
	holding_period: int = Query(BACKTEST_HOLDING_PERIOD_DAYS, ge=5, le=60),
	debug: bool = Query(False),
) -> dict:
	pattern_type = pattern_type.lower()
	if pattern_type not in SUPPORTED_PATTERNS:
		raise HTTPException(status_code=400, detail=f"Unsupported pattern type: {pattern_type}")

	try:
		df = get_ohlcv_with_indicators(ticker, period=BACKTEST_PERIOD)
	except ValueError as exc:
		raise HTTPException(status_code=404, detail=str(exc)) from exc

	if debug:
		result, evaluations = backtest_pattern_debug(
			df.attrs.get("ticker", ticker),
			pattern_type,
			df,
			holding_period_days=holding_period,
		)
		return {"result": result.model_dump(), "evaluations": evaluations}

	result = backtest_pattern(df.attrs.get("ticker", ticker), pattern_type, df, holding_period_days=holding_period)
	return result.model_dump()
