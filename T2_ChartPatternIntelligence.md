# T2 — Chart Pattern Intelligence

> **Your product:** Real-time technical pattern detection (breakouts, reversals,
> support/resistance, divergences) across the full NSE universe — with plain-English
> explanation and historical back-tested success rates for that pattern on that specific stock.
>
> **You own:** Everything in `/chart-pattern-intel/`
> **Your port:** `backend=8002`, `frontend=3002`
> **Dependency on teammates:** Only `shared/` utilities — you are fully independent.

---

## What you are building

A tool where a user enters any NSE stock ticker. The system:
1. Fetches the last 6 months of OHLCV (price/volume) data
2. Runs a pattern detection engine over the data — finds active technical patterns
3. For each pattern found, shows: what the pattern is, what it historically predicts,
   the back-tested success rate **for that specific stock** (not just the pattern in general),
   the entry/stop-loss/target levels, and a plain-English explanation for a retail investor

The output is a **pattern report card** per stock — visual chart with pattern marked,
explanation in simple English, and a historical track record.

This is powerful because most retail investors either can't read charts OR rely on generic
"head and shoulders is bearish" advice. This tool says: *"On RELIANCE specifically,
this pattern has worked 73% of the time in the last 5 years, with an average gain of 11.4%."*

---

## Folder structure

```
chart-pattern-intel/
├── README.md                          ← YOU ARE HERE
│
├── backend/
│   ├── main.py                        ← FastAPI app entrypoint (port 8002)
│   ├── requirements.txt
│   │
│   ├── routes/
│   │   ├── patterns.py                ← GET /patterns/{ticker} — main endpoint
│   │   ├── backtest.py                ← GET /backtest/{ticker}/{pattern}
│   │   └── chart.py                   ← GET /chart/{ticker} — OHLCV data for frontend chart
│   │
│   ├── detectors/
│   │   ├── orchestrator.py            ← Runs all detectors, merges results
│   │   ├── support_resistance.py      ← Detects S/R levels using pivot points
│   │   ├── breakout_detector.py       ← Detects breakouts above resistance with volume
│   │   ├── reversal_detector.py       ← Head & shoulders, double top/bottom, etc.
│   │   ├── momentum_detector.py       ← RSI divergence, MACD crossover, golden cross
│   │   └── candlestick_detector.py    ← Doji, engulfing, hammer, shooting star
│   │
│   ├── backtester/
│   │   ├── engine.py                  ← Runs historical pattern → outcome analysis
│   │   └── stats.py                   ← Computes win rate, avg gain, avg loss, RR ratio
│   │
│   ├── services/
│   │   ├── data_fetcher.py            ← yfinance OHLCV fetcher (6mo + 5yr for backtest)
│   │   └── llm_explainer.py           ← LLM generates plain-English pattern explanation
│   │
│   └── models/
│       ├── pattern.py                 ← Pydantic: Pattern, PatternType, BacktestResult
│       └── chart_data.py              ← Pydantic: OHLCV, ChartResponse
│
└── frontend/
    ├── package.json
    ├── next.config.js
    ├── tailwind.config.js
    └── app/
        ├── layout.tsx
        ├── page.tsx                   ← Ticker search input + pattern report
        └── globals.css
    └── components/
        ├── TickerSearch.tsx            ← Autocomplete search for NSE tickers
        ├── CandlestickChart.tsx        ← TradingView-style chart using lightweight-charts
        ├── PatternOverlay.tsx          ← Draws pattern markings on the chart
        ├── PatternCard.tsx             ← One pattern: name, description, stats, entry/SL/TP
        ├── BacktestStats.tsx           ← Win rate bar, avg gain/loss, sample count
        ├── ExplanationPanel.tsx        ← LLM-generated plain-English explanation
        └── LevelMarkers.tsx            ← S/R levels displayed on chart
    └── lib/
        ├── api.ts
        ├── types.ts
        └── mockData.ts                ← Mock pattern data for UI dev
```

---

## Hour-by-hour plan

### H0–H1: Setup + data layer

**Goal:** FastAPI running, yfinance returning clean OHLCV data as pandas DataFrame.

```bash
cd chart-pattern-intel/backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8002
```

**H0–H0:45: Data fetcher (`services/data_fetcher.py`)**

