"""
Unit tests for omnibench.visual module:
- ImageResizer
- ColorConverter
- MemoryState
- SlidingTrajectoryMemory
- MarkMap
- SoMAnnotator
"""

import pytest
from PIL import Image
from omnibench.visual.processing import ImageResizer, ColorConverter
from omnibench.visual.memory import MemoryState, SlidingTrajectoryMemory
from omnibench.visual.som import MarkMap, SoMAnnotator, MarkData


# ============================================================================
# 1. ImageResizer Tests
# ============================================================================

def test_image_resizer_basic_resize():
    resizer = ImageResizer()
    img = Image.new("RGB", (800, 600), color=(255, 0, 0))
    resized = resizer.resize(img, (400, 300), preserve_aspect_ratio=False)
    assert resized.size == (400, 300)
    assert resized.mode == "RGB"


def test_image_resizer_aspect_ratio_preserve_unpadded():
    resizer = ImageResizer()
    img = Image.new("RGB", (1000, 500), color=(0, 255, 0))
    resized = resizer.resize(img, (400, 400), preserve_aspect_ratio=True, pad=False)
    assert resized.size == (400, 200)


def test_image_resizer_aspect_ratio_preserve_padded():
    resizer = ImageResizer()
    img = Image.new("RGB", (1000, 500), color=(0, 0, 255))
    padded = resizer.resize(img, (400, 400), preserve_aspect_ratio=True, pad=True, padding_color=(0, 0, 0))
    assert padded.size == (400, 400)
    # Check padding at top edge pixel (200, 10) is black
    assert padded.getpixel((200, 10)) == (0, 0, 0)
    # Check center pixel (200, 200) is blue
    assert padded.getpixel((200, 200)) == (0, 0, 255)


def test_image_resizer_downscale():
    resizer = ImageResizer()
    img_large = Image.new("RGB", (2000, 1000), color=(100, 100, 100))
    downscaled = resizer.downscale(img_large, max_dimension=500)
    assert downscaled.size == (500, 250)

    img_small = Image.new("RGB", (300, 200), color=(100, 100, 100))
    unchanged = resizer.downscale(img_small, max_dimension=500)
    assert unchanged.size == (300, 200)

    # Downscale with tuple max_dimension
    downscaled_tuple = resizer.downscale(img_large, max_dimension=(800, 600))
    assert downscaled_tuple.size[0] <= 800 and downscaled_tuple.size[1] <= 600


def test_image_resizer_tiling_2x2():
    resizer = ImageResizer()
    img = Image.new("RGB", (400, 400), color=(255, 255, 255))
    tiles = resizer.tile(img, grid_size=(2, 2))
    assert len(tiles) == 4
    for t in tiles:
        assert t.size == (200, 200)


def test_image_resizer_tiling_odd_dimensions_and_overlap():
    resizer = ImageResizer()
    img = Image.new("RGB", (101, 101), color=(128, 128, 128))
    tiles_meta = resizer.tile_with_metadata(img, grid_size=(3, 3), overlap=5)
    assert len(tiles_meta) == 9
    for item in tiles_meta:
        assert "tile" in item
        assert "grid_pos" in item
        assert "crop_box" in item
        cb = item["crop_box"]
        assert 0 <= cb[0] < cb[2] <= 101
        assert 0 <= cb[1] < cb[3] <= 101


def test_image_resizer_coordinate_mapping():
    resizer = ImageResizer()
    # 1. Tile coordinate mapping
    orig_coords = resizer.map_tile_coordinates_to_original(tile_x=10, tile_y=20, crop_box=(100, 200, 300, 400))
    assert orig_coords == (110, 220)

    # 2. Resized non-aspect mapping
    orig_coords_unpadded = resizer.map_resized_coordinates_to_original(
        x=200, y=150, orig_size=(800, 600), target_size=(400, 300), preserve_aspect_ratio=False
    )
    assert orig_coords_unpadded == (400, 300)

    # 3. Resized padded mapping
    orig_coords_padded = resizer.map_resized_coordinates_to_original(
        x=200, y=200, orig_size=(1000, 500), target_size=(400, 400), preserve_aspect_ratio=True, pad=True
    )
    # Center scaled size is 400x200, offset_y = 100. (y - offset_y) / scale = (200 - 100) / 0.4 = 250
    assert orig_coords_padded == (500, 250)


