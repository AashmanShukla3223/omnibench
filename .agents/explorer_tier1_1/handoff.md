# Handoff Report — E2E Test Specifications for Tier 1 Features (F1 – F7)

**Agent ID**: `explorer_tier1_1`  
**Working Directory**: `/home/oh_my_macos27/OmniBench Computer Use/.agents/explorer_tier1_1`  
**Target File**: `/home/oh_my_macos27/OmniBench Computer Use/.agents/explorer_tier1_1/handoff.md`  
**Date**: 2026-08-08  
**Handoff Type**: Hard Handoff  

---

## 1. Observation

1. **User Request & Requirements**:
   - `ORIGINAL_REQUEST.md` (lines 12-14, 15-17): R1 requires a 100M parameter local ONNX model engine running under ~1.1 GiB host RAM on CPU without GPU, alongside a Universal Gateway adapter protocol for external frontier APIs (OpenAI, Anthropic, Gemini, Ollama) and cascading decision routing. R2 requires modular OS automation drivers supporting 8 action primitives with automated error backoff & retries.
   - `PROJECT.md` (lines 12-24, 47-67): Defines Features 1 through 7:
     - **F1**: ONNX 100M Local Engine (`omnibench.engine.onnx_engine`)
     - **F2**: Model Preprocessor & KV Cache (`omnibench.engine.preprocessor`, `quantizer`, `kv_cache`)
     - **F3**: Gateway Protocol & Schemas (`omnibench.gateway.protocol`)
     - **F4**: External API Adapters (`omnibench.gateway.adapters` for OpenAI, Anthropic, Gemini, Ollama)
     - **F5**: Local & Mock Adapters (`LocalONNXAdapter`, `MockAdapter`)
     - **F6**: Cascading Decision Router (`omnibench.gateway.router`)
     - **F7**: BaseOSDriver Action Primitives (`omnibench.drivers.base`)
   - `TEST_INFRA.md` (lines 8-20, 47-50): Defines Tier 1 E2E target as happy-path and core behavior tests (at least 5 test cases per feature = 35 test cases total for F1-F7). Tests must be opaque-box, executable via Pytest (`pytest tests/e2e/tier1_features`), and target public interfaces, CLI, SDK, and schemas.

2. **Architectural Surveys**:
   - `explorer_survey_1/analysis.md`: Establishes data contracts for `LocalModelEngine` (`predict()`, `load()`, `unload()`, `get_memory_usage_mb()`), `GatewayRequest`, `GatewayResponse`, `RoutingStrategy`, `ChatMessage`, `ToolCall`, `TokenUsage`, and `CascadingRouter`. Host hardware has 4 CPU cores, ~974 MiB - 1.1 GiB free RAM, Python 3.13.5 with `onnxruntime` 1.28.0, `pydantic` 2.13.4, `httpx` 0.28.1, `numpy` 2.5.1, `pillow` 12.3.0, and `psutil` 7.2.2.
   - `explorer_survey_2/analysis.md`: Establishes data contracts for `BaseOSDriver`, `ActionPrimitive`, `ActionType` (`click`, `double_click`, `right_click`, `drag`, `type`, `key_combination`, `scroll`, `wait`), `ActionResult`, and driver exception hierarchy.

3. **Test Infrastructure Layout**:
   - E2E tests are organized under `tests/e2e/tier1_features/`:
     - `test_f1_onnx_engine.py` (F1: 5 tests)
     - `test_f2_preprocessor_kv_cache.py` (F2: 5 tests)
     - `test_f3_gateway_protocol.py` (F3: 5 tests)
     - `test_f4_external_adapters.py` (F4: 5 tests)
     - `test_f5_local_mock_adapters.py` (F5: 5 tests)
     - `test_f6_cascading_router.py` (F6: 5 tests)
     - `test_f7_base_os_driver.py` (F7: 5 tests)

---

## 2. Logic Chain

1. **Step 1 (Observation 1 & 3)**: Requirement R1 and R2 mandate core features F1–F7. Tier 1 testing requires 5 executable test cases per feature (35 total), derived opaque-box from `ORIGINAL_REQUEST.md` and public interface contracts.
2. **Step 2 (Observation 2)**: F1 through F6 cover the local ONNX engine and model gateway pipeline, while F7 covers the platform driver primitive contract.
3. **Step 3 (Observation 2 & 3)**: 
   - For **F1**, test specs must verify engine initialization on CPU (`CPUExecutionProvider`), RAM consumption remaining strictly under ~1.1 GiB (1126.4 MB) RSS, prediction output generation, session memory cleanup on `unload()`, and INT8/INT4 quantization compatibility.
   - For **F2**, test specs must verify screen capture image resizing to 224x224 RGB tensors, text prompt tokenization, INT8 dynamic quantization transformation, KV cache allocation within sequence length window bounds, and cache state reset between episodes.
   - For **F3**, test specs must verify `GatewayRequest` / `GatewayResponse` Pydantic serialization, `ChatMessage` role & multimodal content validation, `ToolDefinition` / `ToolCall` schema parsing, and `TokenUsage` arithmetic integrity.
   - For **F4**, test specs must verify request transformation and response parsing across OpenAI, Anthropic, Gemini, and Ollama adapters using HTTP mocks, alongside HTTP error/timeout exception handling.
   - For **F5**, test specs must verify `LocalONNXAdapter` wrapping `LocalModelEngine.predict()`, `MockAdapter` deterministic response generation, custom mock response injection, mock latency/counter tracking, and strict protocol parity across all adapters.
   - For **F6**, test specs must verify `CascadingRouter` primary-first routing, automatic fallback chain execution on provider errors, strict `LOCAL_ONLY` strategy enforcement, unconfigured API key detection and fallback, and error propagation when all providers fail.
   - For **F7**, test specs must verify `BaseOSDriver` action primitives (`CLICK`, `DOUBLE_CLICK`, `RIGHT_CLICK`, `DRAG`, `TYPE`, `KEY_COMBINATION`, `SCROLL`, `WAIT`), parameter validation, `ActionResult` payload format, and `capture_screenshot()` functionality.
