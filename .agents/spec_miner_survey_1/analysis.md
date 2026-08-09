# Specification Mining Analysis Report: Requirement R4 (Benchmark Evaluation & Verification Engine)

**Agent ID**: `spec_miner_survey_1`  
**Date**: 2026-08-08  
**Scope**: Requirement R4 — Benchmark Evaluation & Verification Engine for OmniBench 1.0  
**Target File**: `/home/oh_my_macos27/OmniBench Computer Use/.agents/spec_miner_survey_1/analysis.md`

---

## 1. Executive Summary & Specification Scope

The **Benchmark Evaluation & Verification Engine** (Requirement R4) provides an automated, extensible, and high-fidelity evaluation framework for assessing computer use agent performance across 6 benchmark benchmark suites: **OSWorld**, **WebArena**, **AndroidWorld**, **Mind2Web**, **GAIA**, and native **OmniBench** composite tasks.

The core architecture combines:
1. **Universal Task Representation Schema**: A unified JSON/YAML format supporting cross-platform operating systems (Linux, Windows, macOS, Android, iOS) and web environments.
2. **Dual Evaluators Engine**: Integrating **Visual State Diffing** (SSIM, pHash, ROI masking, OCR diff) with **System CLI/API State Assertions** (shell outputs, HTTP responses, file SHA-256 hashes, DOM selectors, SQLite queries).
3. **Automatic Self-Correction & Retry Handlers**: Multi-tiered retry policies with exponential backoff for transient UI glitches and visual feedback feedback loops for self-correction.
4. **Task Execution Runner (`BenchmarkRunner`)**: Asynchronous execution lifecycle manager with state isolation, screenshot trajectory logging, and SQLite database persistence.
5. **Tiered Test Suite Architecture (Tiers 1–4)**: Validating component logic, driver mocks, benchmark task samples, and full end-to-end evaluation runs.

---

## 2. Benchmark Families & Task Taxonomy

OmniBench 1.0 standardizes evaluation across six distinct computer use benchmark families:

### 2.1 OSWorld (Desktop Operating Systems)
- **Target OS**: Linux (Ubuntu 22.04+), Windows 10/11, macOS 11+
- **Task Domains**: File management, system settings, desktop applications (VSCode, LibreOffice Calc/Writer, GIMP, Thunderbird, VLC, Terminal).
- **State Evaluation Characteristics**: Filesystem state, application config files, process status, visual screenshot diff of target application state.

### 2.2 WebArena (Web Browser & E-Commerce / Enterprise Tools)
- **Target OS / Environment**: Chromium/Firefox browser connected to mock web services (Shopping/e-commerce, GitLab, Redmine, Postmill/Reddit, OpenStreetMap, Wikipedia).
- **Task Domains**: Multi-page navigation, form submission, data retrieval, e-commerce checkout, issue tracking.
- **State Evaluation Characteristics**: Web DOM assertions (`querySelectorAll`, text content, input values), HTTP REST API queries, database state verification, browser visual screenshot diff.

### 2.3 AndroidWorld (Mobile OS & Applications)
- **Target OS**: Android 10+ (via ADB and `uiautomator` daemon)
- **Task Domains**: System settings (WiFi, Display, Sound), Contacts, Messages, Clock/Alarms, File Manager, third-party apps (Calculator, Media Players).
- **State Evaluation Characteristics**: ADB shell outputs (`dumpsys`, `content query`), UI Automator accessibility tree XML hierarchy, screenshot visual diffing.

### 2.4 Mind2Web (Complex Web Trajectories & DOM Grounding)
- **Target OS / Environment**: Web browser automation engine.
- **Task Domains**: Multi-step web workflows across 31 domains (travel, shopping, entertainment, finance).
- **State Evaluation Characteristics**: Step-level element selection accuracy, action type precision, final state URL and DOM tree validation.

### 2.5 GAIA (General AI Assistant Benchmark)
- **Target OS / Environment**: Cross-platform desktop/web environment with multimodal inputs (audio, video, PDF, Excel, Python code execution).
- **Task Domains**: Complex multi-modal reasoning, file analysis, web search synthesis, data extraction, script execution.
- **State Evaluation Characteristics**: System stdout/file content matching, exact text/numerical output comparison, regex assertion, multi-file artifact integrity.

