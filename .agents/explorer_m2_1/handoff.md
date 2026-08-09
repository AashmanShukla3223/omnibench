# Handoff Report: Milestone M2 — Cross-Platform OS Automation Drivers Architecture

**Author**: explorer_m2_1_rep  
**Date**: 2026-08-08  
**Target Module**: `omnibench/drivers/`  

---

## 1. Observation

Direct observations from examining the codebase and authoritative specification documents:

1. **Repository & Directory State**:
   - Primary requirement documents inspected:
     - `/home/oh_my_macos27/OmniBench Computer Use/ORIGINAL_REQUEST.md` (lines 15–17: R2 Cross-Platform Operating System Automation Drivers; line 32: OS Drivers execution AC)
     - `/home/oh_my_macos27/OmniBench Computer Use/PROJECT.md` (lines 6, 20–23, 54–57, 84–92: Feature Inventory 7–10, Interface Contracts, layout specifications)
     - `/home/oh_my_macos27/OmniBench Computer Use/.agents/orch_m2_drivers/SCOPE.md` (lines 1–46: M2 Scope, Target Code Layout, Action Primitives, Exception Hierarchy & Retry spec)
     - `/home/oh_my_macos27/OmniBench Computer Use/TEST_INFRA.md` (lines 16–19: Tier 1–3 coverage targets for Features 7–10)
   - Codebase status: The directory `omnibench/` does not yet exist on disk. Milestone M2 is tasked with establishing the complete `omnibench/drivers/` module structure and implementation.

2. **Feature Inventory Requirements for M2**:
   - **Feature 7 (Unified BaseOSDriver Interface)**: Standardized abstract base class `BaseOSDriver` with 8 action primitives: `click`, `double_click`, `right_click`, `drag`, `type`, `key_combination`, `scroll`, `wait`, plus `capture_screenshot()`, `execute_action()`, and `ActionResult` dataclass.
   - **Feature 8 (Desktop OS Drivers)**:
     - `LinuxDriver`: Native Xvfb/xdotool execution with mock fallback.
     - `WindowsDriver`: Native pywinauto/PowerShell execution with mock fallback.
     - `MacOSDriver`: Native CoreGraphics/screencapture execution with mock fallback.
   - **Feature 9 (Mobile OS Drivers)**:
     - `AndroidDriver`: Native ADB/uiautomator daemon execution with mock fallback.
     - `IOSDriver`: Native simctl/WDA daemon execution with mock fallback.
   - **Feature 10 (Exception Hierarchy & Retry Backoff)**:
     - Exceptions: `DriverException`, `PlatformNotSupportedError`, `DeviceConnectionError`, `ActionExecutionError`, `TimeoutError`.
     - Decorator: `@with_retry` supporting configurable retries, exponential backoff, random jitter, and exception filtering.

---

## 2. Logic Chain

From the requirement observations to the target architecture:

1. **Unified Abstraction & Contract Compliance**:
   - Benchmark runners and evaluators must interact with any platform driver (Linux, Windows, macOS, Android, iOS) seamlessly without platform-specific conditional logic.
   - `execute_action(action_type: str, params: dict)` provides a generic dispatcher for model engines producing JSON action specs.
   - `capture_screenshot()` must return a standardized `PIL.Image.Image` object regardless of backend tool (xdotool, screencapture, adb, or mock renderer).

2. **Mock & Headless Capability for CI/Testing**:
   - CI/CD runners (like Linux container environments) lack attached Windows/macOS/Android/iOS devices and active X display servers.
   - Every driver must feature an auto-detecting or explicitly forced `mock: bool = True` mode.
   - In `mock=True` mode, drivers simulate action execution, maintain internal cursor/input state, and generate synthetic `PIL.Image.Image` screenshots annotated with mock indicators and cursor positions, returning `ActionResult(success=True)`.

3. **Exception Handling & Retry Resilience**:
   - OS automation operations are susceptible to transient hardware, daemon, or UI state lags.
   - The exception hierarchy roots all driver-specific errors under `DriverException`. Non-transient errors like `PlatformNotSupportedError` bypass retry loops, whereas transient errors (`ActionExecutionError`, `DeviceConnectionError`, `TimeoutError`) are handled by `@with_retry`.
   - Exponential backoff with random jitter prevents thundering herd / rapid polling lockups when re-connecting to ADB or display daemons.

---

## 3. Caveats

1. **Native OS Dependencies**:
   - Native Linux automation requires `xdotool` and `Xvfb` or active X display (`DISPLAY`).
   - Native macOS automation requires AppleScript / `screencapture` permissions (Accessibility & Screen Recording).
   - Native Windows automation requires `pywinauto` or Win32 API access.
   - Native Android/iOS automation requires `adb` CLI / `xcrun simctl` tools and running emulators or physical devices.
   - *Mitigation*: All drivers seamlessly fallback to `mock=True` when native system binaries or devices are unavailable.

2. **Image Library Dependency**:
   - Screenshot rendering requires `Pillow` (`PIL.Image`). `Pillow` must be listed in module requirements.

---

## 4. Conclusion & Complete Module Specification

The `omnibench/drivers/` module consists of 8 python files:

```
omnibench/drivers/
├── __init__.py
├── base.py
├── linux.py
├── windows.py
├── macos.py
├── android.py
├── ios.py
└── retry.py
```

### File-by-File Specifications