4. **Step 4 (Observation 1 & 3)**: Each test specification must define the Test ID, target python module/contract, test objective, step-by-step execution path, inputs/fixtures, and exact assertions so that implementers can construct Pytest files directly.

---

## 3. Caveats

1. **External Network API Keys**: Tests for F4 (External API Adapters) must use HTTP mocking (e.g. `httpx.MockTransport` or `unittest.mock`) to avoid dependence on real API keys or external server availability during automated CI runs.
2. **ONNX Graph Generation**: Tests for F1 and F5 will utilize a lightweight synthetic ONNX VLM model builder (`omnibench/engine/dummy_model.py`) to execute fast, offline CPU inference without downloading heavy pretrained weights from HuggingFace.
3. **Host Display Environment**: Tests for F7 test `BaseOSDriver` primitives against a mock or headless display driver (e.g. `LinuxOSDriver` under `Xvfb` or `MockOSDriver`) to ensure test execution is platform-agnostic and clean in non-interactive CI environments.

---

## 4. Conclusion & Detailed E2E Test Specification (35 Test Cases)

### Summary Matrix of Tier 1 Test Cases (F1 – F7)

| Feature ID | Feature Name | Test ID Range | Target Module / Contract | Test Case Count |
| :--- | :--- | :--- | :--- | :---: |
| **F1** | ONNX 100M Local Engine | `TEST-F1-001` to `TEST-F1-005` | `omnibench.engine.local_engine` | 5 |
| **F2** | Model Preprocessor & KV Cache | `TEST-F2-001` to `TEST-F2-005` | `omnibench.engine.preprocessor`, `quantizer`, `kv_cache` | 5 |
| **F3** | Gateway Protocol & Schemas | `TEST-F3-001` to `TEST-F3-005` | `omnibench.gateway.protocol` | 5 |
| **F4** | External API Adapters | `TEST-F4-001` to `TEST-F4-005` | `omnibench.gateway.adapters.*` | 5 |
| **F5** | Local & Mock Adapters | `TEST-F5-001` to `TEST-F5-005` | `LocalONNXAdapter`, `MockAdapter` | 5 |
| **F6** | Cascading Decision Router | `TEST-F6-001` to `TEST-F6-005` | `omnibench.gateway.router` | 5 |
| **F7** | BaseOSDriver Action Primitives | `TEST-F7-001` to `TEST-F7-005` | `omnibench.drivers.base` | 5 |
| **TOTAL** | | | | **35** |

---

### Detailed Test Specifications

---

#### Feature 1: ONNX 100M Local Engine (F1)

##### `TEST-F1-001`: `test_onnx_engine_load_and_cpu_execution_provider`
- **Target Contract**: `omnibench.engine.local_engine.LocalModelEngine`
- **Objective**: Verify that `LocalModelEngine` initializes and loads an ONNX graph using `CPUExecutionProvider` without requiring GPU execution providers.
- **Test Steps**:
  1. Instantiate `engine = LocalModelEngine(model_path=dummy_onnx_path, quantization="int8")`.
  2. Call `await engine.load()`.
  3. Inspect active execution providers on the internal ONNX session.
- **Fixtures / Inputs**: Synthetic ONNX 100M model path generated by `dummy_model.py`.
- **Assertions**:
  - `engine.is_loaded` is `True`.
  - `'CPUExecutionProvider'` is in `engine.session.get_providers()`.
  - No GPU initialization errors or CUDA warnings are raised.

##### `TEST-F1-002`: `test_onnx_engine_memory_footprint_under_1_1_gib`
- **Target Contract**: `LocalModelEngine.get_memory_usage_mb()` & `psutil.Process().memory_info().rss`
- **Objective**: Ensure that process memory RSS remains strictly under ~1.1 GiB (1126.4 MB) during model load and prediction execution.
- **Test Steps**:
  1. Record baseline process RSS memory: `baseline_mb = process.memory_info().rss / (1024 * 1024)`.
  2. Load synthetic 100M parameter INT8 ONNX model into engine.
  3. Execute 5 consecutive `predict()` calls with 224x224 screenshot bytes and text prompt.
  4. Measure peak RSS memory: `peak_mb = engine.get_memory_usage_mb()`.
