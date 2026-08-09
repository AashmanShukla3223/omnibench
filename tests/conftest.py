"""Shared pytest fixtures for OmniBench test suite."""

from __future__ import annotations

import io
import tempfile
from typing import Generator

import numpy as np
import pytest
from PIL import Image


# ── Image Fixtures ────────────────────────────────────────────────────────────

@pytest.fixture
def blank_image() -> Image.Image:
    """448×448 white RGB image."""
    return Image.new("RGB", (448, 448), (255, 255, 255))


@pytest.fixture
def random_image() -> Image.Image:
    """448×448 random noise RGB image."""
    arr = np.random.randint(0, 256, (448, 448, 3), dtype=np.uint8)
    return Image.fromarray(arr)


@pytest.fixture
def small_image() -> Image.Image:
    """64×64 blue RGB image."""
    return Image.new("RGB", (64, 64), (0, 100, 200))


@pytest.fixture
def image_bytes(blank_image: Image.Image) -> bytes:
    buf = io.BytesIO()
    blank_image.save(buf, format="PNG")
    return buf.getvalue()


# ── Mock Driver ───────────────────────────────────────────────────────────────

@pytest.fixture
def mock_driver():
    """Linux driver in mock mode (no real display required)."""
    from omnibench.drivers.linux import LinuxDriver
    driver = LinuxDriver(mock=True)
    driver.connect()
    yield driver
    driver.disconnect()


# ── Gateway Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def mock_adapter():
    from omnibench.gateway.adapters import MockAdapter
    return MockAdapter(latency_ms=0.0)


@pytest.fixture
def mock_router(mock_adapter):
    from omnibench.gateway.router import CascadingRouter
    return CascadingRouter(adapters=[mock_adapter], mock_fallback=True)


@pytest.fixture
def gateway_request():
    from omnibench.gateway.protocol import GatewayRequest
    return GatewayRequest(prompt="Click the button at (500, 400)", max_tokens=64)


# ── Telemetry Fixtures ────────────────────────────────────────────────────────

@pytest.fixture
def tmp_db(tmp_path) -> Generator:
    """Temporary SQLite telemetry database."""
    from omnibench.telemetry.db import TelemetryDB
    db_path = str(tmp_path / "test_telemetry.db")
    db = TelemetryDB(db_path)
    db.connect()
    yield db
    db.close()


@pytest.fixture
def tmp_logger(tmp_db):
    from omnibench.telemetry.logger import TelemetryLogger
    return TelemetryLogger(db=tmp_db)


# ── Benchmark Fixtures ────────────────────────────────────────────────────────

@pytest.fixture
def native_task():
    from omnibench.benchmarks.task_schema import BenchmarkTask, TaskDomain
    return BenchmarkTask(
        task_id="test_task_001",
        domain=TaskDomain.OMNIBENCH_NATIVE,
        instruction="Wait 0.1 seconds.",
        max_steps=2,
        platform="linux",
    )


@pytest.fixture
def episode_result(native_task):
    from omnibench.benchmarks.task_schema import EpisodeResult
    return EpisodeResult(
        task_id=native_task.task_id,
        domain=native_task.domain.value,
        passed=True,
        score=0.85,
        total_steps=2,
        elapsed_seconds=0.5,
    )