```python
# services/data_fetcher.py
import yfinance as yf
import pandas as pd
import time

def get_ohlcv(ticker: str, period: str = "6mo") -> pd.DataFrame:
    """
    Fetches OHLCV data for pattern detection.
    period: "6mo" for pattern detection, "5y" for backtesting
    Returns DataFrame with columns: Date, Open, High, Low, Close, Volume
    Ticker must end in .NS (e.g. RELIANCE.NS)
    """
    if not ticker.endswith(".NS"):
        ticker = ticker + ".NS"

    time.sleep(0.3)  # rate limit protection
    stock = yf.Ticker(ticker)
    df = stock.history(period=period)

    if df.empty:
        raise ValueError(f"No data found for {ticker}. Check ticker symbol.")

    df = df.reset_index()
    df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
    df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
    df.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
    return df

def get_ohlcv_with_indicators(ticker: str) -> pd.DataFrame:
    """
    Adds technical indicators to OHLCV DataFrame:
    - RSI (14-period)
    - MACD (12, 26, 9)
    - SMA 20, 50, 200
    - Bollinger Bands
    - Volume SMA 20
    """
    df = get_ohlcv(ticker, period="6mo")

    # RSI
    delta = df['close'].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    df['rsi'] = 100 - (100 / (1 + gain / loss))

    # MACD
    ema12 = df['close'].ewm(span=12).mean()
    ema26 = df['close'].ewm(span=26).mean()
    df['macd'] = ema12 - ema26
    df['macd_signal'] = df['macd'].ewm(span=9).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']

    # SMAs
    df['sma20'] = df['close'].rolling(20).mean()
    df['sma50'] = df['close'].rolling(50).mean()
    df['sma200'] = df['close'].rolling(200).mean()

    # Bollinger Bands
    df['bb_mid'] = df['close'].rolling(20).mean()
    bb_std = df['close'].rolling(20).std()
    df['bb_upper'] = df['bb_mid'] + 2 * bb_std
    df['bb_lower'] = df['bb_mid'] - 2 * bb_std

    # Volume SMA
    df['volume_sma20'] = df['volume'].rolling(20).mean()

    return df.dropna()
```

---

### H1–H3: Pattern detectors

**Goal:** 3 detectors working and returning Pattern objects.

**Support/Resistance detector (`detectors/support_resistance.py`)**

```python
# detectors/support_resistance.py
import pandas as pd
from models.pattern import SupportResistanceLevel

def detect(df: pd.DataFrame) -> list[SupportResistanceLevel]:
    """
    Finds S/R levels using pivot point method.
    A level is valid if price touched it at least 2 times in the last 6 months.
    Returns list of levels sorted by strength (number of touches).
    """
    levels = []
    sensitivity = 0.02  # 2% price range = same level

    for i in range(2, len(df) - 2):
        row = df.iloc[i]
        prev2, prev1 = df.iloc[i-2]['low'], df.iloc[i-1]['low']
        next1, next2 = df.iloc[i+1]['low'], df.iloc[i+2]['low']

        # Local low = support
        if row['low'] < prev1 and row['low'] < prev2 and row['low'] < next1 and row['low'] < next2:
            level_price = row['low']
            # Check if this level is unique (not within 2% of existing level)
            is_unique = all(abs(level_price - l.price) / l.price > sensitivity for l in levels)
            if is_unique:
                # Count touches
                touches = ((df['low'] - level_price).abs() / level_price < sensitivity).sum()
                levels.append(SupportResistanceLevel(
                    level_type="support",
                    price=round(level_price, 2),
                    touches=int(touches),
                    strength="strong" if touches >= 3 else "moderate" if touches == 2 else "weak",
                    date_first_seen=row['date'],
                ))

        # Local high = resistance
        prev2h, prev1h = df.iloc[i-2]['high'], df.iloc[i-1]['high']
        next1h, next2h = df.iloc[i+1]['high'], df.iloc[i+2]['high']
        if row['high'] > prev1h and row['high'] > prev2h and row['high'] > next1h and row['high'] > next2h:
            level_price = row['high']
            is_unique = all(abs(level_price - l.price) / l.price > sensitivity for l in levels)
            if is_unique:
                touches = ((df['high'] - level_price).abs() / level_price < sensitivity).sum()
                levels.append(SupportResistanceLevel(
                    level_type="resistance",
                    price=round(level_price, 2),
                    touches=int(touches),
                    strength="strong" if touches >= 3 else "moderate" if touches == 2 else "weak",
                    date_first_seen=row['date'],
                ))

    return sorted(levels, key=lambda l: l.touches, reverse=True)[:10]
```

**Breakout detector (`detectors/breakout_detector.py`)**

