"""
Unit test suite for OmniBench OS Automation Drivers (Milestone M2).

Covers:
- All 8 action primitives (click, double_click, right_click, drag, type, key_combination, scroll, wait)
- Generic dispatcher execute_action() & parameter validation
- Platform driver selection factory (get_driver)
- Exception hierarchy & payload attributes
- Exponential jitter retry decorator (@with_retry) & daemon reconnection
- Mock mode fallback & screenshot capture
"""

import time
from unittest.mock import MagicMock, patch
import pytest
from PIL import Image

from omnibench.drivers import (
    ActionExecutionError,
    ActionResult,
    AndroidDriver,
    BaseOSDriver,
    DeviceConnectionError,
    DriverException,
    IOSDriver,
    LinuxDriver,
    MacOSDriver,
    PlatformNotSupportedError,
    TimeoutError,
    get_driver,
    with_retry,
)
from omnibench.drivers.windows import WindowsDriver


# --- Fixtures ---

@pytest.fixture(params=["linux", "windows", "macos", "android", "ios"])
def all_mock_drivers(request):
    """Fixture providing mock-mode instances of all 5 OS drivers."""
    return get_driver(request.param, mock=True)


# --- 1. Test 8 Action Primitives ---

class Test8ActionPrimitives:
    """Test suite for the 8 core action primitives and execute_action dispatcher."""

    def test_click_primitive(self, all_mock_drivers):
        driver = all_mock_drivers
        res = driver.click(x=100, y=200, button="left")
        assert isinstance(res, ActionResult)
        assert res.success is True
        assert res.action_type == "click"
        assert res.params == {"x": 100, "y": 200, "button": "left"}
        assert len(driver.history) == 1
        assert driver.history[0]["action"] == "click"

    def test_double_click_primitive(self, all_mock_drivers):
        driver = all_mock_drivers
        res = driver.double_click(x=150, y=250)
        assert res.success is True
        assert res.action_type == "double_click"
        assert res.params == {"x": 150, "y": 250}
        assert driver.history[0]["action"] == "double_click"

    def test_right_click_primitive(self, all_mock_drivers):
        driver = all_mock_drivers
        res = driver.right_click(x=300, y=400)
        assert res.success is True
        assert res.action_type == "right_click"
        assert res.params == {"x": 300, "y": 400}

    def test_drag_primitive(self, all_mock_drivers):
        driver = all_mock_drivers
        res = driver.drag(start_x=10, start_y=20, end_x=100, end_y=200, duration_ms=600)
        assert res.success is True
        assert res.action_type == "drag"
        assert res.params["start_x"] == 10
        assert res.params["end_x"] == 100
        assert res.params["duration_ms"] == 600

    def test_type_primitive(self, all_mock_drivers):
        driver = all_mock_drivers
        res = driver.type(text="Hello OmniBench!", interval_ms=10)
        assert res.success is True
        assert res.action_type == "type"
        assert res.params["text"] == "Hello OmniBench!"
        assert res.params["interval_ms"] == 10

    def test_key_combination_primitive(self, all_mock_drivers):
        driver = all_mock_drivers
        res = driver.key_combination(keys=["ctrl", "c"])
        assert res.success is True
        assert res.action_type == "key_combination"
        assert res.params["keys"] == ["ctrl", "c"]

    def test_scroll_primitive(self, all_mock_drivers):
        driver = all_mock_drivers
        res = driver.scroll(x=500, y=500, direction="down", amount=3)
        assert res.success is True
        assert res.action_type in ("scroll", "drag")

    def test_wait_primitive(self, all_mock_drivers):
        driver = all_mock_drivers
        t0 = time.perf_counter()
        res = driver.wait(seconds=0.05)
        elapsed = time.perf_counter() - t0
        assert res.success is True
        assert res.action_type == "wait"
        assert res.params["seconds"] == 0.05
        assert elapsed >= 0.04

    def test_execute_action_generic_dispatcher(self, all_mock_drivers):
        driver = all_mock_drivers

        # Click dispatch
        res1 = driver.execute_action("click", {"x": 50, "y": 60, "button": "left"})
        assert res1.success is True
        assert res1.action_type == "click"

        # Double click dispatch
        res2 = driver.execute_action("double_click", {"x": 70, "y": 80})
        assert res2.success is True

        # Type dispatch
        res3 = driver.execute_action("type", {"text": "test dispatch"})
        assert res3.success is True

        # Key combo dispatch
        res4 = driver.execute_action("key_combination", {"keys": ["alt", "tab"]})
        assert res4.success is True

        # Wait dispatch
        res5 = driver.execute_action("wait", {"seconds": 0.01})
        assert res5.success is True

    def test_execute_action_validation_errors(self, all_mock_drivers):
        driver = all_mock_drivers

        # Missing required parameter
        with pytest.raises(ActionExecutionError) as exc_info:
            driver.execute_action("click", {"x": 100})  # missing y
        assert exc_info.value.action_type == "click"

        # Invalid button name
        with pytest.raises(ActionExecutionError):
            driver.execute_action("click", {"x": 10, "y": 20, "button": "invalid_button"})

        # Negative coordinates
        with pytest.raises(ActionExecutionError):
            driver.execute_action("double_click", {"x": -10, "y": 20})

        # Negative wait seconds
        with pytest.raises(ActionExecutionError):
            driver.execute_action("wait", {"seconds": -1.0})

        # Invalid scroll direction
        with pytest.raises(ActionExecutionError):
            driver.execute_action("scroll", {"x": 100, "y": 100, "direction": "sideways"})

        # Unsupported action type
        with pytest.raises(ActionExecutionError) as exc_info2:
            driver.execute_action("unsupported_action", {})
        assert "Unsupported action_type" in str(exc_info2.value)


