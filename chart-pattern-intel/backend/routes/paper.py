"""Paper trading endpoints."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.data_fetcher import get_ohlcv
from services.paper_trading import PORTFOLIO

router = APIRouter()


class PaperTradeRequest(BaseModel):
	symbol: str
	market: str = "NSE"
	side: str = Field("buy", pattern="^(buy|sell)$")
	quantity: float = Field(..., gt=0)
	price: Optional[float] = None
	period: str = "6mo"


class PaperResetRequest(BaseModel):
	starting_cash: float = Field(100000.0, gt=0)


@router.post("/paper/reset")
def reset_portfolio(payload: PaperResetRequest) -> dict:
	PORTFOLIO.reset(payload.starting_cash)
	return {"status": "ok", "starting_cash": payload.starting_cash}


@router.post("/paper/trade")
def paper_trade(payload: PaperTradeRequest) -> dict:
	symbol = payload.symbol.strip().upper()
	market = payload.market.strip().upper()
	price = payload.price

	if price is None:
		try:
			df = get_ohlcv(symbol, period=payload.period, market=market)
		except ValueError as exc:
			raise HTTPException(status_code=404, detail=str(exc)) from exc
		if df.empty:
			raise HTTPException(status_code=404, detail="No price data for trade")
		price = float(df.iloc[-1]["close"])

	try:
		entry = PORTFOLIO.apply_trade(symbol, market, payload.side, payload.quantity, float(price))
	except ValueError as exc:
		raise HTTPException(status_code=400, detail=str(exc)) from exc

	return {
		"trade": entry.__dict__,
		"summary": PORTFOLIO.snapshot({}),
	}


@router.get("/paper/ledger")
def paper_ledger() -> dict:
	return {"ledger": [entry.__dict__ for entry in PORTFOLIO.ledger]}


@router.get("/paper/summary")
def paper_summary() -> dict:
	latest_prices = {}
	for key, pos in PORTFOLIO.positions.items():
		try:
			df = get_ohlcv(pos.symbol, period="6mo", market=pos.market)
			if not df.empty:
				latest_prices[key] = float(df.iloc[-1]["close"])
		except ValueError:
			continue
	return PORTFOLIO.snapshot(latest_prices)
