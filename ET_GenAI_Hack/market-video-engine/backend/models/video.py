"""Pydantic models for video requests and responses."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class VideoType(str, Enum):
	MARKET_WRAP = "market_wrap"
	SECTOR_ROTATION = "sector_rotation"
	RACE_CHART = "race_chart"
	IPO_TRACKER = "ipo_tracker"
	FULL_OVERVIEW = "full_overview"


class VideoRequest(BaseModel):
	video_type: VideoType = VideoType.FULL_OVERVIEW
	date: str | None = None
	custom_tickers: list[str] = Field(default_factory=list)


class GenerationStage(BaseModel):
	stage: str
	status: str
	started_at: str
	ended_at: str
	duration_ms: float
	details: dict[str, Any] = Field(default_factory=dict)
	error: str | None = None


class VideoStatus(BaseModel):
	status: str
	video_url: str | None = None
	script: str | None = None
	duration_sec: float | None = None
	frame_count: int | None = None
	stages: list[GenerationStage] = Field(default_factory=list)
	error: str | None = None
