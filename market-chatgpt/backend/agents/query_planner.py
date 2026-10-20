import sys, json
from services.llm import call_llm

PLANNER_PROMPT = """
The user has asked: "{question}"

Their portfolio contains these stocks: {tickers}

Your job: break this question into specific data-retrieval sub-queries needed to answer it fully.
Only generate sub-queries for stocks RELEVANT to the question.
Return ONLY a valid JSON array of strings. No explanation. No markdown.

Example output: ["RELIANCE.NS Q3 FY24 earnings results", "INFY.NS revenue guidance 2024", "HDFC.NS NPA ratio Q3"]
Maximum {max_queries} sub-queries.
"""

def plan(question: str, portfolio: list, market_context: list = None, max_queries: int = 4) -> list[str]:
    tickers = [h['ticker'] for h in portfolio]
    if market_context:
        tickers.extend([m['ticker'] + ".NS" for m in market_context])
    # deduplicate
    tickers = list(set(tickers))
    
    prompt = PLANNER_PROMPT.format(
        question=question,
        tickers=", ".join(tickers) if tickers else "The general Indian market",
        max_queries=max_queries,
    )
    
    try:
        response = call_llm(prompt)
        # Strip markdown if LLM wraps in backticks
        clean = response.strip()
        if clean.startswith("```json"):
            clean = clean[7:]
        if clean.startswith("```"):
            clean = clean[3:]
        if clean.endswith("```"):
            clean = clean[:-3]
        return json.loads(clean.strip())
    except Exception as e:
        print(f"Error in query planner: {e}")
        # Fallback: generate one query per ticker up to max
        return [f"{t} latest news and earnings" for t in tickers[:max_queries]]
