"""
OmniBench Visual Grounding & Set-of-Marks Preprocessor - Screen Processing Pipeline.
Contains ImageResizer and ColorConverter implementations.
"""

import math
from typing import List, Tuple, Optional, Union, Dict, Any
from PIL import Image


class ImageResizer:
    """
    Handles image scaling, aspect ratio preservation, grid tiling,
    downscaling, and coordinate transformation mapping for visual grounding.
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
            if not (isinstance(max_dimension[0], int) and isinstance(max_dimension[1], int)):
                raise ValueError(f"max_dimension values must be integers, got {max_dimension}")
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

        if not isinstance(overlap, int) or overlap < 0:
            raise ValueError(f"overlap must be a non-negative integer, got {overlap}")

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
