"""Generates market overview, top gainers, and top losers segments.

Sovereign Analyst Terminal design:
- Market Overview: mega number, area chart, section heading
- Top Gainers: numbered rows with sector tags, volume, full-width bars
- Top Losers: same layout, coral/salmon bars
"""

from __future__ import annotations

from typing import Any

import numpy as np

try:
	import seaborn as sns
except Exception:  # pragma: no cover
	sns = None

from rendering.color_themes import SEMANTIC_COLORS, pick_change_color, signed_text
from rendering.frame_builder import (
	add_info_panel,
	add_ranked_bar_block,
	add_top_banner,
	create_canvas,
	fig_to_png_bytes,
)
from rendering.text_overlay import (
	add_footer,
	add_insight_panel,
	add_progressive_note,
	add_section_header,
	add_subtitle,
	add_ticker_tape,
	add_watermark,
)


def _to_float(value: Any, default: float = 0.0) -> float:
	try:
		return float(value)
	except (TypeError, ValueError):
		return default


def generate_market_overview_frames(snapshot: dict[str, Any], total_frames: int = 18) -> list[bytes]:
	"""Builds the Sovereign Analyst market overview segment.

	Layout:
	  [MARKET ANALYTICS ticker tape]
	  SECTION TITLE
	  MARKET OVERVIEW
	  ┌─────────────────────────┐  ┌────────────────────────┐
	  │ NIFTY 50                │  │    area chart           │
	  │ 22,123.45               │  │    with gradient fill   │
	  │ +1.2% (+263.15) ↗      │  │                         │
	  └─────────────────────────┘  └────────────────────────┘
	  [INSIGHT ENGINE] Nifty surges as broad-based buying...
	  [AI NARRATIVE INSIGHT: ...]
	  SOVEREIGN ANALYST TERMINAL | 24 OCT 2023 | SYSTEM STATUS: OPTIMAL
	"""
	nifty = dict(snapshot.get("nifty", {}))
	open_val = _to_float(nifty.get("open", 0.0))
	high_val = _to_float(nifty.get("high", 0.0))
	low_val = _to_float(nifty.get("low", 0.0))
	close_val = _to_float(nifty.get("close", 0.0))
	close_text = f"{close_val:,.2f}"
	change_pct = _to_float(nifty.get("change_pct", 0.0))
	change_abs = _to_float(nifty.get("change_abs", 0.0))

	# Build intraday path data
	if close_val >= open_val:
		line_y = [open_val, low_val, high_val, close_val]
	else:
		line_y = [open_val, high_val, low_val, close_val]
	line_x = [0, 1, 2, 3]

	frames: list[bytes] = []
	for frame_num in range(total_frames):
		progress = min(frame_num / max(total_frames * 0.7, 1), 1.0)
		visible_points = max(2, int(np.ceil(progress * len(line_x))))

		fig, ax = create_canvas()

		# Ticker tape
		add_ticker_tape(ax)

		# Section header
		ax.text(
			0.065,
			0.88,
			"SECTION TITLE",
			transform=ax.transAxes,
			color=SEMANTIC_COLORS["text_secondary"],
			fontsize=8,
			family="monospace",
		)
		ax.text(
			0.065,
			0.84,
			"MARKET OVERVIEW",
			transform=ax.transAxes,
			color=SEMANTIC_COLORS["text_primary"],
			fontsize=28,
			fontweight="bold",
		)

		# Locale badge (right side)
		ax.text(
			0.93,
			0.88,
			"LOCALE / EXCHANGE",
			transform=ax.transAxes,
			color=SEMANTIC_COLORS["text_secondary"],
			fontsize=7,
			ha="right",
			family="monospace",
		)
		ax.text(
			0.93,
			0.85,
			"NSE: INDIA",
			transform=ax.transAxes,
			color=SEMANTIC_COLORS["text_primary"],
			fontsize=11,
			fontweight="bold",
			ha="right",
		)

		# Divider line
		ax.plot(
			[0.065, 0.60],
			[0.80, 0.80],
			color=SEMANTIC_COLORS["panel_border"],
			linewidth=0.8,
			transform=ax.transAxes,
		)

		# NIFTY 50 panel (left half)
		ax.text(
			0.065,
			0.68,
			"NIFTY 50",
			transform=ax.transAxes,
			color=SEMANTIC_COLORS["text_secondary"],
			fontsize=11,
			fontweight="bold",
			family="monospace",
		)

		# Mega number
		ax.text(
			0.065,
			0.52,
			close_text,
			transform=ax.transAxes,
			color=SEMANTIC_COLORS["text_primary"],
			fontsize=52,
			fontweight="bold",
		)

		# Change line
		arrow = "↗" if change_pct >= 0 else "↘"
		change_color = pick_change_color(change_pct)
		ax.text(
			0.065,
			0.40,
			f"{signed_text(change_pct)}  ({signed_text(change_abs, suffix=' pts')})  {arrow}",
			transform=ax.transAxes,
			color=change_color,
			fontsize=16,
			fontweight="bold",
		)

		# Area chart (right half) - with card background
		import matplotlib.patches as mpatches
		chart_bg = mpatches.FancyBboxPatch(
			(0.58, 0.28),
			0.38,
			0.52,
			boxstyle="round,pad=0.005,rounding_size=0.005",
			transform=ax.transAxes,
			linewidth=0.8,
			edgecolor=SEMANTIC_COLORS["panel_border"],
			facecolor=SEMANTIC_COLORS["panel"],
			zorder=1,
		)
		ax.add_patch(chart_bg)

		chart_ax = fig.add_axes([0.59, 0.30, 0.36, 0.48])
		chart_ax.set_facecolor(SEMANTIC_COLORS["panel"])

		x_subset = line_x[:visible_points]
		y_subset = line_y[:visible_points]
		line_color = "#7A8BA8"  # muted slate for the line
		chart_ax.plot(x_subset, y_subset, color=line_color, linewidth=2.0)
		chart_ax.fill_between(x_subset, min(line_y) * 0.995, y_subset, color=line_color, alpha=0.08)
		chart_ax.scatter(x_subset, y_subset, color=line_color, s=30, zorder=5)

		# Data labels on last point
		if len(x_subset) >= 2:
			last_x = x_subset[-1]
			last_y = y_subset[-1]
			chart_ax.text(
				last_x + 0.1,
				last_y,
				f"L: {last_y:,.2f}",
				color=SEMANTIC_COLORS["text_secondary"],
				fontsize=7,
			)

		chart_ax.tick_params(colors=SEMANTIC_COLORS["text_secondary"], labelsize=7)
		chart_ax.grid(alpha=0.08, color=SEMANTIC_COLORS["text_secondary"])
		for spine in chart_ax.spines.values():
			spine.set_color(SEMANTIC_COLORS["panel_border"])

		# ── OHLCV Data Grid (bottom-left, filling space below the number) ──
		range_val = high_val - low_val
		prev_close = close_val - change_abs

		# Divider line above OHLCV
		ax.plot(
			[0.065, 0.55],
			[0.33, 0.33],
			color=SEMANTIC_COLORS["panel_border"],
			linewidth=0.5,
			transform=ax.transAxes,
		)

		# Row 1: OPEN / HIGH
		ohlcv_y1 = 0.27
		ax.text(0.065, ohlcv_y1, "OPEN", transform=ax.transAxes, color=SEMANTIC_COLORS["text_secondary"], fontsize=8, family="monospace")
		ax.text(0.065, ohlcv_y1 - 0.035, f"{open_val:,.2f}", transform=ax.transAxes, color=SEMANTIC_COLORS["text_primary"], fontsize=14, fontweight="bold")

		ax.text(0.20, ohlcv_y1, "HIGH", transform=ax.transAxes, color=SEMANTIC_COLORS["text_secondary"], fontsize=8, family="monospace")
		ax.text(0.20, ohlcv_y1 - 0.035, f"{high_val:,.2f}", transform=ax.transAxes, color=SEMANTIC_COLORS["text_primary"], fontsize=14, fontweight="bold")

		ax.text(0.34, ohlcv_y1, "LOW", transform=ax.transAxes, color=SEMANTIC_COLORS["text_secondary"], fontsize=8, family="monospace")
		ax.text(0.34, ohlcv_y1 - 0.035, f"{low_val:,.2f}", transform=ax.transAxes, color=SEMANTIC_COLORS["text_primary"], fontsize=14, fontweight="bold")

		ax.text(0.47, ohlcv_y1, "CLOSE", transform=ax.transAxes, color=SEMANTIC_COLORS["text_secondary"], fontsize=8, family="monospace")
		ax.text(0.47, ohlcv_y1 - 0.035, f"{close_val:,.2f}", transform=ax.transAxes, color=SEMANTIC_COLORS["text_primary"], fontsize=14, fontweight="bold")

		# Row 2: RANGE / PREV CLOSE / DAY MOVE / VOLUME
		ohlcv_y2 = 0.17
		ax.text(0.065, ohlcv_y2, "RANGE", transform=ax.transAxes, color=SEMANTIC_COLORS["text_secondary"], fontsize=8, family="monospace")
		ax.text(0.065, ohlcv_y2 - 0.035, f"{range_val:,.2f}", transform=ax.transAxes, color=SEMANTIC_COLORS["text_primary"], fontsize=14, fontweight="bold")

		ax.text(0.20, ohlcv_y2, "PREV CLOSE", transform=ax.transAxes, color=SEMANTIC_COLORS["text_secondary"], fontsize=8, family="monospace")
		ax.text(0.20, ohlcv_y2 - 0.035, f"{prev_close:,.2f}", transform=ax.transAxes, color=SEMANTIC_COLORS["text_primary"], fontsize=14, fontweight="bold")

		ax.text(0.34, ohlcv_y2, "DAY MOVE", transform=ax.transAxes, color=SEMANTIC_COLORS["text_secondary"], fontsize=8, family="monospace")
		ax.text(0.34, ohlcv_y2 - 0.035, f"{signed_text(change_abs, suffix=' pts')}", transform=ax.transAxes, color=change_color, fontsize=14, fontweight="bold")

		ax.text(0.47, ohlcv_y2, "DAY CHANGE", transform=ax.transAxes, color=SEMANTIC_COLORS["text_secondary"], fontsize=8, family="monospace")
		ax.text(0.47, ohlcv_y2 - 0.035, f"{signed_text(change_pct)}", transform=ax.transAxes, color=change_color, fontsize=14, fontweight="bold")

		# Divider line below OHLCV
		ax.plot(
			[0.065, 0.55],
			[0.10, 0.10],
			color=SEMANTIC_COLORS["panel_border"],
			linewidth=0.5,
			transform=ax.transAxes,
		)

		# Source tag
		ax.text(
			0.065,
			0.075,
			"DATA SOURCE: YAHOO FINANCE // NSE LIVE FEED",
			transform=ax.transAxes,
			color=SEMANTIC_COLORS["text_secondary"],
			fontsize=7,
			family="monospace",
		)

		add_footer(ax)
		frames.append(fig_to_png_bytes(fig))

	return frames


