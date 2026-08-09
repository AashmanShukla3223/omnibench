"""Unit tests for omnibench.telemetry — db, logger, analytics."""

import pytest


class TestTelemetryDB:
    def test_schema_creates_tables(self, tmp_db):
        tables = tmp_db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = {r["name"] for r in tables}
        assert "runs" in table_names
        assert "episodes" in table_names
        assert "steps" in table_names
        assert "screenshot_diffs" in table_names

    def test_connect_idempotent(self, tmp_path):
        from omnibench.telemetry.db import TelemetryDB
        db = TelemetryDB(str(tmp_path / "test.db"))
        db.connect()
        db.connect()  # Should not raise
        db.close()

    def test_context_manager(self, tmp_path):
        from omnibench.telemetry.db import TelemetryDB
        with TelemetryDB(str(tmp_path / "ctx.db")) as db:
            tables = db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            assert len(tables) >= 4

    def test_execute_insert_and_select(self, tmp_db):
        tmp_db.execute(
            "INSERT INTO runs (run_id, domain, model_name, started_at) VALUES (?, ?, ?, ?)",
            ("test-run-1", "osworld", "mock", "2026-01-01T00:00:00"),
        )
        tmp_db.commit()
        row = tmp_db.execute("SELECT * FROM runs WHERE run_id=?", ("test-run-1",)).fetchone()
        assert row is not None
        assert row["domain"] == "osworld"


class TestTelemetryLogger:
    def test_create_run(self, tmp_logger):
        run_id = tmp_logger.create_run(domain="osworld", model_name="mock")
        assert isinstance(run_id, str) and len(run_id) > 0

    def test_list_runs_returns_list(self, tmp_logger):
        tmp_logger.create_run(domain="osworld", model_name="mock")
        runs = tmp_logger.list_runs()
        assert isinstance(runs, list)
        assert len(runs) >= 1

    def test_get_run_summary(self, tmp_logger):
        run_id = tmp_logger.create_run(domain="webarena", model_name="gpt4")
        summary = tmp_logger.get_run_summary(run_id)
        assert summary is not None
        assert summary["run_id"] == run_id
        assert summary["domain"] == "webarena"

    def test_get_run_summary_nonexistent(self, tmp_logger):
        result = tmp_logger.get_run_summary("nonexistent-id")
        assert result is None

    def test_log_episode(self, tmp_logger, episode_result):
        run_id = tmp_logger.create_run(domain="omnibench_native", model_name="mock")
        episode_id = tmp_logger.log_episode(run_id, episode_result)
        assert isinstance(episode_id, str)

    def test_list_episodes(self, tmp_logger, episode_result):
        run_id = tmp_logger.create_run(domain="omnibench_native", model_name="mock")
        tmp_logger.log_episode(run_id, episode_result)
        episodes = tmp_logger.list_episodes(run_id)
        assert len(episodes) == 1
        assert episodes[0]["task_id"] == episode_result.task_id

    def test_finalize_run(self, tmp_logger):
        run_id = tmp_logger.create_run(domain="gaia", model_name="local")
        tmp_logger.finalize_run(run_id, total_tasks=5, passed=4, failed=1, score_avg=0.9)
        summary = tmp_logger.get_run_summary(run_id)
        assert summary["total_tasks"] == 5
        assert summary["passed"] == 4
        assert abs(summary["score_avg"] - 0.9) < 0.001


class TestDiffAnalytics:
    def test_episode_diff_summary_empty(self, tmp_path):
        from omnibench.telemetry.analytics import DiffAnalytics
        from omnibench.telemetry.db import TelemetryDB
        db = TelemetryDB(str(tmp_path / "analytics.db"))
        analytics = DiffAnalytics(db=db)
        result = analytics.episode_diff_summary("nonexistent-episode")
        assert isinstance(result, dict)

    def test_run_diff_summary_empty(self, tmp_path):
        from omnibench.telemetry.analytics import DiffAnalytics
        from omnibench.telemetry.db import TelemetryDB
        db = TelemetryDB(str(tmp_path / "analytics2.db"))
        analytics = DiffAnalytics(db=db)
        result = analytics.run_diff_summary("nonexistent-run")
        assert isinstance(result, list)

    def test_mse_histogram_empty(self, tmp_path):
        from omnibench.telemetry.analytics import DiffAnalytics
        from omnibench.telemetry.db import TelemetryDB
        db = TelemetryDB(str(tmp_path / "analytics3.db"))
        analytics = DiffAnalytics(db=db)
        result = analytics.mse_histogram("nonexistent-run")
        assert "bins" in result
        assert "counts" in result
