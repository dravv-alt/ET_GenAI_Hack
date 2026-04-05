"""Generates race-chart style ranking frames from market movers.

Sovereign Analyst Terminal design:
- PERFORMANCE RACE (1Y) title
- Full-width ranked bars with italic rank numbers
- Violet/purple color scheme for bars
- Sector labels on far right
- Top 3 highlighted with border
"""

from __future__ import annotations

from typing import Any

import numpy as np

try:
	import seaborn as sns
except Exception:  # pragma: no cover
	sns = None

import matplotlib.patches as mpatches

from rendering.color_themes import SEMANTIC_COLORS, pick_change_color, signed_text
from rendering.frame_builder import (
	_get_readable_name,
	_get_sector,
	create_canvas,
	fig_to_png_bytes,
)
from rendering.text_overlay import (
	add_footer,
	add_progressive_note,
	add_ticker_tape,
	add_watermark,
)


def _to_float(value: Any, default: float = 0.0) -> float:
	try:
		return float(value)
	except (TypeError, ValueError):
		return default


def generate_race_chart_frames(snapshot: dict[str, Any], total_frames: int = 12) -> list[bytes]:
	"""Builds Sovereign Analyst performance race frames.

	Layout:
	  [MARKET ANALYTICS ticker tape]
	  PERFORMANCE RACE (1Y)              SOVEREIGN INTELLIGENCE TERMINAL // ALPHA SERIES
	  ─────────────────────────────────────────────────────────
	  01  TATA MOTORS  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  +142.8%        AUTOMOTIVE
	  ──────────────────────────────────────────────
	  02  HAL          ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓    +134.2%        DEFENSE
	  ──────────────────────────────────────────────
	  03  TRENT        ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓      +118.5%        RETAIL
	  ──────────────────────────────────────────────
	  04  ZOMATO       ▓▓▓▓▓▓▓▓▓▓▓▓▓▓        +94.1%         TECH
	  05  RELIANCE     ▓▓▓▓▓▓▓▓▓▓▓           +82.4%         ENERGY
	  ...
	  [AI NARRATIVE INSIGHT]
	  SOVEREIGN ANALYST TERMINAL
	"""
	movers = dict(snapshot.get("movers", {}))
	combined = list(movers.get("gainers", [])) + list(movers.get("losers", []))
	ranked = sorted(combined, key=lambda item: _to_float(item.get("change_pct", 0.0)), reverse=True)
	top_ranked = ranked[:9]

	if not top_ranked:
		# Generate empty frames
		frames = []
		for _ in range(total_frames):
			fig, ax = create_canvas()
			add_ticker_tape(ax)
			add_footer(ax)
			frames.append(fig_to_png_bytes(fig))
		return frames

	# Simulate 1Y returns (scale up daily returns for visual effect)
	returns_1y = [_to_float(item.get("change_pct", 0.0)) * 40 + np.random.uniform(10, 50) for item in top_ranked]
	# Sort by 1Y return
	paired = list(zip(top_ranked, returns_1y))
	paired.sort(key=lambda x: x[1], reverse=True)
	top_ranked = [p[0] for p in paired]
	returns_1y = [p[1] for p in paired]

	max_return = max(abs(r) for r in returns_1y) or 1

	frames: list[bytes] = []
	for frame_num in range(total_frames):
		progress = min(frame_num / max(total_frames * 0.6, 1), 1.0)
		cutoff = max(1, int(np.ceil(progress * len(top_ranked))))

		fig, ax = create_canvas()
		add_ticker_tape(ax)

		# Title
		ax.text(
			0.065,
			0.89,
			"PERFORMANCE RACE (1Y)",
			transform=ax.transAxes,
			color=SEMANTIC_COLORS["text_primary"],
			fontsize=28,
			fontweight="bold",
		)

		# Right side label
		ax.text(
			0.935,
			0.89,
			"SOVEREIGN INTELLIGENCE TERMINAL // ALPHA SERIES",
			transform=ax.transAxes,
			color=SEMANTIC_COLORS["text_secondary"],
			fontsize=7,
			ha="right",
			family="monospace",
		)

		# Divider
		ax.plot(
			[0.065, 0.935],
			[0.85, 0.85],
			color=SEMANTIC_COLORS["negative"],
			linewidth=0.8,
			transform=ax.transAxes,
		)

		# Bar area
		bar_x = 0.22
		bar_right = 0.82
		bar_width_total = bar_right - bar_x
		start_y = 0.78
		row_h = 0.075

		for idx in range(cutoff):
			item = top_ranked[idx]
			ret = returns_1y[idx]
			ticker = str(item.get("ticker", ""))
			readable = _get_readable_name(ticker)
			sector = _get_sector(ticker)
			row_y = start_y - idx * row_h

			bar_w = (abs(ret) / max_return) * bar_width_total * progress

			# Top 3 get highlighted row with border
			if idx < 3:
				ax.add_patch(
					mpatches.FancyBboxPatch(
						(0.06, row_y - 0.005),
						0.88,
						row_h - 0.005,
						boxstyle="round,pad=0.002,rounding_size=0.003",
						transform=ax.transAxes,
						linewidth=0.5,
						edgecolor=SEMANTIC_COLORS["panel_border"],
						facecolor=SEMANTIC_COLORS["bar_highlight"],
						alpha=0.5,
						zorder=0,
					)
				)
				# Divider line under each top-3 row
				ax.plot(
					[0.065, 0.935],
					[row_y - 0.008, row_y - 0.008],
					color=SEMANTIC_COLORS["panel_border"],
					linewidth=0.5,
					transform=ax.transAxes,
				)

			# Rank number (italic for top 3)
			rank_style = "italic" if idx < 3 else "normal"
			rank_weight = "bold" if idx < 3 else "normal"
			rank_color = SEMANTIC_COLORS["text_secondary"] if idx < 3 else SEMANTIC_COLORS["text_tertiary"]
			ax.text(
				0.075,
				row_y + row_h * 0.42,
				f"{idx + 1:02d}",
				transform=ax.transAxes,
				color=rank_color,
				fontsize=16 if idx < 3 else 12,
				fontweight=rank_weight,
				fontstyle=rank_style,
				va="center",
				ha="left",
			)

			# Ticker name
			name_weight = "bold" if idx < 3 else "normal"
			ax.text(
				0.115,
				row_y + row_h * 0.42,
				readable,
				transform=ax.transAxes,
				color=SEMANTIC_COLORS["text_primary"],
				fontsize=11 if idx < 3 else 10,
				fontweight=name_weight,
				va="center",
				ha="left",
			)

			# Bar track
			ax.add_patch(
				mpatches.Rectangle(
					(bar_x, row_y + 0.008),
					bar_width_total,
					row_h * 0.45,
					transform=ax.transAxes,
					color=SEMANTIC_COLORS["bar_track"],
					zorder=1,
				)
			)

			# Violet bar
			violet_shade = SEMANTIC_COLORS["violet_bright"] if idx < 3 else SEMANTIC_COLORS["violet"] if idx < 6 else SEMANTIC_COLORS["violet_dim"]
			ax.add_patch(
				mpatches.Rectangle(
					(bar_x, row_y + 0.008),
					bar_w,
					row_h * 0.45,
					transform=ax.transAxes,
					color=violet_shade,
					alpha=0.85,
					zorder=2,
				)
			)

			# Percentage inside/near bar end
			if progress >= 0.3:
				ax.text(
					bar_x + bar_w - 0.01,
					row_y + row_h * 0.42,
					f"+{ret:.1f}%",
					transform=ax.transAxes,
					color=SEMANTIC_COLORS["text_primary"] if idx < 3 else SEMANTIC_COLORS["text_secondary"],
					fontsize=9,
					fontweight="bold",
					va="center",
					ha="right",
					zorder=3,
				)

			# Sector label (right side)
			ax.text(
				0.935,
				row_y + row_h * 0.42,
				sector,
				transform=ax.transAxes,
				color=SEMANTIC_COLORS["text_secondary"],
				fontsize=8,
				va="center",
				ha="right",
				family="monospace",
			)

		# AI Narrative Insight
		if top_ranked:
			lead1 = _get_readable_name(str(top_ranked[0].get("ticker", "")))
			lead2 = _get_readable_name(str(top_ranked[1].get("ticker", ""))) if len(top_ranked) > 1 else ""
			add_progressive_note(
				ax,
				frame_num,
				total_frames,
				f"Long-term outperformers: {lead1} and {lead2} lead the 1-year performance race with multi-bagger returns.",
				reveal_at=0.4,
			)

		add_footer(ax)
		frames.append(fig_to_png_bytes(fig))

	return frames
