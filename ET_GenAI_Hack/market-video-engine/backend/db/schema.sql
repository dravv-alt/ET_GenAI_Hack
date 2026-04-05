-- SQLite schema for rendered videos and scripts

CREATE TABLE IF NOT EXISTS video_runs (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	video_type TEXT NOT NULL,
	status TEXT NOT NULL,
	filename TEXT,
	video_path TEXT,
	script TEXT,
	duration_sec REAL,
	frame_count INTEGER,
	stages_json TEXT,
	error TEXT,
	created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_video_runs_created_at ON video_runs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_video_runs_status ON video_runs(status);
