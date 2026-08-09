# Cross-Platform OS Automation Drivers Specification & Design Report

## 1. Observation

### 1.1 Requirements & Scope Context
- **`ORIGINAL_REQUEST.md` (Lines 15-16, R2)**:
  > "R2. Cross-Platform Operating System Automation Drivers: Modular automation drivers supporting full computer use action primitives (click, double click, right click, drag, type, key combinations, scroll, wait) across Windows 10+, macOS 11+, Linux 2020+, Android 10+ (via ADB/uiautomator daemon), and iOS 14+ (via remote daemon / simctl)."
- **`PROJECT.md` (Lines 6, 20-23, 54-57, 84-92)**:
  - Feature 7: Unified OSDriver Interface (`BaseOSDriver` contract defining 8 action primitives with type validation).
  - Feature 8: Desktop OS Drivers (Linux Xvfb/xdotool, Windows pywinauto/PowerShell, macOS CoreGraphics).
  - Feature 9: Mobile OS Drivers (Android ADB/uiautomator daemon, iOS simctl/daemon).
  - Feature 10: Error Retry & Backoff (Exponential retry backoff decorator with random jitter and daemon reconnect).
  - Interface Contract: `BaseOSDriver.execute_action(action_type: str, params: dict) -> ActionResult` and `BaseOSDriver.capture_screenshot() -> PIL.Image`.
  - Code Layout: `omnibench/drivers/{__init__.py, base.py, linux.py, windows.py, macos.py, android.py, ios.py, retry.py}`.
- **`SCOPE.md` (Lines 25-45)**:
  - Required 8 Action Primitives: `click`, `double_click`, `right_click`, `drag`, `type`, `key_combination`, `scroll`, `wait`.
  - Exception Hierarchy: `DriverException` base class with subclasses `PlatformNotSupportedError`, `DeviceConnectionError`, `ActionExecutionError`, `TimeoutError`.
  - Retry Spec: `@with_retry(max_retries=3, initial_delay=0.5, backoff_factor=2.0, jitter=True, retryable_exceptions=(DriverException, ConnectionError, OSError))`.

### 1.2 System Environment State
- Working directory: `/home/oh_my_macos27/OmniBench Computer Use`.
- System OS: Linux (`x86_64`).
- Module structure `omnibench/drivers/` has not yet been implemented (clean slate for M2 implementation).

---

## 2. Logic Chain

### 2.1 Interface & Data Contract Architecture
From the requirement in `PROJECT.md` line 55 (`BaseOSDriver.execute_action(action_type: str, params: dict) -> ActionResult`) and line 56 (`capture_screenshot() -> PIL.Image`), we derive the strict core types:

#### Data Structure: `ActionResult`
```python
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime, timezone

@dataclass
class ActionResult:
    success: bool
    action_type: str
    params: Dict[str, Any]
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    execution_time_ms: float = 0.0
```

#### Abstract Class: `BaseOSDriver`
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from PIL import Image

class BaseOSDriver(ABC):
    """Abstract base class for all platform automation drivers."""

    @abstractmethod
    def capture_screenshot(self) -> Image.Image:
        """Capture current screen state as a PIL Image in RGB format."""
        pass

    @abstractmethod
    def execute_action(self, action_type: str, params: Dict[str, Any]) -> ActionResult:
        """
        Parse and dispatch action to appropriate primitive method, measuring execution time.
        Handles parameter validation and exception wrapping.
        """
        pass

    @abstractmethod
    def click(self, x: int, y: int, button: str = "left") -> ActionResult: ...

    @abstractmethod
    def double_click(self, x: int, y: int) -> ActionResult: ...

    @abstractmethod
    def right_click(self, x: int, y: int) -> ActionResult: ...

    @abstractmethod
    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int, duration_ms: int = 500) -> ActionResult: ...

    @abstractmethod
    def type(self, text: str, interval_ms: int = 0) -> ActionResult: ...

    @abstractmethod
    def key_combination(self, keys: List[str]) -> ActionResult: ...

    @abstractmethod
    def scroll(self, x: int, y: int, direction: str = "down", amount: int = 1) -> ActionResult: ...

    @abstractmethod
    def wait(self, seconds: float) -> ActionResult: ...
