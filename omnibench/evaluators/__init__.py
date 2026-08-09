"""OmniBench evaluators package."""

from omnibench.evaluators.visual_diff import VisualDiffEvaluator, VisualDiffResult
from omnibench.evaluators.system_assertions import (
    SystemAssertionEvaluator,
    AssertionSpec,
    AssertionResult,
)
from omnibench.evaluators.dual_evaluator import DualEvaluator, EvaluationResult
from omnibench.evaluators.self_correction import SelfCorrectionHandler, CorrectionConfig, CorrectionResult

__all__ = [
    "VisualDiffEvaluator",
    "VisualDiffResult",
    "SystemAssertionEvaluator",
    "AssertionSpec",
    "AssertionResult",
    "DualEvaluator",
    "EvaluationResult",
    "SelfCorrectionHandler",
    "CorrectionConfig",
    "CorrectionResult",
]
