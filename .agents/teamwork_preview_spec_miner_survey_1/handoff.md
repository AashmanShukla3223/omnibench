# Specification Mining Handoff Report — OmniBench 1.0

## Observation
- **Direct Workspace Observations**:
  - `ORIGINAL_REQUEST.md` (lines 1-35): Establishes OmniBench 1.0 as a universal computer use model and benchmark framework integrating cross-platform execution drivers, local 100M parameter ONNX VLM engine (<1.1 GiB RAM on CPU), Universal Model Gateway, Visual SoM preprocessor, dual evaluation engine, CLI, and Web Dashboard.
  - `PROJECT.md` (lines 1-136): Defines 5 system pillars (`omnibench.engine`, `omnibench.gateway`, `omnibench.drivers`, `omnibench.visual`, `omnibench.evaluators`/`benchmarks`, `omnibench.telemetry`/`cli`/`dashboard`), 22 feature inventory items across 6 milestones (M1-M6), and standard Python package layout.
  - `TEST_INFRA.md` (lines 1-53): Establishes test strategy across Tier 1 (105 feature tests), Tier 2 (105 boundary tests), Tier 3 (21 pairwise combination tests), and Tier 4 (6 real-world workload scenarios), targeting ≥237 E2E test cases.
  - Workspace directory contains specifications and configuration files without pre-existing source code in `omnibench/` or `tests/`, confirming project is in specification mining & blueprint verification phase.

## Logic Chain
1. **R1 Engine & Gateway Alignment**:
   - System prompt & requirements demand <1.1 GiB host RAM on CPU without GPU.
   - ONNX Runtime INT8/INT4 quantization (`omnibench.engine.quantizer`) combined with dummy/mock weight loaders ensures memory cap compliance.
   - `GatewayRequest` / `GatewayResponse` protocol schemas isolate gateway clients from underlying providers (OpenAI, Anthropic, Gemini, Ollama, Local ONNX, Mock).
   - `CascadingRouter` provides automatic fallback when external APIs fail or hit rate limits.

2. **R2 Cross-Platform Automation Alignment**:
   - `BaseOSDriver` standardizes 8 action primitives: `click`, `double_click`, `right_click`, `drag`, `type`, `key_combination`, `scroll`, `wait`.
   - Desktop drivers utilize `xdotool`/Xvfb (Linux), `pywinauto`/PowerShell (Windows), and CoreGraphics/Quartz (macOS).
   - Mobile drivers interface via `ADB`/`uiautomator` (Android) and `simctl`/daemon (iOS).
   - Exponential jittered backoff (`omnibench.drivers.retry`) handles temporary UI lockups or RPC daemon dropouts.

3. **R3 Visual Grounding & SoM Alignment**:
   - `Screen Processing Pipeline` handles resolution downscaling, sub-region tiling, and color space transformations (RGB/Grayscale).
   - `Sliding Trajectory Memory` maintains a strict 3-screenshot sliding window buffer alongside unbounded text action logs to prevent memory inflation.
   - `Set-of-Marks (SoM) Generator` detects UI element bounding boxes, overlays numeric tags, and returns a bidirectional `MarkMap` for mark ID <-> pixel coordinate translation.

4. **R4 Benchmark Engine Alignment**:
   - `BenchmarkRunner` standardizes evaluation across 6 datasets: OSWorld, WebArena, AndroidWorld, Mind2Web, GAIA, and OmniBench Native.
   - `DualEvaluator` combines visual state diffing (SSIM, pHash, ROI, OCR) with system CLI/API state assertions.
   - `Self-Correction Handlers` provide L1/L2 retries and visual stagnation prompt injection when screen states remain static despite agent actions.

5. **R5 Interface & Telemetry Alignment**:
   - `omnibench` CLI provides commands: `config`, `dataset`, `run`, `monitor`, `db`, `dashboard`.
   - SQLite telemetry schema (`runs`, `episodes`, `steps`, `screenshot_diffs`) enables transactional run logging.
   - Diff analytics engine computes MSE, SSIM, pixel diff percentages, and generates visual difference overlay masks.
   - Web Dashboard backend (`server.py`) serves HTTP REST endpoints and SSE streams for responsive SPA UI.

