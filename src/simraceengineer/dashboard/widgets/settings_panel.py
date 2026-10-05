"""Settings panel rendered inside its own resizable window.

The panel is a thin pygame renderer on top of ``SettingsForm``: the controls are a
declarative list of specs per tab (``Section``, ``Checkbox``, ``TextInput``,
``Choice``, ``Button``, ``Note``) laid out top-to-bottom in content space by
``layout()``. Only the active tab is laid out; its content scrolls inside a viewport
between a fixed header (title + tab bar) and a fixed footer (error summary +
Cancel/Save). Validation errors and helper text are rendered directly under their
field. Mouse positions are window-relative; hover is tracked from ``MOUSEMOTION``
events because ``pygame.mouse.get_pos()`` follows the focused window only.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

import pygame

from ...microcontroller.serial_transport import list_serial_ports
from ..colors import (
    C_ACCENT,
    C_BORDER,
    C_BORDER_DISABLED,
    C_BTN_CANCEL,
    C_BTN_CANCEL_HOVER,
    C_BTN_HOVER,
    C_BTN_SAVE,
    C_BTN_TEST,
    C_BTN_TEST_BORDER,
    C_CARD,
    C_DIM,
    C_DIVIDER,
    C_ERROR,
    C_GROUP_LABEL,
    C_INPUT_ACTIVE,
    C_INPUT_BG,
    C_INPUT_DISABLED,
    C_NOTE,
    C_SUCCESS,
    C_TAB_ACTIVE,
    C_TEXT,
    C_TEXT_MUTED,
    C_TEXT_ON_ACCENT,
)
from ..settings_form import SettingsForm
from ..ui.scroll import ScrollState
from ..ui.tabs import TabBar
from ..ui.text import wrap_text

if TYPE_CHECKING:
    from ...config import AppConfig

Action = Literal["saved", "cancelled", "test_voice", "test_microcontroller"] | None


def auto_detect_port() -> str | None:
    """Return the serial port when exactly one candidate is connected, else None."""
    candidates = list_serial_ports()
    return candidates[0] if len(candidates) == 1 else None


# ── Control specs ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Section:
    """Group heading; ``major`` draws a full-width separator above it."""

    title: str
    major: bool = False
    line: bool = True


@dataclass(frozen=True)
class Checkbox:
    """Boolean form field; ``half`` lets it share a row in the 2-column grid."""

    field: str
    label: str
    half: bool = True
    help: str = ""


@dataclass(frozen=True)
class TextInput:
    """Free-text form field. ``inline`` puts the label left of the box when it fits."""

    field: str
    label: str
    unit: str = ""
    width: int | None = None
    inline: bool = False
    large: bool = False
    help: str = ""


@dataclass(frozen=True)
class Choice:
    """Single choice among ``options`` (value, label) for a string form attribute."""

    field: str
    label: str
    options: tuple[tuple[str, str], ...]
    help: str = ""


@dataclass(frozen=True)
class Button:
    """Action button; the click returns ``action`` from ``handle_event``."""

    action: Literal["test_voice", "test_microcontroller"]
    label: str


@dataclass(frozen=True)
class Note:
    """Static wrapped note; dimmed while ``enabled_by`` is inactive."""

    text: str
    enabled_by: str | None = None


@dataclass(frozen=True)
class MicroStatus:
    """Microcontroller auto-detect / connection-test status line."""


Control = Section | Checkbox | TextInput | Choice | Button | Note | MicroStatus


@dataclass(frozen=True)
class Tab:
    """One Settings tab: stable id, visible label and its controls."""

    id: str
    label: str
    controls: tuple[Control, ...]


_ALERT_GROUPS: tuple[tuple[str, tuple[tuple[str, str], ...]], ...] = (
    ("Race", (
        ("voice_alert_lap_completed", "Lap completed"),
        ("voice_alert_best_lap", "New best lap"),
        ("voice_alert_final_lap", "Final lap"),
        ("voice_alert_lap_delta", "Lap time delta"),
        ("voice_alert_race_report", "Race progress report"),
        ("voice_alert_overtake", "Position gained or lost"),
        ("voice_alert_laps_to_finish", "Laps remaining countdown"),
    )),
    ("Fuel and pit stops", (
        ("voice_alert_fuel_low", "Fuel low"),
        ("voice_alert_fuel_critical", "Fuel critical"),
        ("voice_alert_pit_window", "Pit window"),
        ("voice_alert_fuel_save", "Fuel saving warning"),
    )),
    ("Car health", (
        ("voice_alert_engine_temp", "Engine temperature"),
        ("voice_alert_oil_temp", "Oil temperature"),
        ("voice_alert_tire_temp", "Tyre temperature"),
        ("voice_alert_tire_inner_temp", "Tyre inner temperature"),
        ("voice_alert_tire_pressure", "Tyre pressure"),
    )),
)

_STRATEGY_ALERTS: tuple[tuple[str, str], ...] = (
    ("voice_alert_strategy_check_in", "Strategy check-in"),
    ("voice_alert_strategy_revised", "Strategy revised"),
    ("voice_alert_fuel_save_recommend", "Fuel saving recommendation"),
    ("voice_alert_advisor_pit_window", "Advisor pit window"),
)


def build_tabs(show_microcontroller: bool) -> list[Tab]:
    """Declarative Settings content: one ``Tab`` per visible tab, in display order."""
    general = (
        TextInput("device_ip", "Device IP address", large=True,
                  help="IP address of the PS5 or PC running Gran Turismo 7. It must be "
                       "on the same network as this computer; required to receive telemetry."),
        Checkbox("recording_on_start", "Record laps automatically when a session starts",
                 half=False,
                 help="Saves the telemetry of every lap for the post-session lap analysis."),
        Choice("fuel_estimation", "Fuel per lap estimate",
               (("last", "Last lap"), ("average", "Average")),
               help="Last lap uses the previous lap's consumption; Average uses the "
                    "rolling average of the session."),
    )
    voice = (
        Checkbox("voice_enabled", "Enable voice alerts", half=False,
                 help="Master switch for every spoken alert from the race engineer."),
        Choice("voice_language", "Voice language", (("en", "English"), ("pt", "Português")),
               help="A language change takes effect after restarting the app."),
        Button("test_voice", "Test voice"),
        Note("Plays a sample alert in the selected language.", enabled_by="voice"),
    )

    alerts: list[Control] = [
        Section("Engineer communications", line=False),
        Note("Choose which alerts the race engineer speaks. "
             "Voice alerts must be enabled on the Voice tab."),
    ]
    for title, group in _ALERT_GROUPS:
        alerts.append(Section(title))
        alerts.extend(Checkbox(name, label) for name, label in group)
    alerts += [
        Section("Tyre wear"),
        Checkbox("voice_alert_tyre_wear", "Tyre wear milestones", half=False),
        TextInput("voice_tyre_wear_threshold_pct", "Announce every", unit="% of wear",
                  width=60, inline=True,
                  help="The engineer reports the average tyre wear each time it grows "
                       "by this amount (1 to 99, default 10)."),
        Section("Strategy alerts"),
        Note("Advice from the race strategy calculator: periodic check-ins, plan "
             "changes, lift-and-coast suggestions and pit window calls.",
             enabled_by="voice"),
    ]
    alerts.extend(Checkbox(name, label) for name, label in _STRATEGY_ALERTS)

    tabs = [
        Tab("general", "General", general),
        Tab("voice", "Voice", voice),
        Tab("alerts", "Alerts", tuple(alerts)),
    ]
    if show_microcontroller:
        tabs.append(Tab("airflow", "Airflow", (
            Checkbox("microcontroller_enabled", "Enable airflow simulation", half=False,
                     help="Drives fans from the car speed through a USB microcontroller. "
                          "Takes effect after restarting the app."),
            TextInput("microcontroller_port", "Serial port (leave blank to auto-detect)",
                      width=280,
                      help="Filled in automatically when exactly one serial device "
                           "is connected."),
            Button("test_microcontroller", "Test connection"),
            MicroStatus(),
            TextInput("fan_speed_ceiling_kmh", "Fan speed ceiling", unit="km/h",
                      width=70, inline=True,
                      help="Car speed at which the fans reach 100%. Lower values give "
                           "more airflow at low speed (default 220)."),
        )))
    return tabs


def build_controls(show_microcontroller: bool) -> list[Control]:
    """Every control of every visible tab, flattened in tab order."""
    return [c for tab in build_tabs(show_microcontroller) for c in tab.controls]


@dataclass
class _Placed:
    """A control laid out in content space (y = 0 at the top of the content)."""

    spec: Control
    rect: pygame.Rect                      # interactive area (box / cell / button)
    bounds: pygame.Rect                    # everything drawn, for culling
    label_y: int = 0
    lines: list[str] = field(default_factory=list)       # label / note lines
    options: list[tuple[str, pygame.Rect]] = field(default_factory=list)
    inline: bool = False                   # TextInput label drawn left of the box
    error_y: int = 0
    error_lines: list[str] = field(default_factory=list)
    help_y: int = 0
    help_lines: list[str] = field(default_factory=list)


# ── Geometry ──────────────────────────────────────────────────────────────────
_PAD = 20
_TITLE_Y = 12
_TAB_H = 30
_SCROLLBAR_W = 6
_COL_GAP = 16
_TWO_COL_MIN_W = 600      # content width at which the Alerts grid uses 2 columns
_MIN_W = 420              # floor for the window's minimum width (keeps wrapped labels readable)
_CHECK = 18
_BTN_W, _BTN_H = 96, 36
_CURSOR_BLINK_MS = 500


class SettingsPanel:
    def __init__(
        self,
        show_microcontroller: bool = False,
        detect_port: Callable[[], str | None] = auto_detect_port,
    ) -> None:
        self._show_micro = show_microcontroller
        self._detect_port = detect_port
        self._tabs = build_tabs(show_microcontroller)
        self._field_tab: dict[str, int] = {
            spec.field: i
            for i, tab in enumerate(self._tabs)
            for spec in tab.controls
            if isinstance(spec, Checkbox | TextInput | Choice)
        }
        self._tab_bar = TabBar([t.label for t in self._tabs],
                               lambda s: self._fonts()[1].size(s)[0], height=_TAB_H)
        self.form: SettingsForm | None = None
        self._active_field: str | None = None
        self._errors: dict[str, str] = {}
        self._summary_lines: list[str] = []
        self._micro_test_result: bool | None = None
        self._cursor_visible = True
        self._cursor_timer = 0
        self._mouse: tuple[int, int] | None = None
        self._scroll = ScrollState()
        self._size: tuple[int, int] | None = None
        self._placed: list[_Placed] = []
        self._content_h = 0
        self._header_h = 80
        self._footer_top = 0
        self._viewport = pygame.Rect(0, self._header_h, 0, 0)
        self._btn_save = pygame.Rect(0, 0, _BTN_W, _BTN_H)
        self._btn_cancel = pygame.Rect(0, 0, _BTN_W, _BTN_H)
        self._font_md: pygame.font.Font | None = None
        self._font_body: pygame.font.Font | None = None
        self._font_sm: pygame.font.Font | None = None

    # ── lifecycle ─────────────────────────────────────────────────────────────

    @property
    def is_open(self) -> bool:
        return self.form is not None

    @property
    def tab_labels(self) -> list[str]:
        return [t.label for t in self._tabs]

    @property
    def active_tab(self) -> str:
        """Id of the active tab (``general``, ``voice``, ``alerts`` or ``airflow``)."""
        return self._tabs[self._tab_bar.active].id

    def open(self, config: AppConfig, active_field: str | None = None) -> None:
        """Load a fresh form from ``config``; ``active_field`` gets keyboard focus."""
        self.form = SettingsForm.from_config(config, self._show_micro, self._detect_port)
        self._active_field = active_field
        self._tab_bar.active = self._field_tab.get(active_field or "", 0)
        self._errors = {}
        self._summary_lines = []
        self._micro_test_result = None
        self._cursor_visible = True
        self._cursor_timer = 0
        self._mouse = None
        self._scroll.reset()
        if self._size is not None:
            self.layout(*self._size)

    def close(self) -> None:
        """Discard the form (unsaved edits are lost)."""
        self.form = None
        self._active_field = None
        self._errors = {}
        self._summary_lines = []

    def set_microcontroller_test_result(self, success: bool) -> None:
        self._micro_test_result = success
        self._relayout()   # the status line text (and height) changed

    # ── fonts ─────────────────────────────────────────────────────────────────

    def _fonts(self) -> tuple[pygame.font.Font, pygame.font.Font, pygame.font.Font]:
        if self._font_md is None or self._font_body is None or self._font_sm is None:
            self._font_md = pygame.font.SysFont("monospace", 20)
            self._font_body = pygame.font.SysFont("monospace", 16)
            self._font_sm = pygame.font.SysFont("monospace", 13)
        return self._font_md, self._font_body, self._font_sm

    # ── layout ────────────────────────────────────────────────────────────────

    def _content_width(self) -> int:
        """Usable content width; the scrollbar lives inside the right padding."""
        assert self._size is not None
        return max(100, self._size[0] - 2 * _PAD)

    def min_size(self) -> tuple[int, int]:
        """Smallest window size that keeps the layout usable, derived from the content.

        Width: the widest non-wrapping row (tab bar, option buttons, action buttons,
        Save/Cancel), floored at ``_MIN_W`` so wrapped labels stay readable.
        Height: header + footer + the General and Voice tabs without scrolling
        (the longer Alerts/Airflow tabs scroll).
        """
        _, body, _ = self._fonts()
        tabs_w = (sum(body.size(t.label)[0] + 2 * 16 for t in self._tabs)
                  + 4 * (len(self._tabs) - 1))
        widest = max(tabs_w, 2 * _BTN_W + 10)
        for tab in self._tabs:
            for spec in tab.controls:
                if isinstance(spec, Choice):
                    row = sum(body.size(label)[0] + 24 for _, label in spec.options)
                    widest = max(widest, row + 10 * (len(spec.options) - 1))
                elif isinstance(spec, Button):
                    widest = max(widest, body.size(spec.label)[0] + 30)
        w = max(_MIN_W, widest + 2 * _PAD)

        # Measure with a throwaway layout, then restore the panel state.
        saved_size, saved_tab = self._size, self._tab_bar.active
        content_h = 0
        for tab_id in ("general", "voice"):
            self._tab_bar.active = next(i for i, t in enumerate(self._tabs) if t.id == tab_id)
            self.layout(w, 10_000)
            content_h = max(content_h, self._content_h)
        footer_h = 10_000 - self._footer_top
        h = self._header_h + content_h + footer_h
        self._tab_bar.active = saved_tab
        self._size = None
        if saved_size is not None:
            self.layout(*saved_size)
        return w, h

    def layout(self, w: int, h: int) -> None:
        """Position the header and the active tab's controls for a ``w`` x ``h`` window.

        Called on open, on resize, on tab switch and whenever inline errors change.
        """
        self._size = (w, h)
        md, body, sm = self._fonts()
        tabs_y = _TITLE_Y + md.get_linesize() + 8
        self._tab_bar.layout(_PAD, tabs_y, w - 2 * _PAD)
        self._header_h = tabs_y + _TAB_H

        lh_body, lh_sm = body.get_linesize(), sm.get_linesize()
        x0 = _PAD
        cw = self._content_width()
        two_col = cw >= _TWO_COL_MIN_W
        col_w = (cw - _COL_GAP) // 2 if two_col else cw

        def measure_body(s: str) -> int:
            return body.size(s)[0]

        def measure_sm(s: str) -> int:
            return sm.size(s)[0]

        def extras(p: _Placed, y: int, name: str, help_text: str, width: int) -> int:
            """Place the inline error then the helper text under a field; new y."""
            if name in self._errors:
                p.error_y = y
                p.error_lines = wrap_text(self._errors[name], width, measure_sm)
                y += len(p.error_lines) * lh_sm + 2
            if help_text:
                p.help_y = y
                p.help_lines = wrap_text(help_text, width, measure_sm)
                y += len(p.help_lines) * lh_sm + 2
            return y

        placed: list[_Placed] = []
        y = 14
        col = 0          # next column for a half-width checkbox (2-column grid)
        row_top = 0
        row_h = 0

        def flush_row() -> None:
            nonlocal y, col, row_h
            if col == 1:
                y = row_top + row_h + 6
                col = 0
                row_h = 0

        for spec in self._tabs[self._tab_bar.active].controls:
            if isinstance(spec, Checkbox):
                half = spec.half and two_col
                if not half:
                    flush_row()
                cell_w = col_w if half else cw
                text_w = cell_w - (_CHECK + 10)
                cx = x0 + col_w + _COL_GAP if half and col == 1 else x0
                cy = row_top if half and col == 1 else y
                p = _Placed(spec, pygame.Rect(cx, cy, cell_w, 0), pygame.Rect(0, 0, 0, 0),
                            lines=wrap_text(spec.label, text_w, measure_body))
                bottom = extras(p, cy + max(_CHECK + 4, len(p.lines) * lh_body + 2),
                                spec.field, spec.help, text_w)
                p.rect.height = bottom - cy
                p.bounds = p.rect.copy()
                placed.append(p)
                if not half:
                    y = bottom + 6
                elif col == 0:
                    row_top, row_h, col = cy, p.rect.height, 1
                else:
                    row_h = max(row_h, p.rect.height)
                    y = row_top + row_h + 6
                    col, row_h = 0, 0
                continue

            flush_row()
            top = y
            if isinstance(spec, Section):
                y += 12 if spec.major else 4
                label_y = y + (8 if spec.line else 0)
                y = label_y + lh_sm + 8
                rect = pygame.Rect(x0, top, cw, y - top)
                placed.append(_Placed(spec, rect, rect.copy(), label_y=label_y))
            elif isinstance(spec, TextInput):
                font = md if spec.large else body
                box_h = font.get_linesize() + (16 if spec.large else 12)
                box_w = min(spec.width or cw, cw)
                label_w = body.size(spec.label)[0]
                unit_w = body.size(spec.unit)[0] + 8 if spec.unit else 0
                inline = spec.inline and label_w + 10 + box_w + unit_w <= cw
                if inline:
                    box = pygame.Rect(x0 + label_w + 10, y, box_w, box_h)
                    p = _Placed(spec, box, pygame.Rect(0, 0, 0, 0), label_y=y, inline=True)
                else:
                    lines = wrap_text(spec.label, cw, measure_sm)
                    box_w = min(box_w, cw - unit_w)
                    box = pygame.Rect(x0, y + len(lines) * lh_sm + 4, box_w, box_h)
                    p = _Placed(spec, box, pygame.Rect(0, 0, 0, 0), label_y=y, lines=lines)
                y = extras(p, box.bottom + 4, spec.field, spec.help, cw)
                p.bounds = pygame.Rect(x0, top, cw, y - top)
                placed.append(p)
                y += 8
            elif isinstance(spec, Choice):
                lines = wrap_text(spec.label, cw, measure_sm)
                gap = 10
                n = len(spec.options)
                btn_w = min(140, (cw - gap * (n - 1)) // n)
                by = y + len(lines) * lh_sm + 4
                options = [
                    (value, pygame.Rect(x0 + i * (btn_w + gap), by, btn_w, 30))
                    for i, (value, _) in enumerate(spec.options)
                ]
                p = _Placed(spec, pygame.Rect(x0, top, cw, by + 30 - top),
                            pygame.Rect(0, 0, 0, 0), label_y=y, lines=lines, options=options)
                y = extras(p, by + 30 + 4, spec.field, spec.help, cw)
                p.bounds = pygame.Rect(x0, top, cw, y - top)
                placed.append(p)
                y += 8
            elif isinstance(spec, Button):
                btn = pygame.Rect(x0, y, min(cw, max(150, body.size(spec.label)[0] + 30)), 32)
                placed.append(_Placed(spec, btn, btn.copy()))
                y = btn.bottom + 8
            elif isinstance(spec, Note):
                lines = wrap_text(spec.text, cw, measure_sm)
                rect = pygame.Rect(x0, y, cw, len(lines) * lh_sm)
                placed.append(_Placed(spec, rect, rect.copy(), lines=lines))
                y = rect.bottom + 8
            elif isinstance(spec, MicroStatus):
                text, _ = self._micro_status() if self.form is not None else ("", C_NOTE)
                lines = wrap_text(text, cw, measure_sm) if text else [""]
                rect = pygame.Rect(x0, y, cw, len(lines) * lh_sm)
                placed.append(_Placed(spec, rect, rect.copy(), lines=lines))
                y = rect.bottom + 8
        flush_row()

        self._placed = placed
        self._content_h = y + 14
        self._update_viewport()

    def _relayout(self) -> None:
        if self._size is not None:
            self.layout(*self._size)

    def _update_viewport(self) -> None:
        """Recompute footer (error summary + buttons) and the scrolling viewport."""
        if self._size is None:
            return
        w, h = self._size
        _, _, sm = self._fonts()
        lh_sm = sm.get_linesize()
        self._summary_lines = []
        if self._errors:
            n = len(self._errors)
            tabs = sorted({self._field_tab[f] for f in self._errors if f in self._field_tab})
            where = ", ".join(self._tabs[i].label for i in tabs)
            text = f"Fix {n} error{'s' if n > 1 else ''} before saving"
            text += f" ({where})" if where else ""
            self._summary_lines = wrap_text(text, max(50, w - 2 * _PAD), lambda s: sm.size(s)[0])
        errors_h = len(self._summary_lines) * lh_sm + (8 if self._summary_lines else 0)
        footer_h = 14 + errors_h + _BTN_H + 14
        footer_top = max(self._header_h, h - footer_h)
        self._footer_top = footer_top
        btn_y = footer_top + 14 + errors_h
        self._btn_cancel = pygame.Rect(w - _PAD - _BTN_W, btn_y, _BTN_W, _BTN_H)
        self._btn_save = pygame.Rect(self._btn_cancel.x - 10 - _BTN_W, btn_y, _BTN_W, _BTN_H)
        self._viewport = pygame.Rect(0, self._header_h, w, max(0, footer_top - self._header_h))
        self._scroll.set_sizes(self._viewport.height, self._content_h)

    def _scroll_into_view(self, rect: pygame.Rect) -> None:
        s = self._scroll
        if rect.top < s.offset:
            s.offset = rect.top - 8
        elif rect.bottom > s.offset + s.viewport_h:
            s.offset = min(rect.top - 8, rect.bottom - s.viewport_h + 8)
        s.set_sizes(s.viewport_h, s.content_h)  # re-clamp

    def _placed_for(self, name: str) -> _Placed | None:
        for p in self._placed:
            if getattr(p.spec, "field", None) == name:
                return p
        return None

    # ── state helpers ─────────────────────────────────────────────────────────

    def _is_active(self, key: str) -> bool:
        """Whether a control keyed by a form field or button action is interactive."""
        form = self.form
        assert form is not None
        if key in ("voice", "test_voice"):
            return form.bools["voice_enabled"]
        if key == "test_microcontroller":
            return form.is_enabled(key) and bool(form.texts["microcontroller_port"])
        return form.is_enabled(key)

    def _text_fields(self) -> list[str]:
        """Enabled text fields of the active tab, in display order."""
        return [p.spec.field for p in self._placed
                if isinstance(p.spec, TextInput) and self._is_active(p.spec.field)]

    def _activate(self, name: str | None) -> None:
        self._active_field = name
        self._cursor_visible = True
        self._cursor_timer = 0
        if name is not None:
            p = self._placed_for(name)
            if p is not None:
                self._scroll_into_view(p.bounds)

    def _cycle_field(self, step: int) -> None:
        fields = self._text_fields()
        if not fields:
            return
        if self._active_field in fields:
            idx = (fields.index(self._active_field) + step) % len(fields)
        else:
            idx = 0 if step > 0 else len(fields) - 1
        self._activate(fields[idx])

    def _switch_tab(self, index: int) -> None:
        """Show tab ``index`` from the top, dropping keyboard focus."""
        if index == self._tab_bar.active and self._placed:
            return
        self._tab_bar.select(index)
        self._active_field = None
        self._scroll.reset()
        self._relayout()

    def _clear_error(self, name: str) -> None:
        if self._errors.pop(name, None) is not None:
            self._relayout()

    def _on_text_changed(self, name: str) -> None:
        if name == "microcontroller_port":
            self._micro_test_result = None
            self._relayout()   # the status line depends on the port
        self._clear_error(name)
        self._cursor_visible = True
        self._cursor_timer = 0

    def _save(self) -> Action:
        assert self.form is not None
        errors = self.form.validate()
        if not errors:
            self._errors = {}
            return "saved"
        self._errors = errors
        # First field in error, in tab order then display order.
        first: str | None = None
        for tab in self._tabs:
            for spec in tab.controls:
                name = getattr(spec, "field", None)
                if name in errors:
                    first = name
                    break
            if first is not None:
                break
        if first is not None and self._field_tab[first] != self._tab_bar.active:
            self._switch_tab(self._field_tab[first])
        else:
            self._relayout()
        if first is not None:
            p = self._placed_for(first)
            if p is not None and isinstance(p.spec, TextInput) and self._is_active(first):
                self._activate(first)
            elif p is not None:
                self._scroll_into_view(p.bounds)
        return None

    # ── events ────────────────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event) -> Action:
        if self.form is None:
            return None
        if event.type == pygame.MOUSEMOTION:
            self._mouse = event.pos
        elif event.type == pygame.WINDOWLEAVE:
            self._mouse = None
        elif event.type == pygame.MOUSEWHEEL:
            self._scroll.scroll(event.y)
        elif event.type == pygame.KEYDOWN:
            return self._handle_key(event)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._mouse = event.pos
            return self._handle_click(event.pos)
        return None

    def _handle_key(self, event: pygame.event.Event) -> Action:
        form = self.form
        assert form is not None
        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            return self._save()
        if event.key == pygame.K_ESCAPE:
            return "cancelled"
        if event.key == pygame.K_TAB:
            self._cycle_field(-1 if event.mod & pygame.KMOD_SHIFT else 1)
            return None
        name = self._active_field
        if name is None or not self._is_active(name):
            if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                n = len(self._tabs)
                step = 1 if event.key == pygame.K_RIGHT else -1
                self._switch_tab((self._tab_bar.active + step) % n)
            return None
        if event.key == pygame.K_BACKSPACE:
            changed = form.backspace(name)
        else:
            changed = bool(event.unicode) and form.type_char(name, event.unicode)
        if changed:
            self._on_text_changed(name)
        return None

    def _handle_click(self, pos: tuple[int, int]) -> Action:
        form = self.form
        assert form is not None
        if self._btn_save.collidepoint(pos):
            return self._save()
        if self._btn_cancel.collidepoint(pos):
            return "cancelled"
        tab = self._tab_bar.hit(pos)
        if tab is not None:
            self._switch_tab(tab)
            return None
        if not self._viewport.collidepoint(pos):
            return None
        cpos = (pos[0], self._scroll.to_content(pos[1], self._viewport.top))
        for p in self._placed:
            spec = p.spec
            if isinstance(spec, Checkbox) and p.rect.collidepoint(cpos):
                if self._is_active(spec.field):
                    form.toggle(spec.field)
                    if spec.field == "microcontroller_enabled":
                        self._micro_test_result = None
                    self._relayout()   # dependent fields / status line may change
                return None
            if isinstance(spec, TextInput) and p.rect.collidepoint(cpos):
                if self._is_active(spec.field):
                    self._activate(spec.field)
                return None
            if isinstance(spec, Choice):
                for value, rect in p.options:
                    if rect.collidepoint(cpos):
                        if self._is_active(spec.field):
                            setattr(form, spec.field, value)
                            self._clear_error(spec.field)
                        return None
            if isinstance(spec, Button) and p.rect.collidepoint(cpos):
                return spec.action if self._is_active(spec.action) else None
        self._active_field = None
        return None

    # ── drawing ───────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface, dt_ms: int) -> None:
        if self.form is None:
            return
        if self._size != surface.get_size():
            self.layout(*surface.get_size())

        self._cursor_timer += dt_ms
        if self._cursor_timer >= _CURSOR_BLINK_MS:
            self._cursor_timer = 0
            self._cursor_visible = not self._cursor_visible

        md, body, sm = self._fonts()
        w, h = surface.get_size()
        surface.fill(C_CARD)

        # Scrolling content
        vp = self._viewport
        dy = vp.top - self._scroll.offset
        old_clip = surface.get_clip()
        surface.set_clip(vp)
        for p in self._placed:
            if p.bounds.bottom + dy < vp.top or p.bounds.top + dy > vp.bottom:
                continue
            self._draw_control(surface, p, dy)
        surface.set_clip(old_clip)

        thumb = self._scroll.indicator()
        if thumb is not None:
            top, height = thumb
            bar = pygame.Rect(w - _SCROLLBAR_W - 4, vp.top + top, _SCROLLBAR_W, height)
            pygame.draw.rect(surface, C_BORDER, bar, border_radius=3)

        # Fixed header: title + tab bar
        surface.fill(C_CARD, pygame.Rect(0, 0, w, self._header_h))
        surface.blit(md.render("Settings", True, C_TEXT), (_PAD, _TITLE_Y))
        pygame.draw.line(surface, C_BORDER, (0, self._header_h - 1), (w, self._header_h - 1))
        for i, rect in enumerate(self._tab_bar.rects):
            active = i == self._tab_bar.active
            hover = not active and self._mouse is not None and rect.collidepoint(self._mouse)
            bg = C_TAB_ACTIVE if active else (C_INPUT_ACTIVE if hover else C_INPUT_BG)
            pygame.draw.rect(surface, bg, rect, border_top_left_radius=6,
                             border_top_right_radius=6)
            pygame.draw.rect(surface, C_ACCENT if active else C_BORDER, rect, 1,
                             border_top_left_radius=6, border_top_right_radius=6)
            label = body.render(self._tab_bar.labels[i], True, C_TEXT if active else C_TEXT_MUTED)
            surface.set_clip(rect)
            surface.blit(label, label.get_rect(center=rect.center))
            surface.set_clip(old_clip)

        # Fixed footer
        surface.fill(C_CARD, pygame.Rect(0, self._footer_top, w, h - self._footer_top))
        pygame.draw.line(surface, C_BORDER, (0, self._footer_top), (w, self._footer_top))
        y = self._footer_top + 14
        for line in self._summary_lines:
            surface.blit(sm.render(line, True, C_ERROR), (_PAD, y))
            y += sm.get_linesize()
        hover_save = self._mouse is not None and self._btn_save.collidepoint(self._mouse)
        hover_cancel = self._mouse is not None and self._btn_cancel.collidepoint(self._mouse)
        self._draw_btn(surface, self._btn_save, "Save", C_BTN_HOVER if hover_save else C_BTN_SAVE)
        self._draw_btn(surface, self._btn_cancel, "Cancel",
                       C_BTN_CANCEL_HOVER if hover_cancel else C_BTN_CANCEL)

    def _draw_btn(self, surface: pygame.Surface, rect: pygame.Rect, text: str,
                  color: tuple[int, int, int]) -> None:
        _, body, _ = self._fonts()
        pygame.draw.rect(surface, color, rect, border_radius=6)
        pygame.draw.rect(surface, C_BORDER, rect, 1, border_radius=6)
        surf = body.render(text, True, C_TEXT)
        surface.blit(surf, surf.get_rect(center=rect.center))

    def _draw_extras(self, surface: pygame.Surface, p: _Placed, x: int, dy: int,
                     enabled: bool) -> None:
        """Inline error (red) then helper text (dimmer) under a field."""
        _, _, sm = self._fonts()
        lh = sm.get_linesize()
        for i, line in enumerate(p.error_lines):
            surface.blit(sm.render(line, True, C_ERROR), (x, p.error_y + dy + i * lh))
        color = C_TEXT_MUTED if enabled else C_DIM
        for i, line in enumerate(p.help_lines):
            surface.blit(sm.render(line, True, color), (x, p.help_y + dy + i * lh))

    def _draw_control(self, surface: pygame.Surface, p: _Placed, dy: int) -> None:
        form = self.form
        assert form is not None
        _, body, sm = self._fonts()
        spec = p.spec
        rect = p.rect.move(0, dy)
        lh_sm = sm.get_linesize()

        if isinstance(spec, Section):
            line_y = rect.y + (12 if spec.major else 4)
            if spec.line:
                if spec.major:
                    pygame.draw.line(surface, C_BORDER, (0, line_y), (surface.get_width(), line_y))
                else:
                    pygame.draw.line(surface, C_DIVIDER, (rect.x, line_y), (rect.right, line_y))
            color = C_TEXT_MUTED if spec.major else C_GROUP_LABEL
            surface.blit(sm.render(spec.title, True, color), (rect.x, p.label_y + dy))

        elif isinstance(spec, Checkbox):
            enabled = self._is_active(spec.field)
            box = pygame.Rect(rect.x, rect.y + 2, _CHECK, _CHECK)
            edge = C_ACCENT if enabled else C_BORDER_DISABLED
            pygame.draw.rect(surface, C_INPUT_BG, box, border_radius=3)
            pygame.draw.rect(surface, edge, box, 1, border_radius=3)
            if form.bools[spec.field]:
                pygame.draw.rect(surface, edge, box.inflate(-5, -5), border_radius=2)
            color = C_TEXT if enabled else C_DIM
            lh = body.get_linesize()
            ty = box.y + (_CHECK - lh) // 2
            for i, line in enumerate(p.lines):
                surface.blit(body.render(line, True, color), (box.right + 10, ty + i * lh))
            self._draw_extras(surface, p, box.right + 10, dy, enabled)

        elif isinstance(spec, TextInput):
            self._draw_text_input(surface, p, spec, rect, dy)

        elif isinstance(spec, Choice):
            enabled = self._is_active(spec.field)
            label_color = C_GROUP_LABEL if enabled else C_DIM
            for i, line in enumerate(p.lines):
                surface.blit(sm.render(line, True, label_color),
                             (rect.x, p.label_y + dy + i * lh_sm))
            current = getattr(form, spec.field)
            labels = dict(spec.options)
            for value, opt in p.options:
                r = opt.move(0, dy)
                selected = current == value
                if not enabled:
                    bg, edge, fg = C_INPUT_DISABLED, C_BORDER_DISABLED, C_DIM
                elif selected:
                    bg, edge, fg = C_ACCENT, C_ACCENT, C_TEXT_ON_ACCENT
                else:
                    bg, edge, fg = C_INPUT_BG, C_BORDER, C_TEXT
                if spec.field in self._errors:
                    edge = C_ERROR
                pygame.draw.rect(surface, bg, r, border_radius=6)
                pygame.draw.rect(surface, edge, r, 1, border_radius=6)
                surf = body.render(labels[value], True, fg)
                surface.blit(surf, surf.get_rect(center=r.center))
            self._draw_extras(surface, p, rect.x, dy, enabled)

        elif isinstance(spec, Button):
            enabled = self._is_active(spec.action)
            bg, edge, fg = ((C_BTN_TEST, C_BTN_TEST_BORDER, C_TEXT) if enabled
                            else (C_INPUT_DISABLED, C_BORDER_DISABLED, C_DIM))
            pygame.draw.rect(surface, bg, rect, border_radius=6)
            pygame.draw.rect(surface, edge, rect, 1, border_radius=6)
            surf = body.render(spec.label, True, fg)
            surface.blit(surf, surf.get_rect(center=rect.center))

        elif isinstance(spec, Note):
            active = spec.enabled_by is None or self._is_active(spec.enabled_by)
            color = C_NOTE if active else C_DIM
            for i, line in enumerate(p.lines):
                surface.blit(sm.render(line, True, color), (rect.x, rect.y + i * lh_sm))

        elif isinstance(spec, MicroStatus):
            text, color = self._micro_status()
            if text:
                lines = wrap_text(text, rect.width, lambda s: sm.size(s)[0])
                for i, line in enumerate(lines):
                    surface.blit(sm.render(line, True, color), (rect.x, rect.y + i * lh_sm))

    def _micro_status(self) -> tuple[str, tuple[int, int, int]]:
        form = self.form
        assert form is not None
        if self._micro_test_result is None:
            missing = form.bools["microcontroller_enabled"] and not form.texts["microcontroller_port"]
            return ("No serial port detected automatically; enter one manually"
                    if missing else "", C_NOTE)
        if self._micro_test_result:
            return "Connected: the device replied PONG", C_SUCCESS
        return "No response from the device", C_ERROR

    def _draw_text_input(self, surface: pygame.Surface, p: _Placed, spec: TextInput,
                         box: pygame.Rect, dy: int) -> None:
        form = self.form
        assert form is not None
        md, body, sm = self._fonts()
        enabled = self._is_active(spec.field)
        active = enabled and self._active_field == spec.field
        has_error = spec.field in self._errors

        label_color = C_GROUP_LABEL if enabled else C_DIM
        if p.inline:
            lbl = body.render(spec.label, True, label_color)
            surface.blit(lbl, (p.bounds.x, box.y + (box.height - lbl.get_height()) // 2))
        else:
            lh = sm.get_linesize()
            for i, line in enumerate(p.lines):
                surface.blit(sm.render(line, True, label_color), (box.x, p.label_y + dy + i * lh))

        if not enabled:
            bg, edge = C_INPUT_DISABLED, C_BORDER_DISABLED
        else:
            bg = C_INPUT_ACTIVE if active else C_INPUT_BG
            edge = C_ACCENT if active else C_BORDER
        if has_error:
            edge = C_ERROR
        pygame.draw.rect(surface, bg, box, border_radius=6)
        pygame.draw.rect(surface, edge, box, 1, border_radius=6)

        font = md if spec.large else body
        text = form.texts[spec.field] + ("|" if active and self._cursor_visible else "")
        surf = font.render(text, True, C_TEXT if enabled else C_DIM)
        inner_w = box.width - 16
        # Keep the end of an overlong value (where the cursor is) visible.
        area = pygame.Rect(max(0, surf.get_width() - inner_w), 0, inner_w, surf.get_height())
        surface.blit(surf, (box.x + 8, box.y + (box.height - surf.get_height()) // 2), area)

        if spec.unit:
            unit = body.render(spec.unit, True, label_color)
            surface.blit(unit, (box.right + 8, box.y + (box.height - unit.get_height()) // 2))

        self._draw_extras(surface, p, p.bounds.x, dy, enabled)