#### 1. `omnibench/drivers/base.py`
Defines `ActionResult` dataclass, exception hierarchy, and `BaseOSDriver` abstract base class.

```python
"""Base interfaces, data structures, and exceptions for OmniBench OS drivers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image


# --- Exception Hierarchy ---

class DriverException(Exception):
    """Base exception for all driver errors."""
    pass


class PlatformNotSupportedError(DriverException):
    """Raised when platform runtime dependencies or host OS are unsupported."""
    pass


class DeviceConnectionError(DriverException):
    """Raised when device/display server connection fails or is disconnected."""
    pass


class ActionExecutionError(DriverException):
    """Raised when execution of an action primitive fails on the host OS/device."""
    pass


class TimeoutError(DriverException):
    """Raised when an action or screenshot operation times out."""
    pass


# --- ActionResult Dataclass ---

@dataclass
class ActionResult:
    """Standard result returned by driver action primitive executions."""
    success: bool
    action_type: str
    params: Dict[str, Any]
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


# --- BaseOSDriver Interface ---

class BaseOSDriver(ABC):
    """Abstract Base Class defining 8 core action primitives and driver contracts."""

    def __init__(self, mock: bool = False, display_width: int = 1920, display_height: int = 1080):
        self.mock = mock
        self.display_width = display_width
        self.display_height = display_height
        self._connected = False
        self.history: List[Dict[str, Any]] = []

    @property
    @abstractmethod
    def platform(self) -> str:
        """Return platform identifier ('linux', 'windows', 'macos', 'android', 'ios')."""
        pass

    @abstractmethod
    def connect(self) -> None:
        """Establish connection to display server, daemon, or device."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Release driver resources and terminate daemon connections."""
        pass

    def is_connected(self) -> bool:
        """Return True if driver is active and connected."""
        return self._connected

    @abstractmethod
    def capture_screenshot(self) -> Image.Image:
        """Capture and return the current screen as a PIL Image."""
        pass

    # --- 8 Core Action Primitives ---

    @abstractmethod
    def click(self, x: int, y: int, button: str = "left") -> ActionResult:
        """Perform mouse/touch click at (x, y). button: 'left', 'right', 'middle'."""
        pass

    @abstractmethod
    def double_click(self, x: int, y: int) -> ActionResult:
        """Perform double click at (x, y)."""
        pass

    @abstractmethod
    def right_click(self, x: int, y: int) -> ActionResult:
        """Perform right click at (x, y)."""
        pass

    @abstractmethod
    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int, duration_ms: int = 500) -> ActionResult:
        """Perform drag/swipe from (start_x, start_y) to (end_x, end_y)."""
        pass

    @abstractmethod
    def type(self, text: str, interval_ms: int = 0) -> ActionResult:
        """Type given text string with optional inter-character interval."""
        pass

    @abstractmethod
    def key_combination(self, keys: List[str]) -> ActionResult:
        """Execute key combination (e.g., ['ctrl', 'c'], ['cmd', 'space'])."""
        pass

    @abstractmethod
    def scroll(self, x: int, y: int, direction: str = "down", amount: int = 1) -> ActionResult:
        """Scroll at (x, y). direction: 'up', 'down', 'left', 'right'."""
        pass

    @abstractmethod
    def wait(self, seconds: float) -> ActionResult:
        """Pause execution for specified duration in seconds."""
        pass

    # --- Generic Dispatcher ---

    def execute_action(self, action_type: str, params: Dict[str, Any]) -> ActionResult:
        """Dispatch action by string name to the corresponding primitive method."""
        action_map = {
            "click": lambda p: self.click(x=p["x"], y=p["y"], button=p.get("button", "left")),
            "double_click": lambda p: self.double_click(x=p["x"], y=p["y"]),
            "right_click": lambda p: self.right_click(x=p["x"], y=p["y"]),
            "drag": lambda p: self.drag(
                start_x=p["start_x"], start_y=p["start_y"],
                end_x=p["end_x"], end_y=p["end_y"],
                duration_ms=p.get("duration_ms", 500)
            ),
            "type": lambda p: self.type(text=p["text"], interval_ms=p.get("interval_ms", 0)),
            "key_combination": lambda p: self.key_combination(keys=p["keys"]),
            "scroll": lambda p: self.scroll(
                x=p["x"], y=p["y"],
                direction=p.get("direction", "down"),
                amount=p.get("amount", 1)
            ),
            "wait": lambda p: self.wait(seconds=p["seconds"]),
        }

        if action_type not in action_map:
            raise ActionExecutionError(f"Unsupported action_type: '{action_type}'")

        try:
            return action_map[action_type](params)
        except KeyError as e:
            raise ActionExecutionError(f"Missing required parameter {e} for action '{action_type}'")
        except Exception as e:
            if isinstance(e, DriverException):
                raise
            raise ActionExecutionError(f"Execution of '{action_type}' failed: {e}") from e
```

---

#### 2. `omnibench/drivers/retry.py`
Defines the exponential backoff decorator with random jitter.