## Features Discovered
| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | R1 Model Engine | ONNX 100M Local Engine | Local ONNX Runtime VLM engine optimized for CPU INT8/INT4 execution operating strictly under <1.1 GiB host RAM. | Prompt string, image bytes/PIL, `max_tokens`, `temperature` | Text output, `action_json`, `usage_tokens`, `latency_ms` | Out-of-memory or model load failures trigger error or fallback to mock | `PROJECT.md` § Feature 1, `ORIGINAL_REQUEST.md` R1 |
| 2 | R1 Model Engine | Model Preprocessor & KV Cache | Image/text input formatter, INT8/INT4 quantizer, and KV cache manager. | Raw image bytes/PIL image, raw prompt text | Formatted tensors, cached KV states, quantized metadata | Invalid image formats raise `ValueError` | `PROJECT.md` § Feature 2 |
| 3 | R1 Gateway | Gateway Protocol & Schemas | Unified Pydantic data contracts (`GatewayRequest`, `GatewayResponse`). | Request parameters (`prompt`, `images`, `temperature`, `max_tokens`, `model_name`) | Validated `GatewayRequest` / `GatewayResponse` instances | Schema validation error raises `ValidationError` | `PROJECT.md` § Feature 3 & Interface Contracts |
| 4 | R1 Gateway | External API Adapters | Unified API adapters for OpenAI, Anthropic Claude, Gemini, and Ollama. | `GatewayRequest` | `GatewayResponse` | API auth errors, 429 rate limits, timeout errors trigger fallback | `PROJECT.md` § Feature 4, `ORIGINAL_REQUEST.md` R1 |
| 5 | R1 Gateway | Local & Mock Adapters | Local ONNX engine adapter (`LocalONNXAdapter`) and offline testing `MockAdapter`. | `GatewayRequest` | `GatewayResponse` | Invalid model path raises `FileNotFoundError` or `EngineError` | `PROJECT.md` § Feature 5 & Interface Contracts |
| 6 | R1 Gateway | Cascading Router | Priority decision router with provider ordering and automated fallback. | `GatewayRequest`, provider priority list | `GatewayResponse` from highest priority operational provider | All providers failing raises `GatewayRoutingError` | `PROJECT.md` § Feature 6, `ORIGINAL_REQUEST.md` R1 |
| 7 | R2 OS Drivers | Unified OSDriver Interface | Abstract `BaseOSDriver` contract defining 8 action primitives. | Action type (`click`, `type`, etc.), action parameters dict | `ActionResult` (`success`, `execution_time_ms`, `error_message`, `screen_state`) | Invalid action parameters raise `InvalidActionError` | `PROJECT.md` § Feature 7 & Interface Contracts |
| 8 | R2 OS Drivers | Desktop OS Drivers | Linux (Xvfb/xdotool), Windows (pywinauto/PowerShell), macOS (CoreGraphics). | Action type, action parameters | `ActionResult` | Missing system display/tools raises `DriverInitializationError` | `PROJECT.md` § Feature 8, `ORIGINAL_REQUEST.md` R2 |
| 9 | R2 OS Drivers | Mobile OS Drivers | Android (ADB/uiautomator daemon) and iOS (simctl/remote daemon). | Mobile action parameters | `ActionResult` | Device disconnection raises `DeviceConnectionError` | `PROJECT.md` § Feature 9, `ORIGINAL_REQUEST.md` R2 |
| 10 | R2 OS Drivers | Error Retry & Backoff | Exponential retry backoff decorator with random jitter and daemon reconnect. | Driver function call, `max_retries`, `base_delay`, `max_delay` | Function execution output or exception | Exceeding max retries raises wrapped driver exception | `PROJECT.md` § Feature 10, `ORIGINAL_REQUEST.md` R2 |
| 11 | R3 Visual Grounding | Screen Processing Pipeline | Screenshot downscaling, sub-region tiling, and color space conversion (RGB/Grayscale). | Raw `PIL.Image` screenshot, target resolution/mode | Processed `PIL.Image` or numpy array | Invalid image size raises `ImageProcessingError` | `PROJECT.md` § Feature 11, `ORIGINAL_REQUEST.md` R3 |
| 12 | R3 Visual Grounding | Sliding Trajectory Memory | Bounded 3-screenshot sliding memory buffer + text action log history. | `PIL.Image` screenshot, string action description | `MemoryState` object (3 screenshots + full text log) | Empty screenshot input raises `ValueError` | `PROJECT.md` § Feature 12 & Interface Contracts |
| 13 | R3 Visual Grounding | Set-of-Marks (SoM) Generator | Interactive UI element bounding box annotator & bidirectional `MarkMap` lookup. | Raw `PIL.Image` screenshot | Tuple (`annotated_image`, `MarkMap`) | Unreadable UI element bounding box defaults to fallback box | `PROJECT.md` § Feature 13 & Interface Contracts |
| 14 | R4 Benchmark Engine | Task Execution Runner | Standardized JSON task schema (`TaskSchema`) and `BenchmarkRunner` event loop. | Task schema definition, driver instance, gateway instance | `BenchmarkResult` (status, trajectory, evaluation summary) | Task execution timeout raises `TaskTimeoutError` | `PROJECT.md` § Feature 14, `ORIGINAL_REQUEST.md` R4 |
| 15 | R4 Benchmark Engine | Benchmark Adapters | Dataset adapters for OSWorld, WebArena, AndroidWorld, Mind2Web, GAIA, OmniBench. | Raw dataset files/configs | Normalized `TaskSchema` objects | Corrupt task dataset files raise `DatasetAdapterError` | `PROJECT.md` § Feature 15, `ORIGINAL_REQUEST.md` R4 |
| 16 | R4 Benchmark Engine | Dual Evaluator Engine | Visual state diffing (SSIM/pHash/ROI/OCR) + system CLI/API state assertions. | Initial state dict, final state dict, trajectory step list | `EvaluationResult` (`passed`, `score`, `visual_diff_score`, `system_assertion_passed`) | Missing state keys raise `EvaluationError` | `PROJECT.md` § Feature 16 & Interface Contracts |
| 17 | R4 Benchmark Engine | Self-Correction Handlers | Automated L1/L2 retries and visual stagnation prompt injection. | Failed step, visual diff metric, retry level | Corrective prompt injection / retry instruction | Max retries exceeded marks step/task failed | `PROJECT.md` § Feature 17, `ORIGINAL_REQUEST.md` R4 |
| 18 | R5 Telemetry & Interface | `omnibench` CLI | Python CLI (`config`, `dataset`, `run`, `monitor`, `db`, `dashboard`). | CLI arguments, command strings | Console log output, status tables, exit code 0/1 | Invalid CLI command displays usage text and exits with status 1 | `PROJECT.md` § Feature 18, `ORIGINAL_REQUEST.md` R5 |
| 19 | R5 Telemetry & Interface | SQLite Telemetry & DDL | Database schema (`runs`, `episodes`, `steps`, `screenshot_diffs`) and logging API. | Run metadata, step payload, screenshots | Database records in SQLite DB file (`omnibench.db`) | Database lock or I/O error triggers retry or raises `DatabaseError` | `PROJECT.md` § Feature 19, `ORIGINAL_REQUEST.md` R5 |
| 20 | R5 Telemetry & Interface | Screenshot Diff Analytics | MSE, SSIM, pixel diff percentage calculation, and diff mask generator. | Image A (before), Image B (after) | Metrics dict (`mse`, `ssim`, `pixel_diff_pct`) and overlay mask image | Mismatched image dimensions raise `DimensionMismatchError` | `PROJECT.md` § Feature 20, `ORIGINAL_REQUEST.md` R5 |
| 21 | R5 Telemetry & Interface | Web Dashboard UI | Python HTTP/SSE live telemetry backend and responsive SPA frontend. | HTTP requests, SSE client connection | Rendered HTML dashboard UI, JSON state, SSE event streams | Missing static assets or port bind error raises `ServerError` | `PROJECT.md` § Feature 21, `ORIGINAL_REQUEST.md` R5 |
| 22 | Acceptance Criteria | E2E Integration & Verification | 100% test suite pass rate across Tier 1-4 (≥237 tests) + Tier 5 adversarial hardening. | Pytest test execution suite | Full test pass report & zero unexpected failures | Failed test case reports assertion details | `PROJECT.md` § Feature 22, `TEST_INFRA.md` |

