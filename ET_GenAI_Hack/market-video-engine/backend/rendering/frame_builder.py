"""Reusable frame-building primitives for Sovereign Analyst Terminal."""

from __future__ import annotations

from io import BytesIO
from typing import Any

import matplotlib

matplotlib.use("Agg", force=True)

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

from rendering.color_themes import SEMANTIC_COLORS, pick_change_color, pick_bar_color, signed_text


# ── Ticker name → readable name mapping (for gainers/losers display) ──
TICKER_SECTORS: dict[str, str] = {
	"RELIANCE": "ENERGY",
	"TCS": "IT",
	"HDFCBANK": "BFSI",
	"INFY": "IT",
	"ICICIBANK": "BFSI",
	"HINDUNILVR": "FMCG",
	"ITC": "FMCG",
	"KOTAKBANK": "BFSI",
	"LT": "INFRA",
	"BAJFINANCE": "BFSI",
	"SBIN": "BFSI",
	"WIPRO": "IT",
	"AXISBANK": "BFSI",
	"MARUTI": "AUTOMOTIVE",
	"ULTRACEMCO": "INFRA",
	"TITAN": "CONSUMER",
	"ASIANPAINT": "CONSUMER",
	"SUNPHARMA": "PHARMA",
	"TATAMOTORS": "AUTOMOTIVE",
	"ONGC": "ENERGY",
	"NESTLEIND": "FMCG",
	"BHARTIARTL": "TELECOM",
	"POWERGRID": "ENERGY",
	"NTPC": "ENERGY",
	"ADANIENT": "ENERGY",
	"ADANIPORTS": "INFRA",
	"TATASTEEL": "METAL",
	"JSWSTEEL": "METAL",
	"BAJAJFINSV": "BFSI",
	"TECHM": "IT",
	"HCLTECH": "IT",
	"DRREDDY": "PHARMA",
	"DIVISLAB": "PHARMA",
	"BRITANNIA": "FMCG",
	"ZOMATO": "TECH",
	"APOLLOHOSP": "HEALTH",
	"HAL": "DEFENSE",
	"TRENT": "RETAIL",
}

TICKER_READABLE: dict[str, str] = {
	"RELIANCE": "RELIANCE",
	"TCS": "TCS",
	"HDFCBANK": "HDFC BANK",
	"INFY": "INFOSYS",
	"ICICIBANK": "ICICI BANK",
	"HINDUNILVR": "HUL",
	"ITC": "ITC",
	"KOTAKBANK": "KOTAK BANK",
	"LT": "L&T",
	"BAJFINANCE": "BAJAJ FINANCE",
	"SBIN": "SBI",
	"WIPRO": "WIPRO",
	"AXISBANK": "AXIS BANK",
	"MARUTI": "MARUTI",
	"ULTRACEMCO": "ULTRATECH",
	"TITAN": "TITAN",
	"ASIANPAINT": "ASIAN PAINTS",
	"SUNPHARMA": "SUN PHARMA",
	"TATAMOTORS": "TATA MOTORS",
	"ONGC": "ONGC",
	"NESTLEIND": "NESTLE",
	"BHARTIARTL": "BHARTI AIRTEL",
	"POWERGRID": "POWER GRID",
	"NTPC": "NTPC",
	"ADANIENT": "ADANI ENT",
	"ADANIPORTS": "ADANI PORTS",
	"TATASTEEL": "TATA STEEL",
	"JSWSTEEL": "JSW STEEL",
	"BAJAJFINSV": "BAJAJ FINSERV",
	"TECHM": "TECH MAHINDRA",
	"HCLTECH": "HCL TECH",
	"DRREDDY": "DR REDDY",
	"DIVISLAB": "DIVIS LAB",
	"BRITANNIA": "BRITANNIA",
	"ZOMATO": "ZOMATO",
	"APOLLOHOSP": "APOLLO HOSP",
	"HAL": "HAL",
	"TRENT": "TRENT",
}


def _get_sector(ticker: str) -> str:
	"""Get sector for a ticker symbol."""
	clean = str(ticker).replace(".NS", "").strip().upper()
	return TICKER_SECTORS.get(clean, "MARKET")


