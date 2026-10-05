"""Help window content: describes every dashboard element."""

from typing import NamedTuple

import pygame

from simraceengineer.dashboard.colors import (
    C_ACCENT,
    C_BORDER,
    C_BTN_GEAR,
    C_BTN_GEAR_HOVER,
    C_DIVIDER,
    C_GREEN,
    C_LIGHT,
    C_LOCK,
    C_MODAL_BG,
    C_MODAL_HEADER,
    C_ORANGE,
    C_SPIN,
    C_TAB_ACTIVE,
    C_YELLOW,
)
from simraceengineer.dashboard.ui.scroll import ScrollState
from simraceengineer.dashboard.ui.tabs import TabBar
from simraceengineer.dashboard.ui.text import wrap_text

# Semantic aliases for modal context
C_CARD = C_MODAL_BG
C_SECTION = C_ACCENT
C_TITLE_BAR = C_MODAL_HEADER

# Modal-specific tones that intentionally differ from the global dashboard palette
C_TITLE = (230, 230, 230)   # bright white for title bar text
C_TEXT = (200, 200, 210)    # slightly dimmer than global C_TEXT for overlay readability
C_DIM = (95, 95, 108)       # dimmer variant for secondary descriptions
C_RED = (210, 55, 55)       # slightly softer red for indicator labels

# fmt: off
_LEFT = [
    ("section", "GAUGES", "speedometer"),
    ("item",  "Speed",          "left gauge · km/h · arc: green→orange→red as limit approaches",               C_TEXT, "speedometer"),
    ("item",  "RPM",            "right gauge · engine revs · same color scheme as speed",                       C_TEXT, "rpm"),
    ("item",  "RPM Bar",        "strip at top · green / orange / red based on rev zone",                        C_TEXT, "rpm"),

    ("section", "GEARS & PEDALS", "gearbox"),
    ("item",  "Gear",           "large number in center · N=neutral · R=reverse",                               C_TEXT, "gearbox"),
    ("item",  "> N (orange)",   "game suggested gear — appears when different from current",                    C_ORANGE, "gearbox"),
    ("item",  "C · B · T",      "vertical bars: clutch (blue) · brake (red) · throttle (green)",                C_TEXT, "car-pedals"),
    ("item",  "FUEL (bar)",     "fuel percentage remaining in tank",                                             C_TEXT, "fuel"),

    ("section", "G-METER · SLIP (bottom left)", "g-force"),
    ("item",  "G dot",          "G force · top=braking · bottom=accel · sides=corners",                         C_TEXT, "g-force"),
    ("item",  "G dot color",    "green <0.8G · orange <1.5G · red ≥1.5G",                                       C_TEXT, "g-force"),
    ("item",  "SLIP bar",       "angle between velocity direction and car heading (oversteer indicator)",        C_TEXT, "drifting"),
    ("item",  "SLIP color",     "green <5° (neutral) · orange <12° · red ≥12° (high oversteer)",                C_TEXT, "drifting"),
]

_RIGHT = [
    ("section", "TIRES (bottom center)", "tire-wheel"),
    ("item",  "Tile color",        "<60° blue · 60-70° yellow · 70-95° green (ideal) · 95-103° orange · >103° red",              C_TEXT, "tire-wheel"),
    ("item",  "Orange border",     "wheelspin · wheel spins faster than expected · TCS may intervene",                             C_SPIN, "tire-wheel"),
    ("item",  "Red border",        "lockup: wheel locking under heavy braking",                                                     C_LOCK, "tire-wheel"),
    ("item",  "Inner bar  ═══",    "suspension travel · blue=light · green=nominal · orange=loaded · red=bottomed out",            C_DIM, "suspension"),
    ("item",  "Outer bar  ◎",      "tyre wear remaining · green=new · yellow=used · orange=worn · red=critical",                   C_DIM, "tire-wheel"),

    ("section", "STATUS STRIP (below RPM bar)", "panel-cluster"),
    ("item",  "TCS / ASM",         "traction control (orange) or stability (yellow) intervened",                C_SPIN, "tcs"),
    ("item",  "REV",               "rev limiter active — engine at max RPM",                                    C_RED),
    ("item",  "HB",                "handbrake applied",                                                         C_RED, "parking"),
    ("item",  "LIGHT",             "headlights on — useful in races with night segments",                       C_LIGHT, "headlight"),
    ("item",  "OIL",               "oil temperature critical — above 130°C",                                    C_RED, "oil"),
    ("item",  "WATER",             "water temperature critical — above 105°C",                                  C_RED, "coolant"),
    ("item",  "FAN",               "airflow simulation microcontroller connected · shown only when the feature is enabled · dim if the cable/serial link drops mid-session", C_GREEN),

    ("section", "INFO PANEL (right)", "race-pos"),
    ("item",  "POS",               "race position · shown when available",                                      C_TEXT, "race-pos"),
    ("item",  "LAP / BEST / LAST", "current lap · best lap · last completed lap",                               C_TEXT, "lap-time"),
    ("item",  "FUEL / FUEL·LAP",   "litres in tank · consumption per lap after 1st lap change",                 C_TEXT, "fuel"),
    ("item",  "LAPS LEFT",         "estimated laps remaining with current fuel",                                 C_TEXT, "fuel"),
    ("item",  "WATER · OIL · BOOST", "fluids and turbo · orange = above safe limit",                            C_ORANGE, "turbo"),
]
# fmt: on