### 2.6 OmniBench Native (Composite & Cross-Platform Tasks)
- **Target OS**: Cross-platform (Desktop + Web + Mobile synchronized tasks).
- **Task Domains**: End-to-end enterprise workflows (e.g. extract data from mobile app -> process in desktop spreadsheet -> upload via web app -> verify database record).
- **State Evaluation Characteristics**: Full dual evaluator protocol (Visual SSIM/ROI + CLI/API assertions + SQLite integrity check).

---

## 3. Universal Benchmark Dataset Schema & Task Format

All benchmark tasks, whether native or imported from OSWorld/WebArena/AndroidWorld/Mind2Web/GAIA, are serialized into a standardized **OmniBench Task Definition** format (`.json` or `.yaml`).

### 3.1 JSON Schema Specification (`task_schema.json`)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "OmniBenchTaskDefinition",
  "type": "object",
  "required": [
    "task_id",
    "benchmark_family",
    "name",
    "instruction",
    "tier",
    "evaluator_config"
  ],
  "properties": {
    "task_id": { "type": "string", "pattern": "^[a-z0-9_\\-]+$" },
    "benchmark_family": {
      "type": "string",
      "enum": ["osworld", "webarena", "androidworld", "mind2web", "gaia", "omnibench_native"]
    },
    "name": { "type": "string" },
    "category": { "type": "string" },
    "instruction": { "type": "string" },
    "tier": { "type": "integer", "minimum": 1, "maximum": 4 },
    "timeout_seconds": { "type": "integer", "default": 300 },
    "max_steps": { "type": "integer", "default": 30 },
    "initial_state": {
      "type": "object",
      "properties": {
        "setup_script": { "type": "string" },
        "url": { "type": "string" },
        "app_package": { "type": "string" },
        "files_to_copy": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "source": { "type": "string" },
              "destination": { "type": "string" }
            }
          }
        }
      }
    },
    "evaluator_config": {
      "type": "object",
      "required": ["mode", "evaluators"],
      "properties": {
        "mode": {
          "type": "string",
          "enum": ["AND", "OR", "WEIGHTED", "FALLBACK"]
        },
        "pass_threshold": { "type": "number", "default": 1.0 },
        "evaluators": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["type"],
            "properties": {
              "type": { "type": "string", "enum": ["visual_diff", "system_assertion"] },
              "weight": { "type": "number", "default": 1.0 },
              "visual_params": {
                "type": "object",
                "properties": {
                  "baseline_image": { "type": "string" },
                  "ssim_threshold": { "type": "number", "default": 0.95 },
                  "roi_bbox": {
                    "type": "array",
                    "items": { "type": "integer" },
                    "minItems": 4,
                    "maxItems": 4
                  },
                  "phash_max_distance": { "type": "integer", "default": 5 },
                  "ocr_required_text": { "type": "array", "items": { "type": "string" } }
                }
              },
              "assertion_params": {
                "type": "object",
                "properties": {
                  "command": { "type": "string" },
                  "expected_stdout": { "type": "string" },
                  "stdout_regex": { "type": "string" },
                  "expected_exit_code": { "type": "integer", "default": 0 },
                  "http_request": {
                    "type": "object",
                    "properties": {
                      "url": { "type": "string" },
                      "method": { "type": "string", "default": "GET" },
                      "expected_status": { "type": "integer", "default": 200 },
                      "json_path_assertions": {
                        "type": "array",
                        "items": {
                          "type": "object",
                          "properties": {
                            "path": { "type": "string" },
                            "expected_value": {}
                          }
                        }
                      }
                    }
                  },
                  "file_assertion": {
                    "type": "object",
                    "properties": {
                      "path": { "type": "string" },
                      "sha256": { "type": "string" },
                      "contains_string": { "type": "string" }
                    }
                  }
                }
              }
            }
          }
        }
      }
    },
    "teardown_script": { "type": "string" }
  }
}
```

---

## 4. Dual Evaluators Architecture & Contracts

The evaluation engine leverages two independent verification axes to prevent evaluation false positives or bypasses:
1. **Visual State Diffing Engine**
2. **System CLI/API Assertion Engine**

```
                       +-----------------------------------+
                       |    Task Final Execution State     |
                       +-----------------+-----------------+
                                         |
                    +--------------------+--------------------+
                    |                                         |
        +-----------v-----------+                 +-----------v-----------+
        |   Visual State Diff   |                 | System State Assert   |
        |        Engine         |                 |        Engine         |
        +-----------+-----------+                 +-----------+-----------+
                    |                                         |
     (SSIM, pHash, ROI, OCR)                      (CLI, HTTP, File, DOM)
                    |                                         |
                    +--------------------+--------------------+
                                         |
                       +-----------------v-----------------+
                       | Dual Evaluation Aggregation Engine|
                       |  (AND / OR / WEIGHTED / FALLBACK) |
                       +-----------------+-----------------+
                                         |
                       +-----------------v-----------------+
                       |  Result: Passed/Failed + Score    |
                       +-----------------------------------+
