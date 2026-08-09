#!/usr/bin/env python3
"""
OmniBench 1.0 — Android Phone Deployment & Interactive Task Runner.

Demonstrates model deployment & task execution on Android devices (e.g. Samsung Galaxy)
over ADB CLI or simulated hardware mock mode.

Usage:
  python scripts/deploy_android.py [--mock] [--contact "Vanya Chaudhary"] [--device-id <id>]
"""

import argparse
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from omnibench.drivers.android import AndroidDriver
from omnibench.gateway.adapters import MockAdapter
from omnibench.gateway.router import CascadingRouter
from omnibench.benchmarks.runner import BenchmarkRunner
from omnibench.benchmarks.task_schema import BenchmarkTask, TaskDomain
from omnibench.telemetry.logger import TelemetryLogger


def main():
    parser = argparse.ArgumentParser(description="Deploy & test OmniBench on Android devices")
    parser.add_argument("--contact", default="Vanya Chaudhary", help="Contact name to call (default: Vanya Chaudhary)")
    parser.add_argument("--mock", action="store_true", default=True, help="Force mock execution mode")
    parser.add_argument("--device-id", default=None, help="ADB Device Serial ID (optional)")
    args = parser.parse_args()

    print(f"📱 OmniBench 1.0 — Android Deployment Test Target: Samsung Galaxy Phone")
    print(f"🎯 Target Action: Make a call to contact '{args.contact}'\n")

    # 1. Initialize Driver
    driver = AndroidDriver(device_id=args.device_id, mock=args.mock)
    driver.connect()
    print(f"[1/4] Android Driver Connected (Platform: {driver.platform}, Mock: {driver.mock})")

    # 2. Direct Primitive Test
    res_launch = driver.launch_app("com.samsung.android.dialer")
    print(f"[2/4] App Launch ('com.samsung.android.dialer') -> Success: {res_launch.success}")

    res_call = driver.call_contact(args.contact)
    print(f"[3/4] Contact Intent Call ('{args.contact}') -> Success: {res_call.success}")
    print(f"      Driver History: {driver.history[-2:]}\n")

    # 3. Agent Task Trajectory Simulation
    print(f"[4/4] Running Full Agent VLM Benchmark Episode...")
    task = BenchmarkTask(
        task_id="android_deploy_call_vanya",
        domain=TaskDomain.ANDROIDWORLD,
        instruction=f"Open Phone app, search for '{args.contact}', and tap the Call button.",
        metadata={"device": "samsung", "contact": args.contact},
        platform="android",
        max_steps=3,
    )

    router = CascadingRouter(adapters=[MockAdapter()], mock_fallback=True)
    runner = BenchmarkRunner(gateway_router=router, driver=driver)
    result = runner.run_episode(task)

    print("\n✅ Execution Trajectory Summary:")
    print(f"   Task ID:         {result.task_id}")
    print(f"   Passed:          {result.passed}")
    print(f"   Score:           {result.score:.2f}")
    print(f"   Total Steps:     {result.total_steps}")
    print(f"   Elapsed Time:    {result.elapsed_seconds:.2f}s")
    for step in result.steps:
        print(f"   Step {step.step_idx + 1}: Action: {step.action_type} ({step.action_params})")

    driver.disconnect()
    print("\n🎉 Android Model Deployment & Task Testing Complete!")


if __name__ == "__main__":
    main()
