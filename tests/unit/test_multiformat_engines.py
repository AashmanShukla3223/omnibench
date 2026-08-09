"""Unit tests for multi-format model engines (ONNX, GGUF, MLX)."""

import pytest
from pathlib import Path
from omnibench.engine.gguf_engine import GGUFEngine, GGUFConfig, export_gguf_model
from omnibench.engine.mlx_engine import MLXEngine, MLXConfig, export_mlx_model
from omnibench.gateway.adapters import GGUFAdapter, MLXAdapter, GatewayRequest


class TestMultiFormatEngines:
    def test_gguf_engine_execution(self):
        engine = GGUFEngine(GGUFConfig(quantization="q4_k_m"))
        engine.load()
        res = engine.generate(None, "Call contact Vanya Chaudhary")
        assert "call_contact" in res["action_json"]["action"]
        assert res["action_json"]["engine"] == "gguf"

    def test_gguf_exporter(self, tmp_path):
        out_file = tmp_path / "model.gguf"
        export_gguf_model(out_file, quantization="q4_k_m")
        assert out_file.exists()
        assert out_file.stat().st_size > 0
        with open(out_file, "rb") as f:
            magic = f.read(4)
            assert magic == b"GGUF"

    def test_mlx_engine_execution(self):
        engine = MLXEngine(MLXConfig(quantization="4bit"))
        engine.load()
        res = engine.generate(None, "Click submit button")
        assert res["action_json"]["action"] == "click"
        assert res["action_json"]["engine"] == "mlx"

    def test_mlx_exporter(self, tmp_path):
        out_dir = tmp_path / "mlx_bundle"
        export_mlx_model(out_dir, quantization="4bit")
        assert (out_dir / "config.json").exists()
        assert (out_dir / "weights.npz").exists()

    def test_gateway_adapters(self):
        gguf_adapter = GGUFAdapter()
        res_g = gguf_adapter.generate(GatewayRequest(prompt="Call contact Vanya Chaudhary"))
        assert res_g.provider_used == "gguf"
        assert res_g.action_json["action"] == "call_contact"

        mlx_adapter = MLXAdapter()
        res_m = mlx_adapter.generate(GatewayRequest(prompt="Click target button"))
        assert res_m.provider_used == "mlx"
        assert res_m.action_json["action"] == "click"
