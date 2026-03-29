# T1 — Opportunity Radar

> **Your product:** AI that continuously monitors corporate filings, quarterly results,
> bulk/block deals, insider trades, and regulatory changes — surfacing missed
> opportunities as daily alerts. **Not a summarizer — a signal-finder.**
>
> **You own:** Everything in `/opportunity-radar/`
> **Your port:** `backend=8001`, `frontend=3001`
> **Dependency on teammates:** Only `shared/` utilities — you are fully independent.

---

## What you are building

A dashboard where a user inputs a list of NSE stocks (or uses the default NSE top 100).
The AI agent continuously scans multiple data signals for each stock and surfaces
**non-obvious opportunities** that a retail investor would miss — e.g.:

- A promoter just bought ₹50 crore of shares in the open market (bullish insider signal)
- A company quietly filed a capex plan that implies 30% capacity expansion
- A mutual fund just disclosed a 5% stake (institutional interest signal)
- Management commentary shifted from "cautious" to "confident" vs last quarter
- A regulatory approval that unlocks a new market segment

The output is a **ranked alert feed** — each alert has: what happened, why it matters,
the signal strength (High / Medium / Low), and a source link.

---

## Folder structure

```
opportunity-radar/
├── README.md                          ← YOU ARE HERE
│
├── backend/
│   ├── main.py                        ← FastAPI app entrypoint (port 8001)
│   ├── requirements.txt
│   ├── db/                            ← SQLite helpers + schema
│   ├── data/                          ← small JSON fallbacks for dev
│   │
│   ├── routes/
│   │   ├── alerts.py                  ← GET /alerts, GET /alerts/{ticker}
│   │   ├── scan.py                    ← POST /scan (trigger a fresh scan)
│   │   └── watchlist.py               ← GET/POST /watchlist
│   │
│   ├── agents/
│   │   ├── orchestrator.py            ← Master agent: runs all scanners, ranks signals
│   │   ├── filing_scanner.py          ← Scans NSE quarterly results + annual reports
│   │   ├── bulk_deal_scanner.py       ← Scans bulk/block deal data from NSE
│   │   ├── insider_scanner.py         ← Scans promoter buying/selling patterns
│   │   ├── sentiment_scanner.py       ← Detects management commentary shifts (LLM)
│   │   └── signal_ranker.py           ← Ranks and deduplicates all alerts by importance
│   │
│   ├── services/
│   │   ├── nse_client.py              ← All NSE public API calls
│   │   ├── llm_analyzer.py            ← LLM calls for text analysis + signal extraction
│   │   └── alert_store.py             ← SQLite-backed alert cache
│   │
│   └── models/
│       ├── alert.py                   ← Pydantic: Alert, SignalStrength, AlertType
│       └── watchlist.py               ← Pydantic: Watchlist, WatchlistItem
│
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.js
    ├── tailwind.config.js
    ├── public/
    └── src/
        ├── main.jsx
        ├── App.jsx                    ← Main alert feed page
        ├── styles.css
        ├── components/
        │   ├── AlertFeed.jsx          ← Ranked list of alerts with filters
        │   ├── AlertCard.jsx          ← Single alert: signal type, ticker, why it matters
        │   ├── SignalBadge.jsx        ← High / Medium / Low badge
        │   ├── WatchlistPanel.jsx     ← Sidebar: manage your tracked stocks
        │   ├── ScanProgress.jsx       ← Progress bar while AI scans stocks
        │   └── SourceLink.jsx         ← Clickable NSE/news source citation
        └── lib/
            ├── api.js                 ← All fetch calls to backend
            └── mockData.js            ← Mock alerts for UI dev (use until H5)
```

---

## Your hour-by-hour plan

### H0–H1: Setup and skeleton

**Goal:** Running FastAPI server + Vite React app, both starting without errors.

```bash
# Terminal 1: Backend
cd opportunity-radar/backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8001

# Terminal 2: Frontend
cd opportunity-radar/frontend
npm install && npm run dev -- --port 3001
```

Tasks:
- [ ] `main.py` with CORS, health endpoint at `GET /health`
- [ ] `models/alert.py` — write Pydantic models first (types guide everything)
- [ ] `frontend/src/lib/mockData.js` — hardcode 5 fake alerts so you can build UI immediately
- [ ] `frontend/src/lib/api.js` — create `USE_MOCK = true` flag so T3 can build without backend