- **Fixtures / Inputs**: Sample prompt string `"Click on the search icon"`, synthetic 224x224 RGB image bytes.
- **Assertions**:
  - `peak_mb < 1126.4` (Strict compliance with ~1.1 GiB host memory limit).
  - RSS memory delta (`peak_mb - baseline_mb`) is $< 350.0$ MB.

##### `TEST-F1-003`: `test_onnx_engine_prediction_pipeline`
- **Target Contract**: `LocalModelEngine.predict(prompt, image_bytes, max_tokens, temperature)`
- **Objective**: Validate the full prediction pipeline output structure and response metadata.
- **Test Steps**:
  1. Initialize and load engine.
  2. Call `output = await engine.predict(prompt="Navigate to settings", image_bytes=sample_png_bytes, max_tokens=64)`.
- **Fixtures / Inputs**: Text prompt `"Navigate to settings"`, sample PNG bytes.
- **Assertions**:
  - `isinstance(output, LocalEngineOutput)` is `True`.
  - `isinstance(output.text, str)` is `True` and non-empty.
  - `output.latency_ms > 0.0`.
  - `output.prompt_tokens > 0` and `output.completion_tokens > 0`.
  - `output.memory_rss_mb > 0.0`.

##### `TEST-F1-004`: `test_onnx_engine_unload_and_memory_cleanup`
- **Target Contract**: `LocalModelEngine.unload()`
- **Objective**: Verify that invoking `unload()` explicitly destroys the ONNX session, triggers garbage collection, and releases host RAM.
- **Test Steps**:
  1. Load engine and perform prediction.
  2. Record memory RSS while model is loaded: `loaded_rss = process.memory_info().rss`.
  3. Call `engine.unload()`.
  4. Record memory RSS after unload: `unloaded_rss = process.memory_info().rss`.
- **Fixtures / Inputs**: Loaded `LocalModelEngine` instance.
- **Assertions**:
  - `engine.is_loaded` is `False`.
  - `engine.session` is `None`.
  - `unloaded_rss < loaded_rss`.

##### `TEST-F1-005`: `test_onnx_engine_quantization_modes_int8_int4`
- **Target Contract**: `LocalModelEngine(quantization=mode)`
- **Objective**: Confirm that engine supports both `int8` (Dynamic INT8) and `int4` (MatMulNBits INT4) model configurations.
- **Test Steps**:
  1. Initialize `engine_int8 = LocalModelEngine(quantization="int8")` and `engine_int4 = LocalModelEngine(quantization="int4")`.
  2. Load both engines and verify tensor element data types.
  3. Run single inference step on each engine.
- **Fixtures / Inputs**: `quantization="int8"` and `quantization="int4"` parameter flags.
- **Assertions**:
  - Both engines load without raising `ValueError` or ONNX runtime initialization exceptions.
  - Both engines return valid prediction output text.

---

#### Feature 2: Model Preprocessor & KV Cache (F2)

##### `TEST-F2-001`: `test_preprocessor_image_resizing_and_normalization`
- **Target Contract**: `omnibench.engine.preprocessor.ImagePreprocessor.process(image_bytes)`
- **Objective**: Verify that arbitrary resolution screenshots (e.g. 1920x1080, 2560x1600) are resized and normalized into a standard (3, 224, 224) float32 numpy tensor.
- **Test Steps**:
  1. Create synthetic 1920x1080 RGB PIL image.
  2. Pass image bytes to `preprocessor.process_image(raw_bytes)`.
- **Fixtures / Inputs**: 1920x1080 red-green gradient image bytes.
- **Assertions**:
  - Output tensor shape is `(1, 3, 224, 224)`.
  - Output tensor dtype is `numpy.float32`.
  - Min and max tensor pixel values lie within normalized range `[-1.0, 1.0]` or `[0.0, 1.0]`.

##### `TEST-F2-002`: `test_preprocessor_text_tokenization_and_encoding`
- **Target Contract**: `omnibench.engine.preprocessor.TextTokenizer`
- **Objective**: Test prompt text tokenization into integer token IDs and bidirectional string decoding.
- **Test Steps**:
  1. Instantiate `tokenizer = TextTokenizer()`.
  2. Encode input string `text = "Click button [Mark 5]"`.
  3. Decode token IDs back to string `decoded = tokenizer.decode(ids)`.
- **Fixtures / Inputs**: Sample string `"Click button [Mark 5]"`.
- **Assertions**:
  - `ids` is a list of positive integers.
  - `ids[0]` matches `BOS` (Beginning of Sequence) token ID.
  - `decoded.strip()` contains `"Click button [Mark 5]"`.

##### `TEST-F2-003`: `test_quantizer_int8_dynamic_quantization`
- **Target Contract**: `omnibench.engine.quantizer.DynamicQuantizer.quantize(float_model_path, quantized_output_path)`
- **Objective**: Verify that `DynamicQuantizer` converts a FP32 ONNX model graph into a quantized INT8 ONNX model graph.
- **Test Steps**:
  1. Provide standard FP32 ONNX model file.
  2. Run `DynamicQuantizer.quantize(fp32_path, int8_path)`.
  3. Load `int8_path` using ONNX module to inspect node data types.
