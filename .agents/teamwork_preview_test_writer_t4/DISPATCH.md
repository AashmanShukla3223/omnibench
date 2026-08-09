## 2026-08-08T11:17:30Z
You are the Test Writer for Tier 4 Real-World Application Workload Tests of OmniBench 1.0.

Your working directory: /home/oh_my_macos27/OmniBench Computer Use/.agents/teamwork_preview_test_writer_t4
Project root: /home/oh_my_macos27/OmniBench Computer Use

Instructions:
1. Read `/home/oh_my_macos27/OmniBench Computer Use/ORIGINAL_REQUEST.md`, `/home/oh_my_macos27/OmniBench Computer Use/TEST_INFRA.md`, and `/home/oh_my_macos27/OmniBench Computer Use/PROJECT.md`.
2. Write Tier 4 Real-World Application Workload Scenario tests in directory `/home/oh_my_macos27/OmniBench Computer Use/tests/e2e/tier4_workloads/`.
3. You MUST author at least 6 real-world application workload scenario tests:
   Organize into file:
   - `test_t4_workloads.py` (6 workload scenario test cases: OSWorld Desktop Trajectory, WebArena Form Filling & E-Commerce, AndroidWorld App Navigation, Mind2Web Search & Extraction, GAIA Multi-Step Reasoning & Tool Execution, OmniBench Native End-to-End Suite)
4. Ensure all tests use proper Pytest structures, realistic simulated workflow execution, assertions, and mock infrastructure so that `pytest tests/e2e/tier4_workloads` runs cleanly with 6 passing tests.
5. Run `pytest tests/e2e/tier4_workloads` to verify that all 6 tests pass.
6. Create `progress.md` and `handoff.md` in your working directory `/home/oh_my_macos27/OmniBench Computer Use/.agents/teamwork_preview_test_writer_t4/` detailing your work and test execution results.
7. Send message to parent orchestrator reporting completion with path to handoff.md.
