# Original User Request

## 2026-08-08T11:14:39Z

OmniBench 1.0 is a universal computer use model and benchmark framework integrating cross-platform system execution drivers (Windows 10+, macOS 11+, Linux 2020+, Android 10+, iOS 14+) with a hybrid local 100M-parameter vision-language model engine (ONNX INT8/INT4 optimized for ~1.1 GiB RAM usage) and a Universal Model Gateway (OpenAI, Anthropic Claude, Gemini, local Ollama).

Working directory: /home/oh_my_macos27/OmniBench Computer Use
Integrity mode: benchmark

## Requirements

### R1. 100M Parameter ONNX Local Model Engine & Universal Model Gateway
Engine capable of running a 100M parameter vision-language model optimized with ONNX Runtime INT8/INT4 under ~1.1 GiB host RAM on CPU without GPU, alongside a Unified Gateway adapter protocol for external frontier LLM APIs (OpenAI, Anthropic, Gemini, Ollama) and cascading decision routing.

### R2. Cross-Platform Operating System Automation Drivers
Modular automation drivers supporting full computer use action primitives (click, double click, right click, drag, type, key combinations, scroll, wait) across Windows 10+, macOS 11+, Linux 2020+, Android 10+ (via ADB/uiautomator daemon), and iOS 14+ (via remote daemon / simctl).

### R3. Visual Grounding & Set-of-Marks (SoM) Preprocessor
Visual processing engine providing screen capture optimization (resizing/tiling, RGB/grayscale), sliding trajectory memory (3 screenshots + text action logs), and a Set-of-Marks (SoM) interactive UI element bounding box generator for precise target grounding.

### R4. Benchmark Evaluation & Verification Engine
Evaluation runner for OSWorld, WebArena, AndroidWorld, Mind2Web, GAIA, and native OmniBench benchmark tasks using dual evaluators (visual state diffing + system CLI/API state assertions) with automatic self-correction & retry handlers.

### R5. Interface & Telemetry Dashboard
Rich Python CLI (`omnibench`) and Web Dashboard UI for benchmark configuration, dataset selection, live trajectory monitoring, and SQLite database logging with screenshot diff analytics.

## Acceptance Criteria

### Execution & Engine Validity
- [ ] ONNX Runtime 100M model engine successfully loads and executes inference on CPU maintaining system memory consumption under 1.1 GiB RAM.
- [ ] Universal Model Gateway cleanly routes requests between external APIs and local fallback model.
- [ ] OS Drivers execute action primitives on host platform with automated error backoff and retries.
- [ ] Benchmarks evaluate state correctness via dual visual & system state assertions and output detailed SQLite results.
- [ ] Web Dashboard and CLI launch and display live run progress and analytics without errors.
