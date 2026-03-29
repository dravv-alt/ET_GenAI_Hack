"""Chart API: returns OHLCV data for frontend charts."""

from fastapi import APIRouter, HTTPException, Query

from models.chart_data import ChartResponse, OHLCV
from services.data_fetcher import get_ohlcv

router = APIRouter()


@router.get("/chart/{ticker}", response_model=ChartResponse)
def get_chart(ticker: str, period: str = Query("6mo", pattern="^(6mo|1y|2y|5y)$")) -> ChartResponse:
	try:
		df = get_ohlcv(ticker, period=period)
	except ValueError as exc:
		raise HTTPException(status_code=404, detail=str(exc)) from exc

	ohlcv = [
		OHLCV(
			date=row["date"],
			open=float(row["open"]),
			high=float(row["high"]),
			low=float(row["low"]),
			close=float(row["close"]),
			volume=float(row["volume"]),
		)
		for _, row in df.iterrows()
	]

	return ChartResponse(ticker=df.attrs.get("ticker", ticker), period=period, ohlcv=ohlcv)
