"""SQLite helper for cached renders and scripts."""

from __future__ import annotations

import json
import os
import sqlite3
import tempfile
import time
from pathlib import Path
from typing import Any


DB_DIR = Path(__file__).resolve().parent
DB_PATH = DB_DIR / "video_engine.db"
SCHEMA_PATH = DB_DIR / "schema.sql"
DATA_DIR = DB_DIR.parent / "data"
CLEANUP_POLICY_PATH = DATA_DIR / "cleanup_policy.json"


def get_conn() -> sqlite3.Connection:
	"""Returns a sqlite connection with row factory enabled."""
	conn = sqlite3.connect(DB_PATH)
	conn.row_factory = sqlite3.Row
	return conn


def _load_cleanup_policy() -> dict[str, Any]:
	default_policy = {
		"enabled": True,
		"run_on_generate": True,
		"db_retention_days": 7,
		"db_max_records": 200,
		"temp_file_retention_hours": 24,
		"temp_file_prefix": "mve_",
		"output_dir": "./output",
	}
	if not CLEANUP_POLICY_PATH.exists():
		return default_policy

	try:
		with CLEANUP_POLICY_PATH.open("r", encoding="utf-8") as fp:
			loaded = json.load(fp)
		if not isinstance(loaded, dict):
			return default_policy
		return {**default_policy, **loaded}
	except Exception:
		return default_policy


def init_schema() -> None:
	"""Initializes sqlite schema if it does not already exist."""
	if not SCHEMA_PATH.exists():
		raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")

	with get_conn() as conn:
		schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
		conn.executescript(schema_sql)
		conn.commit()


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
	stages_raw = row["stages_json"] or "[]"
	try:
		stages = json.loads(stages_raw)
	except json.JSONDecodeError:
		stages = []

	return {
		"id": row["id"],
		"video_type": row["video_type"],
		"status": row["status"],
		"filename": row["filename"],
		"video_path": row["video_path"],
		"script": row["script"],
		"duration_sec": row["duration_sec"],
		"frame_count": row["frame_count"],
		"stages": stages,
		"error": row["error"],
		"created_at": row["created_at"],
	}


def create_video_run(payload: dict[str, Any]) -> int:
	"""Persists one video generation run and returns inserted row id."""
	init_schema()
	stages = payload.get("stages", [])
	stages_json = json.dumps(stages, ensure_ascii=True)

	with get_conn() as conn:
		cursor = conn.execute(
			"""
			INSERT INTO video_runs (
				video_type,
				status,
				filename,
				video_path,
				script,
				duration_sec,
				frame_count,
				stages_json,
				error
			)
			VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
			""",
			(
				payload.get("video_type"),
				payload.get("status"),
				payload.get("filename"),
				payload.get("video_path"),
				payload.get("script"),
				payload.get("duration_sec"),
				payload.get("frame_count"),
				stages_json,
				payload.get("error"),
			),
		)
		conn.commit()
		return int(cursor.lastrowid)


def list_video_runs(limit: int = 20) -> list[dict[str, Any]]:
	"""Returns recent video generation runs sorted by newest first."""
	init_schema()
	safe_limit = max(1, min(limit, 100))
	with get_conn() as conn:
		rows = conn.execute(
			"""
			SELECT
				id,
				video_type,
				status,
				filename,
				video_path,
				script,
				duration_sec,
				frame_count,
				stages_json,
				error,
				created_at
			FROM video_runs
			ORDER BY id DESC
			LIMIT ?
			""",
			(safe_limit,),
		).fetchall()

	results: list[dict[str, Any]] = []
	for row in rows:
		results.append(_row_to_dict(row))

	return results


def get_video_run(run_id: int) -> dict[str, Any] | None:
	"""Returns one generation run by id, or None when missing."""
	init_schema()
	with get_conn() as conn:
		row = conn.execute(
			"""
			SELECT
				id,
				video_type,
				status,
				filename,
				video_path,
				script,
				duration_sec,
				frame_count,
				stages_json,
				error,
				created_at
			FROM video_runs
			WHERE id = ?
			""",
			(run_id,),
		).fetchone()

	if not row:
		return None
	return _row_to_dict(row)


def cleanup_video_artifacts(trigger: str = "manual") -> dict[str, Any]:
	"""Applies cleanup policy to stale DB runs and temporary MP4 files."""
	init_schema()
	policy = _load_cleanup_policy()

	if not bool(policy.get("enabled", True)):
		return {"status": "skipped", "reason": "disabled", "deleted_db_rows": 0, "deleted_files": 0}

	if trigger == "on_generate" and not bool(policy.get("run_on_generate", True)):
		return {"status": "skipped", "reason": "run_on_generate_disabled", "deleted_db_rows": 0, "deleted_files": 0}

	db_retention_days = max(int(policy.get("db_retention_days", 7)), 0)
	db_max_records = max(int(policy.get("db_max_records", 200)), 1)
	file_retention_hours = max(int(policy.get("temp_file_retention_hours", 24)), 0)
	file_prefix = str(policy.get("temp_file_prefix", "mve_")).strip() or "mve_"

	rows_to_delete: dict[int, str | None] = {}

	with get_conn() as conn:
		if db_retention_days > 0:
			older_rows = conn.execute(
				"""
				SELECT id, video_path
				FROM video_runs
				WHERE created_at < datetime('now', ?)
				""",
				(f"-{db_retention_days} days",),
			).fetchall()
			for row in older_rows:
				rows_to_delete[int(row["id"])] = row["video_path"]

		offset_rows = conn.execute(
			"""
			SELECT id, video_path
			FROM video_runs
			ORDER BY id DESC
			LIMIT -1 OFFSET ?
			""",
			(db_max_records,),
		).fetchall()
		for row in offset_rows:
			rows_to_delete[int(row["id"])] = row["video_path"]

		deleted_files = 0
		for _, maybe_path in rows_to_delete.items():
			if not maybe_path:
				continue
			if os.path.exists(maybe_path):
				try:
					os.remove(maybe_path)
					deleted_files += 1
				except OSError:
					pass

		if rows_to_delete:
			placeholders = ",".join(["?"] * len(rows_to_delete))
			conn.execute(f"DELETE FROM video_runs WHERE id IN ({placeholders})", tuple(rows_to_delete.keys()))
			conn.commit()

	configured_output_dir = str(policy.get("output_dir", "")).strip()
	temp_dir = configured_output_dir or tempfile.gettempdir()
	Path(temp_dir).mkdir(parents=True, exist_ok=True)
	now_ts = time.time()
	max_age_sec = file_retention_hours * 3600
	for file_path in Path(temp_dir).glob(f"{file_prefix}*.mp4"):
		try:
			file_age = now_ts - file_path.stat().st_mtime
			if max_age_sec == 0 or file_age >= max_age_sec:
				file_path.unlink(missing_ok=True)
				deleted_files += 1
		except OSError:
			continue

	return {
		"status": "completed",
		"deleted_db_rows": len(rows_to_delete),
		"deleted_files": deleted_files,
		"policy": {
			"db_retention_days": db_retention_days,
			"db_max_records": db_max_records,
			"temp_file_retention_hours": file_retention_hours,
			"temp_file_prefix": file_prefix,
		},
	}
