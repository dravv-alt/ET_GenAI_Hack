import os
from tavily import TavilyClient

def search_news(query: str, max_results: int = 3) -> list[dict]:
    """
    Use Tavily Search API to find recent news for a query.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        print("Warning: TAVILY_API_KEY not set. Cannot fetch real news.")
        return []
        
    try:
        tavily = TavilyClient(api_key=api_key)
        response = tavily.search(query=query + " news india recent", search_depth="basic", max_results=max_results)
        
        results = []
        for r in response.get("results", []):
            results.append({
                "title": r.get('title', ''),
                "url": r.get('url', ''),
                "content": r.get('content', '')
            })
        return results
    except Exception as e:
        print(f"Error fetching news for '{query}': {e}")
        return []