```

### 4.1 Visual State Diffing Engine Specification

The visual evaluator compares the current screenshot ($I_{curr}$) against reference baseline screenshots ($I_{base}$) or specified visual criteria.

#### Algorithmic Metrics:

1. **Structural Similarity Index (SSIM)**:
   $$\text{SSIM}(x, y) = \frac{(2\mu_x\mu_y + C_1)(2\sigma_{xy} + C_2)}{(\mu_x^2 + \mu_y^2 + C_1)(\sigma_x^2 + \sigma_y^2 + C_2)}$$
   - Threshold: Pass if $\text{SSIM}(I_{curr}[ROI], I_{base}[ROI]) \ge 0.95$.

2. **Perceptual Hashing (pHash)**:
   - Calculate 64-bit DCT pHash for candidate and baseline image.
   - Threshold: Pass if Hamming Distance $D_H(\text{pHash}_{curr}, \text{pHash}_{base}) \le 5$.

3. **ROI (Region of Interest) Masking**:
   - Crop bounding box $[x_1, y_1, x_2, y_2]$ to ignore irrelevant dynamic regions (e.g. system clock, cursor blinking, dynamic advertisements).

4. **OCR Text Extraction Verification**:
   - Run Tesseract / EasyOCR on target ROI to verify presence of expected string tokens (e.g., success message, specific computed total).

### 4.2 System CLI / API State Assertion Engine Specification

System state verification executes low-level programmatic probes on the operating system, web service, or mobile device:

1. **CLI Commands**:
   - Linux/macOS: `bash -c "<cmd>"`
   - Windows: `powershell.exe -Command "<cmd>"`
   - Android: `adb shell "<cmd>"`
   - Assertion checks exit code, stdout exact match, or regex pattern match.

2. **HTTP API Assertions**:
   - Query REST/GraphQL endpoints on local/remote mock services (e.g., WebArena GitLab/Redmine API).
   - Validate JSON response properties using JSONPath expressions (e.g., `$.issue.status == "closed"`).

3. **Filesystem Integrity Assertions**:
   - File existence check (`os.path.exists`).
   - File SHA-256 hash comparison.
   - Text file line/content substring matching.

4. **Web Browser DOM Assertions**:
   - Execute JavaScript evaluation snippet via Selenium/Playwright connection.
   - Inspect element attribute values, text content, CSS properties, or selection states.

### 4.3 Dual Evaluation Aggregation Protocol

The `DualEvaluator` aggregates sub-evaluator results according to the defined `mode`:

- **`AND` Mode**: `final_pass = all(eval.passed for eval in evaluators)`
- **`OR` Mode**: `final_pass = any(eval.passed for eval in evaluators)`
- **`WEIGHTED` Mode**:
  $$\text{Score} = \sum_{i=1}^N (w_i \times s_i), \quad \text{final\_pass} = \text{Score} \ge \text{pass\_threshold}$$
- **`FALLBACK` Mode**: Primary system assertion is checked first. If system check returns `UNAVAILABLE` (e.g. API endpoint unreadable), visual diff result is used as fallback.

---

## 5. Automatic Self-Correction & Retry Handlers

To prevent execution failures caused by transient OS lag, animation delays, or visual grounding misclicks, the engine incorporates an automated two-level recovery system:

```
[Agent Action] ---> [Execute Driver Action]
                           |
                           v
               [Check Action Error / Timeout?]
                     /                \
             (Yes)  /                  \ (No)
                   v                    v
      [Level 1: Transient Retry]   [Check Visual State Change?]
      (Exp Backoff, Jitter)             /                \
                   |            (No change)              \ (Changed)
                   v                    v                 v
            [Re-try Action]  [Level 2: Visual Self-Correction] [Next Step]
                                (Inject error + screenshot
                                 to VLM driver)
