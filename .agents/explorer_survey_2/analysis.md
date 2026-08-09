# Technical Survey & Architecture Specification Report for OmniBench 1.0 (Requirements R2, R3, R5)

**Agent ID**: `explorer_survey_2`  
**Date**: 2026-08-08  
**Scope**: Requirements R2 (Cross-Platform OS Automation Drivers), R3 (Visual Grounding & SoM Preprocessor), and R5 (Interface & Telemetry Dashboard).

---

## Executive Summary

This report establishes the complete architectural specification, data contracts, platform abstraction interfaces, visual processing pipelines, database schemas, CLI commands, web dashboard design, and verification strategies for OmniBench 1.0 Requirements **R2**, **R3**, and **R5**. 

The current system environment has been thoroughly audited:
- **Operating System**: Debian GNU/Linux 13 (trixie), kernel 6.6, Xvfb virtual framebuffer available (`/usr/bin/Xvfb`), Node.js 24.18.0 available.
- **Python Runtime**: Python 3.13.5 with `click` (8.1.8) and standard library `sqlite3` installed; external packages will be managed via pure-Python fallbacks or virtualenv dependencies.
- **Project Structure**: Clean slate starting from `ORIGINAL_REQUEST.md`.

---

## 1. Requirement R2 — Cross-Platform OS Automation Drivers

### 1.1 Platform Support Matrix & Execution Mechanisms

Requirement R2 mandates uniform cross-platform driver abstractions covering five major operating systems. Each driver must encapsulate low-level platform APIs while presenting a single standard interface to the benchmark runner.

| Operating System | Target Versions | Execution Backend / API | Screenshot Mechanism | Special Platform Handling |
| :--- | :--- | :--- | :--- | :--- |
| **Windows** | Windows 10, 11+ | `pywinauto` / `UIAutomation` / `win32api` / PowerShell | `BitBlt` / `pyautogui` / `PIL.ImageGrab` | DPI scaling factor awareness (100%-200%), multi-monitor coordinate offsets |
| **macOS** | macOS 11+ (Big Sur+) | Quartz CoreGraphics / AppleScript `osascript` / `cliclick` | `/usr/sbin/screencapture` | Retina display points-to-pixels 2x multiplier scaling, Accessibility permissions check |
| **Linux** | Debian 12/13, Ubuntu 20.04+ | X11: `xdotool` / `python-xlib`; Wayland: `ydotool` / `wtype`; Headless: `Xvfb` | `scrot` / `import` / `grim` / `PIL` | Session type auto-detection (`$XDG_SESSION_TYPE`), virtual display launch on `:99` |
| **Android** | Android 10+ (API level 29+) | `adb shell input` / `uiautomator` daemon (`uiautomator2` port 9008) | `adb exec-out screencap -p` | ADB daemon port forwarding, Android keycodes (`KEYCODE_BACK=4`, `KEYCODE_HOME=3`) |
| **iOS** | iOS 14+ | Simulator: `xcrun simctl` / `idb`; Physical: `WebDriverAgent` (WDA) REST API | `xcrun simctl io screenshot` / WDA HTTP GET `/screenshot` | WDA session lifecycle, device identifier mapping |

---

### 1.2 Action Primitive Specification & Data Contracts

All drivers MUST implement the abstract base class `BaseOSDriver`. Action primitives are represented by standardized Python dataclasses and Enums.

#### Data Structures

```python
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple

class ActionType(str, Enum):
    CLICK = "click"
    DOUBLE_CLICK = "double_click"
    RIGHT_CLICK = "right_click"
    DRAG = "drag"
    TYPE = "type"
    KEY_COMBINATION = "key_combination"
    SCROLL = "scroll"
    WAIT = "wait"

@dataclass
class ActionPrimitive:
    action_type: ActionType
    x: Optional[int] = None
    y: Optional[int] = None
    button: str = "left"  # "left", "right", "middle"
    end_x: Optional[int] = None
    end_y: Optional[int] = None
    duration: float = 0.5  # Drag duration or key press duration
    text: Optional[str] = None
    keys: List[str] = field(default_factory=list)  # e.g., ["ctrl", "c"] or ["cmd", "space"]
    direction: str = "down"  # "up", "down", "left", "right"
    amount: int = 100  # Scroll pixel delta or wheel ticks
    seconds: float = 0.0  # Wait action duration

@dataclass
class ActionResult:
    success: bool
    action: ActionPrimitive
    duration_ms: float
    error_message: Optional[str] = None
    retry_count: int = 0
    screenshot_before: Optional[bytes] = None
    screenshot_after: Optional[bytes] = None
```

