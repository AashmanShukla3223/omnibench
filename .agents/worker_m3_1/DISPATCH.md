## 2026-08-08T11:15:49Z
<USER_REQUEST>
You are worker_m3_1, an implementation worker for Milestone M3 (Visual Grounding & Set-of-Marks Preprocessor).
Your working directory is: /home/oh_my_macos27/OmniBench Computer Use/.agents/worker_m3_1

DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Specification & Design Documents to read FIRST:
- /home/oh_my_macos27/OmniBench Computer Use/ORIGINAL_REQUEST.md
- /home/oh_my_macos27/OmniBench Computer Use/PROJECT.md
- /home/oh_my_macos27/OmniBench Computer Use/.agents/orch_m3_visual/SCOPE.md
- /home/oh_my_macos27/OmniBench Computer Use/.agents/explorer_m3_1/analysis.md
- /home/oh_my_macos27/OmniBench Computer Use/.agents/explorer_m3_2_gen1/analysis.md
- /home/oh_my_macos27/OmniBench Computer Use/.agents/explorer_m3_3/analysis.md

Write Ownership:
You have exclusive write ownership of:
- `omnibench/visual/__init__.py`
- `omnibench/visual/processing.py`
- `omnibench/visual/memory.py`
- `omnibench/visual/som.py`
- `tests/unit/test_visual.py`

Implementation Tasks:
1. `omnibench/visual/processing.py`: Implement `ImageResizer` (resizing with/without aspect ratio preservation, downscaling, grid tiling, pixel coordinate scaling/mapping) and `ColorConverter` (RGB, Grayscale 1-channel & 3-channel, RGBA composite blending).
2. `omnibench/visual/memory.py`: Implement `MemoryState` dataclass (screenshots list max len 3, action logs list, total steps, `to_dict`/`from_dict` JSON serialization with base64 PNG) and `SlidingTrajectoryMemory` (strictly bounded 3-screenshot deque FIFO eviction, full text action log history, `add_step(screenshot, action_str)`).
3. `omnibench/visual/som.py`: Implement `MarkMap` (center coordinates, exact bbox, reverse point-in-box spatial lookup, `to_dict`/`from_dict`, KeyError on invalid IDs) and `SoMAnnotator` (PIL bounding box & numeric badge overlay drawing with high contrast colors, non-mutating copy, fallback uniform grid when elements=None).
4. `omnibench/visual/__init__.py`: Export `ImageResizer`, `ColorConverter`, `SlidingTrajectoryMemory`, `MemoryState`, `SoMAnnotator`, `MarkMap`.
5. Write unit tests in `tests/unit/test_visual.py` testing every class, method, edge case, serialization/deserialization, invalid input validation, and boundary condition.
6. Execute the unit tests (`pytest tests/unit/test_visual.py` or `python -m pytest`). Ensure ALL tests pass cleanly.
7. Write your handoff report to `/home/oh_my_macos27/OmniBench Computer Use/.agents/worker_m3_1/handoff.md` and progress to `/home/oh_my_macos27/OmniBench Computer Use/.agents/worker_m3_1/progress.md`. Include exact verification commands and pass/fail results.
8. Send a message to parent orchestrator when complete.
</USER_REQUEST>
