"""
OmniBench Universal Model Gateway — Adapters.
Implements adapters for: OpenAI, Anthropic Claude, Gemini, Ollama (local),
Local ONNX engine, and Mock (offline testing).
"""

from __future__ import annotations

import io
import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from omnibench.gateway.protocol import GatewayRequest, GatewayResponse

logger = logging.getLogger(__name__)


class BaseAdapter(ABC):
    """Abstract base for all model provider adapters."""

    name: str = "base"

    @abstractmethod
    def generate(self, request: GatewayRequest) -> GatewayResponse:
        """Execute inference and return GatewayResponse."""
        pass

    def is_available(self) -> bool:
        """Return True if this adapter's provider is reachable."""
        return True

    def _parse_action(self, text: str) -> Dict[str, Any]:
        """Extract JSON action dict from model output text."""
        import re
        match = re.search(r"\{[^{}]+\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return {"action": "wait", "params": {"seconds": 0.0}, "raw": text}


class MockAdapter(BaseAdapter):
    """
    Offline mock adapter for CI/testing without real API keys.
    Returns deterministic action JSON based on prompt hash.
    """

    name = "mock"

    def __init__(self, latency_ms: float = 50.0) -> None:
        self.latency_ms = latency_ms

    def generate(self, request: GatewayRequest) -> GatewayResponse:
        t0 = time.perf_counter()
        # Deterministic response based on prompt content
        prompt_hash = hash(request.prompt) % 1000
        x = (prompt_hash * 7) % 1000
        y = (prompt_hash * 13) % 1000
        text = json.dumps({
            "action": "click",
            "params": {"x": x, "y": y, "button": "left"},
        })
        latency = (time.perf_counter() - t0) * 1000 + self.latency_ms
        return GatewayResponse(
            text=text,
            action_json=self._parse_action(text),
            usage_tokens=len(request.prompt.split()),
            latency_ms=latency,
            provider_used="mock",
            model_name="mock-v1",
        )

    def is_available(self) -> bool:
        return True


class LocalONNXAdapter(BaseAdapter):
    """Adapter wrapping the local 100M parameter ONNX inference engine."""

    name = "local_onnx"

    def __init__(self, engine: Optional[Any] = None) -> None:
        self._engine = engine
        self._engine_loaded = False

    def _ensure_loaded(self) -> None:
        if self._engine is None:
            from omnibench.engine.onnx_engine import ONNXEngine, EngineConfig
            self._engine = ONNXEngine(EngineConfig())
        if not self._engine_loaded:
            self._engine.load()
            self._engine_loaded = True

    def generate(self, request: GatewayRequest) -> GatewayResponse:
        t0 = time.perf_counter()
        try:
            self._ensure_loaded()
            images = []
            for img_bytes in request.images:
                from PIL import Image
                images.append(Image.open(io.BytesIO(img_bytes)).convert("RGB"))

            result = self._engine.generate(
                prompt=request.prompt,
                images=images if images else None,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )
            latency = (time.perf_counter() - t0) * 1000
            return GatewayResponse(
                text=result.text,
                action_json=result.action_json,
                usage_tokens=result.tokens_generated,
                latency_ms=latency,
                provider_used="local_onnx",
                model_name="omnibench-100m",
                metadata={"memory_mb": result.memory_mb},
            )
        except Exception as exc:
            latency = (time.perf_counter() - t0) * 1000
            logger.error("LocalONNXAdapter error: %s", exc)
            return GatewayResponse.error_response(str(exc), "local_onnx", latency)

    def is_available(self) -> bool:
        try:
            import onnxruntime
            return True
        except ImportError:
            return False


class GGUFAdapter(BaseAdapter):
    """Adapter wrapping llama.cpp / GGUF model engine."""

    name = "gguf"

    def __init__(self, engine: Optional[Any] = None) -> None:
        self._engine = engine

    def generate(self, request: GatewayRequest) -> GatewayResponse:
        t0 = time.perf_counter()
        if self._engine is None:
            from omnibench.engine.gguf_engine import GGUFEngine
            self._engine = GGUFEngine()
            self._engine.load()

        res = self._engine.generate(None, request.prompt)
        latency = (time.perf_counter() - t0) * 1000.0
        return GatewayResponse(
            text=res["text"],
            action_json=res["action_json"],
            usage_tokens=32,
            latency_ms=latency,
            provider_used="gguf",
            model_name="omnibench-100m-gguf",
        )


class MLXAdapter(BaseAdapter):
    """Adapter wrapping Apple Silicon Metal MLX model engine."""

    name = "mlx"

    def __init__(self, engine: Optional[Any] = None) -> None:
        self._engine = engine

    def generate(self, request: GatewayRequest) -> GatewayResponse:
        t0 = time.perf_counter()
        if self._engine is None:
            from omnibench.engine.mlx_engine import MLXEngine
            self._engine = MLXEngine()
            self._engine.load()

        res = self._engine.generate(None, request.prompt)
        latency = (time.perf_counter() - t0) * 1000.0
        return GatewayResponse(
            text=res["text"],
            action_json=res["action_json"],
            usage_tokens=32,
            latency_ms=latency,
            provider_used="mlx",
            model_name="omnibench-100m-mlx",
        )


class OpenAIAdapter(BaseAdapter):
    """Adapter for OpenAI GPT-4o / GPT-4-vision models via REST API."""

    name = "openai"

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o") -> None:
        import os
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model

    def is_available(self) -> bool:
        return bool(self.api_key)

    def generate(self, request: GatewayRequest) -> GatewayResponse:
        t0 = time.perf_counter()
        try:
            import openai  # type: ignore
            client = openai.OpenAI(api_key=self.api_key)

            messages: List[Dict[str, Any]] = []
            if request.system_prompt:
                messages.append({"role": "system", "content": request.system_prompt})

            content: List[Dict[str, Any]] = [{"type": "text", "text": request.prompt}]
            for img_bytes in request.images:
                import base64
                b64 = base64.b64encode(img_bytes).decode()
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64}"},
                })
            messages.append({"role": "user", "content": content})

            resp = client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
            )
            text = resp.choices[0].message.content or ""
            tokens = resp.usage.total_tokens if resp.usage else 0
            latency = (time.perf_counter() - t0) * 1000
            return GatewayResponse(
                text=text,
                action_json=self._parse_action(text),
                usage_tokens=tokens,
                latency_ms=latency,
                provider_used="openai",
                model_name=self.model,
            )
        except Exception as exc:
            latency = (time.perf_counter() - t0) * 1000
            logger.error("OpenAI adapter error: %s", exc)
            return GatewayResponse.error_response(str(exc), "openai", latency)