#### Action Primitive Requirements

1. **`click(x: int, y: int, button: str = "left") -> ActionResult`**: Move pointer to exact screen coordinate `(x, y)` and trigger single mouse button press & release.
2. **`double_click(x: int, y: int) -> ActionResult`**: Rapid sequence of two left clicks at `(x, y)` within system double-click threshold (< 300ms).
3. **`right_click(x: int, y: int) -> ActionResult`**: Secondary button click at `(x, y)` triggering context menus.
4. **`drag(start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 0.5) -> ActionResult`**: Mouse down at `(start_x, start_y)`, interpolated smooth trajectory to `(end_x, end_y)` over `duration` seconds, mouse up.
5. **`type(text: str, interval: float = 0.0) -> ActionResult`**: Keystroke injection for literal string `text` with optional inter-character pause.
6. **`key_combination(keys: List[str]) -> ActionResult`**: Execute modifier key sequences (e.g. `["ctrl", "c"]`, `["cmd", "shift", "4"]`). Hold modifier keys in forward order, strike final key, release modifiers in reverse order.
7. **`scroll(x: int, y: int, direction: str = "down", amount: int = 100) -> ActionResult`**: Scroll wheel action at `(x, y)` along vertical or horizontal axis.
8. **`wait(seconds: float) -> ActionResult`**: Controlled execution sleep allowing OS state transitions or animation settles.

---

### 1.3 Automated Error Backoff & Retry Protocol

To ensure benchmark resilience against transient UI lags, daemon disconnects, or animation blocks, the driver layer incorporates a standardized retry and health check policy.

#### Exception Hierarchy

```python
class DriverException(Exception):
    """Base exception for driver failures."""
    pass

class PlatformNotSupportedError(DriverException):
    """Raised when driver is invoked on unsupported OS host."""
    pass

class ConnectionTimeoutError(DriverException):
    """Raised when remote daemon (ADB/WDA) or display server is unreachable."""
    pass

class TargetUnresponsiveError(DriverException):
    """Raised when host system or application UI freezes."""
    pass

class ActionExecutionError(DriverException):
    """Raised when underlying system call/primitive returns an error code."""
    pass

class CoordinatesOutOfBoundsError(DriverException):
    """Raised when action coordinates exceed active screen resolution."""
    pass
```

#### Retry Policy Configuration & Algorithm

- **Max Retries**: Default 3 attempts per action.
- **Initial Delay**: 0.5 seconds.
- **Backoff Multiplier**: 2.0 (exponential sequence: 0.5s -> 1.0s -> 2.0s).
- **Max Delay Cap**: 5.0 seconds.
- **Random Jitter**: Add +/- 10% uniform random jitter to prevent synchronization locks.

```python
import time
import random
from functools import wraps

def with_retry(max_retries: int = 3, initial_delay: float = 0.5, backoff_factor: float = 2.0, max_delay: float = 5.0):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            delay = initial_delay
            last_exception = None
            for attempt in range(1, max_retries + 1):
                try:
                    if hasattr(self, "health_check") and not self.health_check():
                        self.reconnect()
                    return func(self, *args, **kwargs)
                except (ActionExecutionError, ConnectionTimeoutError) as e:
                    last_exception = e
                    if attempt == max_retries:
                        break
                    jittered_delay = min(max_delay, delay * (1 + random.uniform(-0.1, 0.1)))
                    time.sleep(jittered_delay)
                    delay *= backoff_factor
            raise last_exception
        return wrapper
    return decorator
```

#### Auto-Reconnection Protocol
Every driver implements:
- `health_check() -> bool`: Verifies connection to display server, X11 socket, ADB daemon (`adb get-state`), or WDA REST endpoint.
- `reconnect() -> bool`: Performs soft reset (e.g. `adb kill-server && adb start-server`, restart Xvfb display, re-establish HTTP session).

---

## 2. Requirement R3 — Visual Grounding & Set-of-Marks (SoM) Preprocessor

### 2.1 Visual Processing Engine Architecture

The visual engine handles screenshot preprocessing, color model transformations, image downscaling/tiling, and sliding window trajectory context management.

```
+------------------+     +-------------------+     +-------------------------+
|  Raw Screenshot  | --> | ImageResizer /    | --> | SlidingTrajectoryMemory |
| (High-Res / 4K)  |     | ColorConverter    |     | (3 Frames + Action Logs)|
+------------------+     +-------------------+     +-------------------------+
          |                                                      |
          v                                                      v
+------------------+                                   +-------------------------+
| Set-of-Marks     | --------------------------------> | Formatted Model Context |
| Annotator (SoM)  |   Mark ID -> (X, Y) Mapping       | (Visual Prompt Input)   |
+------------------+                                   +-------------------------+
```

