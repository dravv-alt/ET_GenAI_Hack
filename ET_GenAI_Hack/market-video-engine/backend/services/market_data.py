"""Market data service for the AI Market Video Engine.

Phase 1 scope:
- Live market fetchers through yfinance.
- Deterministic JSON fallbacks under backend/data.
- Single-call aggregation API for downstream orchestrator use.
"""

from __future__ import annotations

import json
import io
import re
import time
import logging
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any

import yfinance as yf


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_SYMBOL_RE = re.compile(r"^[A-Z0-9^._-]{2,20}$")


def _load_fallback(filename: str) -> Any:
	file_path = DATA_DIR / filename
	with file_path.open("r", encoding="utf-8") as fp:
		return json.load(fp)


def _load_market_universe() -> dict[str, Any]:
	return _load_fallback("market_universe.json")


def _load_fetch_config() -> dict[str, Any]:
	return _load_fallback("data_fetch_config.json")


def _as_float(value: Any, default: float = 0.0) -> float:
	try:
		return float(value)
	except (TypeError, ValueError):
		return default


def _extract_close_change(history_df: Any) -> tuple[float, float] | None:
	"""Returns (last_close, pct_change) from a yfinance history dataframe."""
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
	"""Suppresses expected noisy stderr/stdout/logging from yfinance calls."""
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


def get_nifty_data(period: str = "5d") -> dict[str, float]:
	"""Fetch latest Nifty OHLC and day-over-day change metrics."""
	universe = _load_market_universe()
	fetch_cfg = _load_fetch_config()
	timeout_sec = _as_float(fetch_cfg.get("timeout_sec", 8), 8.0)
	retries = int(_as_float(fetch_cfg.get("retries", 3), 3))
	retry_backoff_sec = _as_float(fetch_cfg.get("retry_backoff_sec", 0.6), 0.6)
	nifty_symbol = str(universe.get("nifty_symbol", "")).strip()
	if not nifty_symbol:
		return _load_fallback("nifty_fallback.json")
	try:
		history = _with_retry(
			lambda: yf.Ticker(nifty_symbol).history(period=period, timeout=timeout_sec),
			retries=retries,
			backoff_sec=retry_backoff_sec,
		)
		if history.empty:
			return _load_fallback("nifty_fallback.json")

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
	except Exception:
		return _load_fallback("nifty_fallback.json")


def get_top_movers(
	n: int = 5,
	max_tickers: int = 20,
	tickers_override: list[str] | None = None,
) -> dict[str, list[dict[str, Any]]]:
	"""Return top gainers and losers from a bounded Nifty sample basket."""
	fallback = _load_fallback("top_movers_fallback.json")
	universe = _load_market_universe()
	fetch_cfg = _load_fetch_config()
	timeout_sec = _as_float(fetch_cfg.get("timeout_sec", 8), 8.0)
	retries = int(_as_float(fetch_cfg.get("retries", 3), 3))
	retry_backoff_sec = _as_float(fetch_cfg.get("retry_backoff_sec", 0.6), 0.6)
	use_threads = bool(fetch_cfg.get("use_threads", False))
	max_tickers_cfg = int(_as_float(fetch_cfg.get("max_tickers", max_tickers), max_tickers))
	min_valid_movers = int(_as_float(fetch_cfg.get("min_valid_movers", max(6, n * 2)), max(6, n * 2)))
	excluded = set(_sanitize_symbols(list(fetch_cfg.get("exclude_tickers", []))))

	raw_source = tickers_override if tickers_override else list(universe.get("sample_tickers", []))
	tickers = _sanitize_symbols(raw_source, excluded=excluded)[: min(max_tickers, max_tickers_cfg)]
	if not tickers:
		return fallback
	try:
		data = _with_retry(
			lambda: yf.download(
				tickers=tickers,
				period="5d",
				interval="1d",
				auto_adjust=False,
				group_by="ticker",
				progress=False,
				threads=use_threads,
				timeout=timeout_sec,
			),
			retries=retries,
			backoff_sec=retry_backoff_sec,
		)
	except Exception:
		return fallback

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
		return fallback

	sorted_movers = sorted(movers, key=lambda item: item["change_pct"], reverse=True)
	return {
		"gainers": sorted_movers[:n],
		"losers": sorted_movers[-n:][::-1],
	}


def get_sector_performance() -> list[dict[str, float | str]]:
	"""Return sorted sector-wise day performance percentages."""
	fallback = _load_fallback("sectors_fallback.json")
	universe = _load_market_universe()
	fetch_cfg = _load_fetch_config()
	timeout_sec = _as_float(fetch_cfg.get("timeout_sec", 8), 8.0)
	retries = int(_as_float(fetch_cfg.get("retries", 3), 3))
	retry_backoff_sec = _as_float(fetch_cfg.get("retry_backoff_sec", 0.6), 0.6)
	use_threads = bool(fetch_cfg.get("use_threads", False))
	min_valid_sectors = int(_as_float(fetch_cfg.get("min_valid_sectors", 4), 4))

	raw_sector_symbols = dict(universe.get("sector_symbols", {}))
	sector_symbols = {
		str(name).strip(): symbol
		for name, symbol in raw_sector_symbols.items()
		if _sanitize_symbol(symbol)
	}
	if not sector_symbols:
		return fallback

	symbols = list(sector_symbols.values())
	try:
		data = _with_retry(
			lambda: yf.download(
				tickers=symbols,
				period="5d",
				interval="1d",
				auto_adjust=False,
				group_by="ticker",
				progress=False,
				threads=use_threads,
				timeout=timeout_sec,
			),
			retries=retries,
			backoff_sec=retry_backoff_sec,
		)
	except Exception:
		return fallback

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
		return fallback
	return sorted(results, key=lambda item: item["change_pct"], reverse=True)


def get_fii_dii_flows() -> dict[str, Any]:
	"""Return latest FII/DII net flow summary.

	Live exchange-grade ingestion will be added in a later phase.
	For Phase 1, we use a deterministic fallback payload.
	"""
	return _load_fallback("fii_dii_fallback.json")


def get_ipo_data() -> list[dict[str, Any]]:
	"""Return IPO tracker payload.

	Live IPO scraping/API integration will be added in a later phase.
	For Phase 1, we use a deterministic fallback payload.
	"""
	return _load_fallback("ipo_fallback.json")


def get_market_snapshot(top_n: int = 5, custom_tickers: list[str] | None = None) -> dict[str, Any]:
	"""One-call aggregate payload used by the orchestrator.

	This ensures data is fetched once per generation request.
	When custom_tickers are provided, top movers are computed from that basket.
	"""
	return {
		"nifty": get_nifty_data(),
		"movers": get_top_movers(n=top_n, tickers_override=custom_tickers),
		"sectors": get_sector_performance(),
		"fii_dii": get_fii_dii_flows(),
		"ipos": get_ipo_data(),
		"scope": {
			"custom_tickers_count": len(custom_tickers or []),
			"is_custom_scope": bool(custom_tickers),
		},
	}