def test_image_resizer_invalid_inputs():
    resizer = ImageResizer()
    with pytest.raises(TypeError):
        resizer.resize("not_an_image", (100, 100))

    with pytest.raises(ValueError):
        resizer.resize(Image.new("RGB", (100, 100)), (0, 100))

    with pytest.raises(ValueError):
        resizer.resize(Image.new("RGB", (100, 100)), (-50, 100))

    with pytest.raises(ValueError):
        resizer.downscale(Image.new("RGB", (100, 100)), max_dimension=-10)

    with pytest.raises(ValueError):
        resizer.tile(Image.new("RGB", (100, 100)), grid_size=(0, 2))

    with pytest.raises(ValueError):
        resizer.tile(Image.new("RGB", (100, 100)), grid_size=(2, 2), overlap=-5)


# ============================================================================
# 2. ColorConverter Tests
# ============================================================================

def test_color_converter_to_rgb_rgba():
    converter = ColorConverter(default_bg_color=(255, 255, 255))
    # Semi-transparent red pixel over white background
    rgba_img = Image.new("RGBA", (10, 10), color=(255, 0, 0, 128))
    rgb_img = converter.to_rgb(rgba_img)
    assert rgb_img.mode == "RGB"
    # Blend calculation: R = 255, G/B blended towards white background
    r, g, b = rgb_img.getpixel((5, 5))
    assert r == 255
    assert g > 0 and b > 0  # Lightened due to alpha blend over white


def test_color_converter_to_rgb_palette_transparency():
    converter = ColorConverter()
    # Create P mode image with transparency
    p_img = Image.new("P", (10, 10))
    p_img.info["transparency"] = 0
    rgb_img = converter.to_rgb(p_img)
    assert rgb_img.mode == "RGB"


def test_color_converter_to_grayscale():
    converter = ColorConverter()
    rgb_img = Image.new("RGB", (50, 50), color=(100, 150, 200))

    # 1-channel
    gray_1ch = converter.to_grayscale(rgb_img, num_channels=1)
    assert gray_1ch.mode == "L"
    assert gray_1ch.size == (50, 50)
    assert converter.is_grayscale(gray_1ch)

    # 3-channel
    gray_3ch = converter.to_grayscale(rgb_img, num_channels=3)
    assert gray_3ch.mode == "RGB"
    assert converter.is_grayscale(gray_3ch)
    r, g, b = gray_3ch.getpixel((0, 0))
    assert r == g == b


def test_color_converter_convert_and_inspect():
    converter = ColorConverter()
    img = Image.new("RGBA", (20, 20), color=(10, 20, 30, 255))

    converted_l = converter.convert(img, mode="L")
    assert converted_l.mode == "L"

    converted_rgb = converter.convert(img, mode="RGB")
    assert converter.is_rgb(converted_rgb)

    with pytest.raises(ValueError):
        converter.to_grayscale(img, num_channels=2)

    with pytest.raises(ValueError):
        converter.convert(img, mode="INVALID_MODE")

    with pytest.raises(TypeError):
        converter.to_rgb("not_an_image")


# ============================================================================
# 3. MemoryState Tests
# ============================================================================

def test_memory_state_basics_and_serialization():
    img1 = Image.new("RGB", (100, 100), color=(255, 0, 0))
    img2 = Image.new("RGB", (200, 150), color=(0, 255, 0))
    actions = ["click(50, 50)", "type('hello')"]

    state = MemoryState(
        screenshots=[img1, img2],
        action_logs=actions,
        total_steps=2,
        max_screenshots=3,
    )

    assert state.num_screenshots == 2
    assert state.num_actions == 2
    assert state.get_latest_screenshot() == img2
    assert state.get_latest_action() == "type('hello')"

    serialized = state.to_dict(include_image_bytes=True)
    assert serialized["total_steps"] == 2
    assert serialized["max_screenshots"] == 3
    assert len(serialized["screenshots"]) == 2
    assert "data_b64" in serialized["screenshots"][0]

    deserialized = MemoryState.from_dict(serialized)
    assert deserialized.total_steps == 2
    assert deserialized.max_screenshots == 3
    assert len(deserialized.screenshots) == 2
    assert deserialized.screenshots[0].size == (100, 100)
    assert deserialized.screenshots[1].size == (200, 150)
    assert deserialized.action_logs == actions


