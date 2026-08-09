"""Android OS automation driver supporting ADB CLI / uiautomator & mock fallback."""

import io
import shutil
import subprocess
import time
from typing import Any, Dict, List, Optional
from PIL import Image, ImageDraw

from omnibench.drivers.base import (
    ActionExecutionError,
    ActionResult,
    BaseOSDriver,
    DeviceConnectionError,
    PlatformNotSupportedError,
    TimeoutError,
)
from omnibench.drivers.retry import with_retry


class AndroidDriver(BaseOSDriver):
    """Android automation driver using ADB shell commands with mock fallback."""

    def __init__(
        self,
        device_id: Optional[str] = None,
        mock: bool = False,
        display_width: int = 1080,
        display_height: int = 2400,
    ):
        super().__init__(mock=mock, display_width=display_width, display_height=display_height)
        self.device_id = device_id

        # Lazy check: auto-fallback to mock mode if adb CLI is missing on host PATH
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

        cmd = ["adb"]
        if self.device_id:
            cmd.extend(["-s", self.device_id])
        cmd.extend(["devices"])

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5.0)
            if res.returncode != 0 or "device" not in res.stdout:
                raise DeviceConnectionError("No ADB device found connected.", device_id=self.device_id)
            self._connected = True
        except subprocess.TimeoutExpired as e:
            raise DeviceConnectionError("ADB connection check timed out", device_id=self.device_id) from e
        except DeviceConnectionError:
            raise
        except Exception as e:
            raise DeviceConnectionError(f"Failed to connect ADB device: {e}", device_id=self.device_id) from e

    def reconnect(self) -> None:
        """Daemon reconnect helper for with_retry decorator."""
        self.connect()

    def disconnect(self) -> None:
        self._connected = False

    def capture_screenshot(self) -> Image.Image:
        if self.mock:
            img = Image.new("RGB", (self.display_width, self.display_height), color=(250, 245, 235))
            draw = ImageDraw.Draw(img)
            draw.rectangle([10, 10, self.display_width - 10, 50], fill=(60, 179, 113))
            draw.text((20, 20), f"Mock Android ({self.device_id or 'default'})", fill=(255, 255, 255))
            if self.history:
                last_act = self.history[-1]
                draw.text((20, 60), f"Last Action: {last_act.get('action')}", fill=(40, 40, 40))
            return img

        cmd = ["adb"]
        if self.device_id:
            cmd.extend(["-s", self.device_id])
        cmd.extend(["exec-out", "screencap", "-p"])

        try:
            res = subprocess.run(cmd, capture_output=True, timeout=8.0)
            if res.returncode != 0 or not res.stdout:
                raise ActionExecutionError("ADB screencap failed", action_type="screenshot")
            # Strip potential carriage returns from adb piping
            clean_bytes = res.stdout.replace(b"\r\r\n", b"\n").replace(b"\r\n", b"\n")
            return Image.open(io.BytesIO(clean_bytes)).convert("RGB")
        except subprocess.TimeoutExpired as e:
            raise TimeoutError("ADB screencap timed out", timeout_seconds=8.0, action_type="screenshot") from e
        except Exception as e:
            raise ActionExecutionError(f"ADB screencap failed: {e}", action_type="screenshot", cause=e) from e

    def _adb_shell(self, args: List[str]) -> subprocess.CompletedProcess:
        cmd = ["adb"]
        if self.device_id:
            cmd.extend(["-s", self.device_id])
        cmd.extend(["shell"] + args)
        return subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=10.0)

    @with_retry(max_retries=3, initial_delay=0.1)
    def click(self, x: int, y: int, button: str = "left") -> ActionResult:
        t0 = time.perf_counter()
        params = {"x": x, "y": y, "button": button}
        if self.mock:
            self.history.append({"action": "click", **params})
            elapsed = (time.perf_counter() - t0) * 1000.0
            return ActionResult(True, "click", params, execution_time_ms=elapsed, metadata={"mock": True})

        try:
            self._adb_shell(["input", "tap", str(x), str(y)])
            elapsed = (time.perf_counter() - t0) * 1000.0
            return ActionResult(True, "click", params, execution_time_ms=elapsed)
        except subprocess.TimeoutExpired as e:
            raise TimeoutError("ADB tap timed out", timeout_seconds=10.0, action_type="click") from e
        except Exception as e:
            raise ActionExecutionError(f"ADB tap failed: {e}", action_type="click", params=params, cause=e) from e

    @with_retry(max_retries=3, initial_delay=0.1)
    def double_click(self, x: int, y: int) -> ActionResult:
        t0 = time.perf_counter()
        params = {"x": x, "y": y}
        if self.mock:
            self.history.append({"action": "double_click", **params})
            elapsed = (time.perf_counter() - t0) * 1000.0
            return ActionResult(True, "double_click", params, execution_time_ms=elapsed, metadata={"mock": True})

        try:
            self._adb_shell(["input", "tap", str(x), str(y)])
            self._adb_shell(["input", "tap", str(x), str(y)])
            elapsed = (time.perf_counter() - t0) * 1000.0
            return ActionResult(True, "double_click", params, execution_time_ms=elapsed)
        except subprocess.TimeoutExpired as e:
            raise TimeoutError("ADB double tap timed out", timeout_seconds=10.0, action_type="double_click") from e
        except Exception as e:
            raise ActionExecutionError(f"ADB double tap failed: {e}", action_type="double_click", params=params, cause=e) from e

    @with_retry(max_retries=3, initial_delay=0.1)
    def right_click(self, x: int, y: int) -> ActionResult:
        t0 = time.perf_counter()
        params = {"x": x, "y": y}
        if self.mock:
            self.history.append({"action": "right_click", **params})
            elapsed = (time.perf_counter() - t0) * 1000.0
            return ActionResult(True, "right_click", params, execution_time_ms=elapsed, metadata={"mock": True})

        res = self.drag(start_x=x, start_y=y, end_x=x, end_y=y, duration_ms=1000)
        return ActionResult(res.success, "right_click", params, execution_time_ms=res.execution_time_ms)

    @with_retry(max_retries=3, initial_delay=0.1)
    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int, duration_ms: int = 500) -> ActionResult:
        t0 = time.perf_counter()
        params = {"start_x": start_x, "start_y": start_y, "end_x": end_x, "end_y": end_y, "duration_ms": duration_ms}
        if self.mock:
            self.history.append({"action": "drag", **params})
            elapsed = (time.perf_counter() - t0) * 1000.0
            return ActionResult(True, "drag", params, execution_time_ms=elapsed, metadata={"mock": True})

        try:
            self._adb_shell(["input", "swipe", str(start_x), str(start_y), str(end_x), str(end_y), str(duration_ms)])
            elapsed = (time.perf_counter() - t0) * 1000.0
            return ActionResult(True, "drag", params, execution_time_ms=elapsed)
        except subprocess.TimeoutExpired as e:
            raise TimeoutError("ADB swipe timed out", timeout_seconds=10.0, action_type="drag") from e
        except Exception as e:
            raise ActionExecutionError(f"ADB swipe failed: {e}", action_type="drag", params=params, cause=e) from e

    @with_retry(max_retries=3, initial_delay=0.1)
    def type(self, text: str, interval_ms: int = 0) -> ActionResult:
        t0 = time.perf_counter()
        params = {"text": text, "interval_ms": interval_ms}
        if self.mock:
            self.history.append({"action": "type", **params})
            elapsed = (time.perf_counter() - t0) * 1000.0
            return ActionResult(True, "type", params, execution_time_ms=elapsed, metadata={"mock": True})

        try:
            escaped = text.replace(" ", "%s")
            self._adb_shell(["input", "text", escaped])
            elapsed = (time.perf_counter() - t0) * 1000.0
            return ActionResult(True, "type", params, execution_time_ms=elapsed)
        except subprocess.TimeoutExpired as e:
            raise TimeoutError("ADB text input timed out", timeout_seconds=10.0, action_type="type") from e
        except Exception as e:
            raise ActionExecutionError(f"ADB text input failed: {e}", action_type="type", params=params, cause=e) from e

    @with_retry(max_retries=3, initial_delay=0.1)
    def key_combination(self, keys: List[str]) -> ActionResult:
        t0 = time.perf_counter()
        params = {"keys": keys}
        if self.mock:
            self.history.append({"action": "key_combination", **params})
            elapsed = (time.perf_counter() - t0) * 1000.0
            return ActionResult(True, "key_combination", params, execution_time_ms=elapsed, metadata={"mock": True})

        try:
            for key in keys:
                key_code = f"KEYCODE_{key.upper()}"
                self._adb_shell(["input", "keyevent", key_code])
            elapsed = (time.perf_counter() - t0) * 1000.0
            return ActionResult(True, "key_combination", params, execution_time_ms=elapsed)
        except subprocess.TimeoutExpired as e:
            raise TimeoutError("ADB keyevent timed out", timeout_seconds=10.0, action_type="key_combination") from e
        except Exception as e:
            raise ActionExecutionError(f"ADB keyevent failed: {e}", action_type="key_combination", params=params, cause=e) from e

    @with_retry(max_retries=3, initial_delay=0.1)
    def scroll(self, x: int, y: int, direction: str = "down", amount: int = 1) -> ActionResult:
        t0 = time.perf_counter()
        params = {"x": x, "y": y, "direction": direction, "amount": amount}
        if self.mock:
            self.history.append({"action": "scroll", **params})
            elapsed = (time.perf_counter() - t0) * 1000.0
            return ActionResult(True, "scroll", params, execution_time_ms=elapsed, metadata={"mock": True})

        dy = 300 * amount
        end_y = max(0, y - dy) if direction.lower() == "down" else y + dy
        return self.drag(start_x=x, start_y=y, end_x=x, end_y=end_y, duration_ms=300)

    def wait(self, seconds: float) -> ActionResult:
        t0 = time.perf_counter()
        time.sleep(seconds)
        elapsed = (time.perf_counter() - t0) * 1000.0
        return ActionResult(True, "wait", {"seconds": seconds}, execution_time_ms=elapsed, metadata={"mock": self.mock})

    @with_retry(max_retries=3, initial_delay=0.1)
    def call_contact(self, contact_name_or_number: str) -> ActionResult:
        """Initiate phone call via Android intent or dialer app (e.g. Samsung Dialer)."""
        t0 = time.perf_counter()
        params = {"contact": contact_name_or_number}
        if self.mock:
            self.history.append({"action": "call_contact", **params})
            elapsed = (time.perf_counter() - t0) * 1000.0
            return ActionResult(True, "call_contact", params, execution_time_ms=elapsed, metadata={"mock": True, "status": f"Calling {contact_name_or_number}"})

        try:
            # Check if parameter is a phone number vs contact name search
            clean_num = "".join(c for c in contact_name_or_number if c.isdigit() or c == "+")
            if clean_num and len(clean_num) >= 3:
                self._adb_shell(["am", "start", "-a", "android.intent.action.CALL", "-d", f"tel:{clean_num}"])
            else:
                # Open Contacts search for name (e.g., Vanya Chaudhary)
                self._adb_shell(["am", "start", "-a", "android.intent.action.VIEW", "content://contacts/people"])
                time.sleep(1.0)
                self.type(contact_name_or_number)
            elapsed = (time.perf_counter() - t0) * 1000.0
            return ActionResult(True, "call_contact", params, execution_time_ms=elapsed)
        except Exception as e:
            raise ActionExecutionError(f"ADB call intent failed: {e}", action_type="call_contact", params=params, cause=e) from e

    @with_retry(max_retries=3, initial_delay=0.1)
    def launch_app(self, package_name: str) -> ActionResult:
        """Launch an Android app by package name (e.g., com.samsung.android.dialer)."""
        t0 = time.perf_counter()
        params = {"package_name": package_name}
        if self.mock:
            self.history.append({"action": "launch_app", **params})
            elapsed = (time.perf_counter() - t0) * 1000.0
            return ActionResult(True, "launch_app", params, execution_time_ms=elapsed, metadata={"mock": True})

        try:
            self._adb_shell(["monkey", "-p", package_name, "-c", "android.intent.category.LAUNCHER", "1"])
            elapsed = (time.perf_counter() - t0) * 1000.0
            return ActionResult(True, "launch_app", params, execution_time_ms=elapsed)
        except Exception as e:
            raise ActionExecutionError(f"ADB launch_app failed: {e}", action_type="launch_app", params=params, cause=e) from e

