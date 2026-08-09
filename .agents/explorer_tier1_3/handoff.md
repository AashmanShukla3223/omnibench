# Tier 1 E2E Test Suite Specification Report (Features F15 - F21)

**Agent**: `explorer_tier1_3`  
**Working Directory**: `/home/oh_my_macos27/OmniBench Computer Use/.agents/explorer_tier1_3`  
**Target Scope**: Tier 1 Feature Coverage for F15 through F21 (35 test cases total: 5 per feature)  
**Status**: Completed  

---

## 1. Observation

Direct observations extracted from project documentation and specifications:

1. **`ORIGINAL_REQUEST.md` Requirements**:
   - **R4. Benchmark Evaluation & Verification Engine**: *"Evaluation runner for OSWorld, WebArena, AndroidWorld, Mind2Web, GAIA, and native OmniBench benchmark tasks using dual evaluators (visual state diffing + system CLI/API state assertions) with automatic self-correction & retry handlers."*
   - **R5. Interface & Telemetry Dashboard**: *"Rich Python CLI (`omnibench`) and Web Dashboard UI for benchmark configuration, dataset selection, live trajectory monitoring, and SQLite database logging with screenshot diff analytics."*

2. **`PROJECT.md` Architecture & Feature Inventory**:
   - **F15 (M4 / R4)**: *Benchmark Adapters* — Dataset adapters for OSWorld, WebArena, AndroidWorld, Mind2Web, GAIA, OmniBench.
   - **F16 (M4 / R4)**: *Dual Evaluator Engine* — Visual state diffing (SSIM/pHash/ROI/OCR) + system CLI/API state assertions. Interface contract: `DualEvaluator.evaluate(initial_state: dict, final_state: dict, trajectory: list) -> EvaluationResult`.
   - **F17 (M4 / R4)**: *Self-Correction Handlers* — Level 1/2 retries and visual stagnation feedback injector.
   - **F18 (M5 / R5)**: *`omnibench` CLI* — Python CLI (`config`, `dataset`, `run`, `monitor`, `db`, `dashboard`).
   - **F19 (M5 / R5)**: *SQLite Telemetry & DDL* — SQLite schema (`runs`, `episodes`, `steps`, `screenshot_diffs`) and logger.
   - **F20 (M5 / R5)**: *Screenshot Diff Analytics* — MSE, SSIM, pixel diff percentage, and difference mask generator.
   - **F21 (M5 / R5)**: *Web Dashboard UI* — Python HTTP/SSE live telemetry backend + responsive SPA dashboard frontend.

3. **`TEST_INFRA.md` Test Philosophy & Targets**:
   - Tier 1 target: Opaque-box, happy-path and core behavior tests verifying public SDK contracts, CLI commands, database schemas, and HTTP endpoints.
   - Target test directory: `tests/e2e/tier1_features/`.
   - Coverage requirement: Exactly 5 test cases per feature for 7 features = 35 test cases total.

---

## 2. Logic Chain

1. **Requirement to Specification Mapping**:
   - Requirements R4 and R5 decompose into 7 distinct features (F15 through F21).
   - Each feature defines a clear public surface area (Python SDK classes, CLI subcommands, SQLite tables, or HTTP REST/SSE endpoints).
   - Opaque-box testing principles dictate that tests verify inputs, outputs, schemas, exit codes, and assertion structures without coupling to internal private implementations.

2. **Feature Coverage Strategy**:
   - **F15 (Benchmark Adapters)**: Must test task loading, prompt formatting, and task schema generation across all supported benchmark domains (OSWorld, WebArena, AndroidWorld, Mind2Web, GAIA, OmniBench).
   - **F16 (Dual Evaluator Engine)**: Must test the combined dual evaluation contract (`DualEvaluator`), visual diffing logic (SSIM/ROI), and system CLI/API state assertion verification.
   - **F17 (Self-Correction Handlers)**: Must test Level 1 prompt re-grounding, Level 2 action backoffs, visual stagnation detection across screenshot trajectories, retry exhaustion caps, and integrated runner self-correction loops.
   - **F18 (`omnibench` CLI)**: Must test all main CLI subcommands (`config`, `dataset`, `run`, `db`, `dashboard`) via command line interface invocation verifying exit codes and output formats.
   - **F19 (SQLite Telemetry Logging)**: Must test SQLite schema DDL creation, run/episode lifecycle logging, step trajectory recording, screenshot diff metric storage, and aggregation queries.
   - **F20 (Screenshot Diff Analytics)**: Must test zero-diff identical images, non-zero MSE/SSIM metric calculations, visual mask generation, resolution auto-scaling, and ROI bounded diff analysis.
   - **F21 (Web Dashboard UI)**: Must test REST API endpoints (`/api/runs`, `/api/runs/{id}/episodes`), live SSE stream (`/api/live`), visual diff artifact delivery (`/api/diff/{id}`), and static SPA serving / 404 error handling.

