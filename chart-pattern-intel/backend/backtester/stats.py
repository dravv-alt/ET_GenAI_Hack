"""Stats helpers for win rate and avg gain/loss calculations."""

from __future__ import annotations

from statistics import median
from typing import Iterable, Optional


def compute_backtest_stats(outcomes: Iterable[float]) -> dict:
	values = list(outcomes)
	if not values:
		return {
			"sample_count": 0,
			"win_rate": None,
			"avg_gain_pct": None,
			"avg_loss_pct": None,
			"rr_ratio": None,
			"median_return_pct": None,
		}

	wins = [v for v in values if v > 0]
	losses = [v for v in values if v <= 0]
	avg_gain = sum(wins) / len(wins) if wins else None
	avg_loss = sum(losses) / len(losses) if losses else None
	rr_ratio = None
	if avg_gain is not None and avg_loss is not None and avg_loss != 0:
		rr_ratio = abs(avg_gain / avg_loss)

	return {
		"sample_count": len(values),
		"win_rate": round(len(wins) / len(values), 3),
		"avg_gain_pct": round(avg_gain, 2) if avg_gain is not None else None,
		"avg_loss_pct": round(avg_loss, 2) if avg_loss is not None else None,
		"rr_ratio": round(rr_ratio, 2) if rr_ratio is not None else None,
		"median_return_pct": round(median(values), 2),
	}


def compute_expectancy(
	win_rate: Optional[float],
	avg_gain: Optional[float],
	avg_loss: Optional[float],
) -> Optional[float]:
	if win_rate is None or avg_gain is None or avg_loss is None:
		return None
	return round((win_rate * avg_gain) + ((1 - win_rate) * avg_loss), 3)
