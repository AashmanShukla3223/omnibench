# Scope: Milestone M3 — Visual Grounding & Set-of-Marks (SoM)

## Target Module
`omnibench/visual/` (`processing.py`, `som.py`, `memory.py`)

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 11 | Screen Processing Pipeline | ImageResizer (tiling/downscaling) and ColorConverter (RGB/Grayscale) | M3 | R3 |
| 12 | Sliding Trajectory Memory | Strictly bounded 3-screenshot memory buffer + text action logs | M3 | R3 |
| 13 | Set-of-Marks (SoM) Generator | Interactive UI bounding box annotator & bidirectional MarkMap lookup | M3 | R3 |

## Interface Contracts
- `SoMAnnotator.annotate(screenshot: Image) -> tuple[Image, MarkMap]`
- `MarkMap.get_coordinates(mark_id: int) -> tuple[int, int]`
- `SlidingTrajectoryMemory.add_step(screenshot: Image, action_str: str) -> MemoryState`

## Detailed Component Specifications
1. **`ImageResizer`** (`omnibench/visual/processing.py`):
   - Downscaling: downscale images to target resolution while preserving aspect ratio or fitting max dimensions.
   - Grid Tiling: split high-res images into grid tiles for fine-grained VLM attention with tile coordinate mapping.
2. **`ColorConverter`** (`omnibench/visual/processing.py`):
   - Support conversions between RGB, Grayscale, BGR, HSV, RGBA as needed, keeping PIL Image or NumPy array formats clean.
3. **`SlidingTrajectoryMemory`** (`omnibench/visual/memory.py`):
   - Strictly bounded 3-screenshot FIFO buffer (oldest dropped when 4th added).
   - Text action log history tracking for full action trajectory.
   - Returns `MemoryState` snapshot object containing current buffer of images and action log history.
4. **`SoMAnnotator`** (`omnibench/visual/som.py`):
   - Annotate screenshot with numbered bounding box badges over detected or provided UI elements.
   - Generates bidirectional `MarkMap` mapping mark ID integer <-> center coordinates `(x, y)` and bounding box `(x1, y1, x2, y2)`.
   - `MarkMap.get_coordinates(mark_id: int) -> tuple[int, int]` returns center `(x, y)` of mark ID.

## Code Layout
`omnibench/visual/`
- `__init__.py`
- `processing.py` (`ImageResizer`, `ColorConverter`)
- `som.py` (`SoMAnnotator`, `MarkMap`)
- `memory.py` (`SlidingTrajectoryMemory`, `MemoryState`)
`tests/unit/test_visual.py`
