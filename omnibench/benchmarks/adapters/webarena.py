"""WebArena benchmark adapter."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from omnibench.benchmarks.task_schema import BenchmarkTask, TaskDomain


class WebArenaAdapter:
    """Adapter for WebArena web navigation benchmark tasks."""
    domain = TaskDomain.WEBARENA

    def __init__(self, data_dir: Optional[str] = None) -> None:
        self.data_dir = Path(data_dir) if data_dir else None

    def load_tasks(self, limit: Optional[int] = None) -> List[BenchmarkTask]:
        if self.data_dir and self.data_dir.exists():
            tasks = []
            for path in sorted(self.data_dir.glob("**/*.json")):
                try:
                    with open(path) as f:
                        data = json.load(f)
                    tasks.append(BenchmarkTask(
                        task_id=str(data.get("task_id", path.stem)),
                        domain=self.domain,
                        instruction=data.get("intent", ""),
                        initial_state={"url": data.get("start_url", "")},
                        expected_outcome=data.get("eval", {}),
                        metadata={"source": "webarena"},
                        platform="linux",
                    ))
                    if limit and len(tasks) >= limit:
                        break
                except Exception:
                    continue
            if tasks:
                return tasks
        return [BenchmarkTask(
            task_id="webarena_synthetic_001",
            domain=self.domain,
            instruction="Navigate to the homepage and find the search bar.",
            initial_state={"url": "http://localhost:4399"},
            metadata={"source": "webarena_synthetic"},
            platform="linux",
        )]
