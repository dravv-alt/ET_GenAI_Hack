import os
from groq import AsyncGroq, Groq

# Use llama-3.3-70b-versatile for high reasoning capabilities by default
GROQ_MODEL = "llama-3.3-70b-versatile"

def get_groq_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is not set")
    return Groq(api_key=api_key)

def get_async_groq_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is not set")
    return AsyncGroq(api_key=api_key)

def call_llm(prompt: str, model: str = GROQ_MODEL, max_tokens: int = 1000) -> str:
    """Synchronous call for fast, single-turn tasks like query planning."""
    client = get_groq_client()
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=model,
        max_tokens=max_tokens,
        temperature=0.1
    )
    return chat_completion.choices[0].message.content

async def stream_llm(prompt: str, model: str = GROQ_MODEL, max_tokens: int = 1500):
    """Asynchronous streaming generator for returning tokens live."""
    client = get_async_groq_client()
    stream = await client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=model,
        max_tokens=max_tokens,
        temperature=0.2,
        stream=True
    )
    
    async for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            yield chunk.choices[0].delta.content
