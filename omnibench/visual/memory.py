"""
OmniBench Visual Grounding & Set-of-Marks Preprocessor - Sliding Trajectory Memory Buffer.
Contains MemoryState dataclass and SlidingTrajectoryMemory implementation.
"""

import base64
from collections import deque
from dataclasses import dataclass, field
import io
from typing import Any, Dict, List, Optional
from PIL import Image


@dataclass
class MemoryState:
    """
    Snapshot representation of the trajectory memory state.

    Attributes:
        screenshots: List of PIL Image objects currently in the sliding buffer (max len <= max_screenshots).
        action_logs: Complete list of text action log strings recorded across all steps.
        total_steps: Total number of execution steps added so far.
        max_screenshots: Maximum allowed capacity for screenshots buffer (default 3).
    """

    screenshots: List[Image.Image] = field(default_factory=list)
    action_logs: List[str] = field(default_factory=list)
    total_steps: int = 0
    max_screenshots: int = 3

    @property
    def num_screenshots(self) -> int:
        """Return the current number of screenshots in the buffer."""
        return len(self.screenshots)

    @property
    def num_actions(self) -> int:
        """Return total number of recorded text actions."""
        return len(self.action_logs)

    def get_latest_screenshot(self) -> Optional[Image.Image]:
        """Return the most recent screenshot in buffer, or None if empty."""
        return self.screenshots[-1] if self.screenshots else None

    def get_latest_action(self) -> Optional[str]:
        """Return the most recent action string, or None if empty."""
        return self.action_logs[-1] if self.action_logs else None

    def to_dict(self, include_image_bytes: bool = True) -> Dict[str, Any]:
        """
        Serialize state to a JSON-compatible dictionary.
        Images are optionally encoded as base64 PNG strings.
        """
        encoded_screenshots = []
        for img in self.screenshots:
            info_dict = {
                "width": img.width,
                "height": img.height,
                "mode": img.mode,
                "format": img.format or "PNG",
            }
            if include_image_bytes:
                buffer = io.BytesIO()
                img_format = img.format if img.format else "PNG"
                # If mode is not compatible directly with PNG or saved format, handle cleanly
                try:
                    img.save(buffer, format=img_format)
                except Exception:
                    # Fallback to PNG in RGB/RGBA
                    fallback_img = img.convert("RGBA") if "A" in img.mode else img.convert("RGB")
                    fallback_img.save(buffer, format="PNG")
                    img_format = "PNG"
                b64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
                info_dict["format"] = img_format
                info_dict["data_b64"] = b64_str

            encoded_screenshots.append(info_dict)

        return {
            "total_steps": self.total_steps,
            "max_screenshots": self.max_screenshots,
            "num_screenshots": len(self.screenshots),
            "num_actions": len(self.action_logs),
            "action_logs": list(self.action_logs),
            "screenshots": encoded_screenshots,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryState":
        """Reconstruct MemoryState from serialized dictionary."""
        total_steps = data.get("total_steps", 0)
        max_screenshots = data.get("max_screenshots", 3)
        action_logs = data.get("action_logs", [])

        screenshots = []
        raw_screenshots = data.get("screenshots", [])
        for item in raw_screenshots:
            if "data_b64" in item:
                img_bytes = base64.b64decode(item["data_b64"].encode("utf-8"))
                img = Image.open(io.BytesIO(img_bytes))
                img.load()
                screenshots.append(img)

        return cls(
            screenshots=screenshots,
            action_logs=list(action_logs),
            total_steps=total_steps,
            max_screenshots=max_screenshots,
        )


class SlidingTrajectoryMemory:
    """
    Sliding Trajectory Memory Buffer for OmniBench agent steps.
    Maintains a strictly bounded sliding window of PIL Images (default capacity: 3)
    and a cumulative log of textual action descriptions.
    """

    def __init__(
        self,
        max_screenshots: int = 3,
        copy_on_add: bool = True,
    ) -> None:
        if not isinstance(max_screenshots, int) or max_screenshots < 1:
            raise ValueError(f"max_screenshots must be a positive integer >= 1, got {max_screenshots}")

        self._max_screenshots = max_screenshots
        self._copy_on_add = copy_on_add
        self._screenshots: deque[Image.Image] = deque(maxlen=max_screenshots)
        self._action_logs: List[str] = []
        self._total_steps: int = 0

    @property
    def max_screenshots(self) -> int:
        return self._max_screenshots

    @property
    def total_steps(self) -> int:
        return self._total_steps

    def add_step(self, screenshot: Image.Image, action_str: str) -> MemoryState:
        """
        Add a step to the memory buffer.

        Args:
            screenshot: PIL Image captured at current step.
            action_str: Text string describing the action taken or action result.

        Returns:
            MemoryState snapshot representing current memory.

        Raises:
            TypeError: If screenshot is not a PIL.Image.Image or action_str is not a string.
        """
        if not isinstance(screenshot, Image.Image):
            raise TypeError(f"screenshot must be a PIL Image instance, got {type(screenshot).__name__}")
        if not isinstance(action_str, str):
            raise TypeError(f"action_str must be a string, got {type(action_str).__name__}")

        img_to_store = screenshot.copy() if self._copy_on_add else screenshot

        # Deque automatically evicts oldest screenshot (index 0) if len >= maxlen
        self._screenshots.append(img_to_store)
        self._action_logs.append(action_str)
        self._total_steps += 1

        return self.get_state()

    def get_state(self) -> MemoryState:
        """Return a current snapshot of MemoryState."""
        return MemoryState(
            screenshots=list(self._screenshots),
            action_logs=list(self._action_logs),
            total_steps=self._total_steps,
            max_screenshots=self._max_screenshots,
        )

    def get_screenshots(self) -> List[Image.Image]:
        """Return list of screenshots currently in memory."""
        return list(self._screenshots)

    def get_action_logs(self) -> List[str]:
        """Return copy of all text action logs."""
        return list(self._action_logs)

    def get_recent_actions(self, n: Optional[int] = None) -> List[str]:
        """Return the most recent n action logs, or all if n is None."""
        if n is None or n >= len(self._action_logs):
            return list(self._action_logs)
        if n <= 0:
            return []
        return self._action_logs[-n:]

    def clear(self) -> None:
        """Reset the buffer to empty state."""
        self._screenshots.clear()
        self._action_logs.clear()
        self._total_steps = 0

    def serialize(self) -> Dict[str, Any]:
        """Serialize internal state to JSON dict."""
        return self.get_state().to_dict(include_image_bytes=True)

    def load_state(self, state: MemoryState) -> None:
        """Load state into buffer from a MemoryState instance."""
        self._max_screenshots = state.max_screenshots
        self._total_steps = state.total_steps
        self._action_logs = list(state.action_logs)
        self._screenshots = deque(state.screenshots[-self._max_screenshots:], maxlen=self._max_screenshots)

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> "SlidingTrajectoryMemory":
        """Construct buffer from serialized dictionary."""
        state = MemoryState.from_dict(data)
        instance = cls(max_screenshots=state.max_screenshots)
        instance.load_state(state)
        return instance
