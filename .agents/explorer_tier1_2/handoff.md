# Handoff Report: Tier 1 E2E Test Specification (Features F8 to F14)

**Agent ID**: `explorer_tier1_2`  
**Working Directory**: `/home/oh_my_macos27/OmniBench Computer Use/.agents/explorer_tier1_2`  
**Handoff Type**: Hard Handoff  
**Target Scope**: Tier 1 Features F8 through F14 (35 Test Cases Total)

---

## 1. Observation

1. **System & Working Environment**:
   - Directory: `/home/oh_my_macos27/OmniBench Computer Use`
   - Agent Directory: `/home/oh_my_macos27/OmniBench Computer Use/.agents/explorer_tier1_2`
   - Python Version: `3.13.5`
   - Core Dependencies Installed: `onnxruntime` (1.28.0), `pydantic` (2.13.4), `httpx` (0.28.1), `numpy` (2.5.1), `pillow` (12.3.0), `psutil` (7.2.2), `click` (8.1.8).
   - Display Utilities: `/usr/bin/Xvfb` (X11 Virtual Framebuffer).

2. **Project Specification Files Inspected**:
   - `ORIGINAL_REQUEST.md`: R2 (Cross-Platform OS Automation Drivers), R3 (Visual Grounding & SoM Preprocessor), R4 (Benchmark Evaluation Engine).
   - `PROJECT.md`: Lines 20-27 (Feature Inventory F8 to F14), Lines 54-63 (Interface contracts for `omnibench.drivers`, `omnibench.visual`, `omnibench.benchmarks`), Lines 84-114 (Code layout).
   - `TEST_INFRA.md`: Lines 17-23 (Feature coverage target: 5 Tier 1 happy-path tests per feature for F8 to F14), Line 35 (Directory layout: `tests/e2e/tier1_features/`), Line 48 (Tier 1 threshold: ≥5 per feature).
   - `DISPATCH.md`: Mission dispatch instructing design of 35 opaque-box Tier 1 E2E test cases for F8 through F14.

3. **Interface Contracts & Feature Specifications (Surveys & Architecture)**:
   - **Feature 8 (Desktop OS Drivers - Linux, Windows, macOS)**: `BaseOSDriver.execute_action(action_type: str, params: dict) -> ActionResult`, `BaseOSDriver.capture_screenshot() -> PIL.Image`. Action primitives: `click`, `double_click`, `right_click`, `drag`, `type`, `key_combination`, `scroll`, `wait`. Linux uses `Xvfb`/`xdotool`, Windows uses `pywinauto`/PowerShell, macOS uses `CoreGraphics`/AppleScript.
   - **Feature 9 (Mobile OS Drivers - Android, iOS)**: `AndroidOSDriver` uses ADB/uiautomator (`adb shell input tap/swipe/text/keyevent`), `IOSDriver` uses `simctl`/WDA REST API. Screenshot via `adb exec-out screencap -p` and `simctl io screenshot`.
   - **Feature 10 (Error Retry & Backoff)**: Decorator `@retry_with_backoff(max_retries=3, initial_delay=0.5, backoff_factor=2.0, jitter=True)`. Exponential delay sequence ($0.5s \rightarrow 1.0s \rightarrow 2.0s$) capped at max delay with $\pm 10\%$ random jitter. Reconnection check via `health_check()` and `reconnect()`.
   - **Feature 11 (Screen Processing Pipeline)**: `ScreenProcessor.process(image, mode, max_dimension, color_space, tile_grid) -> ScreenProcessResult`. Support downscaling to max dimensions (e.g. 1024x1024), 2x2/3x3 grid tiling with spatial bounding boxes, RGB to Grayscale conversion, and coordinate translation (`global_to_tile`, `tile_to_global`).
   - **Feature 12 (Sliding Trajectory Memory)**: `SlidingTrajectoryMemory(capacity=3)`. Methods: `add_step()`, `get_history()`, `clear()`, `get_memory_state()`. Strictly bounded FIFO queue retaining latest 3 screenshots/turns while preserving action summary text logs.
   - **Feature 13 (Set-of-Marks Generator)**: `SoMAnnotator.annotate(screenshot, bboxes) -> tuple[PIL.Image, MarkMap]`. Renders semi-transparent bounding boxes and numeric badges (`[1]`, `[2]`). Bidirectional `MarkMap`: `get_coordinates(mark_id) -> (x, y)`, `get_bbox(mark_id) -> (xmin, ymin, xmax, ymax)`, `get_mark_by_coords(x, y) -> mark_id | None`.
   - **Feature 14 (Task Execution Runner)**: `TaskSchema` (JSON task parser with Pydantic validation) and `BenchmarkRunner(driver, gateway, memory, evaluator).run_task(task) -> TaskRunResult`. Event loop executing step cycle up to `max_steps`, updating trajectory, handling driver calls and stopping conditions.