- **Fixtures / Inputs**: FP32 dummy ONNX model graph.
- **Assertions**:
  - Output quantized file exists on disk.
  - File size of `int8_path` is significantly smaller than `fp32_path` ($\approx 25\% - 50\%$ of original size).
  - Graph nodes contain `QLinearMatMul` or `MatMulInteger` quantization operators.

##### `TEST-F2-004`: `test_kv_cache_manager_allocation_and_windowing`
- **Target Contract**: `omnibench.engine.kv_cache.KVCacheManager`
- **Objective**: Ensure `KVCacheManager` allocates key-value tensor buffers and enforces maximum context sequence length windowing.
- **Test Steps**:
  1. Instantiate `cache = KVCacheManager(max_seq_len=128, num_layers=4, num_heads=4, head_dim=32)`.
  2. Sequentially append key-value state tensors for 150 sequence tokens.
  3. Retrieve cached key-value tensors.
- **Fixtures / Inputs**: `max_seq_len=128`, token state tensors.
- **Assertions**:
  - Length of cached sequence dimension does not exceed `max_seq_len` (128).
  - Oldest tokens beyond window size 128 are automatically evicted.

##### `TEST-F2-005`: `test_kv_cache_reset_between_task_episodes`
- **Target Contract**: `KVCacheManager.reset()`
- **Objective**: Confirm that `reset()` completely clears key-value cache tensors between task steps or evaluation episodes.
- **Test Steps**:
  1. Populate KV cache with state tensors from Episode 1.
  2. Verify `cache.current_seq_len > 0`.
  3. Execute `cache.reset()`.
- **Fixtures / Inputs**: Non-empty `KVCacheManager` state.
- **Assertions**:
  - `cache.current_seq_len == 0`.
  - Internal KV cache tensors are reset to empty zero-tensors.

---

#### Feature 3: Gateway Protocol & Schemas (F3)

##### `TEST-F3-001`: `test_gateway_request_serialization_and_validation`
- **Target Contract**: `omnibench.gateway.protocol.GatewayRequest`
- **Objective**: Validate `GatewayRequest` Pydantic model construction, JSON serialization/deserialization, and field default values.
- **Test Steps**:
  1. Construct `req = GatewayRequest(messages=[ChatMessage(role=ChatRole.USER, content="Hello")], routing_strategy=RoutingStrategy.PRIMARY_FIRST)`.
  2. Serialize to JSON: `json_str = req.model_dump_json()`.
  3. Deserialize back: `req2 = GatewayRequest.model_validate_json(json_str)`.
- **Fixtures / Inputs**: Pydantic `GatewayRequest` parameters.
- **Assertions**:
  - `req2.messages[0].content == "Hello"`.
  - `req2.routing_strategy == RoutingStrategy.PRIMARY_FIRST`.
  - Default `fallback_models` list contains `["anthropic/claude-3-5-sonnet", "ollama/llama3", "local/onnx-100m"]`.

##### `TEST-F3-002`: `test_gateway_response_serialization_and_validation`
- **Target Contract**: `omnibench.gateway.protocol.GatewayResponse`
- **Objective**: Validate `GatewayResponse` structure, default fields, and nested `ToolCall` and `TokenUsage` serialization.
- **Test Steps**:
  1. Construct `resp = GatewayResponse(id="resp_001", provider="openai", model_used="gpt-4o", content="Clicked element", tool_calls=[ToolCall(id="tc_1", name="click", arguments={"x": 100, "y": 200})], usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15))`.
  2. Serialize to dict: `d = resp.model_dump()`.
- **Fixtures / Inputs**: `GatewayResponse` field data.
- **Assertions**:
  - `d["id"] == "resp_001"`.
  - `d["tool_calls"][0]["name"] == "click"`.
  - `d["usage"]["total_tokens"] == 15`.
  - `d["fallback_occurred"]` defaults to `False`.

##### `TEST-F3-003`: `test_chat_message_multimodal_content_roles`
- **Target Contract**: `omnibench.gateway.protocol.ChatMessage` & `ChatRole`
- **Objective**: Verify `ChatMessage` role validation (`SYSTEM`, `USER`, `ASSISTANT`, `TOOL`) and support for multimodal image/text content blocks.
- **Test Steps**:
  1. Create messages for each `ChatRole` enum value.
  2. Create multimodal message with list of content blocks `[{"type": "text", "text": "Screenshot:"}, {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}]`.
- **Fixtures / Inputs**: Multimodal content blocks and valid/invalid role strings.
- **Assertions**:
  - Invalid role strings (e.g., `role="invalid_role"`) raise `pydantic.ValidationError`.
  - Multimodal list content passes validation cleanly.

