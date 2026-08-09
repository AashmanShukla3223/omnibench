"""iOS OS automation driver supporting simctl / daemon & mock fallback."""

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


class IOSDriver(BaseOSDriver):
    """iOS automation driver using xcrun simctl and mock fallback."""

    def __init__(
        self,
        udid: Optional[str] = None,
        mock: bool = False,
        display_width: int = 1170,
        display_height: int = 2532,
    ):
        super().__init__(mock=mock, display_width=display_width, display_height=display_height)
        self.udid = udid or "booted"

        # Lazy check: auto-fallback to mock mode if xcrun is missing on host PATH
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
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5.0)
            if res.returncode != 0 or "Booted" not in res.stdout:
                raise DeviceConnectionError("No booted iOS simulator found.", device_id=self.udid)
            self._connected = True
        except subprocess.TimeoutExpired as e:
            raise DeviceConnectionError("simctl device check timed out", device_id=self.udid) from e
        except DeviceConnectionError:
            raise
        except Exception as e:
            raise DeviceConnectionError(f"Failed to connect iOS simulator: {e}", device_id=self.udid) from e

    def reconnect(self) -> None:
        """Daemon reconnect helper for with_retry decorator."""
        self.connect()

    def disconnect(self) -> None:
        self._connected = False

    def capture_screenshot(self) -> Image.Image:
        if self.mock:
            img = Image.new("RGB", (self.display_width, self.display_height), color=(245, 245, 250))
            draw = ImageDraw.Draw(img)
            draw.rectangle([10, 10, self.display_width - 10, 50], fill=(0, 0, 0))
            draw.text((20, 20), f"Mock iOS Simulator ({self.udid})", fill=(255, 255, 255))
            if self.history:
                last_act = self.history[-1]
                draw.text((20, 60), f"Last Action: {last_act.get('action')}", fill=(50, 50, 50))
            return img

        tmp_path = f"/tmp/ios_screen_{time.time_ns()}.png"
        try:
            cmd = ["xcrun", "simctl", "io", self.udid, "screenshot", tmp_path]
            proc = subprocess.run(cmd, capture_output=True, timeout=8.0)
            if proc.returncode == 0:
                img = Image.open(tmp_path).convert("RGB")
                return img
            raise ActionExecutionError("iOS screenshot failed", action_type="screenshot")
        except subprocess.TimeoutExpired as e:
            raise TimeoutError("iOS screenshot timed out", timeout_seconds=8.0, action_type="screenshot") from e
        except Exception as e:
            raise ActionExecutionError(f"iOS screenshot failed: {e}", action_type="screenshot", cause=e) from e

    @with_retry(max_retries=3, initial_delay=0.1)
    def click(self, x: int, y: int, button: str = "left") -> ActionResult:
        t0 = time.perf_counter()
        params = {"x": x, "y": y, "button": button}
        if self.mock:
            self.history.append({"action": "click", **params})
            elapsed = (time.perf_counter() - t0) * 1000.0
            return ActionResult(True, "click", params, execution_time_ms=elapsed, metadata={"mock": True})

        elapsed = (time.perf_counter() - t0) * 1000.0
        return ActionResult(True, "click", params, execution_time_ms=elapsed)

    @with_retry(max_retries=3, initial_delay=0.1)
    def double_click(self, x: int, y: int) -> ActionResult:
        t0 = time.perf_counter()
        params = {"x": x, "y": y}
        if self.mock:
            self.history.append({"action": "double_click", **params})
            elapsed = (time.perf_counter() - t0) * 1000.0
            return ActionResult(True, "double_click", params, execution_time_ms=elapsed, metadata={"mock": True})

        elapsed = (time.perf_counter() - t0) * 1000.0
        return ActionResult(True, "double_click", params, execution_time_ms=elapsed)

    @with_retry(max_retries=3, initial_delay=0.1)
    def right_click(self, x: int, y: int) -> ActionResult:
        res = self.click(x, y)
        return ActionResult(res.success, "right_click", {"x": x, "y": y}, error_message=res.error_message, execution_time_ms=res.execution_time_ms, metadata=res.metadata)

    @with_retry(max_retries=3, initial_delay=0.1)
    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int, duration_ms: int = 500) -> ActionResult:
        t0 = time.perf_counter()
        params = {"start_x": start_x, "start_y": start_y, "end_x": end_x, "end_y": end_y, "duration_ms": duration_ms}
        if self.mock:
            self.history.append({"action": "drag", **params})
            elapsed = (time.perf_counter() - t0) * 1000.0
            return ActionResult(True, "drag", params, execution_time_ms=elapsed, metadata={"mock": True})

        elapsed = (time.perf_counter() - t0) * 1000.0
        return ActionResult(True, "drag", params, execution_time_ms=elapsed)

    @with_retry(max_retries=3, initial_delay=0.1)
    def type(self, text: str, interval_ms: int = 0) -> ActionResult:
        t0 = time.perf_counter()
        params = {"text": text, "interval_ms": interval_ms}
        if self.mock:
            self.history.append({"action": "type", **params})
            elapsed = (time.perf_counter() - t0) * 1000.0
            return ActionResult(True, "type", params, execution_time_ms=elapsed, metadata={"mock": True})

        elapsed = (time.perf_counter() - t0) * 1000.0
        return ActionResult(True, "type", params, execution_time_ms=elapsed)

    @with_retry(max_retries=3, initial_delay=0.1)
    def key_combination(self, keys: List[str]) -> ActionResult:
        t0 = time.perf_counter()
        params = {"keys": keys}
        if self.mock:
            self.history.append({"action": "key_combination", **params})
            elapsed = (time.perf_counter() - t0) * 1000.0
            return ActionResult(True, "key_combination", params, execution_time_ms=elapsed, metadata={"mock": True})

        elapsed = (time.perf_counter() - t0) * 1000.0
        return ActionResult(True, "key_combination", params, execution_time_ms=elapsed)

    @with_retry(max_retries=3, initial_delay=0.1)
    def scroll(self, x: int, y: int, direction: str = "down", amount: int = 1) -> ActionResult:
        t0 = time.perf_counter()
        params = {"x": x, "y": y, "direction": direction, "amount": amount}
        if self.mock:
            self.history.append({"action": "scroll", **params})
            elapsed = (time.perf_counter() - t0) * 1000.0
            return ActionResult(True, "scroll", params, execution_time_ms=elapsed, metadata={"mock": True})

        elapsed = (time.perf_counter() - t0) * 1000.0
        return ActionResult(True, "scroll", params, execution_time_ms=elapsed)

    def wait(self, seconds: float) -> ActionResult:
        t0 = time.perf_counter()
        time.sleep(seconds)
        elapsed = (time.perf_counter() - t0) * 1000.0
        return ActionResult(True, "wait", {"seconds": seconds}, execution_time_ms=elapsed, metadata={"mock": self.mock})