```python
# detectors/breakout_detector.py
import pandas as pd
from models.pattern import Pattern, PatternType

def detect(df: pd.DataFrame, resistance_levels: list) -> list[Pattern]:
    """
    A valid breakout requires:
    1. Price closes ABOVE resistance level
    2. Volume on breakout day > 1.5x 20-day average volume
    3. Breakout happened in the last 5 trading days (recent = actionable)
    """
    patterns = []
    current_price = df.iloc[-1]['close']
    recent_df = df.tail(5)

    for level in resistance_levels:
        if level.level_type != "resistance":
            continue

        # Check if recent close broke above resistance
        for _, row in recent_df.iterrows():
            if row['close'] > level.price * 1.005:  # 0.5% above = confirmed break
                volume_ratio = row['volume'] / df['volume_sma20'].iloc[-1] if 'volume_sma20' in df.columns else 1.0
                if volume_ratio >= 1.5:  # Volume confirmation
                    patterns.append(Pattern(
                        pattern_type=PatternType.BREAKOUT,
                        name="Volume Breakout",
                        detected_on=row['date'],
                        current_price=current_price,
                        entry_price=round(level.price * 1.01, 2),  # 1% above breakout
                        stop_loss=round(level.price * 0.98, 2),     # 2% below breakout
                        target_price=round(current_price * 1.08, 2),# 8% target
                        confidence=min(0.95, 0.6 + (volume_ratio - 1.5) * 0.1),
                        description=f"Price broke above ₹{level.price} resistance with {volume_ratio:.1f}x normal volume",
                        plain_english=f"{df.attrs.get('ticker','Stock')} broke out above a key resistance level of ₹{level.price} with unusually high trading volume — a strong signal that buyers are in control.",
                        key_levels={"resistance_broken": level.price, "volume_ratio": round(volume_ratio, 2)},
                    ))

    return patterns
```

---

### H3–H5: Backtester

**Goal:** For each pattern found, calculate its historical win rate on THAT specific stock.

```python
# backtester/engine.py
import pandas as pd
from models.pattern import BacktestResult

def backtest_pattern(
    ticker: str,
    pattern_type: str,
    df_5yr: pd.DataFrame,
    holding_period_days: int = 15
) -> BacktestResult:
    """
    For a given pattern type on a specific ticker:
    1. Find all historical occurrences of this pattern (last 5 years)
    2. For each occurrence, record what happened in the next N days
    3. Calculate: win rate, avg gain when won, avg loss when lost, RR ratio

    Returns BacktestResult with stats.
    """
    occurrences = find_historical_occurrences(df_5yr, pattern_type)

    if len(occurrences) < 3:
        return BacktestResult(
            pattern_type=pattern_type,
            ticker=ticker,
            sample_count=len(occurrences),
            win_rate=None,
            avg_gain_pct=None,
            avg_loss_pct=None,
            rr_ratio=None,
            note="Insufficient historical data — fewer than 3 occurrences found"
        )

    outcomes = []
    for idx in occurrences:
        if idx + holding_period_days >= len(df_5yr):
            continue
        entry_price = df_5yr.iloc[idx]['close']
        exit_price = df_5yr.iloc[idx + holding_period_days]['close']
        pct_change = (exit_price - entry_price) / entry_price * 100
        outcomes.append(pct_change)

    wins = [o for o in outcomes if o > 0]
    losses = [o for o in outcomes if o <= 0]
    win_rate = len(wins) / len(outcomes) if outcomes else 0

    return BacktestResult(
        pattern_type=pattern_type,
        ticker=ticker,
        sample_count=len(outcomes),
        win_rate=round(win_rate, 3),
        avg_gain_pct=round(sum(wins) / len(wins), 2) if wins else 0,
        avg_loss_pct=round(sum(losses) / len(losses), 2) if losses else 0,
        rr_ratio=round(abs(sum(wins)/len(wins)) / abs(sum(losses)/len(losses)), 2) if losses and wins else None,
        note=f"Based on {len(outcomes)} historical occurrences over 5 years"
    )
```

---

### H5–H7: LLM explainer + API routes + frontend chart

**LLM explainer (`services/llm_explainer.py`)**

```python
# services/llm_explainer.py
import sys
sys.path.append("../../shared")
from llm_client import call_llm
import json

EXPLAIN_PROMPT = """
You are explaining a stock chart pattern to a retail investor in India who is NOT a technical analyst.
They understand basic concepts like "price going up" and "resistance" but not jargon.

Stock: {ticker}
Pattern detected: {pattern_name}
Current price: ₹{current_price}
Entry suggested: ₹{entry_price}
Stop loss: ₹{stop_loss}
Target: ₹{target_price}
Historical win rate on this stock: {win_rate}% ({sample_count} times tested)
Key detail: {pattern_description}

Write a plain-English explanation in 3 short paragraphs:
1. What this pattern means in simple terms (no jargon)
2. What history says about this pattern on THIS specific stock
3. What the investor should watch for (what would invalidate this signal)

Keep each paragraph under 60 words. Use ₹ for Indian Rupees. Be honest about uncertainty.
"""

def explain_pattern(ticker, pattern_name, current_price, entry_price,
                    stop_loss, target_price, win_rate, sample_count, description) -> str:
    prompt = EXPLAIN_PROMPT.format(**locals())
    return call_llm(prompt)
```

