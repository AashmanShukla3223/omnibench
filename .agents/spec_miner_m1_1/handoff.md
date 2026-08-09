# Specification Report & Handoff — Milestone M1: Engine & Gateway

**Agent**: `spec_miner_m1_1`  
**Milestone**: M1 (Features 1 - 6)  
**Date**: 2026-08-08  
**Target Path**: `/home/oh_my_macos27/OmniBench Computer Use/.agents/spec_miner_m1_1/handoff.md`

---

## 1. Observation

Direct observations extracted from authoritative specification files (`ORIGINAL_REQUEST.md`, `PROJECT.md`, `SCOPE.md`, `TEST_INFRA.md`):

1. **`ORIGINAL_REQUEST.md` (R1 & Acceptance Criteria)**:
   - "Engine capable of running a 100M parameter vision-language model optimized with ONNX Runtime INT8/INT4 under ~1.1 GiB host RAM on CPU without GPU..."
   - "...alongside a Unified Gateway adapter protocol for external frontier LLM APIs (OpenAI, Anthropic, Gemini, Ollama) and cascading decision routing."
   - "ONNX Runtime 100M model engine successfully loads and executes inference on CPU maintaining system memory consumption under 1.1 GiB RAM."
   - "Universal Model Gateway cleanly routes requests between external APIs and local fallback model."

2. **`PROJECT.md` & `SCOPE.md` (Milestone M1 Scope & Code Layout)**:
   - **Feature 1**: ONNX 100M Local Engine (`ONNXLocalEngine` in `omnibench/engine/onnx_engine.py`).
   - **Feature 2**: Model Preprocessor & KV Cache (`Preprocessor`, `KVCacheManager` in `omnibench/engine/preprocessor.py`, `ModelQuantizer` in `omnibench/engine/quantizer.py`, `DummyModelGenerator` in `omnibench/engine/dummy_model.py`).
   - **Feature 3**: Gateway Protocol & Schemas (`GatewayRequest`, `GatewayResponse` in `omnibench/gateway/protocol.py`).
   - **Feature 4**: External API Adapters (`BaseAdapter`, `OpenAIAdapter`, `AnthropicAdapter`, `GeminiAdapter`, `OllamaAdapter` in `omnibench/gateway/adapters.py`).
   - **Feature 5**: Local & Mock Adapters (`LocalONNXAdapter`, `MockAdapter` in `omnibench/gateway/adapters.py`).
   - **Feature 6**: Cascading Router (`CascadingRouter` in `omnibench/gateway/router.py`).

3. **Memory Limits & Assertions**:
   - Limit: Strictly < 1.1 GiB (1,126.4 MiB / 1,181,116,006 bytes) RSS host RAM on CPU.

---

## 2. Logic Chain

From requirement R1 to precise system design:
1. **Model Engine Execution**: Running a vision-language model (VLM) on host CPU under 1.1 GiB RAM requires ONNX Runtime execution with INT8/INT4 dynamic quantization. To make testing and standalone execution robust without requiring massive external downloads, a `DummyModelGenerator` generates lightweight valid ONNX protobuf models on-the-fly.
2. **Preprocessor & KV Cache**: Image inputs (screenshots) must be resized, normalized, and converted into standard FP32 RGB tensors (`(1, 3, H, W)`). Prompt text must be tokenized into int64 tensor shapes (`(1, S)`). For token generation, `KVCacheManager` manages past Key/Value state tensors across transformer layers, preventing repeated matrix multiplications and staying strictly within the 1.1 GiB RAM limit.
3. **Gateway Contract**: `GatewayRequest` and `GatewayResponse` provide a uniform Pydantic interface wrapping prompt strings, image byte arrays, temperature, max tokens, parsed structured action JSON (e.g. `{"action": "click", "x": 100, "y": 200}`), token usage counts, execution latency, and provider attribution.
4. **Adapter Architecture**: `BaseAdapter` defines the abstract interface (`generate(req: GatewayRequest) -> GatewayResponse` and `health_check() -> bool`). Specialized adapters translate standard requests into provider-specific API payloads (`OpenAIAdapter`, `AnthropicAdapter`, `GeminiAdapter`, `OllamaAdapter`), local ONNX execution (`LocalONNXAdapter`), or offline testing stubs (`MockAdapter`).
5. **Cascading Router**: `CascadingRouter` accepts a prioritized list of providers (e.g., OpenAI → Anthropic → Gemini → Ollama → LocalONNX → Mock). Upon request failure or memory assertion breach in one provider, the router automatically catches the error, logs the fallback event, and proceeds down the priority chain.

