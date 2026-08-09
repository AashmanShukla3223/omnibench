"""
OmniBench Self-Correction Handler.
Provides exponential backoff retry and visual stagnation detection for benchmark episodes.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class CorrectionConfig:
    """Configuration for self-correction retry behavior."""

    max_retries_l1: int = 3
    """Level-1 retry: same action with slight variation."""

    max_retries_l2: int = 2
    """Level-2 retry: fallback accessibility-based action."""

    base_delay_s: float = 0.5
    """Base exponential backoff delay in seconds."""

    max_delay_s: float = 8.0
    """Maximum delay cap in seconds."""

    jitter_fraction: float = 0.25
    """Random jitter as fraction of computed delay."""

    stagnation_threshold: float = 0.02
    """Pixel diff below this is treated as visual stagnation."""


@dataclass
class CorrectionResult:
    """Result of a self-correction cycle."""

    success: bool
    attempts: int
    level_reached: int
    final_action: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    stagnation_detected: bool = False


class SelfCorrectionHandler:
    """
    Level 1/2 retry handler with jittered exponential backoff.

    Level 1: Retries the same action with small positional jitter.
    Level 2: Attempts accessibility-based fallback action (keyboard shortcut or wait).
    """

    def __init__(self, config: Optional[CorrectionConfig] = None) -> None:
        self.config = config or CorrectionConfig()

    def _backoff_delay(self, attempt: int) -> None:
        """Sleep with exponential backoff + jitter."""
        delay = min(
            self.config.base_delay_s * (2 ** attempt),
            self.config.max_delay_s,
        )
        jitter = delay * self.config.jitter_fraction * (2 * np.random.random() - 1)
        sleep_time = max(0.0, delay + jitter)
        logger.debug("Backoff delay: %.2f s (attempt %d)", sleep_time, attempt)
        time.sleep(sleep_time)

    def _jitter_action(self, action: Dict[str, Any], attempt: int) -> Dict[str, Any]:
        """Apply small positional jitter to click/drag actions for level-1 retry."""
        import copy
        a = copy.deepcopy(action)
        params = a.get("params", {})
        jitter_px = 5 * attempt
        if "x" in params:
            params["x"] = int(params["x"]) + int(np.random.randint(-jitter_px, jitter_px + 1))
            params["x"] = max(0, params["x"])
        if "y" in params:
            params["y"] = int(params["y"]) + int(np.random.randint(-jitter_px, jitter_px + 1))
            params["y"] = max(0, params["y"])
        a["params"] = params
        return a

    def _fallback_action(self) -> Dict[str, Any]:
        """Return a safe Level-2 fallback action (Tab key to focus next element)."""
        return {"action": "key_combination", "params": {"keys": ["Tab"]}}

    def retry_with_correction(
        self,
        execute_fn: Callable[[Dict[str, Any]], bool],
        action: Dict[str, Any],
        verify_fn: Optional[Callable[[], bool]] = None,
    ) -> CorrectionResult:
        """
        Execute action with L1/L2 retry correction.

        Args:
            execute_fn: Function that executes an action dict. Returns True on success.
            action: Initial action to attempt.
            verify_fn: Optional function returning True if task state changed correctly.

        Returns:
            CorrectionResult with attempt count, level reached, and success flag.
        """
        total_attempts = 0

        # --- Level 1: Retry with jitter ---
        for attempt in range(self.config.max_retries_l1):
            jittered = self._jitter_action(action, attempt)
            try:
                ok = execute_fn(jittered)
                total_attempts += 1
                if ok and (verify_fn is None or verify_fn()):
                    return CorrectionResult(
                        success=True,
                        attempts=total_attempts,
                        level_reached=1,
                        final_action=jittered,
                    )
            except Exception as exc:
                logger.warning("L1 retry %d failed: %s", attempt, exc)
            self._backoff_delay(attempt)

        # --- Level 2: Fallback accessibility action ---
        fallback = self._fallback_action()
        for attempt in range(self.config.max_retries_l2):
            try:
                ok = execute_fn(fallback)
                total_attempts += 1
                if ok and (verify_fn is None or verify_fn()):
                    return CorrectionResult(
                        success=True,
                        attempts=total_attempts,
                        level_reached=2,
                        final_action=fallback,
                    )
            except Exception as exc:
                logger.warning("L2 retry %d failed: %s", attempt, exc)
            self._backoff_delay(attempt + self.config.max_retries_l1)

        return CorrectionResult(
            success=False,
            attempts=total_attempts,
            level_reached=2,
            error="All retry levels exhausted",
        )

    def detect_stagnation(
        self,
        screenshots: List[Any],  # List of PIL Images
    ) -> bool:
        """
        Detect visual stagnation by comparing last two screenshots.
        Returns True if screen appears unchanged (stagnated).
        """
        if len(screenshots) < 2:
            return False
        try:
            from omnibench.evaluators.visual_diff import VisualDiffEvaluator
            evaluator = VisualDiffEvaluator()
            result = evaluator.compare(screenshots[-2], screenshots[-1])
            return result.pixel_diff_pct < self.config.stagnation_threshold
        except Exception:
            return False
