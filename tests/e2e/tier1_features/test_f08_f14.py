"""
E2E Tier 1 — Features F08–F14.

F08: Desktop OS Drivers (Linux/Windows/macOS)
F09: Mobile OS Drivers (Android/iOS)
F10: Error Backoff & Retries
F11: Screen Processing Pipeline
F12: Sliding Trajectory Memory
F13: Set-of-Marks (SoM) Generator
F14: Task Execution Runner
"""

import pytest
import numpy as np
from PIL import Image


# ── F08: Desktop OS Drivers ───────────────────────────────────────────────────

class TestF08DesktopDrivers:
    def test_linux_driver_instantiates(self):
        from omnibench.drivers.linux import LinuxDriver
        d = LinuxDriver(mock=True)
        assert d.platform == "linux"

    def test_linux_driver_connect_disconnect(self):
        from omnibench.drivers.linux import LinuxDriver
        d = LinuxDriver(mock=True)
        d.connect()
        assert d.is_connected()
        d.disconnect()
        assert not d.is_connected()

    def test_linux_driver_screenshot(self, mock_driver):
        img = mock_driver.capture_screenshot()
        assert isinstance(img, Image.Image)

    def test_windows_driver_platform(self):
        from omnibench.drivers.windows import WindowsDriver
        d = WindowsDriver(mock=True)
        assert d.platform == "windows"

    def test_macos_driver_platform(self):
        from omnibench.drivers.macos import MacOSDriver
        d = MacOSDriver(mock=True)
        assert d.platform == "macos"


# ── F09: Mobile OS Drivers ────────────────────────────────────────────────────

class TestF09MobileDrivers:
    def test_android_driver_platform(self):
        from omnibench.drivers.android import AndroidDriver
        d = AndroidDriver(mock=True)
        assert d.platform == "android"

    def test_ios_driver_platform(self):
        from omnibench.drivers.ios import IOSDriver
        d = IOSDriver(mock=True)
        assert d.platform == "ios"

    def test_android_driver_connect(self):
        from omnibench.drivers.android import AndroidDriver
        d = AndroidDriver(mock=True)
        d.connect()
        assert d.is_connected()

    def test_ios_driver_connect(self):
        from omnibench.drivers.ios import IOSDriver
        d = IOSDriver(mock=True)
        d.connect()
        assert d.is_connected()

    def test_android_screenshot_in_mock(self):
        from omnibench.drivers.android import AndroidDriver
        d = AndroidDriver(mock=True)
        d.connect()
        img = d.capture_screenshot()
        assert isinstance(img, Image.Image)


# ── F10: Error Backoff & Retries ──────────────────────────────────────────────

class TestF10RetryBackoff:
    def test_retry_decorator_retries_on_exception(self):
        from omnibench.drivers.retry import with_retry
        calls = [0]

        @with_retry(max_retries=3, initial_delay=0.0, retryable_exceptions=(RuntimeError,))
        def flaky():
            calls[0] += 1
            if calls[0] < 3:
                raise RuntimeError("temporary")
            return "ok"

        result = flaky()
        assert result == "ok"
        assert calls[0] == 3

    def test_retry_raises_after_max_retries(self):
        from omnibench.drivers.retry import with_retry

        @with_retry(max_retries=2, initial_delay=0.0, retryable_exceptions=(RuntimeError,))
        def always_fails():
            raise RuntimeError("permanent")

        with pytest.raises(RuntimeError):
            always_fails()

    def test_self_correction_handler_exists(self):
        from omnibench.evaluators.self_correction import SelfCorrectionHandler
        h = SelfCorrectionHandler()
        assert h is not None

    def test_backoff_config_fields(self):
        from omnibench.evaluators.self_correction import CorrectionConfig
        cfg = CorrectionConfig(max_retries_l1=5, base_delay_s=0.1)
        assert cfg.max_retries_l1 == 5
        assert cfg.base_delay_s == 0.1

    def test_correction_success_on_first_try(self):
        from omnibench.evaluators.self_correction import SelfCorrectionHandler, CorrectionConfig
        h = SelfCorrectionHandler(CorrectionConfig(base_delay_s=0.0))
        result = h.retry_with_correction(lambda a: True, {"action": "click", "params": {"x": 1, "y": 1}})
        assert result.success


# ── F11: Screen Processing ────────────────────────────────────────────────────

class TestF11ScreenProcessing:
    def test_resize_output_shape(self, blank_image):
        from omnibench.visual.processing import ImageResizer
        resizer = ImageResizer()
        out = resizer.resize(blank_image, (224, 224))
        assert out.size == (224, 224)

    def test_downscale_does_not_upscale(self, small_image):
        from omnibench.visual.processing import ImageResizer
        resizer = ImageResizer()
        out = resizer.downscale(small_image, 1024)
        assert out.size == small_image.size  # 64x64 < 1024

    def test_tile_count(self, blank_image):
        from omnibench.visual.processing import ImageResizer
        resizer = ImageResizer()
        tiles = resizer.tile(blank_image, (2, 2))
        assert len(tiles) == 4

    def test_color_converter_to_grayscale(self, blank_image):
        from omnibench.visual.processing import ColorConverter
        cc = ColorConverter()
        gray = cc.to_grayscale(blank_image)
        assert gray.mode in ("L", "RGB")

    def test_color_converter_to_rgb_from_rgba(self):
        from omnibench.visual.processing import ColorConverter
        rgba = Image.new("RGBA", (100, 100), (0, 128, 255, 200))
        cc = ColorConverter()
        rgb = cc.to_rgb(rgba)
        assert rgb.mode == "RGB"


