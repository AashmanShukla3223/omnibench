## 2026-08-08T11:16:47Z

You are the Sub-Orchestrator for Milestone M1 (Engine & Gateway) for OmniBench 1.0.

Your working directory: /home/oh_my_macos27/OmniBench Computer Use/.agents/teamwork_preview_sub_orch_m1
Parent agent ID: 9d3f0848-0386-4730-b0c7-909b8a9e57d8

Scope:
- Milestone M1: 100M Parameter ONNX Local Model Engine & Universal Model Gateway (Features 1-6 in PROJECT.md).
- Target modules: `omnibench/engine/` (`onnx_engine.py`, `preprocessor.py`, `quantizer.py`, `dummy_model.py`) and `omnibench/gateway/` (`protocol.py`, `adapters.py`, `router.py`).

Instructions:
1. Create `SCOPE.md`, `BRIEFING.md`, and `progress.md` in your working directory.
2. Apply the Project Orchestrator procedure: spawn Explorers, Worker, Reviewers, Challengers, and Forensic Auditor for M1 implementation and unit testing.
3. In Worker dispatches, include the MANDATORY INTEGRITY WARNING verbatim: "DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected."
4. Ensure ONNX engine operates strictly under <1.1 GiB RAM on CPU, Gateway protocol contracts are strictly enforced, and provider cascading router operates correctly with mock adapters.
5. Require build and unit tests to pass, all reviewers to APPROVE, challengers to confirm, and auditor verdict CLEAN before marking M1 DONE in PROJECT.md.
6. Write `handoff.md` and report completion back to parent (ID: 9d3f0848-0386-4730-b0c7-909b8a9e57d8) via send_message.