```

### 5.1 Level 1: Transient Action Retry Handler

Handles driver level operational exceptions (e.g., target element momentarily covered, window focus shift, temporary ADB timeout).

- **Retry Strategy**: Exponential Backoff with Random Jitter
  $$\text{Delay}_k = \min(\text{MaxDelay}, \text{BaseDelay} \times 2^k) + \text{Uniform}(0, \text{Jitter})$$
  - `BaseDelay`: 0.5 seconds
  - `MaxDelay`: 5.0 seconds
  - `MaxRetries`: 3 attempts
  - `Jitter`: 0.1 seconds

### 5.2 Level 2: Visual Self-Correction & Recovery Loop

Detects when an action executed without throwing a driver exception but failed to achieve any state change (e.g. misclick outside a button or blocked modal dialog).

1. **State Stagnation Detection**:
   - If $\text{SSIM}(I_{t-1}, I_t) > 0.995$ after an interactive action (click/type), mark step as **Stagnant Action**.
2. **Visual Error Injection**:
   - Capture current screenshot and highlight failure region.
   - Construct feedback message: `"Action [click(x, y)] yielded no visual state change. Target element may have missed focus or modal dialog is overlaying. Suggesting alternative action."`
3. **Recovery Action Primitives**:
   - `press_key("Escape")`: Clear modal overlays or context menus.
   - `switch_window_focus()`: Refocus active desktop application window.
   - `scroll_into_view()`: Bring element into viewport before clicking.

---

## 6. Task Execution Runner Engine Architecture (`BenchmarkRunner`)

The `BenchmarkRunner` handles the complete lifecycle of executing a benchmark suite:

```python
class BenchmarkRunner:
    def __init__(self, config: RunnerConfig, db_logger: TrajectoryLogger):
        self.config = config
        self.logger = db_logger
        
    async def run_task(self, task: OmniBenchTask) -> TaskResult:
        # 1. Environment Setup
        env = await self.setup_environment(task)
        trajectory = []
        
        try:
            # 2. Execution Step Loop
            for step in range(task.max_steps):
                obs = await env.capture_observation() # screenshot + SoM + DOM/A11y
                action = await self.agent.predict_action(obs, trajectory)
                
                # Execute with Level 1 Retry
                exec_res = await self.execute_with_retry(env, action)
                
                # Check Level 2 Visual Stagnation / Self-Correction
                if exec_res.stagnant:
                    action = await self.trigger_self_correction(env, obs, action)
                    exec_res = await env.execute_action(action)
                    
                trajectory.append(StepLog(step, obs, action, exec_res))
                self.logger.log_step(task.task_id, step, obs, action, exec_res)
                
                # Early stopping check if intermediate state passes
                if await self.quick_check_completion(task, env):
                    break
                    
            # 3. Dual Evaluation Verification
            eval_result = await self.dual_evaluator.evaluate(task, env)
            return TaskResult(task_id=task.task_id, passed=eval_result.passed, score=eval_result.score, trajectory=trajectory)
            
        finally:
            # 4. Teardown & Cleanup
            await self.teardown_environment(task, env)
