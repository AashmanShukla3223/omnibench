# Dispatch for Explorer 2 — Tier 1 E2E Test Suite Design

## Working Directory
/home/oh_my_macos27/OmniBench Computer Use/.agents/explorer_tier1_2

## Context & Files to Read
- /home/oh_my_macos27/OmniBench Computer Use/ORIGINAL_REQUEST.md
- /home/oh_my_macos27/OmniBench Computer Use/PROJECT.md
- /home/oh_my_macos27/OmniBench Computer Use/TEST_INFRA.md

## Mission
Investigate and design the complete specification for Tier 1 Feature Coverage E2E tests (features 8 to 14 out of 21).
Tier 1 requires at least 5 happy-path & core behavior test cases per feature (35 test cases total for features 8-14).
Test cases must be opaque-box, executable via pytest, and test public interfaces, CLI, SDK, and schemas.

Target features:
- F8: Desktop OS Drivers (Linux, Windows, macOS) (R2)
- F9: Mobile OS Drivers (Android, iOS) (R2)
- F10: Error Retry & Backoff (R2)
- F11: Screen Processing Pipeline (Resize/Tile/Color) (R3)
- F12: Sliding Trajectory Memory (R3)
- F13: Set-of-Marks (SoM) Generator (R3)
- F14: Task Execution Runner (R4)

Write your findings and test specification report to:
/home/oh_my_macos27/OmniBench Computer Use/.agents/explorer_tier1_2/handoff.md

## 2026-08-08T11:14:10Z
Your working directory is /home/oh_my_macos27/OmniBench Computer Use/.agents/explorer_tier1_2. Read /home/oh_my_macos27/OmniBench Computer Use/ORIGINAL_REQUEST.md, /home/oh_my_macos27/OmniBench Computer Use/PROJECT.md, /home/oh_my_macos27/OmniBench Computer Use/TEST_INFRA.md, and /home/oh_my_macos27/OmniBench Computer Use/.agents/explorer_tier1_2/DISPATCH.md.
Investigate existing code contracts and design detailed E2E test specifications for Tier 1 features F8 through F14 (at least 5 test cases per feature = 35 test cases total). Write your full findings and test specification report to /home/oh_my_macos27/OmniBench Computer Use/.agents/explorer_tier1_2/handoff.md and message back when complete.