##### `TEST-F3-004`: `test_tool_definition_and_tool_call_schema`
- **Target Contract**: `omnibench.gateway.protocol.ToolDefinition` & `ToolCall`
- **Objective**: Verify JSON Schema parameters validation for tool definitions and tool calls.
- **Test Steps**:
  1. Define `tool = ToolDefinition(name="click", description="Click coordinate", parameters={"type": "object", "properties": {"x": {"type": "integer"}, "y": {"type": "integer"}}, "required": ["x", "y"]})`.
  2. Parse a model output tool call into `ToolCall`.
- **Fixtures / Inputs**: Tool schema dictionary.
- **Assertions**:
  - `tool.name == "click"`.
  - `tool.parameters["required"] == ["x", "y"]`.

##### `TEST-F3-005`: `test_token_usage_calculation_and_defaults`
- **Target Contract**: `omnibench.gateway.protocol.TokenUsage`
- **Objective**: Validate token metrics integrity and default values.
- **Test Steps**:
  1. Instantiate `usage = TokenUsage(prompt_tokens=120, completion_tokens=30)`.
  2. Inspect `usage.total_tokens`.
- **Fixtures / Inputs**: `prompt_tokens=120`, `completion_tokens=30`.
- **Assertions**:
  - `usage.total_tokens == 150` (or computed dynamically if `total_tokens` not passed).
  - Default `TokenUsage()` has prompt, completion, and total tokens equal to `0`.

---

#### Feature 4: External API Adapters (F4)

##### `TEST-F4-001`: `test_openai_adapter_request_formatting_and_response_parsing`
- **Target Contract**: `omnibench.gateway.adapters.openai_adapter.OpenAIAdapter`
- **Objective**: Verify that `OpenAIAdapter` formats `GatewayRequest` into OpenAI `/v1/chat/completions` JSON payload and maps HTTP 200 response to `GatewayResponse`.
- **Test Steps**:
  1. Mock HTTP client POST `/v1/chat/completions` returning mock OpenAI JSON response.
  2. Call `adapter = OpenAIAdapter(api_key="sk-test")`.
  3. Run `resp = await adapter.generate(request)`.
- **Fixtures / Inputs**: `GatewayRequest` with image and prompt, mock OpenAI API response body.
- **Assertions**:
  - Outgoing HTTP POST header contains `Authorization: Bearer sk-test`.
  - Payload contains `model: "gpt-4o"` and formatted `messages`.
  - `resp.provider == "openai"`.
  - `resp.content` and `resp.tool_calls` accurately reflect mock API response.

##### `TEST-F4-002`: `test_anthropic_adapter_messages_api_formatting`
- **Target Contract**: `omnibench.gateway.adapters.anthropic_adapter.AnthropicAdapter`
- **Objective**: Verify `AnthropicAdapter` formatting for `/v1/messages` endpoint (system prompt extraction, base64 vision blocks).
- **Test Steps**:
  1. Construct `GatewayRequest` with system prompt and base64 image content.
  2. Mock Anthropic Messages endpoint returning Claude response JSON.
  3. Execute `resp = await adapter.generate(request)`.
- **Fixtures / Inputs**: `request` with `system_prompt="You are an OS agent"`.
- **Assertions**:
  - Outgoing HTTP request extracts `system` into top-level parameter (not inside `messages` array).
  - Outgoing header contains `x-api-key: anthropic-test-key` and `anthropic-version: 2023-06-01`.
  - `resp.provider == "anthropic"`.

##### `TEST-F4-003`: `test_gemini_adapter_generate_content_payload`
- **Target Contract**: `omnibench.gateway.adapters.gemini_adapter.GeminiAdapter`
- **Objective**: Verify `GeminiAdapter` formatting for Google Gemini REST `generateContent` API.
- **Test Steps**:
  1. Mock Gemini endpoint response with `candidates` array.
  2. Call `adapter = GeminiAdapter(api_key="gemini-test-key")`.
  3. Execute `resp = await adapter.generate(request)`.
- **Fixtures / Inputs**: Sample `GatewayRequest`.
- **Assertions**:
  - Outgoing payload uses `contents` and `parts` structure required by Gemini API.
  - `resp.provider == "gemini"`.

##### `TEST-F4-004`: `test_ollama_adapter_local_rest_endpoint`
- **Target Contract**: `omnibench.gateway.adapters.ollama_adapter.OllamaAdapter`
- **Objective**: Verify `OllamaAdapter` calling local Ollama REST server (`http://localhost:11434/api/chat`).
- **Test Steps**:
  1. Mock local HTTP endpoint at `http://localhost:11434/api/chat` with `stream: false`.
  2. Call `adapter = OllamaAdapter(host="http://localhost:11434")`.
  3. Execute `resp = await adapter.generate(request)`.
- **Fixtures / Inputs**: `host="http://localhost:11434"`, mock Ollama chat JSON.
- **Assertions**:
  - Outgoing request body has `"stream": false`.
  - `resp.provider == "ollama"`.

##### `TEST-F4-005`: `test_adapter_http_error_and_timeout_handling`
- **Target Contract**: `BaseAdapter` exception handling across external adapters
- **Objective**: Verify that HTTP 429 (Rate Limit), 500 (Internal Server Error), and connection timeouts are caught and converted into standard `GatewayAdapterError`.
- **Test Steps**:
  1. Configure mock HTTP client to return status code 429 and status code 500 for adapter calls.
  2. Execute `adapter.generate(request)` and catch raised exception.