## Edge Cases
| # | Feature | Input | Observed / Expected Behavior |
|---|---------|-------|------------------------------|
| 1 | ONNX 100M Local Engine | CPU RAM allocation during high-resolution screenshot processing | Image preprocessor resizes image down to model max resolution; INT8/INT4 engine stays strictly under 1.1 GiB RAM cap without crashing. |
| 2 | Cascading Decision Router | Primary provider (OpenAI) returns HTTP 429 Rate Limit error | Router catches HTTP 429 exception, logs warning, and seamlessly cascades to Anthropic -> Gemini -> Ollama -> Local ONNX -> Mock. |
| 3 | BaseOSDriver Action Primitives | Click coordinates `(x, y)` exceeding current display resolution bounds | Driver validates display bounds prior to invocation and raises `InvalidCoordinateError` or safely clamps coordinates to active screen edges. |
| 4 | Mobile OS Drivers (Android ADB) | ADB daemon drops RPC connection during active task step | Exponential retry backoff decorator catches connection error, attempts ADB daemon reconnection up to max retries with jittered delay. |
| 5 | Sliding Trajectory Memory | 4th screenshot frame added to trajectory memory | FIFO memory manager drops 1st (oldest) screenshot, keeping exactly 3 recent screenshots while retaining complete text action log history. |
| 6 | Set-of-Marks (SoM) Generator | Blank / solid color screen with zero detectable UI bounding boxes | Generator returns unmodified original image and an empty `MarkMap` without failing or raising exceptions. |
| 7 | Dual Evaluator Engine | Visual diff score passes threshold but system assertion returns False | Dual evaluator marks overall result as `passed = False`, reporting `visual_diff_score` and `system_assertion_passed = False` independently in `EvaluationResult`. |
| 8 | Self-Correction Handlers | Agent executes click action, but subsequent screenshot diff is 0.0% (stagnation) | Stagnation handler detects zero state delta, increments retry level, and injects visual stagnation notice into model context prompt. |
| 9 | `omnibench` CLI | Invalid CLI subcommand or non-existent benchmark dataset path | CLI prints user-friendly error to stderr, displays help usage documentation, and exits cleanly with non-zero exit code (1). |
| 10 | SQLite Telemetry & DDL | Concurrent write attempts from multiple parallel worker processes | `TelemetryLogger` initializes SQLite in WAL (Write-Ahead Logging) mode with busy timeout handling to prevent database locking errors. |
| 11 | Web Dashboard UI | SSE connection interrupted by client browser tab navigation or reload | Server cleanly releases SSE stream handler; frontend SPA automatically reconnects upon page reload without throwing unhandled exceptions. |