#### Image Processing Pipeline Components

1. **`ImageResizer & TilingManager`**:
   - **Resolution Normalization**: Standardizes high-res (e.g. 3840x2160 or 2560x1600 Retina) screenshots down to model input bounds (e.g. 512x512, 768x768, 1024x1024) while preserving aspect ratio with padding.
   - **Grid Tiling**: Splits high-resolution displays into overlapping 2x2 or 3x3 tiles for high-density UI inspection.
   - **Coordinate Transformation Math**:
     - `global_to_tile(x, y, tile_rect) -> (tile_x, tile_y)`
     - `tile_to_global(tile_x, tile_y, tile_rect) -> (x, y)`

2. **`ColorConverter`**:
   - Modes: Full RGB (3 channels) or Grayscale (`L` mode, 1 channel).
   - Optimizes memory and bandwidth for INT8/INT4 CPU models.

3. **`SlidingTrajectoryMemory`**:
   - Maintains a fixed sliding FIFO window of **exactly the last 3 turns**.
   - Data structure per turn:
     ```python
     @dataclass
     class TrajectoryFrame:
         step_index: int
         timestamp: float
         raw_image_bytes: bytes
         som_image_bytes: bytes
         action: ActionPrimitive
         action_text_log: str  # e.g., "Step 2: CLICK [Mark 14] at (450, 320)"
     ```
   - Capacity constraint: Exceeding 3 turns automatically evicts the oldest frame while keeping text summary logs intact.

---

### 2.2 Set-of-Marks (SoM) Bounding Box Generator & Mapping Contract

Set-of-Marks (SoM) superimposes numbered interactive mark tags over UI element bounding boxes on the screenshot, enabling vision-language models to ground decisions to mark numbers rather than raw pixel coordinates.

#### Bounding Box Sources
1. **Accessibility / UI Automation Tree**:
   - Extract UI nodes from OS API (Android `uiautomator` XML dump, Web DOM `getBoundingClientRect()`, Windows `UIAutomation`, macOS `AXUIElement`).
2. **Computer Vision Contour Detection (Fallback)**:
   - OpenCV / Pillow edge detection + contour bounding box extraction for non-accessible canvas element detection.

#### SoM Drawing Pipeline & Rendering Specification

- **Box Outlines**: High-contrast 2px stroke rectangles around detected interactive elements.
- **Badge Tags**: Solid filled rectangle badge at top-left corner of bounding box with high-contrast text label (e.g. black text on yellow/cyan/red background, e.g. `[1]`, `[2]`, `[14]`).
- **Font & Size Scaling**: Dynamically scaled based on screenshot resolution to guarantee legibility without obscuring adjacent elements.

#### Bidirectional Coordinate Mapping (`MarkMap`)

```python
class MarkMap:
    def __init__(self):
        self._mark_to_box: Dict[int, Tuple[int, int, int, int]] = {} # id -> (xmin, ymin, xmax, ymax)
        self._mark_to_center: Dict[int, Tuple[int, int]] = {}      # id -> (x_center, y_center)

    def register_mark(self, mark_id: int, bbox: Tuple[int, int, int, int]):
        xmin, ymin, xmax, ymax = bbox
        center_x = (xmin + xmax) // 2
        center_y = (ymin + ymax) // 2
        self._mark_to_box[mark_id] = bbox
        self._mark_to_center[mark_id] = (center_x, center_y)

    def get_center(self, mark_id: int) -> Tuple[int, int]:
        if mark_id not in self._mark_to_center:
            raise KeyError(f"Mark ID {mark_id} not found in current SoM map.")
        return self._mark_to_center[mark_id]

    def find_mark_at(self, x: int, y: int) -> Optional[int]:
        for mark_id, (xmin, ymin, xmax, ymax) in self._mark_to_box.items():
            if xmin <= x <= xmax and ymin <= y <= ymax:
                return mark_id
        return None
```

---

## 3. Requirement R5 — Interface & Telemetry Dashboard

Requirement R5 specifies a dual-mode interface: a Python CLI tool (`omnibench`) and an interactive Web Dashboard UI backed by SQLite database persistence and screenshot diff analytics.

### 3.1 Python CLI Framework (`omnibench`)

The CLI is implemented using `click` (v8.1.8).

