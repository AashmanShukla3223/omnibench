# E2E Test Infra: OmniBench 1.0

## Test Philosophy
- Opaque-box, requirement-driven. Derived from `ORIGINAL_REQUEST.md`. No dependency on implementation internals.
- Methodology: Category-Partition + BVA + Pairwise Combinatorial Testing + Real-World Workload Testing.

## Feature Inventory & Test Coverage Target
| # | Feature | Requirement | Tier 1 Target | Tier 2 Target | Tier 3 Target |
|---|---------|-------------|:-------------:|:-------------:|:-------------:|
| 1 | ONNX 100M Engine | R1 | 5 | 5 | ✓ |
| 2 | Model Preprocessor & KV Cache | R1 | 5 | 5 | ✓ |
| 3 | Gateway Protocol & Schemas | R1 | 5 | 5 | ✓ |
| 4 | External API Adapters | R1 | 5 | 5 | ✓ |
| 5 | Local & Mock Adapters | R1 | 5 | 5 | ✓ |
| 6 | Cascading Decision Router | R1 | 5 | 5 | ✓ |
| 7 | BaseOSDriver Action Primitives | R2 | 5 | 5 | ✓ |
| 8 | Desktop OS Drivers | R2 | 5 | 5 | ✓ |
| 9 | Mobile OS Drivers | R2 | 5 | 5 | ✓ |
| 10 | Error Backoff & Retries | R2 | 5 | 5 | ✓ |
| 11 | Screen Processing (Resize/Tile) | R3 | 5 | 5 | ✓ |
| 12 | Sliding Trajectory Memory | R3 | 5 | 5 | ✓ |
| 13 | Set-of-Marks (SoM) Generator | R3 | 5 | 5 | ✓ |
| 14 | Task Execution Runner | R4 | 5 | 5 | ✓ |
| 15 | Benchmark Adapters (6 domains) | R4 | 5 | 5 | ✓ |
| 16 | Dual Evaluator Engine | R4 | 5 | 5 | ✓ |
| 17 | Self-Correction Handlers | R4 | 5 | 5 | ✓ |
| 18 | `omnibench` CLI | R5 | 5 | 5 | ✓ |
| 19 | SQLite Telemetry Logging | R5 | 5 | 5 | ✓ |
| 20 | Screenshot Diff Analytics | R5 | 5 | 5 | ✓ |
| 21 | Web Dashboard UI | R5 | 5 | 5 | ✓ |

## Test Architecture
- **Test Runner**: Pytest execution framework (`pytest tests/e2e`).
- **Test Format**: Standardized test cases verifying CLI commands, HTTP/SSE API endpoints, Python SDK imports, and benchmark task evaluation assertion outputs.
- **Directory Layout**: `tests/e2e/tier1_features/`, `tests/e2e/tier2_boundaries/`, `tests/e2e/tier3_combinations/`, `tests/e2e/tier4_workloads/`.

## Real-World Application Scenarios (Tier 4)
| # | Scenario | Features Exercised | Complexity |
|---|----------|--------------------|------------|
| 1 | Full OSWorld Desktop Task Trajectory | Drivers, Visual SoM, Dual Evaluator, SQLite Telemetry | High |
| 2 | WebArena Form Filling & E-Commerce Flow | Gateway Router, Web Driver, Visual Diffing, CLI | High |
| 3 | AndroidWorld App Navigation | Mobile Driver, Sliding Memory, SoM MarkMap, Evaluator | High |
| 4 | Mind2Web Web Search & Extraction | Gateway, SoM Generator, System Assertions, SQLite | Medium |
| 5 | GAIA Multi-Step Reasoning & Tool Execution | ONNX Engine, Gateway Cascading, Self-Correction | High |
| 6 | OmniBench Native End-to-End Benchmark Suite | All system components (R1 - R5) integrated | High |

## Coverage Thresholds
- Tier 1: ≥5 per feature (21 features × 5 = 105 tests)
- Tier 2: ≥5 per feature boundary/corner case (21 features × 5 = 105 tests)
- Tier 3: ≥21 pairwise feature interaction test cases
- Tier 4: ≥6 realistic application scenarios
- **Total Minimum Test Cases**: 237 test cases