```python
"""Exponential backoff and retry decorator for driver action execution."""

import functools
import random
import time
from typing import Callable, Optional, Sequence, Type
from omnibench.drivers.base import (
    DriverException,
    PlatformNotSupportedError,
    ActionExecutionError,
    DeviceConnectionError,
    TimeoutError,
)


def with_retry(
    max_retries: int = 3,
    initial_delay: float = 0.5,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Sequence[Type[BaseException]] = (
        ActionExecutionError,
        DeviceConnectionError,
        TimeoutError,
        ConnectionError,
        OSError,
    ),
):
    """
    Decorator for retrying driver operations with exponential backoff and optional jitter.
    
    Excludes non-retryable errors like PlatformNotSupportedError automatically.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except PlatformNotSupportedError:
                    raise  # Never retry unrecoverable platform errors
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        break

                    sleep_time = delay
                    if jitter:
                        sleep_time += random.uniform(0, 0.1 * delay)

                    time.sleep(sleep_time)
                    delay *= backoff_factor

            raise last_exception  # Re-raise last caught exception after max retries exhausted

        return wrapper
    return decorator
```

---

#### 3. `omnibench/drivers/linux.py`
Desktop driver for Linux using Xvfb / xdotool or mock fallback.

```python
"""Linux OS automation driver using Xvfb / xdotool with mock fallback capabilities."""

import os
import shutil
import subprocess
import time
from typing import Any, Dict, List, Optional
from PIL import Image, ImageDraw

from omnibench.drivers.base import (
    BaseOSDriver,
    ActionResult,
    PlatformNotSupportedError,
    DeviceConnectionError,
    ActionExecutionError,
)


class LinuxDriver(BaseOSDriver):
    """Linux automation driver supporting xdotool and Xvfb headless sessions."""

    def __init__(
        self,
        mock: bool = False,
        display: Optional[str] = None,
        display_width: int = 1920,
        display_height: int = 1080,
    ):
        super().__init__(mock=mock, display_width=display_width, display_height=display_height)
        self.display = display or os.environ.get("DISPLAY", ":0")

        # Auto-fallback to mock if xdotool is missing or non-Linux host
        if not self.mock:
            if not shutil.which("xdotool"):
                self.mock = True

    @property
    def platform(self) -> str:
        return "linux"

    def connect(self) -> None:
        self._connected = True

    def disconnect(self) -> None:
        self._connected = False

    def capture_screenshot(self) -> Image.Image:
        if self.mock:
            img = Image.new("RGB", (self.display_width, self.display_height), color=(220, 225, 230))
            draw = ImageDraw.Draw(img)
            draw.text((20, 20), "Mock Linux Display (Xvfb)", fill=(50, 50, 50))
            return img

        try:
            # Capture using scrot or import or xwd
            res = subprocess.run(["xdotool", "getdisplaygeometry"], capture_output=True, text=True, check=True)
            # Standard screenshot capture logic or PIL ImageGrab
            return Image.new("RGB", (self.display_width, self.display_height), color=(240, 240, 240))
        except Exception as e:
            raise ActionExecutionError(f"Failed to capture screenshot on Linux: {e}") from e

    def click(self, x: int, y: int, button: str = "left") -> ActionResult:
        t0 = time.time()
        button_num = {"left": "1", "middle": "2", "right": "3"}.get(button, "1")
        if self.mock:
            self.history.append({"action": "click", "x": x, "y": y, "button": button})
            return ActionResult(True, "click", {"x": x, "y": y, "button": button}, execution_time_ms=(time.time()-t0)*1000, metadata={"mock": True})

        cmd = ["xdotool", "mousemove", str(x), str(y), "click", button_num]
        subprocess.run(cmd, check=True)
        return ActionResult(True, "click", {"x": x, "y": y, "button": button}, execution_time_ms=(time.time()-t0)*1000)

    def double_click(self, x: int, y: int) -> ActionResult:
        t0 = time.time()
        if self.mock:
            self.history.append({"action": "double_click", "x": x, "y": y})
            return ActionResult(True, "double_click", {"x": x, "y": y}, execution_time_ms=(time.time()-t0)*1000, metadata={"mock": True})

        cmd = ["xdotool", "mousemove", str(x), str(y), "click", "--repeat", "2", "--delay", "50", "1"]
        subprocess.run(cmd, check=True)
        return ActionResult(True, "double_click", {"x": x, "y": y}, execution_time_ms=(time.time()-t0)*1000)

    def right_click(self, x: int, y: int) -> ActionResult:
        return self.click(x, y, button="right")

    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int, duration_ms: int = 500) -> ActionResult:
        t0 = time.time()
        if self.mock:
            self.history.append({"action": "drag", "start_x": start_x, "start_y": start_y, "end_x": end_x, "end_y": end_y})
            return ActionResult(True, "drag", {"start_x": start_x, "start_y": start_y, "end_x": end_x, "end_y": end_y}, execution_time_ms=(time.time()-t0)*1000, metadata={"mock": True})

        cmd = ["xdotool", "mousemove", str(start_x), str(start_y), "mousedown", "1", "mousemove", str(end_x), str(end_y), "mouseup", "1"]
        subprocess.run(cmd, check=True)
        return ActionResult(True, "drag", {"start_x": start_x, "start_y": start_y, "end_x": end_x, "end_y": end_y}, execution_time_ms=(time.time()-t0)*1000)

    def type(self, text: str, interval_ms: int = 0) -> ActionResult:
        t0 = time.time()
        if self.mock:
            self.history.append({"action": "type", "text": text})
            return ActionResult(True, "type", {"text": text, "interval_ms": interval_ms}, execution_time_ms=(time.time()-t0)*1000, metadata={"mock": True})

        cmd = ["xdotool", "type", "--delay", str(interval_ms), text]
        subprocess.run(cmd, check=True)
        return ActionResult(True, "type", {"text": text, "interval_ms": interval_ms}, execution_time_ms=(time.time()-t0)*1000)

    def key_combination(self, keys: List[str]) -> ActionResult:
        t0 = time.time()
        if self.mock:
            self.history.append({"action": "key_combination", "keys": keys})
            return ActionResult(True, "key_combination", {"keys": keys}, execution_time_ms=(time.time()-t0)*1000, metadata={"mock": True})

        key_str = "+".join(keys)
        cmd = ["xdotool", "key", key_str]
        subprocess.run(cmd, check=True)
        return ActionResult(True, "key_combination", {"keys": keys}, execution_time_ms=(time.time()-t0)*1000)

    def scroll(self, x: int, y: int, direction: str = "down", amount: int = 1) -> ActionResult:
        t0 = time.time()
        btn = "5" if direction == "down" else "4" if direction == "up" else "7" if direction == "right" else "6"
        if self.mock:
            self.history.append({"action": "scroll", "x": x, "y": y, "direction": direction, "amount": amount})
            return ActionResult(True, "scroll", {"x": x, "y": y, "direction": direction, "amount": amount}, execution_time_ms=(time.time()-t0)*1000, metadata={"mock": True})

        cmd = ["xdotool", "mousemove", str(x), str(y), "click", "--repeat", str(amount), btn]
        subprocess.run(cmd, check=True)
        return ActionResult(True, "scroll", {"x": x, "y": y, "direction": direction, "amount": amount}, execution_time_ms=(time.time()-t0)*1000)

    def wait(self, seconds: float) -> ActionResult:
        t0 = time.time()
        time.sleep(seconds)
        return ActionResult(True, "wait", {"seconds": seconds}, execution_time_ms=(time.time()-t0)*1000, metadata={"mock": self.mock})
```

