# Scope: E2E Testing Track — OmniBench 1.0

## Architecture & Testing Philosophy
- **Approach**: Opaque-box, requirement-driven E2E test suite constructed directly from `ORIGINAL_REQUEST.md` and standard specification `TEST_INFRA.md`.
- **Framework**: Standard Pytest suite (`pytest tests/e2e`).
- **Target Directories**:
  - `tests/e2e/tier1_features/`: Tier 1 Feature Coverage (21 features × 5 = 105 tests)
  - `tests/e2e/tier2_boundaries/`: Tier 2 Boundary & Corner Cases (21 features × 5 = 105 tests)
  - `tests/e2e/tier3_combinations/`: Tier 3 Cross-Feature Interactions (21 pairwise tests)
  - `tests/e2e/tier4_workloads/`: Tier 4 Real-World Workload Scenarios (6 scenario tests)

## Feature Inventory & Milestones Mapping
| # | Feature | Requirement | Tier 1 (5 tests) | Tier 2 (5 tests) | Tier 3 (Pairwise) | Tier 4 (Workloads) |
|---|---------|-------------|:----------------:|:----------------:|:-----------------:|:------------------:|
| 1 | ONNX 100M Engine | R1 | M_E2E_T1 | M_E2E_T2 | M_E2E_T3 | M_E2E_T4 (GAIA/Native) |
| 2 | Model Preprocessor & KV Cache | R1 | M_E2E_T1 | M_E2E_T2 | M_E2E_T3 | M_E2E_T4 (GAIA) |
| 3 | Gateway Protocol & Schemas | R1 | M_E2E_T1 | M_E2E_T2 | M_E2E_T3 | M_E2E_T4 (WebArena/Mind2Web) |
| 4 | External API Adapters | R1 | M_E2E_T1 | M_E2E_T2 | M_E2E_T3 | M_E2E_T4 (Mind2Web) |
| 5 | Local & Mock Adapters | R1 | M_E2E_T1 | M_E2E_T2 | M_E2E_T3 | M_E2E_T4 (Native) |
| 6 | Cascading Decision Router | R1 | M_E2E_T1 | M_E2E_T2 | M_E2E_T3 | M_E2E_T4 (WebArena/GAIA) |
| 7 | BaseOSDriver Action Primitives | R2 | M_E2E_T1 | M_E2E_T2 | M_E2E_T3 | M_E2E_T4 (OSWorld) |
| 8 | Desktop OS Drivers | R2 | M_E2E_T1 | M_E2E_T2 | M_E2E_T3 | M_E2E_T4 (OSWorld) |
| 9 | Mobile OS Drivers | R2 | M_E2E_T1 | M_E2E_T2 | M_E2E_T3 | M_E2E_T4 (AndroidWorld) |
| 10 | Error Backoff & Retries | R2 | M_E2E_T1 | M_E2E_T2 | M_E2E_T3 | M_E2E_T4 (Native) |
| 11 | Screen Processing (Resize/Tile) | R3 | M_E2E_T1 | M_E2E_T2 | M_E2E_T3 | M_E2E_T4 (OSWorld) |
| 12 | Sliding Trajectory Memory | R3 | M_E2E_T1 | M_E2E_T2 | M_E2E_T3 | M_E2E_T4 (AndroidWorld) |
| 13 | Set-of-Marks (SoM) Generator | R3 | M_E2E_T1 | M_E2E_T2 | M_E2E_T3 | M_E2E_T4 (OSWorld/AndroidWorld) |
| 14 | Task Execution Runner | R4 | M_E2E_T1 | M_E2E_T2 | M_E2E_T3 | M_E2E_T4 (All) |
| 15 | Benchmark Adapters (6 domains) | R4 | M_E2E_T1 | M_E2E_T2 | M_E2E_T3 | M_E2E_T4 (All) |
| 16 | Dual Evaluator Engine | R4 | M_E2E_T1 | M_E2E_T2 | M_E2E_T3 | M_E2E_T4 (OSWorld/WebArena) |
| 17 | Self-Correction Handlers | R4 | M_E2E_T1 | M_E2E_T2 | M_E2E_T3 | M_E2E_T4 (GAIA) |
| 18 | `omnibench` CLI | R5 | M_E2E_T1 | M_E2E_T2 | M_E2E_T3 | M_E2E_T4 (WebArena/Mind2Web) |
| 19 | SQLite Telemetry Logging | R5 | M_E2E_T1 | M_E2E_T2 | M_E2E_T3 | M_E2E_T4 (OSWorld/Mind2Web) |
| 20 | Screenshot Diff Analytics | R5 | M_E2E_T1 | M_E2E_T2 | M_E2E_T3 | M_E2E_T4 (WebArena) |
| 21 | Web Dashboard UI | R5 | M_E2E_T1 | M_E2E_T2 | M_E2E_T3 | M_E2E_T4 (Native) |

## Milestones
| # | Name | Scope | Target Files | Status |
|---|------|-------|--------------|--------|
| M_E2E_T1 | Tier 1 Feature Coverage Tests | 105 test cases (5 per feature across 21 features) | `tests/e2e/tier1_features/test_t1_features_*.py` | PLANNED |
| M_E2E_T2 | Tier 2 Boundary & Corner Cases | 105 test cases (5 per feature boundary/edge) | `tests/e2e/tier2_boundaries/test_t2_boundaries_*.py` | PLANNED |
| M_E2E_T3 | Tier 3 Pairwise Combinations | 21 test cases (pairwise feature interaction scenarios) | `tests/e2e/tier3_combinations/test_t3_combinations.py` | PLANNED |
| M_E2E_T4 | Tier 4 Application Workloads | 6 complex real-world workload scenario tests | `tests/e2e/tier4_workloads/test_t4_workloads.py` | PLANNED |
| M_E2E_READY | E2E Suite Verification & TEST_READY | Full Pytest validation (237 tests) + `TEST_READY.md` | `/home/oh_my_macos27/OmniBench Computer Use/TEST_READY.md` | PLANNED |
