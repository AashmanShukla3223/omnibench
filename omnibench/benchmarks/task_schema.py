"""
OmniBench Benchmark Task Schema.
Defines the standardized JSON task specification used across all benchmark adapters.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class TaskDomain(str, Enum):
    OSWORLD = "osworld"
    WEBARENA = "webarena"
    ANDROIDWORLD = "androidworld"
    MIND2WEB = "mind2web"
    GAIA = "gaia"
    OMNIBENCH_NATIVE = "omnibench_native"


@dataclass
class BenchmarkTask:
    """Standardized benchmark task specification."""

    task_id: str
    domain: TaskDomain
    instruction: str
    initial_state: Dict[str, Any] = field(default_factory=dict)
    expected_outcome: Dict[str, Any] = field(default_factory=dict)
    assertion_specs: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    max_steps: int = 30
    timeout_seconds: float = 300.0
    platform: str = "linux"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "domain": self.domain.value,
            "instruction": self.instruction,
            "initial_state": self.initial_state,
            "expected_outcome": self.expected_outcome,
            "assertion_specs": self.assertion_specs,
            "metadata": self.metadata,
            "max_steps": self.max_steps,
            "timeout_seconds": self.timeout_seconds,
            "platform": self.platform,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BenchmarkTask":
        return cls(
            task_id=data["task_id"],
            domain=TaskDomain(data.get("domain", "omnibench_native")),
            instruction=data["instruction"],
            initial_state=data.get("initial_state", {}),
            expected_outcome=data.get("expected_outcome", {}),
            assertion_specs=data.get("assertion_specs", []),
            metadata=data.get("metadata", {}),
            max_steps=data.get("max_steps", 30),
            timeout_seconds=data.get("timeout_seconds", 300.0),
            platform=data.get("platform", "linux"),
        )


@dataclass
class EpisodeStep:
    """A single step in a benchmark episode trajectory."""

    step_idx: int
    action_type: str
    action_params: Dict[str, Any]
    screenshot_before: Optional[bytes] = None
    screenshot_after: Optional[bytes] = None
    action_result_success: bool = True
    latency_ms: float = 0.0
    model_response: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EpisodeResult:
    """Complete result of a single benchmark episode execution."""

    task_id: str
    domain: str
    passed: bool
    score: float
    total_steps: int
    elapsed_seconds: float
    steps: List[EpisodeStep] = field(default_factory=list)
    evaluation_details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
