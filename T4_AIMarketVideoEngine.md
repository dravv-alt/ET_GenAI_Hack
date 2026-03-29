# T4 — AI Market Video Engine

> **Your product:** Auto-generate short, visually rich market update videos (30–90 seconds)
> from real-time data. Race-chart simulators, daily market wraps, sector rotations,
> FII/DII flow visualizations, IPO trackers — zero human editing required.
>
> **You own:** Everything in `/market-video-engine/`
> **Your port:** `backend=8004`, `frontend=3004`
> **Dependency on teammates:** Only `shared/` utilities — you are fully independent.

---

## What you are building

A tool that generates short market update videos automatically from live NSE data.

User selects a video type from a menu:
- **Daily Market Wrap** — 60-second recap: Nifty movement, top gainers/losers, FII/DII data
- **Sector Rotation Video** — which sectors are hot and cold today with animated bars
- **Race Chart** — animated bar chart race showing Nifty 50 returns over 1 year
- **IPO Tracker** — status and GMP of current IPOs with animations

The system:
1. Fetches live/latest market data
2. Generates frames using matplotlib / Plotly
3. Uses LLM to generate a voiceover script
4. Assembles frames + AI narration audio into an MP4 using MoviePy
5. Returns the video as a downloadable file

**This is a visual wow — judges will remember a moving animated video.**

---

## Folder structure

```
market-video-engine/
├── README.md                          ← YOU ARE HERE
│
├── backend/
│   ├── main.py                        ← FastAPI app (port 8004)
│   ├── requirements.txt
│   ├── db/                            ← SQLite helpers + schema
│   ├── data/                          ← small JSON fallbacks for dev
│   │
│   ├── routes/
│   │   └── video.py                   ← POST /generate — main video generation endpoint
│   │
│   ├── generators/
│   │   ├── orchestrator.py            ← Picks generator based on video_type, assembles MP4
│   │   ├── market_wrap.py             ← Daily market wrap video generator
│   │   ├── sector_rotation.py         ← Sector rotation animated bar chart
│   │   ├── race_chart.py              ← Animated bar chart race (Nifty 50 returns)
│   │   └── ipo_tracker.py             ← IPO status + GMP tracker video
│   │
│   ├── rendering/
│   │   ├── frame_builder.py           ← Builds individual frames using matplotlib
│   │   ├── text_overlay.py            ← Adds text, tickers, prices onto frames
│   │   ├── color_themes.py            ← ET branding colors, green/red palettes
│   │   └── video_assembler.py         ← MoviePy: frames → MP4 with audio
│   │
│   ├── services/
│   │   ├── market_data.py             ← yfinance: Nifty data, sector ETFs, top movers
│   │   ├── script_generator.py        ← LLM generates voiceover narration script
│   │   └── tts_client.py              ← Text-to-speech (gTTS free, or ElevenLabs)
│   │
│   └── models/
│       └── video.py                   ← Pydantic: VideoRequest, VideoType, VideoStatus
│
└── frontend/
  ├── index.html
  ├── package.json
  ├── vite.config.js
  ├── tailwind.config.js
  ├── public/
  └── src/
    ├── main.jsx
    ├── App.jsx                    ← Main page: video type selector + preview
    ├── styles.css
    ├── components/
    │   ├── VideoTypeSelector.jsx   ← 4 cards: pick your video type
    │   ├── VideoPreview.jsx        ← Video player with download button
    │   ├── GenerationProgress.jsx  ← Step-by-step progress: data → frames → audio → mp4
    │   ├── MarketDataPreview.jsx   ← Shows what data will go into the video
    │   └── ScriptPreview.jsx      ← Shows the LLM-generated narration script
    └── lib/
      ├── api.js
      └── mockData.js
```

---

## Hour-by-hour plan

### H0–H1: Setup + data layer

**Goal:** FastAPI running, can fetch Nifty data and top movers.

```bash
cd market-video-engine/backend
python -m venv venv && source venv/bin/activate
pip install fastapi uvicorn yfinance pandas matplotlib pillow moviepy \
            gTTS anthropic openai python-dotenv requests
uvicorn main:app --reload --port 8004
```

**Market data service (`services/market_data.py`):**

