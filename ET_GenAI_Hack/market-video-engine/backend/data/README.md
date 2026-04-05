# Data

Fallback JSON payloads used by the backend data layer when live sources fail.

- `market_universe.json`: Nifty symbol, ticker universe, and sector symbol map
- `runtime_config.json`: FPS and per-segment frame budget for combined video generation
- `data_fetch_config.json`: yfinance timeout/retry policy, minimum data thresholds, noisy ticker exclusions
- `cleanup_policy.json`: retention policy for temp MP4 files and stale DB generation records
- `nifty_fallback.json`: Nifty OHLC + change metrics
- `top_movers_fallback.json`: top gainers and losers
- `sectors_fallback.json`: sector performance list
- `fii_dii_fallback.json`: institutional flow fallback
- `ipo_fallback.json`: IPO tracker fallback list
