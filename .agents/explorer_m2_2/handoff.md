# Handoff Report — Milestone M2: Error Handling, Retry Mechanism & Test Strategy

**Agent**: explorer_m2_2  
**Working Directory**: `/home/oh_my_macos27/OmniBench Computer Use/.agents/explorer_m2_2`  
**Date**: 2026-08-08  
**Target Milestone**: M2 — Cross-Platform OS Automation Drivers (`omnibench.drivers`)

---

## 1. Observation

### 1.1 Documentation & Requirements Analysis
- **Authoritative Documents Examined**:
  - `ORIGINAL_REQUEST.md`: Requirement R2 mandates modular automation drivers supporting full computer use action primitives (`click`, `double_click`, `right_click`, `drag`, `type`, `key_combination`, `scroll`, `wait`) across Windows 10+, macOS 11+, Linux 2020+, Android 10+, and iOS 14+ with automated error backoff and retries.
  - `PROJECT.md`: Defines Feature 7 (Unified `BaseOSDriver`), Feature 8 (Desktop OS Drivers), Feature 9 (Mobile OS Drivers), Feature 10 (Error Retry & Backoff). Target module structure under `omnibench/drivers/`.
  - `SCOPE.md`: Specifies exception hierarchy (`DriverException`, `PlatformNotSupportedError`, `DeviceConnectionError`, `ActionExecutionError`, `TimeoutError`) and decorator `@with_retry(max_retries=3, initial_delay=0.5, backoff_factor=2.0, jitter=True, retryable_exceptions=...)`.
  - `TEST_INFRA.md`: Requires requirement-driven opaque-box testing with Category-Partition and BVA testing for all features.

### 1.2 Host Environment & System Binaries Inspection
Execution of system binary queries (`which xdotool Xvfb xvfb-run adb simctl python python3 pytest`) on the Linux runner revealed:
- **`Xvfb`**: `/usr/bin/Xvfb` (Available)
- **`xvfb-run`**: `/usr/bin/xvfb-run` (Available)
- **`python3`**: `/usr/bin/python3` (Python 3.12.3 Available)
- **`xdotool`**: Not installed on host PATH (exited code 1).
- **`adb`**: Not installed on host PATH (exited code 1).
- **`simctl`**: Not installed on host PATH (non-macOS system).
- **Python Virtualenv (`.venv`)**: Python 3.12 environment with `pillow` (12.3.0), `numpy` (2.5.1), `onnxruntime` (1.28.0), `psutil` (7.2.2), `pydantic` (2.13.4), `httpx` (0.28.1).
- **Repository Directory State**: Neither `omnibench/drivers/` nor `tests/` directories have been created yet on disk.

---

## 2. Logic Chain

### 2.1 Headless Environment Isolation & Import Safety
1. **Observation**: Host environment lacks `xdotool`, `adb`, and `simctl`. Physical mobile devices and Windows/macOS native APIs are absent.
2. **Deduction**: Importing `omnibench.drivers` or any platform module (`linux.py`, `windows.py`, `macos.py`, `android.py`, `ios.py`) MUST NOT check or invoke host binaries at import time. Doing so would cause immediate import crashes (`FileNotFoundError` / `ImportError`) in test runners or headless CI environments.
3. **Design Requirement**: Binary availability checks must be performed lazily upon driver instantiation (`__init__`) or action execution. Furthermore, every driver must support a `mock: bool = False` mode or fallback mechanism so unit tests and dry runs can execute 100% reliably anywhere without native binaries or hardware connected.

### 2.2 Subprocess Safety Specification
1. **Observation**: Desktop and mobile drivers interact with host OS commands (`xdotool`, `screencapture`, `powershell`, `adb`, `simctl`) via subprocesses.
2. **Risk**: Raw `subprocess.run` calls can block indefinitely, leak zombie processes, fail with missing commands, or throw raw unhandled OS exceptions.
3. **Design Requirement**: All drivers must use a unified internal runner (e.g. `_run_subprocess_cmd`) that:
   - Sets `shell=False` and passes explicit argument lists to prevent shell injection vulnerabilities.
   - Enforces an explicit `timeout` (default 10.0 seconds).
   - Maps `subprocess.TimeoutExpired` -> `omnibench.drivers.retry.TimeoutError`.
   - Maps `FileNotFoundError` -> `PlatformNotSupportedError` (missing system binary).
   - Captures `stdout` and `stderr` safely to populate `ActionExecutionError` details upon non-zero exit codes.

