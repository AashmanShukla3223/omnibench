# Scope: Milestone M2 — Cross-Platform OS Automation Drivers

## Architecture
- `omnibench/drivers/`: Base OS driver abstraction, platform drivers (Linux, Windows, macOS, Android, iOS), and exponential jittered retry backoff decorator with mock fallback support.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 7 | Unified OSDriver Interface | `BaseOSDriver` contract defining 8 action primitives (`click`, `double_click`, `right_click`, `drag`, `type`, `key_combination`, `scroll`, `wait`) with type validation and screenshot capture | M2 | PROJECT.md |
| 8 | Desktop OS Drivers | Linux (`Xvfb`/`xdotool`), Windows (`pywinauto`/`PowerShell`), macOS (`CoreGraphics`) drivers with mock fallback mode | M2 | PROJECT.md |
| 9 | Mobile OS Drivers | Android (`ADB`/`uiautomator` daemon) and iOS (`simctl`/daemon) drivers with mock fallback mode | M2 | PROJECT.md |
| 10 | Error Retry & Backoff | Exponential retry backoff decorator with random jitter and daemon reconnect | M2 | PROJECT.md |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M2 | OS Automation Drivers | `omnibench/drivers/` (`base.py`, `linux.py`, `windows.py`, `macos.py`, `android.py`, `ios.py`, `retry.py`) | none | IN_PROGRESS |

## Interface Contracts
### `omnibench.drivers` ↔ Benchmark Runner & Visual Pillar
- `BaseOSDriver.execute_action(action_type: str, params: dict) -> ActionResult`
- `BaseOSDriver.capture_screenshot() -> PIL.Image`
- Supported action primitives: `click`, `double_click`, `right_click`, `drag`, `type`, `key_combination`, `scroll`, `wait`
- `ActionResult`: `success: bool`, `action_type: str`, `error_message: str | None`, `metadata: dict`
- `with_retry(max_retries: int = 3, base_delay: float = 0.1, max_delay: float = 2.0, jitter: bool = True)`

## Code Layout
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
tests/unit/
└── test_drivers.py
```