```

### 2.2 Parameter Parsing & Dispatch Matrix

In `BaseOSDriver.execute_action(action_type: str, params: dict) -> ActionResult`:
- Normalize `action_type` via `.strip().lower()`.
- Record start time via `time.perf_counter()`.
- Validate required fields and default parameters:

| Action Primitive | Parameter Specs & Types | Default Values | Validation & Error Trigger |
| :--- | :--- | :--- | :--- |
| `click` | `x: int`, `y: int`, `button: str` | `button="left"` | `button` in `("left", "right", "middle")` |
| `double_click` | `x: int`, `y: int` | N/A | `x >= 0`, `y >= 0` |
| `right_click` | `x: int`, `y: int` | N/A | `x >= 0`, `y >= 0` |
| `drag` | `start_x: int`, `start_y: int`, `end_x: int`, `end_y: int`, `duration_ms: int` | `duration_ms=500` | `duration_ms >= 0` |
| `type` | `text: str`, `interval_ms: int` | `interval_ms=0` | `isinstance(text, str)` |
| `key_combination`| `keys: list[str]` | N/A | `len(keys) > 0` |
| `scroll` | `x: int`, `y: int`, `direction: str`, `amount: int` | `direction="down"`, `amount=1` | `direction` in `("up", "down", "left", "right")`, `amount > 0` |
| `wait` | `seconds: float` | N/A | `seconds >= 0.0` |

If parameter validation fails, `execute_action` catches `KeyError` or `ValueError` and returns `ActionResult(success=False, action_type=action_type, params=params, error=str(e), execution_time_ms=elapsed)`.

---

### 2.3 Factory Design (`get_driver`)

Location: `omnibench/drivers/__init__.py` and `omnibench/drivers/base.py`

```python
from omnibench.drivers.base import BaseOSDriver, PlatformNotSupportedError

def get_driver(platform_name: str, **kwargs) -> BaseOSDriver:
    """
    Factory helper returning appropriate platform driver instance.
    
    Args:
        platform_name: Case-insensitive target platform ("linux", "windows", "macos", "android", "ios").
        **kwargs: Optional driver configuration parameters (e.g. display, serial, udid).
    
    Returns:
        Instance of BaseOSDriver concrete subclass.
    """
    norm_platform = platform_name.strip().lower()
    
    if norm_platform in ("linux", "ubuntu", "debian", "xvfb"):
        from omnibench.drivers.linux import LinuxDriver
        return LinuxDriver(**kwargs)
    elif norm_platform in ("windows", "win", "win32", "win64"):
        from omnibench.drivers.windows import WindowsDriver
        return WindowsDriver(**kwargs)
    elif norm_platform in ("macos", "mac", "darwin", "osx"):
        from omnibench.drivers.macos import MacOSDriver
        return MacOSDriver(**kwargs)
    elif norm_platform in ("android", "adb"):
        from omnibench.drivers.android import AndroidDriver
        return AndroidDriver(**kwargs)
    elif norm_platform in ("ios", "simctl", "iphoneos"):
        from omnibench.drivers.ios import IOSDriver
        return IOSDriver(**kwargs)
    else:
        raise PlatformNotSupportedError(f"Unsupported OS driver platform: '{platform_name}'")