# --- 2. Test Platform Driver Selection Factory ---

class TestPlatformDriverSelection:
    """Test suite for get_driver factory and platform aliases."""

    def test_get_driver_explicit_names(self):
        assert isinstance(get_driver("linux", mock=True), LinuxDriver)
        assert isinstance(get_driver("windows", mock=True), WindowsDriver)
        assert isinstance(get_driver("macos", mock=True), MacOSDriver)
        assert isinstance(get_driver("android", mock=True), AndroidDriver)
        assert isinstance(get_driver("ios", mock=True), IOSDriver)

    def test_get_driver_aliases(self):
        assert isinstance(get_driver("ubuntu", mock=True), LinuxDriver)
        assert isinstance(get_driver("win32", mock=True), WindowsDriver)
        assert isinstance(get_driver("darwin", mock=True), MacOSDriver)
        assert isinstance(get_driver("adb", mock=True), AndroidDriver)
        assert isinstance(get_driver("simctl", mock=True), IOSDriver)

    def test_get_driver_auto_detection(self):
        driver = get_driver("auto", mock=True)
        assert isinstance(driver, BaseOSDriver)

    def test_get_driver_unsupported_platform(self):
        with pytest.raises(PlatformNotSupportedError) as exc_info:
            get_driver("solaris", mock=True)
        assert exc_info.value.platform == "solaris"


# --- 3. Test Retry Mechanism ---

