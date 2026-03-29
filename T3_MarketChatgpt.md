# T3 — Market ChatGPT Next Gen

> **Your product:** ET already has a Market ChatGPT. Your challenge: break it and rebuild it
> better. Deeper data integration, multi-step analysis, portfolio-aware answers,
> and source-cited responses.
>
> **You own:** Everything in `/market-chatgpt/`
> **Your port:** `backend=8003`, `frontend=3003`
> **Dependency on teammates:** Only `shared/` utilities — you are fully independent.

---

## What you are building

A chat interface where a user can:
1. Upload their portfolio (CSV of holdings)
2. Ask complex, multi-step investment questions in plain English
3. Get answers that are **aware of their specific portfolio**, not generic

The AI agent:
- Breaks complex questions into sub-queries internally
- Fetches live market data, news, and NSE filings for each relevant holding
- Reasons across all of it and writes a coherent answer
- Cites **every factual claim** with a clickable source link
- Streams the response live (tokens appear as they're generated)
- Maintains conversation history for follow-up questions

**The key differentiation from existing ET Market ChatGPT:**
- It knows YOUR holdings — it answers "is my portfolio at risk?" not just "what is RELIANCE doing?"
- Multi-step reasoning — it doesn't just retrieve and summarize, it reasons
- Every claim has a source — no hallucinated facts

---

## Folder structure

```
market-chatgpt/
├── README.md                          ← YOU ARE HERE
│
├── backend/
│   ├── main.py                        ← FastAPI app (port 8003)
│   ├── requirements.txt
│   │
│   ├── routes/
│   │   ├── portfolio.py               ← POST /parse-portfolio
│   │   └── chat.py                    ← POST /chat (SSE streaming)
│   │
│   ├── agents/
│   │   ├── orchestrator.py            ← Master loop: plan → retrieve → analyze → cite
│   │   ├── query_planner.py           ← LLM breaks question into sub-queries
│   │   ├── retrieval_agent.py         ← Fetches data for each sub-query
│   │   ├── analysis_agent.py          ← LLM reasoning over retrieved context
│   │   └── citation_agent.py          ← Injects source URLs into answer
│   │
│   ├── services/
│   │   ├── market_data.py             ← yfinance: price, OHLCV, fundamentals
│   │   ├── news_fetcher.py            ← Tavily: recent news per ticker
│   │   ├── rag.py                     ← ChromaDB: RAG over NSE filings
│   │   └── llm.py                     ← LLM client + all prompt templates
│   │
│   └── models/
│       ├── portfolio.py               ← Pydantic: Holding, Portfolio, ParseResponse
│       └── chat.py                    ← Pydantic: ChatRequest, Message, SSEEvent
│
└── frontend/
    ├── package.json
    ├── next.config.js
    ├── tailwind.config.js
    └── app/
        ├── layout.tsx
        ├── page.tsx                   ← Portfolio upload landing page
        ├── chat/page.tsx              ← Main chat interface
        └── globals.css
    └── components/
        ├── PortfolioUploader.tsx      ← CSV drag-drop + holdings table display
        ├── HoldingsTable.tsx          ← Table: ticker, qty, avg buy, current, P&L
        ├── ChatWindow.tsx             ← SSE streaming chat container
        ├── MessageBubble.tsx          ← One message: text + source chips
        ├── SignalCard.tsx             ← Bullish/bearish card inline in chat
        ├── SourceChip.tsx             ← Clickable citation badge
        ├── ThinkingIndicator.tsx      ← "Analyzing your portfolio..." spinner
        └── SuggestedQuestions.tsx     ← Pre-set questions based on portfolio
    └── lib/
        ├── api.ts
        ├── types.ts
        └── mockData.ts
```

---

## Hour-by-hour plan

### H0–H1: Setup + models + mock data

**Goal:** Next.js running at 3003, FastAPI at 8003. Frontend can show mock chat.

```bash
# Backend
cd market-chatgpt/backend
python -m venv venv && source venv/bin/activate
pip install fastapi uvicorn python-multipart yfinance pandas anthropic openai \
            langchain chromadb tavily-python python-dotenv
uvicorn main:app --reload --port 8003

# Frontend
cd market-chatgpt/frontend
npm install && npm run dev -- --port 3003
```

**Write Pydantic models first (`models/chat.py`):**

```python
# models/chat.py
from pydantic import BaseModel
from enum import Enum

class SSEEventType(str, Enum):
    THINKING = "thinking"
    TOKEN = "token"
    SIGNAL_CARD = "signal_card"
    SOURCE = "source"
    DONE = "done"
    ERROR = "error"

class SSEEvent(BaseModel):
    type: SSEEventType
    content: str | dict | None = None
    url: str | None = None
    title: str | None = None

class Message(BaseModel):
    role: str           # "user" or "assistant"
    content: str

class Holding(BaseModel):
    ticker: str         # must end in .NS
    quantity: int
    avg_buy_price: float

class ChatRequest(BaseModel):
    question: str
    portfolio: list[Holding]
    conversation_history: list[Message] = []
```

**Mock data for frontend (`lib/mockData.ts`):**

```typescript
// Use this while backend is being built
export const MOCK_SSE_EVENTS = [
  { type: 'thinking', content: 'Analyzing your 5 holdings...' },
  { type: 'thinking', content: 'Fetching Q3 results for INFY and RELIANCE...' },
  { type: 'token', content: 'Based on recent Q3 results, ' },
  { type: 'token', content: 'INFY faces headwinds in its US business, ' },
  { type: 'token', content: 'having cut revenue guidance by 1.5%. ' },
  { type: 'signal_card', content: { ticker: 'INFY.NS', signal: 'bearish', confidence: 0.71,
    reasons: ['Revenue guidance cut 1.5%', 'Deal ramp delays in North America'] }},
  { type: 'token', content: 'RELIANCE however reported strong PAT growth of 8.2%...' },
  { type: 'signal_card', content: { ticker: 'RELIANCE.NS', signal: 'bullish', confidence: 0.84,
    reasons: ['PAT beat by 8.2%', 'Jio subscriber growth 12% YoY'] }},
  { type: 'source', url: 'https://nseindia.com/...', title: 'INFY Q3 FY24 Results' },
  { type: 'source', url: 'https://economictimes.com/...', title: 'Reliance Q3 profit rises 8%' },
  { type: 'done', content: null },
];
```

---

### H1–H3: Portfolio parser + market data service

**Portfolio CSV parser (`routes/portfolio.py`):**

```python
# routes/portfolio.py
from fastapi import APIRouter, UploadFile, File, HTTPException
import csv, io, yfinance as yf, time

router = APIRouter(prefix="/portfolio", tags=["portfolio"])

@router.post("/parse")
async def parse_portfolio(file: UploadFile = File(...)):
    """
    Accepts CSV with header: ticker,quantity,avg_buy_price
    Returns holdings with current prices and P&L calculated
    """
    content = await file.read()
    decoded = content.decode('utf-8')
    reader = csv.DictReader(io.StringIO(decoded))

    required_cols = {'ticker', 'quantity', 'avg_buy_price'}
    if not required_cols.issubset(set(reader.fieldnames or [])):
        raise HTTPException(400, f"CSV must have columns: {required_cols}")

    holdings = []
    for i, row in enumerate(reader, start=2):
        ticker = row['ticker'].strip().upper()
        if not ticker.endswith('.NS'):
            ticker += '.NS'

        try:
            qty = int(row['quantity'])
            avg_price = float(row['avg_buy_price'])
        except ValueError:
            raise HTTPException(400, f"Row {i}: quantity and avg_buy_price must be numbers")

        # Fetch current price
        time.sleep(0.2)
        stock = yf.Ticker(ticker)
        info = stock.fast_info
        current_price = getattr(info, 'last_price', avg_price)  # fallback to avg if unavailable

        pnl_abs = (current_price - avg_price) * qty
        pnl_pct = ((current_price - avg_price) / avg_price) * 100

        holdings.append({
            "ticker": ticker,
            "quantity": qty,
            "avg_buy_price": avg_price,
            "current_price": round(current_price, 2),
            "pnl_abs": round(pnl_abs, 2),
            "pnl_pct": round(pnl_pct, 2),
            "value": round(current_price * qty, 2),
        })

    total_invested = sum(h['avg_buy_price'] * h['quantity'] for h in holdings)
    total_value = sum(h['value'] for h in holdings)

    return {
        "holdings": holdings,
        "summary": {
            "total_invested": round(total_invested, 2),
            "total_current_value": round(total_value, 2),
            "total_pnl_abs": round(total_value - total_invested, 2),
            "total_pnl_pct": round((total_value - total_invested) / total_invested * 100, 2),
            "holdings_count": len(holdings),
        }
    }
```

---

### H3–H6: The agent pipeline (most important part)

This is the core of your product. Build it step by step.

**Step 1: Query planner (`agents/query_planner.py`)**

```python
# agents/query_planner.py
import sys, json
sys.path.append("../../shared")
from llm_client import call_llm

PLANNER_PROMPT = """
The user has asked: "{question}"

Their portfolio contains these stocks: {tickers}

Your job: break this question into specific data-retrieval sub-queries needed to answer it fully.
Only generate sub-queries for stocks RELEVANT to the question.
Return ONLY a valid JSON array of strings. No explanation. No markdown.

Example output: ["RELIANCE.NS Q3 FY24 earnings results", "INFY.NS revenue guidance 2024", "HDFC.NS NPA ratio Q3"]
Maximum {max_queries} sub-queries.
"""

def plan(question: str, portfolio: list, max_queries: int = 8) -> list[str]:
    tickers = [h['ticker'] for h in portfolio]
    prompt = PLANNER_PROMPT.format(
        question=question,
        tickers=", ".join(tickers),
        max_queries=max_queries,
    )
    response = call_llm(prompt)
    try:
        # Strip markdown if LLM wraps in backticks
        clean = response.strip().strip('`').replace('json', '').strip()
        return json.loads(clean)
    except:
        # Fallback: generate one query per ticker
        return [f"{t} latest news and earnings" for t in tickers[:4]]
```

**Step 2: Retrieval agent (`agents/retrieval_agent.py`)**

```python
# agents/retrieval_agent.py
import sys
sys.path.append("../../shared")
from shared.market_data import get_fundamentals
from shared.news_search import search_news

def retrieve(sub_queries: list[str], portfolio: list) -> list[dict]:
    """
    For each sub-query: fetch price data + news + fundamentals.
    Returns list of context docs with: content, url, source_type, ticker
    """
    context_docs = []
    tickers_in_portfolio = {h['ticker'] for h in portfolio}

    for query in sub_queries:
        # Find which ticker this query is about
        ticker = None
        for t in tickers_in_portfolio:
            if t.replace('.NS', '').lower() in query.lower():
                ticker = t
                break

        # Fetch news for this query
        news_results = search_news(query, max_results=3)
        for article in news_results:
            context_docs.append({
                "content": f"[NEWS] {article['title']}\n{article['content'][:500]}",
                "url": article['url'],
                "source_type": "news",
                "ticker": ticker,
                "query": query,
            })

        # Fetch fundamentals if ticker identified
        if ticker:
            try:
                fundamentals = get_fundamentals(ticker)
                context_docs.append({
                    "content": f"[FUNDAMENTALS] {ticker}: PE={fundamentals.get('pe_ratio')}, "
                               f"EPS={fundamentals.get('eps')}, MarketCap={fundamentals.get('market_cap')}",
                    "url": f"https://finance.yahoo.com/quote/{ticker}",
                    "source_type": "fundamentals",
                    "ticker": ticker,
                    "query": query,
                })
            except:
                pass

    return context_docs
```

**Step 3: Analysis agent + Orchestrator (`agents/orchestrator.py`)**

```python
# agents/orchestrator.py
import json, asyncio, sys
from fastapi.responses import StreamingResponse
sys.path.append("../../shared")
from llm_client import stream_llm

ANALYSIS_PROMPT = """
You are a senior equity analyst at India's top brokerage.
The user's question: {question}

Their portfolio:
{portfolio_str}

Market data and news retrieved (use ONLY these facts — do not add facts you don't see here):
{context_str}

Instructions:
1. Answer the question directly and specifically — mention the user's actual holdings
2. Use real numbers from the data above. Never fabricate statistics.
3. For each stock you discuss, include a SIGNAL: bullish/bearish/neutral and 2-3 reasons
4. Keep your total answer under 350 words
5. After your answer, output a JSON block like this (EXACTLY this format):
   SIGNALS_JSON: [{{"ticker": "RELIANCE.NS", "signal": "bullish", "confidence": 0.84, "reasons": ["reason1", "reason2"]}}]
"""

async def run(question: str, portfolio: list, history: list):
    from agents.query_planner import plan
    from agents.retrieval_agent import retrieve

    async def event_stream():
        yield f"data: {json.dumps({'type': 'thinking', 'content': 'Planning analysis...'})}\n\n"

        sub_queries = plan(question, portfolio)
        tickers_mentioned = set(q.split('.NS')[0].split()[0] for q in sub_queries)

        yield f"data: {json.dumps({'type': 'thinking', 'content': f'Fetching data for {len(sub_queries)} queries...'})}\n\n"

        context_docs = retrieve(sub_queries, portfolio)

        # Build prompt
        portfolio_str = "\n".join([
            f"- {h['ticker']}: {h['quantity']} shares @ avg ₹{h['avg_buy_price']} (current ₹{h.get('current_price', '?')})"
            for h in portfolio
        ])
        context_str = "\n\n".join([
            f"[{doc['source_type'].upper()}] ({doc.get('ticker','?')}): {doc['content']}"
            for doc in context_docs[:15]  # limit to 15 docs for token budget
        ])

        prompt = ANALYSIS_PROMPT.format(
            question=question,
            portfolio_str=portfolio_str,
            context_str=context_str,
        )

        yield f"data: {json.dumps({'type': 'thinking', 'content': 'Generating analysis...'})}\n\n"

        # Stream LLM response token by token
        full_response = ""
        async for token in stream_llm(prompt):
            full_response += token
            if "SIGNALS_JSON:" not in full_response:  # don't stream the JSON block
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

        # Extract and emit signal cards
        if "SIGNALS_JSON:" in full_response:
            try:
                json_part = full_response.split("SIGNALS_JSON:")[1].strip()
                signals = json.loads(json_part)
                for signal in signals:
                    yield f"data: {json.dumps({'type': 'signal_card', 'content': signal})}\n\n"
            except:
                pass

        # Emit sources
        for doc in context_docs[:5]:
            if doc.get('url'):
                yield f"data: {json.dumps({'type': 'source', 'url': doc['url'], 'title': doc['content'][:60]})}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "Connection": "keep-alive"})
```

---

### H6–H8: Frontend chat UI

**ChatWindow.tsx — SSE streaming:**

```tsx
// components/ChatWindow.tsx
'use client';
import { useState, useRef } from 'react';

export function ChatWindow({ portfolio }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;
    const userMessage = input;
    setInput('');
    setIsLoading(true);

    // Add user message
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    // Add empty assistant message that we'll fill
    setMessages(prev => [...prev, { role: 'assistant', content: '', sources: [], signals: [], thinking: '' }]);

    const response = await fetch('http://localhost:8003/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: userMessage, portfolio }),
    });

    const reader = response.body!.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const lines = decoder.decode(value).split('\n').filter(l => l.startsWith('data: '));
      for (const line of lines) {
        const event = JSON.parse(line.replace('data: ', ''));

        setMessages(prev => {
          const updated = [...prev];
          const last = { ...updated[updated.length - 1] };

          if (event.type === 'thinking') last.thinking = event.content;
          if (event.type === 'token') last.content += event.content;
          if (event.type === 'signal_card') last.signals = [...(last.signals || []), event.content];
          if (event.type === 'source') last.sources = [...(last.sources || []), { url: event.url, title: event.title }];
          if (event.type === 'done') { last.thinking = ''; setIsLoading(false); }

          updated[updated.length - 1] = last;
          return updated;
        });
      }
    }
  };

  return (
    <div className="flex flex-col h-screen max-w-3xl mx-auto p-4">
      <div className="flex-1 overflow-y-auto space-y-4 mb-4">
        {messages.map((msg, i) => <MessageBubble key={i} message={msg} />)}
      </div>
      <div className="flex gap-2">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && sendMessage()}
          placeholder="Ask about your portfolio..."
          className="flex-1 border border-gray-300 rounded-xl px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={isLoading}
        />
        <button onClick={sendMessage} disabled={isLoading}
          className="bg-blue-600 text-white px-5 py-2 rounded-xl hover:bg-blue-700 disabled:opacity-50">
          Send
        </button>
      </div>
    </div>
  );
}
```

---

### H8–H9: Suggested questions + polish

**SuggestedQuestions component — shows based on portfolio:**

```tsx
// components/SuggestedQuestions.tsx
const QUESTION_TEMPLATES = [
  "Which of my holdings are at risk this quarter based on recent earnings?",
  "Which stock in my portfolio has the strongest buy signal right now?",
  "How is my portfolio positioned vs the Nifty 50?",
  "Which of my holdings should I consider trimming based on valuation?",
  "Are there any upcoming events (results, dividends) for my holdings?",
];

