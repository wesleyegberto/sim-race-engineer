"""Pure tab-bar layout and selection model shared by the Settings and Help panels.

``pygame.Rect`` is used only as a value type; nothing here touches the display.
"""

from collections.abc import Callable, Sequence

import pygame


class TabBar:
    """Horizontal row of tabs sized from their labels, with one active tab."""

    def __init__(
        self,
        labels: Sequence[str],
        measure: Callable[[str], int],
        pad_x: int = 16,
        gap: int = 4,
        height: int = 30,
    ) -> None:
        self.labels: list[str] = list(labels)
        self._measure = measure
        self.pad_x = pad_x
        self.gap = gap
        self.height = height
        self.rects: list[pygame.Rect] = []
        self.active: int = 0

    def layout(self, x: int, y: int, max_width: int) -> None:
        """Place tabs left-to-right from ``(x, y)``.

        Each tab is ``measure(label) + 2 * pad_x`` wide; if the row would exceed
        ``max_width`` every width is shrunk evenly (same amount each) so it fits.
        """
        widths = [self._measure(label) + 2 * self.pad_x for label in self.labels]
        n = len(widths)
        if n == 0:
            self.rects = []
            return
        available = max(0, max_width - self.gap * (n - 1))
        overflow = sum(widths) - available
        if overflow > 0:
            widths = self._shrink(widths, overflow)
        rects: list[pygame.Rect] = []
        cx = x
        for w in widths:
            rects.append(pygame.Rect(cx, y, w, self.height))
            cx += w + self.gap
        self.rects = rects

    @staticmethod
    def _shrink(widths: list[int], overflow: int) -> list[int]:
        """Remove ``overflow`` px spread evenly across widths, never below 1 px."""
        widths = list(widths)
        while overflow > 0:
            shrinkable = [i for i, w in enumerate(widths) if w > 1]
            if not shrinkable:
                break
            per_tab, extra = divmod(overflow, len(shrinkable))
            for rank, i in enumerate(shrinkable):
                cut = min(widths[i] - 1, per_tab + (1 if rank < extra else 0))
                widths[i] -= cut
                overflow -= cut
        return widths

    def hit(self, pos: tuple[int, int]) -> int | None:
        """Index of the tab under ``pos``, or None."""
        for i, rect in enumerate(self.rects):
            if rect.collidepoint(pos):
                return i
        return None

    def select(self, index: int) -> bool:
        """Activate tab ``index``; returns True if the active tab changed."""
        if not 0 <= index < len(self.labels) or index == self.active:
            return False
        self.active = index
        return True

    def next(self) -> None:
        """Activate the next tab, wrapping to the first."""
        if self.labels:
            self.active = (self.active + 1) % len(self.labels)

    def prev(self) -> None:
        """Activate the previous tab, wrapping to the last."""
        if self.labels:
            self.active = (self.active - 1) % len(self.labels)
