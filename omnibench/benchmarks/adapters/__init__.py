"""OmniBench Benchmark Adapters — all six benchmark domain adapters."""

from omnibench.benchmarks.adapters.osworld import OSWorldAdapter
from omnibench.benchmarks.adapters.webarena import WebArenaAdapter
from omnibench.benchmarks.adapters.androidworld import AndroidWorldAdapter
from omnibench.benchmarks.adapters.mind2web import Mind2WebAdapter
from omnibench.benchmarks.adapters.gaia import GAIAAdapter
from omnibench.benchmarks.adapters.omnibench_native import OmniBenchNativeAdapter

__all__ = [
    "OSWorldAdapter",
    "WebArenaAdapter",
    "AndroidWorldAdapter",
    "Mind2WebAdapter",
    "GAIAAdapter",
    "OmniBenchNativeAdapter",
]
