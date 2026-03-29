# ET AI Hackathon 2026 — PS 6: AI for the Indian Investor

> **Hackathon:** ET AI Hackathon 2026 | Avataar.ai + Unstop
> **Problem Statement:** #6 — AI for the Indian Investor
> **Team size:** 4 members | **Duration:** 12 hours
> **Stack:** Python 3.11 + FastAPI · React (JSX) · Vite · TailwindCSS · SQLite

---

## Overview

This repo contains **4 independent AI products** built in parallel by 4 teammates.
Each product solves a different piece of PS 6. They share a common tech stack
and a shared `/shared/` utilities folder, but are otherwise fully independent —
one teammate going down does NOT block others.

---

## The 4 products

| # | Product | Teammate | Folder | Status |
|---|---------|----------|--------|--------|
| 1 | **Opportunity Radar** | T1 | `/opportunity-radar/` | 🔴 Todo |
| 2 | **Chart Pattern Intelligence** | T2 | `/chart-pattern-intel/` | 🔴 Todo |
| 3 | **Market ChatGPT — Next Gen** | T3 | `/market-chatgpt/` | 🔴 Todo |
| 4 | **AI Market Video Engine** | T4 | `/market-video-engine/` | 🔴 Todo |

> Update status as you build: 🔴 Todo → 🟡 In Progress → 🟢 Done

---

## Repository structure

```
et-ai-hackathon-ps6/
│
├── README.md                          ← YOU ARE HERE
│
├── shared/                            ← Shared utilities (all teammates use this)
│   ├── market_data.py                 ← yfinance wrapper (OHLCV, fundamentals)
│   ├── nse_fetcher.py                 ← NSE public API helpers
│   ├── llm_client.py                  ← LLM wrapper (Claude / GPT-4o)
│   ├── news_search.py                 ← Tavily API news search
│   └── .env.example                   ← All API keys needed across all products
│
├── opportunity-radar/                 ← T1's product
│   ├── README.md                      ← T1's full guide (start here if you're T1)
│   ├── backend/
│   │   ├── main.py                     ← FastAPI entrypoint
│   │   ├── requirements.txt
│   │   ├── db/                         ← SQLite helpers + schema
│   │   ├── data/                       ← small JSON fallbacks for dev
│   │   ├── routes/
│   │   ├── agents/
│   │   ├── services/
│   │   └── models/
│   └── frontend/
│       ├── index.html
│       ├── package.json
│       ├── vite.config.js
│       ├── public/
│       └── src/
│           ├── main.jsx
│           ├── App.jsx
│           ├── components/
│           ├── lib/
│           └── styles.css
│
├── chart-pattern-intel/               ← T2's product
│   ├── README.md                      ← T2's full guide
│   ├── backend/
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   ├── db/
│   │   ├── data/
│   │   ├── routes/
│   │   ├── detectors/
│   │   ├── backtester/
│   │   ├── services/
│   │   └── models/
│   └── frontend/
│       ├── index.html
│       ├── package.json
│       ├── vite.config.js
│       ├── public/
│       └── src/
│           ├── main.jsx
│           ├── App.jsx
│           ├── components/
│           ├── lib/
│           └── styles.css
│
├── market-chatgpt/                    ← T3's product
│   ├── README.md                      ← T3's full guide
│   ├── backend/
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   ├── db/
│   │   ├── data/
│   │   ├── routes/
│   │   ├── agents/
│   │   ├── services/
│   │   └── models/
│   └── frontend/
│       ├── index.html
│       ├── package.json
│       ├── vite.config.js
│       ├── public/
│       └── src/
│           ├── main.jsx
│           ├── App.jsx
│           ├── components/
│           ├── lib/
│           └── styles.css
│
├── market-video-engine/               ← T4's product
│   ├── README.md                      ← T4's full guide
│   ├── backend/
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   ├── db/
│   │   ├── data/
│   │   ├── routes/
│   │   ├── generators/
│   │   ├── rendering/
│   │   ├── services/
│   │   └── models/
│   └── frontend/
│       ├── index.html
│       ├── package.json
│       ├── vite.config.js
│       ├── public/
│       └── src/
│           ├── main.jsx
│           ├── App.jsx
│           ├── components/
│           ├── lib/
│           └── styles.css
│
└── docs/
    ├── ARCHITECTURE.md                ← Full system design for all 4 products
    ├── API_CONTRACTS.md               ← All endpoints across all 4 products
    ├── KICKOFF_CHECKLIST.md           ← First 30 minutes before coding
    ├── TIMELINE.md                    ← Hour-by-hour plan for all 4 teammates
    └── IMPACT_MODEL.md                ← Quantified business impact (submission req)
```

---

## Shared setup (everyone does this first — H0 to H0:30)

### 1. Clone repo and install shared deps

```bash
git clone https://github.com/dravv-alt/ET_GenAI_Hack.git
cd ET_GenAI_Hack
cp shared/.env.example shared/.env
# Fill in your API keys in shared/.env
```

### 2. Shared environment variables

```env
# shared/.env — fill these in before ANYONE starts coding

ANTHROPIC_API_KEY=sk-ant-api03-xxxxx        # LLM (preferred)
OPENAI_API_KEY=sk-xxxxx                      # LLM (fallback)
LLM_MODEL=claude-sonnet-4-20250514           # or: gpt-4o

TAVILY_API_KEY=tvly-xxxxx                    # News search — free 1000/month
                                             # Sign up: app.tavily.com

# No other API keys needed — yfinance and NSE are free/public
```

### 3. Install Python shared deps

```bash
pip install fastapi uvicorn yfinance pandas ta-lib requests python-dotenv \
            anthropic openai langchain tavily-python pillow \
            moviepy matplotlib plotly

# SQLite (standard library) is used for fast local storage in all backends
```

### 4. Install Node shared deps (per frontend)

```bash
cd <product>/frontend
npm install     # Vite + React (JSX) setup per product
```

### 5. Verify everything works

```bash
python -c "import yfinance as yf; print(yf.Ticker('RELIANCE.NS').fast_info)"
# Should print Reliance's current price info
```

---

## How products connect for the demo

The 4 products are **independent** and demoed separately. For the final pitch:

- **T4 (Demo Lead)** runs a unified demo that shows all 4 products back to back
- Each product runs on its own port: Radar=3001, Charts=3002, ChatGPT=3003, Video=3004
- The 3-minute video shows each product completing its core workflow

---

## Sync checkpoints

| Time | What to share | Format |
|------|--------------|--------|
| H3 | Each person demos their MVP skeleton | 2 min screen share each |
| H6 | Core feature working | 2 min demo each |
| H9 | Full flow working, demo dry run | 5 min full walkthrough |
| H11 | Record pitch video, final push | All together |

---

## Submission requirements checklist

- [ ] Public GitHub repo with full commit history showing 12-hour build
- [ ] This README with setup instructions
- [ ] `/docs/ARCHITECTURE.md` — all 4 agent architectures (1–2 pages)
- [ ] `/docs/IMPACT_MODEL.md` — quantified business impact
- [ ] 3-minute pitch video (record at H10–H11)
- [ ] Live demo of all 4 products working

---

*Each teammate: go directly to your product's `README.md` for your full guide.*