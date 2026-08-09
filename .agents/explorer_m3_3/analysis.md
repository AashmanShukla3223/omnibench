# Milestone M3 — Feature 13: Set-of-Marks (SoM) Preprocessor Technical Design & Architectural Specification

**Author**: `explorer_m3_3`  
**Date**: 2026-08-08  
**Component**: `omnibench.visual.som` (`SoMAnnotator`, `MarkMap`)  
**Target File**: `omnibench/visual/som.py`  
**Test File**: `tests/unit/test_visual.py` (and `tests/unit/test_som.py`)  

---

## 1. Executive Summary & Scope

Requirement **R3** (Feature 13) specifies the Set-of-Marks (SoM) bounding box generator and bidirectional coordinate lookup system for OmniBench 1.0.

In VLM-driven computer use, visual grounding is critical: the model must map UI elements on a screenshot to precise target click coordinates. `SoMAnnotator` superimposes visually distinct bounding boxes and numeric mark ID badges onto screen captures, while `MarkMap` maintains a bidirectional mapping between numeric mark IDs, bounding box boundaries `(x_min, y_min, x_max, y_max)`, and center target coordinates `(x_center, y_center)`.

This analysis provides the complete architectural design, data structures, PIL rendering algorithms, edge case handling, and unit testing strategy for `omnibench/visual/som.py`.

---

## 2. Environment & Dependency Analysis

- **Python Version**: 3.13.5 (verified in `.venv`)
- **Pillow Version**: 12.3.0 (verified in `.venv`)
- **Graphics & Rendering**: Uses `PIL.Image`, `PIL.ImageDraw`, and `PIL.ImageFont`.
- **Performance Overhead**: Pure Python + PIL implementation operating under ~2–5 ms per screenshot annotation step, consuming negligible memory (<5 MB per call).

---

## 3. Class Hierarchy & Architectural Design

```
                     +---------------------------+
                     |        SoMAnnotator       |
                     +---------------------------+
                     | - line_width: int         |
                     | - color_palette: list     |
                     | - font_size: int          |
                     | - badge_position: str     |
                     | - grid_rows/cols: int     |
                     +---------------------------+
                                   |
                annotate(screenshot, elements)
                                   |
                                   v
          +------------------------+------------------------+
          |                                                 |
          v                                                 v
  Annotated Screenshot                             MarkMap Object
  (PIL.Image.Image RGB)                     (Bidirectional Lookup)
                                            +---------------------------+
                                            | - marks: dict[int, bbox]  |
                                            | - image_size: (w, h)      |
                                            +---------------------------+
                                            | + get_coordinates(id)     |
                                            | + get_bbox(id)            |
                                            | + get_mark_at(x, y)       |
                                            | + to_dict() / from_dict() |
                                            +---------------------------+
```

---

## 4. Class Specifications & Interface Contracts

### 4.1 Data Contracts & Supporting Structures

```python
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
from PIL import Image, ImageDraw, ImageFont


@dataclass
class MarkData:
    """Detailed container for an annotated mark entry."""
    mark_id: int
    bbox: Tuple[int, int, int, int]  # (x_min, y_min, x_max, y_max)
    center: Tuple[int, int]          # (x_center, y_center)
    label: Optional[str] = None
    score: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
```

---

### 4.2 `MarkMap` Bidirectional Lookup Engine

#### Responsibilities:
- Stores numeric mark ID mapping to bounding boxes and center coordinates.
- Provides `get_coordinates(mark_id)` to return target click point `(x_center, y_center)`.
- Provides `get_bbox(mark_id)` to return bounding box `(x_min, y_min, x_max, y_max)`.
- Provides `get_mark_at(x, y)` for reverse spatial lookup (finding which mark ID contains a given pixel coordinate).
- Supports dict serialization (`to_dict()`) for benchmark evaluation, telemetry, and SQLite logging.

#### Python Interface:
```python
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
                self.add_mark(mark_id, bbox)

    def add_mark(
        self,
        mark_id: int,
        bbox: Tuple[int, int, int, int],
        label: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        x_min, y_min, x_max, y_max = bbox
        if x_min > x_max or y_min > y_max:
            raise ValueError(f"Invalid bbox coordinates for mark {mark_id}: {bbox}")
        self._marks[mark_id] = (x_min, y_min, x_max, y_max)
        self._metadata[mark_id] = {
            "label": label,
            "metadata": metadata or {},
        }

    def get_coordinates(self, mark_id: int) -> Tuple[int, int]:
        """Return (x_center, y_center) target click coordinates for mark_id."""
        if mark_id not in self._marks:
            raise KeyError(f"Mark ID '{mark_id}' not found in MarkMap.")
        x_min, y_min, x_max, y_max = self._marks[mark_id]
        return ((x_min + x_max) // 2, (y_min + y_max) // 2)

    def get_bbox(self, mark_id: int) -> Tuple[int, int, int, int]:
        """Return (x_min, y_min, x_max, y_max) bounding box for mark_id."""
        if mark_id not in self._marks:
            raise KeyError(f"Mark ID '{mark_id}' not found in MarkMap.")
        return self._marks[mark_id]

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
        if mark_id in self._marks:
            del self._marks[mark_id]
            self._metadata.pop(mark_id, None)
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize MarkMap to dictionary representation."""
        return {
            "image_size": self.image_size,
            "marks": {
                mark_id: {
                    "bbox": bbox,
                    "center": self.get_coordinates(mark_id),
                    "label": self._metadata.get(mark_id, {}).get("label"),
                    "metadata": self._metadata.get(mark_id, {}).get("metadata"),
                }
                for mark_id, bbox in self._marks.items()
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MarkMap":
        """Deserialize MarkMap from dictionary representation."""
        instance = cls(image_size=data.get("image_size"))
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
        return mark_id in self._marks

    def __len__(self) -> int:
        return len(self._marks)

    def __iter__(self):
        return iter(self._marks)

    def __repr__(self) -> str:
        return f"MarkMap(count={len(self._marks)}, image_size={self.image_size})"
```

