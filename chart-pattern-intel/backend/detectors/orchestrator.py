"""Runs all detectors and merges results into a pattern report."""

from __future__ import annotations

import pandas as pd

from detectors import breakout_detector, candlestick_detector, momentum_detector, reversal_detector, support_resistance


def run_all(df: pd.DataFrame) -> tuple[list, list]:
	levels = support_resistance.detect(df)
	patterns = []
	patterns.extend(breakout_detector.detect(df, levels))
	patterns.extend(momentum_detector.detect(df))
	patterns.extend(reversal_detector.detect(df))
	patterns.extend(candlestick_detector.detect(df))
	return patterns, levels