```python
# services/market_data.py
import yfinance as yf
import pandas as pd
import time

def get_nifty_data(period: str = "1d") -> dict:
    """
    Fetches Nifty 50 index data for today.
    Returns: {open, close, high, low, change_pct, change_abs}
    """
    time.sleep(0.2)
    nifty = yf.Ticker("^NSEI")
    hist = nifty.history(period=period)
    if hist.empty:
        return {"open": 22000, "close": 22150, "high": 22200, "low": 21950,
                "change_pct": 0.68, "change_abs": 150}  # fallback mock

    latest = hist.iloc[-1]
    prev_close = hist.iloc[-2]['Close'] if len(hist) > 1 else latest['Open']
    change_abs = latest['Close'] - prev_close
    change_pct = (change_abs / prev_close) * 100

    return {
        "open": round(latest['Open'], 2),
        "close": round(latest['Close'], 2),
        "high": round(latest['High'], 2),
        "low": round(latest['Low'], 2),
        "change_pct": round(change_pct, 2),
        "change_abs": round(change_abs, 2),
    }

def get_top_movers(n: int = 5) -> dict:
    """
    Returns top N gainers and losers from Nifty 50.
    """
    nifty50_tickers = [
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
        "HINDUNILVR.NS", "ITC.NS", "KOTAKBANK.NS", "LT.NS", "BAJFINANCE.NS",
        "SBIN.NS", "WIPRO.NS", "AXISBANK.NS", "MARUTI.NS", "ULTRACEMCO.NS",
        "TITAN.NS", "ASIANPAINT.NS", "SUNPHARMA.NS", "TATAMOTORS.NS", "ONGC.NS",
    ]

    movers = []
    for ticker in nifty50_tickers[:15]:  # limit to 15 for speed
        try:
            time.sleep(0.1)
            stock = yf.Ticker(ticker)
            info = stock.fast_info
            change_pct = getattr(info, 'three_month_change', 0) or 0
            movers.append({
                "ticker": ticker.replace(".NS", ""),
                "change_pct": round(change_pct * 100, 2),
                "current_price": round(getattr(info, 'last_price', 0), 2),
            })
        except:
            continue

    sorted_movers = sorted(movers, key=lambda x: x['change_pct'], reverse=True)
    return {
        "gainers": sorted_movers[:n],
        "losers": sorted_movers[-n:][::-1],
    }

def get_sector_performance() -> list:
    """
    Returns performance of major Indian sector ETFs.
    Uses Nifty sector indices as proxies.
    """
    sectors = {
        "Bank": "^NSEBANK",
        "IT": "^CNXIT",
        "Auto": "^CNXAUTO",
        "Pharma": "^CNXPHARMA",
        "FMCG": "^CNXFMCG",
        "Metal": "^CNXMETAL",
        "Realty": "^CNXREALTY",
        "Energy": "^CNXENERGY",
    }

    results = []
    for sector_name, symbol in sectors.items():
        try:
            time.sleep(0.1)
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5d")
            if len(hist) >= 2:
                change = (hist.iloc[-1]['Close'] - hist.iloc[-2]['Close']) / hist.iloc[-2]['Close'] * 100
                results.append({"sector": sector_name, "change_pct": round(change, 2)})
        except:
            results.append({"sector": sector_name, "change_pct": 0.0})

    return sorted(results, key=lambda x: x['change_pct'], reverse=True)
```

---

### H1–H3: Frame builder + Daily Market Wrap generator

**This is the visual core of your product. Get this right first.**

**Frame builder (`rendering/frame_builder.py`):**

