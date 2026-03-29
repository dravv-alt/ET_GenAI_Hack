from fastapi import APIRouter, UploadFile, File, HTTPException
import csv, io, yfinance as yf, time
from pydantic import BaseModel

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

        try:
            qty = int(row['quantity'])
            avg_price = float(row['avg_buy_price'])
        except ValueError:
            raise HTTPException(400, f"Row {i}: quantity and avg_buy_price must be numbers")

        # Fetch current price
        # time.sleep(0.2)  # Reduce sleep to speed up response
        stock = yf.Ticker(ticker)
        try:
            info = stock.fast_info
            current_price = getattr(info, 'last_price', avg_price)  # fallback to avg if unavailable
        except Exception:
            current_price = avg_price
            
        pnl_abs = (current_price - avg_price) * qty
        pnl_pct = ((current_price - avg_price) / avg_price) * 100 if avg_price > 0 else 0

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
            "total_pnl_pct": round((total_value - total_invested) / total_invested * 100, 2) if total_invested > 0 else 0,
            "holdings_count": len(holdings),
        }
    }

class QuestionRequest(BaseModel):
    tickers: list[str]

@router.post("/questions")
async def generate_questions(req: QuestionRequest):
    from services.llm import call_llm
    import json
    
    if not req.tickers:
        return {"questions": ["What is the market doing today?", "Which sectors are hot right now?", "Are there any strong buy signals?"]}
        
    tickers_str = ", ".join(req.tickers[:10])
    prompt = f"The user holds these stocks: {tickers_str}. Generate exactly 5 personalized investment questions they might ask about their portfolio right now. Return ONLY a valid JSON array of 5 strings. Do not include markdown formatting or ANY other text. Example: [\"Is Apple at risk?\", \"Should I buy more NVDA?\"]"
    try:
        res = call_llm(prompt)
        clean = res.strip()
        if clean.startswith("```json"): clean = clean[7:]
        if clean.startswith("```"): clean = clean[3:]
        if clean.endswith("```"): clean = clean[:-3]
        questions = json.loads(clean.strip())
        return {"questions": questions}
    except Exception as e:
        print("Error generating questions:", e)
        return {"questions": ["Which of my holdings are at risk this quarter?", "Which stock in my portfolio has the strongest buy signal?", "Should I rebalance my portfolio?"]}