```
omnibench
├── config       # View, set, and validate framework settings
├── dataset      # Select, list, and validate benchmark datasets (OSWorld, WebArena, etc.)
├── run          # Launch evaluation benchmarks with model, driver, and task flags
├── monitor      # Live ASCII terminal dashboard of active trajectory progress
├── db           # Inspect SQLite database runs, episodes, metrics, export reports
└── dashboard    # Launch the HTTP Web Dashboard UI server
```

#### Command Interfaces Specification

```bash
# Configuration management
omnibench config list
omnibench config set --key gateway.openai_key --value "sk-..."

# Dataset management
omnibench dataset list
omnibench dataset inspect --name OSWorld

# Running benchmarks
omnibench run --dataset OSWorld --task 001 --model local_onnx --driver linux --output ./results

# Live monitoring terminal
omnibench monitor --run-id run_20260808_001

# Database inspection & export
omnibench db summary
omnibench db export --run-id run_20260808_001 --format json --out report.json

# Web Dashboard launcher
omnibench dashboard --host 127.0.0.1 --port 8080
```

---

### 3.2 Web Dashboard UI Architecture

The Web Dashboard presents a responsive single-page web interface for dataset management, benchmark triggering, live trajectory inspection, and visual diff analytics.

#### Server Architecture
- **Backend**: Embedded Python WSGI/ASGI HTTP Server (`http.server` or `uvicorn`/`fastapi` when installed) communicating with SQLite database and filesystem artifact store.
- **Real-Time Updates**: Server-Sent Events (SSE) stream or WebSocket endpoint (`/api/stream/trajectory/{run_id}`) broadcasting step actions, screenshot thumbnails, latency metrics, and log outputs.
- **Frontend Views**:
  1. **Overview Dashboard**: Metrics panel showing total runs, pass rate percentage, average latency, and platform breakdown.
  2. **Benchmark Runner Panel**: Dropdowns for dataset selection, task filters, model gateway routing choices, driver selection, and execution trigger.
  3. **Live Trajectory Inspector**: Split screen showing latest screenshot, SoM annotation, sliding memory window (3 turns), model reasoning chain, and text action log.
  4. **Screenshot Diff Analytics Panel**: Side-by-side visual image comparison tool (Baseline vs Actual vs Diff Mask) with interactive metric sliders (SSIM, MSE, Pixel Diff %).

---

### 3.3 SQLite Database Schema (`omnibench.db`)

All benchmark telemetry, execution metadata, trajectories, and visual evaluation results are persisted to a structured SQLite database.

```sql
-- Database DDL Schema for omnibench.db

CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    dataset_name TEXT NOT NULL,
    model_name TEXT NOT NULL,
    driver_platform TEXT NOT NULL,
    total_tasks INTEGER DEFAULT 0,
    passed_tasks INTEGER DEFAULT 0,
    failed_tasks INTEGER DEFAULT 0,
    status TEXT NOT NULL CHECK (status IN ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED')),
    config_json TEXT
);

CREATE TABLE IF NOT EXISTS episodes (
    episode_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    instruction TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('PENDING', 'RUNNING', 'SUCCESS', 'FAILURE', 'ERROR')),
    start_time TEXT NOT NULL,
    end_time TEXT,
    total_steps INTEGER DEFAULT 0,
    error_message TEXT,
    FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS steps (
    step_id TEXT PRIMARY KEY,
    episode_id TEXT NOT NULL,
    step_number INTEGER NOT NULL,
    timestamp TEXT NOT NULL,
    action_type TEXT NOT NULL,
    action_params_json TEXT NOT NULL,
    model_raw_response TEXT,
    latency_ms REAL,
    screenshot_path TEXT,
    som_screenshot_path TEXT,
    FOREIGN KEY (episode_id) REFERENCES episodes(episode_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS screenshot_diffs (
    diff_id TEXT PRIMARY KEY,
    step_id TEXT NOT NULL,
    baseline_image_path TEXT NOT NULL,
    actual_image_path TEXT NOT NULL,
    diff_image_path TEXT NOT NULL,
    ssim_score REAL NOT NULL,
    mse_score REAL NOT NULL,
    pixel_diff_ratio REAL NOT NULL,
    is_match INTEGER NOT NULL CHECK (is_match IN (0, 1)),
    FOREIGN KEY (step_id) REFERENCES steps(step_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_episodes_run_id ON episodes(run_id);
CREATE INDEX IF NOT EXISTS idx_steps_episode_id ON steps(episode_id);
CREATE INDEX IF NOT EXISTS idx_diffs_step_id ON screenshot_diffs(step_id);
```

