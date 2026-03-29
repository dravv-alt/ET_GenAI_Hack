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
