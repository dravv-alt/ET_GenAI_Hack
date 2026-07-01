"""Video generation API: kicks off render and returns a download URL."""

from __future__ import annotations

import json
import os
import tempfile
import time
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from db.db import cleanup_video_artifacts, create_video_run, get_video_run, list_video_runs
from generators.orchestrator import generate_video
from models.video import VideoRequest
from services.market_data import get_market_snapshot
from services.script_generator import generate_combined_script


router = APIRouter(prefix="/video", tags=["video"])
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _load_cleanup_policy() -> dict[str, object]:
	policy_path = DATA_DIR / "cleanup_policy.json"
	if not policy_path.exists():
		return {
			"temp_file_prefix": "mve_",
			"output_dir": "./output",
		}
	try:
		with policy_path.open("r", encoding="utf-8") as fp:
			loaded = json.load(fp)
		if isinstance(loaded, dict):
			return loaded
	except Exception:
		pass
	return {
		"temp_file_prefix": "mve_",
		"output_dir": "./output",
	}


def _resolve_output_dir(policy: dict[str, object]) -> Path:
	configured = str(policy.get("output_dir", "")).strip()
	output_dir = Path(configured) if configured else Path(tempfile.gettempdir())
	output_dir.mkdir(parents=True, exist_ok=True)
	return output_dir


@router.post("/generate")
async def generate_market_video(request: VideoRequest) -> dict[str, object]:
	"""Generates the combined narrative market video."""
	cleanup_policy = _load_cleanup_policy()
	output_dir = _resolve_output_dir(cleanup_policy)
	prefix = str(cleanup_policy.get("temp_file_prefix", "mve_") or "mve_")
	timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
	filename = f"{prefix}{timestamp}_{uuid4().hex[:8]}.mp4"
	output_path = str(output_dir / filename)

	result = await generate_video(
		video_type=request.video_type.value,
		output_path=output_path,
		custom_tickers=request.custom_tickers,
	)
	status = str(result.get("status", "complete"))
	record_payload = {
		"video_type": request.video_type.value,
		"status": status,
		"filename": filename,
		"video_path": output_path,
		"script": result.get("script", ""),
		"duration_sec": result.get("duration_sec"),
		"frame_count": result.get("frame_count", 0),
		"stages": result.get("stages", []),
		"error": result.get("error"),
	}
	run_id = create_video_run(record_payload)
	cleanup_result = cleanup_video_artifacts(trigger="on_generate")

	if status != "complete":
		return {
			"status": "error",
			"run_id": run_id,
			"video_url": None,
			"script": result.get("script", ""),
			"duration_sec": result.get("duration_sec"),
			"frame_count": result.get("frame_count", 0),
			"error": result.get("error", "Video generation failed"),
			"stages": result.get("stages", []),
			"scope": result.get("scope", {}),
			"cleanup": cleanup_result,
		}

	return {
		"status": status,
		"run_id": run_id,
		"video_url": f"/video/download/{filename}",
		"script": result.get("script", ""),
		"duration_sec": result.get("duration_sec", 0),
		"frame_count": result.get("frame_count", 0),
		"stages": result.get("stages", []),
		"scope": result.get("scope", {}),
		"cleanup": cleanup_result,
	}


@router.post("/preview-script")
async def preview_market_script(request: VideoRequest) -> dict[str, object]:
	"""Generates script-only preview for the selected video type."""
	_ = request
	stages: list[dict[str, object]] = []

	fetch_started = time.perf_counter()
	snapshot = get_market_snapshot(top_n=5, custom_tickers=request.custom_tickers)
	stages.append(
		{
			"stage": "fetch_market_data",
			"status": "completed",
			"duration_ms": round((time.perf_counter() - fetch_started) * 1000, 2),
		}
	)

	script_started = time.perf_counter()
	script = generate_combined_script(snapshot)
	stages.append(
		{
			"stage": "generate_script",
			"status": "completed",
			"duration_ms": round((time.perf_counter() - script_started) * 1000, 2),
			"details": {"word_count": len(script.split())},
		}
	)

	nifty = dict(snapshot.get("nifty", {}))
	movers = dict(snapshot.get("movers", {}))
	sectors = list(snapshot.get("sectors", []))

	return {
		"status": "complete",
		"script": script,
		"stages": stages,
		"scope": snapshot.get("scope", {}),
		"summary": {
			"nifty_close": nifty.get("close"),
			"nifty_change_pct": nifty.get("change_pct"),
			"top_gainer": (movers.get("gainers") or [{}])[0].get("ticker"),
			"top_loser": (movers.get("losers") or [{}])[0].get("ticker"),
			"top_sector": (sectors or [{}])[0].get("sector"),
		},
	}


@router.get("/download/{filename}")
async def download_video(filename: str) -> FileResponse:
	"""Downloads generated MP4 from configured output directory."""
	cleanup_policy = _load_cleanup_policy()
	output_dir = _resolve_output_dir(cleanup_policy)
	path = str(output_dir / filename)
	if not os.path.exists(path):
		fallback = os.path.join(tempfile.gettempdir(), filename)
		if os.path.exists(fallback):
			path = fallback
	if not os.path.exists(path):
		raise HTTPException(status_code=404, detail="Video not found")
	return FileResponse(path, media_type="video/mp4", filename="market-update.mp4")


@router.get("/history")
async def video_history(limit: int = 20) -> dict[str, object]:
	"""Returns recent generation runs from sqlite."""
	rows = list_video_runs(limit=limit)
	return {"count": len(rows), "items": rows}


@router.get("/run/{run_id}")
async def video_run_detail(run_id: int) -> dict[str, object]:
	"""Returns one run with replay metadata."""
	run = get_video_run(run_id)
	if not run:
		raise HTTPException(status_code=404, detail="Run not found")

	video_path = str(run.get("video_path") or "")
	filename = str(run.get("filename") or "")
	file_exists = bool(video_path and os.path.exists(video_path))
	file_size = os.path.getsize(video_path) if file_exists else 0
	last_modified = os.path.getmtime(video_path) if file_exists else None

	replay = {
		"download_url": f"/video/download/{filename}" if filename and file_exists else None,
		"can_replay": file_exists,
		"file_exists": file_exists,
		"file_size_bytes": file_size,
		"last_modified_epoch": last_modified,
	}

	return {"item": run, "replay": replay}


@router.post("/cleanup")
async def video_cleanup() -> dict[str, object]:
	"""Runs cleanup policy manually."""
	result = cleanup_video_artifacts(trigger="manual")
	return result
