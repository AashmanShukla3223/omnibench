"""E2E Tier 3 — Pairwise Feature Combination Tests."""

import pytest
from PIL import Image


class TestEngineGatewayIntegration:
    """Engine × Gateway interactions."""

    def test_local_onnx_adapter_uses_engine(self, blank_image, image_bytes):
        from omnibench.gateway.adapters import LocalONNXAdapter
        from omnibench.gateway.protocol import GatewayRequest
        adapter = LocalONNXAdapter()
        req = GatewayRequest(prompt="describe screen", images=[image_bytes])
        resp = adapter.generate(req)
        assert resp.text is not None

    def test_cascading_router_falls_to_local(self):
        from omnibench.gateway.router import CascadingRouter
        from omnibench.gateway.adapters import MockAdapter
        from omnibench.gateway.protocol import GatewayRequest

        class FailAdapter(MockAdapter):
            name = "fail"
            def is_available(self): return False

        router = CascadingRouter(adapters=[FailAdapter()], mock_fallback=True)
        resp = router.route(GatewayRequest(prompt="fallback test"))
        assert resp.success is True


class TestDriverVisualIntegration:
    """Driver × Visual pipeline interactions."""

    def test_driver_screenshot_through_visual_pipeline(self, mock_driver):
        from omnibench.visual.processing import ImageResizer, ColorConverter
        img = mock_driver.capture_screenshot()
        resizer = ImageResizer()
        cc = ColorConverter()
        resized = resizer.resize(img, (224, 224))
        gray = cc.to_grayscale(resized)
        assert gray is not None

    def test_driver_screenshot_through_som(self, mock_driver):
        from omnibench.visual.som import SoMAnnotator
        img = mock_driver.capture_screenshot()
        annotator = SoMAnnotator()
        annotated, mark_map = annotator.annotate(img)
        assert isinstance(annotated, Image.Image)

    def test_driver_screenshot_into_memory(self, mock_driver):
        from omnibench.visual.memory import SlidingTrajectoryMemory
        mem = SlidingTrajectoryMemory(max_screenshots=3)
        img = mock_driver.capture_screenshot()
        mem.add_step(img, "click(100,200)")
        state = mem.get_state()
        assert len(state.screenshots) == 1


class TestEvaluatorTelemetryIntegration:
    """Evaluator × Telemetry interactions."""

    def test_evaluation_result_logged(self, tmp_logger, blank_image, episode_result):
        run_id = tmp_logger.create_run("integration", "mock")
        ep_id = tmp_logger.log_episode(run_id, episode_result)
        eps = tmp_logger.list_episodes(run_id)
        assert len(eps) == 1
        assert eps[0]["score"] == episode_result.score

    def test_visual_diff_score_stored_via_logger(self, tmp_logger, blank_image):
        from omnibench.benchmarks.task_schema import EpisodeResult
        from omnibench.evaluators.visual_diff import VisualDiffEvaluator
        ev = VisualDiffEvaluator()
        diff = ev.compare(blank_image, blank_image)
        run_id = tmp_logger.create_run("eval_telem", "mock")
        result = EpisodeResult(
            task_id="vis_001", domain="omnibench_native",
            passed=diff.passed, score=diff.score, total_steps=1, elapsed_seconds=0.1,
        )
        ep_id = tmp_logger.log_episode(run_id, result)
        eps = tmp_logger.list_episodes(run_id)
        assert eps[0]["task_id"] == "vis_001"


class TestRunnerGatewayDriverCombo:
    """Runner × Gateway × Driver end-to-end."""

    def test_runner_with_mock_router_and_driver(self, mock_driver, mock_router, native_task):
        from omnibench.benchmarks.runner import BenchmarkRunner
        runner = BenchmarkRunner(gateway_router=mock_router, driver=mock_driver)
        result = runner.run_episode(native_task)
        assert result is not None
        assert isinstance(result.score, float)

    def test_runner_logs_to_telemetry(self, mock_driver, mock_router, native_task, tmp_logger):
        from omnibench.benchmarks.runner import BenchmarkRunner
        runner = BenchmarkRunner(gateway_router=mock_router, driver=mock_driver)
        result = runner.run_episode(native_task)
        run_id = tmp_logger.create_run("combo_test", "mock")
        ep_id = tmp_logger.log_episode(run_id, result)
        eps = tmp_logger.list_episodes(run_id)
        assert len(eps) == 1


class TestSoMMemoryGatewayCombo:
    """SoM × Trajectory Memory × Gateway request building."""

    def test_som_annotation_bytes_routed_via_gateway(self, mock_driver, mock_router):
        import io
        from omnibench.visual.som import SoMAnnotator
        from omnibench.gateway.protocol import GatewayRequest
        img = mock_driver.capture_screenshot()
        annotator = SoMAnnotator()
        annotated, _ = annotator.annotate(img)
        buf = io.BytesIO()
        annotated.save(buf, format="PNG")
        req = GatewayRequest(prompt="click mark 3", images=[buf.getvalue()])
        resp = mock_router.route(req)
        assert resp.success is True

    def test_memory_feeds_prompt_context(self, mock_driver):
        from omnibench.visual.memory import SlidingTrajectoryMemory
        mem = SlidingTrajectoryMemory(max_screenshots=3)
        img = mock_driver.capture_screenshot()
        mem.add_step(img, "click(100,200)")
        mem.add_step(img, "type(hello)")
        state = mem.get_state()
        history = " | ".join(state.action_logs[-3:])
        assert "click" in history
        assert "type" in history
