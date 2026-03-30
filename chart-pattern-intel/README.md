# Chart Pattern Intelligence

Stock pattern analyst for multi-market tickers with detection, backtesting, and a Bloomberg-style UI. Users search a ticker, see OHLCV with technical overlays, get ranked pattern signals, and review historical backtest stats.

## What is implemented

### Backend (FastAPI, Python)
- Market data ingestion via yfinance with market-aware ticker normalization (NSE/BSE/DAX/FTSE suffixes, crypto pairs, indices).
- Technical indicators: RSI, MACD, SMA 20/50/200, Bollinger Bands, Volume SMA 20.
- Pattern detectors:
  - Support/Resistance (pivot levels, merged + ranked by touches)
  - Breakout (volume confirmation, extension checks, recency filter)
  - Momentum (RSI divergence, MACD crossover, golden cross)
  - Reversals (double bottom, double top, head and shoulders)
  - Candlestick (hammer, bullish engulfing)
- Pattern ranking: confidence + recency score.
- Backtesting engine with occurrence finders and directional handling for bearish patterns.
- Expanded backtest stats (drawdown, Calmar, Sharpe/Sortino, profit factor, expectancy, exposure, time-in-trade).
- Multi-timeframe confirmation (1D/4H/1H) toggle.
- Ensemble signal scoring with feature breakdown.
- Paper-trading portfolio with ledger + PnL summary.
- Background precompute for scans/backtests (in-memory cache).

### Frontend (React + Vite)
- Bloomberg-style monochrome design system and layout.
- Market dropdown with per-market ticker lists, currency formatting, and aliases (INF -> INFY for India).
- Candlestick chart via lightweight-charts with support/resistance price lines and pattern markers.
- Pattern cards (entry/stop/target, confidence, rank) and key levels panel.
- Score panel (weighted signal score with confidence/recency/backtest win rate).
- Backtest toggle with compact sparkline and stats panel.
- Explanation panel using pattern description + backtest note.
- Period selector (6M/1Y/2Y/5Y) for chart + patterns.
- Auto-refresh toggle (60s) for live updates.
- Market scan button with ranked results list.

## Market ticker lists
- Static per-market lists stored in frontend (NSE, BSE, NIFTY 50, NASDAQ, NYSE, S&P 500, DAX, FTSE 100, Crypto).
- Optional NIFTY 50 updater script to auto-generate from CSV if a source is available.

## Project structure

- backend/            FastAPI app, detectors, backtester
- frontend/           React app (Vite)
- ImplementationPlan.md
- report.md           Backtest quick check results
- To-Note.md          Working notes

## How to run

### Backend

From chart-pattern-intel/backend:

No venv is required.

1) Install deps

python -m pip install -r requirements.txt

2) Start server

python -m uvicorn main:app --reload --port 8002

### Frontend

From chart-pattern-intel/frontend:

1) Install deps

npm install

2) Start UI

npm run dev

Open the Vite URL shown in the terminal (default: http://localhost:5173).

## API endpoints

- GET /health
- GET /chart/{ticker}?period=6mo|1y|2y|5y&market=NSE
- GET /patterns/{ticker}?period=6mo|1y|2y|5y&market=NSE&mtf=false
- GET /backtest/{ticker}/{pattern_type}?holding_period=15&market=NSE
- POST /scan { tickers[], period, limit, market, mtf }
- POST /explain { pattern, backtest }
- POST /paper/reset { starting_cash }
- POST /paper/trade { symbol, market, side, quantity, price?, period? }
- GET /paper/ledger
- GET /paper/summary

## LLM explanations (Gemini)

Set GEMINI_API_KEY in chart-pattern-intel/.env to enable LLM explanations.
If the key is missing or Gemini fails, the backend falls back to a rule-based explanation.

## NIFTY 50 auto-update (optional)

The frontend ships with a static NIFTY 50 list in src/lib/tickers.js.
If you have a CSV source, update it via:

NIFTY50_SOURCE_URL=<csv-url> npm run update:nifty50

Script: frontend/scripts/update_nifty50.cjs

## Known constraints

- Pattern detection can return empty lists for some tickers or short windows.
- Backtest stats are conservative for low sample counts.
- The updater script depends on a reachable CSV source; provide NIFTY50_SOURCE_URL if needed.
- Paper trading and precompute caches are in-memory and reset on server restart.

## Report references

See report.md for backtest sanity checks and sample outputs.
