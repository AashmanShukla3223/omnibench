# Feature 12 Technical Analysis & Design Report: Sliding Trajectory Memory Buffer

## Executive Summary
This document provides the complete architecture, data models, sliding window mechanics, serialization protocols, and unit testing strategy for Feature 12: Sliding Trajectory Memory Buffer (`SlidingTrajectoryMemory` and `MemoryState`) to be implemented in `omnibench/visual/memory.py` under Milestone M3 (Visual Grounding & Set-of-Marks Preprocessor).

---

## 1. Context & Architectural Requirements

### 1.1 Role in OmniBench 1.0 Architecture
OmniBench 1.0 executes complex multi-step computer automation tasks across web, desktop, and mobile operating systems. During an execution episode, the agent captures screenshots and emits action decisions. 

To maintain visual contextual history without exceeding local VLM RAM limits (~1.1 GiB for the 100M local ONNX engine) or LLM context window bounds:
- **Screenshots** must be strictly bounded to a sliding window of recent steps (default: max 3 screenshots).
- **Text Action Logs** preserve the chronological action history for reasoning and evaluators.
- **MemoryState** serves as the immutable/serializable state container representing the trajectory context at any step.

### 1.2 Authoritative Interface Contract
As specified in `PROJECT.md` and `SCOPE.md`:
- `SlidingTrajectoryMemory.add_step(screenshot: PIL.Image.Image, action_str: str) -> MemoryState`
- `MemoryState.screenshots`: `list[PIL.Image.Image]` (max length 3)
- `MemoryState.action_logs`: `list[str]`

---

## 2. Component Design & Data Models

### 2.1 `MemoryState` Dataclass / Model

`MemoryState` represents the immutable snapshot of trajectory memory at a given step.

#### Class Specification
```python
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from PIL import Image
import io
import base64

@dataclass
class MemoryState:
    """Snapshot representation of the trajectory memory state.
    
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
        """Serialize state to a JSON-compatible dictionary.
        
        Images are encoded as base64 PNG strings.
        """
        encoded_screenshots = []
        if include_image_bytes:
            for img in self.screenshots:
                buffer = io.BytesIO()
                # Ensure RGB mode for PNG output if image is palette or RGBA
                img_format = img.format if img.format else "PNG"
                img.save(buffer, format=img_format)
                b64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
                encoded_screenshots.append({
                    "width": img.width,
                    "height": img.height,
                    "mode": img.mode,
                    "format": img_format,
                    "data_b64": b64_str
                })
        else:
            for img in self.screenshots:
                encoded_screenshots.append({
                    "width": img.width,
                    "height": img.height,
                    "mode": img.mode,
                    "format": img.format or "PNG"
                })

        return {
            "total_steps": self.total_steps,
            "max_screenshots": self.max_screenshots,
            "num_screenshots": len(self.screenshots),
            "num_actions": len(self.action_logs),
            "action_logs": list(self.action_logs),
            "screenshots": encoded_screenshots
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
                # Load image into memory to avoid lazy file handle issues
                img.load()
                screenshots.append(img)

        return cls(
            screenshots=screenshots,
            action_logs=list(action_logs),
            total_steps=total_steps,
            max_screenshots=max_screenshots
        )
```

---

### 2.2 `SlidingTrajectoryMemory` Class

`SlidingTrajectoryMemory` manages the state lifecycle, bounded FIFO screenshot eviction, action recording, copy isolation, and reset logic.

#### Class Specification
```python
from collections import deque
from typing import List, Optional, Dict, Any
from PIL import Image

class SlidingTrajectoryMemory:
    """Sliding Trajectory Memory Buffer for OmniBench agent steps.
    
    Maintains a strictly bounded sliding window of PIL Images (default capacity: 3)
    and a cumulative log of textual action descriptions.
    """

    def __init__(
        self,
        max_screenshots: int = 3,
        copy_on_add: bool = True
    ) -> None:
        """Initialize sliding memory buffer.
        
        Args:
            max_screenshots: Maximum number of recent screenshots to keep. Must be >= 1.
            copy_on_add: Whether to create a independent deep copy of incoming PIL images.
        """
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
        """Add a step to the memory buffer.
        
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

        # Store isolated copy if copy_on_add is True
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
            max_screenshots=self._max_screenshots
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
```

