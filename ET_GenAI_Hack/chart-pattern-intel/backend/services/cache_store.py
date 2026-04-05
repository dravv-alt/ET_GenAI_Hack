"""Simple in-memory caches for scans and backtests."""

from __future__ import annotations

import time
from typing import Any, Dict, Tuple

from config import CACHE_TTL_SECONDS

_SCAN_CACHE: Dict[Tuple[Any, ...], Tuple[float, dict]] = {}
_BACKTEST_CACHE: Dict[Tuple[Any, ...], Tuple[float, dict]] = {}


def _cache_get(cache: Dict[Tuple[Any, ...], Tuple[float, dict]], key: Tuple[Any, ...]) -> dict | None:
	cached = cache.get(key)
	if not cached:
		return None
	cached_at, payload = cached
	if time.time() - cached_at > CACHE_TTL_SECONDS:
		cache.pop(key, None)
		return None
	return payload


def _cache_set(cache: Dict[Tuple[Any, ...], Tuple[float, dict]], key: Tuple[Any, ...], payload: dict) -> None:
	cache[key] = (time.time(), payload)


def get_scan_cache(key: Tuple[Any, ...]) -> dict | None:
	return _cache_get(_SCAN_CACHE, key)


def set_scan_cache(key: Tuple[Any, ...], payload: dict) -> None:
	_cache_set(_SCAN_CACHE, key, payload)


def get_backtest_cache(key: Tuple[Any, ...]) -> dict | None:
	return _cache_get(_BACKTEST_CACHE, key)


def set_backtest_cache(key: Tuple[Any, ...], payload: dict) -> None:
	_cache_set(_BACKTEST_CACHE, key, payload)
