"""Text overlay helpers for Sovereign Analyst Terminal frames."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from rendering.color_themes import SEMANTIC_COLORS


# ── Global market indices for the ticker tape ─────────────────────
GLOBAL_TICKERS = [
	("S&P 500", "+1.2%"),
	("NASDAQ", "+0.8%"),
	("DOW", "-0.2%"),
	("GOLD", "+0.5%"),
	("BTC", "+2.1%"),
]


def add_ticker_tape(ax: Any) -> None:
	"""Draws the top ticker tape with global indices and LIVE UPDATE badge."""
	# "MARKET ANALYTICS" branding
	ax.text(
		0.065,
		0.962,
		"MARKET ANALYTICS",
		transform=ax.transAxes,
		color=SEMANTIC_COLORS["text_primary"],
		fontsize=14,
		fontweight="bold",
		va="center",
		ha="left",
		family="monospace",
	)

	# Global tickers
	x_start = 0.24
	for ticker_name, ticker_val in GLOBAL_TICKERS:
		color = "#6B7A94" if ticker_val.startswith("+") else "#E86464"
		ax.text(
			x_start,
			0.962,
			f"{ticker_name} {ticker_val}",
			transform=ax.transAxes,
			color=color,
			fontsize=9,
			va="center",
			ha="left",
		)
		x_start += 0.09

	# LIVE UPDATE badge
	ax.plot(
		0.895,
		0.962,
		marker="s",
		markersize=5,
		color=SEMANTIC_COLORS["live_dot"],
		transform=ax.transAxes,
		zorder=10,
	)
	ax.text(
		0.905,
		0.962,
		"LIVE UPDATE",
		transform=ax.transAxes,
		color=SEMANTIC_COLORS["text_primary"],
		fontsize=9,
		fontweight="bold",
		va="center",
		ha="left",
		style="normal",
	)


def add_section_header(
	ax: Any,
	title: str,
	subtitle: str | None = None,
	y: float = 0.87,
) -> None:
	"""Draws a massive section title with left accent bar and optional subtitle."""
	import matplotlib.patches as mpatches

	# Accent bar (vertical left stripe)
	ax.add_patch(
		mpatches.Rectangle(
			(0.065, y - 0.01),
			0.005,
			0.065,
			transform=ax.transAxes,
			color=SEMANTIC_COLORS["text_secondary"],
			zorder=3,
		)
	)

	# Title text (massive condensed bold)
	ax.text(
		0.08,
		y + 0.035,
		title,
		transform=ax.transAxes,
		color=SEMANTIC_COLORS["text_primary"],
		fontsize=38,
		fontweight="bold",
		va="center",
		ha="left",
	)

	# Subtitle (letter-spaced uppercase)
	if subtitle:
		ax.text(
			0.08,
			y - 0.015,
			subtitle,
			transform=ax.transAxes,
			color=SEMANTIC_COLORS["text_secondary"],
			fontsize=9,
			va="center",
			ha="left",
			family="monospace",
		)


def add_title(
	ax: Any,
	text: str,
	x: float = 0.065,
	y: float = 0.88,
	fontsize: int = 38,
	color: str | None = None,
	weight: str = "bold",
) -> None:
	"""Draws a section title in massive bold type."""
	ax.text(
		x,
		y,
		text,
		transform=ax.transAxes,
		color=color or SEMANTIC_COLORS["text_primary"],
		fontsize=fontsize,
		fontweight=weight,
		ha="left",
		va="center",
	)


def add_subtitle(
	ax: Any,
	text: str,
	x: float = 0.065,
	y: float = 0.84,
	fontsize: int = 9,
	color: str | None = None,
) -> None:
	"""Draws an uppercase letter-spaced subtitle line."""
	ax.text(
		x,
		y,
		text.upper(),
		transform=ax.transAxes,
		color=color or SEMANTIC_COLORS["text_secondary"],
		fontsize=fontsize,
		ha="left",
		va="center",
		family="monospace",
	)


def add_metric_line(
	ax: Any,
	label: str,
	value: float,
	x: float,
	y: float,
	value_suffix: str = "%",
	label_color: str | None = None,
	fontsize_label: int = 12,
	fontsize_value: int = 14,
) -> None:
	"""Adds a label/value pair with signed value formatting and color."""
	from rendering.color_themes import pick_change_color, signed_text

	ax.text(
		x,
		y,
		label,
		transform=ax.transAxes,
		color=label_color or SEMANTIC_COLORS["text_secondary"],
		fontsize=fontsize_label,
		ha="left",
		va="center",
	)
	ax.text(
		x + 0.13,
		y,
		signed_text(value, suffix=value_suffix),
		transform=ax.transAxes,
		color=pick_change_color(value),
		fontsize=fontsize_value,
		fontweight="bold",
		ha="left",
		va="center",
	)


def add_insight_panel(
	ax: Any,
	text: str,
	secondary_text: str | None = None,
	y: float = 0.10,
) -> None:
	"""Removed — AI insights are disabled."""
	pass


def add_progressive_note(
	ax: Any,
	frame_num: int,
	total_frames: int,
	text: str,
	reveal_at: float = 0.4,
	x: float = 0.065,
	y: float = 0.10,
	fontsize: int = 12,
) -> None:
	"""Removed — AI insights are disabled."""
	pass


def add_footer(ax: Any) -> None:
	"""Adds the Sovereign Analyst Terminal footer bar."""
	import matplotlib.patches as mpatches

	# Footer background strip
	ax.add_patch(
		mpatches.Rectangle(
			(0.0, 0.0),
			1.0,
			0.045,
			transform=ax.transAxes,
			color="#0E1016",
			zorder=6,
		)
	)

	# SOVEREIGN ANALYST TERMINAL
	ax.text(
		0.065,
		0.022,
		"SOVEREIGN ANALYST TERMINAL",
		transform=ax.transAxes,
		color=SEMANTIC_COLORS["text_secondary"],
		fontsize=8,
		fontweight="bold",
		va="center",
		ha="left",
		family="monospace",
		zorder=7,
	)

	# Date / time
	now = datetime.now(UTC)
	date_str = now.strftime("%d %b %Y").upper()
	time_str = now.strftime("%H:%M UTC")
	ax.text(
		0.42,
		0.022,
		f"{date_str} | {time_str}",
		transform=ax.transAxes,
		color=SEMANTIC_COLORS["text_secondary"],
		fontsize=8,
		va="center",
		ha="center",
		family="monospace",
		zorder=7,
	)

	# SYSTEM STATUS: OPTIMAL
	ax.text(
		0.90,
		0.022,
		"SYSTEM STATUS: OPTIMAL",
		transform=ax.transAxes,
		color=SEMANTIC_COLORS["text_secondary"],
		fontsize=8,
		va="center",
		ha="right",
		family="monospace",
		zorder=7,
	)


def add_watermark(
	ax: Any,
	text: str = "ET Markets AI",
	alpha: float = 0.0,
	fontsize: int = 11,
) -> None:
	"""Watermark is suppressed in Sovereign Analyst design."""
	pass