---

## 3. Caveats

- **No Active GPU**: All local ONNX model execution must strictly target `CPUExecutionProvider`.
- **Memory Metric**: Memory consumption is monitored using `psutil.Process().memory_info().rss`. 1.1 GiB equals $1.1 \times 1024 \text{ MiB} = 1126.4 \text{ MiB}$.
- **API Keys**: External API adapters (OpenAI, Anthropic, Gemini) must gracefully handle missing API keys (e.g. returning health check `False` or raising `ValueError`/`ConnectionError` handled cleanly by `CascadingRouter`).

---

## 4. Conclusion & Precise Interface Specifications

### 4.1 Detailed Class Specifications for `omnibench.engine`

#### A. `ONNXLocalEngine` (`omnibench/engine/onnx_engine.py`)
- **Imports**: `onnxruntime as ort`, `numpy as np`, `psutil`, `pathlib.Path`, `typing`, `PIL.Image`, `omnibench.engine.preprocessor.Preprocessor`, `omnibench.engine.preprocessor.KVCacheManager`, `omnibench.engine.dummy_model.DummyModelGenerator`.
- **Attributes**:
  - `model_path: Path | None`
  - `session: ort.InferenceSession | None`
  - `preprocessor: Preprocessor`
  - `kv_cache: KVCacheManager`
  - `max_memory_mb: float = 1126.4` (~1.1 GiB)
  - `execution_provider: str = "CPUExecutionProvider"`
  - `quantization: str = "INT8"`
  - `num_threads: int = 4`
  - `is_loaded: bool = False`
- **Function Signatures**:
  ```python
  class ONNXLocalEngine:
      def __init__(
          self,
          model_path: str | Path | None = None,
          execution_provider: str = "CPUExecutionProvider",
          max_memory_mb: float = 1126.4,
          quantization: str = "INT8",
          num_threads: int = 4,
          enable_kv_cache: bool = True
      ) -> None: ...

      def load_model(self, model_path: str | Path | None = None) -> None:
          """Loads ONNX inference session. If model_path is None or missing, auto-generates dummy model."""
          ...

      def generate(
          self,
          prompt: str,
          images: list[bytes | Image.Image | np.ndarray] | None = None,
          max_tokens: int = 128,
          temperature: float = 0.7,
          top_p: float = 0.9
      ) -> dict[str, Any]:
          """Performs inference forward pass, returning {'text': str, 'action_json': dict, 'tokens_used': int, 'latency_ms': float}."""
          ...

      def get_memory_usage(self) -> float:
          """Returns process RSS memory in MiB using psutil."""
          ...

      def assert_memory_constraint(self) -> bool:
          """Raises MemoryError if RSS memory > max_memory_mb."""
          ...

      def unload(self) -> None:
          """Clears ONNX session and KV cache, invoking gc.collect()."""
          ...
  ```

#### B. `Preprocessor` (`omnibench/engine/preprocessor.py`)
- **Attributes**:
  - `target_image_size: tuple[int, int] = (224, 224)`
  - `mean: tuple[float, float, float] = (0.485, 0.456, 0.406)`
  - `std: tuple[float, float, float] = (0.229, 0.224, 0.225)`