class TestRetryMechanism:
    """Test suite for @with_retry decorator, jitter backoff, and reconnection."""

    def test_retry_success_first_attempt(self):
        call_count = 0

        @with_retry(max_retries=3, initial_delay=0.01)
        def succeeds_immediately():
            nonlocal call_count
            call_count += 1
            return "ok"

        res = succeeds_immediately()
        assert res == "ok"
        assert call_count == 1

    def test_retry_recovery_after_transient_failures(self):
        call_count = 0

        @with_retry(max_retries=3, initial_delay=0.01, jitter=False)
        def succeeds_on_third_try():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ActionExecutionError("Transient error", action_type="test")
            return "recovered"

        res = succeeds_on_third_try()
        assert res == "recovered"
        assert call_count == 3

    def test_retry_exhaustion_reraises_last_exception(self):
        call_count = 0

        @with_retry(max_retries=2, initial_delay=0.01, jitter=False)
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise DeviceConnectionError("Permanent connection loss")

        with pytest.raises(DeviceConnectionError) as exc_info:
            always_fails()

        assert "Permanent connection loss" in str(exc_info.value)
        assert call_count == 3  # 1 initial + 2 retries

    def test_retry_reconnect_daemon_trigger(self):
        class DummyDriver:
            def __init__(self):
                self.reconnected = False

            def reconnect(self):
                self.reconnected = True

            @with_retry(max_retries=2, initial_delay=0.01, reconnect_on_error=True)
            def action(self):
                if not self.reconnected:
                    raise DeviceConnectionError("Disconnected")
                return "success"

        driver = DummyDriver()
        res = driver.action()
        assert res == "success"
        assert driver.reconnected is True

    def test_platform_not_supported_bypasses_retry(self):
        call_count = 0

        @with_retry(max_retries=3, initial_delay=0.01)
        def throws_unsupported():
            nonlocal call_count
            call_count += 1
            raise PlatformNotSupportedError("Missing binary xdotool")

        with pytest.raises(PlatformNotSupportedError):
            throws_unsupported()

        assert call_count == 1  # No retries for unrecoverable platform errors


# --- 4. Test Exception Hierarchy and Propagation ---

class TestExceptionHierarchyAndPropagation:
    """Test suite for custom exception classes and payload attributes."""

    def test_exception_subclassing(self):
        assert issubclass(PlatformNotSupportedError, DriverException)
        assert issubclass(DeviceConnectionError, DriverException)
        assert issubclass(ActionExecutionError, DriverException)
        assert issubclass(TimeoutError, DriverException)

    def test_platform_not_supported_payload(self):
        err = PlatformNotSupportedError("Binary missing", platform="linux", required_binary="xdotool")
        assert err.message == "Binary missing"
        assert err.platform == "linux"
        assert err.required_binary == "xdotool"
        assert err.details["required_binary"] == "xdotool"

    def test_device_connection_error_payload(self):
        err = DeviceConnectionError("ADB missing", device_id="emulator-5554", daemon_port=5037)
        assert err.device_id == "emulator-5554"
        assert err.daemon_port == 5037
        assert err.details["device_id"] == "emulator-5554"

    def test_action_execution_error_payload(self):
        cause_err = ValueError("Invalid coordinate")
        err = ActionExecutionError("Execution failed", action_type="click", params={"x": -1, "y": 0}, cause=cause_err)
        assert err.action_type == "click"
        assert err.params == {"x": -1, "y": 0}
        assert err.cause == cause_err
        assert "Invalid coordinate" in err.details["cause"]

    def test_timeout_error_payload(self):
        err = TimeoutError("Command timed out", timeout_seconds=10.0, action_type="screenshot")
        assert err.timeout_seconds == 10.0
        assert err.action_type == "screenshot"
        assert err.details["timeout_seconds"] == 10.0


# --- 5. Test Screenshot Capture and Mock Isolation ---

class TestScreenshotCaptureAndMockIsolation:
    """Test suite for screenshot generation and headless environment safety."""

    def test_capture_screenshot_returns_pil_image(self, all_mock_drivers):
        driver = all_mock_drivers
        img = driver.capture_screenshot()
        assert isinstance(img, Image.Image)
        assert img.size == (driver.display_width, driver.display_height)
        assert img.mode == "RGB"

    def test_action_result_dataclass_attributes(self):
        res = ActionResult(
            success=True,
            action_type="click",
            params={"x": 10, "y": 20},
            error_message=None,
            execution_time_ms=12.5,
            metadata={"mock": True},
        )
        assert res.success is True
        assert res.error is None
        assert res.execution_time_ms == 12.5
        assert res.metadata["mock"] is True

    def test_driver_connection_lifecycle(self, all_mock_drivers):
        driver = all_mock_drivers
        driver.connect()
        assert driver.is_connected() is True
        driver.disconnect()
        assert driver.is_connected() is False