def _get_readable_name(ticker: str) -> str:
	"""Get human-readable name for a ticker symbol."""
	clean = str(ticker).replace(".NS", "").strip().upper()
	return TICKER_READABLE.get(clean, clean)


def create_canvas(width: int = 16, height: int = 9, dpi: int = 100) -> tuple[Any, Any]:
	"""Returns a standardized near-black Sovereign Analyst canvas."""
	fig = plt.figure(figsize=(width, height), dpi=dpi)
	ax = fig.add_axes([0, 0, 1, 1])
	fig.patch.set_facecolor(SEMANTIC_COLORS["background"])
	ax.set_facecolor(SEMANTIC_COLORS["background"])
	ax.axis("off")
	return fig, ax


def add_top_banner(ax: Any, title: str, subtitle: str | None = None) -> None:
	"""Now uses the Sovereign Analyst ticker tape + section header."""
	from rendering.text_overlay import add_ticker_tape, add_section_header
	add_ticker_tape(ax)
	add_section_header(ax, title, subtitle)


def add_info_panel(
	ax: Any,
	x: float,
	y: float,
	w: float,
	h: float,
	title: str,
	value: str,
	delta: float | None = None,
) -> None:
	"""Draws a brutalist info panel with mega typography."""
	# Panel background with border
	ax.add_patch(
		mpatches.FancyBboxPatch(
			(x, y),
			w,
			h,
			boxstyle="round,pad=0.005,rounding_size=0.005",
			transform=ax.transAxes,
			linewidth=0.8,
			edgecolor=SEMANTIC_COLORS["panel_border"],
			facecolor=SEMANTIC_COLORS["panel"],
			zorder=1,
		)
	)

	# Horizontal accent line at top of panel
	ax.plot(
		[x + 0.01, x + w - 0.01],
		[y + h - 0.005, y + h - 0.005],
		color=SEMANTIC_COLORS["text_secondary"],
		linewidth=0.5,
		transform=ax.transAxes,
		alpha=0.4,
		zorder=2,
	)

	# Title label (uppercase, letter-spaced)
	ax.text(
		x + 0.02,
		y + h - 0.04,
		title.upper(),
		transform=ax.transAxes,
		color=SEMANTIC_COLORS["text_secondary"],
		fontsize=10,
		fontweight="bold",
		ha="left",
		va="center",
		family="monospace",
		zorder=2,
	)

	# Mega value
	ax.text(
		x + 0.02,
		y + h * 0.42,
		value,
		transform=ax.transAxes,
		color=SEMANTIC_COLORS["text_primary"],
		fontsize=36,
		fontweight="bold",
		ha="left",
		va="center",
		zorder=2,
	)

	if delta is not None:
		color = pick_change_color(delta)
		ax.text(
			x + 0.02,
			y + 0.06,
			signed_text(delta),
			transform=ax.transAxes,
			color=color,
			fontsize=14,
			fontweight="bold",
			ha="left",
			va="center",
			zorder=2,
		)


