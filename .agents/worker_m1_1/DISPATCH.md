## 2026-08-08T11:16:12Z
You are worker_m1_1.
Your working directory is: /home/oh_my_macos27/OmniBench Computer Use/.agents/worker_m1_1

Please read the following authoritative files:
- /home/oh_my_macos27/OmniBench Computer Use/ORIGINAL_REQUEST.md
- /home/oh_my_macos27/OmniBench Computer Use/PROJECT.md
- /home/oh_my_macos27/OmniBench Computer Use/.agents/orch_m1_engine/SCOPE.md
- /home/oh_my_macos27/OmniBench Computer Use/.agents/spec_miner_m1_1/handoff.md
- /home/oh_my_macos27/OmniBench Computer Use/.agents/explorer_m1_2/handoff.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Objective:
Implement Milestone M1 (100M Parameter ONNX Local Model Engine & Universal Model Gateway) in python:

1. Target Code Layout:
- `omnibench/__init__.py`
- `omnibench/engine/__init__.py`
- `omnibench/engine/onnx_engine.py`: Implement `ONNXLocalEngine` utilizing `onnxruntime` with `CPUExecutionProvider`. Incorporate memory tracking via `psutil` to verify process RSS memory remains strictly < 1.1 GiB (1126.4 MiB). Include auto-generation of synthetic model via `DummyModelGenerator` when no external model file path is provided.
- `omnibench/engine/preprocessor.py`: Implement `Preprocessor` (image resizing to 224x224, RGB float32 tensor formatting, text prompt token formatting) and `KVCacheManager` (layer-wise Key/Value tensor cache with memory limit assertions).
- `omnibench/engine/quantizer.py`: Implement `ModelQuantizer` for INT8/INT4 ONNX quantization and compression ratio calculations.
- `omnibench/engine/dummy_model.py`: Implement `DummyModelGenerator` creating valid lightweight ONNX protobuf model binaries on-the-fly for CPU inference testing.
- `omnibench/gateway/__init__.py`
- `omnibench/gateway/protocol.py`: Implement Pydantic `GatewayRequest` (prompt, images, temperature, max_tokens, model_name, metadata) and `GatewayResponse` (text, action_json, usage_tokens, latency_ms, provider_used, error).
- `omnibench/gateway/adapters.py`: Implement `BaseAdapter`, `OpenAIAdapter`, `AnthropicAdapter`, `GeminiAdapter`, `OllamaAdapter`, `LocalONNXAdapter` (integrating `ONNXLocalEngine`), and `MockAdapter` (for offline test doubles).
- `omnibench/gateway/router.py`: Implement `CascadingRouter` with priority chain routing, automated provider fallback on errors/timeouts, circuit breaker `ProviderHealth`, and mock fallback.
- `tests/unit/test_engine.py`: Unit tests for `omnibench.engine` verifying model loading, generation, memory constraint (<1.1 GiB RAM), preprocessor, KV cache, and quantizer.
- `tests/unit/test_gateway.py`: Unit tests for `omnibench.gateway` verifying protocols, adapters, circuit breaker, cascading router fallback, and mock adapter execution.

2. Verification:
Run `.venv/bin/python3 -m pytest tests/unit/ -v` and confirm all tests pass, system CPU RAM is strictly < 1.1 GiB during execution, and layout complies with `PROJECT.md`.

Write your implementation report to `/home/oh_my_macos27/OmniBench Computer Use/.agents/worker_m1_1/handoff.md` with build/test outputs and memory measurement.
Send message to parent orchestrator when done.