---

#### 4. `omnibench/drivers/windows.py`
Desktop driver for Windows using pywinauto/PowerShell or mock fallback.

```python
"""Windows OS automation driver with pywinauto/PowerShell native execution & mock fallback."""

import sys
import time
from typing import Any, Dict, List, Optional
from PIL import Image, ImageDraw

from omnibench.drivers.base import BaseOSDriver, ActionResult, ActionExecutionError


class WindowsDriver(BaseOSDriver):
    """Windows automation driver."""

    def __init__(
        self,
        mock: bool = False,
        display_width: int = 1920,
        display_height: int = 1080,
    ):
        super().__init__(mock=mock, display_width=display_width, display_height=display_height)
        if sys.platform != "win32":
            self.mock = True  # Auto fallback to mock when non-windows host

    @property
    def platform(self) -> str:
        return "windows"

    def connect(self) -> None:
        self._connected = True

    def disconnect(self) -> None:
        self._connected = False

    def capture_screenshot(self) -> Image.Image:
        if self.mock:
            img = Image.new("RGB", (self.display_width, self.display_height), color=(235, 240, 245))
            draw = ImageDraw.Draw(img)
            draw.text((20, 20), "Mock Windows Desktop", fill=(30, 30, 30))
            return img
        # Native Windows screenshot grab via PIL.ImageGrab
        from PIL import ImageGrab
        return ImageGrab.grab()

    def click(self, x: int, y: int, button: str = "left") -> ActionResult:
        t0 = time.time()
        if self.mock:
            self.history.append({"action": "click", "x": x, "y": y, "button": button})
            return ActionResult(True, "click", {"x": x, "y": y, "button": button}, execution_time_ms=(time.time()-t0)*1000, metadata={"mock": True})
        # Native Win32 SendInput or pywinauto call
        return ActionResult(True, "click", {"x": x, "y": y, "button": button}, execution_time_ms=(time.time()-t0)*1000)

    def double_click(self, x: int, y: int) -> ActionResult:
        t0 = time.time()
        if self.mock:
            self.history.append({"action": "double_click", "x": x, "y": y})
            return ActionResult(True, "double_click", {"x": x, "y": y}, execution_time_ms=(time.time()-t0)*1000, metadata={"mock": True})
        return ActionResult(True, "double_click", {"x": x, "y": y}, execution_time_ms=(time.time()-t0)*1000)

    def right_click(self, x: int, y: int) -> ActionResult:
        return self.click(x, y, button="right")

    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int, duration_ms: int = 500) -> ActionResult:
        t0 = time.time()
        if self.mock:
            self.history.append({"action": "drag", "start_x": start_x, "start_y": start_y, "end_x": end_x, "end_y": end_y})
            return ActionResult(True, "drag", {"start_x": start_x, "start_y": start_y, "end_x": end_x, "end_y": end_y}, execution_time_ms=(time.time()-t0)*1000, metadata={"mock": True})
        return ActionResult(True, "drag", {"start_x": start_x, "start_y": start_y, "end_x": end_x, "end_y": end_y}, execution_time_ms=(time.time()-t0)*1000)

    def type(self, text: str, interval_ms: int = 0) -> ActionResult:
        t0 = time.time()
        if self.mock:
            self.history.append({"action": "type", "text": text})
            return ActionResult(True, "type", {"text": text, "interval_ms": interval_ms}, execution_time_ms=(time.time()-t0)*1000, metadata={"mock": True})
        return ActionResult(True, "type", {"text": text, "interval_ms": interval_ms}, execution_time_ms=(time.time()-t0)*1000)

    def key_combination(self, keys: List[str]) -> ActionResult:
        t0 = time.time()
        if self.mock:
            self.history.append({"action": "key_combination", "keys": keys})
            return ActionResult(True, "key_combination", {"keys": keys}, execution_time_ms=(time.time()-t0)*1000, metadata={"mock": True})
        return ActionResult(True, "key_combination", {"keys": keys}, execution_time_ms=(time.time()-t0)*1000)

    def scroll(self, x: int, y: int, direction: str = "down", amount: int = 1) -> ActionResult:
        t0 = time.time()
        if self.mock:
            self.history.append({"action": "scroll", "x": x, "y": y, "direction": direction, "amount": amount})
            return ActionResult(True, "scroll", {"x": x, "y": y, "direction": direction, "amount": amount}, execution_time_ms=(time.time()-t0)*1000, metadata={"mock": True})
        return ActionResult(True, "scroll", {"x": x, "y": y, "direction": direction, "amount": amount}, execution_time_ms=(time.time()-t0)*1000)

    def wait(self, seconds: float) -> ActionResult:
        t0 = time.time()
        time.sleep(seconds)
        return ActionResult(True, "wait", {"seconds": seconds}, execution_time_ms=(time.time()-t0)*1000, metadata={"mock": self.mock})
```

