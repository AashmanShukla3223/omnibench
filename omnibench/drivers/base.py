"""Base interfaces, data structures, and exceptions for OmniBench OS drivers."""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from PIL import Image


# --- Exception Hierarchy ---

class DriverException(Exception):
    """Base exception for all OmniBench OS driver errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class PlatformNotSupportedError(DriverException):
    """Raised when platform runtime dependencies or host OS are unsupported."""

    def __init__(
        self,
        message: str,
        platform: Optional[str] = None,
        required_binary: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        det = details or {}
        if platform is not None:
            det["platform"] = platform
        if required_binary is not None:
            det["required_binary"] = required_binary
        super().__init__(message, details=det)
        self.platform = platform
        self.required_binary = required_binary


class DeviceConnectionError(DriverException):
    """Raised when device/display server connection fails or drops."""

    def __init__(
        self,
        message: str,
        device_id: Optional[str] = None,
        daemon_port: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        det = details or {}
        if device_id is not None:
            det["device_id"] = device_id
        if daemon_port is not None:
            det["daemon_port"] = daemon_port
        super().__init__(message, details=det)
        self.device_id = device_id
        self.daemon_port = daemon_port


class ActionExecutionError(DriverException):
    """Raised when execution of an action primitive fails."""

    def __init__(
        self,
        message: str,
        action_type: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        det = details or {}
        if action_type is not None:
            det["action_type"] = action_type
        if params is not None:
            det["params"] = params
        if cause is not None:
            det["cause"] = str(cause)
        super().__init__(message, details=det)
        self.action_type = action_type
        self.params = params
        self.cause = cause


class TimeoutError(DriverException):
    """Raised when an action primitive or screenshot operation times out."""

    def __init__(
        self,
        message: str,
        timeout_seconds: Optional[float] = None,
        action_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        det = details or {}
        if timeout_seconds is not None:
            det["timeout_seconds"] = timeout_seconds
        if action_type is not None:
            det["action_type"] = action_type
        super().__init__(message, details=det)
        self.timeout_seconds = timeout_seconds
        self.action_type = action_type


# --- ActionResult Dataclass ---

@dataclass
class ActionResult:
    """Standard result returned by driver action primitive executions."""

    success: bool
    action_type: str
    params: Dict[str, Any]
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def error(self) -> Optional[str]:
        """Alias for error_message."""
        return self.error_message


# --- BaseOSDriver Abstract Base Class ---

class BaseOSDriver(ABC):
    """Abstract base class defining 8 action primitives, screenshot capture, and dispatcher."""

    def __init__(self, mock: bool = False, display_width: int = 1920, display_height: int = 1080):
        self.mock = mock
        self.display_width = display_width
        self.display_height = display_height
        self._connected: bool = False
        self.history: List[Dict[str, Any]] = []

    @property
    @abstractmethod
    def platform(self) -> str:
        """Return platform identifier string ('linux', 'windows', 'macos', 'android', 'ios')."""
        pass

    @abstractmethod
    def connect(self) -> None:
        """Establish connection to display server, daemon, or device."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Release driver resources and terminate daemon connections."""
        pass

    def is_connected(self) -> bool:
        """Return True if driver is active and connected."""
        return self._connected

    @abstractmethod
    def capture_screenshot(self) -> Image.Image:
        """Capture and return the current screen as a PIL Image."""
        pass

    # --- 8 Action Primitives ---

    @abstractmethod
    def click(self, x: int, y: int, button: str = "left") -> ActionResult:
        """Perform click at (x, y). button: 'left', 'right', 'middle'."""
        pass

    @abstractmethod
    def double_click(self, x: int, y: int) -> ActionResult:
        """Perform double click at (x, y)."""
        pass

    @abstractmethod
    def right_click(self, x: int, y: int) -> ActionResult:
        """Perform right click at (x, y)."""
        pass

    @abstractmethod
    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int, duration_ms: int = 500) -> ActionResult:
        """Perform drag/swipe from (start_x, start_y) to (end_x, end_y)."""
        pass

    @abstractmethod
    def type(self, text: str, interval_ms: int = 0) -> ActionResult:
        """Type given text string with optional inter-character interval."""
        pass

    @abstractmethod
    def key_combination(self, keys: List[str]) -> ActionResult:
        """Execute key combination (e.g., ['ctrl', 'c'])."""
        pass

    @abstractmethod
    def scroll(self, x: int, y: int, direction: str = "down", amount: int = 1) -> ActionResult:
        """Scroll at (x, y). direction: 'up', 'down', 'left', 'right'."""
        pass

    @abstractmethod
    def wait(self, seconds: float) -> ActionResult:
        """Pause execution for specified duration in seconds."""
        pass

    # --- Generic Dispatcher & Validation ---

    def execute_action(self, action_type: str, params: Dict[str, Any]) -> ActionResult:
        """
        Validate parameters and dispatch action to appropriate primitive method.
        Measures execution time and wraps validation errors in ActionExecutionError.
        """
        if not isinstance(action_type, str):
            raise ActionExecutionError("Action type must be a string", action_type=str(action_type), params=params)

        norm_action = action_type.strip().lower()

        t_start = time.perf_counter()

        try:
            if norm_action == "click":
                if "x" not in params or "y" not in params:
                    raise KeyError("x and y")
                x, y = int(params["x"]), int(params["y"])
                if x < 0 or y < 0:
                    raise ValueError(f"Coordinates x, y must be non-negative: ({x}, {y})")
                button = str(params.get("button", "left")).lower()
                if button not in ("left", "right", "middle"):
                    raise ValueError(f"Invalid click button: '{button}'")
                res = self.click(x=x, y=y, button=button)

            elif norm_action == "double_click":
                if "x" not in params or "y" not in params:
                    raise KeyError("x and y")
                x, y = int(params["x"]), int(params["y"])
                if x < 0 or y < 0:
                    raise ValueError(f"Coordinates x, y must be non-negative: ({x}, {y})")
                res = self.double_click(x=x, y=y)

            elif norm_action == "right_click":
                if "x" not in params or "y" not in params:
                    raise KeyError("x and y")
                x, y = int(params["x"]), int(params["y"])
                if x < 0 or y < 0:
                    raise ValueError(f"Coordinates x, y must be non-negative: ({x}, {y})")
                res = self.right_click(x=x, y=y)

            elif norm_action == "drag":
                for k in ("start_x", "start_y", "end_x", "end_y"):
                    if k not in params:
                        raise KeyError(k)
                sx, sy = int(params["start_x"]), int(params["start_y"])
                ex, ey = int(params["end_x"]), int(params["end_y"])
                if sx < 0 or sy < 0 or ex < 0 or ey < 0:
                    raise ValueError(f"Drag coordinates must be non-negative: ({sx},{sy}) -> ({ex},{ey})")
                duration = int(params.get("duration_ms", 500))
                if duration < 0:
                    raise ValueError(f"duration_ms must be non-negative: {duration}")
                res = self.drag(start_x=sx, start_y=sy, end_x=ex, end_y=ey, duration_ms=duration)

            elif norm_action == "type":
                if "text" not in params:
                    raise KeyError("text")
                text = params["text"]
                if not isinstance(text, str):
                    raise ValueError(f"text parameter must be a string, got {type(text)}")
                interval = int(params.get("interval_ms", 0))
                if interval < 0:
                    raise ValueError(f"interval_ms must be non-negative: {interval}")
                res = self.type(text=text, interval_ms=interval)

            elif norm_action == "key_combination":
                if "keys" not in params:
                    raise KeyError("keys")
                keys = params["keys"]
                if not isinstance(keys, list) or len(keys) == 0:
                    raise ValueError("keys parameter must be a non-empty list of key names")
                res = self.key_combination(keys=[str(k) for k in keys])

            elif norm_action == "scroll":
                if "x" not in params or "y" not in params:
                    raise KeyError("x and y")
                x, y = int(params["x"]), int(params["y"])
                if x < 0 or y < 0:
                    raise ValueError(f"Scroll coordinates must be non-negative: ({x}, {y})")
                direction = str(params.get("direction", "down")).lower()
                if direction not in ("up", "down", "left", "right"):
                    raise ValueError(f"Invalid scroll direction: '{direction}'")
                amount = int(params.get("amount", 1))
                if amount <= 0:
                    raise ValueError(f"Scroll amount must be positive: {amount}")
                res = self.scroll(x=x, y=y, direction=direction, amount=amount)

            elif norm_action == "wait":
                seconds = float(params.get("seconds", 0.5))
                if seconds < 0.0:
                    raise ValueError(f"Wait seconds must be non-negative: {seconds}")
                res = self.wait(seconds=seconds)

            elif norm_action == "call_contact" or norm_action == "call":
                contact = str(params.get("contact", params.get("contact_name", "Vanya Chaudhary")))
                call_fn = getattr(self, "call_contact", None)
                if callable(call_fn):
                    res = call_fn(contact)
                else:
                    res = ActionResult(True, "call_contact", params, metadata={"mock": getattr(self, "mock", True)})

            elif norm_action == "launch_app":
                pkg = str(params.get("package_name", params.get("app", "com.samsung.android.dialer")))
                launch_fn = getattr(self, "launch_app", None)
                if callable(launch_fn):
                    res = launch_fn(pkg)
                else:
                    res = ActionResult(True, "launch_app", params, metadata={"mock": getattr(self, "mock", True)})

            else:
                raise ActionExecutionError(
                    f"Unsupported action_type: '{action_type}'",
                    action_type=action_type,
                    params=params,
                )

            t_elapsed_ms = (time.perf_counter() - t_start) * 1000.0
            if res.execution_time_ms <= 0.0:
                res.execution_time_ms = t_elapsed_ms
            return res

        except KeyError as e:
            raise ActionExecutionError(
                f"Missing required parameter {e} for action '{action_type}'",
                action_type=action_type,
                params=params,
                cause=e,
            ) from e
        except ValueError as e:
            raise ActionExecutionError(
                f"Invalid parameter value for action '{action_type}': {e}",
                action_type=action_type,
                params=params,
                cause=e,
            ) from e
        except DriverException:
            raise
        except Exception as e:
            raise ActionExecutionError(
                f"Execution of '{action_type}' failed: {e}",
                action_type=action_type,
                params=params,
                cause=e,
            ) from e