**Done when:** `curl http://localhost:8001/health` returns `{"status":"ok"}` and `localhost:3001` loads.

---

### H1–H3: Data layer + core scanner

**Goal:** Real NSE data flowing into your backend.

**H1–H2: NSE client (`services/nse_client.py`)**

```python
# services/nse_client.py
import requests
import time
from functools import lru_cache

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}

@lru_cache(maxsize=100)
def get_bulk_deals(date: str = None) -> list:
    """
    Fetches bulk deal data from NSE.
    Returns list of: {symbol, client_name, deal_type, quantity, price, value_cr}
    Falls back to /data/sample_bulk_deals.json if NSE blocks request.
    """
    try:
        url = "https://www.nseindia.com/api/block-deal"
        resp = requests.get(url, headers=HEADERS, timeout=5)
        resp.raise_for_status()
        return resp.json().get("data", [])
    except Exception:
        # Fallback: load from sample data
        import json
        with open("../../data/sample_bulk_deals.json") as f:
            return json.load(f)

def get_quarterly_results(symbol: str) -> dict:
    """
    Fetches latest quarterly result for a symbol.
    Returns: {symbol, period, revenue, pat, eps, yoy_growth_pct, beat_miss}
    """
    try:
        url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}&section=financials"
        resp = requests.get(url, headers=HEADERS, timeout=5)
        return resp.json()
    except Exception:
        return {}  # Return empty dict — caller handles gracefully

def get_corporate_actions(symbol: str) -> list:
    """
    Fetches corporate actions: dividends, buybacks, splits, bonus.
    """
    try:
        url = f"https://www.nseindia.com/api/corporateAction?index=equities&symbol={symbol}"
        resp = requests.get(url, headers=HEADERS, timeout=5)
        return resp.json()
    except Exception:
        return []
```

**H2–H3: Bulk deal scanner + filing scanner**

```python
# agents/bulk_deal_scanner.py
from services.nse_client import get_bulk_deals
from models.alert import Alert, SignalStrength, AlertType

def scan(watchlist: list[str]) -> list[Alert]:
    """
    Looks for bulk/block deals in the last 7 days for watchlist stocks.
    Generates alerts for:
    - Large promoter purchases (> ₹10 cr) → High signal
    - Institutional accumulation (> ₹50 cr) → High signal
    - Insider selling (promoter selling) → bearish, Medium signal
    """
    deals = get_bulk_deals()
    alerts = []

    for deal in deals:
        symbol = deal.get("symbol", "")
        if symbol not in watchlist:
            continue

        value_cr = deal.get("value_cr", 0)
        deal_type = deal.get("deal_type", "")
        client = deal.get("client_name", "")

        if "PROMOTER" in client.upper() and deal_type == "BUY" and value_cr > 10:
            alerts.append(Alert(
                ticker=symbol,
                alert_type=AlertType.INSIDER_BUY,
                signal_strength=SignalStrength.HIGH,
                title=f"Promoter bought ₹{value_cr:.0f}cr of {symbol}",
                why_it_matters="Promoter open-market buying is one of the strongest bullish signals. Insiders rarely buy unless they expect significant upside.",
                action_hint="Consider reviewing your position — promoter conviction is high.",
                source_url="https://nseindia.com/block-deal",
                source_label="NSE Block Deal Data",
                raw_data=deal,
            ))

    return alerts
```

---

### H3–H5: LLM sentiment scanner + signal ranker

**Goal:** AI extracts signals from management commentary. Ranker produces final alert feed.

**H3–H4: Sentiment scanner (`agents/sentiment_scanner.py`)**

This is your most interesting agent. It uses the LLM to compare management commentary across quarters and detect tone shifts.

