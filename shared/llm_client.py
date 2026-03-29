"""
shared/llm_client.py
====================
Unified LLM client used by ALL products in this repository.

HOW TO IMPORT (from any product backend):
    import sys, os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
    from llm_client import call_llm, stream_llm

API KEY SETUP (in shared/.env):
    GEMINI_API_KEY=your-gemini-key-here       # Get free at: https://aistudio.google.com/apikey
    GROQ_API_KEY=your-groq-key-here           # Get free at: https://console.groq.com/keys
    LLM_MODEL=gemini-2.0-flash                # Default model (Gemini free tier)

FALLBACK LOGIC:
    1. Try Gemini (google-generativeai) with model 'gemini-2.0-flash'
    2. If GEMINI_API_KEY missing or call fails → try Groq (llama-3.3-70b-versatile)
    3. If both fail → raise ValueError with clear instructions

MODELS USED:
    - Gemini: gemini-2.0-flash (1M context, free tier, 15 RPM, 1500 requests/day)
    - Groq:   llama-3.3-70b-versatile (free tier, very fast inference)
"""

import os
from dotenv import load_dotenv

# Load from the .env file in the same directory as this script (shared/.env)
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Read keys and model config from environment
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
GROQ_KEY = os.getenv("GROQ_API_KEY")

# Default to gemini-2.0-flash. Can be overridden via LLM_MODEL env var.
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.0-flash")

# Groq model — Llama 3.3 70B is free and very capable
GROQ_MODEL = "llama-3.3-70b-versatile"


def call_llm(prompt: str, max_tokens: int = 1000, system: str = None) -> str:
    """
    Synchronous LLM call. Returns the full response as a string.

    Args:
        prompt:     The user message / instruction to send to the model.
        max_tokens: Maximum tokens in the response (default 1000).
        system:     Optional system prompt to set model behavior/persona.

    Returns:
        Full text response from the LLM as a plain string.

    Raises:
        ValueError: If no API key is found for either provider.

    FLOW:
        1. Attempt Gemini via google-generativeai SDK
        2. On any error or missing key → attempt Groq via groq SDK
        3. Both fail → raise ValueError
    """
    # ── Attempt 1: Gemini ──────────────────────────────────────────────────────
    if GEMINI_KEY:
        try:
            import google.generativeai as genai

            genai.configure(api_key=GEMINI_KEY)

            # Build the full prompt — Gemini doesn't have a separate 'system' param
            # in the basic generate_content call, so prepend it to the prompt.
            full_prompt = prompt
            if system:
                full_prompt = f"{system}\n\n{prompt}"

            model = genai.GenerativeModel(LLM_MODEL)
            response = model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=0.3,   # Lower temp = more consistent structured output
                ),
            )
            return response.text

        except Exception as e:
            print(f"[llm_client] Gemini failed: {e}. Trying Groq fallback...")

    # ── Attempt 2: Groq ────────────────────────────────────────────────────────
    if GROQ_KEY:
        try:
            from groq import Groq

            client = Groq(api_key=GROQ_KEY)

            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.3,
            )
            return response.choices[0].message.content

        except Exception as e:
            print(f"[llm_client] Groq failed: {e}")

    # ── Both failed ────────────────────────────────────────────────────────────
    raise ValueError(
        "No LLM API key found or all providers failed.\n"
        "Set GEMINI_API_KEY in shared/.env (get free key: https://aistudio.google.com/apikey)\n"
        "Or set GROQ_API_KEY in shared/.env (get free key: https://console.groq.com/keys)"
    )


async def stream_llm(prompt: str, max_tokens: int = 1500, system: str = None):
    """
    Async streaming LLM call. Yields text tokens as they arrive.

    Usage (in async context):
        async for token in stream_llm("explain nifty 50"):
            print(token, end="", flush=True)

    NOTE: Gemini streaming uses synchronous SDK in chunks; Groq supports true streaming.
    For hackathon purposes, Gemini will yield the full response as one chunk.

    Args:
        prompt:     The user message.
        max_tokens: Maximum tokens in the response.
        system:     Optional system prompt.

    Yields:
        str: Text chunks/tokens as they stream from the model.
    """
    # ── Attempt 1: Gemini streaming ────────────────────────────────────────────
    if GEMINI_KEY:
        try:
            import google.generativeai as genai

            genai.configure(api_key=GEMINI_KEY)

            full_prompt = prompt
            if system:
                full_prompt = f"{system}\n\n{prompt}"

            model = genai.GenerativeModel(LLM_MODEL)
            # Gemini supports stream=True — yields chunks
            response = model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=0.3,
                ),
                stream=True,
            )
            for chunk in response:
                if chunk.text:
                    yield chunk.text
            return

        except Exception as e:
            print(f"[llm_client] Gemini streaming failed: {e}. Trying Groq fallback...")

    # ── Attempt 2: Groq streaming ──────────────────────────────────────────────
    if GROQ_KEY:
        try:
            from groq import Groq

            client = Groq(api_key=GROQ_KEY)
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            # Groq supports streaming via stream=True
            stream = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.3,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
            return

        except Exception as e:
            print(f"[llm_client] Groq streaming failed: {e}")

    raise ValueError("No LLM API key found. Set GEMINI_API_KEY or GROQ_API_KEY in shared/.env")


# ── Quick test ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing LLM connection...")
    result = call_llm("Say 'LLM connection successful' and nothing else.")
    print(result)