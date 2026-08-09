# Analysis: Milestone M3 — Visual Trajectory Memory (`omnibench/visual/memory.py`)

## 1. Overview & Objective
This report details the architectural investigation and validation of the Sliding Trajectory Memory system in `omnibench/visual/memory.py` for Milestone M3 (Visual Grounding & Set-of-Marks). 

The visual trajectory memory component provides short-term visual context (sliding window of screenshots) alongside a complete record of textual action logs, allowing the vision-language model engine and downstream evaluators to track execution history efficiently without blowing context windows or memory limits (~1.1 GiB RAM target).

---

## 2. Source Code Examination & Findings

### File Location & Dependencies
- Path: `omnibench/visual/memory.py`
- Dependencies: `collections.deque`, `dataclasses`, `PIL.Image`, `io`, `base64`, `typing`

### 2.1 `MemoryState` Dataclass
`MemoryState` represents an immutable snapshot of the agent's visual memory state at any given step.

```python
@dataclass
class MemoryState:
    screenshots: List[Image.Image] = field(default_factory=list)
    action_logs: List[str] = field(default_factory=list)
    total_steps: int = 0
    max_screenshots: int = 3
```

#### Key Capabilities & Properties:
- **`num_screenshots`**: Returns `len(self.screenshots)` ($\le 3$).
- **`num_actions`**: Returns total recorded action count (`len(self.action_logs)`).
- **`get_latest_screenshot()`**: Returns `screenshots[-1]` or `None` if empty.
- **`get_latest_action()`**: Returns `action_logs[-1]` or `None` if empty.
- **Serialization (`to_dict` / `from_dict`)**:
  - `to_dict(include_image_bytes=True)`: Encodes PIL Images into base64 PNG strings with metadata (`width`, `height`, `mode`, `format`). Automatically handles palette / transparency mode conversions (`P`/`RGBA`/`RGB`).
  - `from_dict(data)`: Deserializes base64 string back into loaded PIL Image instances.

### 2.2 `SlidingTrajectoryMemory` Class
`SlidingTrajectoryMemory` is the stateful trajectory manager.

```python
class SlidingTrajectoryMemory:
    def __init__(self, max_screenshots: int = 3, copy_on_add: bool = True) -> None:
        ...
```

#### Core Design Principles & Data Structures:
1. **Bounded Visual Buffer**: Uses `collections.deque(maxlen=max_screenshots)`. When a 4th screenshot is appended, index 0 (oldest screenshot) is automatically evicted by Python's native `deque` C implementation.
2. **Unbounded Action History**: Uses `List[str]` (`_action_logs`). Action history is cumulative and is never evicted, giving complete multi-step trajectory logging.
3. **Defensive Copying**: `copy_on_add=True` performs `screenshot.copy()` when adding steps, ensuring external modifications to the original PIL Image object do not alter stored state.
4. **Strict Type Contracts & Validation**:
   - `screenshot` must be `PIL.Image.Image` (raises `TypeError` otherwise).
   - `action_str` must be `str` (raises `TypeError` otherwise).
   - `max_screenshots` must be positive integer $\ge 1$ (raises `ValueError` otherwise).

---

## 3. Verification of Interface Contract

Interface defined in `PROJECT.md` and `SCOPE.md`:
```python
SlidingTrajectoryMemory.add_step(screenshot: Image, action_str: str) -> MemoryState
```

### Exact Signature in `omnibench/visual/memory.py`:
```python
def add_step(self, screenshot: Image.Image, action_str: str) -> MemoryState:
    if not isinstance(screenshot, Image.Image):
        raise TypeError(f"screenshot must be a PIL Image instance, got {type(screenshot).__name__}")
    if not isinstance(action_str, str):
        raise TypeError(f"action_str must be a string, got {type(action_str).__name__}")

    img_to_store = screenshot.copy() if self._copy_on_add else screenshot

    self._screenshots.append(img_to_store)
    self._action_logs.append(action_str)
    self._total_steps += 1

    return self.get_state()
```
**Status**: Contract matches specification 100%.

---

## 4. FIFO Eviction & Trajectory Tracing

| Step | Action Added | Deque Screenshots (max 3) | Action Logs History (Cumulative) | Total Steps |
|---|---|---|---|---|
| Initial | - | `[]` | `[]` | 0 |
| Step 1 | `"click(100, 200)"` | `[S1]` | `["click(100, 200)"]` | 1 |
| Step 2 | `"type('omni')"` | `[S1, S2]` | `["click(100, 200)", "type('omni')"]` | 2 |
| Step 3 | `"key_combination('Enter')"` | `[S1, S2, S3]` | `["click(100, 200)", "type('omni')", "key_combination('Enter')"]` | 3 |
| Step 4 | `"scroll(0, -100)"` | `[S2, S3, S4]` *(S1 dropped)* | `["click(100, 200)", "type('omni')", "key_combination('Enter')", "scroll(0, -100)"]` | 4 |

---

## 5. Test Suite & Verification Results

Unit tests for `omnibench/visual` are co-located in `tests/unit/test_visual.py`.

Execution Command:
```bash
.venv/bin/pytest tests/unit/test_visual.py
```

### Execution Summary:
- **Result**: `23 passed in 0.35s`
- **Memory Specific Tests**:
  - `test_memory_state_basics_and_serialization`: Verified snapshot creation, properties, and base64 roundtrip.
  - `test_empty_memory_state`: Verified initial default empty state behaviors.
  - `test_sliding_trajectory_memory_fifo_eviction`: Verified 5-step addition to maxlen=3 buffer drops first 2 screenshots while keeping all 5 action strings.
  - `test_sliding_trajectory_memory_copy_isolation`: Verified mutating source image after `add_step` does not alter stored image.
  - `test_sliding_trajectory_memory_get_recent_actions_and_clear`: Verified `get_recent_actions(n)` slice logic and `clear()` reset.
  - `test_sliding_trajectory_memory_serialization_roundtrip`: Verified complete `serialize()` and `deserialize()` roundtrip.
  - `test_sliding_trajectory_memory_invalid_inputs`: Verified strict type checking exceptions.

---

## 6. Recommendations & Implementation Plan
1. **No Code Modifications Needed**: The existing implementation in `omnibench/visual/memory.py` is fully functional, well-tested, and adheres strictly to all specified requirements.
2. **Downstream Integration Guidelines**:
   - VLM Gateway/Engine should use `MemoryState.screenshots` to format prompt image lists (`images: list[bytes]`).
   - Evaluators should use `MemoryState.action_logs` and `total_steps` for step assertion tracing.
   - Database telemetry loggers can call `MemoryState.to_dict()` for SQLite step logging.