- **Function Signatures**:
  ```python
  class Preprocessor:
      def __init__(
          self,
          target_image_size: tuple[int, int] = (224, 224),
          mean: tuple[float, float, float] = (0.485, 0.456, 0.406),
          std: tuple[float, float, float] = (0.229, 0.224, 0.225)
      ) -> None: ...

      def preprocess_image(self, image: bytes | Image.Image | np.ndarray) -> np.ndarray:
          """Converts input image to float32 RGB tensor array of shape (1, 3, H, W)."""
          ...

      def preprocess_text(self, text: str, max_length: int = 512) -> np.ndarray:
          """Tokenizes string into int64 array of shape (1, seq_len)."""
          ...

      def process_inputs(
          self,
          prompt: str,
          images: list[bytes | Image.Image | np.ndarray] | None = None
      ) -> dict[str, np.ndarray]:
          """Returns dictionary containing input_ids, pixel_values (if images), and attention_mask."""
          ...
  ```

#### C. `KVCacheManager` (`omnibench/engine/preprocessor.py`)
- **Attributes**:
  - `max_batch_size: int = 1`
  - `num_heads: int = 8`
  - `head_dim: int = 64`
  - `max_seq_len: int = 1024`
  - `dtype: np.dtype = np.float32`
  - `cache_keys: dict[int, np.ndarray]`
  - `cache_values: dict[int, np.ndarray]`
- **Function Signatures**:
  ```python
  class KVCacheManager:
      def __init__(
          self,
          max_batch_size: int = 1,
          num_heads: int = 8,
          head_dim: int = 64,
          max_seq_len: int = 1024,
          dtype: np.dtype = np.float32
      ) -> None: ...

      def reset(self) -> None:
          """Clears all cached key/value tensors."""
          ...

      def update(
          self,
          key_states: np.ndarray,
          value_states: np.ndarray,
          layer_idx: int
      ) -> tuple[np.ndarray, np.ndarray]:
          """Appends key_states and value_states for the specified layer_idx and returns updated cache."""
          ...

      def get_cache(self, layer_idx: int) -> tuple[np.ndarray | None, np.ndarray | None]:
          """Retrieves cached key and value states for layer_idx."""
          ...

      def get_memory_footprint(self) -> int:
          """Returns memory consumption of stored cache in bytes."""
          ...
  ```

#### D. `ModelQuantizer` (`omnibench/engine/quantizer.py`)
- **Attributes**:
  - `quant_type: str = "INT8"`
- **Function Signatures**:
  ```python
  class ModelQuantizer:
      def __init__(self, quant_type: str = "INT8") -> None: ...

      def quantize_model(
          self,
          input_model_path: str | Path,
          output_model_path: str | Path
      ) -> Path:
          """Quantizes FP32 ONNX model file to INT8/INT4 ONNX model file."""
          ...

      def estimate_compression_ratio(
          self,
          original_size_bytes: int,
          quantized_size_bytes: int
      ) -> float:
          """Returns compression ratio factor (e.g. 4.0 for 4x reduction)."""
          ...
  ```

#### E. `DummyModelGenerator` (`omnibench/engine/dummy_model.py`)
- **Attributes**:
  - `vocab_size: int = 1000`
  - `hidden_size: int = 128`
  - `num_layers: int = 2`
- **Function Signatures**:
  ```python
  class DummyModelGenerator:
      def __init__(
          self,
          vocab_size: int = 1000,
          hidden_size: int = 128,
          num_layers: int = 2
      ) -> None: ...

      def generate_onnx_file(self, output_path: str | Path) -> Path:
          """Generates a valid lightweight ONNX model binary on disk."""
          ...

      def create_in_memory_dummy(self) -> bytes:
          """Generates ONNX model serialized byte string."""
          ...
  ```

---

### 4.2 Detailed Class Specifications for `omnibench.gateway`

