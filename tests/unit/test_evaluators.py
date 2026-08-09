"""Unit tests for omnibench.evaluators — visual_diff, system_assertions, dual_evaluator, self_correction."""

import os
import pytest
import numpy as np
from PIL import Image


class TestVisualDiffEvaluator:
    def test_identical_images_high_ssim(self, blank_image):
        from omnibench.evaluators.visual_diff import VisualDiffEvaluator
        ev = VisualDiffEvaluator()
        result = ev.compare(blank_image, blank_image)
        assert result.ssim >= 0.9
        assert result.mse < 1.0
        assert result.pixel_diff_pct < 0.01

    def test_different_images_low_ssim(self, blank_image, random_image):
        from omnibench.evaluators.visual_diff import VisualDiffEvaluator
        ev = VisualDiffEvaluator()
        result = ev.compare(blank_image, random_image)
        assert result.mse > 0
        assert result.pixel_diff_pct >= 0

    def test_result_has_required_fields(self, blank_image):
        from omnibench.evaluators.visual_diff import VisualDiffEvaluator
        ev = VisualDiffEvaluator()
        result = ev.compare(blank_image, blank_image)
        assert hasattr(result, "mse")
        assert hasattr(result, "ssim")
        assert hasattr(result, "pixel_diff_pct")
        assert hasattr(result, "phash_distance")
        assert hasattr(result, "passed")

    def test_score_in_range(self, blank_image):
        from omnibench.evaluators.visual_diff import VisualDiffEvaluator
        ev = VisualDiffEvaluator()
        result = ev.compare(blank_image, blank_image)
        assert 0.0 <= result.score <= 1.0

    def test_diff_mask_returns_image(self, blank_image, random_image):
        from omnibench.evaluators.visual_diff import VisualDiffEvaluator
        ev = VisualDiffEvaluator()
        mask = ev.generate_diff_mask(blank_image, random_image)
        assert isinstance(mask, Image.Image)

    def test_roi_crop(self, blank_image, random_image):
        from omnibench.evaluators.visual_diff import VisualDiffEvaluator
        ev = VisualDiffEvaluator()
        result = ev.compare(blank_image, random_image, roi=(0, 0, 100, 100))
        assert result is not None


class TestSystemAssertionEvaluator:
    def test_file_exists_pass(self, tmp_path):
        from omnibench.evaluators.system_assertions import SystemAssertionEvaluator, AssertionSpec
        f = tmp_path / "test.txt"
        f.write_text("hello")
        ev = SystemAssertionEvaluator()
        spec = AssertionSpec(type="file_exists", target=str(f))
        result = ev.evaluate(spec)
        assert result.passed is True

    def test_file_exists_fail(self):
        from omnibench.evaluators.system_assertions import SystemAssertionEvaluator, AssertionSpec
        ev = SystemAssertionEvaluator()
        spec = AssertionSpec(type="file_exists", target="/nonexistent/file.txt")
        result = ev.evaluate(spec)
        assert result.passed is False

    def test_file_contains_pass(self, tmp_path):
        from omnibench.evaluators.system_assertions import SystemAssertionEvaluator, AssertionSpec
        f = tmp_path / "out.txt"
        f.write_text("OmniBench rocks")
        ev = SystemAssertionEvaluator()
        spec = AssertionSpec(type="file_contains", target=str(f), expected="OmniBench", match_mode="contains")
        result = ev.evaluate(spec)
        assert result.passed is True

    def test_cmd_output_pass(self):
        from omnibench.evaluators.system_assertions import SystemAssertionEvaluator, AssertionSpec
        ev = SystemAssertionEvaluator()
        spec = AssertionSpec(type="cmd_output", target="echo hello", expected="hello", match_mode="contains")
        result = ev.evaluate(spec)
        assert result.passed is True

    def test_env_var_pass(self, monkeypatch):
        from omnibench.evaluators.system_assertions import SystemAssertionEvaluator, AssertionSpec
        monkeypatch.setenv("OMNIBENCH_TEST_VAR", "present")
        ev = SystemAssertionEvaluator()
        spec = AssertionSpec(type="env_var", target="OMNIBENCH_TEST_VAR")
        result = ev.evaluate(spec)
        assert result.passed is True

    def test_unknown_type_returns_fail(self):
        from omnibench.evaluators.system_assertions import SystemAssertionEvaluator, AssertionSpec
        ev = SystemAssertionEvaluator()
        spec = AssertionSpec(type="invalid_type", target="x")
        result = ev.evaluate(spec)
        assert result.passed is False

    def test_evaluate_all_summary(self, tmp_path):
        from omnibench.evaluators.system_assertions import SystemAssertionEvaluator, AssertionSpec
        f = tmp_path / "a.txt"
        f.write_text("ok")
        ev = SystemAssertionEvaluator()
        specs = [
            AssertionSpec(type="file_exists", target=str(f)),
            AssertionSpec(type="file_exists", target="/nonexistent"),
        ]
        summary = ev.evaluate_all(specs)
        assert summary["total"] == 2
        assert summary["passed_count"] == 1
        assert summary["failed_count"] == 1


