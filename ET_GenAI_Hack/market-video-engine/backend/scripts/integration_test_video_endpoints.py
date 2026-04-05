"""Endpoint-level integration test script for video generate and download."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from main import app


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run() -> None:
    with TestClient(app) as client:

        health = client.get("/health")
        _assert(health.status_code == 200, f"Health check failed: {health.status_code}")
        _assert(health.json().get("status") == "ok", "Unexpected health response")

        custom_tickers = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS"]
        preview_payload: dict[str, Any] = {"video_type": "full_overview", "custom_tickers": custom_tickers}
        preview_res = client.post("/video/preview-script", json=preview_payload)
        _assert(preview_res.status_code == 200, f"Preview failed: {preview_res.status_code}")
        preview_json = preview_res.json()
        _assert(preview_json.get("status") == "complete", "Preview status is not complete")
        _assert(isinstance(preview_json.get("script"), str) and len(preview_json.get("script")) > 0, "Preview script missing")
        _assert(isinstance(preview_json.get("stages"), list), "Preview stages missing")
        _assert(bool(preview_json.get("scope", {}).get("is_custom_scope")), "Preview custom scope not applied")

        payload: dict[str, Any] = {"video_type": "full_overview", "custom_tickers": custom_tickers}
        generate_res = client.post("/video/generate", json=payload)
        _assert(generate_res.status_code == 200, f"Generate failed: {generate_res.status_code}")

        generate_json = generate_res.json()
        _assert(generate_json.get("status") == "complete", "Generation status is not complete")
        _assert(isinstance(generate_json.get("run_id"), int), "Missing run_id in generation response")
        _assert(bool(generate_json.get("video_url")), "Missing video_url in response")
        _assert(isinstance(generate_json.get("stages"), list), "Missing stages list in response")
        _assert(bool(generate_json.get("scope", {}).get("is_custom_scope")), "Generate custom scope not applied")

        download_url = str(generate_json["video_url"])
        download_res = client.get(download_url)
        _assert(download_res.status_code == 200, f"Download failed: {download_res.status_code}")

        content_type = download_res.headers.get("content-type", "")
        _assert("video/mp4" in content_type, f"Unexpected content-type: {content_type}")
        _assert(len(download_res.content) > 0, "Downloaded video is empty")

        history_res = client.get("/video/history?limit=5")
        _assert(history_res.status_code == 200, f"History failed: {history_res.status_code}")
        history_json = history_res.json()
        _assert(isinstance(history_json.get("items"), list), "History items missing")
        _assert(any(item.get("id") == generate_json.get("run_id") for item in history_json.get("items", [])), "Generated run missing in history")

        run_id = int(generate_json.get("run_id"))
        run_detail_res = client.get(f"/video/run/{run_id}")
        _assert(run_detail_res.status_code == 200, f"Run detail failed: {run_detail_res.status_code}")
        run_detail_json = run_detail_res.json()
        _assert(isinstance(run_detail_json.get("item"), dict), "Run detail missing item")
        _assert(isinstance(run_detail_json.get("replay"), dict), "Run detail missing replay metadata")
        _assert(run_detail_json.get("item", {}).get("id") == run_id, "Run detail id mismatch")

        cleanup_res = client.post("/video/cleanup")
        _assert(cleanup_res.status_code == 200, f"Cleanup failed: {cleanup_res.status_code}")
        cleanup_json = cleanup_res.json()
        _assert(cleanup_json.get("status") in {"completed", "skipped"}, "Unexpected cleanup status")

        print("Integration test passed")
        print(f"preview_script_words: {len(str(preview_json.get('script', '')).split())}")
        print(f"video_url: {download_url}")
        print(f"duration_sec: {generate_json.get('duration_sec')}")
        print(f"frame_count: {generate_json.get('frame_count')}")
        print(f"stage_count: {len(generate_json.get('stages', []))}")
        print(f"history_count: {history_json.get('count')}")
        print(f"run_id: {run_id}")
        print(f"cleanup_status: {cleanup_json.get('status')}")


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:  # pragma: no cover
        print(f"Integration test failed: {exc}")
        sys.exit(1)
