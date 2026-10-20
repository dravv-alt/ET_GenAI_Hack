# Market ChatGPT Next Gen

Welcome to the **Market ChatGPT Next Gen** implementation for the ET AI Hackathon 2026!

This project transforms a standard stock lookup bot into a **deeply personalized Agentic Financial Advisor** powered by ultra-fast Groq LLM inference, dynamic global data retrieval, and a strict Bloomberg Terminal-style minimalist React UI.

---

## 🏗 System Architecture & Major Upgrades

The project is split into two primary folders: `backend/` and `frontend/`.

### The Backend (FastAPI + Groq Engine + Python Agents)
*   **API:** `FastAPI` serves endpoints for parsing portfolios (`/portfolio/parse`), generating targeted AI questions (`/portfolio/questions`), pushing live market feeds (`/market/live`), and generating agentic streaming chat responses (`/chat`).
*   **Global Market Data:** Leverages `yfinance` to query over 60+ global exchanges. Hardcoded limitations to Indian `.NS` tickers have been completely removed.
*   **Free Unlimited News Retrieval:** Replaced rate-limited Tavily configurations with `duckduckgo-search` to fetch real-time news across global stock queries seamlessly, fast, and at zero cost.
*   **LLM Provider:** We use the `Groq` SDK (`llama-3.3-70b-versatile`) because it offers extreme TTFT (Time To First Token) speeds, essential for multi-step agent reasoning without causing massive UI latency.
*   **Agent Pipeline:**
    *   **Planner (`query_planner.py`):** Breaks user queries down into sub-queries mapped actively to their portfolio and dashboard tab context.
    *   **Retriever (`retrieval_agent.py`):** Hits DuckDuckGo for unstructured internet news and `yfinance` for real-time OHLCV fundamentals matching sub-queries.
    *   **Orchestrator (`orchestrator.py`):** The mastermind loop. Relays `[ PLANNING... ]` state to the frontend, streams tokens continuously, outputs strict JSON `SignalCards` (Bullish/Bearish), and mandates Source citation URLs to kill hallucinations.

### The Frontend (React + Vite + Bloomberg Monochrome System)
*   **Bloomberg Monochrome UI:** The frontend aggressively enforces a specialized financial aesthetic. Pure monospace typography (`IBM Plex Mono`), strict 1px grid layouts, and active color coding restricted entirely to directional indicators (Green for Positive P&L, Red for Negative).
*   **Global Market Dashboard:** Instead of just a fixed array of NIFTY 100 stocks, you can instantly toggle views across the **S&P 500, NASDAQ, FTSE, DAX, Nikkei 225, Crypto Top 10, and FX Majors**.
*   **Top Index Ribbon & VIX:** An ever-present marquee showing live benchmarks (`^NSEI`, `^GSPC`, `BTC-USD`) and calculating the current Market Fear/Greed via the CBOE Volatility Index (`^VIX`).
*   **Inline SVG Sparklines:** The active dashboard now pulls customized 5-day historical tick data to plot native SVG mini-trendlines directly inline on every grid row.
*   **Risk Auditing:** Parsing your `.csv` triggers real-time computation of your portfolio's **Concentration Risk %** alerting you of top-heavy vulnerabilities.
*   **Intelligent Prompt Engine:** Submitting your portfolio instantly calls Groq in the background to procedurally generate 5 custom investment questions unique to **your** specific holdings. 
*   **Audio Recognition:** Added native `Web Speech API` support into the Chat Interface allowing immediate hands-free dictation of complex prompt parameters.

---

## 🚀 How to Run the Project

### 1. The Backend
To spin up the Python backend server:

```bash
cd market-chatgpt/backend
# Setup virtual environment if you haven't:
# python -m venv venv && source venv/bin/activate
# pip install -r requirements.txt

# Run the dev server
uvicorn main:app --reload --port 8003
```
*Note: Ensure `.env` contains your `GROQ_API_KEY`! (No Tavily key is needed anymore due to DuckDuckGo search integration).*

### 2. The Frontend
Ensure Node.js is installed, then:

```bash
cd market-chatgpt/frontend
# Install packages
# npm install

# Run the dev server
npm run dev -- --port 3003
```

Navigate to [http://localhost:3003](http://localhost:3003) to open the Terminal!