export function SuggestedQuestions({ onSelect }) {
  return (
    <div className="grid grid-cols-1 gap-2 my-4">
      {QUESTION_TEMPLATES.map((q, i) => (
        <button key={i} onClick={() => onSelect(q)}
          className="text-left text-sm text-blue-600 bg-blue-50 hover:bg-blue-100
                     border border-blue-200 rounded-xl px-4 py-2 transition-colors">
          {q}
        </button>
      ))}
    </div>
  );
}
```

---

### H9–H12: Demo prep

**Demo scenario (practice this exactly):**
1. Show portfolio upload — drag `data/sample_portfolio.csv` (5 stocks)
2. Holdings table loads with current prices and P&L
3. Click suggested question: "Which of my holdings are at risk this quarter?"
4. Live thinking indicator: "Planning analysis... Fetching data for 5 queries..."
5. Answer streams in live — tokens appearing
6. 2 signal cards appear inline: INFY (Bearish) and RELIANCE (Bullish)
7. Source chips at bottom: click one to show it links to actual NSE/ET article
8. Ask follow-up: "Why is RELIANCE bullish?" — show it uses conversation history

**Key talking point:** *"The existing ET Market ChatGPT tells you about a stock. This one tells you about YOUR stocks — your specific holdings, your buy price, your P&L. That's the difference between a generic analyst and a personal advisor."*

---

## API endpoints summary

```
GET  /health                        → health check
POST /portfolio/parse               → CSV upload → holdings JSON
POST /chat                          → SSE streaming agent response
```

## Sample portfolio CSV (for demo)

```csv
ticker,quantity,avg_buy_price
RELIANCE.NS,50,2400.00
INFY.NS,100,1450.00
HDFCBANK.NS,30,1600.00
TCS.NS,20,3500.00
WIPRO.NS,75,420.00
```