#### A. Data Schemas (`omnibench/gateway/protocol.py`)
```python
from pydantic import BaseModel, Field
from typing import Any, Optional

class GatewayRequest(BaseModel):
    prompt: str
    images: list[bytes] = Field(default_factory=list)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=256, gt=0)
    model_name: str = Field(default="auto")
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    stop_sequences: list[str] = Field(default_factory=list)
    extra_params: dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()

    def validate_request(self) -> bool:
        return len(self.prompt.strip()) > 0

class GatewayResponse(BaseModel):
    text: str
    action_json: dict[str, Any] = Field(default_factory=dict)
    usage_tokens: int = 0
    latency_ms: float = 0.0
    provider_used: str
    finish_reason: str = "stop"
    error_message: Optional[str] = None

    def is_success(self) -> bool:
        return self.error_message is None
```

#### B. Adapters (`omnibench/gateway/adapters.py`)
```python
from abc import ABC, abstractmethod
from typing import Any, Optional
from pathlib import Path
from omnibench.gateway.protocol import GatewayRequest, GatewayResponse
from omnibench.engine.onnx_engine import ONNXLocalEngine

class BaseAdapter(ABC):
    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        model_name: str = "default",
        timeout: float = 30.0
    ) -> None:
        self.api_key = api_key
        self.endpoint_url = endpoint_url
        self.model_name = model_name
        self.timeout = timeout

    @abstractmethod
    def generate(self, req: GatewayRequest) -> GatewayResponse:
        pass

    @abstractmethod
    def health_check(self) -> bool:
        pass

class OpenAIAdapter(BaseAdapter):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gpt-4o",
        timeout: float = 30.0
    ) -> None:
        super().__init__(api_key=api_key, model_name=model_name, timeout=timeout)

    def generate(self, req: GatewayRequest) -> GatewayResponse: ...
    def health_check(self) -> bool: ...

class AnthropicAdapter(BaseAdapter):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "claude-3-5-sonnet",
        timeout: float = 30.0
    ) -> None:
        super().__init__(api_key=api_key, model_name=model_name, timeout=timeout)

    def generate(self, req: GatewayRequest) -> GatewayResponse: ...
    def health_check(self) -> bool: ...

class GeminiAdapter(BaseAdapter):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-1.5-pro",
        timeout: float = 30.0
    ) -> None:
        super().__init__(api_key=api_key, model_name=model_name, timeout=timeout)

    def generate(self, req: GatewayRequest) -> GatewayResponse: ...
    def health_check(self) -> bool: ...

class OllamaAdapter(BaseAdapter):
    def __init__(
        self,
        endpoint_url: str = "http://localhost:11434",
        model_name: str = "llama3",
        timeout: float = 30.0
    ) -> None:
        super().__init__(endpoint_url=endpoint_url, model_name=model_name, timeout=timeout)

    def generate(self, req: GatewayRequest) -> GatewayResponse: ...
    def health_check(self) -> bool: ...

class LocalONNXAdapter(BaseAdapter):
    def __init__(
        self,
        engine: Optional[ONNXLocalEngine] = None,
        model_path: Optional[str | Path] = None,
        timeout: float = 30.0
    ) -> None:
        super().__init__(model_name="local_onnx", timeout=timeout)
        self.engine = engine or ONNXLocalEngine(model_path=model_path)

    def generate(self, req: GatewayRequest) -> GatewayResponse: ...
    def health_check(self) -> bool: ...

class MockAdapter(BaseAdapter):
    def __init__(
        self,
        predefined_responses: Optional[list[GatewayResponse] | dict[str, Any]] = None,
        default_action: Optional[dict[str, Any]] = None,
        should_fail: bool = False,
        fail_exception: Optional[Exception] = None
    ) -> None:
        super().__init__(model_name="mock")
        self.predefined_responses = predefined_responses
        self.default_action = default_action or {"action": "click", "x": 100, "y": 100}
        self.should_fail = should_fail
        self.fail_exception = fail_exception or RuntimeError("Mock adapter configured to fail")

    def generate(self, req: GatewayRequest) -> GatewayResponse: ...
    def health_check(self) -> bool: ...
```