def add_ranked_bar_block(
	ax: Any,
	items: list[dict[str, Any]],
	title: str,
	x: float,
	y: float,
	width: float,
	row_height: float,
	frame_num: int,
	total_frames: int,
	value_key: str = "change_pct",
	label_key: str = "ticker",
	bar_context: str = "default",
) -> None:
	"""Draws Sovereign Analyst numbered rank rows with sector tags and volume.

	Layout per row:
	  [rank_num]  [TICKER_NAME]  [SECTOR_BADGE]                [+X.XX%]  VOL: X.XM
	  [============================bar============================]
	"""
	if not items:
		return

	progress = min(frame_num / max(total_frames * 0.6, 1), 1.0)
	max_abs_value = max(abs(float(item.get(value_key, 0.0))) for item in items) or 1.0

	# Bar area config
	bar_x = 0.065
	bar_right = 0.93
	bar_width_total = bar_right - bar_x

	for idx, item in enumerate(items):
		raw_val = float(item.get(value_key, 0.0))
		bar_w = (abs(raw_val) / max_abs_value) * bar_width_total * progress
		row_y = y + row_height * (len(items) - idx - 1)
		ticker = str(item.get(label_key, ""))
		readable = _get_readable_name(ticker)
		sector = _get_sector(ticker)
		volume = item.get("volume", None)

		# Row highlight for top 3
		if idx < 3:
			ax.add_patch(
				mpatches.Rectangle(
					(0.06, row_y - 0.01),
					0.88,
					row_height - 0.005,
					transform=ax.transAxes,
					color=SEMANTIC_COLORS["bar_highlight"],
					alpha=0.4,
					zorder=0,
				)
			)

		# Rank number (italic, large, muted)
		rank_style = "italic" if idx < 3 else "normal"
		rank_color = SEMANTIC_COLORS["text_secondary"] if idx < 3 else SEMANTIC_COLORS["text_tertiary"]
		ax.text(
			0.07,
			row_y + row_height * 0.58,
			f"{idx + 1:02d}",
			transform=ax.transAxes,
			color=rank_color,
			fontsize=18 if idx < 3 else 14,
			fontweight="bold",
			fontstyle=rank_style,
			va="center",
			ha="left",
			zorder=3,
		)

		# Ticker name (bold)
		ax.text(
			0.11,
			row_y + row_height * 0.68,
			readable,
			transform=ax.transAxes,
			color=SEMANTIC_COLORS["text_primary"],
			fontsize=12,
			fontweight="bold",
			va="center",
			ha="left",
			zorder=3,
		)

		# Sector badge
		ax.text(
			0.11,
			row_y + row_height * 0.42,
			sector,
			transform=ax.transAxes,
			color=SEMANTIC_COLORS["badge_text"],
			fontsize=7,
			va="center",
			ha="left",
			family="monospace",
			zorder=3,
		)

		# Percentage value (right-aligned)
		pct_color = pick_change_color(raw_val) if bar_context != "loser" else SEMANTIC_COLORS["negative"]
		if progress >= 0.3:
			ax.text(
				0.88,
				row_y + row_height * 0.68,
				signed_text(raw_val),
				transform=ax.transAxes,
				color=pct_color,
				fontsize=14,
				fontweight="bold",
				va="center",
				ha="right",
				zorder=3,
			)

		# Volume text (if available)
		if volume and progress >= 0.4:
			vol_str = f"VOL: {float(volume)/1e6:.1f}M" if float(volume) > 1e6 else f"VOL: {volume}"
			ax.text(
				0.93,
				row_y + row_height * 0.68,
				vol_str,
				transform=ax.transAxes,
				color=SEMANTIC_COLORS["text_secondary"],
				fontsize=7,
				va="center",
				ha="right",
				family="monospace",
				zorder=3,
			)

		# Bar track (background)
		ax.add_patch(
			mpatches.Rectangle(
				(bar_x, row_y + 0.005),
				bar_width_total,
				row_height * 0.32,
				transform=ax.transAxes,
				color=SEMANTIC_COLORS["bar_track"],
				zorder=1,
			)
		)

		# Animated bar fill
		if bar_context == "loser":
			bar_color = pick_bar_color(raw_val, "loser")
		elif bar_context == "race":
			bar_color = pick_bar_color(raw_val, "race")
		else:
			bar_color = SEMANTIC_COLORS["positive"]

		ax.add_patch(
			mpatches.Rectangle(
				(bar_x, row_y + 0.005),
				bar_w,
				row_height * 0.32,
				transform=ax.transAxes,
				color=bar_color,
				alpha=0.85,
				zorder=2,
			)
		)