---

## 3. Detailed Sliding & Eviction Mechanics

### 3.1 Bounding & Eviction Walkthrough

Consider default configuration `max_screenshots = 3`:

1. **Step 0 (Initial State)**:
   - `total_steps = 0`
   - `screenshots = []` (length 0)
   - `action_logs = []` (length 0)

2. **Step 1 (`add_step(S1, "click(100,200)")`)**:
   - `total_steps = 1`
   - `screenshots = [S1]` (length 1 <= 3)
   - `action_logs = ["click(100,200)"]`

3. **Step 2 (`add_step(S2, "type('search')")`)**:
   - `total_steps = 2`
   - `screenshots = [S1, S2]` (length 2 <= 3)
   - `action_logs = ["click(100,200)", "type('search')"]`

4. **Step 3 (`add_step(S3, "press_key('enter')")`)**:
   - `total_steps = 3`
   - `screenshots = [S1, S2, S3]` (length 3 == 3, full capacity)
   - `action_logs = ["click(100,200)", "type('search')", "press_key('enter')"]`

5. **Step 4 (`add_step(S4, "wait(2.0)")`)**:
   - FIFO eviction occurs: `S1` is removed from index 0.
   - `total_steps = 4`
   - `screenshots = [S2, S3, S4]` (length 3 == 3)
   - `action_logs = ["click(100,200)", "type('search')", "press_key('enter')", "wait(2.0)"]` (length 4)

6. **Step 5 (`add_step(S5, "scroll('down')")`)**:
   - `S2` is evicted from index 0.
   - `total_steps = 5`
   - `screenshots = [S3, S4, S5]` (length 3 == 3)
   - `action_logs = ["click(100,200)", "type('search')", "press_key('enter')", "wait(2.0)", "scroll('down')"]` (length 5)

---

## 4. Proposed Code File Placement

### 4.1 Production File Layout
- **Target File**: `/home/oh_my_macos27/OmniBench Computer Use/omnibench/visual/memory.py`
- **Module Init**: `/home/oh_my_macos27/OmniBench Computer Use/omnibench/visual/__init__.py`
  - Should re-export `SlidingTrajectoryMemory` and `MemoryState`:
    ```python
    from omnibench.visual.memory import SlidingTrajectoryMemory, MemoryState
    
    __all__ = [
        "SlidingTrajectoryMemory",
        "MemoryState",
    ]
    ```

---

## 5. Unit Test Plan (`tests/unit/test_visual.py` or `tests/unit/test_memory.py`)

A comprehensive unit test suite should cover the following 10 test cases:

1. `test_initial_state`: Verify `SlidingTrajectoryMemory` defaults (`total_steps=0`, empty screenshots, empty action logs).
2. `test_add_step_under_capacity`: Add 1 and 2 steps, verify `num_screenshots` matches step count and order is preserved.
3. `test_sliding_window_eviction`: Add 5 steps into max 3 capacity buffer; verify exactly the last 3 screenshots (S3, S4, S5) are present while all 5 action logs are retained.
4. `test_custom_max_screenshots`: Initialize with `max_screenshots=1` and `max_screenshots=5` and verify eviction thresholds match configured bounds.
5. `test_invalid_init_parameters`: Verify `ValueError` when `max_screenshots <= 0` or non-int.
6. `test_add_step_type_validation`: Verify `TypeError` when `screenshot` is not a PIL Image or `action_str` is not a string.
7. `test_image_copy_isolation`: Verify modifying source PIL Image after `add_step()` does not mutate image in memory buffer.
8. `test_clear`: Add steps then call `clear()`; verify state is completely reset (`total_steps=0`, 0 screenshots, 0 actions).
9. `test_serialization_deserialization_roundtrip`: Add steps with generated PIL Images, serialize to dict via `to_dict()`, deserialize via `from_dict()`/`deserialize()`, and verify images, image dimensions, action logs, and total_steps match exactly.
10. `test_recent_actions_query`: Test `get_recent_actions(n)` with `n=2`, `n=0`, and `n > len(actions)`.

---

## 6. Proposed Patch File / Snippets

For worker implementation, the proposed changes are ready to be written to `omnibench/visual/memory.py` and `omnibench/visual/__init__.py`.
