# Handoff Report: Milestone M1 — Gateway & Adapters Analysis

## 1. Observation

### Workspace State & Inspection
- Directory search via `find_by_name` and `ls -la` in `/home/oh_my_macos27/OmniBench Computer Use/` revealed that no project source files in `omnibench/gateway/` or test files in `tests/` currently exist in the repository root.
- Authoritative documentation files present in workspace root:
  - `/home/oh_my_macos27/OmniBench Computer Use/ORIGINAL_REQUEST.md` (Lines 12-14: "R1. 100M Parameter ONNX Local Model Engine & Universal Model Gateway... Unified Gateway adapter protocol for external frontier LLM APIs (OpenAI, Anthropic, Gemini, Ollama) and cascading decision routing.")
  - `/home/oh_my_macos27/OmniBench Computer Use/PROJECT.md` (Lines 16-19: Features 3, 4, 5, 6; Lines 49-52: Gateway Interface Contracts `GatewayRequest` / `GatewayResponse` / `LocalONNXAdapter.generate`)
  - `/home/oh_my_macos27/OmniBench Computer Use/.agents/orch_m1_engine/SCOPE.md` (Lines 6-7, 28-38: Code layout for `omnibench/gateway/protocol.py`, `omnibench/gateway/adapters.py`, `omnibench/gateway/router.py`, `tests/unit/test_gateway.py`)
  - `/home/oh_my_macos27/OmniBench Computer Use/TEST_INFRA.md` (Lines 12-15: Features 3-6 test coverage targets)

### Python Environment Inspection
- Virtual environment at `.venv` was verified using `.venv/bin/python3 -m pip list`.
- Installed packages in `.venv`:
  - `pydantic` (v2.13.4)
  - `onnxruntime` (v1.28.0)
  - `httpx` (v0.28.1)
  - `numpy` (v2.5.1)
  - `pillow` (v12.3.0)
  - `psutil` (v7.2.2)

---

## 2. Logic Chain

1. **Workspace Greenfield Status**: Since `omnibench/gateway/` and `tests/` do not yet exist, all protocol schemas, adapters, router components, and unit tests must be created from scratch following the layout in `PROJECT.md` and `SCOPE.md`.
2. **Protocol Schema Design (`protocol.py`)**:
   - `pydantic` v2 is installed in `.venv`. Using `pydantic.BaseModel` and `ConfigDict(arbitrary_types_allowed=True)` enables native validation for `bytes` image payloads, numeric range validation (`temperature` 0.0-2.0, `max_tokens` > 0), and structured metadata dictionary.
   - `GatewayRequest` contract: `prompt: str`, `images: list[bytes]`, `temperature: float`, `max_tokens: int`, `model_name: str`, `metadata: dict[str, Any]`.
   - `GatewayResponse` contract: `text: str`, `action_json: dict[str, Any]`, `usage_tokens: int`, `latency_ms: float`, `provider_used: str`, `error: Optional[str]`.
   - Helper `parse_action_json()` added to `GatewayResponse` to parse markdown codeblock JSON (` ```json ... ``` `) if `action_json` is not directly provided by the model provider.
3. **Adapter Architecture (`adapters.py`)**:
   - Abstract Base Class `BaseAdapter(ABC)` defines common interface: `provider_name`, `generate(request) -> GatewayResponse`, `agenerate(request)`, `is_healthy() -> bool`.
   - 6 concrete implementations required:
     - `OpenAIAdapter`: OpenAI API integration (vision payloads in base64, token usage parsing).
     - `AnthropicAdapter`: Anthropic Claude API integration (base64 image payload blocks, usage calculation).
     - `GeminiAdapter`: Google Gemini API integration (inline_data image payload).
     - `OllamaAdapter`: Local Ollama REST integration (`/api/generate` or `/api/chat`, eval token counting).
     - `LocalONNXAdapter`: Local CPU ONNX engine adapter delegating to `omnibench.engine.onnx_engine.ONNXEngine`.
     - `MockAdapter`: Offline test double adapter supporting canned responses, canned action JSON, simulated latency, and error simulation for offline testing.
4. **Cascading Decision Router (`router.py`)**:
   - Manages an ordered list of `BaseAdapter` instances in priority sequence (e.g. OpenAI -> Anthropic -> Gemini -> Ollama -> LocalONNX -> Mock).
   - Incorporates `ProviderHealth` circuit breaker tracking consecutive failures and cooldown windows.
   - Implements per-adapter retries, per-request timeout handling, and automatic fallback cascading.
   - Provides `fallback_to_mock` safety net so benchmark tasks never fail due to missing remote API credentials or transient network outages.
5. **Unit Test Strategy (`tests/unit/test_gateway.py`)**:
   - Standard Pytest test cases covering schema validation, adapter responses, error handling, router fallback chains, circuit breaker state transitions, and mock fallback.

---

## 3. Caveats

- **External API Keys**: Live testing of `OpenAIAdapter`, `AnthropicAdapter`, and `GeminiAdapter` requires valid environment API keys (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`). Unit tests should mock network calls (`httpx` responses or `unittest.mock`) to run offline without external dependencies.
- **Ollama Availability**: `OllamaAdapter` relies on a running local Ollama service (`http://localhost:11434`). If Ollama is offline, the router must handle `ConnectionError` gracefully and cascade to `LocalONNXAdapter`.
- **Engine Subsystem Dependency**: `LocalONNXAdapter` interfaces with `omnibench.engine.onnx_engine.ONNXEngine`. It should support graceful degradation or synthetic fallback if the ONNX model file is missing during early development.

---

## 4. Conclusion

The specification and architecture for Milestone M1 Gateway & Adapters are fully defined and aligned with `PROJECT.md`, `SCOPE.md`, and `ORIGINAL_REQUEST.md`.

### Recommended Code Layout for M1 Gateway
```
omnibench/gateway/
├── __init__.py
├── protocol.py       # GatewayRequest & GatewayResponse Pydantic models
├── adapters.py       # BaseAdapter + OpenAI, Anthropic, Gemini, Ollama, LocalONNX, Mock adapters
└── router.py         # CascadingRouter & ProviderHealth circuit breaker

tests/unit/
└── test_gateway.py   # Unit test suite covering protocols, adapters, & router
```

---

## 5. Verification Method

To verify the implementation once written:
1. Run unit test suite:
   ```bash
   .venv/bin/python3 -m pytest tests/unit/test_gateway.py -v
   ```
2. Verify imports and schemas:
   ```bash
   .venv/bin/python3 -c "from omnibench.gateway.protocol import GatewayRequest, GatewayResponse; print(GatewayRequest(prompt='test'))"
   ```
3. Test cascading router fallback behavior with mock adapters:
   ```bash
   .venv/bin/python3 -c "from omnibench.gateway.adapters import MockAdapter; from omnibench.gateway.router import CascadingRouter; router = CascadingRouter([MockAdapter()]); print(router.route(GatewayRequest(prompt='ping')))"
   ```
