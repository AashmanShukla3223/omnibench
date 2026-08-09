# Analysis & Implementation Design: Feature 11 — Screen Processing Pipeline

**Agent**: `explorer_m3_1`  
**Milestone**: M3 (Visual Grounding & Set-of-Marks Preprocessor)  
**Target Module**: `omnibench/visual/processing.py`  
**Target Test Module**: `tests/unit/test_visual_processing.py` (or `tests/unit/test_visual.py`)  
**Date**: 2026-08-08  

---

## 1. Executive Summary

Feature 11 (`Screen Processing Pipeline`) provides image preprocessing capabilities for the OmniBench 1.0 architecture:
1. **`ImageResizer`**: Resizing, aspect-ratio-preserving downscaling, padding, grid tiling, and pixel coordinate mapping between tiled/resized images and original high-resolution screen captures.
2. **`ColorConverter`**: Calibrated, loss-free color-space conversions between PIL modes (`RGB`, `RGBA`, Grayscale `L`, `P`, `1`, etc.), including alpha-channel composite blending with customizable background colors and 3-channel grayscale generation for Vision-Language Models (VLMs).

This document provides the exact class structures, type-annotated method signatures, exception handling rules, internal algorithms, integration points, and comprehensive Tier 1/Tier 2 unit test specifications.

---

## 2. Specification & System Context

### 2.1 Authoritative References
- **`ORIGINAL_REQUEST.md` (R3)**: Screen capture optimization (resizing/tiling, RGB/grayscale).
- **`PROJECT.md` (Feature 11)**: Image Resizer (tiling/downscaling) and Color Converter (RGB/Grayscale).
- **`SCOPE.md` (M3.1)**: Screen processing pipeline contract in `omnibench/visual/processing.py`.
- **`TEST_INFRA.md` (Feature 11)**: Unit/E2E test targets (Tier 1 ≥ 5 tests, Tier 2 ≥ 5 boundary tests).

### 2.2 System Role & Callers
- **`omnibench.engine.preprocessor`**: Uses `ImageResizer` to format raw high-resolution OS screenshots (e.g. 1920x1080, 2560x1440) down to ONNX VLM input dimensions (e.g. 224x224, 384x384) or grid sub-patches.
- **`omnibench.visual.som.SoMAnnotator`**: Uses `ColorConverter.to_rgb` to sanitize raw screenshots before superimposing bounding box marks and text labels.
- **`omnibench.evaluators.visual_diff`**: Uses `ColorConverter.to_grayscale` and `ImageResizer.downscale` prior to calculating SSIM, pHash, and pixel diff matrices.

---

## 3. Detailed Technical Design: `ImageResizer`

### 3.1 Class Overview
`ImageResizer` encapsulates resizing, aspect-ratio preservation, padding, downscaling, grid tiling, and bidirectional coordinate transformation.

```python
class ImageResizer:
    """
    Handles image scaling, aspect ratio preservation, grid tiling, 
    and coordinate transformation mapping for visual grounding.
    """
    def __init__(
        self,
        default_resampling: Image.Resampling = Image.Resampling.LANCZOS,
        default_padding_color: Tuple[int, int, int] = (0, 0, 0)
    ) -> None:
        ...
```

### 3.2 Method Signatures & Behavioral Specifications

#### Method 1: `resize`
```python
def resize(
    self,
    image: Image.Image,
    target_size: Tuple[int, int],
    preserve_aspect_ratio: bool = True,
    pad: bool = False,
    padding_color: Optional[Tuple[int, int, int]] = None,
    resampling: Optional[Image.Resampling] = None
) -> Image.Image:
```
- **Description**: Resizes `image` to `target_size = (target_w, target_h)`.
- **Behavior**:
  - Validates `image` is `PIL.Image.Image` (raises `TypeError` if not).
  - Validates `target_size` consists of two integers `> 0` (raises `ValueError` if not).
  - If `preserve_aspect_ratio=False`:
    - Resizes `image` directly to `(target_w, target_h)` using `resampling`.
  - If `preserve_aspect_ratio=True` and `pad=False`:
    - Computes scale factor `scale = min(target_w / orig_w, target_h / orig_h)`.
    - Computes new size `new_w = max(1, round(orig_w * scale))` and `new_h = max(1, round(orig_h * scale))`.
    - Returns resized image of dimensions `(new_w, new_h)`.
  - If `preserve_aspect_ratio=True` and `pad=True`:
    - Computes `(new_w, new_h)` as above.
    - Creates a new canvas image of size `(target_w, target_h)` filled with `padding_color`.
    - Pastes scaled image centered at `offset_x = (target_w - new_w) // 2`, `offset_y = (target_h - new_h) // 2`.
    - Returns canvas image of exact dimensions `(target_w, target_h)`.

