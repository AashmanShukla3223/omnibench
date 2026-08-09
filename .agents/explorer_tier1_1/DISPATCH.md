# Dispatch for Explorer 1 — Tier 1 E2E Test Suite Design

## Working Directory
/home/oh_my_macos27/OmniBench Computer Use/.agents/explorer_tier1_1

## Context & Files to Read
- /home/oh_my_macos27/OmniBench Computer Use/ORIGINAL_REQUEST.md
- /home/oh_my_macos27/OmniBench Computer Use/PROJECT.md
- /home/oh_my_macos27/OmniBench Computer Use/TEST_INFRA.md

## Mission
Investigate and design the complete specification for Tier 1 Feature Coverage E2E tests (features 1 to 7 out of 21).
Tier 1 requires at least 5 happy-path & core behavior test cases per feature (35 test cases total for features 1-7).
Test cases must be opaque-box, executable via pytest, and test public interfaces, CLI, SDK, and schemas.

Target features:
- F1: ONNX 100M Local Engine (R1)
- F2: Model Preprocessor & KV Cache (R1)
- F3: Gateway Protocol & Schemas (R1)
- F4: External API Adapters (R1)
- F5: Local & Mock Adapters (R1)
- F6: Cascading Decision Router (R1)
- F7: BaseOSDriver Action Primitives (R2)

Write your findings and test specification report to:
/home/oh_my_macos27/OmniBench Computer Use/.agents/explorer_tier1_1/handoff.md

## 2026-08-08T11:14:10Z
Investigate existing code contracts and design detailed E2E test specifications for Tier 1 features F1 through F7 (at least 5 test cases per feature = 35 test cases total). Write your full findings and test specification report to /home/oh_my_macos27/OmniBench Computer Use/.agents/explorer_tier1_1/handoff.md and message back when complete.