### 2.3 Exception Hierarchy Architecture
All driver-related exceptions must inherit from a unified base exception `DriverException`:

```
Exception
└── DriverException
    ├── PlatformNotSupportedError
    ├── DeviceConnectionError
    ├── ActionExecutionError
    └── TimeoutError
```

#### Detailed Class Specifications:
```python
class DriverException(Exception):
    """Base exception for all OmniBench OS automation driver errors."""
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

class PlatformNotSupportedError(DriverException):
    """Raised when platform binary is missing or OS is unsupported."""
    def __init__(self, message: str, platform: str | None = None, required_binary: str | None = None):
        super().__init__(message, {"platform": platform, "required_binary": required_binary})
        self.platform = platform
        self.required_binary = required_binary

class DeviceConnectionError(DriverException):
    """Raised when mobile daemon or display server connection drops."""
    def __init__(self, message: str, device_id: str | None = None, daemon_port: int | None = None):
        super().__init__(message, {"device_id": device_id, "daemon_port": daemon_port})
        self.device_id = device_id
        self.daemon_port = daemon_port

class ActionExecutionError(DriverException):
    """Raised when execution of an action primitive fails."""
    def __init__(self, message: str, action_type: str | None = None, params: dict | None = None, cause: Exception | None = None):
        super().__init__(message, {"action_type": action_type, "params": params, "cause": str(cause) if cause else None})
        self.action_type = action_type
        self.params = params
        self.cause = cause

class TimeoutError(DriverException):
    """Raised when an action primitive or screenshot capture operation times out."""
    def __init__(self, message: str, timeout_seconds: float | None = None, action_type: str | None = None):
        super().__init__(message, {"timeout_seconds": timeout_seconds, "action_type": action_type})
        self.timeout_seconds = timeout_seconds
        self.action_type = action_type
```

### 2.4 Jittered Exponential Retry Decorator (`@with_retry`)
Target module: `omnibench/drivers/retry.py`

#### Decorator Specification & Parameters:
- **`max_retries: int = 3`**: Maximum number of retry attempts after the initial failed attempt (total attempts = `max_retries + 1`).
- **`initial_delay: float = 0.5`**: Base delay in seconds for the first retry.
- **`backoff_factor: float = 2.0`**: Multiplicative factor for exponential delay increase.
- **`jitter: bool = True`**: Whether to add random jitter to backoff delay intervals.
- **`retryable_exceptions`**: Tuple of exception types to retry on. Default: `(DeviceConnectionError, ActionExecutionError, TimeoutError, ConnectionError, OSError)`. Note: `PlatformNotSupportedError` is explicitly excluded from retries.
- **`reconnect_on_error: bool = True`**: Automatically invokes `self.reconnect()` if available when catching `DeviceConnectionError`.

#### Backoff Delay Formula:
For attempt index $k \in \{0, 1, \dots, \text{max\_retries}-1\}$:
$$\text{base\_delay}_k = \text{initial\_delay} \times (\text{backoff\_factor}^k)$$
If `jitter` is `True`:
$$\text{actual\_delay}_k = \text{base\_delay}_k \times \text{random.uniform}(0.5, 1.5)$$
If `jitter` is `False`:
$$\text{actual\_delay}_k = \text{base\_delay}_k$$

#### Reference Implementation Blueprint for `retry.py`:
```python
import functools
import random
import time
import logging
from typing import Callable, Any

from omnibench.drivers.base import (
    DriverException,
    PlatformNotSupportedError,
    DeviceConnectionError,
    ActionExecutionError,
    TimeoutError,
)

logger = logging.getLogger(__name__)

DEFAULT_RETRYABLE = (
    DeviceConnectionError,
    ActionExecutionError,
    TimeoutError,
    ConnectionError,
    OSError,
)

def with_retry(
    max_retries: int = 3,
    initial_delay: float = 0.5,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: tuple[type[BaseException], ...] = DEFAULT_RETRYABLE,
    reconnect_on_error: bool = True,
) -> Callable:
    """Decorator for automatic jittered exponential retry backoff and daemon reconnection."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            self_obj = args[0] if args else None
            last_exc = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except PlatformNotSupportedError:
                    # Non-retryable configuration error: raise immediately
                    raise
                except retryable_exceptions as exc:
                    last_exc = exc
                    if attempt == max_retries:
                        logger.error(f"Action failed after {max_retries + 1} attempts: {exc}")
                        raise last_exc

                    # Daemon reconnection logic
                    if reconnect_on_error and isinstance(exc, DeviceConnectionError) and self_obj:
                        reconnect_fn = getattr(self_obj, "reconnect", None)
                        if callable(reconnect_fn):
                            try:
                                logger.info("Attempting driver reconnection...")
                                reconnect_fn()
                            except Exception as rec_err:
                                logger.warning(f"Reconnection attempt failed: {rec_err}")

                    # Calculate backoff delay
                    base_delay = initial_delay * (backoff_factor ** attempt)
                    if jitter:
                        actual_delay = base_delay * random.uniform(0.5, 1.5)
                    else:
                        actual_delay = base_delay

                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries + 1} failed ({type(exc).__name__}: {exc}). "
                        f"Retrying in {actual_delay:.2f}s..."
                    )
                    time.sleep(actual_delay)

            if last_exc:
                raise last_exc

        return wrapper
    return decorator
```

