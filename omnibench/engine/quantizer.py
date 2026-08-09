"""
OmniBench Engine Quantizer — INT8/INT4 quantization utilities.
Wraps ONNX Runtime quantization tools for model size and RAM reduction.
"""

from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Union

logger = logging.getLogger(__name__)


class QuantizationMode(str, Enum):
    INT8_DYNAMIC = "int8_dynamic"
    INT8_STATIC = "int8_static"
    INT4 = "int4"
    FP32 = "fp32"  # No quantization


@dataclass
class QuantizationConfig:
    """Configuration for model quantization."""

    mode: QuantizationMode = QuantizationMode.INT8_DYNAMIC
    per_channel: bool = False
    reduce_range: bool = True
    weight_type: str = "QInt8"
    op_types_to_quantize: Optional[list] = None


class ModelQuantizer:
    """
    Applies INT8/INT4 quantization to an ONNX model to reduce RAM footprint.

    A 100M-parameter FP32 model (~400 MB) → INT8 (~100-200 MB).
    Uses onnxruntime.quantization if available; otherwise copies model as-is.
    """

    def __init__(self, config: Optional[QuantizationConfig] = None) -> None:
        self.config = config or QuantizationConfig()

    def quantize(
        self,
        input_model_path: Union[str, Path],
        output_model_path: Union[str, Path],
    ) -> Path:
        """
        Quantize the model at input_model_path and save to output_model_path.

        Returns:
            Path to the quantized model file.
        """
        input_path = Path(input_model_path)
        output_path = Path(output_model_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if self.config.mode == QuantizationMode.FP32:
            logger.info("FP32 mode — no quantization applied, copying model.")
            shutil.copy2(input_path, output_path)
            return output_path

        try:
            from onnxruntime.quantization import (  # type: ignore
                quantize_dynamic,
                quantize_static,
                QuantType,
            )

            weight_type = (
                QuantType.QInt8
                if self.config.weight_type == "QInt8"
                else QuantType.QUInt8
            )

            if self.config.mode in (
                QuantizationMode.INT8_DYNAMIC,
                QuantizationMode.INT4,
            ):
                logger.info(
                    "Applying dynamic INT8 quantization: %s → %s",
                    input_path,
                    output_path,
                )
                quantize_dynamic(
                    str(input_path),
                    str(output_path),
                    weight_type=weight_type,
                    per_channel=self.config.per_channel,
                    reduce_range=self.config.reduce_range,
                    op_types_to_quantize=self.config.op_types_to_quantize,
                )
            else:
                logger.warning(
                    "Static quantization requires calibration dataset — "
                    "falling back to dynamic quantization."
                )
                quantize_dynamic(
                    str(input_path),
                    str(output_path),
                    weight_type=weight_type,
                )

            logger.info("Quantization complete: %s", output_path)
            return output_path

        except ImportError:
            logger.warning(
                "onnxruntime.quantization not available — copying model without quantization."
            )
            shutil.copy2(input_path, output_path)
            return output_path

    def estimate_memory_mb(self, model_path: Union[str, Path]) -> float:
        """Estimate runtime memory usage of a model in megabytes."""
        path = Path(model_path)
        if not path.exists():
            return 0.0
        size_bytes = path.stat().st_size
        # Heuristic: runtime RSS is typically 2-3× the model file size
        return (size_bytes * 2.5) / (1024 * 1024)
