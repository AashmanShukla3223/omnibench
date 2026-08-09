"""Exponential backoff and retry decorator for driver action execution."""

import functools
import logging
import random
import time
from typing import Any, Callable, Optional, Sequence, Type

from omnibench.drivers.base import (
    ActionExecutionError,
    DeviceConnectionError,
    DriverException,
    PlatformNotSupportedError,
    TimeoutError,
)

logger = logging.getLogger(__name__)

DEFAULT_RETRYABLE_EXCEPTIONS: tuple[Type[BaseException], ...] = (
    DeviceConnectionError,
    ActionExecutionError,
    TimeoutError,
    ConnectionError,
    OSError,
)


def with_retry(
    max_retries: int = 3,
    initial_delay: float = 0.5,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Sequence[Type[BaseException]] = DEFAULT_RETRYABLE_EXCEPTIONS,
    reconnect_on_error: bool = True,
) -> Callable:
    """
    Decorator for retrying driver operations with exponential backoff, random jitter,
    and automatic daemon reconnection.

    PlatformNotSupportedError is explicitly bypassed and never retried.
    """
    retryable_tuple = tuple(retryable_exceptions)

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            self_obj = args[0] if args else None
            last_exc: Optional[BaseException] = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except PlatformNotSupportedError:
                    # Unrecoverable platform mismatch or missing system binary: raise immediately
                    raise
                except retryable_tuple as exc:
                    last_exc = exc
                    if attempt == max_retries:
                        logger.error("Operation '%s' failed after %d retries: %s", func.__name__, max_retries, exc)
                        raise last_exc

                    # Optional daemon reconnection trigger
                    if reconnect_on_error and isinstance(exc, DeviceConnectionError) and self_obj is not None:
                        reconnect_fn = getattr(self_obj, "reconnect", None) or getattr(self_obj, "connect", None)
                        if callable(reconnect_fn):
                            try:
                                logger.info("Triggering driver reconnection on attempt %d...", attempt + 1)
                                reconnect_fn()
                            except Exception as rec_err:
                                logger.warning("Reconnection attempt failed: %s", rec_err)

                    # Calculate exponential backoff delay
                    base_delay = initial_delay * (backoff_factor ** attempt)
                    if jitter:
                        actual_delay = base_delay * random.uniform(0.5, 1.5)
                    else:
                        actual_delay = base_delay

                    logger.warning(
                        "Attempt %d/%d for '%s' failed (%s: %s). Retrying in %.3fs...",
                        attempt + 1,
                        max_retries + 1,
                        func.__name__,
                        type(exc).__name__,
                        exc,
                        actual_delay,
                    )
                    time.sleep(actual_delay)

            if last_exc:
                raise last_exc

        return wrapper

    return decorator
