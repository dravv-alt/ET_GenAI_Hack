"""LLM explanation API."""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from services.llm_explainer import generate_explanation

router = APIRouter()


class ExplainRequest(BaseModel):
	pattern: Dict[str, Any]
	backtest: Optional[Dict[str, Any]] = None
	market: Optional[str] = None


@router.post("/explain")
def explain(payload: ExplainRequest) -> dict:
	result = generate_explanation(payload.pattern, payload.backtest, payload.market)
	return {"explanation": result["text"], "source": result["source"]}
