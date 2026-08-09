#!/usr/bin/env python3
"""
OmniBench 1.0 — Android Phone Deployment & Interactive Task Runner.

Demonstrates model deployment & task execution on Android devices (e.g. Samsung Galaxy)
over ADB CLI or simulated hardware mock mode with ONNX, GGUF, or Mock engines.

Usage:
  python scripts/deploy_android.py [--model local_onnx|gguf|mock|auto] [--contact "Vanya Chaudhary"] [--no-mock]
"""

import argparse
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from omnibench.drivers.android import AndroidDriver
from omnibench.drivers.base import DeviceConnectionError
from omnibench.gateway.adapters import LocalONNXAdapter, GGUFAdapter, MockAdapter
from omnibench.gateway.router import CascadingRouter
from omnibench.engine.onnx_engine import ONNXEngine, EngineConfig
from omnibench.engine.gguf_engine import GGUFEngine, GGUFConfig
from omnibench.benchmarks.runner import BenchmarkRunner
from omnibench.benchmarks.task_schema import BenchmarkTask, TaskDomain


def main():
    parser = argparse.ArgumentParser(description="Deploy & test OmniBench on Android devices")
    parser.add_argument("--contact", default="Vanya Chaudhary", help="Contact name to call (default: Vanya Chaudhary)")
    parser.add_argument("--model", choices=["local_onnx", "gguf", "mock", "auto"], default="auto", help="Model engine adapter to use (default: auto)")
    parser.add_argument("--mock", action="store_true", default=False, help="Force mock execution mode")
    parser.add_argument("--no-mock", dest="mock", action="store_false", help="Connect to physical Android device via ADB")
    parser.add_argument("--device-id", default=None, help="ADB Device Serial ID (optional)")
    parser.set_defaults(mock=True)
    args = parser.parse_args()

    print(f"📱 OmniBench 1.0 — Android Mobile Deployment & Task Runner")
    print(f"🎯 Target Action: Make a call to contact '{args.contact}'")
    print(f"⚙️  Model Mode:   {args.model.upper()}\n")

    # 1. Initialize Driver with ADB Error Handling
    driver = AndroidDriver(device_id=args.device_id, mock=args.mock)
    try:
        driver.connect()
        print(f"[1/4] Android Driver Connected (Platform: {driver.platform}, Mock: {driver.mock})")
    except DeviceConnectionError as e:
        print(f"\n❌ ADB Device Connection Failure: {e.message}")
        print("💡 Troubleshooting Physical Mobile Phone Execution:")
        print("   1. Enable USB Debugging on your phone: Settings -> Developer Options -> USB Debugging")
        print("   2. Connect phone to PC via USB cable")
        print("   3. Run 'adb devices' and authorize the popup prompt on your phone screen")
        print("   (Or omit --no-mock to test in hardware mock mode)\n")
        sys.exit(1)

    # 2. Direct Primitive Test
    res_launch = driver.launch_app("com.samsung.android.dialer")
    print(f"[2/4] App Launch ('com.samsung.android.dialer') -> Success: {res_launch.success}")

    res_call = driver.call_contact(args.contact)
    print(f"[3/4] Contact Intent Call ('{args.contact}') -> Success: {res_call.success}")
    print(f"      Driver History: {driver.history[-2:]}\n")

    # 3. Model Adapter Resolution
    adapter = None
    if args.model in ("local_onnx", "auto"):
        onnx_file = Path("model.onnx")
        if onnx_file.exists() or args.model == "local_onnx":
            print(f"🧠 Loading Local ONNX VLM Engine ({'model.onnx' if onnx_file.exists() else 'Synthetic Dummy'})...")
            engine = ONNXEngine(EngineConfig(model_path=str(onnx_file) if onnx_file.exists() else None))
            adapter = LocalONNXAdapter(engine=engine)

    if adapter is None and args.model in ("gguf", "auto"):
        gguf_file = Path("model.gguf")
        if gguf_file.exists() or args.model == "gguf":
            print(f"🧠 Loading Local GGUF Engine...")
            engine = GGUFEngine(GGUFConfig(model_path=str(gguf_file) if gguf_file.exists() else None))
            adapter = GGUFAdapter(engine=engine)

    if adapter is None:
        print(f"🧠 Using Mock Adapter fallback...")
        adapter = MockAdapter()

    # 4. Agent Task Trajectory Simulation
    print(f"[4/4] Running Full Agent VLM Benchmark Episode...")
    task = BenchmarkTask(
        task_id="android_deploy_call_vanya",
        domain=TaskDomain.ANDROIDWORLD,
        instruction=f"Open Phone app, search for '{args.contact}', and tap the Call button.",
        metadata={"device": "samsung", "contact": args.contact},
        platform="android",
        max_steps=3,
    )

    router = CascadingRouter(adapters=[adapter], mock_fallback=True)
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
    print("\n🎉 Mobile Deployment & Task Execution Complete!")


if __name__ == "__main__":
    main()
