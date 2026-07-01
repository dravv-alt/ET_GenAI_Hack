"""Market data service for the AI Market Video Engine.

Provides live market data via yfinance and NSE India scrapers.
No hardcoded fallbacks are used. If data is unavailable for a given historic date,
the generators will gracefully omit that segment from the video.
"""

from __future__ import annotations

import json
import io
import re
import time
import logging
from datetime import datetime, timedelta
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any

import pandas as pd
import yfinance as yf
import requests

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_SYMBOL_RE = re.compile(r"^[A-Z0-9^._-]{2,20}$")


def _load_market_universe() -> dict[str, Any]:
	file_path = DATA_DIR / "market_universe.json"
	with file_path.open("r", encoding="utf-8") as fp:
		return json.load(fp)


def _load_fetch_config() -> dict[str, Any]:
	file_path = DATA_DIR / "data_fetch_config.json"
	if file_path.exists():
		with file_path.open("r", encoding="utf-8") as fp:
			return json.load(fp)
	return {}


def _as_float(value: Any, default: float = 0.0) -> float:
	try:
		return float(value)
	except (TypeError, ValueError):
		return default


def _extract_close_change(history_df: Any) -> tuple[float, float] | None:
	if history_df is None or history_df.empty:
		return None

	closes = history_df["Close"].dropna()
	if len(closes) < 2:
		return None

	prev_close = _as_float(closes.iloc[-2])
	last_close = _as_float(closes.iloc[-1])
	if prev_close == 0:
		return None

	pct_change = ((last_close - prev_close) / prev_close) * 100
	return last_close, pct_change


def _sanitize_symbol(raw_symbol: Any) -> str | None:
	if raw_symbol is None:
		return None
	symbol = str(raw_symbol).strip().upper()
	if not symbol:
		return None
	if not _SYMBOL_RE.match(symbol):
		return None
	return symbol


def _sanitize_symbols(raw_symbols: list[Any], excluded: set[str] | None = None) -> list[str]:
	excluded = excluded or set()
	cleaned: list[str] = []
	seen: set[str] = set()
	for raw in raw_symbols:
		symbol = _sanitize_symbol(raw)
		if not symbol or symbol in seen or symbol in excluded:
			continue
		seen.add(symbol)
		cleaned.append(symbol)
	return cleaned


def _with_retry(fetcher: Any, retries: int, backoff_sec: float) -> Any:
	last_error: Exception | None = None
	for attempt in range(max(retries, 1)):
		try:
			with _suppress_yfinance_noise():
				result = fetcher()
			if result is None:
				raise ValueError("Empty result from data source")
			return result
		except Exception as exc:
			last_error = exc
			if attempt < max(retries, 1) - 1 and backoff_sec > 0:
				time.sleep(backoff_sec * (attempt + 1))
	if last_error:
		raise last_error
	raise RuntimeError("Retry wrapper failed without a captured exception")


@contextmanager
def _suppress_yfinance_noise():
	root_disable_before = logging.root.manager.disable
	yf_logger = logging.getLogger("yfinance")
	old_yf_level = yf_logger.level
	try:
		logging.disable(logging.CRITICAL)
		yf_logger.setLevel(logging.CRITICAL)
		with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
			yield
	finally:
		yf_logger.setLevel(old_yf_level)
		logging.disable(root_disable_before)


def _get_history_kwargs(target_date: str | None) -> dict[str, Any]:
	"""Returns kwargs for yf.download / yf.history to fetch historical or recent window."""
	if not target_date:
		return {"period": "5d"}
	try:
		dt = datetime.strptime(target_date, "%Y-%m-%d")
		end_dt = dt + timedelta(days=1)
		start_dt = end_dt - timedelta(days=10)
		return {
			"start": start_dt.strftime("%Y-%m-%d"),
			"end": end_dt.strftime("%Y-%m-%d"),
		}
	except ValueError:
		return {"period": "5d"}


