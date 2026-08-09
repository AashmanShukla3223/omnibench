"""
OmniBench Dual Evaluator Engine.
Combines VisualDiffEvaluator + SystemAssertionEvaluator for comprehensive task scoring.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from PIL import Image

from omnibench.evaluators.visual_diff import VisualDiffEvaluator, VisualDiffResult
from omnibench.evaluators.system_assertions import (
    SystemAssertionEvaluator,
    AssertionSpec,
)

logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """Comprehensive evaluation result from DualEvaluator."""

    passed: bool
    score: float
    visual_diff_score: float
    system_assertion_passed: bool
    visual_result: Optional[VisualDiffResult] = None
    system_result: Optional[Dict[str, Any]] = None
    details: Dict[str, Any] = field(default_factory=dict)


class DualEvaluator:
    """
    Combines visual state diffing and system assertion evaluation.

    Scoring:
    - If both visual and system evaluations are requested:
        score = 0.5 * visual_score + 0.5 * system_score
    - If only visual: score = visual_score
    - If only system: score = 1.0 if all assertions passed else 0.0
    - passed = score >= pass_threshold
    """

    def __init__(
        self,
        visual_evaluator: Optional[VisualDiffEvaluator] = None,
        system_evaluator: Optional[SystemAssertionEvaluator] = None,
        pass_threshold: float = 0.5,
    ) -> None:
        self._visual = visual_evaluator or VisualDiffEvaluator()
        self._system = system_evaluator or SystemAssertionEvaluator()
        self.pass_threshold = pass_threshold

    def evaluate(
        self,
        initial_state: Dict[str, Any],
        final_state: Dict[str, Any],
        trajectory: Optional[List[Dict[str, Any]]] = None,
        assertion_specs: Optional[List[AssertionSpec]] = None,
    ) -> EvaluationResult:
        """
        Evaluate task completion.

        Args:
            initial_state: Dict with optional 'screenshot' (PIL Image) key.
            final_state: Dict with optional 'screenshot' (PIL Image) key.
            trajectory: List of step dicts (action, screenshot, etc.).
            assertion_specs: List of system state assertions to verify.

        Returns:
            EvaluationResult with combined score and per-evaluator details.
        """
        visual_result: Optional[VisualDiffResult] = None
        visual_score = 0.0
        has_visual = False

        system_summary: Optional[Dict[str, Any]] = None
        system_score = 0.0
        has_system = bool(assertion_specs)

        # --- Visual Evaluation ---
        before_img = initial_state.get("screenshot")
        after_img = final_state.get("screenshot")
        if isinstance(before_img, Image.Image) and isinstance(after_img, Image.Image):
            has_visual = True
            visual_result = self._visual.compare(before_img, after_img)
            visual_score = visual_result.score

        # --- System Assertion Evaluation ---
        if has_system and assertion_specs:
            system_summary = self._system.evaluate_all(assertion_specs)
            passed_count = system_summary.get("passed_count", 0)
            total = system_summary.get("total", 1)
            system_score = passed_count / max(total, 1)
            system_assertion_passed = system_summary.get("passed", False)
        else:
            system_assertion_passed = True  # No assertions = vacuously true

        # --- Combined Scoring ---
        if has_visual and has_system:
            score = 0.5 * visual_score + 0.5 * system_score
        elif has_visual:
            score = visual_score
        elif has_system:
            score = system_score
        else:
            # No evaluation criteria — default pass
            score = 1.0
            system_assertion_passed = True

        passed = score >= self.pass_threshold

        return EvaluationResult(
            passed=passed,
            score=score,
            visual_diff_score=visual_score,
            system_assertion_passed=system_assertion_passed,
            visual_result=visual_result,
            system_result=system_summary,
            details={
                "has_visual": has_visual,
                "has_system": has_system,
                "pass_threshold": self.pass_threshold,
                "trajectory_steps": len(trajectory) if trajectory else 0,
            },
        )
