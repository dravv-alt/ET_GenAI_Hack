from fastapi import APIRouter, HTTPException
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

router = APIRouter(prefix="/market", tags=["market"])

NIFTY_100_TICKERS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS", "ITC.NS", "SBI.NS", "BHARTIARTL.NS",
    "HINDUNILVR.NS", "LT.NS", "BAJFINANCE.NS", "HCLTECH.NS", "ASIANPAINT.NS", "AXISBANK.NS", "MARUTI.NS",
    "SUNPHARMA.NS", "KOTAKBANK.NS", "TITAN.NS", "ULTRACEMCO.NS", "WIPRO.NS", "NTPC.NS", "ONGC.NS",
    "POWERGRID.NS", "TATASTEEL.NS", "M&M.NS", "COALINDIA.NS", "ADANIENT.NS", "ADANIPORTS.NS", "HINDALCO.NS",
    "JSWSTEEL.NS", "GRASIM.NS", "HEROMOTOCO.NS", "BAJAJFINSV.NS", "BAJAJ-AUTO.NS", "TECHM.NS", "INDUSINDBK.NS",
    "APOLLOHOSP.NS", "DRREDDY.NS", "DIVISLAB.NS", "CIPLA.NS", "EICHERMOT.NS", "BRITANNIA.NS", "NESTLEIND.NS",
    "TATAMOTORS.NS", "TATARELIABLE.NS", "SHREECEM.NS", "UPL.NS", "SBILIFE.NS", "HDFCLIFE.NS", "BPCL.NS",
    "LTIM.NS", "TATACONSUM.NS", "HAL.NS", "BEL.NS", "BOSCHLTD.NS", "CHOLAFIN.NS", "COLPAL.NS", "DABUR.NS",
    "DLF.NS", "GAIL.NS", "GODREJCP.NS", "HAVELLS.NS", "HDFCAMC.NS", "ICICIGI.NS", "ICICIPRULI.NS", "IOC.NS",
    "INDIGO.NS", "IRCTC.NS", "JINDALSTEL.NS", "JUBLFOOD.NS", "MUTHOOTFIN.NS", "NAUKRI.NS", "PIIND.NS",
    "PIDILITIND.NS", "RECLTD.NS", "PFC.NS", "SRF.NS", "SIEMENS.NS", "TVSMOTOR.NS", "TORNTPHARM.NS", "TRENT.NS",
    "UNITDSPR.NS", "VEDL.NS", "VOLTAS.NS", "ZOMATO.NS", "ABB.NS", "ACC.NS", "AMBUJACEM.NS", "AUROPHARMA.NS",
    "CONCOR.NS", "CROMPTON.NS", "DIXON.NS", "ESCORTS.NS", "GMRINFRA.NS", "IDFCFIRSTB.NS", "IGL.NS", "INDHOTEL.NS",
    "LUPIN.NS", "MFSL.NS", "MRF.NS", "PEL.NS", "PETRONET.NS", "PNB.NS", "SAIL.NS", "UBL.NS"
]

# Simple in-memory cache
market_cache = {"data": [], "last_updated": None}
CACHE_TTL = timedelta(minutes=5)

@router.get("/live")
async def get_live_market():
    global market_cache
    now = datetime.now()

    if market_cache["last_updated"] and now - market_cache["last_updated"] < CACHE_TTL:
        return {"data": market_cache["data"], "cached": True}

    try:
        # Fetch last 5 days to ensure we get at least 2 trading days for change calculation
        # group_by='ticker' isn't needed if we download normal and deal with MultiIndex
        df = yf.download(NIFTY_100_TICKERS, period="5d", progress=False)
        
        results = []
        if df.empty:
            raise Exception("yFinance returned empty DataFrame")

        # The structure is a MultiIndex columns: (Attribute, Ticker)
        # Attribute is 'Close', 'Volume', etc.
        closes = df['Close']
        volumes = df['Volume'] if 'Volume' in df else None
        
        for ticker in closes.columns:
            ticker_series = closes[ticker].dropna()
            if len(ticker_series) < 2:
                continue
                
            last_price = float(ticker_series.iloc[-1])
            prev_price = float(ticker_series.iloc[-2])
            
            pnl_abs = last_price - prev_price
            pnl_pct = (pnl_abs / prev_price) * 100 if prev_price > 0 else 0
            
            vol = 0
            if volumes is not None and ticker in volumes.columns:
                vol_series = volumes[ticker].dropna()
                if len(vol_series) >= 1:
                    vol = int(vol_series.iloc[-1])

            results.append({
                "ticker": ticker.replace('.NS', ''),
                "current_price": round(last_price, 2),
                "pnl_abs": round(pnl_abs, 2),
                "pnl_pct": round(pnl_pct, 2),
                "volume": vol
            })

        # Sort by pnl_pct descending (Top Gainers first)
        results.sort(key=lambda x: x['pnl_pct'], reverse=True)

        market_cache["data"] = results
        market_cache["last_updated"] = now
        
        return {"data": results, "cached": False}
        
    except Exception as e:
        print(f"Error fetching live market data: {e}")
        if market_cache["data"]:
            return {"data": market_cache["data"], "cached": True, "error": str(e)}
        raise HTTPException(500, f"Error fetching live data: {str(e)}")
