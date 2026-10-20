# Opportunity Radar 📡

**Opportunity Radar** is an AI-powered financial signal detection engine. It continuously monitors the Indian stock market (NSE) to surface non-obvious, high-conviction investment opportunities. Instead of relying solely on price action, this module acts as a programmatic analyst—reading corporate filings, tracking insider trades, and analyzing management commentary using Large Language Models (LLMs) to detect sentiment shifts before they reflect in the stock price.

### 🌟 Key Capabilities
- **Insider Activity Tracking (SAST):** Automatically detects when company promoters or insiders are buying or selling significant chunks of their own stock. (e.g., "Promoter bought ₹124cr of equity").
- **Institutional Flow Detection:** Scans for major Bulk/Block deals indicating institutional accumulation or distribution.
- **Fundamental Triggers:** Parses quarterly results and corporate actions to flag "Earnings Beats", "Earnings Misses", or major "CapEx Announcements".
- **AI Sentiment Analysis:** Uses LLM integration (Gemini 2.0 / Groq) to read through management commentary or press releases, quantifying subtle shifts in business outlook or management tone.
- **Automated Ranking Engine:** Deduplicates overlapping signals and ranks them by institutional weight (High, Medium, Low) to prevent alert fatigue.
- **Bloomberg-Style Terminal:** Comes with a fully responsive, ultra-high-density `React` frontend that visualizes these signals directly on a live candlestick chart, mimicking professional trading terminals.

**Port:** `8001` | **DB:** SQLite (`db/radar.db`) | **LLM:** Gemini 2.0 Flash (free) + Groq fallback

---

## 🚀 Quick Start

```bash
cd opportunity-radar/backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Set up API keys
cp .env.example .env
# Edit .env and add:
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

> **Note:** The backend uses CORS to allow all origins by default. To view the full Bloomberg-style interface, ensure you also start the React frontend in `opportunity-radar/frontend/` using `npm run dev`.

---

## 🛠 API Endpoints

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

## 🏗 Architecture & Core Flow

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

## 📂 File Structure

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

## 📊 Supported Signal Types

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

## 🔑 Environment Variables

Create `.env` in the `backend/` root:

```env
# Optional LLM Analysis Keys:
GEMINI_API_KEY=your-gemini-key    # Free at: https://aistudio.google.com/apikey
GROQ_API_KEY=your-groq-key        # Free at: https://console.groq.com/keys
LLM_MODEL=gemini-2.0-flash        # Default LLM used by Sentiment Scanner
```

> **Note:** Both keys are optional — if neither is set, the sentiment scanner is gracefully skipped, and all other scanners (insider, bulk, earnings) still run efficiently using fallbacks.

---

## 🛡️ NSE API Fallbacks (Offline Dev)

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