# ── F12: Sliding Trajectory Memory ───────────────────────────────────────────

class TestF12SlidingMemory:
    def test_add_and_retrieve(self, blank_image):
        from omnibench.visual.memory import SlidingTrajectoryMemory
        mem = SlidingTrajectoryMemory(max_screenshots=3)
        mem.add_step(blank_image, "click(100, 200)")
        state = mem.get_state()
        assert len(state.screenshots) == 1
        assert "click(100, 200)" in state.action_logs

    def test_max_window_enforced(self, blank_image, random_image):
        from omnibench.visual.memory import SlidingTrajectoryMemory
        mem = SlidingTrajectoryMemory(max_screenshots=2)
        for i in range(5):
            mem.add_step(blank_image if i % 2 == 0 else random_image, f"step{i}")
        state = mem.get_state()
        assert len(state.screenshots) <= 2

    def test_clear_resets_memory(self, blank_image):
        from omnibench.visual.memory import SlidingTrajectoryMemory
        mem = SlidingTrajectoryMemory()
        mem.add_step(blank_image, "click(0,0)")
        mem.clear()
        state = mem.get_state()
        assert len(state.screenshots) == 0

    def test_action_log_accumulates(self, blank_image):
        from omnibench.visual.memory import SlidingTrajectoryMemory
        mem = SlidingTrajectoryMemory(max_screenshots=10)
        for i in range(5):
            mem.add_step(blank_image, f"action_{i}")
        state = mem.get_state()
        assert len(state.action_logs) == 5

    def test_empty_state_on_init(self):
        from omnibench.visual.memory import SlidingTrajectoryMemory
        mem = SlidingTrajectoryMemory()
        state = mem.get_state()
        assert state.screenshots == []


# ── F13: Set-of-Marks Generator ──────────────────────────────────────────────

class TestF13SoMGenerator:
    def test_annotate_returns_image_and_markmap(self, blank_image):
        from omnibench.visual.som import SoMAnnotator
        annotator = SoMAnnotator()
        annotated, mark_map = annotator.annotate(blank_image)
        assert isinstance(annotated, Image.Image)
        assert mark_map is not None

    def test_annotated_image_same_size(self, blank_image):
        from omnibench.visual.som import SoMAnnotator
        annotator = SoMAnnotator()
        annotated, _ = annotator.annotate(blank_image)
        assert annotated.size == blank_image.size

    def test_mark_map_lookup(self, blank_image):
        from omnibench.visual.som import SoMAnnotator
        annotator = SoMAnnotator()
        _, mark_map = annotator.annotate(blank_image)
        marks = mark_map._marks
        assert isinstance(marks, dict)

    def test_annotate_random_image(self, random_image):
        from omnibench.visual.som import SoMAnnotator
        annotator = SoMAnnotator()
        annotated, mark_map = annotator.annotate(random_image)
        assert isinstance(annotated, Image.Image)

    def test_mark_map_coordinates_in_bounds(self, blank_image):
        from omnibench.visual.som import SoMAnnotator
        annotator = SoMAnnotator()
        _, mark_map = annotator.annotate(blank_image)
        w, h = blank_image.size
        for mark_id, bbox in mark_map._marks.items():
            x_min, y_min, x_max, y_max = bbox
            assert 0 <= x_min <= w
            assert 0 <= y_min <= h
            assert 0 <= x_max <= w
            assert 0 <= y_max <= h


# ── F14: Task Execution Runner ────────────────────────────────────────────────

class TestF14TaskRunner:
    def test_runner_instantiates(self, mock_driver, mock_router):
        from omnibench.benchmarks.runner import BenchmarkRunner
        runner = BenchmarkRunner(gateway_router=mock_router, driver=mock_driver)
        assert runner is not None

    def test_run_episode_native_task(self, mock_driver, mock_router, native_task):
        from omnibench.benchmarks.runner import BenchmarkRunner
        runner = BenchmarkRunner(gateway_router=mock_router, driver=mock_driver)
        result = runner.run_episode(native_task)
        assert result.task_id == native_task.task_id

    def test_result_domain_matches_task(self, mock_driver, mock_router, native_task):
        from omnibench.benchmarks.runner import BenchmarkRunner
        runner = BenchmarkRunner(gateway_router=mock_router, driver=mock_driver)
        result = runner.run_episode(native_task)
        assert result.domain == native_task.domain.value

    def test_result_score_in_range(self, mock_driver, mock_router, native_task):
        from omnibench.benchmarks.runner import BenchmarkRunner
        runner = BenchmarkRunner(gateway_router=mock_router, driver=mock_driver)
        result = runner.run_episode(native_task)
        assert 0.0 <= result.score <= 1.0

    def test_steps_list_length(self, mock_driver, mock_router, native_task):
        from omnibench.benchmarks.runner import BenchmarkRunner
        runner = BenchmarkRunner(gateway_router=mock_router, driver=mock_driver)
        result = runner.run_episode(native_task)
        assert len(result.steps) <= native_task.max_steps
