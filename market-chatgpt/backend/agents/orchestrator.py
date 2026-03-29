import json, asyncio, sys
from fastapi.responses import StreamingResponse
from services.llm import stream_llm
from agents.query_planner import plan
from agents.retrieval_agent import retrieve

ANALYSIS_PROMPT = """
You are a senior equity analyst and live market omniscient advisor at India's top brokerage.
The user's question: {question}

Their active context (Live Dashboard filters or Portfolio):
{market_str}

Market data and news retrieved (use ONLY these facts — do not add facts you don't see here):
{context_str}

Conversation history:
{history_str}

Instructions:
1. Answer the question directly and specifically based on the context above.
2. Use real numbers from the data above. Never fabricate statistics.
3. For each specific stock you discuss, try to include a SIGNAL: bullish/bearish/neutral and 1-2 reasons.
4. Keep your total answer under 350 words. Focus on insight rather than reciting.
5. After your answer, output a JSON block like this (EXACTLY this format on its own line):
   SIGNALS_JSON: [{{"ticker": "RELIANCE.NS", "signal": "bullish", "confidence": 0.84, "reasons": ["reason1", "reason2"]}}]
"""

async def run(question: str, portfolio: list, market_context: list, history: list):

    async def event_stream():
        yield f"data: {json.dumps({'type': 'thinking', 'content': 'Planning analysis...'})}\n\n"

        # 1. Plan
        sub_queries = plan(question, portfolio, market_context)
        tickers_mentioned = set(q.split('.NS')[0].split()[0] for q in sub_queries)

        yield f"data: {json.dumps({'type': 'thinking', 'content': f'Fetching data for {len(sub_queries)} queries...'})}\n\n"

        # 2. Retrieve context
        try:
            context_docs = retrieve(sub_queries, portfolio, market_context)
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': f'Retrieval Error: {str(e)}'})}\n\n"
            context_docs = []

        # Build prompt variables
        portfolio_str = "\n".join([
            f"- [PORTFOLIO] {h['ticker']}: {h['quantity']} shares @ avg ₹{h['avg_buy_price']}"
            for h in portfolio
        ])

        market_context_str = "\n".join([
            f"- [DASHBOARD] {m['ticker']} (LTP: ₹{m['current_price']}, Chg: {m['pnl_pct']}%)"
            for m in market_context[:40] # cap the context so we don't blow context sizes
        ])

        market_str = portfolio_str + ("\n" if portfolio_str and market_context_str else "") + market_context_str
        if not market_str.strip():
            market_str = "No specific portfolio or dashboard filters active."
        
        context_str = "\n\n".join([
            f"[{doc['source_type'].upper()}] ({doc.get('ticker','?')}): {doc['content']}"
            for doc in context_docs[:15]  # limit to 15 docs for token budget
        ]) if context_docs else "No specific news or facts could be retrieved at this moment."

        history_str = "\n".join([
            f"{m.get('role', 'user')}: {m.get('content', '')}"
            for m in history[-3:]  # last 3 turns
        ]) if history else "No previous history."

        market_str = portfolio_str + ("\n" if portfolio_str else "") + "No specific filters"
        
        prompt = ANALYSIS_PROMPT.replace('{question}', str(question))\
                                .replace('{market_str}', str(market_str))\
                                .replace('{context_str}', str(context_str))\
                                .replace('{history_str}', str(history_str))

        yield f"data: {json.dumps({'type': 'thinking', 'content': 'Generating analysis...'})}\n\n"

        # 3. Stream LLM response
        full_response = ""
        try:
            async for token in stream_llm(prompt):
                full_response += token
                if "SIGNALS_JSON:" not in full_response:  # don't stream the JSON block itself to the user
                    yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': f'LLM Generation Error: {str(e)}'})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            return

        # 4. Extract and emit signal cards
        if "SIGNALS_JSON:" in full_response:
            try:
                json_part = full_response.split("SIGNALS_JSON:")[1].strip()
                if json_part.startswith("```json"): json_part = json_part[7:]
                if json_part.startswith("```"): json_part = json_part[3:]
                json_part = json_part.strip().replace("```", "")
                
                signals = json.loads(json_part)
                if isinstance(signals, list):
                    for signal in signals:
                        yield f"data: {json.dumps({'type': 'signal_card', 'content': signal})}\n\n"
            except Exception as e:
                print(f"Error parsing signals JSON: {e}")

        # 5. Emit sources
        # Emit uniquely by URL
        seen_urls = set()
        for doc in context_docs[:6]:
            if doc.get('url') and doc['url'] not in seen_urls:
                seen_urls.add(doc['url'])
                title_short = doc['content'].split('\n')[0].replace('[NEWS] ', '').strip()[:60]
                if doc['source_type'] == 'fundamentals': url_title = "Yahoo Finance Fundamentals"
                else: url_title = title_short + "..."
                
                yield f"data: {json.dumps({'type': 'source', 'url': doc['url'], 'title': url_title})}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "Connection": "keep-alive"})