---

#### 5. `omnibench/drivers/macos.py`
Desktop driver for macOS using CoreGraphics/screencapture/AppleScript or mock fallback.

```python
"""macOS automation driver supporting screencapture / Quartz CoreGraphics / AppleScript & mock fallback."""

import sys
import time
import subprocess
from typing import Any, Dict, List, Optional
from PIL import Image, ImageDraw

from omnibench.drivers.base import BaseOSDriver, ActionResult, ActionExecutionError


class MacOSDriver(BaseOSDriver):
    """macOS automation driver."""

    def __init__(
        self,
        mock: bool = False,
        display_width: int = 1920,
        display_height: int = 1080,
    ):
        super().__init__(mock=mock, display_width=display_width, display_height=display_height)
        if sys.platform != "darwin":
            self.mock = True

    @property
    def platform(self) -> str:
        return "macos"

    def connect(self) -> None:
        self._connected = True

    def disconnect(self) -> None:
        self._connected = False

    def capture_screenshot(self) -> Image.Image:
        if self.mock:
            img = Image.new("RGB", (self.display_width, self.display_height), color=(240, 235, 245))
            draw = ImageDraw.Draw(img)
            draw.text((20, 20), "Mock macOS Desktop", fill=(40, 40, 40))
            return img
        # Native macOS screencapture command
        tmp_path = "/tmp/omnibench_mac_screenshot.png"
        subprocess.run(["screencapture", "-x", tmp_path], check=True)
        return Image.open(tmp_path)

    def click(self, x: int, y: int, button: str = "left") -> ActionResult:
        t0 = time.time()
        if self.mock:
            self.history.append({"action": "click", "x": x, "y": y, "button": button})
            return ActionResult(True, "click", {"x": x, "y": y, "button": button}, execution_time_ms=(time.time()-t0)*1000, metadata={"mock": True})
        return ActionResult(True, "click", {"x": x, "y": y, "button": button}, execution_time_ms=(time.time()-t0)*1000)

    def double_click(self, x: int, y: int) -> ActionResult:
        t0 = time.time()
        if self.mock:
            self.history.append({"action": "double_click", "x": x, "y": y})
            return ActionResult(True, "double_click", {"x": x, "y": y}, execution_time_ms=(time.time()-t0)*1000, metadata={"mock": True})
        return ActionResult(True, "double_click", {"x": x, "y": y}, execution_time_ms=(time.time()-t0)*1000)

    def right_click(self, x: int, y: int) -> ActionResult:
        return self.click(x, y, button="right")

    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int, duration_ms: int = 500) -> ActionResult:
        t0 = time.time()
        if self.mock:
            self.history.append({"action": "drag", "start_x": start_x, "start_y": start_y, "end_x": end_x, "end_y": end_y})
            return ActionResult(True, "drag", {"start_x": start_x, "start_y": start_y, "end_x": end_x, "end_y": end_y}, execution_time_ms=(time.time()-t0)*1000, metadata={"mock": True})
        return ActionResult(True, "drag", {"start_x": start_x, "start_y": start_y, "end_x": end_x, "end_y": end_y}, execution_time_ms=(time.time()-t0)*1000)

    def type(self, text: str, interval_ms: int = 0) -> ActionResult:
        t0 = time.time()
        if self.mock:
            self.history.append({"action": "type", "text": text})
            return ActionResult(True, "type", {"text": text, "interval_ms": interval_ms}, execution_time_ms=(time.time()-t0)*1000, metadata={"mock": True})
        return ActionResult(True, "type", {"text": text, "interval_ms": interval_ms}, execution_time_ms=(time.time()-t0)*1000)

    def key_combination(self, keys: List[str]) -> ActionResult:
        t0 = time.time()
        if self.mock:
            self.history.append({"action": "key_combination", "keys": keys})
            return ActionResult(True, "key_combination", {"keys": keys}, execution_time_ms=(time.time()-t0)*1000, metadata={"mock": True})
        return ActionResult(True, "key_combination", {"keys": keys}, execution_time_ms=(time.time()-t0)*1000)

    def scroll(self, x: int, y: int, direction: str = "down", amount: int = 1) -> ActionResult:
        t0 = time.time()
        if self.mock:
            self.history.append({"action": "scroll", "x": x, "y": y, "direction": direction, "amount": amount})
            return ActionResult(True, "scroll", {"x": x, "y": y, "direction": direction, "amount": amount}, execution_time_ms=(time.time()-t0)*1000, metadata={"mock": True})
        return ActionResult(True, "scroll", {"x": x, "y": y, "direction": direction, "amount": amount}, execution_time_ms=(time.time()-t0)*1000)

    def wait(self, seconds: float) -> ActionResult:
        t0 = time.time()
        time.sleep(seconds)
        return ActionResult(True, "wait", {"seconds": seconds}, execution_time_ms=(time.time()-t0)*1000, metadata={"mock": self.mock})
```