class AnthropicAdapter(BaseAdapter):
    """Adapter for Anthropic Claude models via Anthropic API."""

    name = "anthropic"

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-sonnet-20241022") -> None:
        import os
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        self.model = model

    def is_available(self) -> bool:
        return bool(self.api_key)

    def generate(self, request: GatewayRequest) -> GatewayResponse:
        t0 = time.perf_counter()
        try:
            import anthropic  # type: ignore
            client = anthropic.Anthropic(api_key=self.api_key)

            content: List[Dict[str, Any]] = []
            for img_bytes in request.images:
                import base64
                b64 = base64.b64encode(img_bytes).decode()
                content.append({
                    "type": "image",
                    "source": {"type": "base64", "media_type": "image/png", "data": b64},
                })
            content.append({"type": "text", "text": request.prompt})

            system = request.system_prompt or "You are OmniBench, a computer use AI agent."
            resp = client.messages.create(
                model=self.model,
                max_tokens=request.max_tokens,
                system=system,
                messages=[{"role": "user", "content": content}],
            )
            text = resp.content[0].text if resp.content else ""
            tokens = (resp.usage.input_tokens + resp.usage.output_tokens) if resp.usage else 0
            latency = (time.perf_counter() - t0) * 1000
            return GatewayResponse(
                text=text,
                action_json=self._parse_action(text),
                usage_tokens=tokens,
                latency_ms=latency,
                provider_used="anthropic",
                model_name=self.model,
            )
        except Exception as exc:
            latency = (time.perf_counter() - t0) * 1000
            logger.error("Anthropic adapter error: %s", exc)
            return GatewayResponse.error_response(str(exc), "anthropic", latency)


class GeminiAdapter(BaseAdapter):
    """Adapter for Google Gemini models via google-generativeai."""

    name = "gemini"

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.0-flash") -> None:
        import os
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model = model

    def is_available(self) -> bool:
        return bool(self.api_key)

    def generate(self, request: GatewayRequest) -> GatewayResponse:
        t0 = time.perf_counter()
        try:
            import google.generativeai as genai  # type: ignore
            from PIL import Image

            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(self.model)

            parts: List[Any] = [request.prompt]
            for img_bytes in request.images:
                parts.append(Image.open(io.BytesIO(img_bytes)).convert("RGB"))

            resp = model.generate_content(
                parts,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=request.max_tokens,
                    temperature=request.temperature,
                ),
            )
            text = resp.text or ""
            latency = (time.perf_counter() - t0) * 1000
            return GatewayResponse(
                text=text,
                action_json=self._parse_action(text),
                usage_tokens=0,
                latency_ms=latency,
                provider_used="gemini",
                model_name=self.model,
            )
        except Exception as exc:
            latency = (time.perf_counter() - t0) * 1000
            logger.error("Gemini adapter error: %s", exc)
            return GatewayResponse.error_response(str(exc), "gemini", latency)


class OllamaAdapter(BaseAdapter):
    """Adapter for local Ollama models via REST API."""

    name = "ollama"

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llava") -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    def is_available(self) -> bool:
        try:
            import urllib.request
            urllib.request.urlopen(f"{self.base_url}/api/tags", timeout=2)
            return True
        except Exception:
            return False

    def generate(self, request: GatewayRequest) -> GatewayResponse:
        t0 = time.perf_counter()
        try:
            import urllib.request
            import base64

            images_b64 = [base64.b64encode(b).decode() for b in request.images]
            payload = json.dumps({
                "model": self.model,
                "prompt": request.prompt,
                "images": images_b64,
                "stream": False,
                "options": {
                    "temperature": request.temperature,
                    "num_predict": request.max_tokens,
                },
            }).encode()

            req = urllib.request.Request(
                f"{self.base_url}/api/generate",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode())

            text = data.get("response", "")
            latency = (time.perf_counter() - t0) * 1000
            return GatewayResponse(
                text=text,
                action_json=self._parse_action(text),
                usage_tokens=data.get("eval_count", 0),
                latency_ms=latency,
                provider_used="ollama",
                model_name=self.model,
            )
        except Exception as exc:
            latency = (time.perf_counter() - t0) * 1000
            logger.error("Ollama adapter error: %s", exc)
            return GatewayResponse.error_response(str(exc), "ollama", latency)
