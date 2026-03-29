"""
services/llm_analyzer.py
========================
LLM wrapper specific to the Opportunity Radar module.

PURPOSE:
    Provides the `analyze_sentiment()` function used by the sentiment scanner
    to detect management commentary tone shifts via the LLM.

HOW IT WORKS:
    1. Accepts prev_commentary and curr_commentary strings (quarterly mgmt commentary).
    2. Formats them into a structured prompt asking for a JSON analysis.
    3. Calls shared/llm_client.py::call_llm() — which tries Gemini then Groq.
    4. Parses the JSON response and returns a dict with shift analysis.
    5. Returns None if:
       - No shift detected by the LLM
       - Confidence below 0.55 (too uncertain to surface as an alert)
       - LLM call fails for any reason
       - JSON parsing fails

PROMPT STRATEGY:
    The prompt instructs the LLM to return ONLY a JSON object (no markdown, no
    explanation). This makes parsing reliable. We use json.loads() directly.

    If the LLM wraps output in ```json ... ``` code fences (common with Gemini),
    we strip those before parsing.

THE SENTIMENT PROMPT:
    Analyzes 5 dimensions of tone shift:
        1. Revenue/growth outlook
        2. Margin guidance
        3. Capex plans
        4. Risk language frequency
        5. New product/expansion mentions

    Returns JSON:
    {
        "shift_detected": true/false,
        "shift_direction": "positive" | "negative" | "neutral",
        "shift_magnitude": "high" | "medium" | "low",
        "key_change": "one sentence describing the main shift",
        "why_it_matters": "investment implication for retail investor",
        "confidence": 0.0–1.0
    }

USAGE:
    from services.llm_analyzer import analyze_sentiment

    result = analyze_sentiment("RELIANCE", prev_text, curr_text)
    if result:
        print(result["shift_direction"], result["confidence"])
"""

import json
import os
import sys

# Add shared/ to path so we can import llm_client from the shared utilities
# This works regardless of the working directory uvicorn is launched from.
_SHARED_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared")
sys.path.insert(0, os.path.abspath(_SHARED_PATH))

try:
    from llm_client import call_llm
    _LLM_AVAILABLE = True
except ImportError:
    print("[llm_analyzer] WARNING: Could not import llm_client from shared/. "
          "Sentiment scanning will be disabled.")
    _LLM_AVAILABLE = False


# ── Sentiment analysis prompt ─────────────────────────────────────────────────
# This prompt is carefully engineered to:
#   1. Give the LLM a clear analyst persona (reduces hallucination)
#   2. Focus on 5 specific, measurable dimensions
#   3. Require ONLY a JSON response (no free-form text, easier to parse)
#   4. Include confidence so we can filter out weak signals
_SENTIMENT_PROMPT = """
You are a senior equity research analyst at a top Indian brokerage house.
I will give you two management commentary excerpts from consecutive quarterly results of {symbol}.

PREVIOUS QUARTER COMMENTARY:
{prev_commentary}

CURRENT QUARTER COMMENTARY:
{curr_commentary}

Analyze the SHIFT in tone and content between the two. Focus ONLY on these 5 dimensions:
1. Revenue/growth outlook — more optimistic or cautious?
2. Margin guidance — expanding or contracting expectations?
3. Capex plans — investing more or pulling back?
4. Risk language — more or fewer risk caveats?
5. New product/expansion mentions — any new markets or growth catalysts?

You MUST return ONLY a valid JSON object with EXACTLY these keys and NO other text:
{{
  "shift_detected": true or false,
  "shift_direction": "positive" or "negative" or "neutral",
  "shift_magnitude": "high" or "medium" or "low",
  "key_change": "one concise sentence describing the most important shift",
  "why_it_matters": "one sentence on what this means for investors",
  "confidence": a number between 0.0 and 1.0
}}

Do NOT include markdown, code fences, or any explanation outside the JSON object.
"""


def analyze_sentiment(
    symbol: str,
    prev_commentary: str,
    curr_commentary: str,
) -> dict | None:
    """
    Uses LLM to detect a meaningful tone shift between two management commentaries.

    Args:
        symbol:          NSE ticker (e.g. "RELIANCE") — used in the prompt for context.
        prev_commentary: Management commentary text from the previous quarter.
                         Will be truncated to first 2000 chars.
        curr_commentary: Management commentary text from the current quarter.
                         Will be truncated to first 2000 chars.

    Returns:
        dict with keys: shift_detected, shift_direction, shift_magnitude,
                        key_change, why_it_matters, confidence
        OR None if:
            - LLM not available (no API key)
            - No shift detected (shift_detected == false)
            - Confidence < 0.55 (signal too weak)
            - LLM call fails
            - JSON parsing fails

    TRUNCATION:
        Commentaries are truncated to 2000 chars each to stay within token budgets
        for free-tier models (Gemini free = 1M input tokens limit, but we stay lean).
    """
    if not _LLM_AVAILABLE:
        print(f"[llm_analyzer] LLM not available. Skipping sentiment scan for {symbol}.")
        return None

    if not prev_commentary or not curr_commentary:
        return None

    # Truncate to 2000 chars each to control token cost
    prompt = _SENTIMENT_PROMPT.format(
        symbol=symbol,
        prev_commentary=prev_commentary[:2000],
        curr_commentary=curr_commentary[:2000],
    )

    try:
        raw_response = call_llm(prompt, max_tokens=500)

        # Strip markdown code fences if LLM wraps the JSON (Gemini sometimes does this)
        # e.g. ```json\n{...}\n``` → {…}
        cleaned = raw_response.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            # Remove first line (```json or ```) and last line (```)
            cleaned = "\n".join(lines[1:-1]).strip()

        data = json.loads(cleaned)

        # Only return a result if the LLM detected a meaningful shift with sufficient confidence
        if not data.get("shift_detected", False):
            print(f"[llm_analyzer] No shift detected for {symbol}.")
            return None

        confidence = float(data.get("confidence", 0))
        if confidence < 0.55:
            print(f"[llm_analyzer] Low confidence ({confidence:.2f}) for {symbol}. Skipping.")
            return None

        print(f"[llm_analyzer] Sentiment shift detected for {symbol}: "
              f"{data.get('shift_direction')} ({confidence:.2f} confidence)")
        return data

    except json.JSONDecodeError as e:
        print(f"[llm_analyzer] JSON parse error for {symbol}: {e}. Raw: {raw_response[:200]}")
        return None
    except Exception as e:
        print(f"[llm_analyzer] Sentiment analysis failed for {symbol}: {e}")
        return None
