# Opportunity Radar API - How to Use

The backend is a FastAPI server running on port `8001`. It exposes a set of RESTful endpoints to manage watchlists, trigger AI scans, and retrieve ranked alerts.

Base URL: `http://localhost:8001`

---

## 1. Health Check
Verify that the server is currently running.

**Endpoint:** `GET /health`

**cURL Example:**
```bash
curl http://localhost:8001/health
```

**Expected Response:**
```json
{
  "status": "ok",
  "service": "opportunity-radar",
  "port": 8001,
  "version": "1.0.0"
}
```

---

## 2. Trigger an AI Scan
This is the core endpoint. It triggers all 4 agents to run sequentially over the requested tickers, process the data, detect anomalies, rank the findings, and save them in the SQLite cache. 
*Note: This runs synchronously and takes 15–45 seconds depending on LLM latency and rate limits.*

**Endpoint:** `POST /scan`

**cURL Example (Providing a specific list):**
```bash
curl -X POST http://localhost:8001/scan \
     -H "Content-Type: application/json" \
     -d '["RELIANCE", "INFY", "HDFCBANK", "TCS"]'
```

**cURL Example (Using default/DB watchlist):**
```bash
curl -X POST http://localhost:8001/scan \
     -H "Content-Type: application/json" \
     -d '[]'
```

**Response (Excerpt):**
```json
{
  "status": "complete",
  "alerts_found": 3,
  "tickers_scanned": ["RELIANCE", "INFY", "HDFCBANK", "TCS"],
  "alerts": [
    {
      "id": "abc-123",
      "ticker": "RELIANCE",
      "alert_type": "insider_buy",
      "signal_strength": "high",
      "title": "MUKESH D AMBANI bought ₹124cr of RELIANCE",
      "why_it_matters": "Promoter open-market buying is a strong bullish signal...",
      "source_url": "https://nseindia.com/..."
    }
  ]
}
```

---

## 3. Retrieve Alert Feed
Fetch the ranked alert feed from the SQLite database cache (populated by `POST /scan`). If no scan has been run yet, this will return an empty list.

**Endpoint:** `GET /alerts`

**Optional Query Parameters:**
*   `limit` (int): Max number of alerts to return (default is 20).
*   `signal` (str): Filter by strength: `high`, `medium`, or `low`.
*   `type` (str): Filter by alert type (e.g. `insider_buy`, `bulk_deal`).

**cURL Example (Fetch 5 High-priority alerts):**
```bash
curl "http://localhost:8001/alerts?limit=5&signal=high"
```

**Expected Response:**
```json
{
  "alerts": [...Array of alert objects...],
  "total": 5,
  "filters_applied": {
    "signal": "high",
    "type": null,
    "limit": 5
  }
}
```

---

## 4. Retrieve Alerts by Ticker
Fetch all cached alerts strictly localized to an individual NSE ticker.

**Endpoint:** `GET /alerts/{ticker}`

**cURL Example:**
```bash
curl http://localhost:8001/alerts/RELIANCE
```

**Expected Response:**
```json
{
  "ticker": "RELIANCE",
  "alerts": [...Array of RELIANCE-only alerts...],
  "total": 2
}
```

---

## 5. Get Watchlist
Retrieve the user's current tracked watchlist from SQLite.

**Endpoint:** `GET /watchlist`

**cURL Example:**
```bash
curl http://localhost:8001/watchlist
```

**Expected Response:**
```json
{
  "tickers": ["RELIANCE", "INFY", "TCS"],
  "items": [
    {"ticker": "RELIANCE", "added_at": "2026-03-29T12:00:00"},
    ...
  ],
  "count": 3
}
```

---

## 6. Update Watchlist
Replace the entirely tracked watchlist. **Note:** This entirely overrides the previous table!

**Endpoint:** `POST /watchlist`

**cURL Example:**
```bash
curl -X POST http://localhost:8001/watchlist \
     -H "Content-Type: application/json" \
     -d '{"tickers": ["TATASTEEL", "WIPRO", "ZOMATO"]}'
```

**Expected Response:**
```json
{
  "tickers": ["TATASTEEL", "WIPRO", "ZOMATO"],
  "items": [...],
  "count": 3
}
```

---

## API Summary & Workflow for Frontend Integration
1. Call `GET /watchlist` on mount to show default tracked stocks on the sidebar.
2. Clicking "Scan Now" calls `POST /scan` with your tracking list (show a loading spinner as this request takes time).
3. The response from `POST /scan` (or polling `GET /alerts`) is used to populate your main dashboard feed (`AlertFeed`).
4. Category filters on the frontend simply map to `GET /alerts?signal=high` or `GET /alerts?type=bulk_deal`.
