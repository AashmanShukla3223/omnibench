"""Mind2Web benchmark adapter."""
from __future__ import annotations
from typing import List, Optional
from omnibench.benchmarks.task_schema import BenchmarkTask, TaskDomain


class Mind2WebAdapter:
    """Adapter for Mind2Web web task benchmark."""
    domain = TaskDomain.MIND2WEB

    def __init__(self, data_dir: Optional[str] = None) -> None:
        self.data_dir = data_dir

    def load_tasks(self, limit: Optional[int] = None) -> List[BenchmarkTask]:
        tasks = [
            BenchmarkTask(
                task_id=f"mind2web_synthetic_{i:03d}",
                domain=self.domain,
                instruction=instr,
                metadata={"source": "mind2web_synthetic", "website": site},
                platform="linux",
            )
            for i, (instr, site) in enumerate([
                ("Search for 'laptop' on Amazon and filter by 4+ stars.", "amazon"),
                ("Find the cheapest flight from NYC to LAX next Monday.", "google_flights"),
                ("Book a table for 2 at an Italian restaurant nearby.", "yelp"),
            ], 1)
        ]
        return tasks[:limit]
