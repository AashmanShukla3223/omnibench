"""
OmniBench Visual Grounding & Set-of-Marks Preprocessor - Set-of-Marks (SoM) Generator.
Contains MarkMap and SoMAnnotator implementations.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
from PIL import Image, ImageDraw, ImageFont


DEFAULT_PALETTE: List[Tuple[int, int, int]] = [
    (230, 25, 75),    # Red
    (60, 180, 75),    # Green
    (255, 225, 25),   # Yellow
    (0, 130, 200),    # Blue
    (245, 130, 48),   # Orange
    (145, 30, 180),   # Purple
    (70, 240, 240),   # Cyan
    (240, 50, 230),   # Magenta
    (210, 245, 60),   # Lime
    (250, 190, 212),  # Pink
]


@dataclass
class MarkData:
    """Detailed container for an annotated mark entry."""
    mark_id: int
    bbox: Tuple[int, int, int, int]  # (x_min, y_min, x_max, y_max)
    center: Tuple[int, int]          # (x_center, y_center)
    label: Optional[str] = None
    score: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class MarkMap:
    """Bidirectional mapping between numeric mark IDs and screen coordinates."""

    def __init__(
        self,
        marks: Optional[Dict[int, Tuple[int, int, int, int]]] = None,
        image_size: Optional[Tuple[int, int]] = None,
    ) -> None:
        self.image_size: Optional[Tuple[int, int]] = image_size
        self._marks: Dict[int, Tuple[int, int, int, int]] = {}
        self._metadata: Dict[int, Dict[str, Any]] = {}

        if marks:
            for mark_id, bbox in marks.items():
                self.add_mark(int(mark_id), bbox)

    def add_mark(
        self,
        mark_id: int,
        bbox: Tuple[int, int, int, int],
        label: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not (isinstance(bbox, (tuple, list)) and len(bbox) == 4):
            raise ValueError(f"bbox must be a tuple/list of 4 integers, got {bbox}")
        x_min, y_min, x_max, y_max = bbox
        if x_min > x_max or y_min > y_max:
            raise ValueError(f"Invalid bbox coordinates for mark {mark_id}: {bbox}")
        self._marks[int(mark_id)] = (int(x_min), int(y_min), int(x_max), int(y_max))
        self._metadata[int(mark_id)] = {
            "label": label,
            "metadata": metadata or {},
        }

    def get_coordinates(self, mark_id: int) -> Tuple[int, int]:
        """Return (x_center, y_center) target click coordinates for mark_id."""
        if int(mark_id) not in self._marks:
            raise KeyError(f"Mark ID '{mark_id}' not found in MarkMap.")
        x_min, y_min, x_max, y_max = self._marks[int(mark_id)]
        return ((x_min + x_max) // 2, (y_min + y_max) // 2)

    def get_bbox(self, mark_id: int) -> Tuple[int, int, int, int]:
        """Return (x_min, y_min, x_max, y_max) bounding box for mark_id."""
        if int(mark_id) not in self._marks:
            raise KeyError(f"Mark ID '{mark_id}' not found in MarkMap.")
        return self._marks[int(mark_id)]

    def get_mark_at(self, x: int, y: int) -> Optional[int]:
        """Reverse spatial lookup: return smallest area mark_id containing point (x, y)."""
        matching_marks: List[Tuple[int, int]] = []  # (area, mark_id)
        for mark_id, (x_min, y_min, x_max, y_max) in self._marks.items():
            if x_min <= x <= x_max and y_min <= y <= y_max:
                area = (x_max - x_min) * (y_max - y_min)
                matching_marks.append((area, mark_id))

        if not matching_marks:
            return None
        # Sort by area ascending so smallest containing box takes precedence
        matching_marks.sort(key=lambda item: item[0])
        return matching_marks[0][1]

    def remove_mark(self, mark_id: int) -> bool:
        mid = int(mark_id)
        if mid in self._marks:
            del self._marks[mid]
            self._metadata.pop(mid, None)
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize MarkMap to dictionary representation."""
        return {
            "image_size": list(self.image_size) if self.image_size else None,
            "marks": {
                str(mark_id): {
                    "bbox": list(bbox),
                    "center": list(self.get_coordinates(mark_id)),
                    "label": self._metadata.get(mark_id, {}).get("label"),
                    "metadata": self._metadata.get(mark_id, {}).get("metadata"),
                }
                for mark_id, bbox in self._marks.items()
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MarkMap":
        """Deserialize MarkMap from dictionary representation."""
        image_size_raw = data.get("image_size")
        image_size = tuple(image_size_raw) if image_size_raw else None
        instance = cls(image_size=image_size)
        raw_marks = data.get("marks", {})
        for mark_id_str, info in raw_marks.items():
            mark_id = int(mark_id_str)
            bbox = tuple(info["bbox"])
            label = info.get("label")
            metadata = info.get("metadata")
            instance.add_mark(mark_id, bbox, label=label, metadata=metadata)
        return instance

    def __getitem__(self, mark_id: int) -> Tuple[int, int, int, int]:
        return self.get_bbox(mark_id)

    def __contains__(self, mark_id: int) -> bool:
        return int(mark_id) in self._marks

    def __len__(self) -> int:
        return len(self._marks)

    def __iter__(self):
        return iter(self._marks)

    def __repr__(self) -> str:
        return f"MarkMap(count={len(self._marks)}, image_size={self.image_size})"


class SoMAnnotator:
    """Set-of-Marks (SoM) bounding box and numerical mark overlay annotator."""

    def __init__(
        self,
        line_width: int = 2,
        color_palette: Optional[List[Union[str, Tuple[int, int, int]]]] = None,
        font_size: int = 14,
        font_path: Optional[str] = None,
        badge_position: str = "top_left",
        grid_rows: int = 4,
        grid_cols: int = 4,
    ) -> None:
        self.line_width: int = max(1, line_width)
        self.color_palette: List[Tuple[int, int, int]] = self._normalize_palette(color_palette)
        self.font_size: int = font_size
        self.font_path: Optional[str] = font_path
        self.badge_position: str = badge_position
        self.grid_rows: int = max(1, grid_rows)
        self.grid_cols: int = max(1, grid_cols)
        self._font: ImageFont.ImageFont = self._load_font()

    def _normalize_palette(
        self, palette: Optional[List[Union[str, Tuple[int, int, int]]]]
    ) -> List[Tuple[int, int, int]]:
        if not palette:
            return DEFAULT_PALETTE
        normalized = []
        for color in palette:
            if isinstance(color, (tuple, list)) and len(color) == 3:
                normalized.append((int(color[0]), int(color[1]), int(color[2])))
            elif isinstance(color, str):
                hex_str = color.lstrip("#")
                if len(hex_str) == 6:
                    try:
                        normalized.append(tuple(int(hex_str[i : i + 2], 16) for i in (0, 2, 4)))
                    except ValueError:
                        normalized.append((255, 0, 0))
                else:
                    normalized.append((255, 0, 0))
        return normalized or DEFAULT_PALETTE

    def _load_font(self) -> ImageFont.ImageFont:
        if self.font_path:
            try:
                return ImageFont.truetype(self.font_path, self.font_size)
            except Exception:
                pass
        return ImageFont.load_default()

    def annotate(
        self,
        screenshot: Image.Image,
        elements: Optional[List[Dict[str, Any]]] = None,
    ) -> Tuple[Image.Image, MarkMap]:
        """
        Annotates screenshot with numeric marks and bounding box overlays.

        Args:
            screenshot: PIL Image object.
            elements: Optional list of UI element dicts containing bbox specifications.

        Returns:
            Tuple of (annotated_image, mark_map).
        """
        if not isinstance(screenshot, Image.Image):
            raise TypeError("screenshot must be a PIL.Image.Image instance.")

        width, height = screenshot.size
        if width <= 0 or height <= 0:
            raise ValueError(f"Invalid screenshot dimensions: {screenshot.size}")

        # Non-mutating copy in RGB mode
        annotated_img = screenshot.copy().convert("RGB")
        draw = ImageDraw.Draw(annotated_img, mode="RGBA")
        mark_map = MarkMap(image_size=(width, height))

        # Parse or generate elements
        parsed_elements = self._prepare_elements(elements, width, height)

        for idx, elem in enumerate(parsed_elements, start=1):
            mark_id = idx
            bbox = elem["bbox"]
            label = elem.get("label")
            color = self.color_palette[(idx - 1) % len(self.color_palette)]

            # 1. Draw Bounding Box Rectangle
            draw.rectangle(bbox, outline=color + (255,), width=self.line_width)

            # 2. Draw Numeric Badge Overlay
            self._draw_badge(draw, mark_id, bbox, color, width, height)

            # 3. Record in MarkMap
            mark_map.add_mark(mark_id, bbox, label=label, metadata=elem.get("metadata"))

        return annotated_img, mark_map

    def _prepare_elements(
        self,
        elements: Optional[List[Dict[str, Any]]],
        width: int,
        height: int,
    ) -> List[Dict[str, Any]]:
        if not elements:
            return self._generate_grid_elements(width, height)

        valid_elements = []
        for elem in elements:
            bbox = self._extract_bbox(elem, width, height)
            if bbox:
                valid_elements.append({
                    "bbox": bbox,
                    "label": elem.get("label") if isinstance(elem, dict) else None,
                    "metadata": elem.get("metadata", {}) if isinstance(elem, dict) else {},
                })
        return valid_elements or self._generate_grid_elements(width, height)

    def _extract_bbox(
        self, elem: Union[Dict[str, Any], Tuple, List], width: int, height: int
    ) -> Optional[Tuple[int, int, int, int]]:
        raw_box = None
        if isinstance(elem, dict):
            if "bbox" in elem:
                raw_box = elem["bbox"]
            elif "box" in elem:
                raw_box = elem["box"]
            elif all(k in elem for k in ("x_min", "y_min", "x_max", "y_max")):
                raw_box = (elem["x_min"], elem["y_min"], elem["x_max"], elem["y_max"])
        elif isinstance(elem, (list, tuple)) and len(elem) == 4:
            raw_box = elem

        if not raw_box or len(raw_box) != 4:
            return None

        x_min = max(0, min(width - 1, int(raw_box[0])))
        y_min = max(0, min(height - 1, int(raw_box[1])))
        x_max = max(x_min + 1, min(width, int(raw_box[2])))
        y_max = max(y_min + 1, min(height, int(raw_box[3])))

        return (x_min, y_min, x_max, y_max)

    def _generate_grid_elements(self, width: int, height: int) -> List[Dict[str, Any]]:
        elements = []
        cell_w = width / self.grid_cols
        cell_h = height / self.grid_rows

        for r in range(self.grid_rows):
            for c in range(self.grid_cols):
                x_min = int(c * cell_w)
                y_min = int(r * cell_h)
                x_max = int((c + 1) * cell_w)
                y_max = int((r + 1) * cell_h)
                elements.append({
                    "bbox": (x_min, y_min, x_max, y_max),
                    "label": f"grid_{r}_{c}",
                    "metadata": {"row": r, "col": c},
                })
        return elements

    def _draw_badge(
        self,
        draw: ImageDraw.Draw,
        mark_id: int,
        bbox: Tuple[int, int, int, int],
        color: Tuple[int, int, int],
        img_width: int,
        img_height: int,
    ) -> None:
        text_str = str(mark_id)
        x_min, y_min, x_max, y_max = bbox

        # Get text bounding box for exact sizing
        text_bbox = draw.textbbox((0, 0), text_str, font=self._font)
        text_w = text_bbox[2] - text_bbox[0]
        text_h = text_bbox[3] - text_bbox[1]

        padding = 2
        badge_w = text_w + (padding * 2) + 2
        badge_h = text_h + (padding * 2) + 2

        # Position determination
        if self.badge_position == "top_left":
            badge_x = x_min
            badge_y = y_min
        elif self.badge_position == "outside_top":
            badge_x = x_min
            badge_y = max(0, y_min - badge_h)
        elif self.badge_position == "center":
            badge_x = (x_min + x_max - badge_w) // 2
            badge_y = (y_min + y_max - badge_h) // 2
        else:
            badge_x = x_min
            badge_y = y_min

        # Clamp badge to image boundaries
        badge_x = max(0, min(img_width - badge_w, badge_x))
        badge_y = max(0, min(img_height - badge_h, badge_y))

        # Solid badge background
        badge_rect = [badge_x, badge_y, badge_x + badge_w, badge_y + badge_h]
        draw.rectangle(badge_rect, fill=color + (230,), outline=(0, 0, 0, 255))

        # Text rendering (white or black depending on color luminance)
        luminance = 0.299 * color[0] + 0.587 * color[1] + 0.114 * color[2]
        text_color = (0, 0, 0) if luminance > 160 else (255, 255, 255)

        draw.text(
            (badge_x + padding + 1, badge_y + padding),
            text_str,
            fill=text_color,
            font=self._font,
        )