---

## 3. Unit Test Strategy (`tests/unit/test_drivers.py`)

The unit test suite for M2 OS drivers must be placed in `tests/unit/test_drivers.py` and structured into 5 cohesive pytest test classes:

### 3.1 `Test8ActionPrimitives`
Validates that all 8 mandatory action primitives operate as specified on `BaseOSDriver` and concrete drivers, verifying parameters and return values (`ActionResult`).

1. **`test_primitive_click`**: Verify `click(x: int, y: int, button: str = "left")` handles valid coordinates and buttons (`"left"`, `"right"`, `"middle"`). Returns `ActionResult` with `action_type="click"`.
2. **`test_primitive_double_click`**: Verify `double_click(x: int, y: int)` executes double click action.
3. **`test_primitive_right_click`**: Verify `right_click(x: int, y: int)` executes right click action.
4. **`test_primitive_drag`**: Verify `drag(start_x, start_y, end_x, end_y, duration_ms=500)` validates positive `duration_ms` and returns `action_type="drag"`.
5. **`test_primitive_type`**: Verify `type(text: str, interval_ms: int = 0)` handles single and multi-character strings with key delay.
6. **`test_primitive_key_combination`**: Verify `key_combination(keys: list[str])` accepts key lists such as `["ctrl", "c"]` or `["cmd", "space"]`.
7. **`test_primitive_scroll`**: Verify `scroll(x, y, direction="down", amount=1)` validates directions (`"up"`, `"down"`, `"left"`, `"right"`).
8. **`test_primitive_wait`**: Verify `wait(seconds: float)` sleeps for duration and returns `ActionResult`.
9. **`test_invalid_action_parameters`**: Verify negative coordinates, negative wait seconds, or invalid scroll directions raise `ValueError` or `ActionExecutionError`.
10. **`test_execute_action_generic_dispatch`**: Verify calling `driver.execute_action(action_type, params)` correctly dispatches to the corresponding method and returns `ActionResult`.

### 3.2 `TestPlatformDriverSelection`
Validates factory function `get_driver(platform_name: str, mock: bool = False) -> BaseOSDriver`.

1. **`test_get_driver_by_explicit_name`**: Verify requesting `"linux"`, `"windows"`, `"macos"`, `"android"`, `"ios"`, `"mock"` instantiates the appropriate driver class.
2. **`test_get_driver_auto_detection`**: Verify `get_driver()` without platform argument detects current OS via `sys.platform`.
3. **`test_unsupported_platform_name`**: Verify requesting `"freebsd"` or `"unknown_os"` raises `PlatformNotSupportedError`.
4. **`test_mock_driver_instantiation`**: Verify passing `mock=True` returns driver operating in mock fallback mode.

### 3.3 `TestRetryMechanism`
Validates decorator `@with_retry` under various failure and recovery conditions using pytest mocks/spies.

1. **`test_retry_success_on_first_try`**: Function succeeds on attempt 1; zero sleep calls made.
2. **`test_retry_recovery_after_transient_failures`**: Function fails 2 times with `DeviceConnectionError`, succeeds on attempt 3. Max retries set to 3. Verify total 3 executions, 2 retries.
3. **`test_retry_exhaustion_reraises_last_exception`**: Function fails all 4 attempts (1 initial + 3 retries). Verify last exception is re-raised with full traceback.
4. **`test_retry_jitter_exponential_backoff_timing`**: Mock `time.sleep` and `random.uniform`; assert base delays follow $0.5, 1.0, 2.0$ sequence for `initial_delay=0.5, backoff_factor=2.0`.
5. **`test_retry_reconnect_daemon_trigger`**: Decorate a method on a mock driver with `reconnect()` method. Throw `DeviceConnectionError`; assert `reconnect()` is invoked before sleeping.
6. **`test_non_retryable_exception_immediate_bypass`**: Throw `PlatformNotSupportedError` or `ValueError`; assert zero retries occur and exception propagates instantly.

