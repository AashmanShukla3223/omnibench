"""E2E Tier 4 — Real-World Application Scenario Workloads."""

import pytest
from PIL import Image


class TestWorkload1OSWorldDesktopTask:
    """Full OSWorld desktop task trajectory simulation."""

    def test_osworld_task_full_episode(self, mock_driver, mock_router, tmp_logger):
        from omnibench.benchmarks.adapters.osworld import OSWorldAdapter
        from omnibench.benchmarks.runner import BenchmarkRunner

        tasks = OSWorldAdapter().load_tasks(limit=1)
        task = tasks[0]
        task.max_steps = 3

        runner = BenchmarkRunner(gateway_router=mock_router, driver=mock_driver)
        result = runner.run_episode(task)

        # Log to telemetry
        run_id = tmp_logger.create_run("osworld", "mock")
        tmp_logger.log_episode(run_id, result)

        assert result.domain == "osworld"
        assert result.total_steps >= 0
        assert isinstance(result.score, float)


class TestWorkload2WebArenaFormFilling:
    """WebArena form filling and navigation flow."""

    def test_webarena_task_episode(self, mock_driver, mock_router, tmp_logger):
        from omnibench.benchmarks.adapters.webarena import WebArenaAdapter
        from omnibench.benchmarks.runner import BenchmarkRunner

        tasks = WebArenaAdapter().load_tasks(limit=1)
        task = tasks[0]

        runner = BenchmarkRunner(gateway_router=mock_router, driver=mock_driver)
        result = runner.run_episode(task)

        run_id = tmp_logger.create_run("webarena", "mock")
        tmp_logger.log_episode(run_id, result)

        assert result.domain == "webarena"
        assert result.elapsed_seconds >= 0


class TestWorkload3AndroidWorldNavigation:
    """AndroidWorld app navigation and interaction."""

    def test_androidworld_task_episode(self, tmp_logger):
        from omnibench.benchmarks.adapters.androidworld import AndroidWorldAdapter
        from omnibench.benchmarks.runner import BenchmarkRunner
        from omnibench.drivers.android import AndroidDriver
        from omnibench.gateway.adapters import MockAdapter
        from omnibench.gateway.router import CascadingRouter

        tasks = AndroidWorldAdapter().load_tasks(limit=1)
        task = tasks[0]

        driver = AndroidDriver(mock=True)
        driver.connect()
        router = CascadingRouter(adapters=[MockAdapter()], mock_fallback=True)

        runner = BenchmarkRunner(gateway_router=router, driver=driver)
        result = runner.run_episode(task)

        run_id = tmp_logger.create_run("androidworld", "mock")
        tmp_logger.log_episode(run_id, result)

        assert result.domain == "androidworld"
        driver.disconnect()


class TestWorkload4Mind2WebSearch:
    """Mind2Web web search and data extraction."""

    def test_mind2web_task_episode(self, mock_driver, mock_router, tmp_logger):
        from omnibench.benchmarks.adapters.mind2web import Mind2WebAdapter
        from omnibench.benchmarks.runner import BenchmarkRunner

        tasks = Mind2WebAdapter().load_tasks(limit=1)
        task = tasks[0]

        runner = BenchmarkRunner(gateway_router=mock_router, driver=mock_driver)
        result = runner.run_episode(task)

        run_id = tmp_logger.create_run("mind2web", "mock")
        tmp_logger.log_episode(run_id, result)
        tmp_logger.finalize_run(run_id, 1, int(result.passed), int(not result.passed), result.score)

        summary = tmp_logger.get_run_summary(run_id)
        assert summary["total_tasks"] == 1


class TestWorkload5GAIAMultiStep:
    """GAIA multi-step reasoning with tool execution."""

    def test_gaia_task_episode(self, mock_driver, mock_router, tmp_logger):
        from omnibench.benchmarks.adapters.gaia import GAIAAdapter
        from omnibench.benchmarks.runner import BenchmarkRunner

        tasks = GAIAAdapter().load_tasks(limit=1)
        task = tasks[0]

        runner = BenchmarkRunner(gateway_router=mock_router, driver=mock_driver)
        result = runner.run_episode(task)

        run_id = tmp_logger.create_run("gaia", "mock")
        tmp_logger.log_episode(run_id, result)

        assert result.domain == "gaia"


class TestWorkload6OmniBenchNativeE2E:
    """OmniBench native end-to-end benchmark suite — exercises all system components."""

    def test_all_native_tasks_run(self, mock_driver, mock_router, tmp_logger):
        from omnibench.benchmarks.adapters.omnibench_native import OmniBenchNativeAdapter
        from omnibench.benchmarks.runner import BenchmarkRunner

        tasks = OmniBenchNativeAdapter().load_tasks()
        for t in tasks: t.max_steps = 2
        assert len(tasks) == 5

        runner = BenchmarkRunner(gateway_router=mock_router, driver=mock_driver)
        run_id = tmp_logger.create_run("omnibench_native", "mock")

        results = []
        for task in tasks:
            result = runner.run_episode(task)
            tmp_logger.log_episode(run_id, result)
            results.append(result)

        passed = sum(1 for r in results if r.passed)
        avg_score = sum(r.score for r in results) / len(results)
        tmp_logger.finalize_run(run_id, len(results), passed, len(results) - passed, avg_score)

        summary = tmp_logger.get_run_summary(run_id)
        assert summary["total_tasks"] == 5
        assert isinstance(avg_score, float)

    def test_analytics_after_native_run(self, mock_driver, mock_router, tmp_logger):
        from omnibench.benchmarks.adapters.omnibench_native import OmniBenchNativeAdapter
        from omnibench.benchmarks.runner import BenchmarkRunner
        from omnibench.telemetry.analytics import DiffAnalytics

        tasks = OmniBenchNativeAdapter().load_tasks(limit=2)
        for t in tasks: t.max_steps = 2
        runner = BenchmarkRunner(gateway_router=mock_router, driver=mock_driver)
        run_id = tmp_logger.create_run("omnibench_native_analytics", "mock")

        for task in tasks:
            result = runner.run_episode(task)
            tmp_logger.log_episode(run_id, result)

        analytics = DiffAnalytics(db=tmp_logger._db)
        diff_summary = analytics.run_diff_summary(run_id)
        assert isinstance(diff_summary, list)