3. **Validation & Assertion Precision**:
   - Every test case specifies exact inputs, execution triggers, expected return types, status codes, and precise assertion conditions (e.g. `passed == True`, `exit_code == 0`, `ssim >= 0.90`, `HTTP 200 OK`).

---

## 3. Caveats

1. **Implementation State**:
   - Milestones M4 (Benchmark & Evaluation) and M5 (Telemetry & Dashboard) are currently in `PLANNED` status. Test specifications are designed against the interface contracts and schemas defined in `PROJECT.md` and `TEST_INFRA.md`.
2. **Mocking & Isolation**:
   - External web environments (WebArena), Android ADB daemons, and live API providers are assumed to be mockable/stubbed during E2E Tier 1 execution to maintain fast, reproducible test execution.
3. **Graphics & Screen Capture in Headless CI**:
   - Visual analytics and diff tests use synthetic Pillow/PNG image fixtures to guarantee deterministic execution across standard Linux CI environments without requiring physical GPU/displays.

---

## 4. Conclusion

A comprehensive suite of **35 detailed E2E test case specifications** (5 test cases per feature for F15 through F21) has been fully designed and documented below. All test cases strictly adhere to opaque-box testing guidelines, testing public Python SDK contracts, CLI commands, SQLite schemas, and HTTP endpoints.

---

## Detailed E2E Test Case Specifications (F15 - F21)

### Feature 15: Benchmark Adapters (`omnibench.benchmarks.adapters`)

#### Test Case 15.1: `test_f15_osworld_adapter_load_and_format`
- **Feature**: F15 - Benchmark Adapters (OSWorld)
- **Target Interface**: `omnibench.benchmarks.adapters.osworld.OSWorldAdapter`
- **Description**: Verify OSWorld benchmark adapter loads task definitions and formats prompt with OS action space instructions.
- **Input Data**: Task payload JSON with `task_id="osworld_001"`, `domain="osworld"`, `instruction="Open terminal and create directory /tmp/test_dir"`.
- **Execution Step**:
  ```python
  adapter = OSWorldAdapter()
  task = adapter.load_task(raw_task_json)
  prompt = adapter.format_prompt(task)
  ```
- **Assertions**:
  - `task.task_id == "osworld_001"`
  - `task.domain == "osworld"`
  - `"click"` in prompt and `"type"` in prompt
  - `"Open terminal"` in prompt

#### Test Case 15.2: `test_f15_webarena_adapter_url_and_dom_spec`
- **Feature**: F15 - Benchmark Adapters (WebArena)
- **Target Interface**: `omnibench.benchmarks.adapters.webarena.WebArenaAdapter`
- **Description**: Verify WebArena adapter parses web task metadata, initial URL, and DOM selector criteria.
- **Input Data**: WebArena task specification with `start_url="http://localhost:7770/shopping"` and goal `"Find red t-shirt under $20"`.
- **Execution Step**:
  ```python
  adapter = WebArenaAdapter()
  task = adapter.load_task(webarena_spec)
  ```
- **Assertions**:
  - `task.domain == "webarena"`
  - `task.initial_state["url"] == "http://localhost:7770/shopping"`
  - `task.eval_spec["target_selector"]` is not None

#### Test Case 15.3: `test_f15_androidworld_adapter_mobile_primitives`
- **Feature**: F15 - Benchmark Adapters (AndroidWorld)
- **Target Interface**: `omnibench.benchmarks.adapters.androidworld.AndroidWorldAdapter`
- **Description**: Verify AndroidWorld adapter converts mobile app task definitions into touch/gesture action primitives.
- **Input Data**: AndroidWorld task definition for toggling system settings.
- **Execution Step**:
  ```python
  adapter = AndroidWorldAdapter()
  task = adapter.load_task(android_task_dict)
  ```
- **Assertions**:
  - `task.domain == "androidworld"`
  - `task.allowed_actions` contains `"swipe"`, `"tap"`, `"home"`
  - `len(task.setup_commands) >= 1`