```

---

## 7. Features Discovered & Edge Cases Tables

### 7.1 Features Discovered
| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| F01 | Benchmark Domain | OSWorld Evaluator | Desktop OS file/app/setting state verification | Task ID, OS platform, bash/powershell script | `EvalResult(passed, score)` | Timeout / SSH driver disconnect handled gracefully | ORIGINAL_REQUEST.md & OSWorld Spec |
| F02 | Benchmark Domain | WebArena Evaluator | Multi-service web DOM & REST API evaluation | Task ID, URL, DOM selector, API specs | `EvalResult(passed, score)` | Browser crash auto-restarts browser | ORIGINAL_REQUEST.md & WebArena Spec |
| F03 | Benchmark Domain | AndroidWorld Evaluator | Mobile ADB shell + UI Automator XML evaluation | Task ID, ADB device serial, content query | `EvalResult(passed, score)` | ADB server restart on connection loss | ORIGINAL_REQUEST.md & AndroidWorld Spec |
| F04 | Benchmark Domain | Mind2Web Evaluator | Web step trajectory & target element selection eval | Trajectory log, DOM action target | `EvalResult(passed, score)` | Handles dynamic element ID mutation | ORIGINAL_REQUEST.md & Mind2Web Spec |
| F05 | Benchmark Domain | GAIA Evaluator | Multimodal assistant tool output & file SHA match | Task ID, expected answer string/regex/hash | `EvalResult(passed, score)` | Normalizes whitespace and line endings | ORIGINAL_REQUEST.md & GAIA Spec |
| F06 | Benchmark Domain | OmniBench Native Evaluator | Cross-platform composite dual-state verification | Task definition JSON, platform drivers | `EvalResult(passed, score)` | Rollback environment on teardown failure | ORIGINAL_REQUEST.md & Native Spec |
| F07 | Visual Eval | SSIM Diff Engine | Structural similarity index comparison on ROI | Image A, Image B, ROI bbox, min_ssim | `float` score, `bool` pass | Raises ValueError if image dimensions mismatch | Visual Engine Spec |
| F08 | Visual Eval | pHash Engine | Perceptual DCT hash distance calculation | Image A, Image B, max_distance | `int` Hamming distance | Falls back to SSIM if image invalid | Visual Engine Spec |
| F09 | Visual Eval | OCR Text Diff | Text extraction & substring match via OCR | ROI image, expected text list | `bool` pass, extracted text | Handles multi-language OCR fallback | Visual Engine Spec |
| F10 | System Eval | CLI Command Asserts | Shell command stdout/exit code matching | Shell command, expected regex, exit code | `bool` pass, actual output | Command execution timeout (10s limit) | System Engine Spec |
| F11 | System Eval | HTTP REST API Asserts | HTTP request and JSONPath value evaluation | URL, method, headers, JSON path rule | `bool` pass, HTTP status | Handles HTTP 5xx retry with backoff | System Engine Spec |
| F12 | System Eval | Filesystem Hash Asserts | SHA-256 hash comparison of generated files | File path, target SHA-256 hash | `bool` pass, actual hash | FileNotFoundError returns false pass | System Engine Spec |
| F13 | Evaluation Aggregator | Dual Evaluator Protocol | Aggregates visual + system checks (`AND`/`OR`/`WEIGHTED`) | Sub-evaluator outputs, weight rules | `EvalResult` summary | Defaults to `AND` mode if unspecified | Dual Evaluator Spec |
| F14 | Retry Handler | Transient Action Retry | Exponential backoff for driver level action errors | Action callable, max retries, base delay | Action result | Max retries exceeded raises ExecutionError | Retry Spec |
| F15 | Self-Correction | Visual Stagnation Loop | Feedback loop injecting visual context on error | Prior & current screenshots, prompt | Revised Action | Terminates loop after 3 consecutive failures | Self-Correction Spec |
| F16 | Runner | Benchmark Execution Runner | Asynchronous benchmark workflow execution manager | Task suite config, driver pool | Benchmark Run Summary | Isolates task failures, continuous suite run | Runner Architecture Spec |

### 7.2 Edge Cases
| # | Feature | Input | Observed / Expected Behavior |
|---|---------|-------|------------------------------|
| E01 | SSIM Visual Diff | Dynamic clock/timestamp visible on screen | ROI masking ignores clock region; evaluation passes without false failure. |
| E02 | CLI Assertion | Output contains trailing whitespace or ANSI color codes | Output strip filter normalizes string prior to regex matching. |
| E03 | ADB Android Evaluator | ADB server connection drops mid-evaluation | Evaluator detects socket break, executes `adb kill-server && adb start-server`, and retries. |
| E04 | Web DOM Evaluator | Element rendered in Shadow DOM or iframe | DOM assertion engine traverses Shadow roots and iframe context frames. |
| E05 | Self-Correction Loop | Agent stuck in infinite toggle loop (e.g. opening/closing menu) | Stagnation memory detects repeating action pattern ($A_t == A_{t-2}$) and forces fallback action. |
| E06 | Dual Aggregator | System check succeeds but visual check fails (e.g. file saved, but dialog left open) | `AND` mode correctly flags task as incomplete due to visual artifact residual. |
| E07 | Dataset Loader | Missing optional baseline screenshot in task config | Engine falls back strictly to System CLI/API evaluation without error. |
| E08 | File Assertion | Large file (>500MB) SHA-256 hash verification | Engine streams file in 64KB chunks to maintain memory usage below 50MB. |

---

## 8. Test Suite Design (Tiers 1–4)

To guarantee software quality and verification accuracy, the testing suite is structured into four progressive tiers:

```
+-------------------------------------------------------------------+
| Tier 4: End-to-End System Benchmark Evaluation Tests             |
| (Full pipeline evaluation across sample task suites)              |
+-------------------------------------------------------------------+
                                  ^
                                  |
