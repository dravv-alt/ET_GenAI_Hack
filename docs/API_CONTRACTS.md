# API Contracts

This document outlines the REST API endpoints exposed by the 4 independent products. All backends are built with FastAPI.

---

## 1. Opportunity Radar (Port 8001)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/health` | Health check |
| `GET`  | `/alerts` | Retrieve all active signals across the market |
| `GET`  | `/alerts/{ticker}` | Retrieve specific signals for a given ticker |
| `POST` | `/scan` | Trigger a manual scan for signals (Bulk Deals, Filings, Insider) |
| `GET`  | `/watchlist` | Get the user's current watchlist |
| `POST` | `/watchlist` | Add or update a ticker in the watchlist |

---

## 2. Chart Pattern Intelligence (Port 8002)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/health` | Health check |
| `POST` | `/scan` | Run pattern detection algorithm across the market universe |
| `GET`  | `/patterns/{ticker}` | Get detected patterns for a specific ticker |
| `GET`  | `/chart/{ticker}` | Get OHLCV chart data and detected patterns for plotting |
| `GET`  | `/backtest/{ticker}/{pattern_type}` | Run historical backtest for a specific pattern |
| `POST` | `/explain` | Generate an LLM explanation for a detected pattern |
| `POST` | `/paper/trade` | Execute a paper trade based on a pattern signal |
| `POST` | `/paper/reset` | Reset the paper trading ledger |
| `GET`  | `/paper/ledger` | View the paper trading history and active positions |
| `GET`  | `/paper/summary` | View total PnL and paper trading statistics |

---

## 3. Market ChatGPT (Port 8003)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/health` | Health check |
| `GET`  | `/market/live` | Get live market overview (Nifty 50, Top Gainers/Losers) |
| `POST` | `/chat` | Main conversational endpoint (RAG query processing) |
| `POST` | `/portfolio/parse` | Upload and parse user portfolio (CSV/JSON) |
| `POST` | `/portfolio/questions` | Generate suggested questions based on portfolio holdings |

---

## 4. AI Market Video Engine (Port 8004)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/health` | Health check |
| `POST` | `/video/generate` | Trigger the video generation pipeline |
| `POST` | `/video/preview-script` | Generate the script without rendering the video |
| `GET`  | `/video/download/{filename}`| Download a rendered video file |
| `GET`  | `/video/history` | View history of generated videos |
| `GET`  | `/video/run/{run_id}` | Get the status of a specific generation run |
| `POST` | `/video/cleanup` | Delete old or failed video rendering caches |