```python
# agents/sentiment_scanner.py
import sys
sys.path.append("../../shared")
from llm_client import call_llm
from models.alert import Alert, SignalStrength, AlertType

SENTIMENT_PROMPT = """
You are a senior equity analyst. I will give you two management commentary excerpts
from consecutive quarterly results of {symbol}.

PREVIOUS QUARTER COMMENTARY:
{prev_commentary}

CURRENT QUARTER COMMENTARY:
{curr_commentary}

Analyze the SHIFT in tone and content between the two. Focus on:
1. Revenue/growth outlook — more optimistic or cautious?
2. Margin guidance — expanding or contracting?
3. Capex plans — investing more or cutting?
4. Risk language — more or fewer risk mentions?
5. Product/expansion mentions — any new markets or segments?

Return ONLY a JSON object:
{{
  "shift_detected": true/false,
  "shift_direction": "positive" | "negative" | "neutral",
  "shift_magnitude": "high" | "medium" | "low",
  "key_change": "one sentence describing the most important shift",
  "why_it_matters": "one sentence on investment implication",
  "confidence": 0.0-1.0
}}
"""

def scan(symbol: str, prev_commentary: str, curr_commentary: str) -> Alert | None:
    if not prev_commentary or not curr_commentary:
        return None

    prompt = SENTIMENT_PROMPT.format(
        symbol=symbol,
        prev_commentary=prev_commentary[:2000],
        curr_commentary=curr_commentary[:2000],
    )

    try:
        import json
        response = call_llm(prompt)
        data = json.loads(response)

        if not data.get("shift_detected") or data.get("confidence", 0) < 0.6:
            return None

        signal_map = {"high": SignalStrength.HIGH, "medium": SignalStrength.MEDIUM, "low": SignalStrength.LOW}

        return Alert(
            ticker=symbol,
            alert_type=AlertType.SENTIMENT_SHIFT,
            signal_strength=signal_map.get(data["shift_magnitude"], SignalStrength.LOW),
            title=f"Management tone shift detected: {symbol}",
            why_it_matters=data["why_it_matters"],
            action_hint="Read the full commentary shift before acting. Verify with price action.",
            source_url=f"https://nseindia.com/companies-listing/corporate-filings/quarterly-results",
            source_label="NSE Quarterly Results",
            raw_data=data,
        )
    except Exception as e:
        print(f"Sentiment scan failed for {symbol}: {e}")
        return None
```

**H4–H5: Signal ranker + orchestrator**

```python
# agents/signal_ranker.py
from models.alert import Alert, SignalStrength

SIGNAL_WEIGHTS = {
    SignalStrength.HIGH: 3,
    SignalStrength.MEDIUM: 2,
    SignalStrength.LOW: 1,
}

def rank(alerts: list[Alert]) -> list[Alert]:
    """
    Deduplicates and ranks alerts by:
    1. Signal strength (High > Medium > Low)
    2. Recency (newer first within same strength)
    3. Removes duplicate ticker+type combinations (keeps highest strength)
    """
    # Deduplicate: keep highest-strength alert per ticker+type
    seen = {}
    for alert in alerts:
        key = f"{alert.ticker}:{alert.alert_type}"
        if key not in seen or SIGNAL_WEIGHTS[alert.signal_strength] > SIGNAL_WEIGHTS[seen[key].signal_strength]:
            seen[key] = alert

    # Sort by signal weight descending
    ranked = sorted(seen.values(), key=lambda a: SIGNAL_WEIGHTS[a.signal_strength], reverse=True)
    return ranked
```

---

### H5–H7: API routes + frontend connection

**Goal:** Frontend showing real alerts from real data.

**Routes to implement:**

```python
# routes/alerts.py
from fastapi import APIRouter
from agents.orchestrator import run_scan
from services.alert_store import get_cached_alerts

router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.get("/")
async def get_all_alerts(limit: int = 20, signal: str = None):
    """
    Returns ranked alert feed.
    ?signal=high → filter to High signals only
    ?limit=20 → max alerts returned
    """
    alerts = get_cached_alerts()
    if signal:
        alerts = [a for a in alerts if a.signal_strength.value == signal]
    return {"alerts": alerts[:limit], "total": len(alerts)}

@router.get("/{ticker}")
async def get_alerts_for_ticker(ticker: str):
    """Returns all alerts for one specific ticker."""
    alerts = [a for a in get_cached_alerts() if a.ticker == ticker.upper()]
    return {"ticker": ticker, "alerts": alerts}

@router.post("/scan")
async def trigger_scan(watchlist: list[str]):
    """
    Triggers a fresh scan for the given watchlist.
    Returns immediately with job_id; client polls GET /alerts for results.
    For hackathon: run synchronously (no job queue needed).
    """
    results = await run_scan(watchlist)
    return {"status": "complete", "alerts_found": len(results)}
```