---

## 2. Logic Chain

1. **Step 1 (From Observation 1 & 2)**: `TEST_INFRA.md` requires 5 opaque-box, requirement-driven Tier 1 test cases for each of the 7 assigned features (F8 to F14), totaling 35 test cases. Tier 1 focuses on happy-path execution, core behavior, parameter handling, schema parsing, and interface contract compliance.
2. **Step 2 (From Observation 3 - F8 & F9)**: Desktop and Mobile OS drivers must be tested for executing standard primitives (`click`, `double_click`, `right_click`, `drag`, `type`, `key_combination`, `scroll`, `wait`), capturing screenshots, scaling coordinates (e.g., Retina 2x multiplier), and handling invalid coordinate bounds.
3. **Step 3 (From Observation 3 - F10)**: The retry and backoff decorator must be tested for exponential timing growth, random jitter calculation, max retries exhaustion, automatic daemon reconnection triggers, non-retryable exception passthrough, and zero-delay immediate success.
4. **Step 4 (From Observation 3 - F11 & F12)**: Visual processing tests require verifying downscaling aspect ratios, 2x2 grid tile bounding box math, spatial coordinate transformations, color space transformations (RGB $\leftrightarrow$ Grayscale), FIFO eviction when exceeding capacity 3, text summary log persistence, and memory state reset.
5. **Step 5 (From Observation 3 - F13 & F14)**: SoM generator tests require verifying badge rendering on PIL images, forward and reverse `MarkMap` queries, out-of-bounds coordinate handling, and `KeyError` on missing mark IDs. Task runner tests require validating `TaskSchema` JSON parsing, complete event loop execution, max steps termination, driver action dispatching, and unhandled exception status reporting.
6. **Step 6 (Synthesis)**: Formulated 35 concrete, executable test specifications across 7 features (F8-F14) in `tests/e2e/tier1_features/`.

---

## 3. Caveats

1. **Host OS Driver Execution Modes**: On Linux host machines without connected Android/iOS devices or physical Windows/macOS installations, mobile and non-Linux drivers will run using platform mock/simulator adapters to verify interface contracts without requiring external hardware hardware bridges.
2. **Synthetic Image Fixtures**: Visual processing and SoM tests use synthetic PIL Image fixtures (e.g., solid color or geometric test patterns created dynamically with PIL `Image.new()`) to maintain fast, deterministic test execution without network dependency.
3. **Implementation Pending**: The codebase under `omnibench/` is in the test-driven specification phase. Test cases are specified against contract interfaces (`BaseOSDriver`, `ScreenProcessor`, `SlidingTrajectoryMemory`, `SoMAnnotator`, `MarkMap`, `BenchmarkRunner`) defined in `PROJECT.md`.

---

## 4. Conclusion & Complete E2E Test Specifications (35 Test Cases)

### Feature 8: Desktop OS Drivers (F08)
- **TEST-E2E-F08-001: Linux Driver Action Execution (Xvfb / xdotool)**
  - *Objective*: Verify `LinuxOSDriver` executes standard action primitives (`click`, `double_click`, `right_click`, `drag`, `type`, `key_combination`, `scroll`, `wait`).
  - *Input*: `action_type="click"`, `params={"x": 100, "y": 200, "button": "left"}`.
  - *Expected Result*: `ActionResult.success == True`, `execution_time_ms > 0`, `error_message == None`.
- **TEST-E2E-F08-002: Windows Driver Action Execution Contract**
  - *Objective*: Verify `WindowsOSDriver` validates action parameters and executes actions via platform adapter.
  - *Input*: `action_type="type"`, `params={"text": "Hello OmniBench", "interval": 0.01}`.
  - *Expected Result*: `ActionResult.success == True`, action recorded with matching parameters.
- **TEST-E2E-F08-003: macOS Driver Coordinate Scaling & Execution**
  - *Objective*: Verify `MacOSDriver` handles Retina display coordinate scaling (points to pixels multiplier).
  - *Input*: `action_type="click"`, `params={"x": 500, "y": 400}`, scaling factor `2.0`.
  - *Expected Result*: Scaled click executed at `(1000, 800)` screen pixels, `ActionResult.success == True`.
