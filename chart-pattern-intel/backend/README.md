# Backend (Python only)

This backend is implemented in Python (FastAPI). No JS/TS backend code should be added here.

## Progress log (Chart Pattern Intelligence)

### 2026-03-29 (local time) — Backend data + detectors + routes

**Summary**
- Implemented the backend data layer, core detectors, and API routes to return OHLCV, patterns, and backtests.

**Changes by folder**

- backend/main.py
	- Added FastAPI app factory, CORS middleware, and router registrations.
	- Added a simple `/health` endpoint for smoke checks.
	- Why: establishes the application entrypoint and makes the API runnable.

- backend/services/
	- Implemented `data_fetcher.py` with:
		- OHLCV fetch from yfinance.
		- Ticker normalization for NSE suffix.
		- Technical indicators (RSI, MACD, SMAs, Bollinger Bands, Volume SMA).
		- Small in-memory cache to avoid repeated calls during demos.
	- Why: provides the data substrate required by detectors and routes.

- backend/models/
	- Implemented `pattern.py` models: `PatternType`, `Pattern`, `BacktestResult`, `SupportResistanceLevel`.
	- Implemented `chart_data.py` models: `OHLCV` and `ChartResponse`.
	- Why: ensures consistent API responses and validation.

- backend/detectors/
	- Implemented `support_resistance.py` using pivot-based levels.
	- Implemented `breakout_detector.py` with volume confirmation.
	- Implemented `momentum_detector.py` for RSI divergence, MACD crossover, and golden cross.
	- Implemented `reversal_detector.py` with a simple double-bottom check.
	- Implemented `candlestick_detector.py` for hammer and bullish engulfing.
	- Implemented `orchestrator.py` to run all detectors and merge results.
	- Why: enables pattern discovery across multiple technical signals.

- backend/routes/
	- Implemented `/patterns/{ticker}` to return patterns + S/R levels.
	- Implemented `/chart/{ticker}` to return OHLCV data with period validation.
	- Implemented `/backtest/{ticker}/{pattern_type}` to compute historical stats.
	- Why: exposes the core functionality to the frontend and demo flows.

- backend/backtester/
	- Implemented `stats.py` helper for win rate, average gain/loss, and RR ratio.
	- Implemented `engine.py` with simple occurrence heuristics for supported pattern types.
	- Why: provides pattern-specific historical performance on a ticker.

### 2026-03-29 (local time) — Phase 1 verification: backend foundation complete

**Phase 1 checklist review**
- Data fetcher stabilized: ticker normalization (.NS), empty-data handling, caching, consistent OHLCV schema.
- Indicator preparation standardized in `get_ohlcv_with_indicators` (RSI, MACD, SMAs, Bollinger Bands, volume SMA).
- Detector output consistency verified: each detector returns `Pattern` with entry/stop/target, confidence, description, and plain-English fields.

**Conclusion**
- Phase 1 is complete based on current implementation in `backend/services/` and `backend/detectors/`.

### 2026-03-29 (local time) — Phase 2 started: pattern engine refinements

**Changes by folder**

- backend/detectors/support_resistance.py
	- Merged nearby levels and filtered to stronger levels only.
	- Reduced output to the top 8 by touch count to avoid noisy charts.
	- Why: cleaner, more reliable S/R zones for breakouts and UI display.

- backend/detectors/breakout_detector.py
	- Added overextension check and required a fresh breakout in the last 5 sessions.
	- Included extension percentage in `key_levels` for UI context.
	- Why: avoids late signals and keeps the breakout detector demo-friendly.

- backend/detectors/momentum_detector.py
	- Enforced recent MACD/golden cross signals using a short lookback window.
	- Why: keeps momentum patterns current and easier to explain.

- backend/detectors/candlestick_detector.py
	- Required a short downtrend before hammer/engulfing signals and slightly lowered confidence.
	- Why: reduces noisy candlestick flags and prioritizes cleaner reversals.

### 2026-03-29 (local time) — Phase 2 continuation: configuration cleanup

**Changes by folder**

- backend/config.py
	- Added shared constants for detector thresholds, lookbacks, and caching.
	- Why: removes hardcoded values and makes tuning consistent.

- backend/services/data_fetcher.py
	- Replaced cache TTL and rate-limit sleep with config constants.
	- Why: avoid magic numbers and centralize tuning.

- backend/detectors/
	- Updated support/resistance, breakout, momentum, reversal, and candlestick detectors to use config constants.
	- Why: reduces hardcoded thresholds across detection logic.

- backend/backtester/engine.py
	- Replaced default holding period with config constant.
	- Why: centralize backtest horizon control.

### 2026-03-29 (local time) — Phase 2 improvement: reversals expanded

**Changes by folder**

- backend/models/pattern.py
	- Added `DOUBLE_TOP` pattern type.
	- Why: enable explicit double-top classification.

- backend/config.py
	- Added double-top and head-and-shoulders tuning constants.
	- Why: keep reversal thresholds consistent and configurable.

- backend/detectors/reversal_detector.py
	- Added double-top and head-and-shoulders detection logic.
	- Why: provide stronger bearish reversal coverage for Phase 2.

### 2026-03-29 (local time) — Phase 2 improvement: backtest + ranking

**Changes by folder**

- backend/backtester/engine.py
	- Added historical occurrence detection for `double_top` and `head_shoulders`.
	- Aligned breakout/RSI windows with config constants for consistency.
	- Why: enable stock-specific backtests for the new reversal patterns.

- backend/config.py
	- Added backtest window tuning and ranking weights.
	- Why: centralize tuning for backtest logic and ranking.

- backend/routes/patterns.py
	- Added pattern ranking (confidence + recency) and sorted output by rank.
	- Included `rank_score` in `key_levels` for frontend ordering.
	- Why: ensures the most actionable patterns appear first.

### 2026-03-29 (local time) — Phase 3 completed: backtesting made robust

**Changes by folder**

- backend/config.py
	- Added Phase 3 backtest constants: period, sample thresholds, entry/success modes, and per-pattern tuning.
	- Why: centralizes backtest behavior and makes tuning demo-safe.

- backend/backtester/stats.py
	- Added `compute_backtest_stats` (win rate, avg gain/loss, RR, median).
	- Why: provides consistent, explainable summary statistics.

- backend/models/pattern.py
	- Extended `BacktestResult` with `median_return_pct`, `holding_period_days`, `entry_mode`, `success_mode`.
	- Why: makes backtest responses self-describing for the frontend.

- backend/backtester/engine.py
	- Implemented occurrence finders for all supported patterns.
	- Added consistent evaluation logic with entry/exit rules and directional handling for bearish patterns.
	- Added low-sample safeguards and cautionary notes.
	- Why: ensures historical results match live logic and stay honest.

- backend/routes/backtest.py
	- Validates pattern types, supports optional `holding_period`, and uses config defaults.
	- Why: delivers the Phase 3 backtest contract cleanly via API.