- **Fixtures / Inputs**: Mock HTTP error responses and timeout exceptions.
- **Assertions**:
  - Adapter raises `GatewayAdapterError` (or subclass `ProviderRateLimitError` / `ProviderServerError`).
  - Raised exception contains HTTP status code and original error message details.

---

#### Feature 5: Local & Mock Adapters (F5)

##### `TEST-F5-001`: `test_local_onnx_adapter_prediction_wrapping`
- **Target Contract**: `omnibench.gateway.adapters.local_onnx_adapter.LocalONNXAdapter`
- **Objective**: Verify `LocalONNXAdapter` wrapping `LocalModelEngine` and producing compliant `GatewayResponse` objects.
- **Test Steps**:
  1. Instantiate `LocalModelEngine` with synthetic dummy model.
  2. Wrap engine into `adapter = LocalONNXAdapter(engine=engine)`.
  3. Execute `resp = await adapter.generate(request)`.
- **Fixtures / Inputs**: Loaded `LocalModelEngine` instance, `GatewayRequest`.
- **Assertions**:
  - `resp.provider == "local_onnx"`.
  - `resp.model_used == "local/onnx-100m"`.
  - `isinstance(resp.latency_ms, float)` and `resp.latency_ms > 0.0`.
  - `resp.fallback_occurred` is `False`.

##### `TEST-F5-002`: `test_mock_adapter_deterministic_response_generation`
- **Target Contract**: `omnibench.gateway.adapters.mock_adapter.MockAdapter`
- **Objective**: Verify `MockAdapter` generating deterministic text and tool call responses without external network access.
- **Test Steps**:
  1. Instantiate `adapter = MockAdapter()`.
  2. Call `resp = await adapter.generate(request)`.
- **Fixtures / Inputs**: Standard `GatewayRequest`.
- **Assertions**:
  - `resp.provider == "mock"`.
  - `resp.model_used == "mock/deterministic"`.
  - `resp.content` is non-empty.
  - Response completes in $< 10$ milliseconds.

##### `TEST-F5-003`: `test_mock_adapter_custom_response_configuration`
- **Target Contract**: `MockAdapter.set_custom_response()` & `MockAdapter.set_error_mode()`
- **Objective**: Verify configuring `MockAdapter` to return preset text, preset tool calls, or raise specific simulated errors.
- **Test Steps**:
  1. Configure `adapter.set_custom_response(content="Preset click", tool_calls=[ToolCall(id="tc_1", name="click", arguments={"x": 50, "y": 50})])`.
  2. Run `resp = await adapter.generate(request)`.
  3. Configure `adapter.set_error_mode(status_code=500)` and run `generate()`.
- **Fixtures / Inputs**: Preset content string, tool calls list, error status code.
- **Assertions**:
  - Step 2: `resp.content == "Preset click"` and `resp.tool_calls[0].name == "click"`.
  - Step 3: Call raises `GatewayAdapterError`.

##### `TEST-F5-004`: `test_mock_adapter_latency_simulation_and_call_counter`
- **Target Contract**: `MockAdapter` latency injection & `call_count` tracking
- **Objective**: Test mock adapter simulated latency (`latency_ms=100`) and invocation counting.
- **Test Steps**:
  1. Instantiate `adapter = MockAdapter(simulated_latency_ms=100.0)`.
  2. Verify initial `adapter.call_count == 0`.
  3. Execute 3 consecutive `generate(request)` calls.
- **Fixtures / Inputs**: `simulated_latency_ms=100.0`.
- **Assertions**:
  - `adapter.call_count == 3`.
  - Recorded `resp.latency_ms >= 100.0`.

##### `TEST-F5-005`: `test_adapter_protocol_polymorphism_and_schema_parity`
- **Target Contract**: `BaseAdapter` interface compliance across all adapter implementations
- **Objective**: Confirm that `LocalONNXAdapter`, `MockAdapter`, `OpenAIAdapter`, `AnthropicAdapter`, `GeminiAdapter`, and `OllamaAdapter` all inherit from `BaseAdapter` and strictly produce `GatewayResponse` outputs matching the common schema.
- **Test Steps**:
  1. Create list of adapter instances `[MockAdapter(), LocalONNXAdapter(engine), ...]`.
  2. Iterate through adapters calling `await adapter.health_check()` and `await adapter.generate(request)`.
- **Fixtures / Inputs**: List of adapter instances, identical `GatewayRequest`.
- **Assertions**:
  - `issubclass(type(adapter), BaseAdapter)` is `True` for every adapter.
  - Every returned object is a valid `GatewayResponse` instance matching schema.

---

#### Feature 6: Cascading Decision Router (F6)