def generate_gainers_frames(snapshot: dict[str, Any], total_frames: int = 12) -> list[bytes]:
	"""Builds the Sovereign Analyst top gainers segment.

	Layout:
	  [MARKET ANALYTICS ticker tape]
	  ┃ TOP GAINERS
	  ┃ NSE / BSE COMPOSITE INDEX
	  01  RELIANCE   ENERGY          +3.4%  VOL: 12.4M
	  [=====================bar=====================]
	  02  HDFC BANK  BFSI            +2.8%  VOL: 8.1M
	  [================bar================]
	  ...
	  [AI NARRATIVE INSIGHT]
	  SOVEREIGN ANALYST TERMINAL
	"""
	gainers = list(dict(snapshot.get("movers", {})).get("gainers", []))

	frames: list[bytes] = []
	for frame_num in range(total_frames):
		fig, ax = create_canvas()

		add_ticker_tape(ax)
		add_section_header(ax, "TOP GAINERS", "NSE / BSE COMPOSITE INDEX")

		add_ranked_bar_block(
			ax=ax,
			items=gainers,
			title="",
			x=0.065,
			y=0.06,
			width=0.87,
			row_height=0.14,
			frame_num=frame_num,
			total_frames=total_frames,
			bar_context="default",
		)

		add_footer(ax)
		frames.append(fig_to_png_bytes(fig))

	return frames


def generate_losers_frames(snapshot: dict[str, Any], total_frames: int = 12) -> list[bytes]:
	"""Builds the Sovereign Analyst top losers segment.

	Same layout as gainers but with coral/salmon color bars.
	"""
	losers = list(dict(snapshot.get("movers", {})).get("losers", []))

	frames: list[bytes] = []
	for frame_num in range(total_frames):
		fig, ax = create_canvas()

		add_ticker_tape(ax)
		add_section_header(ax, "TOP LOSERS", "EQUITIES MARKET | INTRADAY PERFORMANCE DECLINE")

		add_ranked_bar_block(
			ax=ax,
			items=losers,
			title="",
			x=0.065,
			y=0.06,
			width=0.87,
			row_height=0.14,
			frame_num=frame_num,
			total_frames=total_frames,
			bar_context="loser",
		)

		add_footer(ax)
		frames.append(fig_to_png_bytes(fig))

	return frames