## Interface Contracts

### 1. Model Gateway & Engine Contract (`omnibench.gateway` ↔ `omnibench.engine`)
- **`GatewayRequest`**:
  ```python
  class GatewayRequest(BaseModel):
      prompt: str
      images: list[bytes] = []
      temperature: float = 0.7
      max_tokens: int = 512
      model_name: str = "onnx-100m"
  ```
- **`GatewayResponse`**:
  ```python
  class GatewayResponse(BaseModel):
      text: str
      action_json: dict
      usage_tokens: int
      latency_ms: float
      provider_used: str
  ```
- **Adapter Signature**:
  `LocalONNXAdapter.generate(req: GatewayRequest) -> GatewayResponse`

### 2. OS Automation Driver Contract (`omnibench.drivers` ↔ `BenchmarkRunner`)
- **`BaseOSDriver` Signature**:
  `BaseOSDriver.execute_action(action_type: str, params: dict) -> ActionResult`
  `BaseOSDriver.capture_screenshot() -> PIL.Image.Image`
- **Supported Action Primitives**:
  - `click`: `{"x": int, "y": int}`
  - `double_click`: `{"x": int, "y": int}`
  - `right_click`: `{"x": int, "y": int}`
  - `drag`: `{"start_x": int, "start_y": int, "end_x": int, "end_y": int}`
  - `type`: `{"text": str}`
  - `key_combination`: `{"keys": list[str]}`
  - `scroll`: `{"direction": "up"|"down"|"left"|"right", "amount": int}`
  - `wait`: `{"seconds": float}`

### 3. Visual & SoM Processing Contract (`omnibench.visual` ↔ `BenchmarkRunner` & Model Gateway)
- **SoM Annotator**:
  `SoMAnnotator.annotate(screenshot: Image) -> tuple[Image, MarkMap]`
- **MarkMap Coordinates Lookup**:
  `MarkMap.get_coordinates(mark_id: int) -> tuple[int, int]`
- **Sliding Memory**:
  `SlidingTrajectoryMemory.add_step(screenshot: Image, action_str: str) -> MemoryState`