#### Test Case 15.4: `test_f15_mind2web_trajectory_task_parsing`
- **Feature**: F15 - Benchmark Adapters (Mind2Web)
- **Target Interface**: `omnibench.benchmarks.adapters.mind2web.Mind2WebAdapter`
- **Description**: Verify Mind2Web adapter parses multi-step web trajectory tasks and candidate element mappings.
- **Input Data**: Mind2Web task JSON containing step candidate element IDs and target subgoals.
- **Execution Step**:
  ```python
  adapter = Mind2WebAdapter()
  task = adapter.load_task(mind2web_json)
  ```
- **Assertions**:
  - `task.domain == "mind2web"`
  - `len(task.subgoals) >= 2`
  - `task.eval_spec["element_candidates"]` is a list with non-zero length

#### Test Case 15.5: `test_f15_gaia_multimodal_and_omnibench_native`
- **Feature**: F15 - Benchmark Adapters (GAIA & OmniBench Native)
- **Target Interface**: `omnibench.benchmarks.adapters.gaia.GAIAAdapter`, `OmniBenchNativeAdapter`
- **Description**: Verify GAIA multi-modal task adapter and OmniBench native synthetic task adapter produce valid standard `TaskSchema`.
- **Input Data**: GAIA task with text prompt + attachment image bytes; OmniBench native YAML task definition.
- **Execution Step**:
  ```python
  gaia_task = GAIAAdapter().load_task(gaia_payload)
  native_task = OmniBenchNativeAdapter().load_task(native_yaml)
  ```
- **Assertions**:
  - `isinstance(gaia_task, TaskSchema) is True`
  - `gaia_task.has_media_attachment is True`
  - `isinstance(native_task, TaskSchema) is True`
  - `native_task.domain == "omnibench_native"`

---

### Feature 16: Dual Evaluator Engine (`omnibench.evaluators`)

#### Test Case 16.1: `test_f16_dual_evaluator_both_pass`
- **Feature**: F16 - Dual Evaluator Engine
- **Target Interface**: `omnibench.evaluators.dual_evaluator.DualEvaluator`
- **Description**: Verify `DualEvaluator` returns success when both visual state diffing and system assertions pass.
- **Input Data**: Initial state, final state (visual SSIM score 0.95), system assertion (`file_exists=True`).
- **Execution Step**:
  ```python
  evaluator = DualEvaluator()
  result = evaluator.evaluate(initial_state, final_state, trajectory)
  ```
- **Assertions**:
  - `result.passed is True`
  - `result.score == 1.0`
  - `result.visual_diff_score >= 0.90`
  - `result.system_assertion_passed is True`

#### Test Case 16.2: `test_f16_dual_evaluator_system_assertion_failure`
- **Feature**: F16 - Dual Evaluator Engine
- **Target Interface**: `omnibench.evaluators.dual_evaluator.DualEvaluator`
- **Description**: Verify `DualEvaluator` fails when visual diff passes but system assertion fails.
- **Input Data**: Visual diff score 0.98, CLI check `cat /tmp/output.txt` returns exit code 1 (file missing).
- **Execution Step**:
  ```python
  result = evaluator.evaluate(initial_state, final_state, trajectory)
  ```
- **Assertions**:
  - `result.passed is False`
  - `result.score < 1.0`
  - `result.visual_diff_score >= 0.95`
  - `result.system_assertion_passed is False`
  - `"Assertion failed: file /tmp/output.txt missing"` in result.details["errors"]

#### Test Case 16.3: `test_f16_dual_evaluator_visual_diff_failure`
- **Feature**: F16 - Dual Evaluator Engine
- **Target Interface**: `omnibench.evaluators.dual_evaluator.DualEvaluator`
- **Description**: Verify `DualEvaluator` fails when system assertion passes but visual state change is below threshold.
- **Input Data**: System assertion passes (`process_running=True`), final screenshot shows wrong screen (SSIM score 0.35 vs required 0.85).
- **Execution Step**:
  ```python
  result = evaluator.evaluate(initial_state, final_state, trajectory)
  ```
- **Assertions**:
  - `result.passed is False`
  - `result.score < 1.0`
  - `result.visual_diff_score == 0.35`
  - `result.system_assertion_passed is True`

#### Test Case 16.4: `test_f16_visual_diff_ssim_and_roi_masking`
- **Feature**: F16 - Dual Evaluator Engine (Visual Diff)
- **Target Interface**: `omnibench.evaluators.visual_diff.VisualDiffEvaluator`
- **Description**: Verify `VisualDiffEvaluator` correctly calculates SSIM and restricts comparison to Region of Interest (ROI).
- **Input Data**: Image 1, Image 2 (differing only in ROI box `[100, 100, 300, 300]`).
- **Execution Step**:
  ```python
  diff_result = VisualDiffEvaluator.compute_diff(img1, img2, roi=[100, 100, 300, 300])
  ```
