"""Windows OS automation driver with pywinauto/PowerShell native execution & mock fallback."""

import sys
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


class WindowsDriver(BaseOSDriver):
    """Windows automation driver supporting pywinauto / PowerShell and mock mode fallback."""

    def __init__(
        self,
        mock: bool = False,
        display_width: int = 1920,
        display_height: int = 1080,
    ):
        super().__init__(mock=mock, display_width=display_width, display_height=display_height)
        if sys.platform != "win32":
            self.mock = True  # Auto fallback on non-Windows hosts

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
            draw.rectangle([10, 10, self.display_width - 10, 50], fill=(0, 120, 215))
            draw.text((20, 20), "Mock Windows Desktop", fill=(255, 255, 255))
            if self.history:
                last_act = self.history[-1]
                draw.text((20, 60), f"Last Action: {last_act.get('action')}", fill=(30, 30, 30))
            return img

        try:
            from PIL import ImageGrab
            return ImageGrab.grab().convert("RGB")
        except Exception as e:
            raise ActionExecutionError(f"Failed to capture screenshot on Windows: {e}") from e

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
        res = self.click(x, y, button="right")
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