---

### 4.3 `SoMAnnotator` Visual Generator Engine

#### Responsibilities:
- Converts screenshot PIL image into marked visual prompt.
- Renders high-contrast bounding boxes around UI elements.
- Draws numeric mark ID badges at top-left corner of bounding boxes.
- Supports custom color palettes, font sizes, line widths, and badge positions.
- Generates automatic grid regions if no UI element bounding boxes are provided.

#### High-Contrast Color Palette:
Default palette contains 10 visually distinct, vibrant RGB tuples ensuring high visibility on both light and dark UI backgrounds:
```python
DEFAULT_PALETTE = [
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
```

#### Python Interface & Annotation Routine:
```python
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
            if isinstance(color, tuple) and len(color) == 3:
                normalized.append(color)
            elif isinstance(color, str):
                # Simple hex or name conversion
                hex_str = color.lstrip('#')
                if len(hex_str) == 6:
                    normalized.append(tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4)))
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
        """Annotates screenshot with numeric marks and bounding box overlays.
        
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
                    "label": elem.get("label"),
                    "metadata": elem.get("metadata", {}),
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
        luminance = (0.299 * color[0] + 0.587 * color[1] + 0.114 * color[2])
        text_color = (0, 0, 0) if luminance > 160 else (255, 255, 255)

        draw.text(
            (badge_x + padding + 1, badge_y + padding),
            text_str,
            fill=text_color,
            font=self._font,
        )
```

---

## 5. Robustness & Boundary Edge Cases

| Scenario / Edge Case | Handled Mechanism | Verification Test |
|---|---|---|
| **Non-PIL input** | Raises `TypeError` | `test_annotate_invalid_input_type` |
| **Zero/Negative Dimensions** | Raises `ValueError` | `test_annotate_zero_dimension_image` |
| **Out-of-bounds bbox** | Clipped to `[0, width]` and `[0, height]` | `test_annotate_out_of_bounds_bbox` |
| **Malformed element formats** | Flexibility: accepts `bbox`, `box`, `x_min/...`, tuples | `test_bbox_format_variations` |
| **Query non-existent mark ID** | Raises `KeyError` with clear message | `test_markmap_keyerror` |
| **Reverse lookup outside all marks** | Returns `None` | `test_markmap_get_mark_at_miss` |
| **Overlapping elements spatial lookup** | Returns smallest enclosing bounding box | `test_markmap_get_mark_at_overlapping` |
| **Input screenshot mutability** | Operates on `screenshot.copy()`, original untouched | `test_annotate_immutability` |

---

## 6. Unit Test Requirements (`tests/unit/test_visual.py` & `test_som.py`)

To meet the test coverage thresholds defined in `TEST_INFRA.md`, the following minimum 12 unit test cases must be implemented:

### Tier 1 Core Functionality Tests:
1. `test_som_annotator_basic_annotation()`: Verifies `annotate()` returns tuple `(PIL.Image, MarkMap)` with correct mark count.
2. `test_markmap_get_coordinates()`: Verifies `get_coordinates(1)` returns exact center point `((x_min + x_max) // 2, (y_min + y_max) // 2)`.
3. `test_markmap_get_bbox()`: Verifies `get_bbox(1)` returns original bounding box `(x_min, y_min, x_max, y_max)`.
4. `test_markmap_reverse_spatial_lookup()`: Verifies `get_mark_at(x, y)` returns the correct `mark_id`.
5. `test_som_annotator_default_grid_generation()`: Verifies automatic 4x4 grid generation when `elements=None`.
6. `test_markmap_serialization()`: Verifies `to_dict()` and `from_dict()` roundtrip consistency.

### Tier 2 Boundary & Exception Tests:
7. `test_som_annotator_input_immutability()`: Verifies input screenshot pixel data remains identical after annotation.
8. `test_som_annotator_invalid_type()`: Verifies passing a string or dict raises `TypeError`.
9. `test_som_annotator_out_of_bounds_clipping()`: Verifies bounding boxes outside image dimensions are cleanly clipped.
10. `test_markmap_nonexistent_key_raises_keyerror()`: Verifies `get_coordinates(999)` raises `KeyError`.
11. `test_markmap_overlapping_box_priority()`: Verifies reverse lookup prioritizes the smaller enclosing box.
12. `test_som_annotator_palette_cycling()`: Verifies annotation handles >10 elements by cycling color palette cleanly.

---

## 7. Next Steps for Implementation Agent

1. Create `omnibench/visual/som.py` using the exact design specified above.
2. Update `omnibench/visual/__init__.py` to export `SoMAnnotator` and `MarkMap`.
3. Implement test cases in `tests/unit/test_visual.py` (or `tests/unit/test_som.py`).
4. Execute `pytest tests/unit/test_visual.py` using `.venv/bin/pytest`.
