# Project: OmniBench 1.0

## Architecture
OmniBench 1.0 is a universal computer use model and benchmark framework consisting of five primary system pillars and an E2E testing track:
1. **Engine & Gateway (`omnibench.engine`, `omnibench.gateway`)**: 100M ONNX local VLM engine (<1.1 GiB RAM on CPU) and Universal Model Gateway adapter cascading router.
2. **OS Automation Drivers (`omnibench.drivers`)**: Platform driver abstraction supporting Windows, macOS, Linux (Xvfb/xdotool), Android (ADB), and iOS (simctl) action primitives with exponential jittered retry backoff.
3. **Visual Grounding & SoM (`omnibench.visual`)**: Image tiling/resizing, sliding 3-screenshot trajectory memory, and Set-of-Marks UI element annotator + `MarkMap`.
4. **Benchmark & Evaluation (`omnibench.evaluators`, `omnibench.benchmarks`)**: Task runner, benchmark dataset adapters (OSWorld, WebArena, AndroidWorld, Mind2Web, GAIA, native OmniBench), dual evaluators (visual state diffing + system assertions), and self-correction handlers.
5. **CLI & Telemetry Dashboard (`omnibench.telemetry`, `omnibench.cli`, `omnibench.dashboard`)**: `omnibench` CLI, SQLite run logger, screenshot diff analytics engine, and Web UI.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | ONNX 100M Local Engine | Local ONNX Runtime VLM engine optimized for CPU INT8/INT4 under ~1.1 GiB RAM | M1 | R1 |
| 2 | Model Preprocessor & KV Cache | Image/text input formatter, INT8/INT4 quantizer, and KV cache manager | M1 | R1 |
| 3 | Gateway Protocol & Schemas | Unified Pydantic request/response data contracts (`GatewayRequest`/`GatewayResponse`) | M1 | R1 |
| 4 | External API Adapters | Unified adapters for OpenAI, Anthropic Claude, Gemini, and local Ollama | M1 | R1 |
| 5 | Local & Mock Adapters | Local ONNX engine adapter and offline testing Mock adapter | M1 | R1 |
| 6 | Cascading Router | Priority decision router with automated provider fallback & error handling | M1 | R1 |
| 7 | Unified OSDriver Interface | `BaseOSDriver` contract defining 8 action primitives with type validation | M2 | R2 |
| 8 | Desktop OS Drivers | Linux (Xvfb/xdotool), Windows (pywinauto/PowerShell), macOS (CoreGraphics) drivers | M2 | R2 |
| 9 | Mobile OS Drivers | Android (ADB/uiautomator daemon) and iOS (simctl/daemon) drivers | M2 | R2 |
| 10 | Error Retry & Backoff | Exponential retry backoff decorator with random jitter and daemon reconnect | M2 | R2 |
| 11 | Screen Processing Pipeline | Image Resizer (tiling/downscaling) and Color Converter (RGB/Grayscale) | M3 | R3 |
| 12 | Sliding Trajectory Memory | Strictly bounded 3-screenshot memory buffer + text action logs | M3 | R3 |
| 13 | Set-of-Marks (SoM) Generator | Interactive UI bounding box annotator & bidirectional `MarkMap` lookup | M3 | R3 |
| 14 | Task Execution Runner | Standardized JSON task schema and `BenchmarkRunner` event loop | M4 | R4 |
| 15 | Benchmark Adapters | Dataset adapters for OSWorld, WebArena, AndroidWorld, Mind2Web, GAIA, OmniBench | M4 | R4 |
| 16 | Dual Evaluator Engine | Visual state diffing (SSIM/pHash/ROI/OCR) + system CLI/API state assertions | M4 | R4 |
| 17 | Self-Correction Handlers | Level 1/2 retries and visual stagnation feedback injector | M4 | R4 |
| 18 | `omnibench` CLI | Python CLI (`config`, `dataset`, `run`, `monitor`, `db`, `dashboard`) | M5 | R5 |
| 19 | SQLite Telemetry & DDL | SQLite schema (`runs`, `episodes`, `steps`, `screenshot_diffs`) and logger | M5 | R5 |
| 20 | Screenshot Diff Analytics | MSE, SSIM, pixel diff percentage, and difference mask generator | M5 | R5 |
| 21 | Web Dashboard UI | Python HTTP/SSE live telemetry backend + responsive SPA dashboard frontend | M5 | R5 |
| 22 | E2E Verification & Hardening | Pass 100% E2E test suite (Tiers 1-4) + white-box adversarial hardening (Tier 5) | M6 | Acceptance |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Engine & Gateway | `omnibench.engine` & `omnibench.gateway` | none | IN_PROGRESS |
| M2 | OS Automation Drivers | `omnibench.drivers` | none | IN_PROGRESS |
| M3 | Visual Grounding & SoM | `omnibench.visual` | none | IN_PROGRESS |
| M4 | Benchmark Evaluation | `omnibench.evaluators` & `omnibench.benchmarks` | M1, M2, M3 | PLANNED |
| M5 | Telemetry & Dashboard | `omnibench.telemetry`, `omnibench.cli`, `omnibench.dashboard` | M1, M2, M3 | PLANNED |
| M6 | E2E Integration & Hardening | Full E2E verification (Phase 1 & Phase 2) | M1, M2, M3, M4, M5 | PLANNED |

