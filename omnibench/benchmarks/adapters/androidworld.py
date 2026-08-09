"""AndroidWorld benchmark adapter with real-world Samsung phone contact calling tasks."""

from __future__ import annotations
from typing import List, Optional
from omnibench.benchmarks.task_schema import BenchmarkTask, TaskDomain


class AndroidWorldAdapter:
    """Adapter for AndroidWorld mobile benchmark tasks."""
    domain = TaskDomain.ANDROIDWORLD

    def __init__(self, data_dir: Optional[str] = None) -> None:
        self.data_dir = data_dir

    def load_tasks(self, limit: Optional[int] = None) -> List[BenchmarkTask]:
        tasks = [
            BenchmarkTask(
                task_id="android_samsung_call_vanya_001",
                domain=self.domain,
                instruction="Open the Phone app, search for contact 'Vanya Chaudhary', and initiate a voice call.",
                metadata={"device_target": "samsung_galaxy", "contact_target": "Vanya Chaudhary", "app": "com.samsung.android.dialer"},
                platform="android",
                max_steps=5,
            ),
            BenchmarkTask(
                task_id="android_samsung_sms_vanya_002",
                domain=self.domain,
                instruction="Open Messages app and send 'I will call you in 5 minutes' to Vanya Chaudhary.",
                metadata={"device_target": "samsung_galaxy", "contact_target": "Vanya Chaudhary", "app": "com.samsung.android.messaging"},
                platform="android",
                max_steps=5,
            ),
            BenchmarkTask(
                task_id="androidworld_synthetic_001",
                domain=self.domain,
                instruction="Open the Settings app and enable Wi-Fi.",
                metadata={"source": "androidworld_synthetic"},
                platform="android",
                max_steps=5,
            ),
            BenchmarkTask(
                task_id="androidworld_synthetic_002",
                domain=self.domain,
                instruction="Open the Camera app and take a photo.",
                metadata={"source": "androidworld_synthetic"},
                platform="android",
                max_steps=5,
            ),
        ]
        return tasks[: limit]
