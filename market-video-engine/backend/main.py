"""Market Video Engine FastAPI entrypoint (port 8004)."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db.db import init_schema
from routes.video import router as video_router


app = FastAPI(title="AI Market Video Engine", version="0.1.0")

app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup() -> None:
	init_schema()


@app.get("/health")
async def health() -> dict[str, str]:
	return {"status": "ok"}


app.include_router(video_router)