- **Assertions**:
  - `diff_result.ssim < 1.0`
  - `diff_result.roi == [100, 100, 300, 300]`
  - `diff_result.diff_pixels > 0`

#### Test Case 16.5: `test_f16_system_assertions_cli_and_api`
- **Feature**: F16 - Dual Evaluator Engine (System Assertions)
- **Target Interface**: `omnibench.evaluators.system_assertions.SystemAssertionEvaluator`
- **Description**: Verify system state assertion engine evaluates CLI command exit codes, regex output matches, and HTTP endpoint status codes.
- **Input Data**: Assertion specs: `[{"type": "cli", "cmd": "echo hello", "expected_code": 0}, {"type": "http", "url": "http://localhost:8080/health", "expected_status": 200}]`.
- **Execution Step**:
  ```python
  eval_summary = SystemAssertionEvaluator.assert_all(assertion_specs)
  ```
- **Assertions**:
  - `eval_summary.all_passed is True`
  - `len(eval_summary.results) == 2`
  - `eval_summary.results[0].passed is True`

---

### Feature 17: Self-Correction Handlers (`omnibench.evaluators.self_correction`)

#### Test Case 17.1: `test_f17_level1_prompt_regrounding_on_parse_error`
- **Feature**: F17 - Self-Correction Handlers
- **Target Interface**: `omnibench.evaluators.self_correction.SelfCorrectionHandler`
- **Description**: Verify Level 1 self-correction triggers prompt re-grounding feedback when VLM output fails action JSON parsing.
- **Input Data**: Raw invalid VLM text response `"I will click the button"`, `retry_count=0`.
- **Execution Step**:
  ```python
  correction = SelfCorrectionHandler.handle_parse_error(raw_response, retry_count=0)
  ```
- **Assertions**:
  - `correction.should_retry is True`
  - `correction.level == 1`
  - `"Format Error"` in correction.feedback_prompt
  - `"Respond only with JSON format"` in correction.feedback_prompt

#### Test Case 17.2: `test_f17_level2_action_retry_backoff`
- **Feature**: F17 - Self-Correction Handlers
- **Target Interface**: `omnibench.evaluators.self_correction.SelfCorrectionHandler`
- **Description**: Verify Level 2 self-correction applies backoff delay and reconnects driver on transient action execution failure.
- **Input Data**: Action execution exception `OSDriverException("Target element unclickable")`, `retry_count=1`.
- **Execution Step**:
  ```python
  correction = SelfCorrectionHandler.handle_execution_error(action, exception, retry_count=1)
  ```
- **Assertions**:
  - `correction.should_retry is True`
  - `correction.level == 2`
  - `correction.backoff_delay_sec > 0.0`
  - `correction.inject_pre_action == "wait"`

#### Test Case 17.3: `test_f17_visual_stagnation_detection_and_feedback`
- **Feature**: F17 - Self-Correction Handlers
- **Target Interface**: `omnibench.evaluators.self_correction.VisualStagnationDetector`
- **Description**: Verify visual stagnation detector identifies non-changing screen states across 3 consecutive trajectory steps and injects corrective context.
- **Input Data**: Trajectory with screenshots S1, S2, S3 where SSIM(S1, S2) > 0.99 and SSIM(S2, S3) > 0.99.
- **Execution Step**:
  ```python
  stagnant, feedback = VisualStagnationDetector.check(trajectory)
  ```
- **Assertions**:
  - `stagnant is True`
  - `"Visual Stagnation Detected"` in feedback
  - `"Screen has not changed for 3 consecutive steps"` in feedback

#### Test Case 17.4: `test_f17_self_correction_retry_cap_exhaustion`
- **Feature**: F17 - Self-Correction Handlers
- **Target Interface**: `omnibench.evaluators.self_correction.SelfCorrectionHandler`
- **Description**: Verify self-correction handler terminates retries gracefully when maximum retry cap is reached.
- **Input Data**: Repeated failure at `retry_count=3` (`max_retries=3`).
- **Execution Step**:
  ```python
  correction = SelfCorrectionHandler.handle_parse_error(raw_response, retry_count=3)
  ```
- **Assertions**:
  - `correction.should_retry is False`
  - `correction.reason == "MAX_RETRIES_EXCEEDED"`

