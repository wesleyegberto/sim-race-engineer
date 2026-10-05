"""Pure text-wrapping helper shared by the Settings and Help panels."""

from collections.abc import Callable


def _split_word(word: str, max_width: int, measure: Callable[[str], int]) -> list[str]:
    """Hard-split a word wider than ``max_width`` into character chunks.

    Each chunk holds as many characters as fit; a single character wider than
    ``max_width`` still gets its own chunk so progress is always made.
    """
    chunks: list[str] = []
    current = ""
    for ch in word:
        if current and measure(current + ch) > max_width:
            chunks.append(current)
            current = ch
        else:
            current += ch
    if current:
        chunks.append(current)
    return chunks


def _wrap_paragraph(text: str, max_width: int, measure: Callable[[str], int]) -> list[str]:
    """Greedy word wrap of a single paragraph (no explicit newlines)."""
    lines: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}" if current else word
        if measure(candidate) <= max_width:
            current = candidate
            continue
        if current:
            lines.append(current)
            current = ""
        if measure(word) <= max_width:
            current = word
        else:
            *full, current = _split_word(word, max_width, measure)
            lines.extend(full)
    lines.append(current)
    return lines


def wrap_text(text: str, max_width: int, measure: Callable[[str], int]) -> list[str]:
    """Wrap ``text`` into lines no wider than ``max_width`` according to ``measure``.

    - Greedy word wrap; runs of whitespace collapse to a single space.
    - An explicit ``"\\n"`` always starts a new line (blank lines are kept).
    - A word wider than ``max_width`` is hard-split by characters.
    - Empty text returns ``[""]``.

    ``measure`` returns the rendered width of a string, e.g.
    ``lambda s: font.size(s)[0]`` in production or ``len`` in tests.
    """
    lines: list[str] = []
    for paragraph in text.split("\n"):
        lines.extend(_wrap_paragraph(paragraph, max_width, measure))
    return lines