#### Method 2: `downscale`
```python
def downscale(
    self,
    image: Image.Image,
    max_dimension: Union[int, Tuple[int, int]],
    resampling: Optional[Image.Resampling] = None
) -> Image.Image:
```
- **Description**: Downscales `image` if its dimensions exceed `max_dimension`, maintaining aspect ratio without upsizing small images.
- **Behavior**:
  - If `max_dimension` is `int`: `(max_w, max_h) = (max_dimension, max_dimension)`.
  - If `max_dimension` is `tuple[int, int]`: `(max_w, max_h) = max_dimension`.
  - If `orig_w <= max_w` and `orig_h <= max_h`: Returns `image.copy()`.
  - Otherwise, calls `self.resize(image, (max_w, max_h), preserve_aspect_ratio=True, pad=False, resampling=resampling)`.

#### Method 3: `tile`
```python
def tile(
    self,
    image: Image.Image,
    grid_size: Tuple[int, int],
    overlap: int = 0
) -> List[Image.Image]:
```
- **Description**: Splits `image` into a grid of sub-images of dimensions `(rows, cols)` in row-major order.
- **Behavior**:
  - Validates `grid_size = (rows, cols)` where `rows >= 1` and `cols >= 1`. Raises `ValueError` if invalid.
  - Validates `overlap >= 0` (raises `ValueError` if negative).
  - Iterates `r` from `0` to `rows-1` and `c` from `0` to `cols-1`:
    - `left = int(round(c * orig_w / cols)) - (overlap if c > 0 else 0)`
    - `top = int(round(r * orig_h / rows)) - (overlap if r > 0 else 0)`
    - `right = int(round((c + 1) * orig_w / cols)) + (overlap if c < cols - 1 else 0)`
    - `bottom = int(round((r + 1) * orig_h / rows)) + (overlap if r < rows - 1 else 0)`
    - Clamps `left = max(0, left)`, `top = max(0, top)`, `right = min(orig_w, right)`, `bottom = min(orig_h, bottom)`.
    - Crops sub-image `image.crop((left, top, right, bottom))` and appends to list.
  - Returns `list[Image.Image]` containing `rows * cols` tiles.

#### Method 4: `tile_with_metadata`
```python
def tile_with_metadata(
    self,
    image: Image.Image,
    grid_size: Tuple[int, int],
    overlap: int = 0
) -> List[dict]:
```
- **Description**: Returns list of dictionaries for each tile containing metadata needed for coordinate mapping:
  `{"tile": Image, "grid_pos": (row, col), "crop_box": (left, top, right, bottom)}`.

#### Method 5: `map_tile_coordinates_to_original`
```python
def map_tile_coordinates_to_original(
    self,
    tile_x: int,
    tile_y: int,
    crop_box: Tuple[int, int, int, int]
) -> Tuple[int, int]:
```
- **Description**: Translates local tile pixel coordinate `(tile_x, tile_y)` back to original full screenshot coordinate `(orig_x, orig_y) = (crop_box[0] + tile_x, crop_box[1] + tile_y)`.

#### Method 6: `map_resized_coordinates_to_original`
```python
def map_resized_coordinates_to_original(
    self,
    x: int,
    y: int,
    orig_size: Tuple[int, int],
    target_size: Tuple[int, int],
    preserve_aspect_ratio: bool = True,
    pad: bool = False
) -> Tuple[int, int]:
```
- **Description**: Maps pixel coordinate `(x, y)` on a resized image back to original resolution `orig_size = (orig_w, orig_h)`.
- **Behavior**:
  - Accounts for centering offset when `pad=True`.
  - Reverses scaling transformation and clamps within `[0, orig_w - 1]` and `[0, orig_h - 1]`.

---

## 4. Detailed Technical Design: `ColorConverter`

### 4.1 Class Overview
`ColorConverter` performs standard color mode conversions while guaranteeing proper alpha channel composite handling, preventing black artifact issues when converting transparent PNGs to RGB.

