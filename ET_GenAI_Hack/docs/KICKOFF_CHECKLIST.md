# Kickoff Checklist

Quick steps to get the team running in the first 30 minutes.

# Kickoff Checklist — First 30 Minutes

> **Do this together, before anyone writes a single line of code.**
> Time budget: H0:00 to H0:30. Then everyone splits to their product.

---

## Step 1: API keys (H0:00 – H0:10)

Everyone needs these. One person creates, shares in group chat immediately.

### Anthropic API (for LLM)
1. Go to: https://console.anthropic.com
2. Sign in / create account
3. Settings → API Keys → Create Key
4. Copy key → share in group chat immediately
5. Test it works: `curl https://api.anthropic.com/v1/messages -H "x-api-key: YOUR_KEY" -H "anthropic-version: 2023-06-01" -H "content-type: application/json" -d '{"model":"claude-haiku-20240307","max_tokens":10,"messages":[{"role":"user","content":"hi"}]}'`
6. Should return `{"content":[{"text":"Hi!...`

### Tavily API (for news search — T1, T3 need this)
1. Go to: https://app.tavily.com
2. Sign up free → API Keys → copy key
3. Free tier: 1000 searches/month (more than enough)

### No other API keys needed
- yfinance: free, no key
- NSE India public endpoints: free, no key
- gTTS (T4): free, no key
- ChromaDB (T3): local, no key

---

## Step 2: GitHub repo (H0:05 – H0:10, T4 does this)

```bash
# T4 does this, everyone else clones
mkdir et-ai-hackathon-ps6
cd et-ai-hackathon-ps6
git init
git branch -M main

# Create the folder structure
mkdir -p shared opportunity-radar/backend opportunity-radar/frontend
mkdir -p chart-pattern-intel/backend chart-pattern-intel/frontend
mkdir -p market-chatgpt/backend market-chatgpt/frontend
mkdir -p market-video-engine/backend market-video-engine/frontend
mkdir -p data docs scripts

# Create .gitignore first (NEVER commit .env or keys)
cat > .gitignore << 'EOF'
.env
*.env
__pycache__/
*.pyc
venv/
node_modules/
.next/
*.mp4
*.mp3
chroma_db/
*.egg-info/
.DS_Store
EOF

# Create shared .env.example
cat > shared/.env.example << 'EOF'
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
OPENAI_API_KEY=sk-your-key-here-optional
LLM_MODEL=claude-sonnet-4-20250514
TAVILY_API_KEY=tvly-your-key-here
EOF

# Initial commit
git add .
git commit -m "feat: initial repo structure — ET AI Hackathon PS6"

# Push to GitHub
# Create repo on github.com first (public), then:
git remote add origin https://github.com/your-team/et-ai-hackathon-ps6
git push -u origin main

# Add all 4 teammates as collaborators on GitHub
# Settings → Collaborators → Add people → enter GitHub usernames
```

**After T4 pushes, everyone clones:**
```bash
git clone https://github.com/your-team/et-ai-hackathon-ps6
cd et-ai-hackathon-ps6
cp shared/.env.example shared/.env
# Fill in your API keys in shared/.env
```

---

## Step 3: Each person sets up their product (H0:10 – H0:25)

Do these in parallel — all 4 at the same time.

### T1 setup
```bash
cd opportunity-radar/backend
python -m venv venv && source venv/bin/activate
pip install fastapi uvicorn requests yfinance pandas anthropic openai python-dotenv

# Test NSE data (run this before anything else)
python -c "import requests; r = requests.get('https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%2050', headers={'User-Agent':'Mozilla/5.0'}); print(r.status_code)"
# If 200: NSE is accessible. If 403/blocked: you'll use sample data (already handled in code)
```

### T2 setup
```bash
cd chart-pattern-intel/backend
python -m venv venv && source venv/bin/activate
pip install fastapi uvicorn yfinance pandas matplotlib anthropic openai python-dotenv

# Test yfinance (most important dependency)
python -c "import yfinance as yf; df = yf.Ticker('RELIANCE.NS').history(period='6mo'); print(f'Got {len(df)} days of data')"
# Should print: Got ~126 days of data
```

### T3 setup
```bash
cd market-chatgpt/backend
python -m venv venv && source venv/bin/activate
pip install fastapi uvicorn yfinance pandas anthropic openai chromadb tavily-python python-dotenv python-multipart

# Test LLM
python -c "
import anthropic, os
from dotenv import load_dotenv
load_dotenv('../../shared/.env')
client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
msg = client.messages.create(model='claude-haiku-20240307', max_tokens=20, messages=[{'role':'user','content':'say hi'}])
print(msg.content[0].text)
"
# Should print: Hi! or Hello!
```

