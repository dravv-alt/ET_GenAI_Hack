"""Orchestrates combined market video generation pipeline."""

from __future__ import annotations

import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from generators.ipo_tracker import generate_ipo_tracker_frames, generate_outro_frames
from generators.market_wrap import (
	generate_gainers_frames,
	generate_losers_frames,
	generate_market_overview_frames,
)
from generators.race_chart import generate_race_chart_frames
from generators.sector_rotation import generate_fii_dii_frames, generate_sector_rotation_frames
from rendering.video_assembler import assemble_video
from services.market_data import get_market_snapshot
from services.script_generator import generate_combined_script
from services.tts_client import generate_audio


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _load_runtime_config() -> dict[str, Any]:
	config_path = DATA_DIR / "runtime_config.json"
	with config_path.open("r", encoding="utf-8") as config_file:
		return json.load(config_file)


def _now_iso() -> str:
	return datetime.now(UTC).isoformat()


def _stage_record(name: str, status: str, started_at: str, start_perf: float, details: dict[str, Any] | None = None, error: str | None = None) -> dict[str, Any]:
	return {
		"stage": name,
		"status": status,
		"started_at": started_at,
		"ended_at": _now_iso(),
		"duration_ms": round((time.perf_counter() - start_perf) * 1000, 2),
		"details": details or {},
		"error": error,
	}


async def generate_video(
	video_type: str,
	output_path: str,
	custom_tickers: list[str] | None = None,
) -> dict[str, Any]:
	"""Generates one combined narrative market video.

	The `video_type` parameter is accepted for request compatibility.
	Generation currently returns the full overview timeline.
	"""
	_ = video_type
	config = _load_runtime_config()
	segment_frames = dict(config.get("segment_frames", {}))
	fps = int(config.get("fps", 15))
	frame_repeat = max(int(config.get("frame_repeat", 1)), 1)
	stages: list[dict[str, Any]] = []

	snapshot: dict[str, Any] = {}
	frames: list[bytes] = []
	script = ""
	audio_path: str | None = None

	try:
		stage_started = _now_iso()
		stage_perf = time.perf_counter()
		snapshot = get_market_snapshot(top_n=5, custom_tickers=custom_tickers)
		stages.append(
			_stage_record(
				"fetch_market_data",
				"completed",
				stage_started,
				stage_perf,
				details={
					"snapshot_keys": sorted(snapshot.keys()),
					"top_gainers": len(dict(snapshot.get("movers", {})).get("gainers", [])),
					"top_losers": len(dict(snapshot.get("movers", {})).get("losers", [])),
					"sectors": len(snapshot.get("sectors", [])),
				},
			)
		)

		stage_started = _now_iso()
		stage_perf = time.perf_counter()
		segment_counts: dict[str, int] = {}

		segment = generate_market_overview_frames(snapshot, int(segment_frames.get("market_overview", 16)))
		segment_counts["market_overview"] = len(segment)
		frames.extend(segment)

		segment = generate_gainers_frames(snapshot, int(segment_frames.get("gainers", 10)))
		segment_counts["gainers"] = len(segment)
		frames.extend(segment)

		segment = generate_losers_frames(snapshot, int(segment_frames.get("losers", 10)))
		segment_counts["losers"] = len(segment)
		frames.extend(segment)

		segment = generate_sector_rotation_frames(snapshot, int(segment_frames.get("sector_rotation", 10)))
		segment_counts["sector_rotation"] = len(segment)
		frames.extend(segment)

		segment = generate_race_chart_frames(snapshot, int(segment_frames.get("race_chart", 10)))
		segment_counts["race_chart"] = len(segment)
		frames.extend(segment)

		segment = generate_fii_dii_frames(snapshot, int(segment_frames.get("fii_dii", 8)))
		segment_counts["fii_dii"] = len(segment)
		frames.extend(segment)

		segment = generate_ipo_tracker_frames(snapshot, int(segment_frames.get("ipo_tracker", 8)))
		segment_counts["ipo_tracker"] = len(segment)
		frames.extend(segment)

		segment = generate_outro_frames(snapshot, int(segment_frames.get("outro", 6)))
		segment_counts["outro"] = len(segment)
		frames.extend(segment)

		if frame_repeat > 1:
			repeated_frames: list[bytes] = []
			for frame in frames:
				repeated_frames.extend([frame] * frame_repeat)
			frames = repeated_frames

		stages.append(
			_stage_record(
				"render_frames",
				"completed",
				stage_started,
				stage_perf,
				details={
					"segments": segment_counts,
					"frame_repeat": frame_repeat,
					"total_frames": len(frames),
				},
			)
		)

		stage_started = _now_iso()
		stage_perf = time.perf_counter()
		script = generate_combined_script(snapshot)
		stages.append(
			_stage_record(
				"generate_script",
				"completed",
				stage_started,
				stage_perf,
				details={"word_count": len(script.split())},
			)
		)

		stage_started = _now_iso()
		stage_perf = time.perf_counter()
		audio_path = generate_audio(script)
		stages.append(
			_stage_record(
				"generate_audio",
				"completed",
				stage_started,
				stage_perf,
				details={"audio_generated": bool(audio_path)},
			)
		)

		stage_started = _now_iso()
		stage_perf = time.perf_counter()
		assemble_video(
			frame_bytes_list=frames,
			output_path=output_path,
			fps=fps,
			audio_path=audio_path,
		)
		output_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
		stages.append(
			_stage_record(
				"assemble_video",
				"completed",
				stage_started,
				stage_perf,
				details={"fps": fps, "output_size_bytes": output_size},
			)
		)

		duration_sec = round(len(frames) / max(fps, 1), 2)
		return {
			"status": "complete",
			"script": script,
			"duration_sec": duration_sec,
			"frame_count": len(frames),
			"stages": stages,
			"scope": snapshot.get("scope", {}),
		}
	except Exception as exc:
		stages.append(
			{
				"stage": "pipeline_error",
				"status": "failed",
				"started_at": _now_iso(),
				"ended_at": _now_iso(),
				"duration_ms": 0,
				"details": {},
				"error": str(exc),
			}
		)
		return {
			"status": "error",
			"error": str(exc),
			"script": script,
			"duration_sec": None,
			"frame_count": len(frames),
			"stages": stages,
			"scope": snapshot.get("scope", {}),
		}
	finally:
		if audio_path and os.path.exists(audio_path):
			try:
				os.remove(audio_path)
			except OSError:
				pass
