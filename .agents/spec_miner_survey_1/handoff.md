# Handoff Report — Specification Mining for Requirement R4 (Benchmark Evaluation & Verification Engine)

**Agent**: `spec_miner_survey_1`  
**Date**: 2026-08-08  
**Handoff Type**: Hard  
**Target Path**: `/home/oh_my_macos27/OmniBench Computer Use/.agents/spec_miner_survey_1/handoff.md`

---

## 1. Observation

1. **Workspace Root & Requirements**:
   - `ORIGINAL_REQUEST.md` line 21-22:
     > "### R4. Benchmark Evaluation & Verification Engine
     > Evaluation runner for OSWorld, WebArena, AndroidWorld, Mind2Web, GAIA, and native OmniBench benchmark tasks using dual evaluators (visual state diffing + system CLI/API state assertions) with automatic self-correction & retry handlers."
   - `ORIGINAL_REQUEST.md` line 33:
     > "- [ ] Benchmarks evaluate state correctness via dual visual & system state assertions and output detailed SQLite results."

2. **File Structure**:
   - `list_dir` on `/home/oh_my_macos27/OmniBench Computer Use` confirmed only `.agents/` directory and `ORIGINAL_REQUEST.md` currently exist in root.
   - `find_by_name` returned `ORIGINAL_REQUEST.md` as the sole top-level non-agent file.

3. **Specification Mining Output**:
   - Written comprehensive specification analysis to `/home/oh_my_macos27/OmniBench Computer Use/.agents/spec_miner_survey_1/analysis.md` (305 lines).

---

## 2. Logic Chain

1. **Requirement Analysis**: R4 mandates a benchmark evaluation runner for 6 benchmark families (OSWorld, WebArena, AndroidWorld, Mind2Web, GAIA, native OmniBench), dual evaluators combining visual state diffing and system assertions, self-correction/retries, and trajectory logging.
2. **Schema & Contract Definition**: Standardizing task representations via JSON schema allows uniform execution across heterogeneous desktop, web, and mobile environments.
3. **Dual Evaluator Protocol**: Visual state diffing (SSIM, pHash, ROI masking, OCR text matching) and system CLI/API assertions (shell output, HTTP status/JSONPath, file SHA256 hashes, web DOM inspection) provide robust, cheat-resistant task verification under 4 aggregation modes (`AND`, `OR`, `WEIGHTED`, `FALLBACK`).
4. **Resilience Architecture**: Level 1 retry with exponential backoff handles transient UI/driver glitches; Level 2 visual stagnation detection triggers feedback injection into VLM drivers for self-correction.
5. **Testing Strategy**: Structured Tiers 1-4 guarantee component-level accuracy, runner integration, 30-task benchmark family sub-suite validation, and end-to-end suite evaluation.

---

## 3. Caveats

- **External Benchmark Adapters**: When integrating live benchmarks (e.g. OSWorld or WebArena docker containers), the evaluation engine requires environment containers or API endpoints to be running on the host or network.
- **Hardware OCR Availability**: Tier 1 OCR diffing defaults to Tesseract/EasyOCR fallback when GPU acceleration is unavailable.

---

## 4. Conclusion

Requirement R4 is fully specified in `/home/oh_my_macos27/OmniBench Computer Use/.agents/spec_miner_survey_1/analysis.md`. The document provides:
- Benchmark domain breakdown for OSWorld, WebArena, AndroidWorld, Mind2Web, GAIA, and native OmniBench.
- Complete JSON task schema and JSONPath/evaluator contracts.
- Formal visual diffing algorithms (SSIM, pHash, ROI, OCR) and system assertion specifications.
- Dual evaluator aggregation rules (`AND`/`OR`/`WEIGHTED`/`FALLBACK`).
- Two-level auto-retry & visual self-correction specifications.
- Benchmark runner event loop architecture (`BenchmarkRunner`).
- 16 Discovered Features and 8 Edge Cases tables.
- 4-Tier test suite design (Tiers 1-4).

---

## 5. Verification Method

To verify this handoff:
1. Inspect the detailed report file:
   `view_file /home/oh_my_macos27/OmniBench\ Computer\ Use/.agents/spec_miner_survey_1/analysis.md`
2. Confirm the presence of:
   - All 6 benchmark families (OSWorld, WebArena, AndroidWorld, Mind2Web, GAIA, OmniBench native)
   - Dual evaluators (visual state diffing + system assertions)
   - Self-correction and retry mechanisms
   - Features Discovered table (16 entries)
   - Edge Cases table (8 entries)
   - Tiers 1-4 test suite design
3. Invalidation conditions: Any missing benchmark family or evaluator type invalidates full coverage.
