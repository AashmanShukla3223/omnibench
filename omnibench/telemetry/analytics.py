"""OmniBench Screenshot Diff Analytics — aggregate statistics from SQLite."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from omnibench.telemetry.db import TelemetryDB


class DiffAnalytics:
    """Computes aggregate screenshot diff analytics from telemetry database."""

    def __init__(self, db: Optional[TelemetryDB] = None, db_path: Optional[str] = None) -> None:
        self._db = db or TelemetryDB(db_path)
        self._db.connect()

    def episode_diff_summary(self, episode_id: str) -> Dict[str, Any]:
        """Return aggregate diff metrics for a single episode."""
        rows = self._db.execute(
            """SELECT AVG(mse) as avg_mse, AVG(ssim) as avg_ssim,
                      AVG(pixel_diff_pct) as avg_pixel_diff,
                      AVG(phash_distance) as avg_phash
               FROM screenshot_diffs WHERE episode_id=?""",
            (episode_id,),
        ).fetchone()
        return dict(rows) if rows else {}

    def run_diff_summary(self, run_id: str) -> List[Dict[str, Any]]:
        """Return per-episode diff summaries for all episodes in a run."""
        rows = self._db.execute(
            """SELECT e.episode_id, e.task_id,
                      AVG(d.mse) as avg_mse, AVG(d.ssim) as avg_ssim,
                      AVG(d.pixel_diff_pct) as avg_pixel_diff
               FROM episodes e
               LEFT JOIN screenshot_diffs d ON e.episode_id = d.episode_id
               WHERE e.run_id = ?
               GROUP BY e.episode_id""",
            (run_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def mse_histogram(self, run_id: str, bins: int = 10) -> Dict[str, Any]:
        """Compute MSE value histogram across all steps of a run."""
        rows = self._db.execute(
            """SELECT d.mse FROM screenshot_diffs d
               JOIN episodes e ON d.episode_id = e.episode_id
               WHERE e.run_id=? AND d.mse IS NOT NULL""",
            (run_id,),
        ).fetchall()
        values = [r["mse"] for r in rows]
        if not values:
            return {"bins": [], "counts": []}
        min_v, max_v = min(values), max(values)
        bin_width = (max_v - min_v) / bins if max_v > min_v else 1.0
        counts = [0] * bins
        bin_edges = [min_v + i * bin_width for i in range(bins + 1)]
        for v in values:
            idx = min(int((v - min_v) / bin_width), bins - 1)
            counts[idx] += 1
        return {"bins": bin_edges, "counts": counts}
