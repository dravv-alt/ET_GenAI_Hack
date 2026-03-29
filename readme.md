# ET AI Terminal Hub — AI for the Indian Investor

> **Hackathon:** ET AI Hackathon 2026 | Avataar.ai + Unstop
> **Problem Statement:** #6 — AI for the Indian Investor
> **Team size:** 4 members | **Duration:** 12-hour build

---

## 📖 The Narrative: What We Are Solving

Indian retail investors face a severely fragmented digital ecosystem. To make an informed trade, an everyday investor has to cross-reference static OHLCV charts from their broker, read scattered news articles on financial portals, and manually dig through complex NSE corporate filings. This disjointed experience is overwhelming and leads to missed opportunities that institutional investors capitalize on instantly.

**Our solution is the ET AI Terminal Hub.** 

We have built an institutional-grade, AI-native financial terminal tailored specifically for the Indian investor. By combining blazing-fast Large Language Models (LLMs), Python-driven data scraping, and a sleek Bloomberg-inspired React interface, we've created a unified dashboard that automates qualitative and quantitative analysis.

---

## 🚀 App Overview & End-to-End Workflow

The platform operates as a massive Master Terminal Hub (`et-genai-hub`) that seamlessly houses 4 proprietary, parallel AI engines. Each engine solves a distinct piece of the investment life-cycle, and together they form an unstoppable retail investing suite:

### 1. Opportunity Radar (The Scout)
Instead of forcing investors to read complex PDFs, our AI agents continuously scan the NSE for bulk deals, insider trading, and corporate sentiment shifts. Using LLM-driven analytics, it ranks these events and surfaces non-obvious trading signals in a sleek, real-time alert feed.

### 2. Chart Pattern Intelligence (The Analyst)
A fully automated visual technical analysis engine. It instantly detects complex setups (Breakouts, Head & Shoulders, Support/Resistance) and calculates momentum indicators. More importantly, it dynamically backtests these patterns against historical data so you know exactly what your statistical edge is before you trade.

### 3. Market ChatGPT — Next Gen (The Advisor)
A completely voice-enabled conversational AI terminal deeply integrated with live global market data (via yFinance) and real-time news (via DuckDuckGo). Users can upload their latest Portfolio CSVs, and the AI will critically analyze their holdings, calculate concentration risk scores, and suggest personalized, actionable investment questions.

### 4. AI Market Video Engine (The Synthesizer)
Not everyone wants to read charts at the end of the day. This generative engine takes the closing market performance and autonomously synthesizes a daily "Market Wrap" video, complete with trending sector rotation visuals, race charts, and multi-lingual Text-to-Speech (TTS) narrations.

---

## 🛠 Tech Stack

- **Backend:** Python 3.11 + FastAPI + SQLite (for high-speed local data caching).
- **Frontend:** React (JSX) + Vite + Standard CSS (Institutional Bloomberg Monochrome aesthetic).
- **AI Infrastructure:** Groq (Llama-3), Anthropic (Claude), and OpenAI (GPT-4o).
- **Data Layers:** `yfinance` (Global market data), `nse_fetcher` (Indian public APIs), and `duckduckgo-search` (Unlimited, keyless news retrieval).

---

## ⚙️ Environment Variables (.env)

Before starting the applications, create a `.env` file in the `/shared/` directory.

We have heavily optimized our dependencies to rely on free, public APIs wherever possible. **You do NOT need a Tavily key for news anymore, as we upgraded the system to use keyless DuckDuckGo search!**

```env
# shared/.env

# 1. LLM Providers (Provide the ones you wish to use)
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx        # Preferred logic engine
OPENAI_API_KEY=sk-proj-xxxxx                 # Fallback engine
GROQ_API_KEY=gsk_xxxxx                       # Used for blazing fast portfolio analysis QA

# Note: yfinance, NSE, and DuckDuckGo news operate completely free and require no keys.
```

---

## 💻 Running the Master Terminal Hub

The 4 products run effectively as micro-services. To experience the full Terminal Hub:

### Step 1: Install Dependencies
```bash
# Python dependencies
pip install fastapi uvicorn yfinance pandas ta-lib requests python-dotenv \
            anthropic openai langchain duckduckgo-search pillow moviepy

# Run 'npm install' inside the 4 frontend folders + the hub
```

### Step 2: Boot the AI Backends
Open 4 separate terminal tabs and spin up the FastAPI services for each engine:
```bash
cd opportunity-radar/backend && uvicorn main:app --port 8001
cd chart-pattern-intel/backend && uvicorn main:app --port 8002
cd market-chatgpt/backend && uvicorn main:app --port 8003
cd market-video-engine/backend && uvicorn main:app --port 8004
```

### Step 3: Boot the Vite Frontends
Open 4 more terminal tabs and boot their respective UIs:
```bash
cd opportunity-radar/frontend && npm run dev -- --port 3001
cd chart-pattern-intel/frontend && npm run dev -- --port 3002
cd market-chatgpt/frontend && npm run dev -- --port 3003
cd market-video-engine/frontend && npm run dev -- --port 3004
```

### Step 4: Launch the Unified Demo Hub
Finally, launch the master iframe shell that ties them all together beautifully into one UI:
```bash
cd et-genai-hub
npm run dev
```
Navigate to your **et-genai-hub URL (usually `http://localhost:5173`)**. 

You will now have a cohesive, tabbed Bloomberg-style terminal allowing you to seamlessly swap between all 4 AI engines in a single interface!