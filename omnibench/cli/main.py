#!/usr/bin/env python3
"""
OmniBench CLI — omnibench command-line interface.

Commands:
  config     Show/set configuration
  dataset    List available benchmark datasets
  run        Run a benchmark evaluation
  monitor    Monitor a running benchmark
  db         Query telemetry database
  dashboard  Start the web dashboard
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Optional


# ─── Helpers ────────────────────────────────────────────────────────────────

def _print_json(obj: object) -> None:
    print(json.dumps(obj, indent=2, default=str))


def _print_table(rows: list, headers: list) -> None:
    if not rows:
        print("(no data)")
        return
    col_widths = [max(len(str(h)), max((len(str(r.get(h, ""))) for r in rows), default=0)) for h in headers]
    fmt = "  ".join(f"{{:<{w}}}" for w in col_widths)
    print(fmt.format(*headers))
    print("  ".join("-" * w for w in col_widths))
    for row in rows:
        print(fmt.format(*[str(row.get(h, "")) for h in headers]))


# ─── Commands ────────────────────────────────────────────────────────────────

def cmd_config(args: argparse.Namespace) -> int:
    """Show or set OmniBench configuration."""
    import os
    config = {
        "OPENAI_API_KEY": "***" if os.getenv("OPENAI_API_KEY") else "(not set)",
        "ANTHROPIC_API_KEY": "***" if os.getenv("ANTHROPIC_API_KEY") else "(not set)",
        "GEMINI_API_KEY": "***" if os.getenv("GEMINI_API_KEY") else "(not set)",
        "OLLAMA_BASE_URL": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        "OMNIBENCH_DB": os.getenv("OMNIBENCH_DB", "omnibench_telemetry.db"),
    }
    _print_json(config)
    return 0


def cmd_dataset(args: argparse.Namespace) -> int:
    """List available benchmark datasets."""
    from omnibench.benchmarks.adapters import (
        OSWorldAdapter, WebArenaAdapter, AndroidWorldAdapter,
        Mind2WebAdapter, GAIAAdapter, OmniBenchNativeAdapter,
    )
    adapters = [
        ("osworld", OSWorldAdapter()),
        ("webarena", WebArenaAdapter()),
        ("androidworld", AndroidWorldAdapter()),
        ("mind2web", Mind2WebAdapter()),
        ("gaia", GAIAAdapter()),
        ("omnibench_native", OmniBenchNativeAdapter()),
    ]
    rows = []
    for domain, adapter in adapters:
        tasks = adapter.load_tasks(limit=999)
        rows.append({"domain": domain, "tasks": len(tasks)})
    _print_table(rows, ["domain", "tasks"])
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    """Run a benchmark evaluation."""
    import os
    from omnibench.gateway.adapters import MockAdapter, LocalONNXAdapter
    from omnibench.gateway.router import CascadingRouter
    from omnibench.drivers.linux import LinuxDriver
    from omnibench.benchmarks.runner import BenchmarkRunner
    from omnibench.telemetry.logger import TelemetryLogger
    from omnibench.telemetry.db import TelemetryDB

    domain = args.domain or "omnibench_native"
    model = args.model or "mock"
    limit = args.limit or 3

    print(f"[OmniBench] Running benchmark: domain={domain}, model={model}, limit={limit}")

    # Build adapter chain
    if model == "mock":
        adapters = [MockAdapter()]
    else:
        adapters = [LocalONNXAdapter()]

    router = CascadingRouter(adapters=adapters)
    driver = LinuxDriver(mock=True)

    try:
        driver.connect()
    except Exception as exc:
        print(f"[warn] Driver connect: {exc} — running in mock mode")

    runner = BenchmarkRunner(gateway_router=router, driver=driver)

    # Load tasks
    task_adapters = {
        "osworld": lambda: __import__("omnibench.benchmarks.adapters.osworld", fromlist=["OSWorldAdapter"]).OSWorldAdapter(),
        "webarena": lambda: __import__("omnibench.benchmarks.adapters.webarena", fromlist=["WebArenaAdapter"]).WebArenaAdapter(),
        "androidworld": lambda: __import__("omnibench.benchmarks.adapters.androidworld", fromlist=["AndroidWorldAdapter"]).AndroidWorldAdapter(),
        "mind2web": lambda: __import__("omnibench.benchmarks.adapters.mind2web", fromlist=["Mind2WebAdapter"]).Mind2WebAdapter(),
        "gaia": lambda: __import__("omnibench.benchmarks.adapters.gaia", fromlist=["GAIAAdapter"]).GAIAAdapter(),
        "omnibench_native": lambda: __import__("omnibench.benchmarks.adapters.omnibench_native", fromlist=["OmniBenchNativeAdapter"]).OmniBenchNativeAdapter(),
    }

    adapter_fn = task_adapters.get(domain)
    if not adapter_fn:
        print(f"[error] Unknown domain: {domain}")
        return 1

    task_adapter = adapter_fn()
    tasks = task_adapter.load_tasks(limit=limit)

    # Telemetry
    db_path = os.getenv("OMNIBENCH_DB", "omnibench_telemetry.db")
    logger = TelemetryLogger(db_path=db_path)
    run_id = logger.create_run(domain=domain, model_name=model)

    print(f"[OmniBench] Run ID: {run_id}")
    results = []
    for i, task in enumerate(tasks, 1):
        print(f"  [{i}/{len(tasks)}] Task: {task.task_id} ... ", end="", flush=True)
        result = runner.run_episode(task)
        logger.log_episode(run_id, result)
        status = "PASS" if result.passed else "FAIL"
        print(f"{status} (score={result.score:.2f}, steps={result.total_steps})")
        results.append(result)

    # Finalize
    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed
    score_avg = sum(r.score for r in results) / len(results) if results else 0.0
    logger.finalize_run(run_id, len(results), passed, failed, score_avg)

    print(f"\n[OmniBench] Results: {passed}/{len(results)} passed | avg_score={score_avg:.2f}")
    return 0


def cmd_monitor(args: argparse.Namespace) -> int:
    """Monitor recent benchmark runs from telemetry database."""
    import os
    from omnibench.telemetry.db import TelemetryDB
    from omnibench.telemetry.logger import TelemetryLogger

    db_path = os.getenv("OMNIBENCH_DB", "omnibench_telemetry.db")
    logger = TelemetryLogger(db_path=db_path)
    runs = logger.list_runs(limit=args.limit or 20)
    if not runs:
        print("No benchmark runs found.")
        return 0
    _print_table(
        runs,
        ["run_id", "domain", "model_name", "started_at", "total_tasks", "passed", "score_avg"],
    )
    return 0


def cmd_db(args: argparse.Namespace) -> int:
    """Query the OmniBench telemetry database."""
    import os
    from omnibench.telemetry.db import TelemetryDB

    db_path = os.getenv("OMNIBENCH_DB", "omnibench_telemetry.db")
    db = TelemetryDB(db_path)
    db.connect()

    if not args.sql:
        print("Usage: omnibench db --sql '<SQL query>'")
        return 1

    try:
        rows = db.execute(args.sql).fetchall()
        if rows:
            headers = list(rows[0].keys())
            _print_table([dict(r) for r in rows], headers)
        else:
            print("(empty result)")
    except Exception as exc:
        print(f"[error] {exc}")
        return 1
    return 0


def cmd_dashboard(args: argparse.Namespace) -> int:
    """Start the OmniBench web dashboard."""
    port = args.port or 7890
    print(f"[OmniBench] Starting web dashboard on http://localhost:{port}")
    from omnibench.dashboard.server import run_dashboard
    run_dashboard(port=port)
    return 0


# ─── Main ────────────────────────────────────────────────────────────────────

def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="omnibench",
        description="OmniBench 1.0 — Universal Computer Use Model Benchmark CLI",
    )
    subparsers = parser.add_subparsers(dest="command")

    # config
    subparsers.add_parser("config", help="Show configuration")

    # dataset
    subparsers.add_parser("dataset", help="List benchmark datasets")

    # run
    p_run = subparsers.add_parser("run", help="Run a benchmark evaluation")
    p_run.add_argument("--domain", type=str, help="Benchmark domain (e.g. omnibench_native)")
    p_run.add_argument("--model", type=str, help="Model name or 'mock'")
    p_run.add_argument("--limit", type=int, help="Max tasks to run")

    # monitor
    p_mon = subparsers.add_parser("monitor", help="Monitor recent benchmark runs")
    p_mon.add_argument("--limit", type=int, default=20)

    # db
    p_db = subparsers.add_parser("db", help="Query telemetry database")
    p_db.add_argument("--sql", type=str)

    # dashboard
    p_dash = subparsers.add_parser("dashboard", help="Start web dashboard")
    p_dash.add_argument("--port", type=int, default=7890)

    args = parser.parse_args(argv)

    cmd_map = {
        "config": cmd_config,
        "dataset": cmd_dataset,
        "run": cmd_run,
        "monitor": cmd_monitor,
        "db": cmd_db,
        "dashboard": cmd_dashboard,
    }

    if args.command is None:
        parser.print_help()
        return 0

    fn = cmd_map.get(args.command)
    if fn is None:
        print(f"Unknown command: {args.command}")
        return 1

    return fn(args)


if __name__ == "__main__":
    sys.exit(main())
