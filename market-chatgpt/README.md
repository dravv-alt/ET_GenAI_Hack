# Market ChatGPT Next Gen

Welcome to the **Market ChatGPT Next Gen** implementation for the ET AI Hackathon 2026!

This project transforms a standard stock lookup bot into a **deeply personalized Agentic Financial Advisor** powered by ultra-fast Groq LLM inference, dynamic data retrieval, and a strict Bloomberg Terminal-style minimalist React UI.

---

## 🏗 System Architecture

The project is split into two primary folders: `backend/` and `frontend/`.

### The Backend (FastAPI + Groq Engine + Python Agents)
*   **API:** `FastAPI` serves the endpoints for parsing portfolios (`/portfolio/parse`) and generating agentic streaming chat responses (`/chat`).
*   **LLM Provider:** We use the `Groq` SDK (`llama3-70b-8192`) because it offers extreme TTFT (Time To First Token) speeds, essential for multi-step agent reasoning without causing massive UI latency.
*   **Agent Pipeline:**
    *   **Planner (`agents/query_planner.py`):** Breaks the user's plain-English question down into a JSON array of `sub-queries` explicitly mapped to their portfolio holdings.
    *   **Retriever (`agents/retrieval_agent.py`):** Hits `Tavily` for internet news and `yFinance` for real-time market data matching the sub-queries.
    *   **Orchestrator (`agents/orchestrator.py`):** The mastermind loop. Relays `[ PLANNING... ]` state to the frontend, streams tokens continuously, parses output for strict JSON `SignalCards` (Bullish/Bearish), and mandates Source citation URLs to kill hallucinations.

### The Frontend (React + Vite + Bloomberg Monochrome System)
*   **Bloomberg Monochrome:** The frontend aggressively enforces a specialized financial data aesthetics engine. No rounded corners (`border-radius: 0`), flat 1px borders, zero box-shadows, and pure monospace typography (`IBM Plex Mono`). Red/Green are exclusively utilized for directional indicators.
*   **Real-time Streaming:** Consumes Server-Sent Events (SSE) via the browser's native `TextDecoder` to update arrays dynamically and print tokens linearly as the LLM dictates them.
*   **Failsafe Loading:** Intelligently bypasses live CSV API bottlenecks (like `yFinance` timeouts) by offering a "Load Demo Portfolio" failsafe with pre-seeded data right in the `PortfolioUploader.jsx` pane.

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
*Note: Make sure `.env` contains your `GROQ_API_KEY` and `TAVILY_API_KEY`.*

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

---

## 🎨 Notable Technical Decisions

*   **Replacing "Standard Bubbles"**: By adhering blindly to the `Bloomberg Monochrome` framework, we eliminated modern UX conventions (like standard messaging bubbles) in favor of grid layouts and `SignalCards`. This establishes the tool as an institutional product, not an entry-level consumer app.
*   **Mitigating CSV Parse Errors:** yFinance APIs can rate-limit or fail unexpectedly during live fast-paced hackathons. We've hardcoded a robust **[ FAILSAFE ] LOAD DEMO PORTFOLIO** override into the React component to instantaneously populate state if the CSV backend falters.
*   **No LangChain Overhead**: While we could use full LangChain logic strings, custom orchestrators (as built in `orchestrator.py`) stream specific internal thought markers (like the `thinking` event) to the frontend much cooler and faster than out-of-the-box abstraction layers!