### 3.4 `TestExceptionHierarchyAndPropagation`
Validates custom exception classes and payload attributes.

1. **`test_exception_inheritance`**: Assert `issubclass(e, DriverException)` for `PlatformNotSupportedError`, `DeviceConnectionError`, `ActionExecutionError`, `TimeoutError`.
2. **`test_exception_payload_attributes`**:
   - `PlatformNotSupportedError`: assert `e.platform` and `e.required_binary`.
   - `DeviceConnectionError`: assert `e.device_id` and `e.daemon_port`.
   - `ActionExecutionError`: assert `e.action_type`, `e.params`, `e.cause`.
   - `TimeoutError`: assert `e.timeout_seconds`, `e.action_type`.

### 3.5 `TestEnvironmentIsolationAndSubprocess`
Validates import safety and subprocess error wrapping.

1. **`test_import_safety_without_display_or_binaries`**: Verify `import omnibench.drivers` and submodules succeed in headless environments without throwing exceptions.
2. **`test_subprocess_file_not_found_conversion`**: Mock `subprocess.run` raising `FileNotFoundError("xdotool")`; assert driver method wraps it into `PlatformNotSupportedError`.
3. **`test_subprocess_timeout_conversion`**: Mock `subprocess.run` raising `subprocess.TimeoutExpired`; assert driver method wraps it into `omnibench.drivers.retry.TimeoutError`.
4. **`test_mock_driver_screenshot_and_primitives`**: Verify mock driver returns valid RGB `PIL.Image.Image` screenshot and successful `ActionResult` instances without external binary calls.

---

## 4. Caveats

1. **Host Hardware Constraints**: The current Linux test runner lacks attached physical Android/iOS mobile devices, macOS display engines, and Windows Win32 APIs. Therefore, integration tests requiring actual host GUI rendering will rely on Xvfb or mock driver mode during unit testing.
2. **Pytest Installation**: `pytest` package will need to be installed in `.venv` or invoked via python standard `unittest` / `pytest` runner when builder agents create the test files.

---

## 5. Conclusion

- **Driver Architecture**: Readily specified with clean separation between abstract `BaseOSDriver`, concrete platform drivers, retry backoff mechanism (`@with_retry`), and exception hierarchy.
- **Error Handling & Retry Design**: Complete specification provided for 5 custom exceptions, exponential jitter backoff formula, automatic daemon reconnection, and subprocess safety wrappers.
- **Test Strategy**: Pytest suite specified under `tests/unit/test_drivers.py` covering all 8 action primitives, driver selection, retry backoff behavior, exception payload propagation, and headless import safety.

---

## 6. Verification Method

To verify the M2 error handling and test suite implementation once builder agents complete their tasks:

1. **Run Unit Test Suite**:
   ```bash
   .venv/bin/python -m pytest tests/unit/test_drivers.py -v
   ```
2. **Verify Import Isolation & Exception Subclassing**:
   ```bash
   .venv/bin/python -c "
   import omnibench.drivers
   from omnibench.drivers.base import (
       DriverException, PlatformNotSupportedError, DeviceConnectionError, ActionExecutionError, TimeoutError
   )
   from omnibench.drivers.retry import with_retry

   assert issubclass(PlatformNotSupportedError, DriverException)
   assert issubclass(DeviceConnectionError, DriverException)
   assert issubclass(ActionExecutionError, DriverException)
   assert issubclass(TimeoutError, DriverException)
   print('Imports and Exception Hierarchy Verified Successfully!')
   "
   ```
3. **Verify Jitter Retry Decorator**:
   ```bash
   .venv/bin/python -c "
   from omnibench.drivers.retry import with_retry
   from omnibench.drivers.base import ActionExecutionError

   attempts = 0
   @with_retry(max_retries=2, initial_delay=0.01, jitter=False)
   def dummy_action():
       global attempts
       attempts += 1
       if attempts < 3:
           raise ActionExecutionError('Fail')
       return 'Success'

   res = dummy_action()
   assert res == 'Success'
   assert attempts == 3
   print('Retry Decorator Verified Successfully!')
   "
   ```
