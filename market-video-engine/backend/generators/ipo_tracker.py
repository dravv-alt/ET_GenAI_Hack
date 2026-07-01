"""Generates IPO tracker and outro segment frames.

Sovereign Analyst Terminal design:
- IPO Tracker: subscription bars with labels
- Outro: branded closing slate
"""

from __future__ import annotations

from typing import Any

import re

import numpy as np

try:
	import seaborn as sns
except Exception:  # pragma: no cover
	sns = None

import matplotlib.patches as mpatches

from rendering.color_themes import SEMANTIC_COLORS
from rendering.frame_builder import create_canvas, fig_to_png_bytes
from rendering.text_overlay import (
	add_footer,
	add_progressive_note,
	add_section_header,
	add_ticker_tape,
	add_watermark,
)


def _extract_number(text: Any) -> float:
	raw = str(text or "")
	match = re.search(r"[-+]?\d+(?:\.\d+)?", raw)
	if not match:
		return 0.0
	try:
		return float(match.group(0))
	except ValueError:
		return 0.0


def generate_ipo_tracker_frames(snapshot: dict[str, Any], total_frames: int = 10) -> list[bytes]:
	"""Builds Sovereign Analyst IPO tracker frames.

	Layout:
	  [MARKET ANALYTICS ticker tape]
	  IPO TRACKER
	  PRIMARY MARKET PULSE

	  [IPO_NAME_1]       SUBSCRIPTION: [====bar====] 4.1x
	  Band: ₹XXX-XXX     GMP: +XX%

	  [IPO_NAME_2]       SUBSCRIPTION: [===bar===] 2.8x
	  ...

	  [AI NARRATIVE INSIGHT]
	  SOVEREIGN ANALYST TERMINAL
	"""
	ipos = list(snapshot.get("ipos", []))

	frames: list[bytes] = []
	for frame_num in range(total_frames):
		progress = min(frame_num / max(total_frames * 0.65, 1), 1.0)
		fig, ax = create_canvas()

		add_ticker_tape(ax)
		add_section_header(ax, "IPO TRACKER", "PRIMARY MARKET PULSE // SUBSCRIPTION DATA")

		# IPO listings
		max_sub = max((_extract_number(ipo.get("subscription", "0")) for ipo in ipos[:5]), default=1) or 1

		for idx, ipo in enumerate(ipos[:5]):
			base_y = 0.72 - idx * 0.12
			name = str(ipo.get("name", ""))
			sub_val = _extract_number(ipo.get("subscription", "0"))
			band = str(ipo.get("price_band", ""))
			gmp = str(ipo.get("gmp", ""))
			gmp_val = _extract_number(gmp)

			# IPO name (bold)
			ax.text(
				0.065,
				base_y,
				name.upper(),
				transform=ax.transAxes,
				color=SEMANTIC_COLORS["text_primary"],
				fontsize=14,
				fontweight="bold",
			)

			# Band and GMP below name
			ax.text(
				0.065,
				base_y - 0.035,
				f"BAND: {band}",
				transform=ax.transAxes,
				color=SEMANTIC_COLORS["text_secondary"],
				fontsize=8,
				family="monospace",
			)
			gmp_color = "#00C853" if gmp_val >= 0 else SEMANTIC_COLORS["negative"]
			ax.text(
				0.25,
				base_y - 0.035,
				f"GMP: {gmp}",
				transform=ax.transAxes,
				color=gmp_color,
				fontsize=8,
				family="monospace",
			)

			# Subscription bar
			bar_x = 0.65
			bar_width_max = 0.25
			bar_w = (sub_val / max_sub) * bar_width_max * progress

			# Bar track
			ax.add_patch(
				mpatches.Rectangle(
					(bar_x, base_y - 0.015),
					bar_width_max,
					0.035,
					transform=ax.transAxes,
					color=SEMANTIC_COLORS["bar_track"],
				)
			)

			# Bar fill
			ax.add_patch(
				mpatches.Rectangle(
					(bar_x, base_y - 0.015),
					bar_w,
					0.035,
					transform=ax.transAxes,
					color=SEMANTIC_COLORS["positive"],
					alpha=0.7,
				)
			)

			# SUBSCRIPTION label
			ax.text(
				0.65,
				base_y + 0.005,
				"SUBSCRIPTION",
				transform=ax.transAxes,
				color=SEMANTIC_COLORS["text_secondary"],
				fontsize=7,
				family="monospace",
			)

			# Subscription value at end of bar
			if progress >= 0.3:
				ax.text(
					bar_x + bar_w + 0.01,
					base_y - 0.0,
					f"{sub_val:.1f}x",
					transform=ax.transAxes,
					color=SEMANTIC_COLORS["text_primary"],
					fontsize=10,
					fontweight="bold",
				)

		# AI Narrative Insight
		add_progressive_note(
			ax,
			frame_num,
			total_frames,
			"IPO demand trends can influence listing-day sentiment and liquidity flows across the broader market.",
			reveal_at=0.45,
		)

		add_footer(ax)
		frames.append(fig_to_png_bytes(fig))

	return frames


def generate_outro_frames(snapshot: dict[str, Any], total_frames: int = 8) -> list[bytes]:
	"""Builds Sovereign Analyst closing slate frames.

	Layout:
	  [MARKET ANALYTICS ticker tape]

	           SOVEREIGN ANALYST TERMINAL
	           SESSION ANALYSIS COMPLETE

	           Nifty: 22,123.45 | Change: +1.2%

	           SYSTEM STATUS: OPTIMAL
	           Will be back with more updates.

	  SOVEREIGN ANALYST TERMINAL | DATE | SYSTEM STATUS
	"""
	nifty = dict(snapshot.get("nifty", {}))
	close_val = nifty.get("close", "")
	change_pct = nifty.get("change_pct", "")

	frames: list[bytes] = []
	for frame_num in range(total_frames):
		fig, ax = create_canvas()

		add_ticker_tape(ax)

		# Center content
		ax.text(
			0.5,
			0.62,
			"SOVEREIGN ANALYST TERMINAL",
			transform=ax.transAxes,
			color=SEMANTIC_COLORS["text_primary"],
			fontsize=28,
			fontweight="bold",
			ha="center",
			family="monospace",
		)

		ax.text(
			0.5,
			0.54,
			"SESSION ANALYSIS COMPLETE",
			transform=ax.transAxes,
			color=SEMANTIC_COLORS["text_secondary"],
			fontsize=14,
			ha="center",
			family="monospace",
		)

		# Divider
		ax.plot(
			[0.35, 0.65],
			[0.49, 0.49],
			color=SEMANTIC_COLORS["panel_border"],
			linewidth=0.8,
			transform=ax.transAxes,
		)

		ax.text(
			0.5,
			0.44,
			f"Nifty: {close_val} | Change: {change_pct}%",
			transform=ax.transAxes,
			color=SEMANTIC_COLORS["text_secondary"],
			fontsize=12,
			ha="center",
		)

		ax.text(
			0.5,
			0.36,
			"Track momentum, flows, and IPO demand for tomorrow's setup",
			transform=ax.transAxes,
			color=SEMANTIC_COLORS["text_secondary"],
			fontsize=10,
			ha="center",
			family="monospace",
		)

		add_footer(ax)
		frames.append(fig_to_png_bytes(fig))

	return frames
