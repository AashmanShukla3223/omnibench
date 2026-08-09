# Scope: Milestone M1 (Engine & Gateway)

## Mission
Deliver Milestone M1 for OmniBench 1.0: 100M Parameter ONNX Local Model Engine & Universal Model Gateway (Features 1-6 in PROJECT.md).

## Target Modules
- `omnibench/engine/`: `onnx_engine.py`, `preprocessor.py`, `quantizer.py`, `dummy_model.py`
- `omnibench/gateway/`: `protocol.py`, `adapters.py`, `router.py`

## Feature Inventory (M1 Scope)
| # | Feature | Description | Target Module |
|---|---------|-------------|---------------|
| 1 | ONNX 100M Local Engine | Local ONNX Runtime VLM engine optimized for CPU INT8/INT4 under ~1.1 GiB RAM | `omnibench/engine/onnx_engine.py`, `dummy_model.py` |
| 2 | Model Preprocessor & KV Cache | Image/text input formatter, INT8/INT4 quantizer, and KV cache manager | `omnibench/engine/preprocessor.py`, `quantizer.py` |
| 3 | Gateway Protocol & Schemas | Unified Pydantic request/response data contracts (`GatewayRequest`/`GatewayResponse`) | `omnibench/gateway/protocol.py` |
| 4 | External API Adapters | Unified adapters for OpenAI, Anthropic Claude, Gemini, and local Ollama | `omnibench/gateway/adapters.py` |
| 5 | Local & Mock Adapters | Local ONNX engine adapter and offline testing Mock adapter | `omnibench/gateway/adapters.py` |
| 6 | Cascading Router | Priority decision router with automated provider fallback & error handling | `omnibench/gateway/router.py` |

## Interface Contracts
- `GatewayRequest`: `prompt: str`, `images: list[bytes]`, `temperature: float`, `max_tokens: int`, `model_name: str`
- `GatewayResponse`: `text: str`, `action_json: dict`, `usage_tokens: int`, `latency_ms: float`, `provider_used: str`
- `LocalONNXAdapter.generate(req: GatewayRequest) -> GatewayResponse`

## Technical Constraints & Requirements
- CPU RAM for ONNX Engine < 1.1 GiB.
- Gateway protocol schema strict enforcement (Pydantic v2 or standard dataclass/Pydantic validation).
- Cascading Router: Provider priority list, mock adapter support for offline unit tests, failover retry mechanism.
- Unit tests under `tests/unit/test_engine.py` and `tests/unit/test_gateway.py`.
