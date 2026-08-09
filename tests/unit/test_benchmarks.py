"""Unit tests for omnibench.benchmarks — task_schema, adapters, runner."""

import pytest


class TestBenchmarkTask:
    def test_basic_construction(self, native_task):
        assert native_task.task_id == "test_task_001"
        assert native_task.max_steps == 2

    def test_to_dict(self, native_task):
        d = native_task.to_dict()
        assert d["task_id"] == native_task.task_id
        assert d["instruction"] == native_task.instruction
        assert "domain" in d

    def test_from_dict_roundtrip(self, native_task):
        from omnibench.benchmarks.task_schema import BenchmarkTask
        d = native_task.to_dict()
        restored = BenchmarkTask.from_dict(d)
        assert restored.task_id == native_task.task_id
        assert restored.instruction == native_task.instruction


class TestTaskAdapters:
    def test_osworld_loads_synthetic(self):
        from omnibench.benchmarks.adapters.osworld import OSWorldAdapter
        adapter = OSWorldAdapter()
        tasks = adapter.load_tasks()
        assert len(tasks) >= 1
        assert tasks[0].task_id is not None

    def test_webarena_loads_tasks(self):
        from omnibench.benchmarks.adapters.webarena import WebArenaAdapter
        adapter = WebArenaAdapter()
        tasks = adapter.load_tasks()
        assert len(tasks) >= 1

    def test_androidworld_loads_tasks(self):
        from omnibench.benchmarks.adapters.androidworld import AndroidWorldAdapter
        adapter = AndroidWorldAdapter()
        tasks = adapter.load_tasks()
        assert len(tasks) >= 1
        assert tasks[0].platform == "android"

    def test_mind2web_loads_tasks(self):
        from omnibench.benchmarks.adapters.mind2web import Mind2WebAdapter
        adapter = Mind2WebAdapter()
        tasks = adapter.load_tasks()
        assert len(tasks) >= 1

    def test_gaia_loads_tasks(self):
        from omnibench.benchmarks.adapters.gaia import GAIAAdapter
        adapter = GAIAAdapter()
        tasks = adapter.load_tasks()
        assert len(tasks) >= 1

    def test_omnibench_native_loads_tasks(self):
        from omnibench.benchmarks.adapters.omnibench_native import OmniBenchNativeAdapter
        adapter = OmniBenchNativeAdapter()
        tasks = adapter.load_tasks()
        assert len(tasks) == 5

    def test_limit_parameter(self):
        from omnibench.benchmarks.adapters.omnibench_native import OmniBenchNativeAdapter
        adapter = OmniBenchNativeAdapter()
        tasks = adapter.load_tasks(limit=2)
        assert len(tasks) == 2

    def test_all_domains_return_task_domain(self):
        from omnibench.benchmarks.task_schema import TaskDomain
        from omnibench.benchmarks.adapters.osworld import OSWorldAdapter
        tasks = OSWorldAdapter().load_tasks()
        assert tasks[0].domain == TaskDomain.OSWORLD


class TestBenchmarkRunner:
    def test_run_episode_returns_result(self, mock_driver, mock_router, native_task):
        from omnibench.benchmarks.runner import BenchmarkRunner
        from omnibench.benchmarks.task_schema import EpisodeResult
        runner = BenchmarkRunner(gateway_router=mock_router, driver=mock_driver)
        result = runner.run_episode(native_task)
        assert isinstance(result, EpisodeResult)
        assert result.task_id == native_task.task_id
        assert isinstance(result.passed, bool)
        assert isinstance(result.score, float)
        assert result.total_steps >= 0

    def test_episode_result_has_steps(self, mock_driver, mock_router, native_task):
        from omnibench.benchmarks.runner import BenchmarkRunner
        runner = BenchmarkRunner(gateway_router=mock_router, driver=mock_driver)
        result = runner.run_episode(native_task)
        assert isinstance(result.steps, list)

    def test_episode_elapsed_positive(self, mock_driver, mock_router, native_task):
        from omnibench.benchmarks.runner import BenchmarkRunner
        runner = BenchmarkRunner(gateway_router=mock_router, driver=mock_driver)
        result = runner.run_episode(native_task)
        assert result.elapsed_seconds >= 0