**Frontend alert feed (`src/components/AlertFeed.jsx`):**

```jsx
// src/components/AlertCard.jsx

const SIGNAL_COLORS = {
  high: 'bg-green-100 text-green-800 border-green-200',
  medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  low: 'bg-gray-100 text-gray-700 border-gray-200',
};

export function AlertCard({ alert }) {
  return (
    <div className="border border-gray-200 rounded-xl p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-semibold text-sm text-gray-900">{alert.ticker}</span>
            <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${SIGNAL_COLORS[alert.signal_strength]}`}>
              {alert.signal_strength.toUpperCase()}
            </span>
          </div>
          <p className="text-sm font-medium text-gray-800 mb-1">{alert.title}</p>
          <p className="text-xs text-gray-500 mb-2">{alert.why_it_matters}</p>
          <p className="text-xs text-blue-600 italic">{alert.action_hint}</p>
        </div>
      </div>
      <a href={alert.source_url} target="_blank"
         className="mt-3 text-xs text-gray-400 flex items-center gap-1 hover:text-gray-600">
        Source: {alert.source_label} →
      </a>
    </div>
  );
}
```

---

### H7–H9: Polish + edge cases

- [ ] Add loading skeleton while scan runs
- [ ] Filter bar: All / High / Medium / Insider / Sentiment / Filing
- [ ] Empty state if no alerts found
- [ ] Error toast if NSE API fails (with graceful fallback message)
- [ ] Default watchlist: RELIANCE, INFY, HDFCBANK, TCS, WIPRO, ICICIBANK, AXISBANK, SBIN, TATAMOTORS, BAJFINANCE

---

### H9–H12: Demo prep

**Demo scenario (practice this exactly):**
1. Open the dashboard — show default watchlist of 10 NSE stocks
2. Click "Scan Now" — show progress bar as AI scans each stock
3. Alert feed populates with 3–5 ranked alerts
4. Click into a HIGH signal alert — show full detail + source link
5. Explain to judge: "This is the signal a retail investor would have missed. It took our AI 8 seconds to find it."

**Talking points:**
- 14 crore demat account holders — none of them have time to read 10 NSE filings a day
- This product scans ALL of it and surfaces only what matters
- Not a summarizer — a signal-finder (use this exact phrase from the PS)

---

## Pydantic models reference

```python
# models/alert.py
from pydantic import BaseModel
from enum import Enum
from datetime import datetime

class SignalStrength(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class AlertType(str, Enum):
    INSIDER_BUY = "insider_buy"
    INSIDER_SELL = "insider_sell"
    BULK_DEAL = "bulk_deal"
    EARNINGS_BEAT = "earnings_beat"
    EARNINGS_MISS = "earnings_miss"
    SENTIMENT_SHIFT = "sentiment_shift"
    REGULATORY_APPROVAL = "regulatory_approval"
    CAPEX_ANNOUNCEMENT = "capex_announcement"

class Alert(BaseModel):
    id: str = ""                  # auto-generated UUID
    ticker: str
    alert_type: AlertType
    signal_strength: SignalStrength
    title: str                    # short headline, max 80 chars
    why_it_matters: str           # one sentence investment implication
    action_hint: str              # suggested investor action
    source_url: str
    source_label: str
    raw_data: dict = {}
    created_at: datetime = datetime.now()
```

---

## If you get blocked

| Problem | Fix |
|---------|-----|
| NSE API returns 403/blocked | Load from `/data/sample_bulk_deals.json` — already committed |
| LLM API key not working | Check `shared/.env`, run `python ../../shared/llm_client.py` to test |
| yfinance rate limit | Add `time.sleep(0.5)` between calls |
| Frontend not connecting to backend | Check CORS in `main.py`, confirm port is 8001 not 8000 |
| No real filing text to compare | Use hardcoded management commentary strings from `/data/sample_commentaries.json` |

---

## API endpoints summary

```
GET  /health                      → health check
GET  /alerts?limit=20&signal=high → ranked alert feed
GET  /alerts/{ticker}             → alerts for one stock
POST /scan  body: ["RELIANCE", "INFY", ...]  → trigger fresh scan
GET  /watchlist                   → get current watchlist
POST /watchlist body: {tickers: [...]}       → set watchlist
```