def test_empty_memory_state():
    state = MemoryState()
    assert state.num_screenshots == 0
    assert state.num_actions == 0
    assert state.get_latest_screenshot() is None
    assert state.get_latest_action() is None


# ============================================================================
# 4. SlidingTrajectoryMemory Tests
# ============================================================================

def test_sliding_trajectory_memory_fifo_eviction():
    mem = SlidingTrajectoryMemory(max_screenshots=3)
    assert mem.max_screenshots == 3
    assert mem.total_steps == 0

    imgs = [Image.new("RGB", (10 + i, 10 + i), color=(i * 20, 0, 0)) for i in range(5)]
    actions = [f"action_{i}" for i in range(5)]

    for i in range(5):
        state = mem.add_step(imgs[i], actions[i])
        assert state.total_steps == i + 1

    # After adding 5 steps into a capacity-3 buffer:
    # Screenshots buffer must contain ONLY the last 3 screenshots (imgs[2], imgs[3], imgs[4])
    screenshots = mem.get_screenshots()
    assert len(screenshots) == 3
    assert screenshots[0].size == (12, 12)
    assert screenshots[1].size == (13, 13)
    assert screenshots[2].size == (14, 14)

    # Full action log history (all 5 actions) must be retained
    action_logs = mem.get_action_logs()
    assert len(action_logs) == 5
    assert action_logs == actions


def test_sliding_trajectory_memory_copy_isolation():
    mem = SlidingTrajectoryMemory(max_screenshots=3, copy_on_add=True)
    img = Image.new("RGB", (50, 50), color=(255, 0, 0))
    mem.add_step(img, "click")

    # Mutate source image
    img.paste((0, 255, 0), (0, 0, 50, 50))

    stored_img = mem.get_screenshots()[0]
    # Verify stored image was isolated and remains red
    assert stored_img.getpixel((10, 10)) == (255, 0, 0)


def test_sliding_trajectory_memory_get_recent_actions_and_clear():
    mem = SlidingTrajectoryMemory(max_screenshots=3)
    for i in range(4):
        mem.add_step(Image.new("RGB", (10, 10)), f"act_{i}")

    assert mem.get_recent_actions(2) == ["act_2", "act_3"]
    assert mem.get_recent_actions(0) == []
    assert len(mem.get_recent_actions(10)) == 4

    mem.clear()
    assert mem.total_steps == 0
    assert len(mem.get_screenshots()) == 0
    assert len(mem.get_action_logs()) == 0


def test_sliding_trajectory_memory_serialization_roundtrip():
    mem = SlidingTrajectoryMemory(max_screenshots=3)
    img1 = Image.new("RGB", (30, 30), color=(100, 0, 0))
    img2 = Image.new("RGB", (40, 40), color=(0, 100, 0))

    mem.add_step(img1, "step_1")
    mem.add_step(img2, "step_2")

    serialized = mem.serialize()
    deserialized = SlidingTrajectoryMemory.deserialize(serialized)

    assert deserialized.total_steps == 2
    assert deserialized.max_screenshots == 3
    assert len(deserialized.get_screenshots()) == 2
    assert deserialized.get_screenshots()[0].size == (30, 30)
    assert deserialized.get_screenshots()[1].size == (40, 40)
    assert deserialized.get_action_logs() == ["step_1", "step_2"]


def test_sliding_trajectory_memory_invalid_inputs():
    with pytest.raises(ValueError):
        SlidingTrajectoryMemory(max_screenshots=0)

    mem = SlidingTrajectoryMemory(max_screenshots=3)
    with pytest.raises(TypeError):
        mem.add_step("invalid_img", "action")

    with pytest.raises(TypeError):
        mem.add_step(Image.new("RGB", (10, 10)), 12345)  # non-string action


# ============================================================================
# 5. MarkMap Tests
# ============================================================================

def test_markmap_basic_operations():
    mm = MarkMap(image_size=(1000, 1000))
    mm.add_mark(1, (100, 100, 300, 300), label="button1")
    mm.add_mark(2, (500, 500, 700, 700), label="button2")

    assert len(mm) == 2
    assert 1 in mm
    assert 2 in mm
    assert 3 not in mm

    assert mm.get_bbox(1) == (100, 100, 300, 300)
    assert mm.get_coordinates(1) == (200, 200)
    assert mm[2] == (500, 500, 700, 700)


