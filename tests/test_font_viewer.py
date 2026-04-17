# pylint: disable=missing-docstring,protected-access
from types import SimpleNamespace

from colossus_ltsm.font_viewer import FontViewer


def _make_viewer():
    viewer = object.__new__(FontViewer)
    viewer.addr_mode_var = SimpleNamespace(get=lambda: "horizontal")
    return viewer


def test_hex_to_rgb_returns_expected_tuple():
    viewer = _make_viewer()
    assert viewer._hex_to_rgb("#0078FF") == (0, 120, 255)
    assert viewer._hex_to_rgb("#000000") == (0, 0, 0)


def test_hex_to_rgb_accepts_lowercase_colors():
    viewer = _make_viewer()
    assert viewer._hex_to_rgb("#ff8800") == (255, 136, 0)


def test_calc_bytes_per_char_rounds_up_to_full_bytes():
    viewer = _make_viewer()
    assert viewer._calc_bytes_per_char(1, 1) == 1
    assert viewer._calc_bytes_per_char(8, 1) == 1
    assert viewer._calc_bytes_per_char(9, 1) == 2
    assert viewer._calc_bytes_per_char(16, 16) == 32
