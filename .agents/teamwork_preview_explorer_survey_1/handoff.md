# Handoff Report: Codebase Survey & Repository Analysis

**Agent**: `teamwork_preview_explorer_survey_1`  
**Working Directory**: `/home/oh_my_macos27/OmniBench Computer Use/.agents/teamwork_preview_explorer_survey_1`  
**Date**: 2026-08-08  

---

## 1. Observation

### 1.1 Existing Codebase Layout & Root Files
A search of `/home/oh_my_macos27/OmniBench Computer Use/` using filesystem discovery commands (`find . -maxdepth 4 -not -path '*/.*'`) directly observed:
```
/home/oh_my_macos27/OmniBench Computer Use/
├── ORIGINAL_REQUEST.md (Original user & system requirements)
├── PROJECT.md (System architecture, feature inventory, milestone plan, interface contracts, target layout)
├── TEST_INFRA.md (E2E testing methodology, tier breakdown, coverage targets)
├── .venv/ (Python 3.13 virtual environment)
└── .agents/ (Agent metadata and workspace directories)
```
No Python source directory (`omnibench/`), test directory (`tests/`), build file (`pyproject.toml` / `setup.py`), or configuration file currently exists in the root workspace.

### 1.2 System Dependencies & Environment Details
Execution of diagnostic commands in the host environment revealed:
- **Operating System**: `Debian GNU/Linux 13 (trixie)`, Kernel `6.6.141-09476-g954adab60416 x86_64`
- **CPU**: 4-core `Intel(R) Celeron(R) N4120 CPU @ 1.10GHz`
- **Host Memory**: Total `2.7 GiB`, Used `1.9 GiB`, Available `~850 MiB`
- **Python Environment**: `/home/oh_my_macos27/OmniBench Computer Use/.venv/bin/python` (Python 3.13.5)
- **Installed Packages in `.venv`**:
  - `onnxruntime` v1.28.0 (Model execution engine)
  - `pillow` v12.3.0 (Image processing / screenshot handling)
  - `numpy` v2.5.1 (Array & numerical calculations)
  - `pydantic` v2.13.4 & `pydantic_core` v2.46.4 (Data validation & gateway schema contracts)
  - `httpx` v0.28.1 & `httpcore` v1.0.9 (HTTP/SSE client for gateway API adapters)
  - `psutil` v7.2.2 (System memory telemetry monitoring)
  - `protobuf` v7.35.1, `flatbuffers` v25.12.19
- **System Binary Tools**:
  - Available: `/usr/bin/Xvfb`, `/usr/bin/ffmpeg`
  - Missing from PATH: `xdotool`, `adb`, `simctl`, `tesseract`, `sqlite3` CLI (note: Python standard library `sqlite3` is available), `pytest`.

### 1.3 Target Architecture & Component Inventory (from `PROJECT.md`)
`PROJECT.md` specifies five core system pillars and 22 feature items:
1. **Engine & Gateway (`omnibench.engine`, `omnibench.gateway`)**:
   - 100M parameter ONNX Runtime VLM engine (INT8/INT4 CPU optimized <1.1 GiB RAM).
   - Universal Model Gateway adapter protocol (`GatewayRequest`/`GatewayResponse`) with cascading fallback router across OpenAI, Anthropic, Gemini, Ollama, and local ONNX model.
2. **OS Automation Drivers (`omnibench.drivers`)**:
   - `BaseOSDriver` abstract contract defining 8 action primitives (`click`, `double_click`, `right_click`, `drag`, `type`, `key_combination`, `scroll`, `wait`) and `capture_screenshot()`.
   - Driver implementations for Linux (Xvfb/xdotool), Windows (pywinauto/PowerShell), macOS (CoreGraphics), Android (ADB/uiautomator daemon), iOS (simctl/daemon).
   - Exponential jittered retry backoff decorator.
3. **Visual Grounding & Set-of-Marks (`omnibench.visual`)**:
   - Screen processing pipeline (resizing, tiling, RGB/grayscale).
   - Set-of-Marks (SoM) bounding box generator and `MarkMap` lookup.
   - Sliding Trajectory Memory (bounded 3-screenshot memory buffer + action logs).
4. **Benchmark Evaluation (`omnibench.evaluators`, `omnibench.benchmarks`)**:
   - Task execution runner & JSON task schema.
   - Adapters for OSWorld, WebArena, AndroidWorld, Mind2Web, GAIA, and OmniBench native.
   - Dual evaluator engine (SSIM/pHash visual state diffing + CLI/API system state assertions).
   - Level 1/2 self-correction & visual stagnation feedback injector.
