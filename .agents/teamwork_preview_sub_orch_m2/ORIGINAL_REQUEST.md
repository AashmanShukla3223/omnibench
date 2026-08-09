# Original Request — Milestone M2 (OS Automation Drivers)

## Initial Request — 2026-08-08T11:16:47Z
You are the Sub-Orchestrator for Milestone M2 (OS Automation Drivers) for OmniBench 1.0.

Your working directory: /home/oh_my_macos27/OmniBench Computer Use/.agents/teamwork_preview_sub_orch_m2
Parent agent ID: 9d3f0848-0386-4730-b0c7-909b8a9e57d8

Scope:
- Milestone M2: Cross-Platform Operating System Automation Drivers (Features 7-10 in PROJECT.md).
- Target module: `omnibench/drivers/` (`base.py`, `linux.py`, `windows.py`, `macos.py`, `android.py`, `ios.py`, `retry.py`).

Instructions:
1. Create `SCOPE.md`, `BRIEFING.md`, and `progress.md` in your working directory.
2. Apply the Project Orchestrator procedure: spawn Explorers, Worker, Reviewers, Challengers, and Forensic Auditor for M2 implementation and unit testing.
3. In Worker dispatches, include the MANDATORY INTEGRITY WARNING verbatim.
4. Support 8 action primitives (`click`, `double_click`, `right_click`, `drag`, `type`, `key_combination`, `scroll`, `wait`), platform drivers for Linux (Xvfb/xdotool), Windows (pywinauto/PowerShell), macOS (CoreGraphics), Android (ADB/uiautomator daemon), iOS (simctl/daemon), and exponential jittered retry backoff with mock fallback mode.
5. Require build and unit tests to pass, all reviewers to APPROVE, challengers to confirm, and auditor verdict CLEAN before marking M2 DONE in PROJECT.md.
6. Write `handoff.md` and report completion back to parent (ID: 9d3f0848-0386-4730-b0c7-909b8a9e57d8) via send_message.
