"""Pydantic models for OHLCV chart responses."""

from __future__ import annotations

from typing import List

from pydantic import BaseModel


class OHLCV(BaseModel):
	date: str
	open: float
	high: float
	low: float
	close: float
	volume: float


class ChartResponse(BaseModel):
	ticker: str
	period: str
	ohlcv: List[OHLCV]
