from pydantic import BaseModel
from enum import Enum

class SSEEventType(str, Enum):
    THINKING = "thinking"
    TOKEN = "token"
    SIGNAL_CARD = "signal_card"
    SOURCE = "source"
    DONE = "done"
    ERROR = "error"

class SSEEvent(BaseModel):
    type: SSEEventType
    content: str | dict | None = None
    url: str | None = None
    title: str | None = None

class Message(BaseModel):
    role: str           # "user" or "assistant"
    content: str

class Holding(BaseModel):
    ticker: str         # must end in .NS
    quantity: int
    avg_buy_price: float

class MarketData(BaseModel):
    ticker: str
    current_price: float
    pnl_abs: float
    pnl_pct: float
    volume: int | None = None

class ChatRequest(BaseModel):
    question: str
    portfolio: list[Holding] = [] # Optional fallback
    market_context: list[MarketData] = []
    conversation_history: list[Message] = []