#### Test Case 17.5: `test_f17_benchmark_runner_self_correction_cycle`
- **Feature**: F17 - Self-Correction Handlers
- **Target Interface**: `omnibench.benchmarks.runner.BenchmarkRunner`
- **Description**: Verify end-to-end integration of self-correction handler inside `BenchmarkRunner` loop.
- **Input Data**: Task with mock VLM provider returning bad action on step 1, corrected action after feedback prompt on step 2.
- **Execution Step**:
  ```python
  runner = BenchmarkRunner(enable_self_correction=True)
  run_result = runner.run_task(task)
  ```
- **Assertions**:
  - `run_result.passed is True`
  - `run_result.self_correction_count == 1`
  - `len(run_result.trajectory) == 2`

---

### Feature 18: `omnibench` CLI (`omnibench.cli`)

#### Test Case 18.1: `test_f18_cli_config_set_and_show`
- **Feature**: F18 - `omnibench` CLI
- **Target Interface**: `omnibench.cli.main` (CLI entry point)
- **Description**: Verify `omnibench config` subcommand sets config parameters and outputs current configuration in JSON format.
- **Input Data**: CLI command args `["config", "set", "gateway.provider", "mock"]` followed by `["config", "show", "--json"]`.
- **Execution Step**:
  ```python
  runner = CliRunner()
  res1 = runner.invoke(cli, ["config", "set", "gateway.provider", "mock"])
  res2 = runner.invoke(cli, ["config", "show", "--json"])
  ```
- **Assertions**:
  - `res1.exit_code == 0`
  - `res2.exit_code == 0`
  - `json.loads(res2.output)["gateway"]["provider"] == "mock"`

#### Test Case 18.2: `test_f18_cli_dataset_list_and_info`
- **Feature**: F18 - `omnibench` CLI
- **Target Interface**: `omnibench.cli.main`
- **Description**: Verify `omnibench dataset` lists available benchmarks and displays dataset details.
- **Input Data**: CLI command args `["dataset", "list"]` and `["dataset", "info", "osworld"]`.
- **Execution Step**:
  ```python
  runner = CliRunner()
  res_list = runner.invoke(cli, ["dataset", "list"])
  res_info = runner.invoke(cli, ["dataset", "info", "osworld"])
  ```
- **Assertions**:
  - `res_list.exit_code == 0`
  - `"osworld"` in res_list.output and `"webarena"` in res_list.output
  - `res_info.exit_code == 0`
  - `"OSWorld"` in res_info.output

#### Test Case 18.3: `test_f18_cli_run_execution_trigger`
- **Feature**: F18 - `omnibench` CLI
- **Target Interface**: `omnibench.cli.main`
- **Description**: Verify `omnibench run` executes a benchmark run with specified flags and outputs execution summary.
- **Input Data**: CLI args `["run", "--benchmark", "osworld", "--task-id", "task_01", "--provider", "mock"]`.
- **Execution Step**:
  ```python
  runner = CliRunner()
  result = runner.invoke(cli, ["run", "--benchmark", "osworld", "--task-id", "task_01", "--provider", "mock"])
  ```
- **Assertions**:
  - `result.exit_code == 0`
  - `"Benchmark Run Completed"` in result.output
  - `"Pass Rate"` in result.output

#### Test Case 18.4: `test_f18_cli_db_query_and_export`
- **Feature**: F18 - `omnibench` CLI
- **Target Interface**: `omnibench.cli.main`
- **Description**: Verify `omnibench db` subcommand queries run telemetry database and exports run trajectories.
- **Input Data**: Temp sqlite database file; CLI args `["db", "summary", "--db-path", db_file]` and `["db", "export", "--run-id", "run_101", "--format", "json"]`.
- **Execution Step**:
  ```python
  res_sum = runner.invoke(cli, ["db", "summary", "--db-path", db_path])
  res_exp = runner.invoke(cli, ["db", "export", "--run-id", "run_101", "--format", "json", "--db-path", db_path])
  ```
- **Assertions**:
  - `res_sum.exit_code == 0`
  - `res_exp.exit_code == 0`
  - `json.loads(res_exp.output)["run_id"] == "run_101"`

#### Test Case 18.5: `test_f18_cli_dashboard_launch_options`
- **Feature**: F18 - `omnibench` CLI
- **Target Interface**: `omnibench.cli.main`
- **Description**: Verify `omnibench dashboard` parses host and port flags correctly for dashboard web server launching.
- **Input Data**: CLI command args `["dashboard", "--host", "127.0.0.1", "--port", "9090", "--help"]`.
- **Execution Step**:
  ```python
  runner = CliRunner()
  result = runner.invoke(cli, ["dashboard", "--help"])
  ```