```python
class ColorConverter:
    """
    Handles image mode conversions (RGB, RGBA, Grayscale, Palette) 
    with transparent background compositing support.
    """
    def __init__(
        self,
        default_bg_color: Tuple[int, int, int] = (255, 255, 255)
    ) -> None:
        self.default_bg_color = default_bg_color
```

### 4.2 Method Signatures & Behavioral Specifications

#### Method 1: `to_rgb`
```python
def to_rgb(
    self,
    image: Image.Image,
    bg_color: Optional[Tuple[int, int, int]] = None
) -> Image.Image:
```
- **Description**: Converts any PIL Image (`RGBA`, `L`, `P`, `1`, `CMYK`, `LA`) to `RGB` mode.
- **Behavior**:
  - If `image.mode == "RGB"`: Returns `image.copy()`.
  - If `image.mode in ("RGBA", "LA")`:
    - Creates a solid background RGB image of size `image.size` filled with `bg_color` (defaults to `self.default_bg_color`).
    - Converts `image` to `RGBA` if needed to extract alpha mask.
    - Pastes `image` onto background using `image.getchannel('A')` (or `image.split()[-1]`) as mask.
    - Returns composite `RGB` image.
  - If `image.mode == "P"`:
    - Checks if palette contains transparency info (`"transparency"` in `image.info`).
    - If transparent, converts to `RGBA` first, then composites onto background.
    - Otherwise, directly calls `image.convert("RGB")`.
  - For other modes (`L`, `1`, `CMYK`): Directly calls `image.convert("RGB")`.

#### Method 2: `to_grayscale`
```python
def to_grayscale(
    self,
    image: Image.Image,
    num_channels: int = 3
) -> Image.Image:
```
- **Description**: Converts image to grayscale.
- **Behavior**:
  - Validates `num_channels in (1, 3)` (raises `ValueError` if not).
  - First converts `image` to RGB using `to_rgb(image)` to ensure alpha channels are properly composited.
  - Converts RGB to 1-channel grayscale `L` using luminance formula ($L = 0.299R + 0.587G + 0.114B$).
  - If `num_channels == 1`: Returns `L` image.
  - If `num_channels == 3`: Merges `L` channel into 3 identical RGB channels `Image.merge("RGB", (L, L, L))` and returns `RGB` image.

#### Method 3: `convert`
```python
def convert(
    self,
    image: Image.Image,
    mode: str,
    bg_color: Optional[Tuple[int, int, int]] = None
) -> Image.Image:
```
- **Description**: Generic conversion method to target mode `mode` (e.g., `"RGB"`, `"L"`, `"RGBA"`, `"HSV"`).
- **Behavior**:
  - Validates `mode` string against PIL modes. Raises `ValueError` for unknown modes.
  - Handles target mode `"RGB"` via `to_rgb()`.
  - Handles target mode `"L"` via `to_grayscale(image, num_channels=1)`.
  - For other valid modes, invokes PIL `image.convert(mode)`.

#### Method 4: `is_grayscale` & `is_rgb`
```python
def is_grayscale(self, image: Image.Image) -> bool:
    """Returns True if image is mode 'L', '1', 'I', 'F' or RGB with equal channels."""

def is_rgb(self, image: Image.Image) -> bool:
    """Returns True if image mode is 'RGB'."""
```

---

## 5. Code Implementation Blueprint (`omnibench/visual/processing.py`)

Below is the complete implementation design to be placed in `omnibench/visual/processing.py`:

