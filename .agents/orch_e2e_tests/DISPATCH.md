# Scope: E2E Testing Track
Parent Orchestrator Conversation ID: 56ba8294-13aa-4aec-878c-ea8d969fa715
Working Directory: /home/oh_my_macos27/OmniBench Computer Use/.agents/orch_e2e_tests

## Mission
Orchestrate the design and implementation of the complete opaque-box E2E test suite for OmniBench 1.0 per `TEST_INFRA.md`.

## Requirements
- Requirement-driven, opaque-box test suite based on `ORIGINAL_REQUEST.md` and `PROJECT.md`.
- Implement test cases in `tests/e2e/`:
  - Tier 1: Feature Coverage (≥105 test cases, ≥5 per feature)
  - Tier 2: Boundary & Corner Cases (≥105 test cases, ≥5 per feature boundary)
  - Tier 3: Cross-Feature Interactions (≥21 test cases)
  - Tier 4: Real-World Scenarios (≥6 application-level scenarios)
- Output: Executable pytest test suite under `tests/e2e/`.
- Publish `TEST_READY.md` at project root when complete.

## Instructions
1. Read `/home/oh_my_macos27/OmniBench Computer Use/ORIGINAL_REQUEST.md`, `/home/oh_my_macos27/OmniBench Computer Use/PROJECT.md`, and `/home/oh_my_macos27/OmniBench Computer Use/TEST_INFRA.md`.
2. Apply the Iteration Loop (Explorer -> Worker (or test_writer) -> Reviewer -> Challenger -> Auditor -> Gate) to build the test suite.
3. Verify test cases can be run via `pytest tests/e2e`.
4. Publish `TEST_READY.md` at project root summarizing test count and coverage.
5. Report completion to parent.