```

---

### 2.4 Detailed Specifications per Platform Driver

#### 1. Linux Driver (`omnibench/drivers/linux.py`)
- **Display Handling (Xvfb)**:
  - Check `$DISPLAY` environment variable. If missing or `display` param passed, check if `Xvfb` process is running or spawn `Xvfb :99 -screen 0 1920x1080x24` via `subprocess.Popen`.
  - Set `os.environ["DISPLAY"] = display_name`.
- **Command Execution Backend**:
  - Primary CLI backend: `xdotool`.
  - Fallback Python backend: `pyautogui`.
  - Command mapping:
    - `click(x, y, button)`: `xdotool mousemove x y click 1` (1=left, 2=middle, 3=right) or `pyautogui.click(x, y, button=button)`.
    - `double_click(x, y)`: `xdotool mousemove x y click --repeat 2 --delay 50 1` or `pyautogui.doubleClick(x, y)`.
    - `right_click(x, y)`: `xdotool mousemove x y click 3` or `pyautogui.rightClick(x, y)`.
    - `drag(start_x, start_y, end_x, end_y, duration_ms)`: `xdotool mousemove start_x start_y mousedown 1 mousemove end_x end_y mouseup 1` with step sleep.
    - `type(text, interval_ms)`: `xdotool type --delay <ms> -- "<text>"` or `pyautogui.typewrite()`.
    - `key_combination(keys)`: key mapping translation (e.g. `"ctrl"` -> `"Control_L"`, `"alt"` -> `"Alt_L"`, `"super"` -> `"Super_L"`), executing `xdotool key key1+key2`.
    - `scroll(x, y, direction, amount)`: `xdotool mousemove x y click --repeat <amount> 4` (up) or `5` (down).
    - `wait(seconds)`: `time.sleep(seconds)`.
- **Screenshot Capture**:
  - Pipeline:
    1. Exec `scrot -z -` -> stdout byte stream -> `PIL.Image.open(io.BytesIO(raw_bytes))`.
    2. Fallback: `import -window root png:-` (ImageMagick).
    3. Fallback: `PIL.ImageGrab.grab()` or `pyautogui.screenshot()`.

#### 2. Windows Driver (`omnibench/drivers/windows.py`)
- **Execution Backend**:
  - Primary backend: `pywinauto` (Win32 & UIA backends).
  - Secondary CLI backend: PowerShell commands & Win32 API via `ctypes` (`user32.dll` / `gdi32.dll`).
  - Command mapping:
    - `click(x, y, button)`: `ctypes.windll.user32.SetCursorPos(x, y)` + `mouse_event(MOUSEEVENTF_LEFTDOWN | MOUSEEVENTF_LEFTUP)` or `pywinauto.mouse.click()`.
    - `double_click(x, y)`: `pywinauto.mouse.double_click(coords=(x, y))`.
    - `right_click(x, y)`: `pywinauto.mouse.right_click(coords=(x, y))`.
    - `drag(...)`: `pywinauto.mouse.press(coords=(start_x, start_y))` -> `time.sleep(duration_ms / 1000.0)` -> `pywinauto.mouse.release(coords=(end_x, end_y))`.
    - `type(text, interval_ms)`: `pywinauto.keyboard.send_keys(text)` or PowerShell `[System.Windows.Forms.SendKeys]::SendWait`.
    - `key_combination(keys)`: translate key names to pywinauto shortcut format (`["ctrl", "c"]` -> `"^c"`).
    - `scroll(x, y, direction, amount)`: `pywinauto.mouse.scroll(coords=(x, y), wheel_dist=(amount if direction=='up' else -amount))`.
    - `wait(seconds)`: `time.sleep(seconds)`.
- **Screenshot Capture**:
  - Primary: `PIL.ImageGrab.grab()` using Win32 GDI API.
  - Fallback: PowerShell `[System.Drawing.Graphics]::CopyFromScreen` saving to temporary buffer.

#### 3. macOS Driver (`omnibench/drivers/macos.py`)
- **Execution Backend**:
  - Primary backend: PyObjC `Quartz.CoreGraphics` events or `ctypes` loading `/System/Library/Frameworks/CoreGraphics.framework`.
  - Secondary CLI backend: `osascript` (AppleScript CLI) or `cliclick` utility.
  - Command mapping:
    - `click(x, y, button)`: `CGEventCreateMouseEvent(None, kCGEventLeftMouseDown, CGPoint(x, y), 0)` and `kCGEventLeftMouseUp`.
    - `double_click(x, y)`: Quartz mouse event with `kCGMouseEventClickState` set to `2`.
    - `right_click(x, y)`: Quartz event with `kCGEventRightMouseDown` and `kCGEventRightMouseUp`.
    - `drag(...)`: `kCGEventLeftMouseDown` at start -> series of `kCGEventLeftMouseDragged` -> `kCGEventLeftMouseUp` at end.
    - `type(text, interval_ms)`: `CGEventKeyboardSetUnicodeString` or `osascript -e 'tell application "System Events" to keystroke "<text>"'`.
    - `key_combination(keys)`: `osascript -e 'tell application "System Events" to key code <code...> using {<modifiers...>}'`.
    - `scroll(x, y, direction, amount)`: `CGEventCreateScrollWheelEvent(None, kCGScrollEventUnitLine, 1, dy)`.
    - `wait(seconds)`: `time.sleep(seconds)`.
- **Screenshot Capture**:
  - Primary: `subprocess.run(["screencapture", "-x", temp_file_path])` -> `PIL.Image.open(temp_file_path)`.
  - Fallback: `Quartz.CGWindowListCreateImage`.

#### 4. Android Driver (`omnibench/drivers/android.py`)
- **Device Management**:
  - Target device specified via `device_serial: Optional[str] = None`.
  - Base command array: `["adb", "-s", serial]` if serial specified else `["adb"]`.
- **Execution Backend**:
  - Primary backend: ADB shell input commands.
  - Fallback / RPC backend: `uiautomator` HTTP/RPC daemon (e.g. `uiautomator2` python client or jsonrpc over port 9008) when fine UI element hierarchy or daemon persistence is required.
  - Command mapping:
    - `click(x, y, button)`: `adb shell input tap x y`.
    - `double_click(x, y)`: two consecutive `adb shell input tap x y` invocations.
    - `right_click(x, y)`: simulated via long press `adb shell input swipe x y x y 1000` or `adb shell input keyevent 82` (MENU key).
    - `drag(start_x, start_y, end_x, end_y, duration_ms)`: `adb shell input swipe start_x start_y end_x end_y duration_ms`.
    - `type(text, interval_ms)`: shell-escaped `adb shell input text "<escaped_text>"`.
    - `key_combination(keys)`: Android Keycode map lookup (e.g. `HOME`->3, `BACK`->4, `ENTER`->66, `DELETE`->67, `APP_SWITCH`->187) -> `adb shell input keyevent <code1> <code2>`.
    - `scroll(x, y, direction, amount)`: calculated swipe `adb shell input swipe x y_start x y_end 300` based on direction and scroll amount.
    - `wait(seconds)`: `time.sleep(seconds)`.
- **Screenshot Capture**:
  - Primary: `adb shell screencap -p` piped to bytes -> strip CRLF line endings (`raw.replace(b'\r\n', b'\n')`) -> `PIL.Image.open(io.BytesIO(cleaned_bytes))`.
  - Fallback: `adb shell screencap /sdcard/screen.png && adb pull /sdcard/screen.png local_tmp.png`.

#### 5. iOS Driver (`omnibench/drivers/ios.py`)
- **Device / Simulator Management**:
  - `udid: str = "booted"` (defaults to currently booted iOS simulator).
- **Execution Backend**:
  - Primary CLI backend: `xcrun simctl`.
  - Daemon fallback backend: WebDriverAgent (WDA) / XCTest HTTP daemon on `http://localhost:8100`.
  - Command mapping:
    - `click(x, y, button)`: `xcrun simctl io booted tap x y` or WDA `POST /wda/tap/0`.
    - `double_click(x, y)`: WDA `POST /wda/doubleTap`.
    - `right_click(x, y)`: long press / 3D touch simulation via WDA `POST /wda/touchAndHold`.
    - `drag(start_x, start_y, end_x, end_y, duration_ms)`: `xcrun simctl io booted drag start_x start_y end_x end_y` or WDA `POST /wda/dragfromtoforduration`.
    - `type(text, interval_ms)`: `xcrun simctl io booted type "<text>"` or WDA `POST /wda/keys`.
    - `key_combination(keys)`: `xcrun simctl io booted keyevent <key>` or WDA `POST /wda/pressButton`.
    - `scroll(x, y, direction, amount)`: drag vector based on scroll direction or WDA scroll endpoint.
    - `wait(seconds)`: `time.sleep(seconds)`.
