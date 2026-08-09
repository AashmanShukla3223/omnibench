# Scope: Milestone M2 — OS Automation Drivers
Parent Orchestrator Conversation ID: 56ba8294-13aa-4aec-878c-ea8d969fa715
Working Directory: /home/oh_my_macos27/OmniBench Computer Use/.agents/orch_m2_drivers

## Mission
Orchestrate the design, implementation, and verification of Milestone M2 (Cross-Platform Operating System Automation Drivers).

## Scope & Target Code Layout
- Target modules: `omnibench/drivers/`
- Features to implement (Features 7 - 10 in `PROJECT.md`):
  7. Unified `BaseOSDriver` Interface (8 action primitives: click, double_click, right_click, drag, type, key_combination, scroll, wait)
  8. Desktop OS Drivers: Linux (Xvfb/xdotool), Windows (pywinauto/PowerShell), macOS (CoreGraphics/screencapture)
  9. Mobile OS Drivers: Android (ADB/uiautomator daemon), iOS (simctl/daemon)
  10. Exception Hierarchy & Jittered Exponential Backoff Retry Decorator

## Instructions
1. Read `/home/oh_my_macos27/OmniBench Computer Use/ORIGINAL_REQUEST.md` and `/home/oh_my_macos27/OmniBench Computer Use/PROJECT.md`.
2. Create `SCOPE.md` in your working directory.
3. Run the Iteration Loop (Explorer -> Worker -> Reviewer -> Challenger -> Auditor -> Gate).
4. Verify all action primitives execute with automated error backoff and retries.
5. Update `PROJECT.md` status for M2 to `DONE`.
6. Report completion to parent.