- **TEST-E2E-F08-004: Desktop Driver Screenshot Capture**
  - *Objective*: Verify `capture_screenshot()` on desktop drivers returns a valid RGB PIL Image.
  - *Input*: `driver.capture_screenshot()`.
  - *Expected Result*: Returns `PIL.Image.Image` instance, `mode == "RGB"`, `width > 0`, `height > 0`.
- **TEST-E2E-F08-005: Desktop Driver Out-of-Bounds Coordinate Handling**
  - *Objective*: Verify driver handles out-of-bounds screen coordinates gracefully.
  - *Input*: `action_type="click"`, `params={"x": -50, "y": 99999}` on a 1920x1080 display.
  - *Expected Result*: Raises `CoordinatesOutOfBoundsError` or returns `ActionResult(success=False)`.

### Feature 9: Mobile OS Drivers (F09)
- **TEST-E2E-F09-001: Android Driver Tap and Swipe Primitives**
  - *Objective*: Verify `AndroidOSDriver` translates `click` and `drag` into ADB `input tap` and `input swipe`.
  - *Input*: `click(x=300, y=600)` and `drag(start_x=100, start_y=500, end_x=100, end_y=100)`.
  - *Expected Result*: ADB commands dispatched correctly, returning `ActionResult(success=True)`.
- **TEST-E2E-F09-002: Android Driver Text Input & Keyevent Injection**
  - *Objective*: Verify `AndroidOSDriver` executes text injection and keyevents (`KEYCODE_BACK=4`).
  - *Input*: `type(text="search text")` and `key_combination(keys=["KEYCODE_BACK"])`.
  - *Expected Result*: ADB input commands formatted with string escaping, `ActionResult(success=True)`.
- **TEST-E2E-F09-003: iOS Driver Touch & Drag Execution**
  - *Objective*: Verify `IOSDriver` touch and swipe execution via `simctl` / WDA HTTP endpoint.
  - *Input*: `click(x=200, y=400)` on iOS simulator target.
  - *Expected Result*: Returns `ActionResult.success == True`, duration logged.
- **TEST-E2E-F09-004: Mobile Driver Screencap Capture**
  - *Objective*: Verify mobile screenshot capture via `adb exec-out screencap -p` and `simctl io screenshot`.
  - *Input*: `mobile_driver.capture_screenshot()`.
  - *Expected Result*: Decodes raw PNG byte stream into PIL Image object.
- **TEST-E2E-F09-005: Mobile Driver Disconnect Detection & Timeout**
  - *Objective*: Verify mobile driver detects lost ADB/WDA daemon connection.
  - *Input*: Trigger action while daemon process is unreachable.
  - *Expected Result*: `health_check()` returns `False`, driver attempts reconnection or raises `ConnectionTimeoutError`.

### Feature 10: Error Retry & Backoff (F10)
- **TEST-E2E-F10-001: Exponential Backoff Timing and Jitter Calculation**
  - *Objective*: Verify `@retry_with_backoff` increases delay exponentially ($0.1s \rightarrow 0.2s \rightarrow 0.4s$) with random jitter.
  - *Input*: Decorated function failing 2 times before succeeding on 3rd try with `initial_delay=0.1, backoff_factor=2.0`.
  - *Expected Result*: Total sleep time strictly within expected jitter window ($0.3s \pm 0.05s$), returns result with `retry_count=2`.
- **TEST-E2E-F10-002: Max Retries Exhaustion Exception Propagation**
  - *Objective*: Verify decorator stops after `max_retries` attempts and re-raises the underlying exception.
  - *Input*: Function throwing `ActionExecutionError` on every call, `max_retries=3`.
  - *Expected Result*: Total invocations == 3, raises `ActionExecutionError`.
- **TEST-E2E-F10-003: Transient Connection Failure Auto-Reconnection**
  - *Objective*: Verify decorator invokes driver `reconnect()` when catching `ConnectionTimeoutError`.
  - *Input*: 1st call raises `ConnectionTimeoutError`, causing `reconnect()` call, 2nd call succeeds.
  - *Expected Result*: `driver.reconnect()` called once, action returns `ActionResult(success=True)`.
- **TEST-E2E-F10-004: Non-Retryable Exception Immediate Failure**
  - *Objective*: Verify non-retryable exceptions (e.g. `PlatformNotSupportedError`) bypass retries.
  - *Input*: Function throwing `PlatformNotSupportedError` on 1st call.
  - *Expected Result*: Instantly raises exception, call count == 1, 0 delay.
