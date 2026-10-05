"""Unit tests for `wrap_text` using `len` as the measure function."""

import pytest

from simraceengineer.dashboard.ui.text import wrap_text


def test_short_text_fits_on_one_line():
    assert wrap_text("hello world", 20, len) == ["hello world"]


def test_text_exactly_max_width_stays_on_one_line():
    assert wrap_text("hello world", 11, len) == ["hello world"]


def test_greedy_multi_line_wrap():
    assert wrap_text("the quick brown fox jumps", 10, len) == ["the quick", "brown fox", "jumps"]


def test_oversize_word_is_hard_split():
    assert wrap_text("abcdefghij", 4, len) == ["abcd", "efgh", "ij"]


def test_oversize_word_after_short_word():
    assert wrap_text("hi abcdefghij ok", 4, len) == ["hi", "abcd", "efgh", "ij", "ok"]


def test_oversize_word_tail_joins_next_word_when_it_fits():
    assert wrap_text("abcdef g", 4, len) == ["abcd", "ef g"]


def test_empty_text_returns_single_empty_line():
    assert wrap_text("", 10, len) == [""]


def test_whitespace_only_returns_single_empty_line():
    assert wrap_text("   ", 10, len) == [""]


def test_explicit_newline_starts_new_line():
    assert wrap_text("one\ntwo", 20, len) == ["one", "two"]


def test_blank_line_between_paragraphs_is_kept():
    assert wrap_text("one\n\ntwo", 20, len) == ["one", "", "two"]


def test_newline_combined_with_wrapping():
    assert wrap_text("aa bb cc\ndd", 5, len) == ["aa bb", "cc", "dd"]


def test_single_char_wider_than_max_width_goes_on_its_own_line():
    def measure(s: str) -> int:
        return len(s) * 10

    assert wrap_text("ab", 5, measure) == ["a", "b"]


def test_custom_measure_is_used():
    def measure(s: str) -> int:
        return len(s) * 2

    assert wrap_text("aa bb", 6, measure) == ["aa", "bb"]


@pytest.mark.parametrize("max_width", [1, 3, 5, 8, 13, 40])
def test_no_line_exceeds_max_width(max_width: int):
    text = (
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit.\n"
        "Supercalifragilisticexpialidocious words must be split too."
    )
    lines = wrap_text(text, max_width, len)
    assert all(len(line) <= max_width for line in lines)
    # No characters are lost (ignoring whitespace).
    assert "".join(lines).replace(" ", "") == text.replace(" ", "").replace("\n", "")