```python
"""
OmniBench Visual Grounding & Set-of-Marks Preprocessor - Screen Processing Pipeline.
Contains ImageResizer and ColorConverter implementations.
"""

import math
from typing import List, Tuple, Optional, Union, Dict, Any
from PIL import Image


class ImageResizer:
    """
    ImageResizer handles screen capture resizing, downscaling, grid tiling,
    and coordinate transformation mapping for visual grounding.
    """

    def __init__(
        self,
        default_resampling: Image.Resampling = Image.Resampling.LANCZOS,
        default_padding_color: Tuple[int, int, int] = (0, 0, 0),
    ) -> None:
        self.default_resampling = default_resampling
        self.default_padding_color = default_padding_color

    def resize(
        self,
        image: Image.Image,
        target_size: Tuple[int, int],
        preserve_aspect_ratio: bool = True,
        pad: bool = False,
        padding_color: Optional[Tuple[int, int, int]] = None,
        resampling: Optional[Image.Resampling] = None,
    ) -> Image.Image:
        if not isinstance(image, Image.Image):
            raise TypeError(f"Expected PIL.Image.Image, got {type(image)}")

        if not (
            isinstance(target_size, (tuple, list))
            and len(target_size) == 2
            and isinstance(target_size[0], int)
            and isinstance(target_size[1], int)
            and target_size[0] > 0
            and target_size[1] > 0
        ):
            raise ValueError(f"target_size must be a tuple of 2 positive integers, got {target_size}")

        resample_filter = resampling if resampling is not None else self.default_resampling
        pad_color = padding_color if padding_color is not None else self.default_padding_color

        target_w, target_h = target_size
        orig_w, orig_h = image.size

        if not preserve_aspect_ratio:
            return image.resize((target_w, target_h), resample=resample_filter)

        scale = min(target_w / orig_w, target_h / orig_h)
        new_w = max(1, int(round(orig_w * scale)))
        new_h = max(1, int(round(orig_h * scale)))

        scaled_img = image.resize((new_w, new_h), resample=resample_filter)

        if not pad:
            return scaled_img

        # Create canvas with pad_color and center scaled_img
        if image.mode in ("RGBA", "LA"):
            canvas = Image.new("RGBA", (target_w, target_h), pad_color + (255,))
        else:
            canvas = Image.new(image.mode if image.mode != "P" else "RGB", (target_w, target_h), pad_color)

        offset_x = (target_w - new_w) // 2
        offset_y = (target_h - new_h) // 2
        canvas.paste(scaled_img, (offset_x, offset_y))
        return canvas

    def downscale(
        self,
        image: Image.Image,
        max_dimension: Union[int, Tuple[int, int]],
        resampling: Optional[Image.Resampling] = None,
    ) -> Image.Image:
        if not isinstance(image, Image.Image):
            raise TypeError(f"Expected PIL.Image.Image, got {type(image)}")

        if isinstance(max_dimension, int):
            if max_dimension <= 0:
                raise ValueError(f"max_dimension must be positive, got {max_dimension}")
            max_w, max_h = max_dimension, max_dimension
        elif isinstance(max_dimension, (tuple, list)) and len(max_dimension) == 2:
            if max_dimension[0] <= 0 or max_dimension[1] <= 0:
                raise ValueError(f"max_dimension values must be positive, got {max_dimension}")
            max_w, max_h = max_dimension[0], max_dimension[1]
        else:
            raise ValueError(f"Invalid max_dimension specification: {max_dimension}")

        orig_w, orig_h = image.size
        if orig_w <= max_w and orig_h <= max_h:
            return image.copy()

        return self.resize(
            image,
            target_size=(max_w, max_h),
            preserve_aspect_ratio=True,
            pad=False,
            resampling=resampling,
        )

    def tile(
        self,
        image: Image.Image,
        grid_size: Tuple[int, int],
        overlap: int = 0,
    ) -> List[Image.Image]:
        tiles_meta = self.tile_with_metadata(image, grid_size, overlap=overlap)
        return [item["tile"] for item in tiles_meta]

    def tile_with_metadata(
        self,
        image: Image.Image,
        grid_size: Tuple[int, int],
        overlap: int = 0,
    ) -> List[Dict[str, Any]]:
        if not isinstance(image, Image.Image):
            raise TypeError(f"Expected PIL.Image.Image, got {type(image)}")

        if not (
            isinstance(grid_size, (tuple, list))
            and len(grid_size) == 2
            and isinstance(grid_size[0], int)
            and isinstance(grid_size[1], int)
            and grid_size[0] >= 1
            and grid_size[1] >= 1
        ):
            raise ValueError(f"grid_size must be a tuple of positive integers (rows, cols), got {grid_size}")

        if overlap < 0:
            raise ValueError(f"overlap must be non-negative, got {overlap}")

        rows, cols = grid_size
        orig_w, orig_h = image.size
        tiles_metadata = []

        for r in range(rows):
            for c in range(cols):
                left = int(round(c * orig_w / cols)) - (overlap if c > 0 else 0)
                top = int(round(r * orig_h / rows)) - (overlap if r > 0 else 0)
                right = int(round((c + 1) * orig_w / cols)) + (overlap if c < cols - 1 else 0)
                bottom = int(round((r + 1) * orig_h / rows)) + (overlap if r < rows - 1 else 0)

                left = max(0, left)
                top = max(0, top)
                right = min(orig_w, right)
                bottom = min(orig_h, bottom)

                crop_box = (left, top, right, bottom)
                tile_img = image.crop(crop_box)
                tiles_metadata.append(
                    {
                        "tile": tile_img,
                        "grid_pos": (r, c),
                        "crop_box": crop_box,
                    }
                )

        return tiles_metadata

    def map_tile_coordinates_to_original(
        self,
        tile_x: int,
        tile_y: int,
        crop_box: Tuple[int, int, int, int],
    ) -> Tuple[int, int]:
        left, top, _, _ = crop_box
        return (left + tile_x, top + tile_y)

    def map_resized_coordinates_to_original(
        self,
        x: int,
        y: int,
        orig_size: Tuple[int, int],
        target_size: Tuple[int, int],
        preserve_aspect_ratio: bool = True,
        pad: bool = False,
    ) -> Tuple[int, int]:
        orig_w, orig_h = orig_size
        target_w, target_h = target_size

        if not preserve_aspect_ratio:
            orig_x = int(round(x * (orig_w / target_w)))
            orig_y = int(round(y * (orig_h / target_h)))
        elif not pad:
            scale = min(target_w / orig_w, target_h / orig_h)
            orig_x = int(round(x / scale))
            orig_y = int(round(y / scale))
        else:
            scale = min(target_w / orig_w, target_h / orig_h)
            new_w = max(1, int(round(orig_w * scale)))
            new_h = max(1, int(round(orig_h * scale)))
            offset_x = (target_w - new_w) // 2
            offset_y = (target_h - new_h) // 2
            adj_x = x - offset_x
            adj_y = y - offset_y
            orig_x = int(round(adj_x / scale))
            orig_y = int(round(adj_y / scale))

        orig_x = max(0, min(orig_w - 1, orig_x))
        orig_y = max(0, min(orig_h - 1, orig_y))
        return (orig_x, orig_y)


class ColorConverter:
    """
    ColorConverter provides strict, calibrated color space conversions
    between RGB, RGBA, Grayscale ('L'), and other PIL image modes.
    """

    def __init__(
        self,
        default_bg_color: Tuple[int, int, int] = (255, 255, 255),
    ) -> None:
        self.default_bg_color = default_bg_color

    def to_rgb(
        self,
        image: Image.Image,
        bg_color: Optional[Tuple[int, int, int]] = None,
    ) -> Image.Image:
        if not isinstance(image, Image.Image):
            raise TypeError(f"Expected PIL.Image.Image, got {type(image)}")

        background_color = bg_color if bg_color is not None else self.default_bg_color

        if image.mode == "RGB":
            return image.copy()

        if image.mode in ("RGBA", "LA"):
            bg_canvas = Image.new("RGB", image.size, background_color)
            alpha_mask = image.convert("RGBA").split()[-1]
            bg_canvas.paste(image.convert("RGB"), mask=alpha_mask)
            return bg_canvas

        if image.mode == "P":
            if "transparency" in image.info:
                rgba_img = image.convert("RGBA")
                return self.to_rgb(rgba_img, bg_color=background_color)
            return image.convert("RGB")

        return image.convert("RGB")

    def to_grayscale(
        self,
        image: Image.Image,
        num_channels: int = 3,
    ) -> Image.Image:
        if not isinstance(image, Image.Image):
            raise TypeError(f"Expected PIL.Image.Image, got {type(image)}")

        if num_channels not in (1, 3):
            raise ValueError(f"num_channels must be 1 or 3, got {num_channels}")

        rgb_img = self.to_rgb(image)
        l_img = rgb_img.convert("L")

        if num_channels == 1:
            return l_img

        return Image.merge("RGB", (l_img, l_img, l_img))

    def convert(
        self,
        image: Image.Image,
        mode: str,
        bg_color: Optional[Tuple[int, int, int]] = None,
    ) -> Image.Image:
        if not isinstance(image, Image.Image):
            raise TypeError(f"Expected PIL.Image.Image, got {type(image)}")

        supported_modes = ("RGB", "RGBA", "L", "P", "1", "CMYK", "HSV", "LAB")
        if mode not in supported_modes:
            raise ValueError(f"Unsupported mode '{mode}'. Supported modes: {supported_modes}")

        if mode == "RGB":
            return self.to_rgb(image, bg_color=bg_color)
        if mode == "L":
            return self.to_grayscale(image, num_channels=1)

        return image.convert(mode)

    def is_grayscale(self, image: Image.Image) -> bool:
        if not isinstance(image, Image.Image):
            raise TypeError(f"Expected PIL.Image.Image, got {type(image)}")

        if image.mode in ("L", "1", "I", "F"):
            return True

        if image.mode == "RGB":
            r, g, b = image.split()
            return r.tobytes() == g.tobytes() == b.tobytes()

        return False

    def is_rgb(self, image: Image.Image) -> bool:
        if not isinstance(image, Image.Image):
            raise TypeError(f"Expected PIL.Image.Image, got {type(image)}")
        return image.mode == "RGB"
```