+-------------------------------------------------------------------+
| Tier 3: Benchmark Task Subset Tests                               |
| (Dry-run mock evaluation on 5 representative tasks per family)    |
+-------------------------------------------------------------------+
                                  ^
                                  |
+-------------------------------------------------------------------+
| Tier 2: Integration & Driver Mock Tests                           |
| (Runner execution loop, SQLite logging, dual aggregator logic)    |
+-------------------------------------------------------------------+
                                  ^
                                  |
+-------------------------------------------------------------------+
| Tier 1: Unit & Component Tests                                    |
| (SSIM, pHash, CLI parser, schema validator, retry timer)          |
+-------------------------------------------------------------------+
```

### 8.1 Tier 1: Unit & Component Tests
- **Objective**: Isolated verification of core utility functions and evaluators.
- **Coverage**:
  - `test_task_schema_validation()`: Validates JSON/YAML task specs against draft-07 schema.
  - `test_ssim_calculation()`: Verifies exact and thresholded SSIM score calculation on synthetic test images.
  - `test_phash_hamming_distance()`: Verifies pHash distance calculation.
  - `test_cli_assertion_parser()`: Validates regex and exit code matching logic.
  - `test_exponential_backoff()`: Verifies retry delays and max retry limits.

### 8.2 Tier 2: Integration & Driver Mock Tests
- **Objective**: Test interaction between `BenchmarkRunner`, `DualEvaluator`, and `TrajectoryLogger`.
- **Coverage**:
  - `test_runner_task_lifecycle()`: Mock driver execution flow from setup to teardown.
  - `test_dual_evaluator_aggregation()`: Tests `AND`, `OR`, `WEIGHTED`, and `FALLBACK` modes with mock sub-evaluators.
  - `test_sqlite_trajectory_persistence()`: Verifies step logging and screenshot metadata storage in SQLite database.
  - `test_transient_retry_recovery()`: Simulates driver transient exceptions and verifies backoff recovery.

### 8.3 Tier 3: Benchmark Task Subset Tests
- **Objective**: Validate task loading and execution on 5 sample tasks per benchmark family (30 tasks total).
- **Coverage**:
  - `test_osworld_desktop_tasks()`: Linux file creation and terminal command evaluation.
  - `test_webarena_shopping_tasks()`: Web e-commerce navigation and DOM state evaluation.
  - `test_androidworld_settings_tasks()`: Android settings toggle via mock ADB shell.
  - `test_mind2web_trajectory_tasks()`: Mind2Web action step matching.
  - `test_gaia_file_analysis_tasks()`: File hashing and text extraction matching.
  - `test_omnibench_composite_tasks()`: Desktop + Web dual verification task execution.

### 8.4 Tier 4: End-to-End System Benchmark Evaluation Tests
- **Objective**: Full end-to-end execution of evaluation suite with full dashboard and CLI integration.
- **Coverage**:
  - `test_e2e_benchmark_suite_execution()`: Run benchmark runner CLI command `omnibench eval --suite sample`.
  - `test_e2e_evaluator_accuracy()`: Verify 100% precision and recall of dual evaluators on ground-truth pass/fail trajectory recordings.

---

## 9. Conclusion & Next Steps

This specification report establishes the definitive technical design for Requirement R4. The contracts, schemas, evaluators, retry algorithms, and test tiers documented here are ready for architectural integration into `PROJECT.md` and subsequent implementation.
