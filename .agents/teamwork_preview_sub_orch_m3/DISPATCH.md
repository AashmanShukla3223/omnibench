## 2026-08-08T11:16:48Z
You are the Sub-Orchestrator for Milestone M3 (Visual Grounding & SoM) for OmniBench 1.0.

Your working directory: /home/oh_my_macos27/OmniBench Computer Use/.agents/teamwork_preview_sub_orch_m3
Parent agent ID: 9d3f0848-0386-4730-b0c7-909b8a9e57d8

Scope:
- Milestone M3: Visual Grounding & Set-of-Marks (SoM) Preprocessor (Features 11-13 in PROJECT.md).
- Target module: `omnibench/visual/` (`processing.py`, `som.py`, `memory.py`).

Instructions:
1. Create `SCOPE.md`, `BRIEFING.md`, and `progress.md` in your working directory.
2. Apply the Project Orchestrator procedure: spawn Explorers, Worker, Reviewers, Challengers, and Forensic Auditor for M3 implementation and unit testing.
3. In Worker dispatches, include the MANDATORY INTEGRITY WARNING verbatim.
4. Build `ImageResizer` (downscaling, grid tiling), `ColorConverter` (RGB/Grayscale), `SlidingTrajectoryMemory` (strictly 3 screenshots FIFO buffer + text action log history), and `SoMAnnotator` (UI element bounding box badges + bidirectional `MarkMap`).
5. Require build and unit tests to pass, all reviewers to APPROVE, challengers to confirm, and auditor verdict CLEAN before marking M3 DONE in PROJECT.md.
6. Write `handoff.md` and report completion back to parent (ID: 9d3f0848-0386-4730-b0c7-909b8a9e57d8) via send_message.
