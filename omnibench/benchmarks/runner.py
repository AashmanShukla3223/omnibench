"""
OmniBench Benchmark Runner.
Executes benchmark episodes with agent-in-the-loop action/observe cycles.
"""

from __future__ import annotations

import io
import logging
import time
from typing import Any, Callable, Dict, List, Optional

from PIL import Image

from omnibench.benchmarks.task_schema import (
    BenchmarkTask,
    EpisodeResult,
    EpisodeStep,
)
from omnibench.evaluators.dual_evaluator import DualEvaluator, EvaluationResult
from omnibench.evaluators.self_correction import SelfCorrectionHandler
from omnibench.evaluators.system_assertions import AssertionSpec
from omnibench.gateway.protocol import GatewayRequest, GatewayResponse
from omnibench.visual.memory import SlidingTrajectoryMemory
from omnibench.visual.som import SoMAnnotator

logger = logging.getLogger(__name__)


class BenchmarkRunner:
    """
    Executes benchmark tasks in agent-observe-act episodes.

    Per-step cycle:
    1. Capture screenshot via driver.
    2. Annotate with SoM bounding boxes.
    3. Build gateway request with screenshot + instruction context.
    4. Route through cascading model gateway.
    5. Parse and execute action on OS driver.
    6. Self-correct on failure.
    7. Evaluate final state.
    """

    def __init__(
        self,
        gateway_router: Any,
        driver: Any,
        evaluator: Optional[DualEvaluator] = None,
        som_annotator: Optional[SoMAnnotator] = None,
        trajectory_memory: Optional[SlidingTrajectoryMemory] = None,
        correction_handler: Optional[SelfCorrectionHandler] = None,
    ) -> None:
        self._router = gateway_router
        self._driver = driver
        self._evaluator = evaluator or DualEvaluator()
        self._som = som_annotator or SoMAnnotator()
        self._memory = trajectory_memory or SlidingTrajectoryMemory(max_screenshots=3)
        self._correction = correction_handler or SelfCorrectionHandler()

    def _capture_screenshot(self) -> Optional[Image.Image]:
        try:
            return self._driver.capture_screenshot()
        except Exception as exc:
            logger.error("Screenshot capture failed: %s", exc)
            return None

    def _image_to_bytes(self, image: Image.Image) -> bytes:
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        return buf.getvalue()

    def _build_prompt(self, task: BenchmarkTask, step_idx: int) -> str:
        memory_state = self._memory.get_state()
        history_str = " | ".join(memory_state.action_logs[-3:]) if memory_state.action_logs else "None"
        return (
            f"Task: {task.instruction}\n"
            f"Step: {step_idx + 1}/{task.max_steps}\n"
            f"Platform: {task.platform}\n"
            f"Recent actions: {history_str}\n"
            "Output a JSON action: "
            '{"action": "<type>", "params": {<params>}}\n'
            "Action types: click, double_click, right_click, drag, type, key_combination, scroll, wait, terminate"
        )

    def _execute_action(self, action_json: Dict[str, Any]) -> bool:
        action_type = action_json.get("action", "wait")
        params = action_json.get("params", {})

        if action_type == "terminate":
            return True

        try:
            result = self._driver.execute_action(action_type, params)
            return result.success
        except Exception as exc:
            logger.error("Action execution error: %s", exc)
            return False

    def run_episode(self, task: BenchmarkTask) -> EpisodeResult:
        """Execute a complete benchmark episode for the given task."""
        t0 = time.perf_counter()
        steps: List[EpisodeStep] = []
        self._memory.clear()

        # Capture initial state
        initial_screenshot = self._capture_screenshot()
        initial_state: Dict[str, Any] = {}
        if initial_screenshot:
            initial_state["screenshot"] = initial_screenshot

        error: Optional[str] = None

        for step_idx in range(task.max_steps):
            step_t0 = time.perf_counter()

            # Capture current screenshot
            screenshot = self._capture_screenshot()
            screenshot_bytes_before = self._image_to_bytes(screenshot) if screenshot else None

            # Build SoM-annotated image
            images_for_request: List[bytes] = []
            if screenshot:
                try:
                    annotated, _ = self._som.annotate(screenshot)
                    images_for_request = [self._image_to_bytes(annotated)]
                except Exception:
                    images_for_request = [self._image_to_bytes(screenshot)] if screenshot else []

            # Build and route model request
            prompt = self._build_prompt(task, step_idx)
            req = GatewayRequest(
                prompt=prompt,
                images=images_for_request,
                model_name="auto",
            )
            try:
                response: GatewayResponse = self._router.route(req)
                action_json = response.action_json
                model_text = response.text
            except Exception as exc:
                logger.error("Gateway routing error: %s", exc)
                action_json = {"action": "wait", "params": {"seconds": 1.0}}
                model_text = ""

            # Execute action (with self-correction)
            action_type = action_json.get("action", "wait")
            success = self._execute_action(action_json)

            if not success:
                def _exec(a: Dict[str, Any]) -> bool:
                    return self._execute_action(a)
                correction = self._correction.retry_with_correction(_exec, action_json)
                success = correction.success
                if correction.final_action:
                    action_json = correction.final_action

            # Update trajectory memory
            if screenshot:
                self._memory.add_step(screenshot, f"{action_type}:{action_json.get('params', {})}")

            after_screenshot = self._capture_screenshot()
            screenshot_bytes_after = self._image_to_bytes(after_screenshot) if after_screenshot else None

            step = EpisodeStep(
                step_idx=step_idx,
                action_type=action_type,
                action_params=action_json.get("params", {}),
                screenshot_before=screenshot_bytes_before,
                screenshot_after=screenshot_bytes_after,
                action_result_success=success,
                latency_ms=(time.perf_counter() - step_t0) * 1000,
                model_response=model_text,
            )
            steps.append(step)

            # Terminate if model requested it
            if action_type == "terminate":
                break

        elapsed = time.perf_counter() - t0

        # Evaluate final state
        final_screenshot = self._capture_screenshot()
        final_state: Dict[str, Any] = {}
        if final_screenshot:
            final_state["screenshot"] = final_screenshot

        assertion_specs = [
            AssertionSpec(**spec) for spec in task.assertion_specs
        ] if task.assertion_specs else []

        eval_result: EvaluationResult = self._evaluator.evaluate(
            initial_state=initial_state,
            final_state=final_state,
            trajectory=[s.__dict__ for s in steps],
            assertion_specs=assertion_specs if assertion_specs else None,
        )

        return EpisodeResult(
            task_id=task.task_id,
            domain=task.domain.value,
            passed=eval_result.passed,
            score=eval_result.score,
            total_steps=len(steps),
            elapsed_seconds=elapsed,
            steps=steps,
            evaluation_details={
                "visual_score": eval_result.visual_diff_score,
                "system_passed": eval_result.system_assertion_passed,
                "details": eval_result.details,
            },
            error=error,
        )
