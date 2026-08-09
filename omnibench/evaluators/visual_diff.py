"""
OmniBench Visual State Diff Evaluator.
Computes image similarity metrics: MSE, SSIM, pHash distance, ROI diff, pixel diff %.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


@dataclass
class VisualDiffResult:
    """Result of a visual state comparison."""

    mse: float
    pixel_diff_pct: float
    ssim: float
    phash_distance: int
    passed: bool
    details: Dict[str, Any] = field(default_factory=dict)

    @property
    def score(self) -> float:
        """Normalized similarity score in [0, 1]. 1.0 = identical."""
        return max(0.0, self.ssim)


class VisualDiffEvaluator:
    """
    Compares two screenshots to assess visual state transitions.

    Metrics computed:
    - MSE: Mean Squared Error (lower = more similar)
    - Pixel Diff %: Fraction of pixels changed beyond threshold
    - SSIM: Structural Similarity Index (higher = more similar)
    - pHash Distance: Perceptual hash Hamming distance (lower = more similar)
    """

    def __init__(
        self,
        mse_threshold: float = 5000.0,
        pixel_diff_threshold: float = 0.20,
        ssim_threshold: float = 0.70,
        phash_threshold: int = 20,
        resize_for_eval: Tuple[int, int] = (256, 256),
        pixel_change_tolerance: int = 15,
    ) -> None:
        self.mse_threshold = mse_threshold
        self.pixel_diff_threshold = pixel_diff_threshold
        self.ssim_threshold = ssim_threshold
        self.phash_threshold = phash_threshold
        self.resize_for_eval = resize_for_eval
        self.pixel_change_tolerance = pixel_change_tolerance

    def _to_array(self, image: Image.Image) -> np.ndarray:
        """Convert PIL Image to uint8 numpy array resized for evaluation."""
        return np.array(
            image.convert("RGB").resize(self.resize_for_eval, Image.Resampling.LANCZOS),
            dtype=np.uint8,
        )

    def _compute_mse(self, a: np.ndarray, b: np.ndarray) -> float:
        diff = a.astype(np.float32) - b.astype(np.float32)
        return float(np.mean(diff ** 2))

    def _compute_pixel_diff_pct(self, a: np.ndarray, b: np.ndarray) -> float:
        diff = np.abs(a.astype(np.int32) - b.astype(np.int32))
        changed = np.any(diff > self.pixel_change_tolerance, axis=-1)
        return float(np.mean(changed))

    def _compute_ssim(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute SSIM using scikit-image if available, else simplified formula."""
        try:
            from skimage.metrics import structural_similarity as ssim  # type: ignore
            return float(ssim(a, b, channel_axis=-1, data_range=255))
        except ImportError:
            # Simplified luminance-based SSIM fallback
            af = a.mean(axis=-1).astype(np.float64)
            bf = b.mean(axis=-1).astype(np.float64)
            mu_a, mu_b = af.mean(), bf.mean()
            sigma_a = af.std()
            sigma_b = bf.std()
            sigma_ab = float(np.mean((af - mu_a) * (bf - mu_b)))
            C1, C2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
            num = (2 * mu_a * mu_b + C1) * (2 * sigma_ab + C2)
            den = (mu_a**2 + mu_b**2 + C1) * (sigma_a**2 + sigma_b**2 + C2)
            return float(num / den) if den != 0 else 1.0

    def _compute_phash(self, image: Image.Image, hash_size: int = 8) -> int:
        """Compute perceptual hash as integer."""
        img = image.convert("L").resize((hash_size * 4, hash_size * 4), Image.Resampling.LANCZOS)
        img = img.resize((hash_size, hash_size), Image.Resampling.LANCZOS)
        pixels = np.array(img, dtype=np.float32)
        mean = pixels.mean()
        bits = (pixels > mean).flatten()
        return int(sum(b << i for i, b in enumerate(bits)))

    def _phash_distance(self, h1: int, h2: int) -> int:
        """Hamming distance between two pHash integers."""
        xor = h1 ^ h2
        return bin(xor).count("1")

    def compare(
        self,
        before: Image.Image,
        after: Image.Image,
        roi: Optional[Tuple[int, int, int, int]] = None,
    ) -> VisualDiffResult:
        """
        Compare before and after screenshots.

        Args:
            before: Initial state screenshot.
            after: Final state screenshot.
            roi: Optional (left, top, right, bottom) region of interest crop.

        Returns:
            VisualDiffResult with all metrics and pass/fail determination.
        """
        b_img = before.convert("RGB")
        a_img = after.convert("RGB")

        if roi is not None:
            b_img = b_img.crop(roi)
            a_img = a_img.crop(roi)

        b_arr = self._to_array(b_img)
        a_arr = self._to_array(a_img)

        mse = self._compute_mse(b_arr, a_arr)
        pixel_diff = self._compute_pixel_diff_pct(b_arr, a_arr)
        ssim = self._compute_ssim(b_arr, a_arr)
        ph_before = self._compute_phash(b_img)
        ph_after = self._compute_phash(a_img)
        phash_dist = self._phash_distance(ph_before, ph_after)

        passed = (
            mse <= self.mse_threshold
            or pixel_diff <= self.pixel_diff_threshold
            or ssim >= self.ssim_threshold
            or phash_dist <= self.phash_threshold
        )

        return VisualDiffResult(
            mse=mse,
            pixel_diff_pct=pixel_diff,
            ssim=ssim,
            phash_distance=phash_dist,
            passed=passed,
            details={
                "mse_threshold": self.mse_threshold,
                "ssim_threshold": self.ssim_threshold,
                "phash_threshold": self.phash_threshold,
            },
        )

    def generate_diff_mask(
        self, before: Image.Image, after: Image.Image
    ) -> Image.Image:
        """Generate a visual difference mask highlighting changed pixels."""
        b_arr = self._to_array(before)
        a_arr = self._to_array(after)
        diff = np.abs(b_arr.astype(np.int32) - a_arr.astype(np.int32)).astype(np.uint8)
        diff_enhanced = np.clip(diff * 5, 0, 255).astype(np.uint8)
        return Image.fromarray(diff_enhanced, mode="RGB")
