"""Thin wrapper around a secondary pygame-ce ``pygame.Window`` used to host a panel.

The dashboard keeps the main window created by ``pygame.display.set_mode``; panels
such as Settings and Help live in their own resizable OS windows driven by the same
main loop (SDL requires all windows on the main thread on macOS).

Event routing: pygame-ce tags window-related events with ``event.window`` (the
``pygame.Window`` for secondary windows, ``None`` for the display-module window).
Keyboard/text events are routed by focus as a fallback when the attribute is missing.
"""

import pygame

_FOCUS_ROUTED = {pygame.KEYDOWN, pygame.KEYUP, pygame.TEXTINPUT, pygame.TEXTEDITING}


class PanelWindow:
    def __init__(self, title: str, size: tuple[int, int], min_size: tuple[int, int],
                 icon: pygame.Surface | None = None) -> None:
        self._title = title
        self._size = size
        self._min_size = min_size
        self._icon = icon
        self._window: pygame.Window | None = None

    @property
    def is_open(self) -> bool:
        return self._window is not None

    def open(self) -> bool:
        """Create the window, or focus it if already open. Returns True when created."""
        if self._window is not None:
            self._window.focus()
            return False
        self._window = pygame.Window(self._title, self._size, resizable=True)
        self._window.minimum_size = self._min_size
        if self._icon is not None:
            # Secondary windows don't inherit the display-module icon
            self._window.set_icon(self._icon)
        return True

    def close(self) -> None:
        if self._window is not None:
            self._window.destroy()
            self._window = None

    def owns(self, event: pygame.event.Event) -> bool:
        if self._window is None:
            return False
        if hasattr(event, "window"):
            return event.window is self._window
        return event.type in _FOCUS_ROUTED and self._window.focused

    def surface(self) -> pygame.Surface:
        assert self._window is not None
        return self._window.get_surface()

    def size(self) -> tuple[int, int]:
        assert self._window is not None
        w, h = self._window.size
        return w, h

    def present(self) -> None:
        if self._window is not None:
            self._window.flip()