#### C. Cascading Router (`omnibench/gateway/router.py`)
```python
from typing import Any, Optional
from omnibench.gateway.protocol import GatewayRequest, GatewayResponse
from omnibench.gateway.adapters import BaseAdapter

class CascadingRouter:
    def __init__(
        self,
        adapters: Optional[list[tuple[str, BaseAdapter]]] = None,
        priority_chain: Optional[list[str]] = None,
        max_retries_per_adapter: int = 2,
        retry_delay_sec: float = 0.5
    ) -> None:
        self.adapter_map: dict[str, BaseAdapter] = {}
        self.priority_chain: list[str] = priority_chain or [
            "openai", "anthropic", "gemini", "ollama", "local_onnx", "mock"
        ]
        self.max_retries_per_adapter = max_retries_per_adapter
        self.retry_delay_sec = retry_delay_sec

        if adapters:
            for name, adapter in adapters:
                self.register_adapter(name, adapter)

    def register_adapter(self, name: str, adapter: BaseAdapter) -> None:
        self.adapter_map[name] = adapter

    def route(self, req: GatewayRequest) -> GatewayResponse:
        """Routes GatewayRequest through priority chain. Auto-fallbacks on error."""
        ...

    def set_priority_chain(self, chain: list[str]) -> None:
        self.priority_chain = chain

    def get_status(self) -> dict[str, Any]:
        """Returns map of adapter registered status and health_check results."""
        ...
```

---

### 4.3 Memory Assertion & Monitoring Helper Logic
```python
import psutil
import gc

MEMORY_LIMIT_MB = 1126.4  # ~1.1 GiB (1,181,116,006 bytes)

def check_cpu_memory(limit_mb: float = MEMORY_LIMIT_MB) -> tuple[bool, float]:
    """Checks current process RSS RAM in MiB against maximum limit."""
    process = psutil.Process()
    rss_mb = process.memory_info().rss / (1024 * 1024)
    return (rss_mb <= limit_mb, rss_mb)

def assert_cpu_memory(limit_mb: float = MEMORY_LIMIT_MB) -> float:
    """Asserts process RSS memory <= limit_mb. Raises MemoryError on failure."""
    passed, current_mb = check_cpu_memory(limit_mb)
    if not passed:
        gc.collect()
        passed_after_gc, current_mb_after_gc = check_cpu_memory(limit_mb)
        if not passed_after_gc:
            raise MemoryError(
                f"Strict CPU RAM Limit Exceeded! Current RSS: {current_mb_after_gc:.2f} MiB "
                f"exceeds limit of {limit_mb:.2f} MiB (~1.1 GiB)."
            )
        return current_mb_after_gc
    return current_mb
```

---

## Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | Engine | ONNX 100M Local Engine | CPU INT8/INT4 ONNX VLM execution under 1.1 GiB RAM | Prompt str, image bytes/PIL, max_tokens, temp | dict with text, action_json, latency, tokens | Raises `MemoryError` if RSS > 1.1 GiB, `FileNotFoundError` if missing explicit model | `ORIGINAL_REQUEST.md`, `PROJECT.md`, `SCOPE.md` |
| 2 | Engine | Model Preprocessor | Image resizing/normalization & text tokenization | Image bytes/PIL/array, prompt string | Float32 tensor (1,3,H,W), Int64 array (1,S), input dict | `ValueError` on bad image format or empty prompt | `PROJECT.md`, `SCOPE.md` |
| 3 | Engine | KV Cache Manager | Layer-wise Key/Value tensor cache for transformer generation | Key state array, value state array, layer index | Updated cached key & value state arrays | Raises `ValueError` on seq len overflow, maintains RAM bound | `PROJECT.md`, `SCOPE.md` |
| 4 | Engine | Model Quantizer | FP32 ONNX model to INT8/INT4 dynamic quantization | FP32 `.onnx` file path, target quant type | Quantized `.onnx` file path, compression ratio | Raises `RuntimeError` on ONNX quant failure | `PROJECT.md`, `SCOPE.md` |
| 5 | Engine | Dummy Model Generator | Lightweight synthetic ONNX model binary for fallback & testing | Output Path, vocab_size, hidden_size, num_layers | `.onnx` file or serialized bytes | Raises `OSError` if output path unwriteable | `PROJECT.md`, `SCOPE.md` |
| 6 | Gateway | Gateway Protocol Schemas | Pydantic Request/Response data contracts (`GatewayRequest`/`GatewayResponse`) | Prompt, images, params / text, action_json, usage | Pydantic model objects, serialized dicts | `ValidationError` on bad schema inputs | `PROJECT.md`, `SCOPE.md` |
| 7 | Gateway | External API Adapters | Unified API wrappers for OpenAI, Anthropic, Gemini, Ollama | `GatewayRequest` | `GatewayResponse` | Raises/returns error response on API/network failure | `ORIGINAL_REQUEST.md`, `PROJECT.md`, `SCOPE.md` |
| 8 | Gateway | Local & Mock Adapters | `LocalONNXAdapter` (wraps ONNX Engine) & `MockAdapter` (offline testing) | `GatewayRequest` | `GatewayResponse` | Memory check on local ONNX; config failures on mock | `PROJECT.md`, `SCOPE.md` |
| 9 | Gateway | Cascading Router | Priority decision router with automated provider fallback | `GatewayRequest`, priority adapter chain | `GatewayResponse` from first working provider | Raises `RuntimeError` / `AllAdaptersFailedError` if all fail | `ORIGINAL_REQUEST.md`, `PROJECT.md`, `SCOPE.md` |

---

## Edge Cases

| # | Feature | Input | Observed Behavior |
|---|---------|-------|-------------------|
| 1 | `ONNXLocalEngine` | `model_path=None` | Auto-invokes `DummyModelGenerator` to build & load temporary in-memory or on-disk model. |
| 2 | `ONNXLocalEngine` | Host RAM RSS reaches 1.1 GiB (1126.4 MiB) | Triggers `gc.collect()`. If still > 1126.4 MiB, raises `MemoryError`. |
| 3 | `CascadingRouter` | Primary API (e.g. OpenAI) returns 429 / 500 error | Router catches exception, logs fallback warning, and attempts next adapter in chain (e.g. Anthropic/LocalONNX). |
| 4 | `CascadingRouter` | All registered adapters fail | Router aggregates error messages from all adapters and raises `RuntimeError("All adapters in cascading chain failed: [...]")`. |
| 5 | `Preprocessor` | Empty prompt string or invalid image bytes | Raises `ValueError` with clear error message before sending to ONNX session. |
| 6 | `GatewayRequest` | Negative max_tokens or temperature > 2.0 | Pydantic `ValidationError` raised during instantiation. |
| 7 | `KVCacheManager` | Exceeds `max_seq_len` (1024 tokens) | Returns truncated window or resets cache state without exceeding 1.1 GiB RAM. |

---

## 5. Verification Method

To verify the specifications and implementation of Milestone M1:

1. **File Existence Check**:
   - Confirm layout matches `PROJECT.md`:
     - `omnibench/engine/__init__.py`
     - `omnibench/engine/onnx_engine.py`
     - `omnibench/engine/preprocessor.py`
     - `omnibench/engine/quantizer.py`
     - `omnibench/engine/dummy_model.py`
     - `omnibench/gateway/__init__.py`
     - `omnibench/gateway/protocol.py`
     - `omnibench/gateway/adapters.py`
     - `omnibench/gateway/router.py`

2. **Unit Test Execution**:
   - Run `pytest tests/unit/test_engine.py tests/unit/test_gateway.py` once implemented.
   - Assert all imports, function signatures, Pydantic validations, and mock adapter responses function as expected.

3. **Memory Constraint Verification**:
   - Execute test checking `ONNXLocalEngine.get_memory_usage()` under synthetic generation loop to confirm process RSS remains strictly below 1126.4 MiB (~1.1 GiB).
