"""Fetches OHLCV data from yfinance with light caching."""

from __future__ import annotations

import time
from typing import Dict, Tuple

import pandas as pd
import yfinance as yf

from config import CACHE_TTL_SECONDS, RATE_LIMIT_DELAY_SECONDS

_CACHE: Dict[Tuple[str, str, str, str, bool], Tuple[float, pd.DataFrame]] = {}

_MARKET_SUFFIXES = {
	"NSE": ".NS",
	"BSE": ".BO",
	"FTSE": ".L",
	"DAX": ".DE",
	"NIFTY50": ".NS",
}

_ALLOWED_MARKETS = {
	"NSE",
	"BSE",
	"NASDAQ",
	"NYSE",
	"SP500",
	"DAX",
	"FTSE",
	"CRYPTO",
	"NIFTY50",
}

_CRYPTO_QUOTES = ("-USD", "-USDT")


def _normalize_ticker(ticker: str, market: str = "NSE") -> str:
	if not ticker:
		raise ValueError("Ticker is required")
	market = market.strip().upper()
	if market not in _ALLOWED_MARKETS:
		raise ValueError(f"Unsupported market: {market}")

	ticker = ticker.strip().upper()
	if ticker.startswith("^"):
		return ticker
	if market == "CRYPTO" and "-" in ticker:
		return ticker
	if ticker.endswith(_CRYPTO_QUOTES):
		return ticker
	for suffix in _MARKET_SUFFIXES.values():
		if ticker.endswith(suffix):
			return ticker
	if market in _MARKET_SUFFIXES:
		return f"{ticker}{_MARKET_SUFFIXES[market]}"
	return ticker


def _cache_get(key: Tuple[str, str, str, str, bool]) -> pd.DataFrame | None:
	cached = _CACHE.get(key)
	if not cached:
		return None
	cached_at, df = cached
	if time.time() - cached_at > CACHE_TTL_SECONDS:
		_CACHE.pop(key, None)
		return None
	return df.copy()


def _cache_set(key: Tuple[str, str, str, str, bool], df: pd.DataFrame) -> None:
	_CACHE[key] = (time.time(), df.copy())


def get_ohlcv(
	ticker: str,
	period: str = "6mo",
	market: str = "NSE",
	interval: str = "1d",
) -> pd.DataFrame:
	"""
	Fetches OHLCV data for pattern detection.
	period: "6mo" for pattern detection, "5y" for backtesting
	Returns DataFrame with columns: date, open, high, low, close, volume
	"""
	normalized = _normalize_ticker(ticker, market=market)
	cache_key = (market, normalized, period, interval, False)
	cached = _cache_get(cache_key)
	if cached is not None:
		cached.attrs["ticker"] = normalized
		return cached

	time.sleep(RATE_LIMIT_DELAY_SECONDS)
	stock = yf.Ticker(normalized)
	df = stock.history(period=period, interval=interval)

	if df.empty:
		raise ValueError(f"No data found for {normalized}. Check ticker symbol.")

	df = df.reset_index()
	if "Date" in df.columns:
		df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
	elif "Datetime" in df.columns:
		if interval == "1d":
			df["Datetime"] = df["Datetime"].dt.strftime("%Y-%m-%d")
		else:
			df["Datetime"] = df["Datetime"].dt.strftime("%Y-%m-%d %H:%M")

	df = df.rename(columns={
		"Date": "date",
		"Datetime": "date",
		"Open": "open",
		"High": "high",
		"Low": "low",
		"Close": "close",
		"Volume": "volume",
	})
	df = df[["date", "open", "high", "low", "close", "volume"]]
	df.attrs["ticker"] = normalized

	_cache_set(cache_key, df)
	return df.copy()


def get_ohlcv_with_indicators(
	ticker: str,
	period: str = "6mo",
	market: str = "NSE",
	interval: str = "1d",
) -> pd.DataFrame:
	"""
	Adds technical indicators to OHLCV DataFrame:
	- RSI (14-period)
	- MACD (12, 26, 9)
	- SMA 20, 50, 200
	- Bollinger Bands
	- Volume SMA 20
	"""
	normalized = _normalize_ticker(ticker, market=market)
	cache_key = (market, normalized, period, interval, True)
	cached = _cache_get(cache_key)
	if cached is not None:
		cached.attrs["ticker"] = normalized
		return cached

	df = get_ohlcv(ticker, period=period, market=market, interval=interval)

	delta = df["close"].diff()
	gain = delta.clip(lower=0).rolling(14).mean()
	loss = (-delta.clip(upper=0)).rolling(14).mean()
	df["rsi"] = 100 - (100 / (1 + gain / loss))

	ema12 = df["close"].ewm(span=12, adjust=False).mean()
	ema26 = df["close"].ewm(span=26, adjust=False).mean()
	df["macd"] = ema12 - ema26
	df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
	df["macd_hist"] = df["macd"] - df["macd_signal"]

	df["sma20"] = df["close"].rolling(20).mean()
	df["sma50"] = df["close"].rolling(50).mean()
	df["sma200"] = df["close"].rolling(200).mean()

	df["bb_mid"] = df["close"].rolling(20).mean()
	bb_std = df["close"].rolling(20).std()
	df["bb_upper"] = df["bb_mid"] + 2 * bb_std
	df["bb_lower"] = df["bb_mid"] - 2 * bb_std

	df["volume_sma20"] = df["volume"].rolling(20).mean()

	df = df.dropna().reset_index(drop=True)
	df.attrs["ticker"] = normalized

	_cache_set(cache_key, df)
	return df.copy()