_TAB_LABELS = ["OVERVIEW", "DASHBOARD", "VOICE ALERTS", "SETTINGS", "LAP RECORD"]

# fmt: off
_VOICE_LEFT = [
    ("section", "LAP & PACE", "lap-time"),
    ("item", "Lap completed",
     "fires on lap change when no new best lap was set",
     C_TEXT, "lap-time"),
    ("item", "Best lap",
     "new personal best — fires instead of 'Lap completed'",
     C_GREEN, "lap-time"),
    ("item", "Final lap",
     "fires entering the last lap of a timed/lapped race",
     C_ORANGE, "flags"),
    ("item", "Race report",
     "35% and 70% race summary · position · avg tyre wear · worst tyre warning",
     C_TEXT, "lap-time"),
    ("item", "Lap delta",
     ">3s off best — fires once after the halfway point of the lap",
     C_ORANGE, "lap-time"),

    ("section", "FUEL & PIT", "fuel"),
    ("item", "Fuel low",
     "fuel <20% · includes estimated laps remaining",
     C_ORANGE, "fuel"),
    ("item", "Fuel critical",
     "fuel <10% · repeats every min-interval while below threshold",
     C_RED, "fuel"),
    ("item", "Pit window",
     "2–4 laps of fuel remain in a race · 'Box box box'",
     C_ACCENT, "fuel"),
    ("item", "Fuel < 1 lap",
     "less than 1 lap of fuel · highest priority fuel alert · always active · no toggle",
     C_RED, "fuel"),

    ("section", "STRATEGY", "strategy"),
    ("item", "Strategy: pit window",
     "in pit window, can't finish · 'Box box box + reason' · toggle: voice_alert_strategy in config file",
     C_ACCENT, "strategy"),
    ("item", "Strategy: tyres",
     "2–5 laps to pit · tyres degrading · plan ahead · toggle: voice_alert_strategy in config file",
     C_ORANGE, "tire-wheel"),
]

_VOICE_RIGHT = [
    ("section", "ENGINE", "engine"),
    ("item", "Water temp",
     "coolant >105°C · repeats every 20s while above threshold",
     C_RED, "coolant"),
    ("item", "Oil temp",
     "oil >130°C · repeats every 20s while above threshold",
     C_RED, "oil"),

    ("section", "TYRES", "tire-wheel"),
    ("item", "Tyre temp",
     "any surface >100°C · hot corners named · once per lap",
     C_ORANGE, "tire-wheel"),
    ("item", "Tyre wear",
     "any inner zone >110°C · high inner temp signals wear · once per lap",
     C_ORANGE, "tire-wheel"),
    ("item", "Tyre wear %",
     "stint avg wear hits each 10% block · fires once per bucket",
     C_ORANGE, "tire-wheel"),
    ("item", "Pressure low",
     "any tyre <160 kPa · grip loss / puncture risk · once per lap",
     C_RED, "tire-pressure"),
    ("item", "Pressure high",
     "any tyre >250 kPa · blowout risk in heat · once per lap",
     C_RED, "tire-pressure"),

    ("section", "PLANNED PIT", "pit-stop"),
    ("item", "Approaching",
     "'Pit in N lap(s)' · fires 2 laps before planned stop · toggle: voice_alert_strategy in config file",
     C_ACCENT, "pit-stop"),
    ("item", "Box now",
     "'Box this lap. On strategy' · on the planned stop lap",
     C_GREEN, "pit-stop"),
    ("item", "Tyre warning",
     "tyres won't reach planned stop · fires when life < plan lap",
     C_ORANGE, "tire-wheel"),
    ("item", "Missed / rescheduled",
     "missed window · reschedules to new lap if fuel allows",
     C_RED, "pit-stop"),

    ("section", "HOW TO READ", "info"),
    ("item", "Corner names",
     "front/rear + left/right · only affected corners are named",
     C_DIM),
    ("item", "Cooldowns",
     "same alert won't repeat until its cooldown expires",
     C_DIM),
    ("item", "Thresholds",
     "all values configurable via the SETTINGS tab",
     C_DIM),
]
# fmt: on

# Three feature cards — rendered full-width at the top of the APP GUIDE tab.
# Each entry: ("card", title, subtitle, description, accent_color, icon_key)
# fmt: off
_APP_HEADER = [
    ("card",
     "1 · DASHBOARD",
     "Real-time telemetry while driving",
     ("Connect the PS5 to the same network. The app displays speed · RPM · gear · tyres · G-forces · fuel"
      " and electronics interventions on a second screen."),
     C_ACCENT, "speedometer"),
    ("card",
     "2 · VOICE ALERTS",
     "Pit-wall engineer while you race",
     ("Automatic spoken alerts: fuel status · tyre temps · lap pace · pit windows and planned stop reminders."
      " Available in English or Portuguese."),
     C_GREEN, "voice-cmd"),
    ("card",
     "3 · LAP ANALYSIS",
     "Post-session interactive browser viewer",
     ("After the session ends: click ANALYSIS in the header · select session.parquet (all laps merged into one file)"
      " · the browser opens at localhost:8050."),
     C_ORANGE, "lap-analysis"),
]

