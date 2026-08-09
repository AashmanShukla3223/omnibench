"""
OmniBench SQLite Telemetry Database — Schema DDL and connection manager.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional


SCHEMA_DDL = """
CREATE TABLE IF NOT EXISTS runs (
    run_id      TEXT PRIMARY KEY,
    domain      TEXT NOT NULL,
    model_name  TEXT NOT NULL,
    started_at  TEXT NOT NULL,
    finished_at TEXT,
    total_tasks INTEGER DEFAULT 0,
    passed      INTEGER DEFAULT 0,
    failed      INTEGER DEFAULT 0,
    score_avg   REAL DEFAULT 0.0,
    metadata    TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS episodes (
    episode_id      TEXT PRIMARY KEY,
    run_id          TEXT NOT NULL REFERENCES runs(run_id),
    task_id         TEXT NOT NULL,
    domain          TEXT NOT NULL,
    passed          INTEGER NOT NULL,
    score           REAL NOT NULL,
    total_steps     INTEGER NOT NULL,
    elapsed_seconds REAL NOT NULL,
    error           TEXT,
    created_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS steps (
    step_id         TEXT PRIMARY KEY,
    episode_id      TEXT NOT NULL REFERENCES episodes(episode_id),
    step_idx        INTEGER NOT NULL,
    action_type     TEXT NOT NULL,
    action_params   TEXT NOT NULL,
    success         INTEGER NOT NULL,
    latency_ms      REAL NOT NULL,
    model_response  TEXT,
    created_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS screenshot_diffs (
    diff_id         TEXT PRIMARY KEY,
    episode_id      TEXT NOT NULL REFERENCES episodes(episode_id),
    step_idx        INTEGER NOT NULL,
    mse             REAL,
    ssim            REAL,
    pixel_diff_pct  REAL,
    phash_distance  INTEGER,
    created_at      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_episodes_run_id ON episodes(run_id);
CREATE INDEX IF NOT EXISTS idx_steps_episode_id ON steps(episode_id);
"""


class TelemetryDB:
    """SQLite database manager for OmniBench telemetry."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path or "omnibench_telemetry.db"
        self._conn: Optional[sqlite3.Connection] = None

    def connect(self) -> None:
        """Open SQLite connection and initialize schema."""
        path = Path(self.db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.executescript(SCHEMA_DDL)
        self._conn.commit()

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self.connect()
        return self._conn

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        return self.conn.execute(sql, params)

    def executemany(self, sql: str, params_list: list) -> sqlite3.Cursor:
        return self.conn.executemany(sql, params_list)

    def commit(self) -> None:
        self.conn.commit()

    def __enter__(self) -> "TelemetryDB":
        self.connect()
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
