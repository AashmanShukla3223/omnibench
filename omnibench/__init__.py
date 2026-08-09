"""OmniBench top-level package."""

__version__ = "1.0.0"
__author__ = "OmniBench Team"

# Lazy imports to avoid pulling heavy deps at package import time
import importlib

__all__ = [
    "engine",
    "gateway",
    "drivers",
    "visual",
    "evaluators",
    "benchmarks",
    "telemetry",
    "cli",
    "dashboard",
]


def __getattr__(name: str):
    if name in __all__:
        return importlib.import_module(f"omnibench.{name}")
    raise AttributeError(f"module 'omnibench' has no attribute '{name}'")