_APP_LEFT = [
    ("section", "CONNECTION STATUS", "semaphore"),
    ("item",  "LIVE  (green)",    "connected to GT7 telemetry and receiving data",                C_GREEN),
    ("item",  "WAIT  (yellow)",   "connecting or connected but awaiting first packet",            C_YELLOW),
    ("item",  "ERR   (orange)",   "connection error — check device IP and network",               C_ORANGE),
    ("item",  "DISC  (grey)",     "disconnected — device IP is set but not active",               C_DIM),
    ("item",  "OFF   (red)",      "no device IP configured — open Settings to set one",          C_RED),

    ("section", "RECORDING", "rec-button"),
    ("item",  "Session name",      "set folder name · green = name set · locked while recording", C_TEXT, "pencil"),
    ("item",  "REC",              "rec = start · pause = pause · resumes same session",          C_RED, "rec-button"),
]

_APP_RIGHT = [
    ("section", "HEADER BUTTONS", "panel-cluster"),
    ("item",  "Strategy",         "configure planned pit stops · green background when stops are set", C_GREEN, "strategy"),
    ("item",  "Analysis",         "opens file picker → select session.parquet → browser at :8050", C_ACCENT, "lap-analysis"),
    ("item",  "Help",             "opens this guide in its own window · click again to focus it", C_TEXT, "info"),
    ("item",  "Settings",         "opens Settings in its own window · the dashboard stays live", C_TEXT, "settings"),
    ("item",  "Close dashboard",  "closing the main dashboard window quits the app",             C_DIM),
]

_SETTINGS_LEFT = [
    ("section", "SETTINGS WINDOW", "settings"),
    ("item",  "Separate window",   "gear button opens Settings in its own resizable window · the dashboard keeps updating · clicking the gear again focuses it", C_TEXT, "settings"),
    ("item",  "Tabs",              "General · Voice · Alerts · Airflow (only when the airflow feature is unlocked) · click or ←/→ when no field is active", C_TEXT),
    ("item",  "Save · Enter",      "applies and stores every change in sim-race.conf",            C_GREEN),
    ("item",  "Cancel · Esc · close", "discards unsaved changes · closing the window equals Cancel", C_RED),
    ("item",  "Tab / Shift+Tab",   "move between text fields · mouse wheel scrolls long tabs",    C_TEXT),
    ("item",  "Validation",        "invalid values are shown in red under the field and Save jumps to the tab with the error", C_ORANGE),
    ("item",  "First launch",      "with no Device IP set, Settings opens on General with the IP field focused", C_ACCENT),

    ("section", "GENERAL TAB", "semaphore"),
    ("item",  "Device IP address", "PS5 / PC running GT7 · required to receive telemetry · 4 numbers 0–255 (e.g. 192.168.1.20)", C_TEXT),
    ("item",  "Record laps automatically when a session starts", "saves every lap for the post-session lap analysis", C_TEXT, "rec-button"),
    ("item",  "Fuel per lap estimate", "Last lap: previous lap's consumption · Average: session rolling average", C_TEXT, "fuel"),

    ("section", "VOICE TAB", "voice-cmd"),
    ("item",  "Enable voice alerts", "master switch for every spoken alert",                     C_TEXT),
    ("item",  "Voice language",    "English or Português · takes effect after restarting the app", C_TEXT),
    ("item",  "Test voice",        "plays a sample alert in the selected language",               C_TEXT),

    ("section", "TYRE WEAR ALERT", "tire-wheel"),
    ("item",  "Tyre wear milestones", "Alerts tab · announce the average tyre wear as it grows",  C_ORANGE, "tire-wheel"),
    ("item",  "Announce every … % of wear", "milestone step · 1–99 · default 10",                C_TEXT),

    ("section", "AIRFLOW SIMULATION"),
    ("item",  "Enable airflow simulation", "Airflow tab · drives fans from car speed via a USB microcontroller · requires app restart", C_TEXT),
    ("item",  "Serial port (leave blank to auto-detect)", "filled in automatically when exactly one serial device is detected · type one in manually otherwise", C_TEXT),
    ("item",  "Test connection",   "sends PING to the device and reports success if it replies PONG", C_TEXT),
    ("item",  "Fan speed ceiling", "km/h at which the fans reach 100% · 1–999 · default 220 · lower = stronger airflow at low speed", C_TEXT),
]