- **Screenshot Capture**:
  - Primary: `xcrun simctl io booted screenshot screenshot.png` -> `PIL.Image.open("screenshot.png")`.
  - Fallback: WDA `GET /screenshot` returning base64 PNG data.

---

### 2.5 Error Handling & Exponential Jitter Retry Specification

Location: `omnibench/drivers/retry.py`

#### Exception Hierarchy
```python
class DriverException(Exception):
    """Base exception for all OS driver errors."""
    pass

class PlatformNotSupportedError(DriverException):
    """Raised when an requested operating system platform is unsupported."""
    pass

class DeviceConnectionError(DriverException):
    """Raised when ADB device, iOS simulator, or display connection fails."""
    pass

class ActionExecutionError(DriverException):
    """Raised when an action primitive fails to execute or parameter validation fails."""
    pass

class TimeoutError(DriverException):
    """Raised when an action or screenshot capture times out."""
    pass
```

#### Decorator Implementation: `@with_retry`
```python
import time
import random
import functools

def with_retry(
    max_retries: int = 3,
    initial_delay: float = 0.5,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: tuple = (DriverException, ConnectionError, OSError)
):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self_or_func, *args, **kwargs):
            delay = initial_delay
            last_exception = None
            for attempt in range(1, max_retries + 1):
                try:
                    return func(self_or_func, *args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        break
                    
                    # Connection recovery attempt
                    if isinstance(e, (DeviceConnectionError, ConnectionError)) and hasattr(self_or_func, "reconnect_daemon"):
                        try:
                            self_or_func.reconnect_daemon()
                        except Exception:
                            pass
                    
                    sleep_time = delay
                    if jitter:
                        sleep_time += random.uniform(0, delay * 0.5)
                    time.sleep(sleep_time)
                    delay *= backoff_factor
            raise last_exception
        return wrapper
    return decorator
```