- **Assertions**:
  - `result.exit_code == 0`
  - `"--host"` in result.output
  - `"--port"` in result.output

---

### Feature 19: SQLite Telemetry Logging (`omnibench.telemetry`)

#### Test Case 19.1: `test_f19_db_schema_ddl_initialization`
- **Feature**: F19 - SQLite Telemetry Logging
- **Target Interface**: `omnibench.telemetry.db.DatabaseManager`
- **Description**: Verify database initialization creates required SQLite tables (`runs`, `episodes`, `steps`, `screenshot_diffs`) and indices.
- **Input Data**: Temporary DB path `/tmp/test_schema.db`.
- **Execution Step**:
  ```python
  db_mgr = DatabaseManager("/tmp/test_schema.db")
  db_mgr.init_db()
  tables = db_mgr.get_table_names()
  ```
- **Assertions**:
  - `set(["runs", "episodes", "steps", "screenshot_diffs"]).issubset(set(tables))`

#### Test Case 19.2: `test_f19_run_and_episode_lifecycle_logging`
- **Feature**: F19 - SQLite Telemetry Logging
- **Target Interface**: `omnibench.telemetry.logger.TelemetryLogger`
- **Description**: Verify logging run creation, episode start, status updates, and end lifecycle events.
- **Input Data**: Run metadata `{benchmark: "webarena"}` and episode metadata `{task_id: "web_01"}`.
- **Execution Step**:
  ```python
  logger = TelemetryLogger(db_path)
  run_id = logger.start_run("webarena", config={})
  episode_id = logger.start_episode(run_id, "web_01")
  logger.end_episode(episode_id, status="success", score=1.0)
  ep_data = logger.get_episode(episode_id)
  ```
- **Assertions**:
  - `ep_data["status"] == "success"`
  - `ep_data["score"] == 1.0`
  - `ep_data["run_id"] == run_id`

#### Test Case 19.3: `test_f19_step_trajectory_record_insertion`
- **Feature**: F19 - SQLite Telemetry Logging
- **Target Interface**: `omnibench.telemetry.logger.TelemetryLogger`
- **Description**: Verify step action execution data, screenshot file path, and latency metrics are correctly inserted into `steps` table.
- **Input Data**: Step data dict with `step_number=1`, `action_type="click"`, `action_params={"x": 50, "y": 75}`, `latency_ms=120.5`.
- **Execution Step**:
  ```python
  step_id = logger.log_step(episode_id, step_data)
  stored_step = logger.get_step(step_id)
  ```
- **Assertions**:
  - `stored_step["action_type"] == "click"`
  - `json.loads(stored_step["action_params"])["x"] == 50`
  - `stored_step["latency_ms"] == 120.5`

#### Test Case 19.4: `test_f19_screenshot_diff_metrics_storage`
- **Feature**: F19 - SQLite Telemetry Logging
- **Target Interface**: `omnibench.telemetry.logger.TelemetryLogger`
- **Description**: Verify screenshot diff analytics (MSE, SSIM, pixel diff percentage, diff mask path) are logged with foreign key link to step.
- **Input Data**: `step_id=10`, `mse=8.5`, `ssim=0.96`, `pixel_diff_pct=1.5`, `diff_mask_path="/tmp/mask.png"`.
- **Execution Step**:
  ```python
  diff_id = logger.log_screenshot_diff(step_id, mse=8.5, ssim=0.96, pixel_diff_pct=1.5, diff_mask_path="/tmp/mask.png")
  stored_diff = logger.get_screenshot_diff(step_id)
  ```
- **Assertions**:
  - `stored_diff["mse"] == 8.5`
  - `stored_diff["ssim"] == 0.96`
  - `stored_diff["pixel_diff_pct"] == 1.5`
  - `stored_diff["diff_mask_path"] == "/tmp/mask.png"`

#### Test Case 19.5: `test_f19_run_summary_aggregation_query`
- **Feature**: F19 - SQLite Telemetry Logging
- **Target Interface**: `omnibench.telemetry.logger.TelemetryLogger`
- **Description**: Verify run summary query correctly computes total episodes, passed/failed counts, and average score.
- **Input Data**: Run with 4 episodes (3 success with score 1.0, 1 failure with score 0.0).
- **Execution Step**:
  ```python
  summary = logger.get_run_summary(run_id)
  ```