##### `TEST-F6-001`: `test_router_primary_first_successful_routing`
- **Target Contract**: `omnibench.gateway.router.CascadingRouter.route(request)`
- **Objective**: Confirm that `CascadingRouter` routes directly to the primary provider adapter when healthy, returning `fallback_occurred=False`.
- **Test Steps**:
  1. Configure router with primary adapter `MockAdapter(name="openai")` and fallback adapter `MockAdapter(name="local_onnx")`.
  2. Send `GatewayRequest(routing_strategy=RoutingStrategy.PRIMARY_FIRST)`.
- **Fixtures / Inputs**: Primary adapter, fallback adapter, `PRIMARY_FIRST` strategy.
- **Assertions**:
  - `resp.provider == "openai"`.
  - `resp.fallback_occurred` is `False`.
  - `resp.fallback_chain == []`.

##### `TEST-F6-002`: `test_router_fallback_chain_execution_on_error`
- **Target Contract**: `CascadingRouter` error handling & fallback chain
- **Objective**: Verify that when the primary adapter fails (e.g. HTTP 500 or timeout), `CascadingRouter` automatically invokes the fallback adapter, setting `fallback_occurred=True` and populating `fallback_chain`.
- **Test Steps**:
  1. Set primary adapter to failing mock (`status_code=500`).
  2. Set secondary adapter to successful `MockAdapter(name="local_onnx")`.
  3. Send request through router.
- **Fixtures / Inputs**: Failing primary adapter, operational secondary adapter.
- **Assertions**:
  - `resp.provider == "local_onnx"`.
  - `resp.fallback_occurred` is `True`.
  - `resp.fallback_chain == ["openai"]`.

##### `TEST-F6-003`: `test_router_local_only_strategy_enforcement`
- **Target Contract**: `RoutingStrategy.LOCAL_ONLY`
- **Objective**: Verify that `RoutingStrategy.LOCAL_ONLY` bypasses all external network adapters and routes directly to `LocalONNXAdapter`.
- **Test Steps**:
  1. Configure router with primary external adapter (`OpenAIAdapter`) and local ONNX adapter (`LocalONNXAdapter`).
  2. Send `GatewayRequest(routing_strategy=RoutingStrategy.LOCAL_ONLY)`.
- **Fixtures / Inputs**: Router instance, `RoutingStrategy.LOCAL_ONLY`.
- **Assertions**:
  - `resp.provider == "local_onnx"`.
  - Primary external adapter `generate()` is never invoked.

##### `TEST-F6-004`: `test_router_missing_api_key_automatic_fallback`
- **Target Contract**: `CascadingRouter` credential check & fallback
- **Objective**: Test that when external provider API keys are missing/unconfigured (`OPENAI_API_KEY=None`), router skips external provider without crashing and routes to available local/mock adapter.
- **Test Steps**:
  1. Initialize router with `OpenAIAdapter` without setting `OPENAI_API_KEY`.
  2. Send `GatewayRequest(routing_strategy=RoutingStrategy.AUTO)`.
- **Fixtures / Inputs**: Unset environment variables for external API keys.
- **Assertions**:
  - Request succeeds cleanly without raising `KeyError` or `ValueError`.
  - `resp.provider` reflects local or mock adapter.
  - `resp.fallback_occurred` is `True`.

##### `TEST-F6-005`: `test_router_all_providers_failure_propagation`
- **Target Contract**: `CascadingRouter` total failure exception handling
- **Objective**: Confirm that when ALL primary and fallback adapters in the chain fail, `CascadingRouter` raises `GatewayRoutingError` containing the complete failure history.
- **Test Steps**:
  1. Configure primary and all fallback adapters to fail (raise errors).
  2. Send `GatewayRequest` through router and catch exception.
- **Fixtures / Inputs**: All adapters set to fail mode.
- **Assertions**:
  - Router raises `GatewayRoutingError`.
  - Exception object contains `attempted_providers = ["openai", "anthropic", "local_onnx"]` and detailed error messages per provider.

---

#### Feature 7: BaseOSDriver Action Primitives (F7)

##### `TEST-F7-001`: `test_base_os_driver_action_primitive_click_and_double_click`
- **Target Contract**: `omnibench.drivers.base.BaseOSDriver.execute_action` (`ActionType.CLICK`, `ActionType.DOUBLE_CLICK`)
- **Objective**: Verify execution of `CLICK` and `DOUBLE_CLICK` primitives, coordinate validation, and `ActionResult` output formatting.
- **Test Steps**:
  1. Instantiate driver (`driver = MockOSDriver(screen_width=1920, screen_height=1080)`).
  2. Call `res1 = driver.execute_action(ActionPrimitive(action_type=ActionType.CLICK, x=500, y=300, button="left"))`.
  3. Call `res2 = driver.execute_action(ActionPrimitive(action_type=ActionType.DOUBLE_CLICK, x=500, y=300))`.
- **Fixtures / Inputs**: `(x=500, y=300)` coordinates within screen bounds.
- **Assertions**:
  - `res1.success` and `res2.success` are `True`.
  - `res1.action.action_type == ActionType.CLICK`.
  - `res2.action.action_type == ActionType.DOUBLE_CLICK`.
  - `res1.duration_ms >= 0.0`.

