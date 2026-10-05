"""Unit tests for `TabBar` (no display required)."""

import pytest

from simraceengineer.dashboard.ui.tabs import TabBar

LABELS = ["General", "Voice", "Alerts", "Airflow"]


def _bar(labels=LABELS, **kwargs) -> TabBar:
    return TabBar(labels, len, **kwargs)


def _assert_no_overlap(bar: TabBar) -> None:
    for a, b in zip(bar.rects, bar.rects[1:]):
        assert a.right <= b.left


def test_widths_come_from_label_size_plus_padding():
    bar = _bar(pad_x=16, gap=4, height=30)
    bar.layout(10, 20, 1000)
    assert [r.width for r in bar.rects] == [len(lbl) + 32 for lbl in LABELS]
    assert all(r.y == 20 and r.height == 30 for r in bar.rects)
    assert bar.rects[0].x == 10
    assert bar.rects[1].x == bar.rects[0].right + 4
    _assert_no_overlap(bar)


@pytest.mark.parametrize("max_width", [200, 120, 60, 20])
def test_overflow_shrinks_tabs_to_fit_max_width(max_width: int):
    bar = _bar()
    bar.layout(5, 0, max_width)
    assert len(bar.rects) == len(LABELS)
    assert bar.rects[0].left == 5
    assert bar.rects[-1].right - 5 <= max_width
    _assert_no_overlap(bar)


def test_overflow_shrinks_evenly():
    bar = _bar(labels=["aaaa", "bbbbbbbb"], pad_x=0, gap=0)
    bar.layout(0, 0, 8)  # natural 12 → overflow 4 → 2 px each
    assert [r.width for r in bar.rects] == [2, 6]


def test_empty_labels_produce_no_rects():
    bar = _bar(labels=[])
    bar.layout(0, 0, 100)
    assert bar.rects == []
    assert bar.hit((1, 1)) is None


def test_hit_returns_index_or_none():
    bar = _bar()
    bar.layout(0, 0, 1000)
    for i, rect in enumerate(bar.rects):
        assert bar.hit(rect.center) == i
    assert bar.hit((bar.rects[-1].right + 50, 5)) is None
    assert bar.hit((5, 100)) is None
    # The gap between tabs belongs to no tab.
    assert bar.hit((bar.rects[0].right + 1, 5)) is None


def test_hit_before_layout_is_none():
    assert _bar().hit((0, 0)) is None


def test_select_returns_whether_changed():
    bar = _bar()
    assert bar.active == 0
    assert bar.select(0) is False
    assert bar.select(2) is True
    assert bar.active == 2
    assert bar.select(2) is False


@pytest.mark.parametrize("index", [-1, 4, 99])
def test_select_out_of_range_is_ignored(index: int):
    bar = _bar()
    assert bar.select(index) is False
    assert bar.active == 0


def test_next_wraps_around():
    bar = _bar()
    bar.select(3)
    bar.next()
    assert bar.active == 0
    bar.next()
    assert bar.active == 1


def test_prev_wraps_around():
    bar = _bar()
    bar.prev()
    assert bar.active == 3
    bar.prev()
    assert bar.active == 2
