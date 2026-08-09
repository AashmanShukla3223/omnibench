"""Unit tests for omnibench.engine — ONNXEngine, EngineConfig, preprocessor, quantizer."""

import pytest
import numpy as np
from PIL import Image


class TestEngineConfig:
    def test_defaults(self):
        from omnibench.engine.onnx_engine import EngineConfig
        cfg = EngineConfig()
        assert cfg.image_size == 448
        assert cfg.max_tokens == 256
        assert cfg.num_threads == 4
        assert cfg.quantization == "int8"

    def test_custom_config(self):
        from omnibench.engine.onnx_engine import EngineConfig
        cfg = EngineConfig(image_size=224, max_tokens=128, num_threads=2)
        assert cfg.image_size == 224
        assert cfg.max_tokens == 128

    def test_model_path_none_by_default(self):
        from omnibench.engine.onnx_engine import EngineConfig
        cfg = EngineConfig()
        assert cfg.model_path is None


class TestONNXEngine:
    def test_load_dummy_model(self):
        from omnibench.engine.onnx_engine import ONNXEngine, EngineConfig
        engine = ONNXEngine(EngineConfig())
        engine.load()  # Should not raise — uses dummy model or mock fallback

    def test_generate_returns_result(self, blank_image):
        from omnibench.engine.onnx_engine import ONNXEngine, EngineConfig, EngineResult
        engine = ONNXEngine(EngineConfig())
        engine.load()
        result = engine.generate(prompt="Click OK", images=[blank_image])
        assert isinstance(result, EngineResult)
        assert isinstance(result.text, str)
        assert isinstance(result.latency_ms, float)
        assert result.latency_ms >= 0

    def test_generate_without_images(self):
        from omnibench.engine.onnx_engine import ONNXEngine, EngineConfig
        engine = ONNXEngine(EngineConfig())
        engine.load()
        result = engine.generate(prompt="Type hello")
        assert result.text is not None

    def test_action_json_is_dict(self, blank_image):
        from omnibench.engine.onnx_engine import ONNXEngine, EngineConfig
        engine = ONNXEngine(EngineConfig())
        engine.load()
        result = engine.generate(prompt="click", images=[blank_image])
        assert isinstance(result.action_json, dict)

    def test_context_manager(self):
        from omnibench.engine.onnx_engine import ONNXEngine, EngineConfig
        with ONNXEngine(EngineConfig()) as engine:
            result = engine.generate("test")
            assert result is not None


class TestPreprocessor:
    def test_preprocess_image_pil(self, blank_image):
        from omnibench.engine.preprocessor import Preprocessor
        p = Preprocessor()
        arr = p.preprocess_image(blank_image)
        assert arr.shape == (1, 3, 224, 224)
        assert arr.dtype == np.float32

    def test_preprocess_image_bytes(self, image_bytes):
        from omnibench.engine.preprocessor import Preprocessor
        p = Preprocessor()
        arr = p.preprocess_image(image_bytes)
        assert arr.ndim == 4

    def test_preprocess_text(self):
        from omnibench.engine.preprocessor import Preprocessor
        p = Preprocessor()
        arr = p.preprocess_text("hello")
        assert arr.ndim == 2
        assert arr.dtype == np.int64

    def test_process_inputs_has_keys(self, blank_image):
        from omnibench.engine.preprocessor import Preprocessor
        p = Preprocessor()
        result = p.process_inputs("test prompt", images=[blank_image])
        assert "input_ids" in result
        assert "pixel_values" in result


class TestTextTokenizer:
    def test_encode_decode_roundtrip(self):
        from omnibench.engine.preprocessor_ext import TextTokenizer
        tk = TextTokenizer()
        tokens = tk.encode("hello")
        assert isinstance(tokens, list)
        assert all(isinstance(t, int) for t in tokens)

    def test_encode_numpy(self):
        from omnibench.engine.preprocessor_ext import TextTokenizer
        tk = TextTokenizer()
        arr = tk.encode_numpy("test")
        assert arr.shape[0] == 1
        assert arr.dtype == np.int64

    def test_empty_string(self):
        from omnibench.engine.preprocessor_ext import TextTokenizer
        tk = TextTokenizer()
        result = tk.encode("")
        assert isinstance(result, list)


class TestModelQuantizer:
    def test_fp32_mode_copies_file(self, tmp_path):
        from omnibench.engine.quantizer import ModelQuantizer, QuantizationConfig, QuantizationMode
        src = tmp_path / "model.onnx"
        src.write_bytes(b"fake_onnx_data")
        dst = tmp_path / "quantized.onnx"
        q = ModelQuantizer(QuantizationConfig(mode=QuantizationMode.FP32))
        result = q.quantize(src, dst)
        assert result.exists()
        assert result.read_bytes() == b"fake_onnx_data"

    def test_estimate_memory_mb(self, tmp_path):
        from omnibench.engine.quantizer import ModelQuantizer
        f = tmp_path / "model.onnx"
        f.write_bytes(b"x" * 1024 * 1024)  # 1 MB
        q = ModelQuantizer()
        mem = q.estimate_memory_mb(f)
        assert mem > 0

    def test_nonexistent_file_returns_zero(self):
        from omnibench.engine.quantizer import ModelQuantizer
        q = ModelQuantizer()
        assert q.estimate_memory_mb("/nonexistent/model.onnx") == 0.0