## Interface Contracts

### `omnibench.gateway` ↔ `omnibench.engine`
- `GatewayRequest`: `prompt: str`, `images: list[bytes]`, `temperature: float`, `max_tokens: int`, `model_name: str`
- `GatewayResponse`: `text: str`, `action_json: dict`, `usage_tokens: int`, `latency_ms: float`, `provider_used: str`
- `LocalONNXAdapter.generate(req: GatewayRequest) -> GatewayResponse`

### `omnibench.drivers` ↔ Benchmark Runner
- `BaseOSDriver.execute_action(action_type: str, params: dict) -> ActionResult`
- `BaseOSDriver.capture_screenshot() -> PIL.Image`
- Action types: `click`, `double_click`, `right_click`, `drag`, `type`, `key_combination`, `scroll`, `wait`

### `omnibench.visual` ↔ Benchmark Runner & Model Engine
- `SoMAnnotator.annotate(screenshot: Image) -> tuple[Image, MarkMap]`
- `MarkMap.get_coordinates(mark_id: int) -> tuple[int, int]`
- `SlidingTrajectoryMemory.add_step(screenshot: Image, action_str: str) -> MemoryState`

### `omnibench.evaluators` ↔ Benchmark Runner
- `DualEvaluator.evaluate(initial_state: dict, final_state: dict, trajectory: list) -> EvaluationResult`
- `EvaluationResult`: `passed: bool`, `score: float`, `visual_diff_score: float`, `system_assertion_passed: bool`, `details: dict`

## Code Layout
```
/home/oh_my_macos27/OmniBench Computer Use/
├── omnibench/
│   ├── __init__.py
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── onnx_engine.py
│   │   ├── preprocessor.py
│   │   ├── quantizer.py
│   │   └── dummy_model.py
│   ├── gateway/
│   │   ├── __init__.py
│   │   ├── protocol.py
│   │   ├── adapters.py
│   │   └── router.py
│   ├── drivers/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── linux.py
│   │   ├── windows.py
│   │   ├── macos.py
│   │   ├── android.py
│   │   ├── ios.py
│   │   └── retry.py
│   ├── visual/
│   │   ├── __init__.py
│   │   ├── processing.py
│   │   ├── som.py
│   │   └── memory.py
│   ├── evaluators/
│   │   ├── __init__.py
│   │   ├── visual_diff.py
│   │   ├── system_assertions.py
│   │   ├── dual_evaluator.py
│   │   └── self_correction.py
│   ├── benchmarks/
│   │   ├── __init__.py
│   │   ├── runner.py
│   │   ├── task_schema.py
│   │   └── adapters/
│   │       ├── osworld.py
│   │       ├── webarena.py
│   │       ├── androidworld.py
│   │       ├── mind2web.py
│   │       ├── gaia.py
│   │       └── omnibench_native.py
│   ├── telemetry/
│   │   ├── __init__.py
│   │   ├── logger.py
│   │   ├── db.py
│   │   └── analytics.py
│   ├── cli/
│   │   ├── __init__.py
│   │   └── main.py
│   └── dashboard/
│       ├── __init__.py
│       ├── server.py
│       └── static/
│           └── index.html
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── ORIGINAL_REQUEST.md
├── PROJECT.md
└── TEST_INFRA.md
```
