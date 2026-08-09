"""E2E Tier 2 — Boundary & Edge Cases for all 21 features."""

import pytest
from PIL import Image
import numpy as np


class TestBoundaryEngineConfig:
    def test_zero_temperature_generates(self):
        from omnibench.engine.onnx_engine import ONNXEngine, EngineConfig
        engine = ONNXEngine(EngineConfig())
        engine.load()
        result = engine.generate("test", temperature=0.0)
        assert result is not None

    def test_max_tokens_one(self):
        from omnibench.engine.onnx_engine import ONNXEngine, EngineConfig
        engine = ONNXEngine(EngineConfig())
        engine.load()
        result = engine.generate("test", max_tokens=1)
        assert isinstance(result.text, str)

    def test_empty_prompt(self):
        from omnibench.engine.onnx_engine import ONNXEngine, EngineConfig
        engine = ONNXEngine(EngineConfig())
        engine.load()
        result = engine.generate("")
        assert result is not None


class TestBoundaryGatewayProtocol:
    def test_min_temperature(self):
        from omnibench.gateway.protocol import GatewayRequest
        req = GatewayRequest(prompt="x", temperature=0.0)
        assert req.temperature == 0.0

    def test_max_temperature(self):
        from omnibench.gateway.protocol import GatewayRequest
        req = GatewayRequest(prompt="x", temperature=2.0)
        assert req.temperature == 2.0

    def test_temperature_just_over_max_raises(self):
        from omnibench.gateway.protocol import GatewayRequest
        with pytest.raises(ValueError):
            GatewayRequest(prompt="x", temperature=2.001)

    def test_single_char_prompt(self):
        from omnibench.gateway.protocol import GatewayRequest
        req = GatewayRequest(prompt="a")
        assert req.prompt == "a"

    def test_very_long_prompt(self):
        from omnibench.gateway.protocol import GatewayRequest
        req = GatewayRequest(prompt="x" * 10000)
        assert len(req.prompt) == 10000


class TestBoundaryDriverActions:
    def test_click_at_origin(self, mock_driver):
        result = mock_driver.execute_action("click", {"x": 0, "y": 0})
        assert result is not None

    def test_scroll_minimum_amount(self, mock_driver):
        result = mock_driver.execute_action("scroll", {"x": 100, "y": 100, "amount": 1})
        assert result is not None

    def test_wait_zero_seconds(self, mock_driver):
        result = mock_driver.execute_action("wait", {"seconds": 0.0})
        assert result is not None

    def test_type_empty_string(self, mock_driver):
        result = mock_driver.execute_action("type", {"text": ""})
        assert result is not None

    def test_key_combination_single_key(self, mock_driver):
        result = mock_driver.execute_action("key_combination", {"keys": ["Enter"]})
        assert result is not None


class TestBoundaryVisualProcessing:
    def test_resize_to_1x1(self, blank_image):
        from omnibench.visual.processing import ImageResizer
        r = ImageResizer()
        out = r.resize(blank_image, (1, 1))
        assert out.size == (1, 1)

    def test_tile_1x1_grid(self, blank_image):
        from omnibench.visual.processing import ImageResizer
        r = ImageResizer()
        tiles = r.tile(blank_image, (1, 1))
        assert len(tiles) == 1

    def test_grayscale_already_gray(self):
        from omnibench.visual.processing import ColorConverter
        gray = Image.new("L", (100, 100), 128)
        cc = ColorConverter()
        out = cc.to_rgb(gray)
        assert out.mode == "RGB"

    def test_memory_max_1_screenshot(self, blank_image):
        from omnibench.visual.memory import SlidingTrajectoryMemory
        mem = SlidingTrajectoryMemory(max_screenshots=1)
        for _ in range(5):
            mem.add_step(blank_image, "a")
        assert len(mem.get_state().screenshots) == 1

    def test_phash_identical_images_zero_distance(self, blank_image):
        from omnibench.evaluators.visual_diff import VisualDiffEvaluator
        ev = VisualDiffEvaluator()
        h1 = ev._compute_phash(blank_image)
        h2 = ev._compute_phash(blank_image)
        assert ev._phash_distance(h1, h2) == 0


class TestBoundaryTelemetry:
    def test_empty_runs_list(self, tmp_logger):
        runs = tmp_logger.list_runs()
        assert isinstance(runs, list)

    def test_nonexistent_run_summary_is_none(self, tmp_logger):
        assert tmp_logger.get_run_summary("no-such-id") is None

    def test_log_episode_with_no_steps(self, tmp_logger):
        from omnibench.benchmarks.task_schema import EpisodeResult
        run_id = tmp_logger.create_run("test", "mock")
        result = EpisodeResult(
            task_id="edge_001", domain="test", passed=False,
            score=0.0, total_steps=0, elapsed_seconds=0.01,
        )
        ep_id = tmp_logger.log_episode(run_id, result)
        assert ep_id is not None

    def test_finalize_run_zero_tasks(self, tmp_logger):
        run_id = tmp_logger.create_run("test", "mock")
        tmp_logger.finalize_run(run_id, 0, 0, 0, 0.0)
        s = tmp_logger.get_run_summary(run_id)
        assert s["total_tasks"] == 0

    def test_multiple_finalize_calls_idempotent(self, tmp_logger):
        run_id = tmp_logger.create_run("test", "mock")
        tmp_logger.finalize_run(run_id, 5, 5, 0, 1.0)
        tmp_logger.finalize_run(run_id, 5, 3, 2, 0.7)  # second call updates
        s = tmp_logger.get_run_summary(run_id)
        assert s["passed"] == 3
