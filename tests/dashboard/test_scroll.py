"""Unit tests for `ScrollState`."""

from simraceengineer.dashboard.ui.scroll import ScrollState


def _state(viewport_h: int, content_h: int, step: int = 40) -> ScrollState:
    s = ScrollState(step=step)
    s.set_sizes(viewport_h, content_h)
    return s


def _indicator(s: ScrollState) -> tuple[int, int]:
    result = s.indicator()
    assert result is not None
    return result


def test_no_scroll_when_content_fits():
    s = _state(400, 300)
    assert s.max_offset == 0
    assert not s.can_scroll
    s.scroll(-5)
    assert s.offset == 0
    assert s.indicator() is None


def test_no_scroll_when_content_equals_viewport():
    s = _state(400, 400)
    assert not s.can_scroll
    assert s.indicator() is None


def test_max_offset_is_content_minus_viewport():
    s = _state(400, 1000)
    assert s.max_offset == 600
    assert s.can_scroll


def test_scroll_down_with_negative_wheel():
    s = _state(400, 1000)
    s.scroll(-1)
    assert s.offset == 40
    s.scroll(-2)
    assert s.offset == 120


def test_scroll_up_with_positive_wheel():
    s = _state(400, 1000)
    s.offset = 200
    s.scroll(1)
    assert s.offset == 160


def test_scroll_clamps_at_zero():
    s = _state(400, 1000)
    s.scroll(3)
    assert s.offset == 0


def test_scroll_clamps_at_max_offset():
    s = _state(400, 1000)
    s.scroll(-100)
    assert s.offset == 600


def test_custom_step():
    s = _state(400, 1000, step=10)
    s.scroll(-1)
    assert s.offset == 10


def test_resize_reclamps_offset():
    s = _state(400, 1000)
    s.scroll(-100)
    assert s.offset == 600
    s.set_sizes(800, 1000)
    assert s.offset == 200
    s.set_sizes(800, 500)
    assert s.offset == 0


def test_reset_goes_to_top():
    s = _state(400, 1000)
    s.scroll(-3)
    s.reset()
    assert s.offset == 0


def test_to_content_maps_window_y_to_content_y():
    s = _state(400, 1000)
    assert s.to_content(150, 100) == 50
    s.scroll(-2)
    assert s.to_content(150, 100) == 130


def test_indicator_proportional_at_top():
    s = _state(400, 800)
    assert s.indicator() == (0, 200)


def test_indicator_at_bottom_touches_viewport_end():
    s = _state(400, 800)
    s.scroll(-100)
    top, height = _indicator(s)
    assert top + height == 400


def test_indicator_in_middle():
    s = _state(400, 800)
    s.offset = 200
    assert s.indicator() == (100, 200)


def test_indicator_has_minimum_height_and_stays_inside():
    s = _state(100, 100_000)
    top, height = _indicator(s)
    assert height == 20
    assert top == 0
    s.scroll(-100_000)
    top, height = _indicator(s)
    assert top + height == 100
