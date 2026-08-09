# Scope: Milestone M3 — Visual Grounding & Set-of-Marks Preprocessor

## Architecture
Milestone M3 implements the visual processing, memory management, and visual grounding engine for OmniBench 1.0. It is located in `omnibench/visual/` and comprises three core modules:
1. `processing.py`: `ImageResizer` (resizing, downscaling, grid tiling) and `ColorConverter` (RGB, Grayscale conversions).
2. `memory.py`: `SlidingTrajectoryMemory` (strictly bounded 3-screenshot buffer, text action log maintaining history, state representation `MemoryState`).
3. `som.py`: `SoMAnnotator` (UI element bounding box annotator drawing numeric marks) and `MarkMap` (bidirectional mapping between mark IDs and bounding box coordinates/centers).

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 11 | Screen Processing Pipeline | `ImageResizer` (tiling/downscaling) and `ColorConverter` (RGB/Grayscale) | M3 | R3 |
| 12 | Sliding Trajectory Memory | Strictly bounded 3-screenshot memory buffer + text action logs | M3 | R3 |
| 13 | Set-of-Marks (SoM) Generator | Interactive UI bounding box annotator & bidirectional `MarkMap` lookup | M3 | R3 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M3.1 | Screen Processing Pipeline | `omnibench/visual/processing.py` | none | IN_PROGRESS |
| M3.2 | Sliding Trajectory Memory | `omnibench/visual/memory.py` | M3.1 | IN_PROGRESS |
| M3.3 | Set-of-Marks (SoM) Generator | `omnibench/visual/som.py` | M3.1 | IN_PROGRESS |

## Interface Contracts
### `omnibench.visual` Interface
- `ImageResizer.resize(image: Image, target_size: tuple[int, int]) -> Image`
- `ImageResizer.tile(image: Image, grid_size: tuple[int, int]) -> list[Image]`
- `ColorConverter.to_grayscale(image: Image) -> Image`
- `ColorConverter.to_rgb(image: Image) -> Image`
- `SlidingTrajectoryMemory.add_step(screenshot: Image, action_str: str) -> MemoryState`
- `MemoryState.screenshots: list[Image]` (max length 3)
- `MemoryState.action_logs: list[str]`
- `SoMAnnotator.annotate(screenshot: Image, elements: list[dict] | None = None) -> tuple[Image, MarkMap]`
- `MarkMap.get_coordinates(mark_id: int) -> tuple[int, int]` (center point or target point)
- `MarkMap.get_bbox(mark_id: int) -> tuple[int, int, int, int]` (x_min, y_min, x_max, y_max)

## Code Layout
- `omnibench/visual/__init__.py`
- `omnibench/visual/processing.py`
- `omnibench/visual/memory.py`
- `omnibench/visual/som.py`
- `tests/unit/test_visual.py`