_SETTINGS_RIGHT = [
    ("section", "ALERTS TAB · RACE", "racing"),
    ("item",  "Lap completed",     "announce each lap time when no new best was set",              C_TEXT, "lap-time"),
    ("item",  "New best lap",      "announce when a new personal best is set",                     C_GREEN, "lap-time"),
    ("item",  "Final lap",         "announce entering the last lap of a timed / lapped race",      C_ORANGE, "flags"),
    ("item",  "Lap time delta",    "warn when lap pace exceeds the configured delta threshold",    C_ORANGE, "lap-time"),
    ("item",  "Race progress report", "35% and 70% race summary · position · avg tyre wear · worst tyre warning", C_TEXT, "lap-time"),
    ("item",  "Position gained or lost", "position gained → encouragement · position lost → support · 15s cooldown", C_GREEN, "race-pos"),
    ("item",  "Laps remaining countdown", "countdown at 5, 4, 3, 2, 1 laps remaining · only in races ≥ 10 laps", C_ACCENT, "flags"),

    ("section", "FUEL AND PIT STOPS", "fuel"),
    ("item",  "Fuel low",          "warn when fuel drops below low threshold (default 20%)",       C_ORANGE, "fuel"),
    ("item",  "Fuel critical",     "warn when fuel drops below critical threshold (default 10%)",  C_RED, "fuel"),
    ("item",  "Pit window",        "alert when 2–4 laps of fuel remain in a race",                C_ACCENT, "fuel"),
    ("item",  "Fuel saving warning", "warn when fuel margin < 1.5 laps to finish · only in races ≥ 10 laps · replaces fuel-to-finish call", C_ORANGE, "fuel"),

    ("section", "CAR HEALTH", "engine"),
    ("item",  "Engine / Oil temperature", "warn when coolant >105°C or oil >130°C · every 20s",  C_RED, "engine"),
    ("item",  "Tyre temperature",  "warn when any surface temp >100°C · once per lap",            C_ORANGE, "tire-wheel"),
    ("item",  "Tyre inner temperature", "warn when any inner zone >110°C · wear indicator",       C_ORANGE, "tire-wheel"),
    ("item",  "Tyre pressure",     "warn below 160 kPa or above 250 kPa · once per lap",         C_RED, "tire-pressure"),

    ("section", "STRATEGY ALERTS", "strategy"),
    ("item",  "Strategy check-in", "periodic strategy briefing: fuel laps, recommended box lap · fires at 33%/66% of race (≥10 laps) or every 3 laps (short races)", C_ACCENT, "strategy"),
    ("item",  "Strategy revised",  "fires when strategy health changes to REVISE: pit lap has shifted by >2 laps from plan", C_ORANGE, "strategy"),
    ("item",  "Fuel saving recommendation", "fires when fuel delta is between 0 and fuel_save_delta_l (default 2 L): suggests lift-and-coast to extend range", C_ORANGE, "fuel"),
    ("item",  "Advisor pit window", "fires 1–2 laps before advisor pit window opens, and once when the window is active: 'box window open, N laps to box'", C_ACCENT, "strategy"),
]

_LAP_RECORD_LEFT = [
    ("section", "FILE STORAGE", "time"),
    ("item",  "Location",              "~/sim-race-engineer/laps/<YYYY-MM-DDTHHMMSS>/lap_NN.parquet",       C_TEXT),
    ("item",  "session.parquet",       "all laps merged · auto-created at session end",              C_ACCENT),
    ("item",  "Format",                "Parquet · Snappy · ~60 Hz · auto-saved on lap change",       C_TEXT),

    ("section", "TIMING", "lap-time"),
    ("item",  "tick / packet_id",      "frame index within lap · GT7 packet counter",                C_TEXT, "lap-time"),
    ("item",  "lap_number",            "lap number in session · starts at 1",                        C_TEXT, "lap-time"),
    ("item",  "lap_time_ms / lap_finish_ms", "in-lap elapsed (ms) · official finish time (ms)",     C_TEXT, "lap-time"),

    ("section", "MOTION", "speedometer"),
    ("item",  "speed_kmh",             "km/h · derived from velocity vector",                        C_TEXT, "speedometer"),
    ("item",  "pos_x/y/z · vel_x/y/z","world position (m) · world velocity (m/s)",                 C_TEXT),

    ("section", "CONTROLS", "car-pedals"),
    ("item",  "throttle / brake / clutch / handbrake", "0.0–1.0 · pedal inputs",                   C_TEXT, "car-pedals"),
    ("item",  "gear / rev_limiter",    "0=R 15=N 1–8=gear · bool at max RPM",                       C_TEXT, "gearbox"),

    ("section", "SESSION", "flags"),
    ("item",  "session_type",          "\"race\" or \"practice\" · derived from GT7 flags",          C_TEXT, "flags"),
    ("item",  "total_laps / cars_in_race", "scheduled laps (0=unlimited) · field size",             C_TEXT, "race-pos"),
]