- **TEST-E2E-F10-005: Zero-Delay Immediate Success**
  - *Objective*: Verify successful function calls return immediately without sleep overhead.
  - *Input*: Healthy function returning `ActionResult(success=True)` on 1st attempt.
  - *Expected Result*: Execution time < 5ms, sleep time == 0, `retry_count=0`.

### Feature 11: Screen Processing Pipeline (F11)
- **TEST-E2E-F11-001: Downscaling Image Normalization**
  - *Objective*: Downscale 3840x2160 screenshot to max bounds `(1024, 1024)` preserving aspect ratio.
  - *Input*: PIL Image (3840, 2160), `mode="downscale"`, `max_dimension=(1024, 1024)`.
  - *Expected Result*: Output PIL Image size == `(1024, 576)`, aspect ratio preserved ($16:9$).
- **TEST-E2E-F11-002: Grid Tiling Image Decomposition**
  - *Objective*: Split high-res image into a 2x2 grid of tiles with spatial bounding boxes.
  - *Input*: PIL Image (2000, 1000), `mode="tile"`, `tile_grid=(2, 2)`.
  - *Expected Result*: Returns list of 4 tile tuple items `(tile_img, (xmin, ymin, xmax, ymax))`, each size `(1000, 500)`.
- **TEST-E2E-F11-003: Spatial Coordinate Translation (Global <-> Tile)**
  - *Objective*: Verify point translation between global screenshot and localized tile coordinates.
  - *Input*: Global point `(1500, 800)` on 2000x1000 image, tile (1, 1) rect `(1000, 500, 2000, 1000)`.
  - *Expected Result*: `global_to_tile` yields `(500, 300)`; `tile_to_global(500, 300)` yields `(1500, 800)`.
- **TEST-E2E-F11-004: Color Space Conversion (RGB to Grayscale)**
  - *Objective*: Convert RGB screenshot to single-channel Grayscale (`L` mode).
  - *Input*: RGB PIL Image, `color_space="L"`.
  - *Expected Result*: Output image `mode == "L"`, single channel array data.
- **TEST-E2E-F11-005: ScreenProcessor Result Metadata Specification**
  - *Objective*: Verify `ScreenProcessResult` includes complete execution metadata.
  - *Input*: `ScreenProcessor.process(img, mode="downscale", max_dimension=(800, 800))`.
  - *Expected Result*: `ScreenProcessResult.metadata` contains `original_size`, `new_size`, `scale_factor`, `color_space`.

### Feature 12: Sliding Trajectory Memory (F12)
- **TEST-E2E-F12-001: Memory Initialization and Step Addition**
  - *Objective*: Verify adding a step to `SlidingTrajectoryMemory(capacity=3)` records step data.
  - *Input*: `add_step(screenshot=img1, action_str="CLICK [1]")`.
  - *Expected Result*: `get_history()` length == 1, total_steps == 1.
- **TEST-E2E-F12-002: Capacity Bounded FIFO Eviction**
  - *Objective*: Verify adding 4 steps to capacity=3 memory evicts the 1st step.
  - *Input*: Add Step 1, Step 2, Step 3, Step 4 in order.
  - *Expected Result*: `get_history()` contains exactly 3 steps: Step 2, Step 3, Step 4. Step 1 screenshot is evicted.
- **TEST-E2E-F12-003: Action Text Summary History Retention**
  - *Objective*: Verify text action log history retains full trajectory context even after image eviction.
  - *Input*: Query `get_action_log_history()` after adding 5 steps to memory.
  - *Expected Result*: Returns list of 5 text summary strings ("Step 1: ...", ..., "Step 5: ...").
- **TEST-E2E-F12-004: Memory Clear State Reset**
  - *Objective*: Verify `clear()` resets history list and step counter.
  - *Input*: Call `clear()` on memory containing 3 turns.
  - *Expected Result*: `get_history() == []`, total_steps == 0, image memory released.
- **TEST-E2E-F12-005: Memory State Snapshot Data Contract**
  - *Objective*: Verify `get_memory_state()` returns structured `MemoryState` object.
  - *Input*: `memory.get_memory_state()`.
  - *Expected Result*: `MemoryState.capacity == 3`, `MemoryState.current_size == 3`, `screenshots` list length == 3.

