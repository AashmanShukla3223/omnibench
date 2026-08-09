"""GAIA benchmark adapter."""
from __future__ import annotations
from typing import List, Optional
from omnibench.benchmarks.task_schema import BenchmarkTask, TaskDomain


class GAIAAdapter:
    """Adapter for GAIA multi-step reasoning benchmark tasks."""
    domain = TaskDomain.GAIA

    def __init__(self, data_dir: Optional[str] = None) -> None:
        self.data_dir = data_dir

    def load_tasks(self, limit: Optional[int] = None) -> List[BenchmarkTask]:
        tasks = [
            BenchmarkTask(
                task_id=f"gaia_synthetic_{i:03d}",
                domain=self.domain,
                instruction=instr,
                metadata={"source": "gaia_synthetic", "level": level},
                platform="linux",
                max_steps=50,
            )
            for i, (instr, level) in enumerate([
                ("What is the capital of France? Use the browser to verify.", 1),
                ("Find the current price of Apple (AAPL) stock and write it to a file.", 2),
                ("Download the Wikipedia article on Python and count the word 'programming'.", 3),
            ], 1)
        ]
        return tasks[:limit]
