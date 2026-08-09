"""Synthetic ONNX Model Generator for CPU inference testing in OmniBench."""

import tempfile
from pathlib import Path
from typing import Union
import numpy as np
import onnx
from onnx import helper, TensorProto


class DummyModelGenerator:
    """Generates valid lightweight synthetic ONNX model binaries on-the-fly."""

    def __init__(
        self,
        vocab_size: int = 1000,
        hidden_size: int = 128,
        num_layers: int = 2,
        opset_version: int = 17,
    ) -> None:
        self.vocab_size = vocab_size
        self.hidden_size = hidden_size
        self.image_size = hidden_size if hidden_size in (224, 448) else 224
        self.opset_version = opset_version

    def _build_model_proto(self) -> onnx.ModelProto:
        """Constructs an ONNX ModelProto with input_ids and pixel_values inputs."""
        input_ids = helper.make_tensor_value_info(
            "input_ids", TensorProto.INT64, [1, 4]
        )
        pixel_values = helper.make_tensor_value_info(
            "pixel_values", TensorProto.FLOAT, [1, 3, None, None]
        )
        logits = helper.make_tensor_value_info(
            "logits", TensorProto.FLOAT, [1, 4, self.vocab_size]
        )

        dummy_logits = np.zeros((1, 4, self.vocab_size), dtype=np.float32)
        tensor_logits = helper.make_tensor(
            "const_logits",
            TensorProto.FLOAT,
            [1, 4, self.vocab_size],
            dummy_logits.flatten().tolist(),
        )

        const_node = helper.make_node(
            "Constant",
            inputs=[],
            outputs=["logits"],
            value=tensor_logits,
        )

        opset = helper.make_opsetid("", self.opset_version)
        graph = helper.make_graph(
            [const_node],
            "omnibench_dummy_graph",
            [input_ids, pixel_values],
            [logits],
        )

        model = helper.make_model(
            graph,
            producer_name="omnibench",
            opset_imports=[opset],
        )
        return model

    def generate_onnx_file(self, output_path: Union[str, Path]) -> Path:
        """Generates a valid lightweight ONNX model binary on disk."""
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        model = self._build_model_proto()
        onnx.save(model, str(target))
        return target

    def create_in_memory_dummy(self) -> bytes:
        """Generates ONNX model serialized byte string."""
        model = self._build_model_proto()
        return model.SerializeToString()
