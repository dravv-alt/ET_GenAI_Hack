from services.market_data import get_fundamentals
from services.news_fetcher import search_news

def retrieve(sub_queries: list[str], portfolio: list, market_context: list = None) -> list[dict]:
    """
    For each sub-query: fetch price data + news + fundamentals.
    Returns list of context docs with: content, url, source_type, ticker
    """
    context_docs = []
    tickers_in_portfolio = {h['ticker'] for h in portfolio}
    if market_context:
        tickers_in_portfolio.update({m['ticker'] + '.NS' for m in market_context})

    for query in sub_queries:
        # Find which ticker this query is about
        ticker = None
        for t in tickers_in_portfolio:
            if t.replace('.NS', '').lower() in query.lower():
                ticker = t
                break
                
        # If no explicit ticker found, guess if any ticker from portfolio/market is substring
        if not ticker:
            for t in tickers_in_portfolio:
                base_t = t.split('.')[0].lower()
                if base_t in query.lower():
                    ticker = t
                    break

        # Fetch news for this query
        news_results = search_news(query, max_results=3)
        for article in news_results:
            context_docs.append({
                "content": f"[NEWS] {article['title']}\n{article['content'][:500]}",
                "url": article['url'],
                "source_type": "news",
                "ticker": ticker,
                "query": query,
            })

        # Fetch fundamentals if ticker identified
        if ticker:
            try:
                fundamentals = get_fundamentals(ticker)
                if fundamentals:
                    context_docs.append({
                        "content": f"[FUNDAMENTALS] {ticker}: PE={fundamentals.get('pe_ratio')}, "
                                   f"EPS={fundamentals.get('eps')}, MarketCap={fundamentals.get('market_cap')}",
                        "url": f"https://finance.yahoo.com/quote/{ticker}",
                        "source_type": "fundamentals",
                        "ticker": ticker,
                        "query": query,
                    })
            except:
                pass

    return context_docs