### 4. Dual Evaluator Engine Contract (`omnibench.evaluators` ↔ `BenchmarkRunner`)
- **DualEvaluator Signature**:
  `DualEvaluator.evaluate(initial_state: dict, final_state: dict, trajectory: list) -> EvaluationResult`
- **`EvaluationResult` Schema**:
  ```python
  class EvaluationResult(BaseModel):
      passed: bool
      score: float
      visual_diff_score: float
      system_assertion_passed: bool
      details: dict
  ```

### 5. Telemetry & Database Schema Contract (`omnibench.telemetry`)
- **Tables**: `runs`, `episodes`, `steps`, `screenshot_diffs`
- **SQLite DDL Requirements**:
  - `runs`: `run_id TEXT PRIMARY KEY, benchmark_name TEXT, start_time TIMESTAMP, end_time TIMESTAMP, total_tasks INT, status TEXT`
  - `episodes`: `episode_id TEXT PRIMARY KEY, run_id TEXT, task_id TEXT, passed BOOLEAN, score REAL, visual_diff_score REAL`
  - `steps`: `step_id TEXT PRIMARY KEY, episode_id TEXT, step_num INT, action_type TEXT, action_params TEXT, latency_ms REAL`
  - `screenshot_diffs`: `diff_id TEXT PRIMARY KEY, step_id TEXT, mse REAL, ssim REAL, pixel_diff_pct REAL, mask_path TEXT`

## Acceptance Criteria Mapping

| Acceptance Criterion | Project Requirement | Pillar / Modules | Target Verification Method |
|----------------------|---------------------|------------------|----------------------------|
| ONNX Runtime 100M model engine successfully loads and executes inference on CPU maintaining system memory consumption under 1.1 GiB RAM. | R1 | `omnibench.engine` (`onnx_engine.py`, `quantizer.py`) | Tier 1/2 unit test asserting process memory RSS <1.1 GiB during model load & inference. |
| Universal Model Gateway cleanly routes requests between external APIs and local fallback model. | R1 | `omnibench.gateway` (`protocol.py`, `adapters.py`, `router.py`) | Integration tests simulating provider error/rate limit and asserting fallback routing sequence. |
| OS Drivers execute action primitives on host platform with automated error backoff and retries. | R2 | `omnibench.drivers` (`base.py`, `linux.py`, `windows.py`, `macos.py`, `android.py`, `ios.py`, `retry.py`) | Driver unit and integration tests executing all 8 primitives with simulated failures and retry verification. |
| Benchmarks evaluate state correctness via dual visual & system state assertions and output detailed SQLite results. | R4, R5 | `omnibench.evaluators`, `omnibench.benchmarks`, `omnibench.telemetry` | End-to-end evaluation runner test verifying SQLite database record insertion and dual evaluator scores. |
| Web Dashboard and CLI launch and display live run progress and analytics without errors. | R5 | `omnibench.cli`, `omnibench.dashboard`, `omnibench.telemetry` | CLI execution tests (`omnibench run`, `omnibench dashboard`) and HTTP/SSE endpoint responsiveness tests. |

## Caveats
- No code modifications or source files were written during this phase (specification mining only).
- Live execution testing of external LLM API adapters (OpenAI, Anthropic, Gemini) requires environment API keys; offline mock adapters (`MockAdapter`) will validate protocol compliance in automated testing.
- Platform specific driver testing requires appropriate host environment configuration (e.g. Xvfb for Linux headless GUI execution, ADB daemon for Android, simctl for iOS).

## Conclusion
The specification mining process has comprehensively enumerated all requirements, features (22 total), edge cases (11 total), interface contracts (5 total), and acceptance criteria mappings for OmniBench 1.0. All pillars (R1 through R5) are fully documented and structured for implementation and test suite construction.

## Verification Method
1. Inspect handoff report at `/home/oh_my_macos27/OmniBench Computer Use/.agents/teamwork_preview_spec_miner_survey_1/handoff.md`.
2. Cross-reference `Features Discovered` (22 items) against `PROJECT.md` Feature Inventory and `ORIGINAL_REQUEST.md` Requirements R1-R5.
3. Validate presence of mandatory tables (`Features Discovered`, `Edge Cases`), 5 Interface Contracts, and 5 Acceptance Criteria Mappings.
