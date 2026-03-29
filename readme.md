<![CDATA[<div align="center">

# 🇮🇳 AI for the Indian Investor

### ET AI Hackathon 2026 — Problem Statement #6

> **Four AI-powered products that shift the information asymmetry between Wall Street–grade research teams and the 14 crore retail investors who have nothing but a phone and hope.**

[![Stack](https://img.shields.io/badge/Stack-Python_|_FastAPI_|_React_|_SQLite-blue?style=flat-square)](#tech-stack)
[![LLM](https://img.shields.io/badge/LLM-Gemini_2.0_Flash_|_Groq-orange?style=flat-square)](#tech-stack)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](#)

</div>

---

## 💡 The Problem

India is in the middle of a financialization wave—**14 crore demat accounts**, SIP inflows at ₹19,000 crore/month, a generation of first-time investors making decisions based on WhatsApp forwards and Twitter tips.

Meanwhile, institutional players deploy **50-analyst research teams**, real-time filing scanners, and proprietary charting desks. Retail investors? They get generic news summaries and free TradingView.

**The gap is not data. The gap is intelligence.**

Our platform closes this gap with four independent, AI-native products—each solving a specific failure mode in the retail investor's workflow.

---

## 🏗 The Four Products

| # | Product | What It Does | Core AI |
|---|---------|-------------|---------|
| 📡 | [**Opportunity Radar**](#-opportunity-radar) | Scans NSE filings, insider trades & bulk deals—surfaces signals a human would miss | LLM Sentiment Analysis + Rule Engine |
| 📈 | [**Chart Pattern Intelligence**](#-chart-pattern-intelligence) | Detects technical patterns and back-tests them on *that specific stock's* history | Pattern Detection + Stock-Specific Backtesting |
| 💬 | [**Market ChatGPT — Next Gen**](#-market-chatgpt--next-gen) | Portfolio-aware conversational analyst with cited, streaming responses | Multi-Agent RAG + LLM Reasoning |
| 🎬 | [**AI Market Video Engine**](#-ai-market-video-engine) | Auto-generates broadcast-quality market update videos from live data — zero editing | Frame Generation + LLM Script + TTS |

> Each product runs independently. Together, they form a complete AI-powered investing intelligence layer.

---

## 📡 Opportunity Radar

> *"14 crore demat holders. None of them have time to read 10 NSE filings a day. This product scans ALL of it and surfaces only what matters."*

### What It Does

Opportunity Radar is an **AI-powered signal detection engine** that continuously monitors the Indian stock market (NSE) to surface non-obvious, high-conviction investment opportunities. It acts as a programmatic analyst—reading corporate filings, tracking insider trades, parsing bulk deals, and analyzing management commentary using LLMs to detect sentiment shifts **before they reflect in the stock price**.

### Key Capabilities

| Capability | How It Works |
|-----------|-------------|
| 🔍 **Insider Activity Tracking** | Monitors SAST disclosures — detects promoter buying/selling in real-time |
| 📦 **Institutional Flow Detection** | Scans bulk/block deals for institutional accumulation signals |
| 📊 **Fundamental Triggers** | Parses quarterly results for earnings beats, misses, and CapEx announcements |
| 🧠 **AI Sentiment Analysis** | LLM compares management commentary across quarters, quantifies tone shifts |
| ⚖️ **Automated Ranking** | Deduplicates signals and ranks by institutional weight (High / Medium / Low) |
| 🖥️ **Bloomberg-Style Terminal UI** | High-density React frontend with live candlestick charts, data tables & signal panels |

### Signal Types

| Alert Type | Example Trigger | Typical Strength |
|-----------|----------------|-----------------|
| `insider_buy` | Promoter bought ₹124cr of RELIANCE on open market | **HIGH** |
| `insider_sell` | Promoter reduced stake by 0.5% | MEDIUM |
| `bulk_deal` | FII purchased ₹80cr block of INFY | **HIGH** |
| `earnings_beat` | YoY PAT growth > 15% | **HIGH** |
| `earnings_miss` | YoY PAT decline > 10% | MEDIUM |
| `sentiment_shift` | LLM detected management tone shifted from "cautious" → "confident" | HIGH / MEDIUM |
| `capex_announcement` | New capacity expansion filing detected | MEDIUM |

### Architecture

```
POST /scan → Orchestrator
                ├── Insider Scanner (SAST filings)
                ├── Bulk Deal Scanner (NSE block deals)
                ├── Filing Scanner (quarterly results via yfinance + NSE)
                └── Sentiment Scanner (LLM tone-shift detection)
                        ↓
                Signal Ranker (dedup + sort by weight)
                        ↓
                Alert Store (SQLite persistence)
                        ↓
GET /alerts → Ranked JSON feed → Bloomberg-Style React Terminal
```

### Tech Stack

- **Backend:** FastAPI (Python) on port `8001`, SQLite for persistence
- **LLM:** Gemini 2.0 Flash (free tier) + Groq fallback
- **Frontend:** React + Vite, `lightweight-charts` for candlestick rendering
- **Design:** Bloomberg Monochrome — IBM Plex Mono, zero border-radius, 1px borders, green/red signal coding

### Demo Scenario

1. Dashboard loads with default NSE watchlist (RELIANCE, TCS, INFY, etc.)
2. Click **"RUN FULL SCAN"** — AI scans each stock across all four data sources
3. Alert feed populates: *"MUKESH D AMBANI (Promoter) bought ₹124cr of RELIANCE"*
4. Click the alert → candlestick chart updates, AI analysis panel shows *why* it matters
5. Signal Logic panel shows 90/100 confidence with Technical, Fundamental, Sentiment breakdown

> **The pitch:** *"This is the signal a retail investor would have missed. It took our AI 8 seconds to find it."*

---

## 📈 Chart Pattern Intelligence

> *"Generic tools say 'head and shoulders is bearish 65% of the time.' We say 'on RELIANCE specifically, this pattern worked 71% of the time with an average gain of 9.3%.' That's the difference."*

### What It Does

A tool where a user enters any NSE stock ticker. The system fetches 6 months of OHLCV data, runs a **pattern detection engine**, and for each pattern found, shows:
- What the pattern is in plain English (no jargon)
- The **stock-specific back-tested success rate** (not generic pattern stats)
- Entry / Stop-Loss / Target price levels
- Historical win rate, average gain/loss, and risk-reward ratio

### Key Capabilities

| Capability | Details |
|-----------|---------|
| 🎯 **Support/Resistance Detection** | Pivot-point method, validates levels with ≥2 historical touches |
| 📊 **Breakout Detection** | Price above resistance + volume ≥ 1.5x 20-day average |
| 🔄 **Reversal Patterns** | Head & shoulders, double top/bottom |
| 📉 **Momentum Signals** | RSI divergence, MACD crossover, golden cross |
| 🕯️ **Candlestick Patterns** | Doji, engulfing, hammer, shooting star |
| 📜 **Stock-Specific Backtesting** | Tests each pattern against 5 years of history *for that exact stock* |
| 💬 **LLM Plain-English Explainer** | AI translates technical patterns into retail-friendly language |

### Architecture

```
GET /patterns/{ticker}
    → Data Fetcher (yfinance OHLCV + indicators)
        → Pattern Detector Orchestrator
            ├── Support/Resistance Detector
            ├── Breakout Detector
            ├── Reversal Detector
            ├── Momentum Detector
            └── Candlestick Detector
        → Backtester Engine (5-year history, per-stock win rate)
        → LLM Explainer (plain English translation)
    → Pattern Report Card (chart + stats + explanation)
```

### Tech Stack

- **Backend:** FastAPI (Python) on port `8002`
- **Data:** yfinance for OHLCV + technical indicators
- **Frontend:** React + Vite, `lightweight-charts` for interactive charting

---

## 💬 Market ChatGPT — Next Gen

> *"The existing ET Market ChatGPT tells you about a stock. This one tells you about YOUR stocks — your specific holdings, your buy price, your P&L. That's the difference between a generic analyst and a personal advisor."*

### What It Does

A conversational AI that is **aware of the user's specific portfolio**. Upload a CSV of your holdings, and ask complex multi-step questions. The AI:

1. **Plans** — breaks complex questions into targeted sub-queries
2. **Retrieves** — fetches live market data, news, and fundamentals for each relevant holding
3. **Reasons** — synthesizes across all data points with multi-step analysis
4. **Cites** — every factual claim includes a clickable source link
5. **Streams** — tokens appear live as analysis is generated

### Key Capabilities

| Capability | Details |
|-----------|---------|
| 📂 **Portfolio Upload** | CSV drag-drop. System enriches with current prices and P&L |
| 🧠 **Multi-Agent Pipeline** | Query Planner → Retrieval Agent → Analysis Agent → Citation Agent |
| 📡 **Live Data Integration** | yfinance fundamentals + Tavily news search per sub-query |
| 🔗 **Source-Cited Responses** | Every claim has a clickable URL — no hallucinated facts |
| ⚡ **SSE Streaming** | Real-time token streaming with thinking indicators |
| 📊 **Inline Signal Cards** | Bullish/Bearish cards embedded within the chat response |

### Example Interaction

```
User: "Which of my holdings are at risk this quarter?"

AI (streaming):
  [Thinking] Planning analysis…
  [Thinking] Fetching data for 5 queries…

  Based on recent Q3 results, INFY faces headwinds in its US business,
  having cut revenue guidance by 1.5%...

  [SIGNAL CARD] INFY — Bearish (71% confidence)
    • Revenue guidance cut 1.5%
    • Deal ramp delays in North America

  RELIANCE however reported strong PAT growth of 8.2%...

  [SIGNAL CARD] RELIANCE — Bullish (84% confidence)
    • PAT beat by 8.2%
    • Jio subscriber growth 12% YoY

  [Sources]
    📄 INFY Q3 FY24 Results — nseindia.com
    📄 Reliance Q3 profit rises 8% — economictimes.com
```

### Tech Stack

- **Backend:** FastAPI (Python) on port `8003`, SSE streaming
- **LLM:** Multi-agent pipeline (Query Planner → Retrieval → Analysis → Citation)
- **Data:** yfinance + Tavily news search
- **Frontend:** React + Vite, streaming chat UI

---

## 🎬 AI Market Video Engine

> *"Zero human editing. Our AI fetched today's market data, generated a script, converted it to speech, built the animated frames, and assembled this video in 30 seconds. An ET producer would take 3 hours."*

### What It Does

Auto-generates short, broadcast-quality market update videos (30–90 seconds) from live NSE data. Race charts, daily wraps, sector rotations — all rendered programmatically with AI-generated voiceover narration.

### Video Types

| Type | Description | Duration |
|------|------------|----------|
| 📊 **Daily Market Wrap** | Nifty movement, top gainers/losers, FII/DII data | ~60 seconds |
| 🔄 **Sector Rotation** | Animated horizontal bar chart — which sectors are hot/cold today | ~30 seconds |
| 🏁 **Nifty 50 Race Chart** | Animated bar chart race showing 1-year returns | ~45 seconds |
| 🚀 **IPO Tracker** | Current IPOs with status and GMP visualization | ~30 seconds |

### Pipeline

```
User selects "Daily Market Wrap"
    → Fetch live NSE data (Nifty, top movers, sectors)
    → LLM generates voiceover script (~130 words)
    → gTTS converts script to audio
    → matplotlib renders animated frames (16:9, ET branding)
    → MoviePy assembles frames + audio → MP4
    → Video ready for download/playback in ~30 seconds
```

### Key Capabilities

| Capability | Details |
|-----------|---------|
| 🎨 **Branded Frame Rendering** | ET Markets color scheme, 16:9, animated bar charts |
| 🎙️ **AI Script Generation** | LLM writes newscaster-style voiceover from raw data |
| 🔊 **Text-to-Speech** | gTTS (free) with ElevenLabs upgrade path |
| 🎬 **Automated Assembly** | MoviePy stitches frames + audio into production MP4 |
| 📈 **Live Data Pipeline** | yfinance → frames → video, all powered by real market data |

### Tech Stack

- **Backend:** FastAPI (Python) on port `8004`
- **Rendering:** matplotlib + Pillow for frame generation
- **Audio:** gTTS (Google Text-to-Speech, free)
- **Video:** MoviePy for MP4 assembly
- **Frontend:** React + Vite, video player + progress stepper

---

## 📐 System Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    ET AI Investor Platform                      │
├────────────┬────────────┬────────────┬─────────────────────────┤
│  Opportunity│ Chart Pat. │  Market    │   AI Market             │
│  Radar      │ Intel      │  ChatGPT   │   Video Engine          │
│  :8001      │ :8002      │  :8003     │   :8004                 │
├─────────────┴────────────┴────────────┴─────────────────────────┤
│                     Shared Utilities                            │
│   market_data.py · nse_fetcher.py · llm_client.py · news_search│
├─────────────────────────────────────────────────────────────────┤
│   Data: yfinance · NSE APIs · Tavily News · LLMs (Gemini/Groq) │
└─────────────────────────────────────────────────────────────────┘
```

Each product is **fully independent** — separate backend, separate frontend, separate database. No runtime coupling. They share only utility libraries and API key configuration.

---

## 💰 Business Impact

| Product | Primary Impact | Quantified Value |
|---------|---------------|-----------------|
| **Opportunity Radar** | 48 min/day saved per investor; surfaces ₹48K/year alpha per user | ₹179 cr/year subscription + ₹240 cr/year alpha |
| **Chart Pattern Intel** | Replaces ₹12K/year TradingView Pro; stock-specific edge | ₹240 cr/year value delivered |
| **Market ChatGPT** | Democratizes ₹25K–75K/year advisor access | ₹2,500 cr/year advisor value |
| **Video Engine** | Eliminates ₹2.2 cr/year manual production per format | ₹20 cr/year savings + ₹312 cr/year ad revenue |

### **Total addressable value: ₹3,000+ crore/year**

> *India's 14 crore demat holders deserve the same intelligence layer that hedge funds use. These four products deliver exactly that — at zero marginal cost.*

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- API keys (all free-tier): Gemini or Groq (for LLM), Tavily (for news search)

### 1. Clone & Configure

```bash
git clone https://github.com/dravv-alt/ET_GenAI_Hack.git
cd ET_GenAI_Hack
```

### 2. Run Any Product

Each product follows the same pattern:

```bash
# Backend
cd <product>/backend
python -m venv venv && venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn main:app --reload --port <port>

# Frontend (separate terminal)
cd <product>/frontend
npm install && npm run dev
```

| Product | Backend Port | Frontend Port |
|---------|-------------|--------------|
| Opportunity Radar | `8001` | `5173` |
| Chart Pattern Intel | `8002` | `3002` |
| Market ChatGPT | `8003` | `3003` |
| AI Market Video | `8004` | `3004` |

### 3. Verify

```bash
curl http://localhost:8001/health
# → {"status":"ok","service":"opportunity-radar","port":8001}
```

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.11 + FastAPI |
| **Frontend** | React (JSX) + Vite |
| **Database** | SQLite (zero-config, local persistence) |
| **LLM** | Gemini 2.0 Flash (free) · Groq (fallback) |
| **Market Data** | yfinance (free) · NSE public APIs |
| **News** | Tavily API (free 1000/month) |
| **Charts** | lightweight-charts · matplotlib · Plotly |
| **Video** | MoviePy + gTTS |
| **Design System** | Bloomberg Monochrome (IBM Plex Mono, zero-decoration) |

---

## 📂 Repository Structure

```
ET_GenAI_Hack/
├── readme.md                              ← You are here
│
├── opportunity-radar/                     ← Product 1: AI Signal Detection
│   ├── backend/                           ← FastAPI + SQLite + LLM agents
│   └── frontend/                          ← Bloomberg-style React terminal
│
├── chart-pattern-intel/                   ← Product 2: Pattern Detection + Backtesting
│   ├── backend/                           ← FastAPI + yfinance + pattern detectors
│   └── frontend/                          ← Interactive charting UI
│
├── market-chatgpt/                        ← Product 3: Portfolio-Aware AI Analyst
│   ├── backend/                           ← FastAPI + multi-agent RAG pipeline
│   └── frontend/                          ← Streaming chat interface
│
├── market-video-engine/                   ← Product 4: Automated Video Generation
│   ├── backend/                           ← FastAPI + matplotlib + MoviePy
│   └── frontend/                          ← Video generator + preview
│
├── shared/                                ← Shared utilities across all products
│   ├── market_data.py                     ← yfinance wrapper
│   ├── nse_fetcher.py                     ← NSE API helpers
│   ├── llm_client.py                      ← LLM wrapper (Gemini/Groq)
│   └── news_search.py                     ← Tavily news search
│
└── docs/                                  ← Architecture, API contracts, impact model
    ├── SYSTEM_OVERVIEW.md
    ├── IMPACT_MODEL.md
    └── ARCHITECTURE.md
```

---

## 👥 Team

| Member | Product Owned | Key Contribution |
|--------|--------------|-----------------|
| T1 | Opportunity Radar | Full-stack: NSE signal pipeline + Bloomberg terminal UI |
| T2 | Chart Pattern Intelligence | Pattern detection engine + stock-specific backtester |
| T3 | Market ChatGPT Next Gen | Multi-agent RAG pipeline + streaming chat |
| T4 | AI Market Video Engine | Automated video rendering + LLM narration |

---

## 📋 Submission Checklist

- [x] Public GitHub repo with full commit history
- [x] README with setup instructions and business pitch
- [x] `/docs/IMPACT_MODEL.md` — quantified business impact (₹3,000 cr/year TAV)
- [x] `/docs/SYSTEM_OVERVIEW.md` — system architecture
- [ ] 3-minute pitch video
- [x] Live demo of all 4 products working independently

---

<div align="center">

### The real impact isn't time saved. It's **democratizing the intelligence layer that has always been reserved for the top 1%.**

*Built in 12 hours at ET AI Hackathon 2026*

</div>
]]>