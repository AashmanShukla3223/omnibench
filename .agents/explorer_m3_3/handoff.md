# Handoff Report: Set-of-Marks (SoM) Generator & MarkMap Lookup Design

**Agent**: `explorer_m3_3`  
**Milestone**: M3 — Visual Grounding & Set-of-Marks Preprocessor  
**Target Module**: `omnibench/visual/som.py` (`SoMAnnotator`, `MarkMap`)  
**Date**: 2026-08-08  

---

## 1. Observation

- **Authoritative Specifications**:
  - `ORIGINAL_REQUEST.md`: Requirement R3 specifies Set-of-Marks (SoM) visual processing and element bounding box overlay for target grounding.
  - `PROJECT.md` & `.agents/orch_m3_visual/SCOPE.md`: Define `SoMAnnotator.annotate(screenshot: Image, elements: list[dict] | None = None) -> tuple[Image, MarkMap]`, `MarkMap.get_coordinates(mark_id: int) -> tuple[int, int]`, and `MarkMap.get_bbox(mark_id: int) -> tuple[int, int, int, int]`.
  - `TEST_INFRA.md`: Requires minimum 5 Tier 1 unit tests and 5 Tier 2 boundary tests for Feature 13 (Set-of-Marks Generator).
- **Environment Verification**:
  - Python 3.13.5 and Pillow 12.3.0 are installed in `.venv`.
  - `PIL.ImageDraw.Draw.textbbox` is verified and operational for accurate numeric badge dimensioning.
- **Codebase Context**:
  - `omnibench/visual/` is designated for `processing.py`, `memory.py`, and `som.py`.

---

## 2. Logic Chain

1. **VLM Visual Grounding Requirement**: Computer use vision-language models issue actions by referencing visual mark IDs (e.g., `click(mark_id=3)`).
2. **Annotation Routine Design**: `SoMAnnotator` converts input screenshots into annotated images by drawing high-contrast bounding boxes (using a 10-color RGB palette) and drawing prominent numerical mark badges at element corners.
3. **Automatic Fallback Grid**: If explicit UI element bounding boxes are not provided (`elements=None`), `SoMAnnotator` automatically partitions the screen into a configurable grid (default 4x4) to ensure grounding is always available.
4. **Bidirectional Lookup Contract**: `MarkMap` maintains forward lookups (`get_coordinates` for center click point, `get_bbox` for box boundaries) and reverse spatial lookups (`get_mark_at(x, y)`).
5. **Data Integrity & Non-Mutability**: `annotate()` operates on `screenshot.copy().convert("RGB")` to guarantee that original screenshot memory buffers are never mutated in place.

---

## 3. Caveats

- **External Object Detection Models**: `SoMAnnotator` provides the drawing engine, automatic grid generator, and bbox parser. It does not embed a heavy neural UI detection model (e.g. YOLO/Florence-2), keeping execution CPU-friendly and lightweight. Bounding box coordinates from external detectors or DOM trees are passed in via `elements`.
- **Font Rendering Fallback**: `ImageFont.load_default()` is used when custom TTF fonts are absent. Badge padding accommodates font scaling dynamically using `draw.textbbox`.

---

## 4. Conclusion

The complete architectural design, API contracts, PIL drawing routines, boundary protections, and unit test specifications for Feature 13 (`SoMAnnotator` and `MarkMap`) are finalized and documented in `/home/oh_my_macos27/OmniBench Computer Use/.agents/explorer_m3_3/analysis.md`. The design is fully compatible with Python 3.13, Pillow 12.3.0, and the OmniBench 1.0 visual grounding pipeline.

---

## 5. Verification Method

To independently verify the design and implementation when `omnibench/visual/som.py` is created:

1. **File Inspection**:
   - Inspect `/home/oh_my_macos27/OmniBench Computer Use/.agents/explorer_m3_3/analysis.md` for class and algorithm specs.
2. **Code Verification**:
   - Verify `omnibench/visual/som.py` implements `SoMAnnotator` and `MarkMap`.
   - Verify `omnibench/visual/__init__.py` exports both classes.
3. **Unit Test Execution**:
   - Run the test suite:
     ```bash
     .venv/bin/pytest tests/unit/test_visual.py -v
     ```
   - Invalidation conditions: Any test failure, unhandled `KeyError` on invalid mark IDs, or mutation of the input PIL Image.
