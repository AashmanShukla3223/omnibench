"""
OmniBench Universal Model Gateway — Cascading Router.
Routes GatewayRequests through prioritized adapter chain with automatic fallback.
"""

from __future__ import annotations

import logging
import time
from typing import List, Optional

from omnibench.gateway.protocol import GatewayRequest, GatewayResponse
from omnibench.gateway.adapters import (
    BaseAdapter,
    LocalONNXAdapter,
    MockAdapter,
)

logger = logging.getLogger(__name__)


class CascadingRouter:
    """
    Priority-ordered adapter cascade router.

    On each request:
    1. Tries adapters in priority order (highest first).
    2. If an adapter is unavailable or returns an error, advances to next.
    3. Falls back to LocalONNXAdapter as guaranteed last resort.
    4. Final fallback is MockAdapter for guaranteed non-None response.
    """

    def __init__(
        self,
        adapters: Optional[List[BaseAdapter]] = None,
        local_adapter: Optional[BaseAdapter] = None,
        mock_fallback: bool = True,
    ) -> None:
        self._adapters: List[BaseAdapter] = adapters or []
        self._local_adapter: BaseAdapter = local_adapter or LocalONNXAdapter()
        self._mock_fallback: bool = mock_fallback
        self._mock_adapter: BaseAdapter = MockAdapter()

    def add_adapter(self, adapter: BaseAdapter, priority: int = 0) -> None:
        """Add adapter at given priority position (0 = highest)."""
        self._adapters.insert(priority, adapter)

    def route(self, request: GatewayRequest) -> GatewayResponse:
        """
        Route request through adapter cascade and return first successful response.
        """
        # Build priority chain: external adapters → local ONNX → mock
        chain: List[BaseAdapter] = list(self._adapters)

        # If model_name explicitly targets local, skip external adapters
        if request.model_name not in ("auto", "local", "local_onnx"):
            chain = [a for a in chain if a.name != "local_onnx"]

        chain.append(self._local_adapter)
        if self._mock_fallback:
            chain.append(self._mock_adapter)

        last_error: Optional[str] = None
        for adapter in chain:
            if not adapter.is_available():
                logger.debug("Adapter %s unavailable — skipping.", adapter.name)
                continue
            try:
                t0 = time.perf_counter()
                response = adapter.generate(request)
                latency = (time.perf_counter() - t0) * 1000

                if response.success:
                    logger.debug(
                        "Request routed via %s in %.1f ms", adapter.name, latency
                    )
                    return response
                else:
                    last_error = response.error
                    logger.warning(
                        "Adapter %s returned error: %s", adapter.name, response.error
                    )
            except Exception as exc:
                last_error = str(exc)
                logger.error(
                    "Adapter %s raised exception: %s", adapter.name, exc
                )

        # All adapters failed
        error_msg = f"All adapters failed. Last error: {last_error}"
        logger.error(error_msg)
        return GatewayResponse.error_response(error_msg, "cascade_router")

    def available_providers(self) -> List[str]:
        """Return names of all currently available adapters."""
        all_adapters = list(self._adapters) + [self._local_adapter]
        if self._mock_fallback:
            all_adapters.append(self._mock_adapter)
        return [a.name for a in all_adapters if a.is_available()]
