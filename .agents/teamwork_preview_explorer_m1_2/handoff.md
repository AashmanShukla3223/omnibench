# Handoff Report — Explorer 2 (Milestone M1: Gateway Architecture & Design)

## 1. Observation

Direct observations from examining project files and codebase state:
- **Files Inspected**:
  - `/home/oh_my_macos27/OmniBench Computer Use/ORIGINAL_REQUEST.md` (R1: Universal Model Gateway & Cascading Decision Routing)
  - `/home/oh_my_macos27/OmniBench Computer Use/PROJECT.md` (Features 3-6, Interface contracts for `GatewayRequest`/`GatewayResponse`)
  - `/home/oh_my_macos27/OmniBench Computer Use/.agents/teamwork_preview_sub_orch_m1/SCOPE.md` (M1 Scope: Gateway protocol, adapters, cascading router)
  - Existing directory structure: `omnibench/gateway/` does not exist yet and must be created.
- **Environment Context**:
  - System Python is Python 3.13.5. External provider SDKs (`openai`, `anthropic`, `google-generativeai`, `pydantic`) are not pre-installed in default environment.
  - Pydantic models must be constructed with defensive fallback (standard dataclasses / Pydantic v2 support) to ensure compatibility across environments.
- **Interface Contracts Required**:
  - `GatewayRequest`: `prompt: str`, `images: list[bytes]`, `temperature: float`, `max_tokens: int`, `model_name: str`
  - `GatewayResponse`: `text: str`, `action_json: dict`, `usage_tokens: int`, `latency_ms: float`, `provider_used: str`
  - `LocalONNXAdapter.generate(req: GatewayRequest) -> GatewayResponse`

---

## 2. Logic Chain

From the requirement specifications to the implementation design:
1. **Requirement R1 & Features 3-6**: Request a unified adapter protocol interfacing external frontier APIs (OpenAI, Anthropic Claude, Gemini, Ollama), a local ONNX 100M model engine, and an offline mock provider, coupled with a cascading priority router for automated failover.
2. **Schema Contract (`protocol.py`)**:
   - `GatewayRequest` must encapsulate all multimodal model parameters. Images can be provided as raw bytes, base64 strings, or PIL Images, auto-normalized to `list[bytes]`.
   - `GatewayResponse` must unify raw model outputs into structured format containing text explanation, extracted `action_json` dict, token usage stats, wall-clock `latency_ms`, `provider_used`, and a `fallback_history` list for auditability.
3. **Adapter Architecture (`adapters.py`)**:
   - Standard interface defined by `BaseGatewayAdapter` with abstract `generate(request: GatewayRequest) -> GatewayResponse`.
   - Adapters for:
     - `OpenAIAdapter`: API call or HTTP fallback to `/v1/chat/completions`.
     - `AnthropicAdapter`: API call or HTTP fallback to `/v1/messages`.
     - `GeminiAdapter`: Google GenAI API call or REST endpoint.
     - `OllamaAdapter`: Local HTTP call to `http://localhost:11434/api/chat`.
     - `LocalONNXAdapter`: Direct call to `omnibench.engine.onnx_engine.ONNXEngine`.
     - `MockAdapter`: Deterministic offline adapter with configurable responses, simulated latency, and programmable error triggers.
   - Robust JSON extraction helper (`_extract_action_json`) in base adapter to parse action dictionaries from raw text responses (handling ````json ... ```` fences).
4. **Cascading Router Architecture (`router.py`)**:
   - `CascadingRouter` manages an ordered priority list of provider names (e.g. `["openai", "anthropic", "gemini", "ollama", "local_onnx", "mock"]`).
   - `route(request: GatewayRequest) -> GatewayResponse`: Iterates through priority providers. If a provider succeeds, returns its response immediately. If a provider fails (due to missing API key, network timeout, rate limit, or invalid response), appends error entry to `fallback_history` and attempts next priority provider.
   - Final fallback ensures request resolution (e.g. falling back to `mock` or `local_onnx`).

---

## 3. Caveats

- **Read-Only Scope**: This report provides architectural design and technical specifications. Implementation will be performed by worker agents.
- **External Dependency Independence**: Adapters must operate without crashing if optional client libraries (`openai`, `anthropic`, etc.) are missing, falling back to HTTP request wrappers or notifying the Cascading Router to proceed down the priority chain.
- **Action JSON Parsing Robustness**: Prompting VLM models sometimes results in extra formatting (e.g. markdown quotes). The base parser must handle raw JSON, code fences, and regex extraction for key action keys (`action`, `x`, `y`, `text`, etc.).

---

## 4. Conclusion & Technical Implementation Strategy

### A. Module Structure to Create (`omnibench/gateway/`)
```
omnibench/gateway/
├── __init__.py
├── protocol.py
├── adapters.py
└── router.py
```

### B. Detailed File Implementation Specifications

