"""
OmniBench Web Dashboard Server.
Serves the static SPA and JSON/SSE telemetry API using Python stdlib http.server.
"""

from __future__ import annotations

import json
import os
import queue
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlparse, parse_qs

_STATIC_DIR = Path(__file__).parent / "static"
_event_queues: List[queue.Queue] = []
_event_lock = threading.Lock()


def _get_db_path() -> str:
    return os.getenv("OMNIBENCH_DB", "omnibench_telemetry.db")


def _get_runs() -> List[Dict[str, Any]]:
    try:
        from omnibench.telemetry.logger import TelemetryLogger
        logger = TelemetryLogger(db_path=_get_db_path())
        return logger.list_runs(limit=100)
    except Exception as exc:
        return [{"error": str(exc)}]


def _get_run_detail(run_id: str) -> Dict[str, Any]:
    try:
        from omnibench.telemetry.logger import TelemetryLogger
        logger = TelemetryLogger(db_path=_get_db_path())
        summary = logger.get_run_summary(run_id) or {}
        episodes = logger.list_episodes(run_id)
        return {"run": summary, "episodes": episodes}
    except Exception as exc:
        return {"error": str(exc)}


def broadcast_event(event: Dict[str, Any]) -> None:
    """Push a live event to all connected SSE clients."""
    data = json.dumps(event)
    with _event_lock:
        dead = []
        for q in _event_queues:
            try:
                q.put_nowait(data)
            except queue.Full:
                dead.append(q)
        for q in dead:
            _event_queues.remove(q)


class OmniBenchHandler(BaseHTTPRequestHandler):
    """HTTP request handler for OmniBench Dashboard."""

    def log_message(self, fmt: str, *args: Any) -> None:
        pass  # Suppress default access logs

    def _send_json(self, data: Any, status: int = 200) -> None:
        body = json.dumps(data, default=str).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, path: Path) -> None:
        content = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _send_sse_stream(self) -> None:
        """Send Server-Sent Events stream for live updates."""
        q: queue.Queue = queue.Queue(maxsize=100)
        with _event_lock:
            _event_queues.append(q)
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        try:
            # Send initial ping
            self.wfile.write(b"event: ping\ndata: {}\n\n")
            self.wfile.flush()
            while True:
                try:
                    data = q.get(timeout=15)
                    msg = f"data: {data}\n\n".encode()
                    self.wfile.write(msg)
                    self.wfile.flush()
                except queue.Empty:
                    # Heartbeat
                    self.wfile.write(b": heartbeat\n\n")
                    self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            with _event_lock:
                if q in _event_queues:
                    _event_queues.remove(q)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path in ("/", "/index.html"):
            html_file = _STATIC_DIR / "index.html"
            if html_file.exists():
                self._send_html(html_file)
            else:
                self._send_json({"error": "index.html not found"}, 404)
        elif path == "/api/runs":
            self._send_json(_get_runs())
        elif path.startswith("/api/runs/"):
            run_id = path[len("/api/runs/"):]
            self._send_json(_get_run_detail(run_id))
        elif path == "/stream":
            self._send_sse_stream()
        elif path == "/api/health":
            self._send_json({"status": "ok", "version": "1.0.0"})
        else:
            self._send_json({"error": f"Not found: {path}"}, 404)


def run_dashboard(port: int = 7890, host: str = "0.0.0.0") -> None:
    """Start the OmniBench web dashboard HTTP server (blocking)."""
    server = HTTPServer((host, port), OmniBenchHandler)
    print(f"[OmniBench Dashboard] Running at http://localhost:{port}")
    print("[OmniBench Dashboard] Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[OmniBench Dashboard] Shutting down.")
        server.shutdown()


def start_dashboard_thread(port: int = 7890) -> threading.Thread:
    """Start dashboard server in a background daemon thread."""
    t = threading.Thread(target=run_dashboard, kwargs={"port": port}, daemon=True)
    t.start()
    return t