---

## 6. Unit Test Specification (`tests/unit/test_visual_processing.py`)

In compliance with `TEST_INFRA.md`, at least 5 Tier 1 tests and 5 Tier 2 tests must be defined.

### 6.1 Tier 1 Tests (Normal Functionality & Happy Paths)

1. **`test_image_resizer_basic_resize`**:
   - Create 800x600 test image.
   - Resize to (400, 300) with `preserve_aspect_ratio=False`.
   - Assert output size == (400, 300).

2. **`test_image_resizer_aspect_ratio_preserve`**:
   - Create 1000x500 test image (2:1 aspect ratio).
   - Resize to (400, 400) with `preserve_aspect_ratio=True`, `pad=False`.
   - Assert output size == (400, 200).

3. **`test_image_resizer_aspect_ratio_padded`**:
   - Create 1000x500 test image.
   - Resize to (400, 400) with `preserve_aspect_ratio=True`, `pad=True`, `padding_color=(0,0,0)`.
   - Assert output size == (400, 400). Top/bottom padding is black.

4. **`test_image_resizer_tiling_2x2`**:
   - Create 400x400 test image.
   - Tile with `grid_size=(2, 2)`.
   - Assert output list length == 4. Each tile size == (200, 200).

5. **`test_color_converter_to_rgb_from_rgba`**:
   - Create 100x100 RGBA image with alpha transparency (0.5).
   - Convert via `to_rgb(bg_color=(255, 255, 255))`.
   - Assert output mode == `"RGB"`.

