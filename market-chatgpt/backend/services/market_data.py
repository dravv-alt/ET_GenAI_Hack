import yfinance as yf

def get_fundamentals(ticker: str) -> dict:
    """
    Fetch market fundamentals for a given ticker symbol.
    """
    try:
        if not ticker.endswith('.NS'):
            ticker += '.NS'
            
        stock = yf.Ticker(ticker)
        info = getattr(stock, 'info', {})
        
        pe_ratio = info.get('trailingPE', 'N/A')
        eps = info.get('trailingEps', 'N/A')
        market_cap = info.get('marketCap', 'N/A')
        
        # Format market cap
        if isinstance(market_cap, (int, float)):
            if market_cap >= 1e12:
                market_cap = f"₹{round(market_cap / 1e12, 2)}T"
            elif market_cap >= 1e9:
                market_cap = f"₹{round(market_cap / 1e9, 2)}B"
                
        return {
            "pe_ratio": pe_ratio,
            "eps": eps,
            "market_cap": market_cap,
            "52_week_high": info.get('fiftyTwoWeekHigh', 'N/A'),
            "52_week_low": info.get('fiftyTwoWeekLow', 'N/A')
        }
    except Exception as e:
        print(f"Error fetching fundamentals for {ticker}: {e}")
        return {}