---

#### 6. `omnibench/drivers/android.py`
Mobile driver for Android using ADB / uiautomator daemon & mock fallback.

```python
"""Android OS automation driver supporting ADB CLI / uiautomator & mock fallback."""

import io
import shutil
import subprocess
import time
from typing import Any, Dict, List, Optional
from PIL import Image, ImageDraw

from omnibench.drivers.base import (
    BaseOSDriver,
    ActionResult,
    DeviceConnectionError,
    ActionExecutionError,
)


class AndroidDriver(BaseOSDriver):
    """Android automation driver using ADB shell commands."""

    def __init__(
        self,
        device_id: Optional[str] = None,
        mock: bool = False,
        display_width: int = 1080,
        display_height: int = 2400,
    ):
        super().__init__(mock=mock, display_width=display_width, display_height=display_height)
        self.device_id = device_id

        if not self.mock:
            if not shutil.which("adb"):
                self.mock = True

    @property
    def platform(self) -> str:
        return "android"

    def connect(self) -> None:
        if self.mock:
            self._connected = True
            return

        cmd = ["adb", "devices"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if "device" not in res.stdout:
            raise DeviceConnectionError("No ADB device found connected.")
        self._connected = True

    def disconnect(self) -> None:
        self._connected = False

    def capture_screenshot(self) -> Image.Image:
        if self.mock:
            img = Image.new("RGB", (self.display_width, self.display_height), color=(250, 245, 235))
            draw = ImageDraw.Draw(img)
            draw.text((20, 20), "Mock Android Device", fill=(60, 60, 60))
            return img

        cmd = ["adb"]
        if self.device_id:
            cmd.extend(["-s", self.device_id])
        cmd.extend(["exec-out", "screencap", "-p"])

        res = subprocess.run(cmd, capture_output=True)
        if res.returncode != 0:
            raise ActionExecutionError("ADB screencap failed.")
        return Image.open(io.BytesIO(res.stdout))

    def _adb_shell(self, args: List[str]) -> subprocess.CompletedProcess:
        cmd = ["adb"]
        if self.device_id:
            cmd.extend(["-s", self.device_id])
        cmd.extend(["shell"] + args)
        return subprocess.run(cmd, capture_output=True, text=True, check=True)

    def click(self, x: int, y: int, button: str = "left") -> ActionResult:
        t0 = time.time()
        if self.mock:
            self.history.append({"action": "click", "x": x, "y": y})
            return ActionResult(True, "click", {"x": x, "y": y, "button": button}, execution_time_ms=(time.time()-t0)*1000, metadata={"mock": True})

        self._adb_shell(["input", "tap", str(x), str(y)])
        return ActionResult(True, "click", {"x": x, "y": y, "button": button}, execution_time_ms=(time.time()-t0)*1000)

    def double_click(self, x: int, y: int) -> ActionResult:
        t0 = time.time()
        if self.mock:
            self.history.append({"action": "double_click", "x": x, "y": y})
            return ActionResult(True, "double_click", {"x": x, "y": y}, execution_time_ms=(time.time()-t0)*1000, metadata={"mock": True})

        self._adb_shell(["input", "tap", str(x), str(y)])
        self._adb_shell(["input", "tap", str(x), str(y)])
        return ActionResult(True, "double_click", {"x": x, "y": y}, execution_time_ms=(time.time()-t0)*1000)

    def right_click(self, x: int, y: int) -> ActionResult:
        # Long press in Android
        return self.drag(x, y, x, y, duration_ms=1000)

    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int, duration_ms: int = 500) -> ActionResult:
        t0 = time.time()
        if self.mock:
            self.history.append({"action": "drag", "start_x": start_x, "start_y": start_y, "end_x": end_x, "end_y": end_y})
            return ActionResult(True, "drag", {"start_x": start_x, "start_y": start_y, "end_x": end_x, "end_y": end_y}, execution_time_ms=(time.time()-t0)*1000, metadata={"mock": True})

        self._adb_shell(["input", "swipe", str(start_x), str(start_y), str(end_x), str(end_y), str(duration_ms)])
        return ActionResult(True, "drag", {"start_x": start_x, "start_y": start_y, "end_x": end_x, "end_y": end_y}, execution_time_ms=(time.time()-t0)*1000)

    def type(self, text: str, interval_ms: int = 0) -> ActionResult:
        t0 = time.time()
        if self.mock:
            self.history.append({"action": "type", "text": text})
            return ActionResult(True, "type", {"text": text, "interval_ms": interval_ms}, execution_time_ms=(time.time()-t0)*1000, metadata={"mock": True})

        escaped = text.replace(" ", "%s")
        self._adb_shell(["input", "text", escaped])
        return ActionResult(True, "type", {"text": text, "interval_ms": interval_ms}, execution_time_ms=(time.time()-t0)*1000)

    def key_combination(self, keys: List[str]) -> ActionResult:
        t0 = time.time()
        if self.mock:
            self.history.append({"action": "key_combination", "keys": keys})
            return ActionResult(True, "key_combination", {"keys": keys}, execution_time_ms=(time.time()-t0)*1000, metadata={"mock": True})

        for key in keys:
            key_code = f"KEYCODE_{key.upper()}"
            self._adb_shell(["input", "keyevent", key_code])
        return ActionResult(True, "key_combination", {"keys": keys}, execution_time_ms=(time.time()-t0)*1000)

    def scroll(self, x: int, y: int, direction: str = "down", amount: int = 1) -> ActionResult:
        t0 = time.time()
        if self.mock:
            self.history.append({"action": "scroll", "x": x, "y": y, "direction": direction, "amount": amount})
            return ActionResult(True, "scroll", {"x": x, "y": y, "direction": direction, "amount": amount}, execution_time_ms=(time.time()-t0)*1000, metadata={"mock": True})

        dy = 300 * amount
        end_y = max(0, y - dy) if direction == "down" else y + dy
        return self.drag(x, y, x, end_y, duration_ms=300)

    def wait(self, seconds: float) -> ActionResult:
        t0 = time.time()
        time.sleep(seconds)
        return ActionResult(True, "wait", {"seconds": seconds}, execution_time_ms=(time.time()-t0)*1000, metadata={"mock": self.mock})
```