_LAP_RECORD_RIGHT = [
    ("section", "ENGINE", "engine"),
    ("item",  "rpm / turbo_boost",     "RPM · bar above atmosphere",                                 C_TEXT, "engine"),
    ("item",  "water_temp / oil_temp", "°C · coolant · oil",                                         C_TEXT, "coolant"),
    ("item",  "fuel_level",            "L · instantaneous fuel remaining",                            C_TEXT, "fuel"),

    ("section", "DYNAMICS", "g-force"),
    ("item",  "g_lat / g_lon",         "G · lateral · longitudinal (EMA-smoothed)",                  C_TEXT, "g-force"),
    ("item",  "slip_angle_deg",        "° · yaw slip angle · oversteer indicator",                   C_TEXT, "drifting"),

    ("section", "TYRES", "tire-wheel"),
    ("item",  "tire_fl/fr/rl/rr_temp", "°C · surface temp per corner (FL FR RL RR)",                C_TEXT, "tire-wheel"),
    ("item",  "sus_fl/fr/rl/rr",       "m · suspension travel per corner",                           C_TEXT, "suspension"),
    ("item",  "tcs_active / asm_active","bool · TCS · stability management interventions",           C_TEXT, "tcs"),

    ("section", "LAP AGGREGATES", "lap-time"),
    ("item",  "fuel_at_start/end/used", "L · fuel at start · end · consumed this lap",              C_TEXT, "fuel"),
    ("item",  "fuel_avg",               "L/lap · rolling session average",                           C_TEXT, "fuel"),
    ("item",  "full_throttle / full_brake ticks", "frames ≥ 0.98 throttle · brake",                 C_TEXT, "car-pedals"),
    ("item",  "throttle+brake / coasting ticks",  "trail braking · coasting frames",                C_TEXT, "car-pedals"),
]
# fmt: on

_FOOTER = "ESC or close the window to dismiss  ·  ←/→ switch tabs"

_PAD = 24
_COL_GAP = 28
_HEADER_H = 48      # tab bar row
_FOOTER_H = 28
_TAB_H = 30
_TWO_COLUMN_MIN_W = 900
_ITEM_GAP = 6       # gap between items
_SECTION_PRE_GAP = 12
_SECTION_UNDER_H = 7
_ICON_SZ = 14
_ICON_GAP = 5
# Entries tied to the hidden airflow-simulation feature (see AppConfig.microcontroller_unlocked)
_MICRO_SECTIONS = {"AIRFLOW SIMULATION"}
_MICRO_ITEMS = {"FAN"}


def _without_microcontroller(entries: list) -> list:
    """Drop airflow-simulation sections (with their items) and standalone items."""
    out = []
    skipping = False
    for entry in entries:
        if entry[0] == "section":
            skipping = entry[1] in _MICRO_SECTIONS
        if skipping or (entry[0] == "item" and entry[1] in _MICRO_ITEMS):
            continue
        out.append(entry)
    return out


_FEATURE_CARD_GAP = 16
_FEATURE_CARD_PAD = 10
_CONTENT_PAD_TOP = 12     # space between the tab bar and the first content row
_CONTENT_PAD_BOTTOM = 16  # space after the last content row
_DESC_INDENT = 12         # item descriptions are indented under the item name
_SCROLL_STEP = 40         # px per mouse-wheel notch
_MIN_ENTRIES_H = 160      # room below the feature cards for a few entries at minimum height
_INDICATOR_W = 4
_INDICATOR_MARGIN = 4


class _TextOp(NamedTuple):
    """One rendered text line, in content space (y = 0 is the top of the content)."""

    x: int
    y: int
    text: str
    font: str      # "body" | "title" | "small"
    color: tuple
    max_w: int     # width the line was wrapped to (column or card inner width)


class _IconOp(NamedTuple):
    """An icon centred vertically on ``cy``; skipped when the icon is not loaded."""

    x: int
    cy: int
    key: str


class _LineOp(NamedTuple):
    x1: int
    y1: int
    x2: int
    y2: int
    color: tuple


class _CardOp(NamedTuple):
    """A feature-card background with border."""

    rect: tuple[int, int, int, int]


_Op = _TextOp | _IconOp | _LineOp | _CardOp


class _RenderList(NamedTuple):
    ops: list[_Op]
    height: int  # total content height, including padding