def add_bidirectional_bars(
	ax: Any,
	items: list[dict[str, Any]],
	frame_num: int,
	total_frames: int,
	name_key: str = "sector",
	value_key: str = "change_pct",
) -> None:
	"""Draws bidirectional horizontal bars from center zero-line for sector rotation.

	Positive bars extend right, negative bars extend left.
	Percentage text is displayed INSIDE the bars.
	"""
	if not items:
		return

	progress = min(frame_num / max(total_frames * 0.6, 1), 1.0)
	max_abs = max(abs(float(item.get(value_key, 0.0))) for item in items) or 1.0

	# Layout constants
	center_x = 0.50  # zero line position
	bar_half_width = 0.35  # max extent from center
	start_y = 0.70
	row_h = 0.078
	bar_h = 0.045

	# Header scale labels
	for pct_val, label_x in [(-3.0, center_x - bar_half_width), (-1.5, center_x - bar_half_width * 0.5),
							  (0.0, center_x), (1.5, center_x + bar_half_width * 0.5), (3.0, center_x + bar_half_width)]:
		label_text = f"{pct_val:+.1f}%" if pct_val != 0 else "0.0% BASE"
		ax.text(
			label_x,
			0.79,
			label_text,
			transform=ax.transAxes,
			color=SEMANTIC_COLORS["text_secondary"],
			fontsize=7,
			va="center",
			ha="center",
			family="monospace",
		)

	# Zero line
	ax.plot(
		[center_x, center_x],
		[start_y - len(items) * row_h, start_y + 0.02],
		color=SEMANTIC_COLORS["text_secondary"],
		linewidth=0.5,
		transform=ax.transAxes,
		alpha=0.3,
	)

	for idx, item in enumerate(items):
		val = float(item.get(value_key, 0.0))
		name = str(item.get(name_key, ""))
		bar_y = start_y - idx * row_h

		# Animated bar width
		normalized = (abs(val) / max_abs) * bar_half_width * progress

		if val >= 0:
			# Positive: bar extends right from center
			bar_start = center_x
			bar_color = SEMANTIC_COLORS["positive"]
			# Sector name on left of center
			ax.text(
				center_x - 0.02,
				bar_y + bar_h / 2,
				name.upper(),
				transform=ax.transAxes,
				color=SEMANTIC_COLORS["text_primary"],
				fontsize=11,
				fontweight="bold",
				va="center",
				ha="right",
			)
			# Percentage inside bar
			if progress >= 0.3:
				ax.text(
					center_x + 0.01,
					bar_y + bar_h / 2,
					signed_text(val),
					transform=ax.transAxes,
					color=SEMANTIC_COLORS["text_secondary"],
					fontsize=9,
					fontweight="bold",
					va="center",
					ha="left",
					zorder=3,
				)
		else:
			# Negative: bar extends left from center
			bar_start = center_x - normalized
			bar_color = SEMANTIC_COLORS["negative_soft"]
			# Sector name on right of center
			ax.text(
				center_x + 0.02,
				bar_y + bar_h / 2,
				name.upper(),
				transform=ax.transAxes,
				color=SEMANTIC_COLORS["text_secondary"],
				fontsize=11,
				fontweight="bold",
				va="center",
				ha="left",
			)
			# Percentage inside bar
			if progress >= 0.3:
				ax.text(
					center_x - 0.01,
					bar_y + bar_h / 2,
					signed_text(val),
					transform=ax.transAxes,
					color=SEMANTIC_COLORS["negative"],
					fontsize=9,
					fontweight="bold",
					va="center",
					ha="right",
					zorder=3,
				)

		# Bar track
		ax.add_patch(
			mpatches.Rectangle(
				(center_x - bar_half_width, bar_y),
				bar_half_width * 2,
				bar_h,
				transform=ax.transAxes,
				color=SEMANTIC_COLORS["bar_track"],
				alpha=0.3,
			)
		)

		# Actual bar
		ax.add_patch(
			mpatches.Rectangle(
				(bar_start, bar_y),
				normalized,
				bar_h,
				transform=ax.transAxes,
				color=bar_color,
				alpha=0.75,
				zorder=2,
			)
		)


def fig_to_png_bytes(fig: Any) -> bytes:
	"""Serializes a Matplotlib figure to PNG bytes and closes it safely."""
	buffer = BytesIO()
	try:
		fig.savefig(buffer, format="png", dpi=fig.dpi)
		buffer.seek(0)
		return buffer.read()
	finally:
		plt.close(fig)
		buffer.close()
