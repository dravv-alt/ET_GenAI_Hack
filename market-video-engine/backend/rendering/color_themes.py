"""Color palette constants and helpers for Sovereign Analyst Terminal visuals."""

from __future__ import annotations


# ── Sovereign Analyst Terminal palette ────────────────────────────
SA_BG = "#12141A"  # near-black background
SA_BG_ALT = "#181B24"  # slightly lighter background
SA_PANEL = "#1A1E28"  # panel background
SA_PANEL_BORDER = "#252A36"  # subtle panel border
SA_GRID = "#1E2330"  # grid / divider lines

SA_WHITE = "#FFFFFF"
SA_TEXT_PRIMARY = "#E8ECF4"  # primary text (off-white)
SA_TEXT_SECONDARY = "#6B7A94"  # muted labels / metadata
SA_TEXT_TERTIARY = "#3D4A60"  # very muted text for rank numbers

SA_POSITIVE = "#C5D0E0"  # positive bars (cool slate-blue)
SA_POSITIVE_TEXT = "#E8ECF4"  # positive percentage text
SA_NEGATIVE = "#E86464"  # negative / losers (coral-red)
SA_NEGATIVE_SOFT = "#F0A0A0"  # softer salmon for negative bars
SA_NEGATIVE_BG = "#2A1A1A"  # background tint for negative context

SA_VIOLET = "#7C6ADB"  # race chart / accent bars (muted violet)
SA_VIOLET_BRIGHT = "#9D82FF"  # brighter violet for top performers
SA_VIOLET_DIM = "#4A4070"  # dimmed violet for lower rank bars

SA_GREEN_FLOW = "#00C853"  # FII/DII positive flow
SA_ACCENT_BAR = "#8C9AB8"  # accent bar in headers (slate)
SA_ACCENT_GOLD = "#C8A86E"  # subtle gold accent (unused, reserved)
SA_INFO_BLUE = "#5B8DEF"  # informational / insight text

SA_BAR_TRACK = "#1E2535"  # background track for bars
SA_BAR_HIGHLIGHT = "#2A3248"  # highlighted row background (top 3)

SA_INSIGHT_BG = "#14171E"  # AI insight panel background
SA_INSIGHT_TEXT = "#B0B8CC"  # AI insight text color

SA_BADGE_BG = "#1D2230"  # sector badge background
SA_BADGE_TEXT = "#7A8AA0"  # sector badge text

SA_LIVE_DOT = "#E86464"  # live indicator dot
SA_TICKER_TEXT = "#6B7A94"  # top ticker tape text


# Semantic color mapping used by generators.
SEMANTIC_COLORS = {
	"background": SA_BG,
	"background_alt": SA_BG_ALT,
	"panel": SA_PANEL,
	"panel_border": SA_PANEL_BORDER,
	"grid": SA_GRID,
	"text_primary": SA_TEXT_PRIMARY,
	"text_secondary": SA_TEXT_SECONDARY,
	"text_tertiary": SA_TEXT_TERTIARY,
	"accent": SA_ACCENT_BAR,
	"positive": SA_POSITIVE,
	"positive_text": SA_POSITIVE_TEXT,
	"negative": SA_NEGATIVE,
	"negative_soft": SA_NEGATIVE_SOFT,
	"violet": SA_VIOLET,
	"violet_bright": SA_VIOLET_BRIGHT,
	"violet_dim": SA_VIOLET_DIM,
	"info": SA_INFO_BLUE,
	"bar_track": SA_BAR_TRACK,
	"bar_highlight": SA_BAR_HIGHLIGHT,
	"insight_bg": SA_INSIGHT_BG,
	"insight_text": SA_INSIGHT_TEXT,
	"badge_bg": SA_BADGE_BG,
	"badge_text": SA_BADGE_TEXT,
	"live_dot": SA_LIVE_DOT,
	"ticker_text": SA_TICKER_TEXT,
}


def pick_change_color(value: float) -> str:
	"""Returns positive/negative color based on signed value."""
	return SA_POSITIVE_TEXT if value >= 0 else SA_NEGATIVE


def pick_bar_color(value: float, context: str = "default") -> str:
	"""Returns bar fill color based on value and context."""
	if context == "race":
		return SA_VIOLET_BRIGHT if value >= 100 else SA_VIOLET if value >= 50 else SA_VIOLET_DIM
	if context == "loser":
		return SA_NEGATIVE if abs(value) >= 1.5 else SA_NEGATIVE_SOFT
	return SA_POSITIVE  # default: cool slate-blue


def signed_text(value: float, decimals: int = 2, suffix: str = "%") -> str:
	"""Returns +x.xx%/-x.xx% style formatting."""
	sign = "+" if value >= 0 else ""
	return f"{sign}{value:.{decimals}f}{suffix}"
