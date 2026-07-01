# System Architecture

The repository is structured as a monolithic repository containing 4 independent, highly decoupled AI products. 

Each product operates as a standalone microservice with its own dedicated React frontend and FastAPI backend, communicating only with external services or the `shared` utilities module.

## High-Level Architecture Diagram

```mermaid
graph TD
    subgraph "External Providers"
        LLM["LLMs (Claude / Groq)"]
        YF["yfinance (Market Data)"]
        NSE["NSE Public APIs"]
        NEWS["Tavily (News API)"]
    end

    subgraph "Shared Utilities (/shared)"
        SC["llm_client.py"]
        SM["market_data.py"]
        SN["nse_fetcher.py"]
        SW["news_search.py"]
    end

    subgraph "Product 1: Opportunity Radar"
        F1["Frontend (Port 3001)"]
        B1["Backend (Port 8001)"]
        DB1[("SQLite DB")]
        F1 <-->|REST| B1
        B1 --- DB1
    end

    subgraph "Product 2: Chart Pattern Intel"
        F2["Frontend (Port 3002)"]
        B2["Backend (Port 8002)"]
        DB2[("SQLite DB")]
        F2 <-->|REST| B2
        B2 --- DB2
    end

    subgraph "Product 3: Market ChatGPT"
        F3["Frontend (Port 3003)"]
        B3["Backend (Port 8003)"]
        DB3[("SQLite DB")]
        F3 <-->|REST| B3
        B3 --- DB3
    end

    subgraph "Product 4: Market Video Engine"
        F4["Frontend (Port 3004)"]
        B4["Backend (Port 8004)"]
        DB4[("SQLite DB")]
        F4 <-->|REST| B4
        B4 --- DB4
    end

    %% Backend Dependencies
    B1 --> SC & SM & SN & SW
    B2 --> SC & SM
    B3 --> SC & SM & SW
    B4 --> SC & SM & SN

    %% Shared Utilities to External
    SC --> LLM
    SM --> YF
    SN --> NSE
    SW --> NEWS
```

## Shared Module (`/shared`)
To prevent code duplication, the 4 products rely on a common utilities package:
- **`llm_client.py`**: A unified wrapper to interact with Claude 3.5 Sonnet and Groq. Handles fallbacks and JSON parsing.
- **`market_data.py`**: Interacts with the `yfinance` library to pull historical OHLCV data.
- **`nse_fetcher.py`**: A specialized client to fetch live data directly from NSE India APIs (e.g. bulk deals, indices).
- **`news_search.py`**: Wraps the Tavily API for semantic news retrieval.

## Design Principles
1. **Decoupled Deployments**: If one teammate's product crashes, the other 3 continue to function flawlessly. They do not share databases or memory states.
2. **Local Priority**: All products use SQLite for fast, localized state management (paper trading ledgers, video history, alert stores) to ensure zero setup friction.
3. **Stateless Operations**: AI inferences and market analyses are stateless and rely entirely on live or cached pulls from `shared`.