##### `TEST-F7-002`: `test_base_os_driver_action_primitive_right_click_and_drag`
- **Target Contract**: `BaseOSDriver.execute_action` (`ActionType.RIGHT_CLICK`, `ActionType.DRAG`)
- **Objective**: Verify execution of `RIGHT_CLICK` and `DRAG` action primitives and start/end coordinate handling.
- **Test Steps**:
  1. Call `res_rc = driver.execute_action(ActionPrimitive(action_type=ActionType.RIGHT_CLICK, x=400, y=200, button="right"))`.
  2. Call `res_drag = driver.execute_action(ActionPrimitive(action_type=ActionType.DRAG, x=100, y=100, end_x=500, end_y=500, duration=0.5))`.
- **Fixtures / Inputs**: Start `(100, 100)` and end `(500, 500)` drag coordinates.
- **Assertions**:
  - Both action results report `success == True`.
  - `res_drag.action.end_x == 500` and `res_drag.action.end_y == 500`.

##### `TEST-F7-003`: `test_base_os_driver_action_primitive_type_and_key_combination`
- **Target Contract**: `BaseOSDriver.execute_action` (`ActionType.TYPE`, `ActionType.KEY_COMBINATION`)
- **Objective**: Verify `TYPE` string keystroke injection and `KEY_COMBINATION` key array execution (e.g. `["ctrl", "c"]`).
- **Test Steps**:
  1. Call `res_type = driver.execute_action(ActionPrimitive(action_type=ActionType.TYPE, text="Hello OmniBench"))`.
  2. Call `res_key = driver.execute_action(ActionPrimitive(action_type=ActionType.KEY_COMBINATION, keys=["ctrl", "a"]))`.
- **Fixtures / Inputs**: `text="Hello OmniBench"`, `keys=["ctrl", "a"]`.
- **Assertions**:
  - `res_type.action.text == "Hello OmniBench"`.
  - `res_key.action.keys == ["ctrl", "a"]`.
  - Both actions return `success == True`.

##### `TEST-F7-004`: `test_base_os_driver_action_primitive_scroll_and_wait`
- **Target Contract**: `BaseOSDriver.execute_action` (`ActionType.SCROLL`, `ActionType.WAIT`)
- **Objective**: Verify `SCROLL` (direction, amount) and `WAIT` (duration sleep) execution timing.
- **Test Steps**:
  1. Call `res_scroll = driver.execute_action(ActionPrimitive(action_type=ActionType.SCROLL, x=600, y=400, direction="down", amount=200))`.
  2. Measure execution time of `res_wait = driver.execute_action(ActionPrimitive(action_type=ActionType.WAIT, seconds=0.2))`.
- **Fixtures / Inputs**: `direction="down"`, `amount=200`, `seconds=0.2`.
- **Assertions**:
  - `res_scroll.action.direction == "down"` and `amount == 200`.
  - Elapsed duration for `res_wait` is $\ge 200$ ms ($0.2$ s).

##### `TEST-F7-005`: `test_base_os_driver_screenshot_capture_and_coordinate_bounds_validation`
- **Target Contract**: `BaseOSDriver.capture_screenshot()` & `CoordinatesOutOfBoundsError`
- **Objective**: Verify `capture_screenshot()` returns valid PIL Image or image bytes, and driver raises `CoordinatesOutOfBoundsError` when action coordinates exceed screen dimensions.
- **Test Steps**:
  1. Call `img = driver.capture_screenshot()`.
  2. Attempt click action out of bounds: `driver.execute_action(ActionPrimitive(action_type=ActionType.CLICK, x=9999, y=9999))`.
- **Fixtures / Inputs**: Out-of-bounds coordinates `(9999, 9999)` for 1920x1080 screen.
- **Assertions**:
  - Step 1: `img` is not `None` and returns valid image object / non-empty bytes.
  - Step 2: Driver raises `CoordinatesOutOfBoundsError`.

---

## 5. Verification Method

To independently verify the test specifications and execute the resulting Pytest suite:

1. **Environment Setup & Verification**:
   ```bash
   cd "/home/oh_my_macos27/OmniBench Computer Use"
   .venv/bin/python -c "import onnxruntime, pydantic, httpx, numpy, pillow, psutil; print('Environment verified!')"
   ```

2. **Execute Tier 1 E2E Pytest Suite**:
   ```bash
   .venv/bin/pytest tests/e2e/tier1_features -v
   ```

3. **Verify Expected Results**:
   - All 35 test cases (`TEST-F1-001` through `TEST-F7-005`) pass with 0 failures (`35 passed in X.XXs`).
   - Memory RSS during F1 execution stays strictly under 1126.4 MB (1.1 GiB).
   - F4 and F5 adapters return compliant `GatewayResponse` schemas.
   - F6 `CascadingRouter` correctly handles fallbacks and strategy enforcement.
   - F7 `BaseOSDriver` action primitives execute and validate bounds correctly.

4. **Invalidation Conditions**:
   - Any test failure in `tests/e2e/tier1_features/`.
   - Process RSS memory exceeding 1.1 GiB (1126.4 MB) during `LocalModelEngine` execution.
   - Incomplete schema validation or unhandled exceptions during adapter HTTP mocking.