def _download_stitched(tickers: list[str] | str, target_date: str | None, timeout_sec: float, retries: int, retry_backoff_sec: float, use_threads: bool = True, is_single: bool = False) -> Any:
	"""Fetches yfinance data. Stitches historical api with live api to bypass the 1-day Yahoo Finance lag bug."""
	hist_kwargs = _get_history_kwargs(target_date)
	
	def fetch_data(kwargs: dict):
		if is_single:
			return yf.Ticker(tickers).history(timeout=timeout_sec, **kwargs)
		else:
			return yf.download(
				tickers=tickers,
				interval="1d",
				auto_adjust=False,
				group_by="ticker",
				progress=False,
				threads=use_threads,
				timeout=timeout_sec,
				**kwargs
			)

	hist_df = _with_retry(lambda: fetch_data(hist_kwargs), retries, retry_backoff_sec)
	
	try:
		live_df = _with_retry(lambda: fetch_data({"period": "1d"}), 1, 0.0)
		if not live_df.empty:
			df = pd.concat([hist_df, live_df])
			df = df[~df.index.duplicated(keep='last')]
			df = df.sort_index()
		else:
			df = hist_df
	except Exception:
		df = hist_df
		
	if target_date and not df.empty:
		try:
			target_dt = datetime.strptime(target_date, "%Y-%m-%d").date()
			df = df[df.index.date <= target_dt]
		except Exception:
			pass
			
	return df


def get_nifty_data(target_date: str | None = None) -> dict[str, float]:
	universe = _load_market_universe()
	fetch_cfg = _load_fetch_config()
	timeout_sec = _as_float(fetch_cfg.get("timeout_sec", 60), 60.0)
	retries = int(_as_float(fetch_cfg.get("retries", 3), 3))
	retry_backoff_sec = _as_float(fetch_cfg.get("retry_backoff_sec", 1.0), 1.0)
	
	nifty_symbol = str(universe.get("nifty_symbol", "")).strip()
	if not nifty_symbol:
		return {}

	try:
		history = _download_stitched(nifty_symbol, target_date, timeout_sec, retries, retry_backoff_sec, is_single=True)
		if history.empty:
			return {}

		latest = history.iloc[-1]
		prev_close = history.iloc[-2]["Close"] if len(history) > 1 else latest["Open"]

		prev_close_f = _as_float(prev_close, _as_float(latest["Open"], 1.0))
		close_f = _as_float(latest["Close"])
		change_abs = close_f - prev_close_f
		change_pct = (change_abs / prev_close_f) * 100 if prev_close_f else 0.0

		return {
			"open": round(_as_float(latest["Open"]), 2),
			"close": round(close_f, 2),
			"high": round(_as_float(latest["High"]), 2),
			"low": round(_as_float(latest["Low"]), 2),
			"change_pct": round(change_pct, 2),
			"change_abs": round(change_abs, 2),
		}
	except Exception as e:
		return {}


def get_top_movers(
	n: int = 5,
	max_tickers: int = 20,
	target_date: str | None = None,
) -> dict[str, list[dict[str, Any]]]:
	universe = _load_market_universe()
	fetch_cfg = _load_fetch_config()
	timeout_sec = _as_float(fetch_cfg.get("timeout_sec", 60), 60.0)
	retries = int(_as_float(fetch_cfg.get("retries", 3), 3))
	retry_backoff_sec = _as_float(fetch_cfg.get("retry_backoff_sec", 1.0), 1.0)
	use_threads = bool(fetch_cfg.get("use_threads", True))
	max_tickers_cfg = int(_as_float(fetch_cfg.get("max_tickers", max_tickers), max_tickers))
	min_valid_movers = int(_as_float(fetch_cfg.get("min_valid_movers", max(2, n * 2)), max(2, n * 2)))
	excluded = set(_sanitize_symbols(list(fetch_cfg.get("exclude_tickers", []))))

	raw_source = list(universe.get("sample_tickers", []))
	tickers = _sanitize_symbols(raw_source, excluded=excluded)[: min(max_tickers, max_tickers_cfg)]
	if not tickers:
		return {}
		
	try:
		data = _download_stitched(tickers, target_date, timeout_sec, retries, retry_backoff_sec, use_threads=use_threads)
	except Exception:
		return {}

	movers: list[dict[str, Any]] = []
	for ticker in tickers:
		try:
			history_df = data[ticker] if ticker in data.columns.get_level_values(0) else None
			if history_df is None or history_df.empty:
				continue

			extracted = _extract_close_change(history_df)
			if not extracted:
				continue

			last_close, pct_change = extracted
			movers.append(
				{
					"ticker": ticker.replace(".NS", ""),
					"change_pct": round(pct_change, 2),
					"current_price": round(last_close, 2),
				}
			)
		except Exception:
			continue

	if len(movers) < min_valid_movers:
		return {}

	sorted_movers = sorted(movers, key=lambda item: item["change_pct"], reverse=True)
	return {
		"gainers": sorted_movers[:n],
		"losers": sorted_movers[-n:][::-1],
	}