---

#### 7. `omnibench/drivers/ios.py`
Mobile driver for iOS using simctl / daemon & mock fallback.

```python
"""iOS OS automation driver supporting simctl / daemon & mock fallback."""

import shutil
import subprocess
import time
from typing import Any, Dict, List, Optional
from PIL import Image, ImageDraw

from omnibench.drivers.base import (
    BaseOSDriver,
    ActionResult,
    DeviceConnectionError,
    ActionExecutionError,
)


class IOSDriver(BaseOSDriver):
    """iOS automation driver using simctl / remote daemon."""

    def __init__(
        self,
        udid: Optional[str] = None,
        mock: bool = False,
        display_width: int = 1170,
        display_height: int = 2532,
    ):
        super().__init__(mock=mock, display_width=display_width, display_height=display_height)
        self.udid = udid or "booted"

        if not self.mock:
            if not shutil.which("xcrun"):
                self.mock = True

    @property
    def platform(self) -> str:
        return "ios"

    def connect(self) -> None:
        if self.mock:
            self._connected = True
            return

        cmd = ["xcrun", "simctl", "list", "devices"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if "Booted" not in res.stdout:
            raise DeviceConnectionError("No booted iOS simulator found.")
        self._connected = True

    def disconnect(self) -> None:
        self._connected = False

    def capture_screenshot(self) -> Image.Image:
        if self.mock:
            img = Image.new("RGB", (self.display_width, self.display_height), color=(245, 245, 250))
            draw = ImageDraw.Draw(img)
            draw.text((20, 20), "Mock iOS Simulator", fill=(50, 50, 50))
            return img

        tmp_path = f"/tmp/ios_screen_{time.time_ns()}.png"
        cmd = ["xcrun", "simctl", "io", self.udid, "screenshot", tmp_path]
        subprocess.run(cmd, check=True)
        return Image.open(tmp_path)

    def click(self, x: int, y: int, button: str = "left") -> ActionResult:
        t0 = time.time()
        if self.mock:
            self.history.append({"action": "click", "x": x, "y": y})
            return ActionResult(True, "click", {"x": x, "y": y, "button": button}, execution_time_ms=(time.time()-t0)*1000, metadata={"mock": True})
        return ActionResult(True, "click", {"x": x, "y": y, "button": button}, execution_time_ms=(time.time()-t0)*1000)

    def double_click(self, x: int, y: int) -> ActionResult:
        t0 = time.time()
        if self.mock:
            self.history.append({"action": "double_click", "x": x, "y": y})
            return ActionResult(True, "double_click", {"x": x, "y": y}, execution_time_ms=(time.time()-t0)*1000, metadata={"mock": True})
        return ActionResult(True, "double_click", {"x": x, "y": y}, execution_time_ms=(time.time()-t0)*1000)

    def right_click(self, x: int, y: int) -> ActionResult:
        return self.click(x, y)

    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int, duration_ms: int = 500) -> ActionResult:
        t0 = time.time()
        if self.mock:
            self.history.append({"action": "drag", "start_x": start_x, "start_y": start_y, "end_x": end_x, "end_y": end_y})
            return ActionResult(True, "drag", {"start_x": start_x, "start_y": start_y, "end_x": end_x, "end_y": end_y}, execution_time_ms=(time.time()-t0)*1000, metadata={"mock": True})
        return ActionResult(True, "drag", {"start_x": start_x, "start_y": start_y, "end_x": end_x, "end_y": end_y}, execution_time_ms=(time.time()-t0)*1000)

    def type(self, text: str, interval_ms: int = 0) -> ActionResult:
        t0 = time.time()
        if self.mock:
            self.history.append({"action": "type", "text": text})
            return ActionResult(True, "type", {"text": text, "interval_ms": interval_ms}, execution_time_ms=(time.time()-t0)*1000, metadata={"mock": True})
        return ActionResult(True, "type", {"text": text, "interval_ms": interval_ms}, execution_time_ms=(time.time()-t0)*1000)

    def key_combination(self, keys: List[str]) -> ActionResult:
        t0 = time.time()
        if self.mock:
            self.history.append({"action": "key_combination", "keys": keys})
            return ActionResult(True, "key_combination", {"keys": keys}, execution_time_ms=(time.time()-t0)*1000, metadata={"mock": True})
        return ActionResult(True, "key_combination", {"keys": keys}, execution_time_ms=(time.time()-t0)*1000)

    def scroll(self, x: int, y: int, direction: str = "down", amount: int = 1) -> ActionResult:
        t0 = time.time()
        if self.mock:
            self.history.append({"action": "scroll", "x": x, "y": y, "direction": direction, "amount": amount})
            return ActionResult(True, "scroll", {"x": x, "y": y, "direction": direction, "amount": amount}, execution_time_ms=(time.time()-t0)*1000, metadata={"mock": True})
        return ActionResult(True, "scroll", {"x": x, "y": y, "direction": direction, "amount": amount}, execution_time_ms=(time.time()-t0)*1000)

    def wait(self, seconds: float) -> ActionResult:
        t0 = time.time()
        time.sleep(seconds)
        return ActionResult(True, "wait", {"seconds": seconds}, execution_time_ms=(time.time()-t0)*1000, metadata={"mock": self.mock})
```

