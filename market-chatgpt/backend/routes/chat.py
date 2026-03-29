from fastapi import APIRouter
from models.chat import ChatRequest
from agents.orchestrator import run

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("")
async def chat_endpoint(request: ChatRequest):
    """
    Accepts ChatRequest and returns a Server-Sent Events (SSE) stream.
    """
    # Converting Pydantic models to dicts for the orchestration agent
    portfolio_dicts = [h.dict() for h in request.portfolio]
    history_dicts = [m.dict() for m in request.conversation_history]
    
    return await run(
        question=request.question,
        portfolio=portfolio_dicts,
        history=history_dicts
    )
