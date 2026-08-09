"""OmniBench OS Drivers package initialization and public exports."""

import sys
from typing import Optional

from omnibench.drivers.android import AndroidDriver
from omnibench.drivers.base import (
    ActionExecutionError,
    ActionResult,
    BaseOSDriver,
    DeviceConnectionError,
    DriverException,
    PlatformNotSupportedError,
    TimeoutError,
)
from omnibench.drivers.ios import IOSDriver
from omnibench.drivers.linux import LinuxDriver
from omnibench.drivers.macos import MacOSDriver
from omnibench.drivers.retry import with_retry
from omnibench.drivers.windows import WindowsDriver


def get_driver(platform_name: Optional[str] = None, mock: bool = False, **kwargs) -> BaseOSDriver:
    """
    Factory function to retrieve the appropriate OS driver instance.

    Args:
        platform_name: Platform identifier ('auto', 'linux', 'windows', 'macos', 'android', 'ios').
                       If None or 'auto', auto-detects from host OS.
        mock: Force driver into mock mode if True.
        **kwargs: Additional driver parameters (display_width, display_height, device_id, udid, etc.).

    Returns:
        Instance of BaseOSDriver concrete subclass.
    """
    target = (platform_name or "auto").strip().lower()

    if target in ("auto", "host"):
        if sys.platform.startswith("linux"):
            target = "linux"
        elif sys.platform == "win32":
            target = "windows"
        elif sys.platform == "darwin":
            target = "macos"
        else:
            raise PlatformNotSupportedError(f"Unsupported host platform: {sys.platform}", platform=sys.platform)

    driver_map = {
        "linux": LinuxDriver,
        "ubuntu": LinuxDriver,
        "debian": LinuxDriver,
        "xvfb": LinuxDriver,
        "windows": WindowsDriver,
        "win": WindowsDriver,
        "win32": WindowsDriver,
        "win64": WindowsDriver,
        "macos": MacOSDriver,
        "mac": MacOSDriver,
        "darwin": MacOSDriver,
        "osx": MacOSDriver,
        "android": AndroidDriver,
        "adb": AndroidDriver,
        "ios": IOSDriver,
        "simctl": IOSDriver,
        "iphoneos": IOSDriver,
    }

    if target not in driver_map:
        raise PlatformNotSupportedError(f"Unknown driver platform '{platform_name}'.", platform=platform_name)

    driver_cls = driver_map[target]
    return driver_cls(mock=mock, **kwargs)


__all__ = [
    "BaseOSDriver",
    "ActionResult",
    "DriverException",
    "PlatformNotSupportedError",
    "DeviceConnectionError",
    "ActionExecutionError",
    "TimeoutError",
    "LinuxDriver",
    "WindowsDriver",
    "MacOSDriver",
    "AndroidDriver",
    "IOSDriver",
    "with_retry",
    "get_driver",
]
