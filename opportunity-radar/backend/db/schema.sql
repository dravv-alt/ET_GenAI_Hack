-- db/schema.sql
-- ==============
-- SQLite schema for the Opportunity Radar backend.
--
-- TABLES:
--   1. alerts    — Cached alert objects from the last scan.
--                  Cleared and repopulated on each POST /scan.
--                  Indexed on ticker and signal_strength for fast filtering.
--
--   2. watchlist — The set of NSE tickers currently being monitored.
--                  Managed via GET/POST /watchlist endpoints.
--                  Simple key-value: ticker (PK) + added_at timestamp.
--
-- USAGE:
--   This file is read and executed by db/db.py:init_schema() on app startup.
--   SQLite creates the file at db/radar.db automatically.
--
-- NOTES:
--   - raw_data stored as TEXT (JSON string) — parsed in Python when reading.
--   - created_at stored as TEXT in ISO 8601 format ("2026-03-29T10:30:00").
--   - signal_strength stored as TEXT: 'high' | 'medium' | 'low'.
--   - alert_type stored as TEXT: see AlertType enum in models/alert.py.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS alerts (
    id              TEXT PRIMARY KEY,           -- UUID string e.g. "550e8400-e29b..."
    ticker          TEXT NOT NULL,              -- NSE symbol e.g. "RELIANCE"
    alert_type      TEXT NOT NULL,              -- "insider_buy" | "bulk_deal" | etc.
    signal_strength TEXT NOT NULL,              -- "high" | "medium" | "low"
    title           TEXT NOT NULL,              -- Short headline ~80 chars
    why_it_matters  TEXT NOT NULL,              -- Investment implication sentence
    action_hint     TEXT NOT NULL,              -- Suggested investor action
    source_url      TEXT NOT NULL,              -- Link to original data source
    source_label    TEXT NOT NULL,              -- Human-readable source name
    raw_data        TEXT NOT NULL DEFAULT '{}', -- JSON string of original scanner data
    created_at      TEXT NOT NULL               -- ISO 8601 datetime string
);

-- Index for fast filtering by ticker (GET /alerts/{ticker})
CREATE INDEX IF NOT EXISTS idx_alerts_ticker
    ON alerts (ticker);

-- Index for fast filtering + sorting by signal strength
-- (GET /alerts?signal=high uses this)
CREATE INDEX IF NOT EXISTS idx_alerts_signal_strength
    ON alerts (signal_strength, created_at DESC);


CREATE TABLE IF NOT EXISTS watchlist (
    ticker      TEXT PRIMARY KEY,   -- NSE symbol e.g. "RELIANCE" (no .NS suffix)
    added_at    TEXT NOT NULL       -- ISO 8601 datetime when added
);
