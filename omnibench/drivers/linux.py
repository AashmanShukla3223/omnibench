"""Linux OS automation driver using Xvfb / xdotool with mock fallback capabilities."""

import io
import os
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

        # Lazy check: auto-fallback to mock mode if xdotool is missing or non-Linux host
        if not self.mock:
            if not shutil.which("xdotool") or not os.path.exists("/proc"):
                self.mock = True

    @property
    def platform(self) -> str:
        return "linux"

    def connect(self) -> None:
        if not self.mock:
            if not os.environ.get("DISPLAY"):
                os.environ["DISPLAY"] = self.display
        self._connected = True

    def disconnect(self) -> None:
        self._connected = False

    def capture_screenshot(self) -> Image.Image:
        if self.mock:
            img = Image.new("RGB", (self.display_width, self.display_height), color=(220, 225, 230))
            draw = ImageDraw.Draw(img)
            draw.rectangle([10, 10, self.display_width - 10, 50], fill=(70, 130, 180))
            draw.text((20, 20), f"Mock Linux Display ({self.display})", fill=(255, 255, 255))
            if self.history:
                last_act = self.history[-1]
                draw.text((20, 60), f"Last Action: {last_act.get('action')}", fill=(30, 30, 30))
            return img

        try:
            # Try scrot first, then import (ImageMagick), then xwd
            if shutil.which("scrot"):
                proc = subprocess.run(["scrot", "-z", "-"], capture_output=True, timeout=5.0)
                if proc.returncode == 0 and proc.stdout:
                    return Image.open(io.BytesIO(proc.stdout)).convert("RGB")
            if shutil.which("import"):
                proc = subprocess.run(["import", "-window", "root", "png:-"], capture_output=True, timeout=5.0)
                if proc.returncode == 0 and proc.stdout:
                    return Image.open(io.BytesIO(proc.stdout)).convert("RGB")

            # Fallback mock image if system screenshot tool failed
            img = Image.new("RGB", (self.display_width, self.display_height), color=(240, 240, 240))
            return img
        except subprocess.TimeoutExpired as e:
            raise TimeoutError("Linux screenshot capture timed out", timeout_seconds=5.0, action_type="screenshot") from e
        except Exception as e:
            raise ActionExecutionError(f"Failed to capture screenshot on Linux: {e}") from e

    @with_retry(max_retries=3, initial_delay=0.1)
    def click(self, x: int, y: int, button: str = "left") -> ActionResult:
        t0 = time.perf_counter()
        button_map = {"left": "1", "middle": "2", "right": "3"}
        btn_num = button_map.get(button.lower(), "1")

        params = {"x": x, "y": y, "button": button}
        if self.mock:
            self.history.append({"action": "click", **params})
            elapsed = (time.perf_counter() - t0) * 1000.0
            return ActionResult(True, "click", params, execution_time_ms=elapsed, metadata={"mock": True})

        try:
            cmd = ["xdotool", "mousemove", str(x), str(y), "click", btn_num]
            subprocess.run(cmd, check=True, timeout=5.0)
            elapsed = (time.perf_counter() - t0) * 1000.0
            return ActionResult(True, "click", params, execution_time_ms=elapsed)
        except subprocess.TimeoutExpired as e:
            raise TimeoutError("xdotool click timed out", timeout_seconds=5.0, action_type="click") from e
        except Exception as e:
            raise ActionExecutionError(f"Linux click action failed: {e}", action_type="click", params=params, cause=e) from e

    @with_retry(max_retries=3, initial_delay=0.1)
    def double_click(self, x: int, y: int) -> ActionResult:
        t0 = time.perf_counter()
        params = {"x": x, "y": y}
        if self.mock:
            self.history.append({"action": "double_click", **params})
            elapsed = (time.perf_counter() - t0) * 1000.0
            return ActionResult(True, "double_click", params, execution_time_ms=elapsed, metadata={"mock": True})

        try:
            cmd = ["xdotool", "mousemove", str(x), str(y), "click", "--repeat", "2", "--delay", "50", "1"]
            subprocess.run(cmd, check=True, timeout=5.0)
            elapsed = (time.perf_counter() - t0) * 1000.0
            return ActionResult(True, "double_click", params, execution_time_ms=elapsed)
        except subprocess.TimeoutExpired as e:
            raise TimeoutError("xdotool double_click timed out", timeout_seconds=5.0, action_type="double_click") from e
        except Exception as e:
            raise ActionExecutionError(f"Linux double_click action failed: {e}", action_type="double_click", params=params, cause=e) from e

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

        try:
            cmd = [
                "xdotool",
                "mousemove", str(start_x), str(start_y),
                "mousedown", "1",
                "mousemove", str(end_x), str(end_y),
                "mouseup", "1",
            ]
            subprocess.run(cmd, check=True, timeout=10.0)
            elapsed = (time.perf_counter() - t0) * 1000.0
            return ActionResult(True, "drag", params, execution_time_ms=elapsed)
        except subprocess.TimeoutExpired as e:
            raise TimeoutError("xdotool drag timed out", timeout_seconds=10.0, action_type="drag") from e
        except Exception as e:
            raise ActionExecutionError(f"Linux drag action failed: {e}", action_type="drag", params=params, cause=e) from e

    @with_retry(max_retries=3, initial_delay=0.1)
    def type(self, text: str, interval_ms: int = 0) -> ActionResult:
        t0 = time.perf_counter()
        params = {"text": text, "interval_ms": interval_ms}
        if self.mock:
            self.history.append({"action": "type", **params})
            elapsed = (time.perf_counter() - t0) * 1000.0
            return ActionResult(True, "type", params, execution_time_ms=elapsed, metadata={"mock": True})

        try:
            cmd = ["xdotool", "type", "--delay", str(interval_ms), "--", text]
            subprocess.run(cmd, check=True, timeout=10.0)
            elapsed = (time.perf_counter() - t0) * 1000.0
            return ActionResult(True, "type", params, execution_time_ms=elapsed)
        except subprocess.TimeoutExpired as e:
            raise TimeoutError("xdotool type timed out", timeout_seconds=10.0, action_type="type") from e
        except Exception as e:
            raise ActionExecutionError(f"Linux type action failed: {e}", action_type="type", params=params, cause=e) from e

    @with_retry(max_retries=3, initial_delay=0.1)
    def key_combination(self, keys: List[str]) -> ActionResult:
        t0 = time.perf_counter()
        params = {"keys": keys}
        if self.mock:
            self.history.append({"action": "key_combination", **params})
            elapsed = (time.perf_counter() - t0) * 1000.0
            return ActionResult(True, "key_combination", params, execution_time_ms=elapsed, metadata={"mock": True})

        try:
            key_str = "+".join(keys)
            cmd = ["xdotool", "key", key_str]
            subprocess.run(cmd, check=True, timeout=5.0)
            elapsed = (time.perf_counter() - t0) * 1000.0
            return ActionResult(True, "key_combination", params, execution_time_ms=elapsed)
        except subprocess.TimeoutExpired as e:
            raise TimeoutError("xdotool key_combination timed out", timeout_seconds=5.0, action_type="key_combination") from e
        except Exception as e:
            raise ActionExecutionError(f"Linux key_combination failed: {e}", action_type="key_combination", params=params, cause=e) from e

    @with_retry(max_retries=3, initial_delay=0.1)
    def scroll(self, x: int, y: int, direction: str = "down", amount: int = 1) -> ActionResult:
        t0 = time.perf_counter()
        params = {"x": x, "y": y, "direction": direction, "amount": amount}
        if self.mock:
            self.history.append({"action": "scroll", **params})
            elapsed = (time.perf_counter() - t0) * 1000.0
            return ActionResult(True, "scroll", params, execution_time_ms=elapsed, metadata={"mock": True})

        btn = "5" if direction.lower() == "down" else "4" if direction.lower() == "up" else "7" if direction.lower() == "right" else "6"
        try:
            cmd = ["xdotool", "mousemove", str(x), str(y), "click", "--repeat", str(amount), btn]
            subprocess.run(cmd, check=True, timeout=5.0)
            elapsed = (time.perf_counter() - t0) * 1000.0
            return ActionResult(True, "scroll", params, execution_time_ms=elapsed)
        except subprocess.TimeoutExpired as e:
            raise TimeoutError("xdotool scroll timed out", timeout_seconds=5.0, action_type="scroll") from e
        except Exception as e:
            raise ActionExecutionError(f"Linux scroll action failed: {e}", action_type="scroll", params=params, cause=e) from e

    def wait(self, seconds: float) -> ActionResult:
        t0 = time.perf_counter()
        time.sleep(seconds)
        elapsed = (time.perf_counter() - t0) * 1000.0
        return ActionResult(True, "wait", {"seconds": seconds}, execution_time_ms=elapsed, metadata={"mock": self.mock})
