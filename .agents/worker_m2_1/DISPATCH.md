## 2026-08-08T11:15:34Z
<USER_REQUEST>
You are worker_m2_1, the implementation worker for Milestone M2 (Cross-Platform OS Automation Drivers).
Your working directory is: /home/oh_my_macos27/OmniBench Computer Use/.agents/worker_m2_1

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Instructions:
1. Read the authoritative requirement and specification files BEFORE implementing:
   - /home/oh_my_macos27/OmniBench Computer Use/ORIGINAL_REQUEST.md
   - /home/oh_my_macos27/OmniBench Computer Use/PROJECT.md
   - /home/oh_my_macos27/OmniBench Computer Use/.agents/orch_m2_drivers/SCOPE.md
   - /home/oh_my_macos27/OmniBench Computer Use/.agents/explorer_m2_1/handoff.md
   - /home/oh_my_macos27/OmniBench Computer Use/.agents/explorer_m2_2/handoff.md
   - /home/oh_my_macos27/OmniBench Computer Use/.agents/explorer_m2_3/handoff.md

2. Target Code Ownership:
   You exclusively own and must implement the following files under /home/oh_my_macos27/OmniBench Computer Use/:
   - `omnibench/__init__.py`
   - `omnibench/drivers/__init__.py`
   - `omnibench/drivers/base.py`
   - `omnibench/drivers/linux.py`
   - `omnibench/drivers/windows.py`
   - `omnibench/drivers/macos.py`
   - `omnibench/drivers/android.py`
   - `omnibench/drivers/ios.py`
   - `omnibench/drivers/retry.py`
   - `tests/__init__.py`
   - `tests/unit/__init__.py`
   - `tests/unit/test_drivers.py`

3. Implementation Details:
   - `base.py`: Define `DriverException`, `PlatformNotSupportedError`, `DeviceConnectionError`, `ActionExecutionError`, `TimeoutError`, `ActionResult` dataclass, and `BaseOSDriver` abstract base class defining 8 action primitives (`click`, `double_click`, `right_click`, `drag`, `type`, `key_combination`, `scroll`, `wait`), `capture_screenshot()`, and `execute_action(action_type, params)`.
   - `retry.py`: Implement `@with_retry(max_retries=3, initial_delay=0.5, backoff_factor=2.0, jitter=True, retryable_exceptions=...)` exponential jitter backoff decorator with daemon reconnect capability and `PlatformNotSupportedError` bypass.
   - `linux.py`, `windows.py`, `macos.py`, `android.py`, `ios.py`: Implement concrete drivers for each platform. Include lazy system binary checks and mock mode fallback (`mock: bool = False`) so all 8 primitives and screenshot capture execute reliably in headless/CI environments where native display servers or hardware are absent.
   - `drivers/__init__.py`: Export all drivers, exceptions, `ActionResult`, `@with_retry`, and `get_driver(platform_name: str | None = None, mock: bool = False, **kwargs) -> BaseOSDriver` factory function.
   - `tests/unit/test_drivers.py`: Create comprehensive pytest test suite covering all 8 primitives, platform selection factory, retry backoff retries, exception hierarchy payload attributes, and mock mode fallback.

4. Build & Verification:
   - Run python imports verification and run pytest:
     `.venv/bin/python -m pytest tests/unit/test_drivers.py -v`
   - Ensure 100% of unit tests pass cleanly.

5. Write your implementation report, test commands, and test pass evidence in /home/oh_my_macos27/OmniBench Computer Use/.agents/worker_m2_1/handoff.md.

6. Report completion to parent orchestrator via send_message.
</USER_REQUEST>
