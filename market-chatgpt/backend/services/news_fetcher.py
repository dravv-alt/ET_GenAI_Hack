from duckduckgo_search import DDGS

def search_news(query: str, max_results: int = 3) -> list[dict]:
    """
    Use DuckDuckGo Search API to find recent news for a query.
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.news(query + " stock market", max_results=max_results))
            
        return [
            {
                "title": r.get('title', ''),
                "url": r.get('url', ''),
                "content": r.get('body', '')
            }
            for r in results
        ]
    except Exception as e:
        print(f"Error fetching news for '{query}': {e}")
        return []
