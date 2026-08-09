# Scope: Milestone M1 — Engine & Gateway

## Architecture
Milestone M1 delivers the local ONNX model engine and the universal model gateway for OmniBench 1.0:
- `omnibench/engine/`: ONNX VLM engine (<1.1 GiB RAM on CPU), preprocessor, KV cache manager, INT8/INT4 quantization helper, and fallback dummy ONNX model generator.
- `omnibench/gateway/`: Protocol schemas (`GatewayRequest`/`GatewayResponse`), API adapters (OpenAI, Anthropic, Gemini, Ollama, Local ONNX, Mock), and cascading decision router.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | ONNX 100M Local Engine | Local ONNX Runtime VLM engine optimized for CPU INT8/INT4 under ~1.1 GiB RAM | M1 | R1 |
| 2 | Model Preprocessor & KV Cache | Image/text input formatter, INT8/INT4 quantizer, and KV cache manager | M1 | R1 |
| 3 | Gateway Protocol & Schemas | Unified Pydantic request/response data contracts (`GatewayRequest`/`GatewayResponse`) | M1 | R1 |
| 4 | External API Adapters | Unified adapters for OpenAI, Anthropic Claude, Gemini, and local Ollama | M1 | R1 |
| 5 | Local & Mock Adapters | Local ONNX engine adapter (`LocalONNXAdapter`) and offline testing Mock adapter | M1 | R1 |
| 6 | Cascading Router | Priority decision router with automated provider fallback & error handling | M1 | R1 |

## Interface Contracts
### `omnibench.gateway` ↔ `omnibench.engine`
- `GatewayRequest`: `prompt: str`, `images: list[bytes]`, `temperature: float`, `max_tokens: int`, `model_name: str`
- `GatewayResponse`: `text: str`, `action_json: dict`, `usage_tokens: int`, `latency_ms: float`, `provider_used: str`
- `LocalONNXAdapter.generate(req: GatewayRequest) -> GatewayResponse`

## Memory Limit Constraint
- Host CPU RAM usage must be strictly < 1.1 GiB (1179.6 MB) during inference and model execution.

## Code Layout
- `omnibench/engine/__init__.py`
- `omnibench/engine/onnx_engine.py`
- `omnibench/engine/preprocessor.py`
- `omnibench/engine/quantizer.py`
- `omnibench/engine/dummy_model.py`
- `omnibench/gateway/__init__.py`
- `omnibench/gateway/protocol.py`
- `omnibench/gateway/adapters.py`
- `omnibench/gateway/router.py`
- `tests/unit/test_engine.py`
- `tests/unit/test_gateway.py`
