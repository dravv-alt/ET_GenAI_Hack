# PRD & Technical Analysis: Market ChatGPT — Next Gen

## 1. Executive Summary

**Product Vision**: The Economic Times (ET) currently offers a standard Market ChatGPT. While capable of answering broad financial queries, it functions largely as a generic stock-lookup and text-summarization tool. The challenge is to break this mold and reconstruct it as **Market ChatGPT Next Gen**—a profoundly personalized, agent-driven financial advisor.

**The "Apart from Current System" Differentiation**:
*   **Current System**: Answers "What is RELIANCE doing?" (Generic, stateless, zero personalization).
*   **Next Gen**: Answers "Based on RELIANCE's Q3 results, is my portfolio at risk, and should I trim my position?" (Personalized, portfolio-aware, multi-step reasoning, cited).

We are upgrading from a **query-response paradigm** to a **data-synthesizing agent paradigm**. 

---

## 2. Competitive & Gap Analysis (Current vs. Next Gen)

| Feature | Legacy ET Market ChatGPT | Market ChatGPT Next Gen |
| :--- | :--- | :--- |
| **Context Awareness** | General market knowledge up to training cut-off. | **Portfolio-Aware**: Injects user's actual holdings, quantities, and average buy price into the prompt sequence. |
| **Reasoning Depth** | Single-pass basic RAG (Retrieve & Generate). | **Multi-Step Agentic**: A Query Planner breaks down complex prompts into multiple sub-queries before synthesizing. |
| **Data Integration** | Generic surface web search. | **Deep Financial Hooks**: yFinance (price/fundamentals), Tavily (recent news), NSE Filings via lightweight RAG. |
| **Trust / Citing** | Often hallucinates figures or lacks sources. | **Source-Cited Responses**: Every factual claim is bound to a clickable source badge (strict schema generation). |
| **UX & Delivery** | Wait 10 seconds, get a wall of text. | **Reactive Streaming**: Token-by-token SSE streaming, inline Signal Cards (Bullish/Bearish), and 'Thinking' indicators. |

---

## 3. Product Features & Requirements

### 3.1. Portfolio Integration (The "Personal Advisor" Pillar)
*   **Requirement**: Users must be able to upload a CSV of their holdings (`ticker`, `quantity`, `avg_buy_price`).
*   **Execution**: The backend must instantly normalize tickers (e.g., appending `.NS`), fetch live LTP (Last Traded Price) via yFinance, and render an interactive P&L table on the frontend before any chat begins.
*   **Why it matters**: The LLM's system prompt will be explicitly populated with the portfolio state, allowing it to perform weighted impact analysis on the user's net worth rather than abstract market commentary.

### 3.2. Agentic Multi-Step Analysis (The "Deep Reasoning" Pillar)
*   **Requirement**: The system cannot just search the user's raw string. It must decompose queries.
*   **Execution**: Implement an Agent-based Orchestration Pipeline:
    1.  **Query Planner LLM**: Reads "How does tech guidance impact me?" and translates it into `["INFY.NS revenue guidance", "TCS.NS Q3 results", "WIPRO.NS recent block deals"]`.
    2.  **Retrieval Agent**: Iterates over the planned queries, hitting external APIs in parallel.
    3.  **Analysis Agent**: Compiles the retrieved docs against the user's uploaded portfolio context and generates the final narrative.

### 3.3. Deeper Data Integration
*   To enable real intelligence, the Retrieval Agent must hit three specialized pillars:
    *   **Price Dynamics & Fundamentals**: Market cap, PE, EPS, 52W High/Low via `yfinance`.
    *   **Live News & Sentiment**: Rapid scraping of recent headlines via `tavily-python` or News APIs.
    *   **Corporate Filings**: A lightweight local SQLite RAG store containing recent NSE corporate announcements or earnings transcripts.

### 3.4. Strict Citations & Hallucination Mitigation
*   **Requirement**: The user's trust is paramount. 0% hallucination tolerance.
*   **Execution**: The LLM will be instructed to (1) ONLY use the context provided by the Retrieval Agent, and (2) emit structured JSON citation blocks. 
*   **Frontend Impact**: The chat window will feature clickable `SourceChip` components at the bottom of messages, referencing exactly where the agent derived a PAT growth percentage or a deal win stat.

---

## 4. Super Detailed System Architecture

### 4.1. The Backend (FastAPI - Port 8003)
The backend architecture relies on highly decoupled services communicating asynchronously.

*   `POST /portfolio/parse`: Ingests CSV, handles real-time hydration of LTP (Last Traded Price). Validates ticker integrity.
*   `POST /chat`: Uses Server-Sent Events (SSE) to stream back distinct event types:
    *   `thinking`: Allows the frontend to show "Analyzing INFY results..." while the Query Planner runs.
    *   `token`: The actual prose response streaming in chunks.
    *   `signal_card`: A structured payload `{"ticker": "INFY.NS", "signal": "bearish", "reasons": [...]}` injected dynamically into the chat UI.
    *   `source`: URL and Title metadata for citations.

### 4.2. The Frontend (Vite + React - Port 3003)
*   **Upload flow**: Drag-and-drop CSV `PortfolioUploader.jsx` parses locally and visually verifies data in `HoldingsTable.jsx`.
*   **Chat flow**: `ChatWindow.jsx` listens to the SSE stream. 
*   **Reactive UI**: When the backend streams a `signal_card` event, the UI renders a rich, color-coded widget (e.g., Red for Bearish, Green for Bullish) inline within the chat bubble, breaking up the text wall.
*   **Contextual Prompts**: `SuggestedQuestions.jsx` will dynamically populate prompts based on the uploaded CSV (e.g., "Which of my 5 holdings took the biggest hit today?").

---

## 5. Development Roadmap & Execution Strategy

1.  **Foundation (Day 1)**: Setup FastAPI & Vite. Define standard Pydantic schema for SSE streaming `(SSEEvent, Message, Holding)`. Establish mock streaming data to build frontend components `(MessageBubble, SignalCard, SourceChip)`.
2.  **Data Ingestion (Day 1)**: Build the CSV parsing route. Connect `yfinance` to fetch live prices and calculate absolute/percentage P&L.
3.  **Agent Orchestration (Day 2)**: 
    *   Build the `Query Planner` using LangChain/Anthropic/OpenAI prompt engineering.
    *   Flesh out the `Retrieval Agent` (wiring up Tavily for news, yFinance for fundamentals).
    *   Build the `Analysis Agent` to synthesize and format outputs (stripping markdown, enforcing JSON signal drops).
4.  **UI Polish & Integration (Day 3)**: Wire the SSE endpoints in React. Ensure smooth visual transitions (thinking spinners, dynamic text append). Perform rigorous edge-case testing (e.g., what if a ticker is invalid? What if the LLM refuses to answer?).

---

## 6. Success Metrics
*   **Reduction in hallucination rate**: Down to < 1% due to strict RAG context limits.
*   **Increased Engagement**: Users engaging in 3+ multi-turn conversations because answers are deeply tied to their genuine financial health rather than generic market trivia.
*   **Perceived Speed**: Time-to-first-token (TTFT) < 2.5 seconds via streaming, offset by intelligent `thinking` updates while background retrieval happens.