### T4 setup
```bash
cd market-video-engine/backend
python -m venv venv && source venv/bin/activate
pip install fastapi uvicorn yfinance pandas matplotlib pillow moviepy gTTS anthropic openai python-dotenv

# Test MoviePy (trickiest dependency)
python -c "from moviepy.editor import ImageSequenceClip; print('MoviePy OK')"
# If error: pip install moviepy==1.0.3 (older version more stable)

# Test gTTS
python -c "from gtts import gTTS; gTTS('test').save('/tmp/test.mp3'); print('gTTS OK')"
```

---

## Step 4: 10-minute sync meeting (H0:25 – H0:35)

Stand up. Go around quickly. Keep it to 10 minutes max.

### Agenda (strict)

**2 minutes — verify everyone is unblocked:**
- T1: "yfinance working? NSE accessible?"
- T2: "OHLCV data pulling?"
- T3: "LLM API returning response?"
- T4: "MoviePy imported without error?"

**3 minutes — agree on demo scenario:**
- T4 describes the 3-minute pitch video flow
- All 4 products must have ONE working demo scenario by H9
- Each demo scenario should be < 60 seconds to walk through

**2 minutes — agree on sync checkpoints:**
- H3: Each person shows their skeleton (running app, even if just health endpoint)
- H6: Core feature working (even if rough)
- H9: Full demo flow working — THIS IS THE HARD DEADLINE
- H11: Record pitch video together

**2 minutes — designate help channels:**
- Stuck on LLM? → T3 has most experience with it
- Stuck on data? → T1 or T2 help
- Stuck on frontend? → T3 helps
- Stuck on video gen? → T4 figures it out (no one else is building this)
- Blocked for > 20 minutes? → IMMEDIATELY shout in group chat, don't spin alone

**1 minute — go!**
```
✓ Everyone has API keys in their .env
✓ Everyone has cloned the repo
✓ Everyone's venv is set up
✓ Everyone knows their product's README location
✓ Sync times agreed: H3, H6, H9, H11

GO BUILD.
```

---

## Green light criteria — before splitting off

Every teammate must confirm ALL of these before going heads-down:

```
[ ] I can run: uvicorn main:app --reload --port 800X  (no import errors)
[ ] I can run: npm run dev -- --port 300X  (Next.js loads at localhost:300X)
[ ] I have my API keys in shared/.env
[ ] LLM API returns a response when I test it
[ ] yfinance returns data for RELIANCE.NS
[ ] I have read my product's README.md completely
[ ] I know exactly what I'm building in H0–H3
```

If any box is unchecked → fix it NOW, before splitting. Don't leave with a broken setup.

---

## Emergency fallbacks (if things go wrong)

| Situation | What to do |
|-----------|-----------|
| LLM API key doesn't work | Use OpenAI key instead — swap `ANTHROPIC_API_KEY` for `OPENAI_API_KEY` |
| NSE API blocked entirely | Load all data from `/data/sample_*.json` files (pre-committed) |
| yfinance rate limited | Add `time.sleep(1)` between calls; cache results in memory |
| MoviePy won't install (T4) | Build a slideshow (PIL images shown as "video frames") instead of MP4 |
| ChromaDB fails (T3) | Skip RAG, answer without filing context — still works |
| Frontend won't build | Demo backend via Swagger UI at localhost:800X/docs |
| Person completely blocked | Shout in group chat at H3 — NOT H6. Early signal = fixable. Late signal = panic. |

---

## Git workflow during hackathon

```bash
# Each person works on their own branch
git checkout -b feature/opportunity-radar    # T1
git checkout -b feature/chart-patterns       # T2
git checkout -b feature/market-chatgpt       # T3
git checkout -b feature/video-engine         # T4

# Commit frequently — judges look at commit history
# Good commit messages:
git commit -m "feat(radar): NSE bulk deal scanner working"
git commit -m "feat(charts): breakout detector returning patterns"
git commit -m "fix(chatgpt): SSE streaming now stable"
git commit -m "feat(video): market wrap frames generating"

# Merge to main at H9 (T4 coordinates this)
git checkout main
git merge feature/opportunity-radar
git merge feature/chart-patterns
git merge feature/market-chatgpt
git merge feature/video-engine
git push origin main

# Final push must be before submission deadline
```