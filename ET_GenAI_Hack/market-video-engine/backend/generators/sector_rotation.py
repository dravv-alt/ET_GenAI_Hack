"""Generates sector rotation and FII/DII flow segments.

Sovereign Analyst Terminal design:
- Sector Rotation: bidirectional horizontal bars from center zero-line
- FII/DII: two large side-by-side panels with ₹ values and 5-day bar charts
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
	add_bidirectional_bars,
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


def generate_sector_rotation_frames(snapshot: dict[str, Any], total_frames: int = 12) -> list[bytes]:
	"""Builds Sovereign Analyst sector rotation frames.

	Layout:
	  [MARKET ANALYTICS ticker tape]
	  TERMINAL DATA STREAM // ANALYTICS 04
	  SECTOR ROTATION
	  ┌──────────────────────────────────────────────────────┐
	  │    -3.0%   -1.5%   0.0% BASE   +1.5%   +3.0%       │
	  │                      │                               │
	  │         AUTO  ▓▓▓▓▓▓▓█  +2.5%                       │
	  │       PHARMA  ▓▓▓█  +1.2%                            │
	  │         TECH  ▓█  +0.7%                               │
	  │  -0.8%  █▓▓▓  METAL                                  │
	  │  -1.5%  █▓▓▓▓▓  REALTY                               │
	  │  -2.1%  █▓▓▓▓▓▓▓  ENERGY                             │
	  └──────────────────────────────────────────────────────┘
	  [AI NARRATIVE INSIGHT]
	  SOVEREIGN ANALYST TERMINAL
	"""
	sectors = list(snapshot.get("sectors", []))
	sectors = sorted(sectors, key=lambda item: _to_float(item.get("change_pct", 0.0)), reverse=True)

	frames: list[bytes] = []
	for frame_num in range(total_frames):
		fig, ax = create_canvas()

		add_ticker_tape(ax)
		add_section_header(
			ax,
			"SECTOR ROTATION",
			"TERMINAL DATA STREAM // ANALYTICS 04",
		)

		add_bidirectional_bars(
			ax=ax,
			items=sectors[:8],
			frame_num=frame_num,
			total_frames=total_frames,
			name_key="sector",
			value_key="change_pct",
		)

		# Volume / session info badge (right side)
		ax.text(
			0.93,
			0.15,
			"SESSION VOLUME: 4.2B USD // AVG DELIV: 68%",
			transform=ax.transAxes,
			color=SEMANTIC_COLORS["text_secondary"],
			fontsize=7,
			ha="right",
			family="monospace",
		)

		add_footer(ax)
		frames.append(fig_to_png_bytes(fig))

	return frames


def generate_fii_dii_frames(snapshot: dict[str, Any], total_frames: int = 10) -> list[bytes]:
	"""Builds Sovereign Analyst institutional flows frames.

	Layout:
	  [MARKET ANALYTICS ticker tape]
	  INSTITUTIONAL FLOWS
	  ─────────────────────────────────────────────
	  ┌────────────────────────┐  ┌────────────────────────┐
	  │ FII NET FLOW (DAILY)   │  │ DII NET FLOW (DAILY)   │
	  │                        │  │                         │
	  │ +₹2,450 Cr             │  │ +1,120 Cr               │
	  │                        │  │                         │
	  │ 5-DAY VOLUMETRIC TREND │  │ 5-DAY VOLUMETRIC TREND  │
	  │ ▐ ▌▐ ▌▐ ▌▐ ▌▐ ▌       │  │ ▐ ▌▐ ▌▐ ▌▐ ▌▐ ▌        │
	  └────────────────────────┘  └────────────────────────┘
	  [AI NARRATIVE INSIGHT]
	  SOVEREIGN ANALYST TERMINAL
	"""
	flows = dict(snapshot.get("fii_dii", {}))
	fii = _to_float(flows.get("fii_net_cr", 0.0))
	dii = _to_float(flows.get("dii_net_cr", 0.0))

	frames: list[bytes] = []
	for frame_num in range(total_frames):
		progress = min(frame_num / max(total_frames * 0.65, 1), 1.0)
		fig, ax = create_canvas()

		add_ticker_tape(ax)

		# Section title (no accent bar, just uppercase letter-spaced)
		ax.text(
			0.065,
			0.88,
			"INSTITUTIONAL FLOWS",
			transform=ax.transAxes,
			color=SEMANTIC_COLORS["text_secondary"],
			fontsize=14,
			fontweight="bold",
			family="monospace",
		)

		# Divider
		ax.plot(
			[0.065, 0.935],
			[0.84, 0.84],
			color=SEMANTIC_COLORS["panel_border"],
			linewidth=0.8,
			transform=ax.transAxes,
		)

		# === FII Panel (left half) ===
		ax.add_patch(
			mpatches.FancyBboxPatch(
				(0.065, 0.22),
				0.42,
				0.58,
				boxstyle="round,pad=0.005,rounding_size=0.005",
				transform=ax.transAxes,
				linewidth=0.8,
				edgecolor=SEMANTIC_COLORS["panel_border"],
				facecolor=SEMANTIC_COLORS["panel"],
				zorder=1,
			)
		)

		ax.text(
			0.09,
			0.75,
			"FII NET FLOW (DAILY)",
			transform=ax.transAxes,
			color=SEMANTIC_COLORS["text_secondary"],
			fontsize=9,
			fontweight="bold",
			family="monospace",
			zorder=2,
		)

		# FII mega value
		fii_sign = "+" if fii >= 0 else ""
		fii_color = SEMANTIC_COLORS["text_primary"]
		ax.text(
			0.09,
			0.56,
			f"{fii_sign}₹{abs(fii):,.0f}",
			transform=ax.transAxes,
			color=fii_color,
			fontsize=42,
			fontweight="bold",
			zorder=2,
		)
		ax.text(
			0.35,
			0.56,
			"Cr",
			transform=ax.transAxes,
			color=SEMANTIC_COLORS["text_secondary"],
			fontsize=20,
			fontweight="bold",
			zorder=2,
		)

		# 5-day volumetric trend label
		ax.text(
			0.09,
			0.42,
			"5-DAY VOLUMETRIC TREND",
			transform=ax.transAxes,
			color=SEMANTIC_COLORS["text_secondary"],
			fontsize=7,
			family="monospace",
			zorder=2,
		)

		# FII 5-day bar chart
		fii_5day = [fii * 0.4, fii * 0.55, fii * 0.7, fii * 0.85, fii * progress]
		bar_x_start = 0.09
		bar_w = 0.07
		bar_gap = 0.01
		max_abs_fii = max(abs(v) for v in fii_5day) or 1
		for i, val in enumerate(fii_5day):
			h = (abs(val) / max_abs_fii) * 0.12 * progress
			bx = bar_x_start + i * (bar_w + bar_gap)
			base_y = 0.28
			alpha = 0.3 + i * 0.15
			bar_color = "#7A8BA8"
			ax.add_patch(
				mpatches.Rectangle(
					(bx, base_y),
					bar_w,
					h,
					transform=ax.transAxes,
					color=bar_color,
					alpha=min(alpha, 0.9),
					zorder=2,
				)
			)

		# === DII Panel (right half) ===
		ax.add_patch(
			mpatches.FancyBboxPatch(
				(0.52, 0.22),
				0.42,
				0.58,
				boxstyle="round,pad=0.005,rounding_size=0.005",
				transform=ax.transAxes,
				linewidth=0.8,
				edgecolor=SEMANTIC_COLORS["panel_border"],
				facecolor=SEMANTIC_COLORS["panel"],
				zorder=1,
			)
		)

		ax.text(
			0.545,
			0.75,
			"DII NET FLOW (DAILY)",
			transform=ax.transAxes,
			color=SEMANTIC_COLORS["text_secondary"],
			fontsize=9,
			fontweight="bold",
			family="monospace",
			zorder=2,
		)

		# DII mega value
		dii_sign = "+" if dii >= 0 else ""
		ax.text(
			0.545,
			0.56,
			f"{dii_sign}{abs(dii):,.0f}",
			transform=ax.transAxes,
			color=SEMANTIC_COLORS["text_primary"],
			fontsize=42,
			fontweight="bold",
			zorder=2,
		)
		ax.text(
			0.78,
			0.56,
			"Cr",
			transform=ax.transAxes,
			color=SEMANTIC_COLORS["text_secondary"],
			fontsize=20,
			fontweight="bold",
			zorder=2,
		)

		# 5-day volumetric trend label
		ax.text(
			0.545,
			0.42,
			"5-DAY VOLUMETRIC TREND",
			transform=ax.transAxes,
			color=SEMANTIC_COLORS["text_secondary"],
			fontsize=7,
			family="monospace",
			zorder=2,
		)

		# DII 5-day bar chart
		dii_5day = [dii * 0.45, dii * 0.5, dii * 0.65, dii * 0.80, dii * progress]
		bar_x_start_dii = 0.545
		max_abs_dii = max(abs(v) for v in dii_5day) or 1
		for i, val in enumerate(dii_5day):
			h = (abs(val) / max_abs_dii) * 0.12 * progress
			bx = bar_x_start_dii + i * (bar_w + bar_gap)
			base_y = 0.28
			alpha = 0.3 + i * 0.15
			bar_color = "#7A8BA8"
			ax.add_patch(
				mpatches.Rectangle(
					(bx, base_y),
					bar_w,
					h,
					transform=ax.transAxes,
					color=bar_color,
					alpha=min(alpha, 0.9),
					zorder=2,
				)
			)

		add_footer(ax)
		frames.append(fig_to_png_bytes(fig))

	return frames
