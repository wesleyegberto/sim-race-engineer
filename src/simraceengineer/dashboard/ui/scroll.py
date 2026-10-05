"""Pure vertical scroll state shared by the Settings and Help panels."""

from dataclasses import dataclass

_MIN_INDICATOR_H = 20


@dataclass
class ScrollState:
    """Vertical scroll offset of a content area inside a fixed viewport."""

    viewport_h: int = 0
    content_h: int = 0
    offset: int = 0
    step: int = 40

    @property
    def max_offset(self) -> int:
        """Largest valid offset: ``max(0, content_h - viewport_h)``."""
        return max(0, self.content_h - self.viewport_h)

    @property
    def can_scroll(self) -> bool:
        """True when the content is taller than the viewport."""
        return self.max_offset > 0

    def _clamp(self) -> None:
        self.offset = min(max(self.offset, 0), self.max_offset)

    def set_sizes(self, viewport_h: int, content_h: int) -> None:
        """Update viewport/content heights and re-clamp the offset."""
        self.viewport_h = max(0, viewport_h)
        self.content_h = max(0, content_h)
        self._clamp()

    def scroll(self, wheel_y: int) -> None:
        """Apply a mouse-wheel delta; ``wheel_y > 0`` scrolls up (towards the top)."""
        self.offset -= wheel_y * self.step
        self._clamp()

    def reset(self) -> None:
        """Scroll back to the top."""
        self.offset = 0

    def to_content(self, y: int, viewport_top: int) -> int:
        """Map a window y coordinate to a y coordinate in content space."""
        return y - viewport_top + self.offset

    def indicator(self) -> tuple[int, int] | None:
        """Scrollbar thumb as ``(top, height)`` in viewport px, or None if no scroll.

        The height is proportional to the visible fraction of the content (with a
        minimum of 20 px) and the thumb always stays inside the viewport.
        """
        if not self.can_scroll or self.viewport_h <= 0:
            return None
        height = round(self.viewport_h * self.viewport_h / self.content_h)
        height = min(self.viewport_h, max(_MIN_INDICATOR_H, height))
        track = self.viewport_h - height
        top = round(track * self.offset / self.max_offset)
        return top, height