class HelpPanel:
    """Help content rendered into its own resizable window.

    The panel is sized by ``layout(w, h)`` (called on open and on every resize) and
    draws onto whatever surface it is given. Mouse positions are window-relative,
    so hover is tracked from the window's own MOUSEMOTION events rather than the
    global ``pygame.mouse.get_pos()``.

    Content is laid out once per (tab, width) into a cached content-space render
    list (all text wrapped with ``wrap_text``) and blitted with the current scroll
    offset, clipped to the viewport between the tab bar and the footer.
    """

    def __init__(self, show_microcontroller: bool = False) -> None:
        self.active = False
        self._header_by_tab = [_APP_HEADER, None,   None,          None,            None]
        self._left_by_tab   = [_APP_LEFT,  _LEFT,   _VOICE_LEFT,  _SETTINGS_LEFT,  _LAP_RECORD_LEFT]
        self._right_by_tab  = [_APP_RIGHT, _RIGHT,  _VOICE_RIGHT, _SETTINGS_RIGHT, _LAP_RECORD_RIGHT]
        if not show_microcontroller:
            self._left_by_tab = [_without_microcontroller(e) for e in self._left_by_tab]
            self._right_by_tab = [_without_microcontroller(e) for e in self._right_by_tab]
        # Fonts are created lazily: pygame.font must be initialised first.
        self._font_body: pygame.font.Font | None = None
        self._font_title: pygame.font.Font | None = None
        self._font_small: pygame.font.Font | None = None
        self._text_cache: dict[tuple[int, str, tuple], pygame.Surface] = {}
        self._render_cache: dict[tuple[int, int], _RenderList] = {}
        self._scroll = ScrollState(step=_SCROLL_STEP)
        self._tabs: TabBar | None = None
        self._size: tuple[int, int] = (0, 0)
        self._columns = 2
        self._col_w = 0
        self._col_xs: list[int] = []
        self._hover: tuple[int, int] | None = None

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    def open(self) -> None:
        self.active = True
        self._hover = None
        self._scroll.reset()

    def close(self) -> None:
        self.active = False
        self._hover = None

    @property
    def active_tab(self) -> int:
        return self._tab_bar().active

    @property
    def columns(self) -> int:
        return self._columns

    def min_size(self) -> tuple[int, int]:
        """Smallest window size that keeps the layout usable, derived from the content.

        Width: the tab bar at its natural size, and the OVERVIEW feature cards side by
        side with their titles on one line. Height: header + footer + the feature cards
        plus room for a few entries; everything else scrolls.
        """
        self._ensure_fonts()
        small, title = self._font("small"), self._font("title")
        tabs_w = sum(small.size(label)[0] + 2 * 16 for label in _TAB_LABELS)
        tabs_w += 4 * (len(_TAB_LABELS) - 1)
        card_w = max(
            title.size(card[1])[0] + (_ICON_SZ + _ICON_GAP if card[5] else 0)
            for card in _APP_HEADER
        ) + 2 * _FEATURE_CARD_PAD
        cards_w = len(_APP_HEADER) * card_w + _FEATURE_CARD_GAP * (len(_APP_HEADER) - 1)
        w = max(tabs_w, cards_w) + 2 * _PAD

        # Measure the card block with a throwaway layout, then restore the panel state.
        saved_size = self._size
        self.layout(w, 10_000)
        cards_bottom = self._build_feature_cards([], _PAD, _CONTENT_PAD_TOP, _APP_HEADER)
        self._render_cache.clear()
        self._text_cache.clear()
        self._size = (0, 0)
        if saved_size != (0, 0):
            self.layout(*saved_size)
        return w, _HEADER_H + 1 + cards_bottom + _MIN_ENTRIES_H + _FOOTER_H

    def layout(self, w: int, h: int) -> None:
        """Recompute tab and column geometry for a ``w`` x ``h`` window."""
        self._ensure_fonts()
        if w != self._size[0]:
            # Wrapped lines depend on the width: drop layouts and stale text surfaces.
            self._render_cache.clear()
            self._text_cache.clear()
        self._size = (w, h)
        tabs = self._tab_bar()
        tabs.layout(_PAD, (_HEADER_H - _TAB_H) // 2, max(0, w - 2 * _PAD))
        content_w = max(0, w - 2 * _PAD)
        if w >= _TWO_COLUMN_MIN_W:
            self._columns = 2
            self._col_w = (content_w - _COL_GAP) // 2
            self._col_xs = [_PAD, _PAD + self._col_w + _COL_GAP]
        else:
            self._columns = 1
            self._col_w = content_w
            self._col_xs = [_PAD]
        self._sync_scroll()

    def _viewport(self) -> pygame.Rect:
        """Scrollable area between the tab bar and the footer, in window px."""
        w, h = self._size
        top = _HEADER_H + 1
        return pygame.Rect(0, top, w, max(0, h - _FOOTER_H - top))

    def _sync_scroll(self) -> None:
        if self._size == (0, 0):
            return
        self._scroll.set_sizes(self._viewport().height, self._render_list().height)

    def _on_tab_changed(self) -> None:
        self._scroll.reset()
        self._sync_scroll()

    # ── Events ─────────────────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event) -> str | None:
        """Handle an event owned by the Help window. Returns ``"closed"`` on Esc."""
        tabs = self._tab_bar()
        before = tabs.active
        result = self._dispatch(event, tabs)
        if tabs.active != before:
            self._on_tab_changed()
        return result

    def _dispatch(self, event: pygame.event.Event, tabs: TabBar) -> str | None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "closed"
            if event.key == pygame.K_LEFT:
                tabs.prev()
            elif event.key == pygame.K_RIGHT:
                tabs.next()
            return None
        if event.type == pygame.MOUSEWHEEL:
            self._sync_scroll()
            self._scroll.scroll(event.y)
            return None
        if event.type == pygame.MOUSEMOTION:
            self._hover = event.pos
            return None
        if event.type == pygame.WINDOWLEAVE:
            self._hover = None
            return None
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            index = tabs.hit(event.pos)
            if index is not None:
                tabs.select(index)
            # Any other click is deliberately ignored: Help never closes on click.
        return None

    # ── Rendering ──────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface, icons: dict | None = None) -> None:
        if not self.active:
            return
        self._ensure_fonts()
        if surface.get_size() != self._size:
            self.layout(*surface.get_size())
        w, h = self._size
        small = self._font_small
        assert small is not None

        surface.fill(C_CARD)
        self._draw_header(surface, w)

        render = self._render_list()
        self._scroll.set_sizes(self._viewport().height, render.height)
        viewport = self._viewport()
        prev_clip = surface.get_clip()
        surface.set_clip(viewport.clip(prev_clip))
        self._blit_ops(surface, render.ops, viewport, icons)
        indicator = self._scroll.indicator()
        if indicator is not None:
            top, height = indicator
            thumb = pygame.Rect(
                w - _INDICATOR_W - _INDICATOR_MARGIN, viewport.top + top, _INDICATOR_W, height
            )
            pygame.draw.rect(surface, C_DIM, thumb, border_radius=2)
        surface.set_clip(prev_clip)

        content_bottom = h - _FOOTER_H
        pygame.draw.line(surface, C_BORDER, (0, content_bottom), (w, content_bottom), 1)
        ftr = self._text(small, _FOOTER, C_DIM)
        surface.blit(ftr, ftr.get_rect(center=(w // 2, content_bottom + _FOOTER_H // 2)))

    def _blit_ops(
        self,
        surface: pygame.Surface,
        ops: list[_Op],
        viewport: pygame.Rect,
        icons: dict | None,
    ) -> None:
        """Blit content-space ops shifted by the scroll offset, culling off-screen ones."""
        dy = viewport.top - self._scroll.offset
        for op in ops:
            if isinstance(op, _TextOp):
                font = self._font(op.font)
                sy = op.y + dy
                if sy > viewport.bottom or sy + font.get_linesize() < viewport.top:
                    continue
                surface.blit(self._text(font, op.text, op.color), (op.x, sy))
            elif isinstance(op, _IconOp):
                icon = icons.get(op.key) if icons else None
                if icon:
                    surface.blit(icon, icon.get_rect(midleft=(op.x, op.cy + dy)))
            elif isinstance(op, _LineOp):
                pygame.draw.line(surface, op.color, (op.x1, op.y1 + dy), (op.x2, op.y2 + dy), 1)
            else:
                x, y, cw, ch = op.rect
                rect = pygame.Rect(x, y + dy, cw, ch)
                if not rect.colliderect(viewport):
                    continue
                pygame.draw.rect(surface, C_MODAL_HEADER, rect, border_radius=6)
                pygame.draw.rect(surface, C_DIVIDER, rect, 1, border_radius=6)

    def _draw_header(self, surface: pygame.Surface, w: int) -> None:
        small = self._font_small
        assert small is not None
        pygame.draw.rect(surface, C_TITLE_BAR, pygame.Rect(0, 0, w, _HEADER_H))
        pygame.draw.line(surface, C_BORDER, (0, _HEADER_H), (w, _HEADER_H), 1)
        tabs = self._tab_bar()
        prev_clip = surface.get_clip()
        for i, (label, rect) in enumerate(zip(tabs.labels, tabs.rects)):
            active = i == tabs.active
            hovered = self._hover is not None and rect.collidepoint(self._hover)
            if active:
                bg = C_TAB_ACTIVE
            elif hovered:
                bg = C_BTN_GEAR_HOVER
            else:
                bg = C_BTN_GEAR
            pygame.draw.rect(surface, bg, rect, border_radius=4)
            if active:
                pygame.draw.rect(surface, C_ACCENT, rect, 1, border_radius=4)
            lbl = self._text(small, label, C_TITLE if (active or hovered) else C_DIM)
            surface.set_clip(rect.inflate(-4, 0))
            surface.blit(lbl, lbl.get_rect(center=rect.center))
            surface.set_clip(prev_clip)

    # ── Content layout (content space, cached per tab and width) ───────────────

    def _render_list(self) -> _RenderList:
        """Return the cached render list for the active tab at the current width."""
        tab = self.active_tab
        key = (tab, self._size[0])
        render = self._render_cache.get(key)
        if render is None:
            render = self._build_render_list(tab)
            self._render_cache[key] = render
        return render

    def _build_render_list(self, tab: int) -> _RenderList:
        self._ensure_fonts()
        ops: list[_Op] = []
        y = _CONTENT_PAD_TOP
        cards = self._header_by_tab[tab]
        if cards:
            y = self._build_feature_cards(ops, _PAD, y, cards) + 10

        left, right = self._left_by_tab[tab], self._right_by_tab[tab]
        columns = [left, right] if self._columns == 2 else [left + right]
        bottom = y
        for x, entries in zip(self._col_xs, columns):
            bottom = max(bottom, self._build_column(ops, x, y, entries))
        for x in self._col_xs[1:]:
            div_x = x - _COL_GAP // 2
            ops.append(_LineOp(div_x, y - 4, div_x, bottom, C_DIVIDER))
        return _RenderList(ops, bottom + _CONTENT_PAD_BOTTOM)

    def _add_lines(
        self,
        ops: list[_Op],
        font_key: str,
        text: str,
        color: tuple,
        x: int,
        y: int,
        max_w: int,
        gap: int = 0,
    ) -> int:
        """Wrap ``text`` to ``max_w`` and append one text op per line. Returns the new y."""
        font = self._font(font_key)
        max_w = max(1, max_w)
        for line in wrap_text(text, max_w, lambda s: font.size(s)[0]):
            ops.append(_TextOp(x, y, line, font_key, color, max_w))
            y += font.get_linesize() + gap
        return y

    def _build_feature_cards(self, ops: list[_Op], x: int, y: int, cards: list) -> int:
        """Lay out feature cards spanning the full content width; each card grows to fit."""
        title_font = self._font("title")
        full_w = max(0, self._size[0] - 2 * _PAD)
        n = len(cards)
        card_w = max(1, (full_w - _FEATURE_CARD_GAP * (n - 1)) // n)

        y = self._add_lines(ops, "small", "HOW IT WORKS", C_SECTION, x, y, full_w) + 2
        ops.append(_LineOp(x, y, x + full_w, y, C_DIVIDER))
        y += _SECTION_UNDER_H + 2

        card_ops: list[list[_Op]] = []
        card_bottom = y
        for i, entry in enumerate(cards):
            _, title, subtitle, desc, color, icon_key = entry
            cx = x + i * (card_w + _FEATURE_CARD_GAP)
            tx = cx + _FEATURE_CARD_PAD
            inner_right = cx + card_w - _FEATURE_CARD_PAD
            body: list[_Op] = []
            ty = y + _FEATURE_CARD_PAD
            ix = tx
            if icon_key:
                body.append(_IconOp(ix, ty + title_font.get_height() // 2, icon_key))
                ix += _ICON_SZ + _ICON_GAP
            ty = self._add_lines(body, "title", title, color, ix, ty, inner_right - ix) + 3
            ty = self._add_lines(body, "small", subtitle, C_TEXT, tx, ty, inner_right - tx) + 4
            ty = self._add_lines(body, "small", desc, C_DIM, tx, ty, inner_right - tx, gap=1)
            card_ops.append(body)
            card_bottom = max(card_bottom, ty + _FEATURE_CARD_PAD)

        card_h = card_bottom - y
        for i, body in enumerate(card_ops):
            cx = x + i * (card_w + _FEATURE_CARD_GAP)
            ops.append(_CardOp((cx, y, card_w, card_h)))
            ops.extend(body)
        return card_bottom

    def _build_column(self, ops: list[_Op], x: int, y: int, entries: list) -> int:
        """Lay out one column of sections/items starting at ``y``. Returns the end y."""
        body = self._font("body")
        right = x + self._col_w
        first_section = True
        for entry in entries:
            if entry[0] == "section":
                if not first_section:
                    y += _SECTION_PRE_GAP
                first_section = False
                icon_key = entry[2] if len(entry) > 2 else None
                ix = x
                if icon_key:
                    ops.append(_IconOp(ix, y + body.get_height() // 2, icon_key))
                    ix += _ICON_SZ + _ICON_GAP
                y = self._add_lines(ops, "body", entry[1], C_SECTION, ix, y, right - ix) + 3
                ops.append(_LineOp(x, y, right, y, C_DIVIDER))
                y += _SECTION_UNDER_H
            else:
                _, name, desc, color = entry[:4]
                icon_key = entry[4] if len(entry) > 4 else None
                ix = x + 2
                if icon_key:
                    ops.append(_IconOp(ix, y + body.get_height() // 2, icon_key))
                    ix += _ICON_SZ + _ICON_GAP
                y = self._add_lines(ops, "body", f"• {name}", color, ix, y, right - ix)
                desc_x = x + _DESC_INDENT
                y = self._add_lines(ops, "small", desc, C_DIM, desc_x, y, right - desc_x)
                y += _ITEM_GAP
        return y

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _ensure_fonts(self) -> None:
        if self._font_body is None:
            self._font_body = pygame.font.SysFont("monospace", 16)
            self._font_title = pygame.font.SysFont("monospace", 20)
            self._font_small = pygame.font.SysFont("monospace", 13)

    def _font(self, key: str) -> pygame.font.Font:
        self._ensure_fonts()
        font = {"body": self._font_body, "title": self._font_title, "small": self._font_small}[key]
        assert font is not None
        return font

    def _tab_bar(self) -> TabBar:
        if self._tabs is None:
            self._ensure_fonts()
            small = self._font_small
            assert small is not None
            self._tabs = TabBar(_TAB_LABELS, lambda s: small.size(s)[0], height=_TAB_H)
        return self._tabs

    def _text(self, font: pygame.font.Font, text: str, color: tuple) -> pygame.Surface:
        """Render ``text`` once per (font, text, colour) and reuse the surface."""
        key = (id(font), text, color)
        surf = self._text_cache.get(key)
        if surf is None:
            surf = font.render(text, True, color)
            self._text_cache[key] = surf
        return surf