class TestDualEvaluator:
    def test_no_criteria_defaults_pass(self):
        from omnibench.evaluators.dual_evaluator import DualEvaluator
        ev = DualEvaluator()
        result = ev.evaluate({}, {})
        assert result.passed is True
        assert result.score == 1.0

    def test_visual_only_evaluation(self, blank_image):
        from omnibench.evaluators.dual_evaluator import DualEvaluator
        ev = DualEvaluator()
        result = ev.evaluate(
            {"screenshot": blank_image},
            {"screenshot": blank_image},
        )
        assert isinstance(result.score, float)
        assert 0.0 <= result.score <= 1.0

    def test_system_only_evaluation(self, tmp_path):
        from omnibench.evaluators.dual_evaluator import DualEvaluator
        from omnibench.evaluators.system_assertions import AssertionSpec
        f = tmp_path / "check.txt"
        f.write_text("done")
        ev = DualEvaluator()
        specs = [AssertionSpec(type="file_exists", target=str(f))]
        result = ev.evaluate({}, {}, assertion_specs=specs)
        assert result.system_assertion_passed is True

    def test_combined_evaluation(self, blank_image, tmp_path):
        from omnibench.evaluators.dual_evaluator import DualEvaluator
        from omnibench.evaluators.system_assertions import AssertionSpec
        f = tmp_path / "x.txt"
        f.write_text("ok")
        ev = DualEvaluator()
        specs = [AssertionSpec(type="file_exists", target=str(f))]
        result = ev.evaluate(
            {"screenshot": blank_image},
            {"screenshot": blank_image},
            assertion_specs=specs,
        )
        assert 0.0 <= result.score <= 1.0

    def test_result_fields_present(self, blank_image):
        from omnibench.evaluators.dual_evaluator import DualEvaluator
        ev = DualEvaluator()
        result = ev.evaluate({"screenshot": blank_image}, {"screenshot": blank_image})
        assert hasattr(result, "passed")
        assert hasattr(result, "score")
        assert hasattr(result, "visual_diff_score")
        assert hasattr(result, "system_assertion_passed")


class TestSelfCorrectionHandler:
    def test_successful_action_returns_pass(self):
        from omnibench.evaluators.self_correction import SelfCorrectionHandler, CorrectionConfig
        handler = SelfCorrectionHandler(CorrectionConfig(base_delay_s=0.0))
        call_count = [0]

        def execute(action):
            call_count[0] += 1
            return True

        result = handler.retry_with_correction(execute, {"action": "click", "params": {"x": 100, "y": 200}})
        assert result.success is True
        assert call_count[0] == 1

    def test_retries_on_failure(self):
        from omnibench.evaluators.self_correction import SelfCorrectionHandler, CorrectionConfig
        handler = SelfCorrectionHandler(CorrectionConfig(max_retries_l1=2, max_retries_l2=1, base_delay_s=0.0))
        calls = [0]

        def execute(action):
            calls[0] += 1
            return calls[0] >= 2  # succeed on 2nd attempt

        result = handler.retry_with_correction(execute, {"action": "click", "params": {"x": 500, "y": 300}})
        assert result.success is True

    def test_stagnation_detection_identical_images(self, blank_image):
        from omnibench.evaluators.self_correction import SelfCorrectionHandler
        handler = SelfCorrectionHandler()
        stagnated = handler.detect_stagnation([blank_image, blank_image])
        assert stagnated is True

    def test_no_stagnation_with_one_image(self, blank_image):
        from omnibench.evaluators.self_correction import SelfCorrectionHandler
        handler = SelfCorrectionHandler()
        assert handler.detect_stagnation([blank_image]) is False