def get_sector_performance(target_date: str | None = None) -> list[dict[str, float | str]]:
	universe = _load_market_universe()
	fetch_cfg = _load_fetch_config()
	timeout_sec = _as_float(fetch_cfg.get("timeout_sec", 60), 60.0)
	retries = int(_as_float(fetch_cfg.get("retries", 3), 3))
	retry_backoff_sec = _as_float(fetch_cfg.get("retry_backoff_sec", 1.0), 1.0)
	use_threads = bool(fetch_cfg.get("use_threads", True))
	min_valid_sectors = int(_as_float(fetch_cfg.get("min_valid_sectors", 2), 2))

	raw_sector_symbols = dict(universe.get("sector_symbols", {}))
	sector_symbols = {
		str(name).strip(): symbol
		for name, symbol in raw_sector_symbols.items()
		if _sanitize_symbol(symbol)
	}
	if not sector_symbols:
		return []

	symbols = list(sector_symbols.values())

	try:
		data = _download_stitched(symbols, target_date, timeout_sec, retries, retry_backoff_sec, use_threads=use_threads)
	except Exception:
		return []

	results: list[dict[str, float | str]] = []
	for sector_name, symbol in sector_symbols.items():
		try:
			history_df = data[symbol] if symbol in data.columns.get_level_values(0) else None
			extracted = _extract_close_change(history_df)
			if not extracted:
				continue

			_, pct_change = extracted
			results.append({"sector": sector_name, "change_pct": round(pct_change, 2)})
		except Exception:
			continue

	if len(results) < min_valid_sectors:
		return []
	return sorted(results, key=lambda item: item["change_pct"], reverse=True)


def get_fii_dii_flows(target_date: str | None = None) -> dict[str, Any]:
	"""Scrapes real FII/DII data from NSE India API. No fake fallbacks used."""
	try:
		url = 'https://www.nseindia.com/api/fiidiiTradeReact'
		headers = {
			'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
			'Accept': '*/*',
		}
		s = requests.Session()
		s.get('https://www.nseindia.com', headers=headers, timeout=5)
		r = s.get(url, headers=headers, timeout=5)
		if r.status_code == 200:
			data = r.json()
			fii_net = 0.0
			dii_net = 0.0
			for row in data:
				# If a specific historic date is requested, and NSE's latest response doesn't match,
				# we gracefully omit the FII/DII data rather than showing fake/latest data.
				if target_date:
					parsed_dt = datetime.strptime(row.get('date', ''), '%d-%b-%Y')
					requested_dt = datetime.strptime(target_date, '%Y-%m-%d')
					if parsed_dt.date() != requested_dt.date():
						return {}
						
				cat = row.get("category", "")
				if "FII" in cat:
					fii_net = float(row.get("netValue", 0))
				elif "DII" in cat:
					dii_net = float(row.get("netValue", 0))
					
			if fii_net or dii_net:
				return {
					"fii_net_cr": fii_net,
					"dii_net_cr": dii_net
				}
	except Exception:
		pass
	return {}


def get_ipo_data(target_date: str | None = None) -> list[dict[str, Any]]:
	"""Returns empty list. No historic IPO tracking API is available reliably.
	Since we strictly enforce NO fallbacks, we simply omit IPOs for historic renders."""
	return []


def get_market_snapshot(top_n: int = 5, target_date: str | None = None) -> dict[str, Any]:
	return {
		"nifty": get_nifty_data(target_date),
		"movers": get_top_movers(n=top_n, target_date=target_date),
		"sectors": get_sector_performance(target_date),
		"fii_dii": get_fii_dii_flows(target_date),
		"ipos": get_ipo_data(target_date),
		"scope": {
			"target_date": target_date,
			"is_historic": bool(target_date),
		},
	}
