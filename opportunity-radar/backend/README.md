# Opportunity Radar — Backend

AI-powered NSE signal detector. Surfaces non-obvious investment opportunities from corporate filings, bulk deals, insider trades, and LLM-based sentiment shift detection.

**Port:** `8001` | **DB:** SQLite (`db/radar.db`) | **LLM:** Gemini 2.0 Flash (free) + Groq fallback

---

## Quick Start

```bash
cd opportunity-radar/backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Set up API keys (copy from shared/.env.example)
cp ../../shared/.env.example ../../shared/.env
# Edit shared/.env and add:
#   GEMINI_API_KEY=your-key   → https://aistudio.google.com/apikey (free)
#   GROQ_API_KEY=your-key     → https://console.groq.com/keys (free)

# Start server
uvicorn main:app --reload --port 8001
```

**Verify it's running:**
```bash
curl http://localhost:8001/health
# → {"status":"ok","service":"opportunity-radar","port":8001}
```

**Swagger UI:** http://localhost:8001/docs

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/alerts` | Ranked alert feed. Query: `?limit=20&signal=high&type=insider_buy` |
| `GET` | `/alerts/{ticker}` | All alerts for one stock e.g. `/alerts/RELIANCE` |
| `POST` | `/scan` | Trigger fresh scan. Body: `["RELIANCE", "INFY", "TCS"]` |
| `GET` | `/watchlist` | Current monitored watchlist |
| `POST` | `/watchlist` | Replace watchlist. Body: `{"tickers": ["RELIANCE", "INFY"]}` |

### Example Calls

```bash
# Run a scan on specific stocks
curl -X POST http://localhost:8001/scan \
     -H "Content-Type: application/json" \
     -d '["RELIANCE", "INFY", "HDFCBANK", "TCS"]'

# Get all HIGH signal alerts
curl "http://localhost:8001/alerts?signal=high&limit=10"

# Get alerts for a specific stock
curl http://localhost:8001/alerts/RELIANCE

# Update watchlist
curl -X POST http://localhost:8001/watchlist \
     -H "Content-Type: application/json" \
     -d '{"tickers": ["RELIANCE", "INFY", "HDFCBANK", "TCS", "WIPRO"]}'
```

---

## Architecture

```
POST /scan
    └── orchestrator.run_scan(watchlist)
            ├── bulk_deal_scanner.scan()    NSE block deal data → INSIDER_BUY / BULK_DEAL alerts
            ├── insider_scanner.scan()      SAST filings       → INSIDER_BUY / INSIDER_SELL alerts  
            ├── filing_scanner.scan()       yfinance + NSE     → EARNINGS_BEAT / EARNINGS_MISS / CAPEX alerts
            └── sentiment_scanner.scan_all() LLM (Gemini/Groq) → SENTIMENT_SHIFT alerts
                    ↓
            signal_ranker.rank()            Dedup + sort by signal strength
                    ↓
            alert_store.save_alerts()       Persist to SQLite (db/radar.db)
                    ↓
GET /alerts → alert_store.get_cached_alerts() → ranked JSON response
```

---

## File Structure

```
backend/
├── main.py                    FastAPI entrypoint, CORS, routers, startup
├── requirements.txt
│
├── models/
│   ├── alert.py               Alert, AlertType, SignalStrength Pydantic models
│   └── watchlist.py           Watchlist, WatchlistItem, WatchlistUpdateRequest
│
├── db/
│   ├── schema.sql             CREATE TABLE alerts + watchlist (IF NOT EXISTS)
│   ├── db.py                  get_conn(), init_schema()
│   └── radar.db               Auto-created on first startup
│
├── data/
│   ├── sample_bulk_deals.json       NSE API fallback (when blocked)
│   ├── sample_insider_trades.json   SAST data fallback
│   └── sample_commentaries.json     Mgmt commentary for LLM sentiment scanner
│
├── services/
│   ├── nse_client.py          NSE API with session cookies + JSON fallbacks
│   ├── llm_analyzer.py        Gemini/Groq sentiment analysis wrapper
│   └── alert_store.py         SQLite alert cache (save/read/clear)
│
├── agents/
│   ├── orchestrator.py        Master agent: runs all scanners, ranks, persists
│   ├── bulk_deal_scanner.py   NSE block deal → promoter/institutional signals
│   ├── insider_scanner.py     SAST disclosures → insider trade signals
│   ├── filing_scanner.py      Quarterly results + corp actions → earnings signals
│   ├── sentiment_scanner.py   LLM tone shift detection from mgmt commentary
│   └── signal_ranker.py       Dedup by ticker+type, sort by signal weight
│
└── routes/
    ├── alerts.py              GET /alerts, GET /alerts/{ticker}
    ├── scan.py                POST /scan
    └── watchlist.py           GET /watchlist, POST /watchlist
```

---

## Signal Types

| Alert Type | Trigger | Strength |
|-----------|---------|---------|
| `insider_buy` | Promoter open-market purchase | HIGH (>₹10cr) / MEDIUM |
| `insider_sell` | Promoter selling stake | MEDIUM |
| `bulk_deal` | Large institutional block buy | HIGH (>₹50cr) / MEDIUM |
| `earnings_beat` | YoY PAT growth >15% | HIGH |
| `earnings_miss` | YoY PAT decline >10% | MEDIUM |
| `sentiment_shift` | LLM detects mgmt tone change | HIGH / MEDIUM / LOW |
| `capex_announcement` | Buyback / capacity expansion filing | MEDIUM |
| `regulatory_approval` | Govt approval unlocks new market | MEDIUM |

---

## Environment Variables

Add to `shared/.env`:

```env
GEMINI_API_KEY=your-gemini-key    # Free at: https://aistudio.google.com/apikey
GROQ_API_KEY=your-groq-key        # Free at: https://console.groq.com/keys
LLM_MODEL=gemini-2.0-flash        # Default Gemini model
```

> **Note:** Both keys are optional — if neither is set, the sentiment scanner is skipped and all other scanners still run using fallback data.

---

## NSE API Fallbacks

NSE public APIs frequently return 403 errors to non-browser clients.  
Every NSE call falls back to pre-loaded JSON files in `data/`:

| Function | Fallback File |
|---------|--------------|
| `get_bulk_deals()` | `data/sample_bulk_deals.json` |
| `get_insider_trades()` | `data/sample_insider_trades.json` |
| `get_quarterly_results()` | Returns `{}` → filing_scanner uses yfinance |
| `get_corporate_actions()` | Returns `[]` |
| Management commentary | `data/sample_commentaries.json` |

The demo is **fully functional with no internet** using only fallback data.

---

## Default Watchlist

If no watchlist is set, scans these 10 NSE stocks:

`RELIANCE, INFY, HDFCBANK, TCS, WIPRO, ICICIBANK, AXISBANK, SBIN, TATAMOTORS, BAJFINANCE`