- **Assertions**:
  - `summary["total_episodes"] == 4`
  - `summary["passed_episodes"] == 3`
  - `summary["failed_episodes"] == 1`
  - `summary["pass_rate"] == 0.75`
  - `summary["avg_score"] == 0.75`

---

### Feature 20: Screenshot Diff Analytics (`omnibench.telemetry.analytics`)

#### Test Case 20.1: `test_f20_identical_images_zero_diff`
- **Feature**: F20 - Screenshot Diff Analytics
- **Target Interface**: `omnibench.telemetry.analytics.ScreenshotDiffAnalytics`
- **Description**: Verify comparing two identical screenshots yields zero MSE, 1.0 SSIM, and 0% pixel diff percentage.
- **Input Data**: 200x200 solid RGB PIL Image fixture `img1` and `img2 = img1.copy()`.
- **Execution Step**:
  ```python
  metrics = ScreenshotDiffAnalytics.compute_diff(img1, img2)
  ```
- **Assertions**:
  - `metrics.mse == 0.0`
  - `metrics.ssim == 1.0`
  - `metrics.pixel_diff_pct == 0.0`

#### Test Case 20.2: `test_f20_modified_region_metrics_calculation`
- **Feature**: F20 - Screenshot Diff Analytics
- **Target Interface**: `omnibench.telemetry.analytics.ScreenshotDiffAnalytics`
- **Description**: Verify modified screen region produces accurate MSE, SSIM reduction, and non-zero pixel diff percentage.
- **Input Data**: 100x100 white image (10,000 pixels) vs 100x100 image with a 10x10 black square (100 pixels changed).
- **Execution Step**:
  ```python
  metrics = ScreenshotDiffAnalytics.compute_diff(white_img, modified_img)
  ```
- **Assertions**:
  - `metrics.mse > 0.0`
  - `metrics.ssim < 1.0`
  - `metrics.pixel_diff_pct == 1.0`  # 100 / 10000 = 1%

#### Test Case 20.3: `test_f20_diff_mask_generation`
- **Feature**: F20 - Screenshot Diff Analytics
- **Target Interface**: `omnibench.telemetry.analytics.ScreenshotDiffAnalytics`
- **Description**: Verify visual difference mask generator produces an RGB image highlighting modified pixels.
- **Input Data**: Baseline screenshot and modified screenshot.
- **Execution Step**:
  ```python
  mask_img = ScreenshotDiffAnalytics.generate_diff_mask(baseline_img, modified_img, highlight_color=(255, 0, 0))
  ```
- **Assertions**:
  - `isinstance(mask_img, PIL.Image.Image) is True`
  - `mask_img.size == baseline_img.size`
  - `mask_img.mode == "RGB"`

#### Test Case 20.4: `test_f20_resolution_auto_normalization`
- **Feature**: F20 - Screenshot Diff Analytics
- **Target Interface**: `omnibench.telemetry.analytics.ScreenshotDiffAnalytics`
- **Description**: Verify analytics engine automatically resizes differing resolution images before matrix diff calculation.
- **Input Data**: Image 1 (1920x1080) and Image 2 (1280x720).
- **Execution Step**:
  ```python
  metrics = ScreenshotDiffAnalytics.compute_diff(img_1080p, img_720p, normalize_size=True)
  ```
- **Assertions**:
  - `metrics is not None`
  - `metrics.ssim >= 0.0`
  - No shape mismatch exception raised during execution

#### Test Case 20.5: `test_f20_roi_bounded_diff_analysis`
- **Feature**: F20 - Screenshot Diff Analytics
- **Target Interface**: `omnibench.telemetry.analytics.ScreenshotDiffAnalytics`
- **Description**: Verify setting Region of Interest (ROI) restricts diff calculations to specified sub-rectangle.
- **Input Data**: Two images differing only in top status bar (y: 0-50); ROI set to `[0, 100, 500, 500]`.
- **Execution Step**:
  ```python
  metrics = ScreenshotDiffAnalytics.compute_diff(img1, img2, roi=[0, 100, 500, 500])
  ```
- **Assertions**:
  - `metrics.pixel_diff_pct == 0.0`
  - `metrics.ssim == 1.0`

---

### Feature 21: Web Dashboard UI (`omnibench.dashboard`)

#### Test Case 21.1: `test_f21_api_get_runs_list`
- **Feature**: F21 - Web Dashboard UI
- **Target Interface**: `omnibench.dashboard.server` (`GET /api/runs`)
- **Description**: Verify `/api/runs` REST endpoint returns list of stored benchmark runs.
- **Input Data**: Test HTTP client (e.g. Starlette / FastAPI TestClient or standard `http.server` test runner) connected to database with 2 runs.
- **Execution Step**:
  ```python
  response = client.get("/api/runs")
  ```
