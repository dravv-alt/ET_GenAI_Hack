# System Overview (AI Agent Guide)

This repo contains four independent products that will be demoed together. Each teammate owns one product folder, but all products share the same stack conventions and shared utilities. This document gives a quick map so any AI agent can connect the pieces at the end.

## Products and ownership

- T1: Opportunity Radar -> opportunity-radar
- T2: Chart Pattern Intelligence -> chart-pattern-intel
- T3: Market ChatGPT -> market-chatgpt
- T4: AI Market Video Engine -> market-video-engine

## Shared constraints (hackathon)

- Backend: Python (FastAPI) only
- Frontend: React (JSX) with Vite
- Local storage: SQLite (no external DB)
- Shared utilities: shared/ (LLM, NSE, market data, news search)

## Ports (run in parallel)

- T1 backend: 8001, frontend: 3001
- T2 backend: 8002, frontend: 3002
- T3 backend: 8003, frontend: 3003
- T4 backend: 8004, frontend: 3004

## Shared env config

- shared/.env (copy from shared/.env.example)
- Keys used by all products: ANTHROPIC_API_KEY, OPENAI_API_KEY, LLM_MODEL, TAVILY_API_KEY

## Integration contract (minimal)

Each product is independent. Integration for the final demo is a simple runbook:

1. Start all four backends (uvicorn main:app --reload --port <port>)
2. Start all four frontends (npm run dev -- --port <port>)
3. Demo products sequentially in the browser

No runtime coupling is required, but teams should follow these cross-cutting conventions:

- CORS enabled in all backends (allow localhost:3001-3004)
- Consistent data shapes in API responses (per docs/API_CONTRACTS.md)
- Shared LLM and data helpers live in shared/

## Data flow map

- T1 Opportunity Radar
  - Input: NSE watchlist and filings
  - Output: ranked alerts with source links

- T2 Chart Pattern Intelligence
  - Input: ticker -> OHLCV
  - Output: detected patterns + backtest stats

- T3 Market ChatGPT
  - Input: portfolio CSV + question
  - Output: streaming answer with sources

- T4 AI Market Video Engine
  - Input: video type
  - Output: generated MP4 and narration script

## Demo flow (connects all four)

1. Open Opportunity Radar (3001) -> run scan -> show 3 alerts
2. Open Chart Pattern Intelligence (3002) -> run ticker -> show patterns
3. Open Market ChatGPT (3003) -> upload portfolio -> ask question -> streaming answer
4. Open Market Video Engine (3004) -> generate market wrap -> play video

## Team coordination rules

- Only edit files inside your product folder unless touching shared/
- If a shared utility changes, announce in team chat
- Keep endpoints consistent with docs/API_CONTRACTS.md
- Avoid changing port defaults

## Quick checklist for AI agents

- Confirm ports match above
- Confirm .env exists in shared/
- Use shared/ utilities instead of copying logic
- Keep FastAPI routers minimal and fast (no heavy queues)
- Use SQLite only for caching and demo state
