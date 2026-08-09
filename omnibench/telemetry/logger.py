"""
OmniBench Telemetry Logger — writes runs, episodes, and steps to SQLite.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from omnibench.benchmarks.task_schema import EpisodeResult, EpisodeStep
from omnibench.telemetry.db import TelemetryDB


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class TelemetryLogger:
    """Logs benchmark run and episode data to the OmniBench SQLite database."""

    def __init__(self, db: Optional[TelemetryDB] = None, db_path: Optional[str] = None) -> None:
        self._db = db or TelemetryDB(db_path)
        if not hasattr(self._db, '_conn') or self._db._conn is None:
            self._db.connect()

    def create_run(
        self,
        domain: str,
        model_name: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create a new benchmark run record and return its run_id."""
        run_id = str(uuid.uuid4())
        self._db.execute(
            """INSERT INTO runs (run_id, domain, model_name, started_at, metadata)
               VALUES (?, ?, ?, ?, ?)""",
            (run_id, domain, model_name, _now(), json.dumps(metadata or {})),
        )
        self._db.commit()
        return run_id

    def finalize_run(
        self,
        run_id: str,
        total_tasks: int,
        passed: int,
        failed: int,
        score_avg: float,
    ) -> None:
        """Update run record with final statistics."""
        self._db.execute(
            """UPDATE runs SET finished_at=?, total_tasks=?, passed=?, failed=?, score_avg=?
               WHERE run_id=?""",
            (_now(), total_tasks, passed, failed, score_avg, run_id),
        )
        self._db.commit()

    def log_episode(self, run_id: str, result: EpisodeResult) -> str:
        """Log an episode result and all its steps. Returns episode_id."""
        episode_id = str(uuid.uuid4())
        self._db.execute(
            """INSERT INTO episodes
               (episode_id, run_id, task_id, domain, passed, score, total_steps, elapsed_seconds, error, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                episode_id,
                run_id,
                result.task_id,
                result.domain,
                int(result.passed),
                result.score,
                result.total_steps,
                result.elapsed_seconds,
                result.error,
                _now(),
            ),
        )
        # Log steps
        step_rows = []
        diff_rows = []
        for step in result.steps:
            step_id = str(uuid.uuid4())
            step_rows.append((
                step_id,
                episode_id,
                step.step_idx,
                step.action_type,
                json.dumps(step.action_params),
                int(step.action_result_success),
                step.latency_ms,
                step.model_response,
                _now(),
            ))
            # Screenshot diff if available
            diff_meta = step.metadata.get("visual_diff") if hasattr(step, 'metadata') else None
            if diff_meta:
                diff_rows.append((
                    str(uuid.uuid4()),
                    episode_id,
                    step.step_idx,
                    diff_meta.get("mse"),
                    diff_meta.get("ssim"),
                    diff_meta.get("pixel_diff_pct"),
                    diff_meta.get("phash_distance"),
                    _now(),
                ))

        if step_rows:
            self._db.executemany(
                """INSERT INTO steps
                   (step_id, episode_id, step_idx, action_type, action_params,
                    success, latency_ms, model_response, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                step_rows,
            )
        if diff_rows:
            self._db.executemany(
                """INSERT INTO screenshot_diffs
                   (diff_id, episode_id, step_idx, mse, ssim, pixel_diff_pct, phash_distance, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                diff_rows,
            )
        self._db.commit()
        return episode_id

    def get_run_summary(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve run summary dict by run_id."""
        row = self._db.execute(
            "SELECT * FROM runs WHERE run_id=?", (run_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_runs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List recent benchmark runs."""
        rows = self._db.execute(
            "SELECT * FROM runs ORDER BY started_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    def list_episodes(self, run_id: str) -> List[Dict[str, Any]]:
        """List all episodes for a run."""
        rows = self._db.execute(
            "SELECT * FROM episodes WHERE run_id=? ORDER BY created_at", (run_id,)
        ).fetchall()
        return [dict(r) for r in rows]