6. **`test_color_converter_to_grayscale_1ch_and_3ch`**:
   - Create 100x100 RGB image.
   - Convert to 1-channel grayscale -> assert mode == `"L"`, size == (100, 100).
   - Convert to 3-channel grayscale -> assert mode == `"RGB"`, `is_grayscale()` is `True`.

### 6.2 Tier 2 Tests (Boundary Conditions & Error Cases)

1. **`test_image_resizer_invalid_inputs`**:
   - Pass string/list instead of `PIL.Image.Image` -> verify `TypeError`.
   - Pass invalid `target_size=(0, 100)` or `(-10, 20)` -> verify `ValueError`.
   - Pass `grid_size=(0, 2)` -> verify `ValueError`.

2. **`test_image_resizer_odd_dimensions_tiling`**:
   - Create 101x101 image.
   - Tile into `(3, 3)` grid.
   - Assert 9 tiles returned and total pixel coverage spans `[0, 101]` without index error or missing border pixels.

3. **`test_color_converter_invalid_channels_and_mode`**:
   - `to_grayscale(img, num_channels=2)` -> verify `ValueError`.
   - `convert(img, mode="INVALID_MODE")` -> verify `ValueError`.

4. **`test_coordinate_mapping_accuracy`**:
   - Test `map_tile_coordinates_to_original(10, 20, (100, 200, 300, 400))` -> yields `(110, 220)`.
   - Test `map_resized_coordinates_to_original` for padded/scaled image.

5. **`test_color_converter_transparent_rgba_composite`**:
   - Create fully transparent RGBA pixel `(0, 0, 0, 0)`.
   - Convert to RGB with white background `(255, 255, 255)`.
   - Assert resulting pixel is pure white `(255, 255, 255)`, verifying background alpha blending logic.

---

## 7. Package Exports (`omnibench/visual/__init__.py`)

To ensure clean imports across the codebase, `omnibench/visual/__init__.py` must export:

```python
from omnibench.visual.processing import ImageResizer, ColorConverter

__all__ = [
    "ImageResizer",
    "ColorConverter",
]
```

---

## 8. Verification & Next Steps for Implementation Team

1. Create module directory `omnibench/visual/` and file `omnibench/visual/processing.py`.
2. Implement `ImageResizer` and `ColorConverter` as designed above.
3. Write `omnibench/visual/__init__.py`.
4. Implement test suite in `tests/unit/test_visual_processing.py`.
5. Run unit tests using `pytest tests/unit/test_visual_processing.py`.
