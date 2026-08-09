# Dispatch for Worker / Test Writer 1 — Tier 1 Tests (F1 to F7)

## Working Directory
/home/oh_my_macos27/OmniBench Computer Use/.agents/worker_tier1_1

## Context & Files to Read
- /home/oh_my_macos27/OmniBench Computer Use/ORIGINAL_REQUEST.md
- /home/oh_my_macos27/OmniBench Computer Use/PROJECT.md
- /home/oh_my_macos27/OmniBench Computer Use/TEST_INFRA.md
- /home/oh_my_macos27/OmniBench Computer Use/.agents/explorer_tier1_1/handoff.md

## Assigned File Ownership (Exclusive)
`tests/e2e/tier1_features/test_f01_f07.py`

## Mission
Write 35 executable Pytest test cases covering Tier 1 Features F1 to F7 (5 test cases per feature: F1 ONNX Engine, F2 Preprocessor & KV Cache, F3 Gateway Protocol, F4 External Adapters, F5 Local & Mock Adapters, F6 Cascading Router, F7 BaseOSDriver Action Primitives) exactly per the test specifications in `explorer_tier1_1/handoff.md`.
All tests must be executable with pytest and pass cleanly.
Run pytest to verify your tests pass before submitting your handoff.

## MANDATORY INTEGRITY WARNING
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
