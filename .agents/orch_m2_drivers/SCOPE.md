# Scope: Milestone M2 — OS Automation Drivers

## Architecture
Modular automation drivers supporting full computer use action primitives across Linux, Windows, macOS, Android, and iOS.
Base abstraction contract `BaseOSDriver` with concrete platform driver implementations and exponential jitter retry decorator.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 7 | Unified OSDriver Interface | `BaseOSDriver` contract defining 8 action primitives with type validation | M2 | R2 |
| 8 | Desktop OS Drivers | Linux (Xvfb/xdotool), Windows (pywinauto/PowerShell), macOS (CoreGraphics) drivers | M2 | R2 |
| 9 | Mobile OS Drivers | Android (ADB/uiautomator daemon) and iOS (simctl/daemon) drivers | M2 | R2 |
| 10 | Error Retry & Backoff | Exponential retry backoff decorator with random jitter and daemon reconnect | M2 | R2 |

## Target Code Layout
- `omnibench/drivers/__init__.py`
- `omnibench/drivers/base.py`
- `omnibench/drivers/linux.py`
- `omnibench/drivers/windows.py`
- `omnibench/drivers/macos.py`
- `omnibench/drivers/android.py`
- `omnibench/drivers/ios.py`
- `omnibench/drivers/retry.py`

## Target Action Primitives (8 required)
1. `click(x: int, y: int, button: str = "left")`
2. `double_click(x: int, y: int)`
3. `right_click(x: int, y: int)`
4. `drag(start_x: int, start_y: int, end_x: int, end_y: int, duration_ms: int = 500)`
5. `type(text: str, interval_ms: int = 0)`
6. `key_combination(keys: list[str])`
7. `scroll(x: int, y: int, direction: str = "down", amount: int = 1)`
8. `wait(seconds: float)`

Additional core methods on `BaseOSDriver`:
- `capture_screenshot() -> PIL.Image`
- `execute_action(action_type: str, params: dict) -> ActionResult`

## Exception Hierarchy & Retry Specification
- `DriverException` (Base)
  - `PlatformNotSupportedError`
  - `DeviceConnectionError`
  - `ActionExecutionError`
  - `TimeoutError`
- Decorator `@with_retry(max_retries=3, initial_delay=0.5, backoff_factor=2.0, jitter=True, retryable_exceptions=(DriverException, ConnectionError, OSError))`