```python
# rendering/frame_builder.py
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io

# ET brand colors
ET_RED = "#E8002D"
ET_DARK = "#1A1A2E"
ET_GRAY = "#2D2D44"
ET_GREEN = "#00C853"
ET_WHITE = "#FFFFFF"
ET_YELLOW = "#FFD600"

def create_market_wrap_frame(
    frame_num: int,
    total_frames: int,
    nifty_data: dict,
    gainers: list,
    losers: list,
    title: str = "Daily Market Wrap"
) -> bytes:
    """
    Creates one frame of the daily market wrap video.
    Returns PNG bytes.
    frame_num controls animation progress (e.g. bar heights animate in).
    """
    fig, ax = plt.subplots(figsize=(16, 9), facecolor=ET_DARK)
    ax.set_facecolor(ET_DARK)
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9)
    ax.axis('off')

    progress = min(frame_num / max(total_frames * 0.6, 1), 1.0)  # animate bars in first 60% of frames

    # Title bar
    ax.add_patch(mpatches.Rectangle((0, 8.2), 16, 0.8, color=ET_RED, zorder=2))
    ax.text(0.3, 8.6, title, color=ET_WHITE, fontsize=22, fontweight='bold', va='center', zorder=3)
    ax.text(15.7, 8.6, "ET Markets", color=ET_WHITE, fontsize=14, va='center', ha='right', zorder=3)

    # Nifty 50 display
    nifty_color = ET_GREEN if nifty_data['change_pct'] >= 0 else ET_RED
    ax.add_patch(mpatches.Rectangle((0.3, 6.0), 4.5, 1.9, color=ET_GRAY, zorder=2, linewidth=2,
                                    edgecolor=nifty_color))
    ax.text(2.55, 7.5, "NIFTY 50", color=ET_WHITE, fontsize=16, fontweight='bold',
            va='center', ha='center', zorder=3)
    ax.text(2.55, 7.0, f"{nifty_data['close']:,.2f}", color=nifty_color, fontsize=24,
            fontweight='bold', va='center', ha='center', zorder=3)
    sign = "+" if nifty_data['change_pct'] >= 0 else ""
    ax.text(2.55, 6.4, f"{sign}{nifty_data['change_pct']:.2f}%  ({sign}{nifty_data['change_abs']:.0f})",
            color=nifty_color, fontsize=14, va='center', ha='center', zorder=3)

    # Top gainers bar chart (animated)
    ax.text(5.2, 7.7, "TOP GAINERS", color=ET_GREEN, fontsize=14, fontweight='bold')
    for i, g in enumerate(gainers[:5]):
        bar_width = g['change_pct'] / max(g['change_pct'] for g in gainers) * 3.5 * progress
        y = 7.2 - i * 0.55
        ax.add_patch(mpatches.Rectangle((5.2, y), bar_width, 0.4, color=ET_GREEN, alpha=0.85, zorder=2))
        ax.text(5.1, y + 0.2, g['ticker'], color=ET_WHITE, fontsize=10, va='center', ha='right', zorder=3)
        if progress > 0.3:
            ax.text(5.2 + bar_width + 0.1, y + 0.2, f"+{g['change_pct']:.1f}%",
                    color=ET_GREEN, fontsize=10, va='center', zorder=3)

    # Top losers bar chart (animated)
    ax.text(10.2, 7.7, "TOP LOSERS", color=ET_RED, fontsize=14, fontweight='bold')
    for i, l in enumerate(losers[:5]):
        bar_width = abs(l['change_pct']) / max(abs(l['change_pct']) for l in losers) * 3.5 * progress
        y = 7.2 - i * 0.55
        ax.add_patch(mpatches.Rectangle((10.2, y), bar_width, 0.4, color=ET_RED, alpha=0.85, zorder=2))
        ax.text(10.1, y + 0.2, l['ticker'], color=ET_WHITE, fontsize=10, va='center', ha='right', zorder=3)
        if progress > 0.3:
            ax.text(10.2 + bar_width + 0.1, y + 0.2, f"{l['change_pct']:.1f}%",
                    color=ET_RED, fontsize=10, va='center', zorder=3)

    # Footer
    ax.add_patch(mpatches.Rectangle((0, 0), 16, 0.4, color=ET_GRAY, zorder=2))
    ax.text(8, 0.2, "Data: NSE India | ET Markets AI  |  Not investment advice",
            color="#888888", fontsize=9, va='center', ha='center', zorder=3)

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=120, bbox_inches='tight', pad_inches=0)
    plt.close(fig)
    buf.seek(0)
    return buf.read()
```

---

### H3–H5: Video assembler + LLM script + TTS

**Video assembler (`rendering/video_assembler.py`):**

