# shared/llm_client.py
# Used by ALL 4 teammates. Import like: sys.path.append("../../shared"); from llm_client import call_llm

import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

LLM_MODEL = os.getenv("LLM_MODEL", "claude-sonnet-4-20250514")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

def call_llm(prompt: str, max_tokens: int = 1000, system: str = None) -> str:
    """
    Synchronous LLM call. Returns full response string.
    Tries Anthropic first, falls back to OpenAI if key available.
    """
    if ANTHROPIC_KEY:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
        messages = [{"role": "user", "content": prompt}]
        kwargs = {"model": LLM_MODEL, "max_tokens": max_tokens, "messages": messages}
        if system:
            kwargs["system"] = system
        response = client.messages.create(**kwargs)
        return response.content[0].text

    elif OPENAI_KEY:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_KEY)
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        response = client.chat.completions.create(
            model="gpt-4o", max_tokens=max_tokens, messages=messages
        )
        return response.choices[0].message.content

    else:
        raise ValueError("No LLM API key found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY in shared/.env")


async def stream_llm(prompt: str, max_tokens: int = 1500, system: str = None):
    """
    Async streaming LLM call. Yields tokens as they arrive.
    Use in async contexts with: async for token in stream_llm(prompt): ...
    """
    if ANTHROPIC_KEY:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
        messages = [{"role": "user", "content": prompt}]
        kwargs = {"model": LLM_MODEL, "max_tokens": max_tokens, "messages": messages}
        if system:
            kwargs["system"] = system

        with client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                yield text

    elif OPENAI_KEY:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=OPENAI_KEY)
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        async with client.chat.completions.stream(
            model="gpt-4o", max_tokens=max_tokens, messages=messages
        ) as stream:
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
    else:
        raise ValueError("No LLM API key found.")


# Quick test — run this file directly to verify setup
if __name__ == "__main__":
    print("Testing LLM connection...")
    result = call_llm("Say 'LLM connection successful' and nothing else.")
    print(result)