- **Assertions**:
  - `response.status_code == 200`
  - `response.headers["content-type"] == "application/json"`
  - `len(response.json()["runs"]) == 2`

#### Test Case 21.2: `test_f21_api_get_run_episodes`
- **Feature**: F21 - Web Dashboard UI
- **Target Interface**: `omnibench.dashboard.server` (`GET /api/runs/{run_id}/episodes`)
- **Description**: Verify `/api/runs/{run_id}/episodes` REST endpoint returns episode metadata for specific run.
- **Input Data**: Request GET `/api/runs/run_test_01/episodes`.
- **Execution Step**:
  ```python
  response = client.get("/api/runs/run_test_01/episodes")
  ```
- **Assertions**:
  - `response.status_code == 200`
  - `response.json()["run_id"] == "run_test_01"`
  - `isinstance(response.json()["episodes"], list) is True`

#### Test Case 21.3: `test_f21_live_sse_telemetry_stream`
- **Feature**: F21 - Web Dashboard UI
- **Target Interface**: `omnibench.dashboard.server` (`GET /api/live`)
- **Description**: Verify `/api/live` Server-Sent Events endpoint streams real-time trajectory step events.
- **Input Data**: Event trigger in background logging step completion event.
- **Execution Step**:
  ```python
  response = client.get("/api/live", stream=True)
  first_event = parse_sse_event(response)
  ```
- **Assertions**:
  - `response.status_code == 200`
  - `response.headers["content-type"] == "text/event-stream"`
  - `first_event["event"] == "step_complete"`

#### Test Case 21.4: `test_f21_diff_viewer_artifact_endpoint`
- **Feature**: F21 - Web Dashboard UI
- **Target Interface**: `omnibench.dashboard.server` (`GET /api/diff/{step_id}`)
- **Description**: Verify `/api/diff/{step_id}` endpoint returns image URLs and visual diff metrics payload.
- **Input Data**: Step with registered initial screenshot, final screenshot, diff mask, and SSIM metrics.
- **Execution Step**:
  ```python
  response = client.get("/api/diff/step_007")
  data = response.json()
  ```
- **Assertions**:
  - `response.status_code == 200`
  - `"initial_image_url"` in data
  - `"final_image_url"` in data
  - `"diff_mask_url"` in data
  - `"ssim"` in data["metrics"]

#### Test Case 21.5: `test_f21_static_spa_delivery_and_404`
- **Feature**: F21 - Web Dashboard UI
- **Target Interface**: `omnibench.dashboard.server` (`GET /`, `GET /api/nonexistent`)
- **Description**: Verify web server delivers index HTML for root path `/` and returns 404 JSON for unknown API routes.
- **Input Data**: GET `/` and GET `/api/nonexistent`.
- **Execution Step**:
  ```python
  resp_root = client.get("/")
  resp_404 = client.get("/api/nonexistent")
  ```
- **Assertions**:
  - `resp_root.status_code == 200`
  - `"text/html"` in resp_root.headers["content-type"]
  - `"<div id=\"app\">"` in resp_root.text
  - `resp_404.status_code == 404`
  - `resp_404.json()["error"] == "Endpoint not found"`

---

## 5. Verification Method

### Test Suite Execution Setup
To independently verify these test specifications once M4 and M5 implementation code is created:

1. **Target File Locations**:
   - `tests/e2e/tier1_features/test_f15_benchmark_adapters.py`
   - `tests/e2e/tier1_features/test_f16_dual_evaluator.py`
   - `tests/e2e/tier1_features/test_f17_self_correction.py`
   - `tests/e2e/tier1_features/test_f18_omnibench_cli.py`
   - `tests/e2e/tier1_features/test_f19_sqlite_telemetry.py`
   - `tests/e2e/tier1_features/test_f20_screenshot_analytics.py`
   - `tests/e2e/tier1_features/test_f21_web_dashboard.py`

2. **Execution Command**:
   ```bash
   pytest tests/e2e/tier1_features/ -v --tb=short
   ```

3. **Pass Criteria**:
   - 35 test cases executed, 35 passed (0 failures, 0 errors).
   - Code coverage threshold >= 90% across `omnibench/benchmarks/`, `omnibench/evaluators/`, `omnibench/cli/`, `omnibench/telemetry/`, and `omnibench/dashboard/`.
