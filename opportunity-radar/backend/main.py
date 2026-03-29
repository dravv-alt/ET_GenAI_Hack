"""
main.py
=======
Opportunity Radar — FastAPI application entrypoint. Runs on PORT 8001.

HOW TO RUN:
    cd opportunity-radar/backend
    uvicorn main:app --reload --port 8001

WHAT THIS FILE DOES:
    1. Creates the FastAPI application instance with metadata.
    2. Adds CORSMiddleware so the React frontend (localhost:3001) can call the API.
    3. Includes all three routers (alerts, scan, watchlist) at the root prefix.
    4. Registers a startup event handler that initializes the SQLite schema.
    5. Defines GET /health for quick health checks and monitoring.

CORS POLICY:
    Set to allow all origins ("*") for the hackathon. In production, restrict
    to specific origins (e.g., ["https://etmarkets.com", "http://localhost:3001"]).

STARTUP EVENTS:
    On startup:
        - db.init_schema() creates SQLite tables if they don't exist.
          Safe to call multiple times — uses IF NOT EXISTS in schema.sql.

ROUTERS:
    routes/alerts.py   → GET /alerts, GET /alerts/{ticker}
    routes/scan.py     → POST /scan
    routes/watchlist.py→ GET /watchlist, POST /watchlist

SWAGGER UI:
    FastAPI auto-generates API docs at: http://localhost:8001/docs
    ReDoc (alternative) at:            http://localhost:8001/redoc
    Use these to test endpoints without curl during development.

DEPENDENCIES (all in requirements.txt):
    fastapi, uvicorn, requests, yfinance, pandas,
    google-generativeai, groq, python-dotenv
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db.db import init_schema
from routes.alerts import router as alerts_router
from routes.scan import router as scan_router
from routes.watchlist import router as watchlist_router

# ── FastAPI app instance ───────────────────────────────────────────────────────
app = FastAPI(
    title="Opportunity Radar API",
    description=(
        "AI-powered NSE signal detector. Surfaces non-obvious opportunities "
        "from corporate filings, bulk deals, insider trades, and sentiment shifts."
    ),
    version="1.0.0",
    docs_url="/docs",     # Swagger UI
    redoc_url="/redoc",   # ReDoc
)

# ── CORS Middleware ────────────────────────────────────────────────────────────
# Required for browser-based React frontend to call this API.
# In development, we allow all origins. Restrict in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Allow all — change to ["http://localhost:3001"] in prod
    allow_credentials=True,
    allow_methods=["*"],           # Allow GET, POST, OPTIONS, etc.
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────────
# All mounted at root (no prefix) since each router defines its own paths.
app.include_router(alerts_router)    # GET /alerts, GET /alerts/{ticker}
app.include_router(scan_router)      # POST /scan
app.include_router(watchlist_router) # GET /watchlist, POST /watchlist


# ── Startup event ─────────────────────────────────────────────────────────────
@app.on_event("startup")
def on_startup():
    """
    Called once when the server starts.
    Initializes the SQLite database schema (creates tables if not exist).
    """
    print("[main] Starting Opportunity Radar API on port 8001...")
    init_schema()
    print("[main] Database initialized. Ready to serve requests.")


# ── Health check ───────────────────────────────────────────────────────────────
@app.get("/health", tags=["health"])
async def health_check():
    """
    Simple health check endpoint.

    Used to verify the server is running before starting a demo.

    Returns:
        {"status": "ok", "service": "opportunity-radar", "port": 8001}

    Test with:
        curl http://localhost:8001/health
    """
    return {
        "status": "ok",
        "service": "opportunity-radar",
        "port": 8001,
        "version": "1.0.0",
    }