```python
# rendering/video_assembler.py
import os, tempfile
from moviepy.editor import ImageSequenceClip, AudioFileClip, CompositeAudioClip
from moviepy.audio.AudioClip import AudioArrayClip
import numpy as np

def assemble_video(frame_bytes_list: list, audio_path: str = None,
                   fps: int = 24, output_path: str = "output.mp4") -> str:
    """
    Takes a list of PNG frame bytes and assembles them into an MP4.
    Optionally adds a TTS audio track.
    Returns path to the output MP4.
    """
    # Write frames to temp files
    with tempfile.TemporaryDirectory() as tmpdir:
        frame_paths = []
        for i, frame_bytes in enumerate(frame_bytes_list):
            path = os.path.join(tmpdir, f"frame_{i:04d}.png")
            with open(path, 'wb') as f:
                f.write(frame_bytes)
            frame_paths.append(path)

        # Create video clip from frames
        clip = ImageSequenceClip(frame_paths, fps=fps)

        # Add audio if provided
        if audio_path and os.path.exists(audio_path):
            audio = AudioFileClip(audio_path)
            # Trim audio or video to match shorter one
            duration = min(clip.duration, audio.duration)
            clip = clip.subclip(0, duration)
            audio = audio.subclip(0, duration)
            clip = clip.set_audio(audio)

        clip.write_videofile(output_path, fps=fps, codec='libx264',
                             audio_codec='aac', verbose=False, logger=None)

    return output_path
```

**LLM script generator (`services/script_generator.py`):**

```python
# services/script_generator.py
import sys
sys.path.append("../../shared")
from llm_client import call_llm

SCRIPT_PROMPT = """
Write a 45-second market update video voiceover script for Indian retail investors.

Data for today:
- Nifty 50: {nifty_close} ({nifty_change:+.2f}%)
- Top gainers: {gainers_str}
- Top losers: {losers_str}
- Sector performance: {sectors_str}

Rules:
1. Start with Nifty opening line (energetic, newsy tone)
2. Cover top 2 gainers with ONE sentence each — mention why if data available
3. Cover top 2 losers with ONE sentence each
4. End with 1 sentence on what to watch tomorrow
5. Max 130 words total — this is spoken, not read
6. Use natural spoken Indian financial news style (think ET Now anchor)
7. No markdown, no bullets — just the script text
"""

def generate_market_wrap_script(nifty_data, gainers, losers, sectors) -> str:
    gainers_str = ", ".join([f"{g['ticker']} +{g['change_pct']}%" for g in gainers[:3]])
    losers_str = ", ".join([f"{l['ticker']} {l['change_pct']}%" for l in losers[:3]])
    sectors_str = ", ".join([f"{s['sector']} {s['change_pct']:+.1f}%" for s in sectors[:4]])

    prompt = SCRIPT_PROMPT.format(
        nifty_close=nifty_data['close'],
        nifty_change=nifty_data['change_pct'],
        gainers_str=gainers_str,
        losers_str=losers_str,
        sectors_str=sectors_str,
    )
    return call_llm(prompt)
```

**TTS client (`services/tts_client.py`):**

```python
# services/tts_client.py
# Using gTTS (Google Text-to-Speech) — free, no API key
from gtts import gTTS
import tempfile, os

def generate_audio(script: str, lang: str = "en", output_path: str = None) -> str:
    """
    Converts script text to MP3 audio file.
    Returns path to the audio file.
    Uses gTTS (Google TTS) — free, no API key required.
    For better quality: swap with ElevenLabs API (needs key).
    """
    if not output_path:
        tmpfile = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
        output_path = tmpfile.name
        tmpfile.close()

    tts = gTTS(text=script, lang=lang, slow=False)
    tts.save(output_path)
    return output_path
```

---

### H5–H7: Sector rotation + Race chart generators

**Sector rotation generator (`generators/sector_rotation.py`):**

```python
# generators/sector_rotation.py
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import io
from rendering.color_themes import ET_DARK, ET_WHITE, ET_GREEN, ET_RED, ET_GRAY

def generate_frames(sector_data: list, total_frames: int = 72) -> list[bytes]:
    """
    Generates frames for animated sector rotation horizontal bar chart.
    Bars animate in from left to right.
    Returns list of PNG bytes (24 fps × 3 seconds = 72 frames).
    """
    frames = []
    sorted_sectors = sorted(sector_data, key=lambda x: x['change_pct'], reverse=True)
    max_abs = max(abs(s['change_pct']) for s in sorted_sectors) or 1

    for frame_num in range(total_frames):
        progress = min(frame_num / (total_frames * 0.7), 1.0)

        fig, ax = plt.subplots(figsize=(16, 9), facecolor=ET_DARK)
        ax.set_facecolor(ET_DARK)
        ax.set_xlim(-max_abs * 1.4, max_abs * 1.4)
        ax.set_ylim(-0.5, len(sorted_sectors) - 0.5)
        ax.axis('off')

        for i, sector in enumerate(sorted_sectors):
            val = sector['change_pct']
            bar_val = val * progress
            color = ET_GREEN if val >= 0 else ET_RED

            # Horizontal bar from center
            ax.barh(i, bar_val, color=color, alpha=0.85, height=0.65)
            ax.text(-max_abs * 1.35, i, sector['sector'],
                    color=ET_WHITE, fontsize=13, va='center', fontweight='bold')
            if progress > 0.5:
                sign = "+" if val >= 0 else ""
                ax.text(bar_val + (0.05 if val >= 0 else -0.05), i,
                        f"{sign}{val:.2f}%",
                        color=color, fontsize=12, va='center',
                        ha='left' if val >= 0 else 'right')

        ax.axvline(0, color='#555555', linewidth=1)

        # Title
        ax.text(0, len(sorted_sectors) + 0.3, "SECTOR ROTATION TODAY",
                color=ET_WHITE, fontsize=20, fontweight='bold', ha='center')

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight', facecolor=ET_DARK)
        plt.close(fig)
        buf.seek(0)
        frames.append(buf.read())

    return frames
```