---

### 3.4 Screenshot Diff Analytics Engine Specification

Visual state evaluation requires comparing actual task output screenshots against reference golden screenshots.

#### Algorithms & Metrics

1. **Mean Squared Error (MSE)**:
   $$\text{MSE} = \frac{1}{W \times H \times C} \sum_{x,y,c} (I_1(x,y,c) - I_2(x,y,c))^2$$
   - Normalized range: $[0.0, \infty)$. Score of `0.0` represents an exact pixel match.

2. **Structural Similarity Index (SSIM)**:
   - Measures perceptual visual similarity considering luminance, contrast, and structure.
   - Range: $[-1.0, 1.0]$. Match threshold: $\ge 0.95$.

3. **Pixel Difference Ratio**:
   - Calculates percentage of pixels where absolute color delta $|\Delta RGB| > \text{threshold}$ (default threshold = 30).
   - Match threshold: $\le 0.02$ (less than 2% pixel area diff).

4. **Visual Diff Image Generator**:
   - Generates a visual diff mask image highlighting changed pixels in bright red overlay over a muted grayscale background of the baseline image.

---

## 4. Module & Directory Structure Proposal

```
omnibench/
├── __init__.py
├── cli/
│   ├── __init__.py
│   ├── main.py                # Primary `omnibench` CLI entry point (click)
│   ├── config_cmd.py          # Config management
│   ├── dataset_cmd.py         # Dataset inspection
│   ├── run_cmd.py             # Runner execution
│   ├── monitor_cmd.py         # Terminal live monitor
│   ├── db_cmd.py              # Database query tool
│   └── dashboard_cmd.py       # Web UI server launcher
├── drivers/
│   ├── __init__.py
│   ├── base.py                # BaseOSDriver, ActionPrimitive, ActionType, ActionResult
│   ├── exceptions.py          # Driver error hierarchy
│   ├── retry.py               # Exponential backoff decorator & reconnect logic
│   ├── windows.py             # WindowsOSDriver
│   ├── macos.py               # MacOSDriver
│   ├── linux.py               # LinuxOSDriver (X11, Wayland, Xvfb)
│   ├── android.py             # AndroidOSDriver (ADB / uiautomator)
│   └── ios.py                 # IOSDriver (simctl / WDA)
├── visual/
│   ├── __init__.py
│   ├── resizer.py             # Resizing & Grid Tiling
│   ├── converter.py           # RGB / Grayscale mode conversions
│   ├── memory.py              # 3-screenshot sliding window buffer
│   ├── som.py                 # Set-of-Marks generator & MarkMap coordinate lookup
│   └── diff.py                # Screenshot diff analytics (MSE, SSIM, Diff Mask)
├── dashboard/
│   ├── __init__.py
│   ├── server.py              # Dashboard API server & SSE broadcaster
│   ├── routes.py              # REST API routes
│   └── static/                # HTML5/JS/CSS frontend
├── db/
│   ├── __init__.py
│   ├── schema.py              # SQLite DDL schema runner
│   ├── repository.py          # Repository pattern for database access
│   └── connection.py          # SQLite connection manager
```

---

## 5. Verification & Test Plan Matrix

To verify implementation accuracy, the test suite will be organized into four tiers:

| Tier | Test Scope | Focus Area | Verification Method |
| :--- | :--- | :--- | :--- |
| **Tier 1: Unit Tests** | Data structures, Enums, Math, Schema | `ActionPrimitive` serialization, `MarkMap` coordinate conversions, MSE/SSIM math, SQLite DDL creation | Python `unittest` |
| **Tier 2: Component Integration** | Driver retries, Visual pipeline, DB repo | Mock driver error backoff, sliding window eviction after 3 steps, SQLite CRUD operations | Python `unittest` with mock objects |
| **Tier 3: Platform & Interface** | CLI commands, Web API endpoints, Drivers | `omnibench` CLI command execution, Web Dashboard API responses, Xvfb Linux driver primitive execution | CLI runner tests & HTTP client tests |
| **Tier 4: End-to-End System** | Complete pipeline trajectory | Full benchmark run: synthetic task -> SoM preprocessing -> driver click -> DB log -> Screenshot diff | E2E integration test script |

---

## 6. Conclusion

Requirements R2, R3, and R5 have been fully specified with concrete class interfaces, exception hierarchies, database schemas, image processing pipelines, CLI tools, web dashboard layouts, and tiered verification plans. Implementation agents can execute directly from this architecture specification without design ambiguity.