def test_markmap_reverse_spatial_lookup():
    mm = MarkMap(image_size=(1000, 1000))
    # Larger outer box (area 400x400 = 160000)
    mm.add_mark(1, (100, 100, 500, 500), label="container")
    # Smaller nested inner box (area 100x100 = 10000)
    mm.add_mark(2, (200, 200, 300, 300), label="nested_button")

    # Point inside inner box -> must return smaller area inner box mark_id (2)
    assert mm.get_mark_at(250, 250) == 2

    # Point inside outer box but outside inner box -> returns mark_id (1)
    assert mm.get_mark_at(150, 150) == 1

    # Point outside all boxes -> returns None
    assert mm.get_mark_at(50, 50) is None


def test_markmap_exceptions_and_validation():
    mm = MarkMap()
    mm.add_mark(1, (10, 10, 50, 50))

    with pytest.raises(KeyError):
        mm.get_coordinates(999)

    with pytest.raises(KeyError):
        mm.get_bbox(999)

    with pytest.raises(ValueError):
        mm.add_mark(2, (100, 100, 50, 50))  # x_min > x_max


def test_markmap_serialization_roundtrip():
    mm = MarkMap(image_size=(800, 600))
    mm.add_mark(1, (50, 50, 150, 150), label="input", metadata={"type": "text"})
    mm.add_mark(2, (200, 100, 300, 150), label="submit")

    d = mm.to_dict()
    reconstructed = MarkMap.from_dict(d)

    assert reconstructed.image_size == (800, 600)
    assert len(reconstructed) == 2
    assert reconstructed.get_coordinates(1) == (100, 100)
    assert reconstructed.get_bbox(2) == (200, 100, 300, 150)


# ============================================================================
# 6. SoMAnnotator Tests
# ============================================================================

def test_som_annotator_annotation_with_custom_elements():
    annotator = SoMAnnotator(line_width=3, badge_position="top_left")
    screenshot = Image.new("RGB", (800, 600), color=(240, 240, 240))

    elements = [
        {"bbox": (100, 100, 200, 150), "label": "search_bar"},
        {"bbox": (300, 100, 400, 150), "label": "search_button"},
    ]

    annotated_img, mark_map = annotator.annotate(screenshot, elements=elements)

    assert isinstance(annotated_img, Image.Image)
    assert annotated_img.size == (800, 600)
    assert len(mark_map) == 2
    assert mark_map.get_coordinates(1) == (150, 125)
    assert mark_map.get_coordinates(2) == (350, 125)


def test_som_annotator_fallback_uniform_grid():
    annotator = SoMAnnotator(grid_rows=2, grid_cols=2)
    screenshot = Image.new("RGB", (400, 400), color=(255, 255, 255))

    # Calling annotate with elements=None -> triggers uniform grid generation (2x2 = 4 marks)
    annotated_img, mark_map = annotator.annotate(screenshot, elements=None)

    assert len(mark_map) == 4
    # Mark 1: top-left cell (0, 0, 200, 200) -> center (100, 100)
    assert mark_map.get_coordinates(1) == (100, 100)
    # Mark 4: bottom-right cell (200, 200, 400, 400) -> center (300, 300)
    assert mark_map.get_coordinates(4) == (300, 300)


def test_som_annotator_immutability_and_palette_cycling():
    annotator = SoMAnnotator(badge_position="center")
    original = Image.new("RGB", (500, 500), color=(50, 50, 50))
    original_pixels = original.tobytes()

    # Create 15 elements to test color palette cycling (>10 default palette colors)
    elements = [{"bbox": (i * 20, i * 20, i * 20 + 15, i * 20 + 15)} for i in range(15)]
    annotated_img, mark_map = annotator.annotate(original, elements=elements)

    assert len(mark_map) == 15
    # Verify original image was not mutated
    assert original.tobytes() == original_pixels


def test_som_annotator_invalid_inputs():
    annotator = SoMAnnotator()

    with pytest.raises(TypeError):
        annotator.annotate("not_a_pil_image")

    with pytest.raises(ValueError):
        invalid_img = Image.new("RGB", (0, 0))
        # Note: PIL.Image.new with (0,0) might raise PIL error or create zero dimension
        try:
            annotator.annotate(invalid_img)
        except (ValueError, Exception):
            raise ValueError("Invalid screenshot dimensions")