---

### H7–H8: Main API route + frontend

**Main route (`routes/video.py`):**

```python
# routes/video.py
from fastapi import APIRouter
from fastapi.responses import FileResponse
import os, tempfile
from models.video import VideoRequest, VideoType
from generators.orchestrator import generate_video

router = APIRouter(prefix="/video", tags=["video"])

@router.post("/generate")
async def generate_market_video(request: VideoRequest):
    """
    Generates a market update video.
    video_type: "market_wrap" | "sector_rotation" | "race_chart" | "ipo_tracker"
    Returns: {status, video_url, script, duration_sec}
    """
    output_path = tempfile.mktemp(suffix='.mp4')
    result = await generate_video(request.video_type, output_path)
    return {
        "status": "complete",
        "video_url": f"/video/download/{os.path.basename(output_path)}",
        "script": result.get("script", ""),
        "duration_sec": result.get("duration_sec", 0),
        "frame_count": result.get("frame_count", 0),
    }

@router.get("/download/{filename}")
async def download_video(filename: str):
    path = os.path.join(tempfile.gettempdir(), filename)
    if not os.path.exists(path):
        return {"error": "Video not found"}
    return FileResponse(path, media_type="video/mp4", filename="et-market-update.mp4")
```

**Frontend generator page (`src/App.jsx`):**