**Frontend chart (`components/CandlestickChart.tsx`):**

```tsx
// Install: npm install lightweight-charts
// components/CandlestickChart.tsx
'use client';
import { useEffect, useRef } from 'react';
import { createChart, CrosshairMode } from 'lightweight-charts';

export function CandlestickChart({ ohlcv, patterns, levels }) {
  const chartRef = useRef(null);

  useEffect(() => {
    if (!chartRef.current) return;
    const chart = createChart(chartRef.current, {
      width: chartRef.current.clientWidth,
      height: 400,
      crosshair: { mode: CrosshairMode.Normal },
      layout: { background: { color: '#ffffff' }, textColor: '#333' },
      grid: { vertLines: { color: '#f0f0f0' }, horzLines: { color: '#f0f0f0' } },
    });

    const candleSeries = chart.addCandlestickSeries({
      upColor: '#26a69a', downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a', wickDownColor: '#ef5350',
    });

    candleSeries.setData(ohlcv.map(d => ({
      time: d.date, open: d.open, high: d.high, low: d.low, close: d.close,
    })));

    // Draw S/R levels as horizontal lines
    levels.forEach(level => {
      const lineSeries = chart.addLineSeries({
        color: level.level_type === 'support' ? '#26a69a' : '#ef5350',
        lineWidth: 1,
        lineStyle: 2, // dashed
      });
      lineSeries.setData(ohlcv.map(d => ({ time: d.date, value: level.price })));
    });

    return () => chart.remove();
  }, [ohlcv, levels]);

  return <div ref={chartRef} className="w-full rounded-xl border border-gray-200" />;
}
```

---

### H7–H9: Polish

- [ ] BacktestStats component: horizontal bar showing win rate (green = wins, red = losses)
- [ ] Filter: show only High confidence patterns (confidence > 0.7)
- [ ] If no patterns found: show "No strong patterns detected — market is range-bound"
- [ ] Pattern card: Entry / SL / Target shown as price levels with % distance from current

---

### H9–H12: Demo prep

**Demo scenario (practice this exactly):**
1. Enter "RELIANCE" in the search box
2. Show chart loads with S/R levels marked
3. Show 2 patterns detected (e.g. Breakout + RSI Divergence)
4. Click first pattern — show BacktestStats: "This pattern worked 71% of the time on RELIANCE (17 historical occurrences)"
5. Show LLM plain-English explanation below
6. Show Entry / Stop Loss / Target levels highlighted on chart

**Key talking point:** *"Generic pattern tools say 'head and shoulders is bearish 65% of the time.' We say 'on RELIANCE specifically, this pattern worked 71% of the time with an average gain of 9.3%.' That's the difference."*

---

## Pydantic models reference

```python
# models/pattern.py
from pydantic import BaseModel
from enum import Enum

class PatternType(str, Enum):
    BREAKOUT = "breakout"
    SUPPORT_BOUNCE = "support_bounce"
    RSI_DIVERGENCE = "rsi_divergence"
    MACD_CROSSOVER = "macd_crossover"
    GOLDEN_CROSS = "golden_cross"
    DOUBLE_BOTTOM = "double_bottom"
    HEAD_SHOULDERS = "head_shoulders"
    HAMMER = "hammer"
    ENGULFING = "engulfing"

class Pattern(BaseModel):
    pattern_type: PatternType
    name: str
    detected_on: str
    current_price: float
    entry_price: float
    stop_loss: float
    target_price: float
    confidence: float           # 0.0 to 1.0
    description: str            # technical description
    plain_english: str          # LLM-generated retail-friendly explanation
    key_levels: dict = {}

class BacktestResult(BaseModel):
    pattern_type: str
    ticker: str
    sample_count: int
    win_rate: float | None
    avg_gain_pct: float | None
    avg_loss_pct: float | None
    rr_ratio: float | None
    note: str

class SupportResistanceLevel(BaseModel):
    level_type: str             # "support" or "resistance"
    price: float
    touches: int
    strength: str               # "strong" | "moderate" | "weak"
    date_first_seen: str
```

---

## API endpoints summary

```
GET  /health                              → health check
GET  /patterns/{ticker}                   → all patterns + S/R levels for a ticker
GET  /backtest/{ticker}/{pattern_type}    → historical stats for a pattern on a ticker
GET  /chart/{ticker}?period=6mo          → raw OHLCV data for frontend chart
```