---

## 3. Caveats

1. **Host Environment Constraints**:
   - OS Driver execution on Linux requires X11/Xvfb. Headless CI environments must launch Xvfb prior to invoking GUI primitives.
   - Windows driver requires `pywinauto` or PowerShell on Windows hosts.
   - macOS driver requires PyObjC (`Quartz`) or Accessibility Permissions granted to Terminal/Python binary.
   - Mobile drivers (Android / iOS) require external dependencies (`adb` in system PATH for Android, Xcode command line tools / `xcrun simctl` for iOS).
2. **Fallback Mocking for Cross-Platform Testing**:
   - On host environments running on Linux (such as the current benchmark host), native calls to Windows `ctypes.windll` or macOS `Quartz` will fail if executed directly.
   - Recommendation: Concrete drivers for non-host platforms must implement fallback/mock modes or graceful degradation (`PlatformNotSupportedError` or dry-run execution) during unit testing unless running on target host/emulator.
3. **Screenshot Buffer Parsing**:
   - `adb shell screencap -p` on Linux converts line endings `\n` to `\r\n` when binary output is piped through stdout in certain adb versions. Direct byte array replacement (`data.replace(b'\r\r\n', b'\n').replace(b'\r\n', b'\n')`) is required before passing to `PIL.Image.open()`.

---

## 4. Conclusion

The specification for `omnibench.drivers` establishes a unified cross-platform OS automation architecture.
- Abstract contract `BaseOSDriver` guarantees support for 8 primitive actions (`click`, `double_click`, `right_click`, `drag`, `type`, `key_combination`, `scroll`, `wait`), `capture_screenshot() -> PIL.Image.Image`, and `execute_action() -> ActionResult`.
- Concrete drivers cover Linux (Xvfb/xdotool/scrot), Windows (pywinauto/PowerShell/Win32), macOS (CoreGraphics/screencapture), Android (ADB input/uiautomator), and iOS (simctl/WDA).
- Dynamic factory function `get_driver(platform_name: str) -> BaseOSDriver` handles case-insensitive alias mapping and instantiation.
- Exponential backoff decorator `@with_retry` ensures fault tolerance against transient device drops, connection timeouts, and command execution failures.

---

## 5. Verification Method

### 5.1 Unit & Integration Test Commands
1. **Directory & File Layout Verification**:
   ```bash
   ls -la omnibench/drivers/
   # Expected files: __init__.py, base.py, linux.py, windows.py, macos.py, android.py, ios.py, retry.py
   ```
2. **Driver Interface & Factory Test**:
   ```bash
   pytest tests/unit/test_drivers.py -v
   ```
   *Expected result*:
   - `get_driver("linux")` returns instance of `LinuxDriver`.
   - `get_driver("windows")` returns instance of `WindowsDriver`.
   - `get_driver("macos")` returns instance of `MacOSDriver`.
   - `get_driver("android")` returns instance of `AndroidDriver`.
   - `get_driver("ios")` returns instance of `IOSDriver`.
   - `get_driver("invalid")` raises `PlatformNotSupportedError`.
3. **Action Execution & ActionResult Contract Test**:
   - Verify `execute_action("click", {"x": 100, "y": 200})` returns `ActionResult` object with `success: bool`, `action_type: "click"`, `timestamp` (ISO string), and `execution_time_ms > 0`.
4. **Retry Mechanism Test**:
   - Test mock method with `@with_retry(max_retries=3)` that fails twice with `DriverException` and succeeds on 3rd attempt -> verifies decorator retries twice and returns result.