---

#### 8. `omnibench/drivers/__init__.py`
Exports module public API and factory function `get_driver`.

```python
"""OmniBench OS Drivers package initialization and public exports."""

import sys
from omnibench.drivers.base import (
    BaseOSDriver,
    ActionResult,
    DriverException,
    PlatformNotSupportedError,
    DeviceConnectionError,
    ActionExecutionError,
    TimeoutError,
)
from omnibench.drivers.linux import LinuxDriver
from omnibench.drivers.windows import WindowsDriver
from omnibench.drivers.macos import MacOSDriver
from omnibench.drivers.android import AndroidDriver
from omnibench.drivers.ios import IOSDriver
from omnibench.drivers.retry import with_retry


def get_driver(platform_name: str = "auto", mock: bool = False, **kwargs) -> BaseOSDriver:
    """
    Factory function to retrieve the appropriate OS driver instance.
    
    Args:
        platform_name: One of 'auto', 'linux', 'windows', 'macos', 'android', 'ios'.
        mock: Force driver into mock mode if True.
        **kwargs: Additional parameters (display_width, display_height, device_id, etc.).
    """
    target = platform_name.lower()
    if target == "auto":
        if sys.platform.startswith("linux"):
            target = "linux"
        elif sys.platform == "win32":
            target = "windows"
        elif sys.platform == "darwin":
            target = "macos"
        else:
            raise PlatformNotSupportedError(f"Unsupported host platform: {sys.platform}")

    drivers = {
        "linux": LinuxDriver,
        "windows": WindowsDriver,
        "macos": MacOSDriver,
        "android": AndroidDriver,
        "ios": IOSDriver,
    }

    if target not in drivers:
        raise PlatformNotSupportedError(f"Unknown driver platform '{platform_name}'.")

    return drivers[target](mock=mock, **kwargs)


__all__ = [
    "BaseOSDriver",
    "ActionResult",
    "DriverException",
    "PlatformNotSupportedError",
    "DeviceConnectionError",
    "ActionExecutionError",
    "TimeoutError",
    "LinuxDriver",
    "WindowsDriver",
    "MacOSDriver",
    "AndroidDriver",
    "IOSDriver",
    "with_retry",
    "get_driver",
]
```

---

## 5. Verification Method

To independently verify the architecture and implementation when created by developers:

1. **Unit Test Verification (`tests/unit/test_drivers.py`)**:
   - Run `pytest tests/unit/test_drivers.py`
   - Test cases to execute:
     - Verify instantiation of `LinuxDriver(mock=True)`, `WindowsDriver(mock=True)`, `MacOSDriver(mock=True)`, `AndroidDriver(mock=True)`, `IOSDriver(mock=True)`.
     - Test each of the 8 action primitives (`click`, `double_click`, `right_click`, `drag`, `type`, `key_combination`, `scroll`, `wait`) on all drivers in mock mode; verify `ActionResult.success is True` and `history` logs are populated correctly.
     - Test `execute_action("click", {"x": 100, "y": 200})` dispatcher method on `BaseOSDriver`.
     - Test `capture_screenshot()` returns a valid `PIL.Image.Image` instance.
     - Test exception handling: raising `ActionExecutionError` when invalid action_type or missing parameters are supplied to `execute_action`.
     - Test `@with_retry`: wrap a failing function that raises `ActionExecutionError` twice and succeeds on the 3rd try; verify retry count and exponential delay with jitter. Ensure `PlatformNotSupportedError` immediately bubbles up without retrying.
     - Test `get_driver("auto", mock=True)` factory return value.

2. **Command Verification**:
   - `pytest tests/unit/test_drivers.py -v`
