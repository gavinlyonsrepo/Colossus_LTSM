# pylint: disable=missing-docstring,protected-access
from types import SimpleNamespace

import pytest
from PIL import ImageFont

from colossus_ltsm.font_converter import FontConverter


def _make_test_converter():
    converter = object.__new__(FontConverter)
    converter._log = lambda *args, **kwargs: None
    converter.ttf_path = SimpleNamespace(get=lambda: "DejaVuSans.ttf")
    return converter


def _load_test_font():
    try:
        return ImageFont.truetype("DejaVuSans.ttf", 24)
    except OSError:
        font = ImageFont.load_default()
        if not hasattr(font, "getbbox"):
            pytest.skip("No usable PIL font available for glyph rendering.")
        return font

def test_validate_dimensions_accepts_valid_parameters():
    converter = _make_test_converter()
    params = {
        "width": 16,
        "height": 16,
        "start": 65,
        "end": 65,
        "font_name": "TestFont",
        "output_name": "test",
        "ext": "hpp",
        "array_style": "cpp",
        "addr_mode": "horizontal",
    }
    assert converter._validate_dimensions(params) is True


def test_validate_dimensions_rejects_invalid_parameters():
    converter = _make_test_converter()
    params = {
        "width": 0,
        "height": 16,
        "start": 65,
        "end": 65,
        "font_name": "TestFont",
        "output_name": "test",
        "ext": "hpp",
        "array_style": "cpp",
        "addr_mode": "horizontal",
    }
    assert converter._validate_dimensions(params) is False

    params["width"] = 8
    params["height"] = -1
    assert converter._validate_dimensions(params) is False


def test_calculate_baseline_returns_valid_value():
    font = _load_test_font()
    converter = _make_test_converter()
    baseline = converter._calculate_baseline(font, 32, 65, 67)

    assert isinstance(baseline, int)
    assert 0 <= baseline <= 32


def test_scan_ink_extents_returns_valid_range():
    font = _load_test_font()
    converter = _make_test_converter()
    ink_extents = converter._scan_ink_extents(font, 65, 67)

    assert isinstance(ink_extents, tuple)
    assert len(ink_extents) == 2
    assert all(isinstance(value, int) and value >= 0 for value in ink_extents)


def test_generate_glyph_blocks_returns_expected_block_count_and_byte_arrays():
    font = _load_test_font()
    converter = _make_test_converter()
    params = {
        "width": 48,
        "height": 32,
        "start": 65,
        "end": 67,
        "font_name": "TestFont",
        "output_name": "test",
        "ext": "hpp",
        "array_style": "cpp",
        "addr_mode": "horizontal",
    }

    glyph_blocks = converter._generate_glyph_blocks(font, params)

    assert [char for char, _ in glyph_blocks] == ["A", "B", "C"]
    assert len(glyph_blocks) == 3
    assert all(len(data) == 192 for _, data in glyph_blocks)
    assert any(byte != 0 for _, data in glyph_blocks for byte in data)


def test_generate_glyph_blocks_supports_vertical_addressing():
    font = _load_test_font()
    converter = _make_test_converter()
    horizontal_params = {
        "width": 48,
        "height": 32,
        "start": 65,
        "end": 65,
        "font_name": "TestFont",
        "output_name": "test",
        "ext": "hpp",
        "array_style": "cpp",
        "addr_mode": "horizontal",
    }
    vertical_params = horizontal_params.copy()
    vertical_params["addr_mode"] = "vertical"

    horizontal_blocks = converter._generate_glyph_blocks(font, horizontal_params)
    vertical_blocks = converter._generate_glyph_blocks(font, vertical_params)

    assert len(horizontal_blocks) == 1
    assert len(vertical_blocks) == 1

    _, horizontal_data = horizontal_blocks[0]
    _, vertical_data = vertical_blocks[0]

    assert len(horizontal_data) == 192
    assert len(vertical_data) == 192
    assert all(isinstance(byte, int) and 0 <= byte <= 0xFF for byte in vertical_data)
    assert horizontal_data != vertical_data