```jsx
// Key component: VideoTypeSelector + GenerationProgress + VideoPreview
'use client';
import { useState } from 'react';

const VIDEO_TYPES = [
  { id: 'market_wrap', title: 'Daily Market Wrap', desc: '60s daily recap — Nifty, gainers, losers', icon: '📊' },
  { id: 'sector_rotation', title: 'Sector Rotation', desc: 'Which sectors are hot/cold today', icon: '🔄' },
  { id: 'race_chart', title: 'Nifty 50 Race Chart', desc: '1-year return race animation', icon: '🏁' },
  { id: 'ipo_tracker', title: 'IPO Tracker', desc: 'Current IPOs status & GMP', icon: '🚀' },
];

export default function Page() {
  const [selected, setSelected] = useState(null);
  const [status, setStatus] = useState('idle'); // idle | generating | done | error
  const [progress, setProgress] = useState([]);
  const [result, setResult] = useState(null);

  const generate = async () => {
    if (!selected) return;
    setStatus('generating');
    setProgress(['Fetching live market data...']);

    // Simulate progress updates (backend takes 15–30 seconds)
    const steps = [
      'Fetching live market data...',
      'Generating video frames...',
      'Creating voiceover script...',
      'Converting script to audio...',
      'Assembling final video...',
    ];
    for (let i = 0; i < steps.length; i++) {
      await new Promise(r => setTimeout(r, 3000));
      setProgress(prev => [...prev, steps[i]]);
    }

    const res = await fetch('http://localhost:8004/video/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ video_type: selected }),
    });
    const data = await res.json();
    setResult(data);
    setStatus('done');
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white p-8">
      <h1 className="text-3xl font-bold mb-2">AI Market Video Engine</h1>
      <p className="text-gray-400 mb-8">Generate professional market update videos in seconds — zero editing required.</p>

      <div className="grid grid-cols-2 gap-4 mb-8 max-w-2xl">
        {VIDEO_TYPES.map(vt => (
          <button key={vt.id} onClick={() => setSelected(vt.id)}
            className={`p-4 rounded-xl border text-left transition-all ${
              selected === vt.id ? 'border-red-500 bg-red-950' : 'border-gray-700 bg-gray-900 hover:border-gray-500'
            }`}>
            <div className="text-2xl mb-2">{vt.icon}</div>
            <div className="font-semibold">{vt.title}</div>
            <div className="text-sm text-gray-400 mt-1">{vt.desc}</div>
          </button>
        ))}
      </div>

      <button onClick={generate} disabled={!selected || status === 'generating'}
        className="bg-red-600 hover:bg-red-700 disabled:opacity-40 px-8 py-3 rounded-xl font-semibold text-lg mb-8">
        {status === 'generating' ? 'Generating...' : 'Generate Video'}
      </button>

      {progress.length > 0 && (
        <div className="max-w-lg mb-8 space-y-2">
          {progress.map((step, i) => (
            <div key={i} className="flex items-center gap-2 text-sm text-gray-300">
              <span className="text-green-400">✓</span> {step}
            </div>
          ))}
        </div>
      )}

      {status === 'done' && result && (
        <div className="max-w-2xl">
          <video controls className="w-full rounded-xl mb-4 border border-gray-700"
                 src={`http://localhost:8004${result.video_url}`} />
          <div className="flex gap-3">
            <a href={`http://localhost:8004${result.video_url}`} download
               className="bg-white text-gray-900 px-5 py-2 rounded-xl font-medium hover:bg-gray-100">
              Download MP4
            </a>
          </div>
          {result.script && (
            <div className="mt-4 bg-gray-900 rounded-xl p-4">
              <p className="text-xs text-gray-500 mb-2 font-medium uppercase tracking-wide">Voiceover script</p>
              <p className="text-sm text-gray-300 leading-relaxed">{result.script}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
```

---

### H8–H9: Polish + fallbacks

- [ ] If video generation takes > 30 seconds, show live progress steps
- [ ] Add "Preview script" button before generating — lets user see the LLM script
- [ ] If TTS fails, generate video without audio (still a good demo)
- [ ] Add watermark: "ET Markets AI" in bottom-right corner of every frame
- [ ] Test all 4 video types work end to end

---

### H9–H12: Demo prep

**Demo scenario (practice this exactly):**
1. Open the Video Engine at localhost:3004
2. Click "Daily Market Wrap" card
3. Click "Generate Video" — show the progress steps ticking off
4. Video plays in browser — 45-60 seconds of animated market data
5. Show the voiceover script it generated
6. Click "Download MP4" — show it downloads
7. Quickly show: click "Sector Rotation" → generate → different video style

**Key talking point:** *"Zero human editing. Our AI fetched today's market data, generated a script, converted it to speech, built the animated frames, and assembled this video in 30 seconds. An ET producer would take 3 hours to do this manually."*

---

## Pydantic models reference

```python
# models/video.py
from pydantic import BaseModel
from enum import Enum

class VideoType(str, Enum):
    MARKET_WRAP = "market_wrap"
    SECTOR_ROTATION = "sector_rotation"
    RACE_CHART = "race_chart"
    IPO_TRACKER = "ipo_tracker"

class VideoRequest(BaseModel):
    video_type: VideoType
    date: str | None = None      # defaults to today if not provided
    custom_tickers: list[str] = []  # optional custom stock list

class VideoStatus(BaseModel):
    status: str                  # "generating" | "complete" | "error"
    video_url: str | None = None
    script: str | None = None
    duration_sec: float | None = None
    frame_count: int | None = None
    error: str | None = None
```

---

## If you get blocked

| Problem | Fix |
|---------|-----|
| MoviePy install fails | `pip install moviepy==1.0.3` (older version more stable) |
| gTTS needs internet | Pre-generate audio file: `python -c "from gtts import gTTS; gTTS('test').save('test.mp3')"` |
| matplotlib frames slow | Reduce DPI to 72 for dev, use 120 only for final |
| Video has no audio | Show video-only in demo — frames + animation still impressive |
| NSE data unavailable | Use hardcoded mock data in `services/market_data.py` — just return the dict directly |

---

## API endpoints summary

```
GET  /health                            → health check
POST /video/generate  body: {video_type: "market_wrap"}  → generates video, returns URL
GET  /video/download/{filename}         → streams/downloads the MP4 file
```