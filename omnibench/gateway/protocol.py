"""
OmniBench Universal Model Gateway — Protocol schemas.
Defines GatewayRequest and GatewayResponse Pydantic contracts.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class GatewayRequest:
    """Unified request schema for all model providers."""

    prompt: str
    images: List[bytes] = field(default_factory=list)
    temperature: float = 0.1
    max_tokens: int = 256
    model_name: str = "auto"
    system_prompt: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.prompt, str):
            raise TypeError(f"prompt must be str, got {type(self.prompt)}")
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError(f"temperature must be in [0.0, 2.0], got {self.temperature}")
        if self.max_tokens < 1:
            raise ValueError(f"max_tokens must be >= 1, got {self.max_tokens}")


@dataclass
class GatewayResponse:
    """Unified response schema returned by all model providers."""

    text: str
    action_json: Dict[str, Any]
    usage_tokens: int
    latency_ms: float
    provider_used: str
    model_name: str = "unknown"
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return self.error is None

    @classmethod
    def error_response(
        cls,
        error_message: str,
        provider: str = "unknown",
        latency_ms: float = 0.0,
    ) -> "GatewayResponse":
        return cls(
            text="",
            action_json={},
            usage_tokens=0,
            latency_ms=latency_ms,
            provider_used=provider,
            error=error_message,
        )