#### 1. `omnibench/gateway/protocol.py`
- Define `GatewayRequest`:
  ```python
  class GatewayRequest(BaseModel):
      prompt: str
      images: list[bytes] = Field(default_factory=list)
      temperature: float = 0.7
      max_tokens: int = 512
      model_name: str = "mock"
      system_prompt: str | None = None
      extra_params: dict = Field(default_factory=dict)
  ```
- Define `GatewayResponse`:
  ```python
  class GatewayResponse(BaseModel):
      text: str
      action_json: dict = Field(default_factory=dict)
      usage_tokens: int = 0
      latency_ms: float = 0.0
      provider_used: str = "unknown"
      fallback_history: list[dict] = Field(default_factory=list)
      raw_response: str | None = None
      success: bool = True
      error: str | None = None
  ```
- Define custom exception hierarchy:
  - `GatewayError(Exception)`
  - `ProviderError(GatewayError)`
  - `ProviderUnavailableError(ProviderError)`
  - `AuthenticationError(ProviderError)`
  - `AllProvidersFailedError(GatewayError)`

#### 2. `omnibench/gateway/adapters.py`
- `BaseGatewayAdapter`:
  - `generate(request: GatewayRequest) -> GatewayResponse` (abstract method)
  - `_extract_action_json(raw_text: str) -> dict`: Uses regex & `json.loads` to locate JSON blocks containing `"action"` key.
- Provider Implementations:
  - `MockAdapter`: Pre-configured dictionary of action responses or dynamic echo. Supports `set_mock_action()`, `fail_next_n_calls()`.
  - `LocalONNXAdapter`: Accepts an instance of `ONNXEngine` (or lazy imports `omnibench.engine.onnx_engine.ONNXEngine`). Calls engine `predict(prompt, images)` and formats `GatewayResponse`.
  - `OpenAIAdapter`: Checks `OPENAI_API_KEY`. Formats vision payload (`data:image/png;base64,...`). Measures latency via `time.perf_counter()`.
  - `AnthropicAdapter`: Checks `ANTHROPIC_API_KEY`. Formats image content blocks (`image/png`, base64).
  - `GeminiAdapter`: Checks `GEMINI_API_KEY` / `GOOGLE_API_KEY`. Formats inline data parts.
  - `OllamaAdapter`: Connects to `host:port` (default `http://localhost:11434`). Sends prompt & base64 images to `/api/chat`.
- Adapter Registry / Factory:
  - `get_adapter(provider_name: str, **kwargs) -> BaseGatewayAdapter`

#### 3. `omnibench/gateway/router.py`
- `CascadingRouter`:
  - Constructor: `def __init__(self, priority_list: list[str] = None, adapters: dict[str, BaseGatewayAdapter] = None)`
    - Default priority list: `["openai", "anthropic", "gemini", "ollama", "local_onnx", "mock"]`
  - Methods:
    - `register_adapter(name: str, adapter: BaseGatewayAdapter)`
    - `set_priority_list(priority_list: list[str])`
    - `route(request: GatewayRequest) -> GatewayResponse`:
      ```python
      def route(self, request: GatewayRequest) -> GatewayResponse:
          fallback_history = []
          for provider_name in self.priority_list:
              adapter = self.adapters.get(provider_name)
              if not adapter:
                  continue
              try:
                  start_time = time.perf_counter()
                  response = adapter.generate(request)
                  response.fallback_history = fallback_history
                  return response
              except Exception as e:
                  fallback_history.append({
                      "provider": provider_name,
                      "error": str(e),
                      "timestamp": time.time()
                  })
          raise AllProvidersFailedError(f"All providers in priority list failed: {fallback_history}")
      ```

#### 4. `omnibench/gateway/__init__.py`
- Export primary public classes:
  - `GatewayRequest`, `GatewayResponse`
  - `BaseGatewayAdapter`, `OpenAIAdapter`, `AnthropicAdapter`, `GeminiAdapter`, `OllamaAdapter`, `LocalONNXAdapter`, `MockAdapter`
  - `CascadingRouter`
  - `GatewayError`, `AllProvidersFailedError`

---

## 5. Verification Method

Once implementation is completed by the worker agent:
1. **Unit Test Verification**:
   Execute pytest on gateway test suite:
   ```bash
   pytest tests/unit/test_gateway.py -v
   ```
2. **Interactive Verification Script**:
   Run a standalone python verification script:
   ```python
   python3 -c "
   from omnibench.gateway.protocol import GatewayRequest, GatewayResponse
   from omnibench.gateway.adapters import MockAdapter
   from omnibench.gateway.router import CascadingRouter

   req = GatewayRequest(prompt='Click on Submit button', model_name='mock')
   router = CascadingRouter(priority_list=['mock'])
   resp = router.route(req)
   assert resp.provider_used == 'mock'
   assert resp.action_json is not None
   print('Gateway router verification PASSED successfully!')
   "
   ```
3. **Failover Cascading Test**:
   Configure `CascadingRouter(priority_list=['failing_provider', 'mock'])` where `failing_provider` raises `ProviderUnavailableError`. Verify that router falls back to `mock` and records `fallback_history`.
