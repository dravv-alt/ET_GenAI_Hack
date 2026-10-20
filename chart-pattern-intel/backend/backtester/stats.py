"""Stats helpers for win rate and avg gain/loss calculations."""

from __future__ import annotations

from statistics import mean, median, pstdev
from typing import Iterable, Optional


def _safe_mean(values: list[float]) -> Optional[float]:
	return mean(values) if values else None


def _safe_pstdev(values: list[float]) -> Optional[float]:
	return pstdev(values) if len(values) > 1 else None


def _compute_equity_curve(returns_pct: list[float]) -> list[float]:
	equity = 1.0
	curve = []
	for ret in returns_pct:
		equity *= 1 + (ret / 100)
		curve.append(equity)
	return curve


def compute_backtest_stats(
	outcomes: Iterable[float],
	evaluations: Optional[list[dict]] = None,
	total_bars: Optional[int] = None,
	total_years: Optional[float] = None,
	risk_free_rate: float = 0.0,
) -> dict:
	values = list(outcomes)
	if not values:
		return {
			"sample_count": 0,
			"win_rate": None,
			"avg_gain_pct": None,
			"avg_loss_pct": None,
			"rr_ratio": None,
			"median_return_pct": None,
			"profit_factor": None,
			"expectancy": None,
			"sharpe_ratio": None,
			"sortino_ratio": None,
			"max_drawdown_pct": None,
			"calmar_ratio": None,
			"exposure_pct": None,
			"avg_time_in_trade_bars": None,
			"avg_bars_to_target": None,
			"avg_bars_to_stop": None,
		}

	wins = [v for v in values if v > 0]
	losses = [v for v in values if v <= 0]
	avg_gain = sum(wins) / len(wins) if wins else None
	avg_loss = sum(losses) / len(losses) if losses else None
	rr_ratio = None
	if avg_gain is not None and avg_loss is not None and avg_loss != 0:
		rr_ratio = abs(avg_gain / avg_loss)

	profit_factor = None
	if wins and losses:
		profit_factor = abs(sum(wins) / sum(losses)) if sum(losses) != 0 else None

	expectancy = compute_expectancy(
		round(len(wins) / len(values), 3),
		round(avg_gain, 2) if avg_gain is not None else None,
		round(avg_loss, 2) if avg_loss is not None else None,
	) if values else None

	returns_decimal = [v / 100 for v in values]
	avg_return = _safe_mean(returns_decimal)
	std_return = _safe_pstdev(returns_decimal)
	trades_per_year = None
	if total_years and total_years > 0:
		trades_per_year = len(values) / total_years

	sharpe_ratio = None
	if avg_return is not None and std_return and trades_per_year and trades_per_year > 0:
		rf_per_trade = risk_free_rate / trades_per_year
		sharpe_ratio = (avg_return - rf_per_trade) / std_return * (trades_per_year ** 0.5)

	sortino_ratio = None
	downside = [r for r in returns_decimal if r < 0]
	downside_dev = _safe_pstdev(downside)
	if avg_return is not None and downside_dev and trades_per_year and trades_per_year > 0:
		rf_per_trade = risk_free_rate / trades_per_year
		sortino_ratio = (avg_return - rf_per_trade) / downside_dev * (trades_per_year ** 0.5)

	max_drawdown_pct = None
	calmar_ratio = None
	curve = _compute_equity_curve(values)
	if curve:
		peak = curve[0]
		max_drawdown = 0.0
		for point in curve:
			if point > peak:
				peak = point
			drawdown = (point / peak) - 1
			if drawdown < max_drawdown:
				max_drawdown = drawdown
		max_drawdown_pct = abs(max_drawdown) * 100
		if total_years and total_years > 0 and max_drawdown != 0:
			cagr = curve[-1] ** (1 / total_years) - 1
			calmar_ratio = cagr / abs(max_drawdown)

	exposure_pct = None
	avg_time_in_trade_bars = None
	avg_bars_to_target = None
	avg_bars_to_stop = None
	if evaluations:
		bars_held = [e.get("bars_held") for e in evaluations if e.get("bars_held") is not None]
		if bars_held:
			avg_time_in_trade_bars = mean(bars_held)
			if total_bars and total_bars > 0:
				exposure_pct = sum(bars_held) / total_bars * 100
		target_bars = [e.get("bars_to_target") for e in evaluations if e.get("bars_to_target") is not None]
		stop_bars = [e.get("bars_to_stop") for e in evaluations if e.get("bars_to_stop") is not None]
		if target_bars:
			avg_bars_to_target = mean(target_bars)
		if stop_bars:
			avg_bars_to_stop = mean(stop_bars)

	return {
		"sample_count": len(values),
		"win_rate": round(len(wins) / len(values), 3),
		"avg_gain_pct": round(avg_gain, 2) if avg_gain is not None else None,
		"avg_loss_pct": round(avg_loss, 2) if avg_loss is not None else None,
		"rr_ratio": round(rr_ratio, 2) if rr_ratio is not None else None,
		"median_return_pct": round(median(values), 2),
		"profit_factor": round(profit_factor, 2) if profit_factor is not None else None,
		"expectancy": round(expectancy, 3) if expectancy is not None else None,
		"sharpe_ratio": round(sharpe_ratio, 2) if sharpe_ratio is not None else None,
		"sortino_ratio": round(sortino_ratio, 2) if sortino_ratio is not None else None,
		"max_drawdown_pct": round(max_drawdown_pct, 2) if max_drawdown_pct is not None else None,
		"calmar_ratio": round(calmar_ratio, 2) if calmar_ratio is not None else None,
		"exposure_pct": round(exposure_pct, 2) if exposure_pct is not None else None,
		"avg_time_in_trade_bars": round(avg_time_in_trade_bars, 2) if avg_time_in_trade_bars is not None else None,
		"avg_bars_to_target": round(avg_bars_to_target, 2) if avg_bars_to_target is not None else None,
		"avg_bars_to_stop": round(avg_bars_to_stop, 2) if avg_bars_to_stop is not None else None,
	}


def compute_expectancy(
	win_rate: Optional[float],
	avg_gain: Optional[float],
	avg_loss: Optional[float],
) -> Optional[float]:
	if win_rate is None or avg_gain is None or avg_loss is None:
		return None
	return round((win_rate * avg_gain) + ((1 - win_rate) * avg_loss), 3)