### Feature 13: Set-of-Marks (SoM) Generator (F13)
- **TEST-E2E-F13-001: Bounding Box Badge Overlay Rendering**
  - *Objective*: Verify `SoMAnnotator.annotate()` draws bounding boxes with badge numbers on screenshot.
  - *Input*: 800x600 screenshot, bounding boxes `[{"bbox": (100, 100, 200, 150), "label": "button"}]`.
  - *Expected Result*: Returns `(annotated_img, mark_map)` where annotated image has dimensions 800x600 and updated pixel colors around box.
- **TEST-E2E-F13-002: MarkMap Forward Center Coordinate Query**
  - *Objective*: Verify `MarkMap.get_coordinates(mark_id)` returns center point of bounding box.
  - *Input*: Register mark ID 1 with bbox `(100, 200, 300, 400)`.
  - *Expected Result*: `get_coordinates(1)` returns `(200, 300)`.
- **TEST-E2E-F13-003: MarkMap Bounding Box Query**
  - *Objective*: Verify `MarkMap.get_bbox(mark_id)` returns full bounding box rectangle.
  - *Input*: Register mark ID 2 with bbox `(50, 50, 150, 100)`.
  - *Expected Result*: `get_bbox(2)` returns `(50, 50, 150, 100)`.
- **TEST-E2E-F13-004: Reverse Coordinate to Mark Lookup**
  - *Objective*: Verify `MarkMap.get_mark_by_coords(x, y)` identifies mark enclosing coordinates.
  - *Input*: Query point `(75, 75)` and `(500, 500)` against registered mark ID 2 `(50, 50, 150, 100)`.
  - *Expected Result*: `get_mark_by_coords(75, 75) == 2`, `get_mark_by_coords(500, 500) == None`.
- **TEST-E2E-F13-005: Unregistered Mark ID KeyError Handling**
  - *Objective*: Verify querying non-existent mark ID raises `KeyError`.
  - *Input*: `MarkMap.get_coordinates(999)`.
  - *Expected Result*: Raises `KeyError` with descriptive error string.

### Feature 14: Task Execution Runner (F14)
- **TEST-E2E-F14-001: TaskSchema JSON Validation**
  - *Objective*: Verify Pydantic validation for benchmark JSON task definitions.
  - *Input*: Valid JSON string vs invalid JSON string (missing `task_id`).
  - *Expected Result*: Valid JSON parses to `TaskSchema` instance; invalid JSON raises `pydantic.ValidationError`.
- **TEST-E2E-F14-002: BenchmarkRunner Event Loop Successful Trajectory**
  - *Objective*: Verify `BenchmarkRunner` completes event loop when evaluator passes.
  - *Input*: Task with `max_steps=5`, mock gateway returns valid actions, evaluator passes on step 2.
  - *Expected Result*: `TaskRunResult.status == "success"`, `steps_executed == 2`, trajectory length == 2.
- **TEST-E2E-F14-003: BenchmarkRunner Max Steps Boundary Termination**
  - *Objective*: Verify event loop terminates when reaching `max_steps`.
  - *Input*: Task with `max_steps=3`, evaluator never passes.
  - *Expected Result*: `TaskRunResult.status == "max_steps_exceeded"`, `steps_executed == 3`.
- **TEST-E2E-F14-004: BenchmarkRunner Driver Action Dispatch Integration**
  - *Objective*: Verify runner dispatches parsed action from gateway to driver.
  - *Input*: Gateway returns action `click(x=150, y=250)`.
  - *Expected Result*: `driver.execute_action()` invoked with `"click"` and `{"x": 150, "y": 250}`, result stored in trajectory.
- **TEST-E2E-F14-005: BenchmarkRunner Exception Handling & Status Reporting**
  - *Objective*: Verify runner catches unhandled driver exceptions and returns error status.
  - *Input*: Driver raises `DriverException("Display lost")` during step 1.
  - *Expected Result*: `TaskRunResult.status == "error"`, `TaskRunResult.error_message` contains `"Display lost"`.

---

## 5. Verification Method

To verify these test specifications against the project architecture:

1. **Verify Test File Structure**:
   ```bash
   ls -la /home/oh_my_macos27/OmniBench\ Computer\ Use/.agents/explorer_tier1_2/handoff.md
   ```
2. **Count Test Specifications**:
   - Total test cases documented: **35 test cases** (7 features $\times$ 5 test cases per feature).
3. **Pytest Test Execution Command**:
   When implementing tests in `tests/e2e/tier1_features/test_f08_f14.py`:
   ```bash
   .venv/bin/pytest tests/e2e/tier1_features/ -k "test_f08 or test_f09 or test_f10 or test_f11 or test_f12 or test_f13 or test_f14" -v
   ```