5. **Telemetry & Dashboard (`omnibench.telemetry`, `omnibench.cli`, `omnibench.dashboard`)**:
   - SQLite schema (`runs`, `episodes`, `steps`, `screenshot_diffs`) & logger.
   - Screenshot diff analytics engine (MSE, SSIM, difference mask).
   - `omnibench` CLI (`config`, `dataset`, `run`, `monitor`, `db`, `dashboard`).
   - Responsive SPA Web Dashboard + HTTP/SSE live telemetry server.

---

## 2. Logic Chain

- **Step 1 (Greenfield Baseline)**: Observation 1.1 confirms that the repository root currently contains zero Python source code or test files. All architectural requirements, schemas, and milestones are documented in `ORIGINAL_REQUEST.md`, `PROJECT.md`, and `TEST_INFRA.md`.
- **Step 2 (Dependency Readiness)**: Observation 1.2 confirms that `.venv` already contains the critical Python dependencies (`onnxruntime`, `pillow`, `pydantic`, `httpx`, `psutil`, `numpy`). Therefore, initial module creation for M1, M2, M3, M4, M5 can proceed without needing third-party C/C++ extensions or unavailable Python libraries.
- **Step 3 (Hardware & Platform Fallback)**: Observation 1.2 shows that the host environment has 2.7 GiB total RAM (~850 MiB free) and lacks physical Windows/macOS/mobile attached hardware. Therefore:
  - The ONNX VLM engine must strictly maintain lightweight INT8/INT4 CPU memory usage under 1.1 GiB (or provide a lightweight dummy model fallback during unit testing).
  - OS drivers for Windows, macOS, Android, and iOS must include synthetic/mock execution fallbacks when native platform APIs or daemons are unavailable on Linux.
- **Step 4 (Modular Interface Boundaries)**: Observation 1.3 details explicit interface contracts (`GatewayRequest`/`GatewayResponse`, `BaseOSDriver`, `MarkMap`, `DualEvaluator`, `EvaluationResult`). These strict contracts enable parallel development of components without cross-module tight coupling.

---

## 3. Caveats

1. **Non-Linux Driver Testing**: The test execution environment is Linux. Android (ADB), iOS (simctl), Windows (pywinauto), and macOS (CoreGraphics) drivers cannot be executed against real OS targets in this environment. They must be validated via mock drivers, unit tests, and structural validation.
2. **Missing `pytest` in `.venv`**: `pytest` is not installed in `.venv`. Test runners will either need `pytest` added to the venv or use Python's built-in `unittest` runner / standalone custom runner script.
3. **RAM Limits**: Host free RAM is ~850 MiB. Care must be taken during ONNX model loading and image processing to prevent OOM errors.

---

## 4. Conclusion & Recommendations

### 4.1 Summary
The OmniBench 1.0 repository is fully specified and ready for implementation. Key dependencies are pre-installed in `.venv`.

### 4.2 Architectural Decomposition Plan
We recommend decomposing development into five modular packages following `PROJECT.md`:

```
omnibench/
├── __init__.py
├── engine/             # M1: ONNX VLM Engine (onnx_engine.py, preprocessor.py, quantizer.py, dummy_model.py)
├── gateway/            # M1: Universal Gateway (protocol.py, adapters.py, router.py)
├── drivers/            # M2: OS Drivers (base.py, linux.py, windows.py, macos.py, android.py, ios.py, retry.py)
├── visual/             # M3: Visual Grounding & SoM (processing.py, som.py, memory.py)
├── evaluators/         # M4: Dual Evaluators & Self-Correction (visual_diff.py, system_assertions.py, dual_evaluator.py, self_correction.py)
├── benchmarks/         # M4: Benchmark Runner & Adapters (runner.py, task_schema.py, adapters/*)
├── telemetry/          # M5: SQLite DDL & Analytics (db.py, logger.py, analytics.py)
├── cli/                # M5: CLI commands (main.py)
└── dashboard/          # M5: Telemetry Web Server & SPA (server.py, static/index.html)
```

---

## 5. Verification Method

To independently verify the findings in this report:

1. **Inspect Workspace Files**:
   ```bash
   find /home/oh_my_macos27/OmniBench\ Computer\ Use/ -maxdepth 2 -not -path '*/.*'
   ```
   *Expected Output*: Only `ORIGINAL_REQUEST.md`, `PROJECT.md`, `TEST_INFRA.md`, `.venv`, `.agents`.

2. **Verify Python Environment & Core Packages**:
   ```bash
   /home/oh_my_macos27/OmniBench\ Computer\ Use/.venv/bin/python -c "import onnxruntime, PIL, pydantic, httpx, psutil, numpy; print('Environment verified successfully')"
   ```
   *Expected Output*: `Environment verified successfully`.

3. **Verify Host Memory & OS Details**:
   ```bash
   free -h && uname -a
   ```
