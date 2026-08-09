"""OSWorld benchmark adapter — loads OSWorld-format task JSON files."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional
from omnibench.benchmarks.task_schema import BenchmarkTask, TaskDomain


class OSWorldAdapter:
    """Adapter for OSWorld desktop computer use benchmark tasks."""

    domain = TaskDomain.OSWORLD

    def __init__(self, data_dir: Optional[str] = None) -> None:
        self.data_dir = Path(data_dir) if data_dir else None

    def load_tasks(self, limit: Optional[int] = None) -> List[BenchmarkTask]:
        if self.data_dir is None or not self.data_dir.exists():
            return self._synthetic_tasks()
        tasks = []
        for path in sorted(self.data_dir.glob("**/*.json")):
            try:
                with open(path) as f:
                    data = json.load(f)
                tasks.append(self._parse(data, path.stem))
                if limit and len(tasks) >= limit:
                    break
            except Exception:
                continue
        return tasks or self._synthetic_tasks()

    def _parse(self, data: Dict[str, Any], task_id: str) -> BenchmarkTask:
        return BenchmarkTask(
            task_id=data.get("id", task_id),
            domain=self.domain,
            instruction=data.get("instruction", data.get("task", "")),
            initial_state=data.get("initial_state", {}),
            expected_outcome=data.get("expected", {}),
            assertion_specs=data.get("evaluator", {}).get("assertions", []),
            metadata={"source": "osworld", "raw": data},
            max_steps=data.get("max_steps", 30),
            platform=data.get("platform", "linux"),
        )

    def _synthetic_tasks(self) -> List[BenchmarkTask]:
        return [
            BenchmarkTask(
                task_id="osworld_synthetic_001",
                domain=self.domain,
                instruction="Open a text editor and type 'Hello, OmniBench!'",
                assertion_specs=[],
                metadata={"source": "osworld_synthetic"},
                platform="linux",
            )
        ]
