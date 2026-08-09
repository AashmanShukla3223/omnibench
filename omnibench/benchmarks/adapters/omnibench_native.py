"""OmniBench Native benchmark adapter — built-in integration tests."""
from __future__ import annotations
from typing import List, Optional
from omnibench.benchmarks.task_schema import BenchmarkTask, TaskDomain


class OmniBenchNativeAdapter:
    """Built-in OmniBench native benchmark tasks testing the full system stack."""
    domain = TaskDomain.OMNIBENCH_NATIVE

    def load_tasks(self, limit: Optional[int] = None) -> List[BenchmarkTask]:
        tasks = [
            BenchmarkTask(
                task_id="native_gateway_echo",
                domain=self.domain,
                instruction="Generate a click action at coordinates (500, 400).",
                assertion_specs=[],
                metadata={"source": "omnibench_native", "category": "gateway"},
                platform="linux",
                max_steps=3,
            ),
            BenchmarkTask(
                task_id="native_driver_wait",
                domain=self.domain,
                instruction="Wait for 1 second, then take a screenshot.",
                assertion_specs=[],
                metadata={"source": "omnibench_native", "category": "driver"},
                platform="linux",
                max_steps=3,
            ),
            BenchmarkTask(
                task_id="native_som_annotate",
                domain=self.domain,
                instruction="Annotate the current screen with Set-of-Marks and return the element count.",
                assertion_specs=[],
                metadata={"source": "omnibench_native", "category": "visual"},
                platform="linux",
                max_steps=2,
            ),
            BenchmarkTask(
                task_id="native_evaluator_e2e",
                domain=self.domain,
                instruction="Take before and after screenshots and compute the visual diff score.",
                assertion_specs=[],
                metadata={"source": "omnibench_native", "category": "evaluator"},
                platform="linux",
                max_steps=2,
            ),
            BenchmarkTask(
                task_id="native_telemetry_log",
                domain=self.domain,
                instruction="Run a benchmark step and verify it is logged to the SQLite database.",
                assertion_specs=[],
                metadata={"source": "omnibench_native", "category": "telemetry"},
                platform="linux",
                max_steps=2,
            ),
        ]
        return tasks[:limit]
