"""Help overlay: describes every dashboard element."""

import pygame

C_OVERLAY = (0, 0, 0, 185)
C_CARD = (22, 22, 30)
C_TITLE_BAR = (28, 28, 42)
C_BORDER = (60, 60, 80)
C_DIVIDER = (42, 42, 55)
C_TITLE = (230, 230, 230)
C_SECTION = (80, 140, 220)
C_TEXT = (200, 200, 210)
C_DIM = (95, 95, 108)
C_ACCENT = (80, 140, 220)
C_ORANGE = (255, 165, 0)
C_SPIN = (255, 140, 0)
C_LOCK = (220, 40, 40)
C_RED = (210, 55, 55)
C_GREEN = (60, 200, 80)
C_YELLOW = (240, 210, 0)
C_LIGHT = (190, 200, 255)

# fmt: off
_LEFT = [
    ("section", "GAUGES", "panel-cluster"),
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
    ("item",  "Tile color",        "blue=cold (<60°C) · green=ideal (60-130°C) · red=hot (>130°C)",             C_TEXT, "tire-wheel"),
    ("item",  "Orange border",     "wheelspin · wheel spins faster than expected · TCS may intervene",           C_SPIN, "tire-wheel"),
    ("item",  "Red border",        "lockup: wheel locking under heavy braking",                                  C_LOCK, "tire-wheel"),
    ("item",  "Side bar",          "suspension travel · blue=light · green=nominal · red=max",                   C_DIM, "suspension"),

    ("section", "STATUS STRIP (below RPM bar)", "panel-cluster"),
    ("item",  "TCS / ASM",         "traction control (orange) or stability (yellow) intervened",                C_SPIN, "tcs"),
    ("item",  "REV",               "rev limiter active — engine at max RPM",                                    C_RED),
    ("item",  "HB",                "handbrake applied",                                                         C_RED, "parking"),
    ("item",  "LIGHT",             "headlights on — useful in races with night segments",                       C_LIGHT, "headlight"),
    ("item",  "OIL!",              "oil temperature critical — above 130°C",                                    C_RED, "oil"),
    ("item",  "WATER!",            "water temperature critical — above 105°C",                                  C_RED, "coolant"),

    ("section", "INFO PANEL (right)", "flags"),
    ("item",  "POS",               "race position · shown when available",                                      C_TEXT, "race-pos"),
    ("item",  "LAP / BEST / LAST", "current lap · best lap · last completed lap",                               C_TEXT, "stopwatch"),
    ("item",  "FUEL / FUEL·LAP",   "litres in tank · consumption per lap after 1st lap change",                 C_TEXT, "fuel"),
    ("item",  "LAPS LEFT",         "estimated laps remaining with current fuel",                                 C_TEXT, "fuel"),
    ("item",  "WATER · OIL · BOOST", "fluids and turbo · orange = above safe limit",                            C_ORANGE, "turbo"),
]
# fmt: on

_TAB_LABELS = ["APP GUIDE", "DASHBOARD", "VOICE ALERTS", "SETTINGS"]

# fmt: off
_VOICE_LEFT = [
    ("section", "LAP & PACE", "stopwatch"),
    ("item", "Lap completed",
     "fires on lap change when no new best lap was set",
     C_TEXT, "stopwatch"),
    ("item", "Best lap",
     "new personal best — fires instead of 'Lap completed'",
     C_GREEN, "stopwatch"),
    ("item", "Final lap",
     "fires entering the last lap of a timed/lapped race",
     C_ORANGE, "flags"),
    ("item", "Lap delta",
     ">3s off best — fires once after the halfway point of the lap",
     C_ORANGE, "stopwatch"),

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
     "less than 1 lap of fuel · highest priority fuel alert",
     C_RED, "fuel"),

    ("section", "STRATEGY", "flags"),
    ("item", "Strategy: pit window",
     "in pit window, can't finish · 'Box box box + reason'",
     C_ACCENT, "fuel"),
    ("item", "Strategy: tyres",
     "2–5 laps to pit · tyres degrading · plan ahead",
     C_ORANGE, "tire-wheel"),
]

_VOICE_RIGHT = [
    ("section", "ENGINE", "coolant"),
    ("item", "Water temp",
     "coolant >105°C · repeats every 20s while above threshold",
     C_RED, "coolant"),
    ("item", "Oil temp",
     "oil >130°C · repeats every 20s while above threshold",
     C_RED, "oil"),

    ("section", "TYRES", "tire-wheel"),
    ("item", "Tyre temp",
     "any surface >100°C · hot corners named · 30s cooldown",
     C_ORANGE, "tire-wheel"),
    ("item", "Tyre wear",
     "any inner zone >110°C · high inner temp signals wear · 30s",
     C_ORANGE, "tire-wheel"),
    ("item", "Tyre wear %",
     "stint avg wear hits each 10% block · fires once per bucket",
     C_ORANGE, "tire-wheel"),
    ("item", "Pressure low",
     "any tyre <160 kPa · grip loss / puncture risk · 30s",
     C_RED, "tire-wheel"),
    ("item", "Pressure high",
     "any tyre >250 kPa · blowout risk in heat · 30s cooldown",
     C_RED, "tire-wheel"),

    ("section", "PLANNED PIT", "race-pos"),
    ("item", "Approaching",
     "'Pit in N lap(s)' · fires 2 laps before planned stop",
     C_ACCENT, "fuel"),
    ("item", "Box now",
     "'Box this lap. On strategy' · on the planned stop lap",
     C_GREEN, "fuel"),
    ("item", "Tyre warning",
     "tyres won't reach planned stop · fires when life < plan lap",
     C_ORANGE, "tire-wheel"),
    ("item", "Missed / rescheduled",
     "missed window · reschedules to new lap if fuel allows",
     C_RED, "fuel"),

    ("section", "HOW TO READ", "panel-cluster"),
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
     "Connect the PS5 to the same network. The app displays speed · RPM · gear · tyres · G-forces · fuel"
     " and electronics interventions on a second screen.",
     C_ACCENT, "speedometer"),
    ("card",
     "2 · VOICE ALERTS",
     "Pit-wall engineer while you race",
     "Automatic spoken alerts: fuel status · tyre temps · lap pace · pit windows and planned stop reminders."
     " Available in English or Portuguese.",
     C_GREEN, "flags"),
    ("card",
     "3 · LAP ANALYSIS",
     "Post-session interactive browser viewer",
     "After the session ends: click ANALYSIS in the header · select session.parquet (all laps merged into one file)"
     " · the browser opens at localhost:8050.",
     C_ORANGE, "stopwatch"),
]

_APP_LEFT = [
    ("section", "LAP RECORDING", "stopwatch"),
    ("item",  "Auto-save",            "laps saved automatically — no manual action required",             C_TEXT, "stopwatch"),
    ("item",  "On lap change",        "previous lap saved when the current_lap counter increments",       C_TEXT, "stopwatch"),
    ("item",  "On session end",       "current buffer saved as lap_NN_incomplete.parquet",                C_TEXT, "stopwatch"),
    ("item",  "Free Session Restart", "restarting in free session keeps same folder — laps continue",    C_TEXT, "stopwatch"),
    ("item",  "Location",             "~/simracing_laps/<YYYY-MM-DDTHHMMSS>/lap_NN.parquet",             C_TEXT),
    ("item",  "session.parquet",      "all laps merged — created at session end · open this for analysis", C_ACCENT),
    ("item",  "Format",               "Apache Parquet · Snappy · one row per frame (~60 Hz)",            C_TEXT),

    ("section", "RECORDED PER FRAME", "panel-cluster"),
    ("item",  "Driving inputs",   "speed · rpm · gear · throttle · brake · clutch · handbrake",  C_TEXT, "car-pedals"),
    ("item",  "Position",         "pos_x/y/z · vel_x/y/z — world coordinates (metres)",          C_TEXT, "speedometer"),
    ("item",  "G-force & slip",   "g_lat · g_lon · slip_angle_deg (EMA-smoothed, computed)",     C_TEXT, "g-force"),
    ("item",  "Tires",            "surface temp FL/FR/RL/RR · suspension travel",                C_TEXT, "tire-wheel"),
    ("item",  "Engine & fluids",  "turbo_boost · water_temp · oil_temp · fuel_level",            C_TEXT, "fuel"),
]

_APP_RIGHT = [
    ("section", "LAP SUMMARY (filled at lap end)", "stopwatch"),
    ("item",  "fuel_at_start",    "fuel level when the lap began (litres)",                       C_TEXT, "fuel"),
    ("item",  "fuel_at_end",      "fuel level when the lap ended (litres)",                       C_TEXT, "fuel"),
    ("item",  "fuel_used",        "litres consumed this lap (start − end)",                       C_TEXT, "fuel"),
    ("item",  "fuel_avg",         "session average litres/lap at the moment lap ended",           C_TEXT, "fuel"),
    ("item",  "lap_finish_ms",    "official lap time from GT7 (milliseconds)",                    C_TEXT, "stopwatch"),
    ("item",  "Pedal counters",   "full_throttle · full_brake · coasting ticks",                  C_TEXT, "car-pedals"),

    ("section", "HEADER CONTROLS", "panel-cluster"),
    ("item",  "ANALYSIS",         "opens file picker → select session.parquet → browser at :8050", C_ACCENT, "stopwatch"),
    ("item",  "REC",              "red = recording · grey = paused · same session mid-race",      C_RED, "rec-button"),
    ("item",  "LIVE  (green)",    "connected to GT7 telemetry and receiving data",                C_GREEN),
    ("item",  "WAIT  (yellow)",   "connecting or connected but awaiting first packet",            C_YELLOW),
    ("item",  "ERR   (orange)",   "connection error — check device IP and network",               C_ORANGE),
    ("item",  "DISC  (grey)",     "disconnected — device IP is set but not active",               C_DIM),
    ("item",  "OFF   (red)",      "no device IP configured — open SETTINGS tab to set one",      C_RED),
]

_SETTINGS_LEFT = [
    ("section", "FILE  (~/simracing/simracing.conf)", "panel-cluster"),
    ("item",  "device_ip",        "PS5 / PC IP address — required to receive telemetry",          C_TEXT),
    ("item",  "record_on_start",  "true / false — start lap recording automatically on session start", C_TEXT, "rec"),
    ("item",  "fuel_estimation",  "\"last\" or \"average\" — how FUEL/LAP is calculated",          C_TEXT, "fuel"),
]

_SETTINGS_RIGHT: list = []
# fmt: on

_FOOTER = "Press ESC or click anywhere to close"

_CARD_X, _CARD_Y = 44, 58       # card sits just below the header
_CARD_W, _CARD_H = 1192, 730    # bottom ≈ 788, leaves margin on 800px screen
_PAD = 24
_COL_GAP = 28
_TITLE_H = 44
_ITEM_NAME_H = 18   # advance per name line (14pt ≈ 17-18px)
_ITEM_DESC_H = 18   # advance per description line
_ITEM_GAP = 1       # gap between items
_SECTION_PRE_GAP = 6
_SECTION_UNDER_H = 5
_FEATURE_CARD_H = 90  # height of each HOW IT WORKS card
_FEATURE_CARD_GAP = 16


class HelpPanel:
    def __init__(self) -> None:
        self.active = False
        self._overlay: pygame.Surface | None = None  # lazy-init on first draw
        self._surf_title: pygame.Surface | None = None
        self._surf_footer: pygame.Surface | None = None
        self._surf_how_it_works: pygame.Surface | None = None
        self._surf_tab_active: list[pygame.Surface | None] = [None] * len(_TAB_LABELS)
        self._surf_tab_inactive: list[pygame.Surface | None] = [None] * len(_TAB_LABELS)
        self._card = pygame.Rect(_CARD_X, _CARD_Y, _CARD_W, _CARD_H)
        col_w = (_CARD_W - 2 * _PAD - _COL_GAP) // 2
        self._col_w = col_w
        self._col_left_x = _CARD_X + _PAD
        self._col_right_x = self._col_left_x + col_w + _COL_GAP
        close_sz = 22
        self._close_btn = pygame.Rect(
            _CARD_X + _CARD_W - close_sz - 10,
            _CARD_Y + (_TITLE_H - close_sz) // 2,
            close_sz, close_sz,
        )
        tab_w, tab_h, tab_gap = 110, 26, 3
        tab_y = _CARD_Y + (_TITLE_H - tab_h) // 2
        cx = _CARD_X + _CARD_W // 2
        n_tabs = len(_TAB_LABELS)
        total_tab_w = n_tabs * tab_w + (n_tabs - 1) * tab_gap
        tab_start_x = cx - total_tab_w // 2
        self._tab_rects = [
            pygame.Rect(tab_start_x + i * (tab_w + tab_gap), tab_y, tab_w, tab_h)
            for i in range(n_tabs)
        ]
        self._active_tab = 0

    def open(self) -> None:
        self.active = True

    def handle_event(self, event: pygame.event.Event) -> str | None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.active = False
            return "closed"
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, tab_rect in enumerate(self._tab_rects):
                if tab_rect.collidepoint(event.pos):
                    self._active_tab = i
                    return None
            self.active = False
            return "closed"
        return None

    def draw(
        self,
        surface: pygame.Surface,
        font_md: pygame.font.Font,
        font_sm: pygame.font.Font,
        icon_close: pygame.Surface | None = None,
        icons: dict | None = None,
    ) -> None:
        if not self.active:
            return

        if self._overlay is None:
            self._overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            self._overlay.fill(C_OVERLAY)
        surface.blit(self._overlay, (0, 0))

        pygame.draw.rect(surface, C_CARD, self._card, border_radius=10)
        pygame.draw.rect(surface, C_BORDER, self._card, 1, border_radius=10)

        title_bar = pygame.Rect(_CARD_X, _CARD_Y, _CARD_W, _TITLE_H)
        pygame.draw.rect(surface, C_TITLE_BAR, title_bar,
                         border_top_left_radius=10, border_top_right_radius=10)
        pygame.draw.line(
            surface, C_BORDER,
            (_CARD_X, _CARD_Y + _TITLE_H),
            (_CARD_X + _CARD_W, _CARD_Y + _TITLE_H), 1,
        )
        _t = self._surf_title
        if _t is None:
            _t = font_md.render("RACE ENGINEER  —  UI GUIDE", True, C_TITLE)
            self._surf_title = _t
        surface.blit(_t, _t.get_rect(midleft=(_CARD_X + _PAD, _CARD_Y + _TITLE_H // 2)))

        mouse = pygame.mouse.get_pos()
        for i, (label, tab_rect) in enumerate(zip(_TAB_LABELS, self._tab_rects)):
            active = (i == self._active_tab)
            bg = (45, 72, 140) if active else (38, 38, 58)
            pygame.draw.rect(surface, bg, tab_rect, border_radius=4)
            if active:
                pygame.draw.rect(surface, C_ACCENT, tab_rect, 1, border_radius=4)
                _tab = self._surf_tab_active[i]
                if _tab is None:
                    _tab = font_sm.render(label, True, C_TITLE)
                    self._surf_tab_active[i] = _tab
            else:
                _tab = self._surf_tab_inactive[i]
                if _tab is None:
                    _tab = font_sm.render(label, True, C_DIM)
                    self._surf_tab_inactive[i] = _tab
            surface.blit(_tab, _tab.get_rect(center=tab_rect.center))

        close_bg = (70, 40, 40) if self._close_btn.collidepoint(mouse) else (42, 42, 58)
        pygame.draw.rect(surface, close_bg, self._close_btn, border_radius=4)
        if icon_close:
            surface.blit(icon_close, icon_close.get_rect(center=self._close_btn.center))
        else:
            x_surf = font_sm.render("X", True, C_TITLE)
            surface.blit(x_surf, x_surf.get_rect(center=self._close_btn.center))

        _header_by_tab = [_APP_HEADER, None,   None,        None]
        _left_by_tab   = [_APP_LEFT,  _LEFT,   _VOICE_LEFT, _SETTINGS_LEFT]
        _right_by_tab  = [_APP_RIGHT, _RIGHT,  _VOICE_RIGHT, _SETTINGS_RIGHT]

        left_entries  = _left_by_tab[self._active_tab]
        right_entries = _right_by_tab[self._active_tab]
        header_cards  = _header_by_tab[self._active_tab]

        content_y = _CARD_Y + _TITLE_H + 12

        if header_cards:
            content_y = self._draw_feature_cards(
                surface, font_md, font_sm, self._col_left_x, content_y, header_cards, icons,
            )
            content_y += 10

        self._draw_column(surface, font_sm, self._col_left_x, content_y, left_entries, icons)

        div_x = self._col_right_x - _COL_GAP // 2
        pygame.draw.line(
            surface, C_DIVIDER,
            (div_x, content_y - 4),
            (div_x, _CARD_Y + _CARD_H - 28), 1,
        )
        self._draw_column(surface, font_sm, self._col_right_x, content_y, right_entries, icons)

        _ftr = self._surf_footer
        if _ftr is None:
            _ftr = font_sm.render(_FOOTER, True, C_DIM)
            self._surf_footer = _ftr
        surface.blit(_ftr, _ftr.get_rect(
            center=(_CARD_X + _CARD_W // 2, _CARD_Y + _CARD_H - 14)))

    def _draw_feature_cards(
        self,
        surface: pygame.Surface,
        font_md: pygame.font.Font,
        font_sm: pygame.font.Font,
        x: int,
        y: int,
        cards: list,
        icons: dict | None = None,
    ) -> int:
        """Renders feature cards spanning the full content width. Returns new y after the section."""
        full_w = _CARD_W - 2 * _PAD
        n = len(cards)
        card_w = (full_w - _FEATURE_CARD_GAP * (n - 1)) // n

        _hiw = self._surf_how_it_works
        if _hiw is None:
            _hiw = font_sm.render("HOW IT WORKS", True, C_SECTION)
            self._surf_how_it_works = _hiw
        surface.blit(_hiw, (x, y))
        y += _hiw.get_height() + 4
        pygame.draw.line(surface, C_DIVIDER, (x, y), (x + full_w, y), 1)
        y += _SECTION_UNDER_H + 2

        _ICON_SZ = 14
        _ICON_GAP = 5
        _PAD_CARD = 10

        for i, entry in enumerate(cards):
            _, title, subtitle, desc, color, icon_key = entry
            cx = x + i * (card_w + _FEATURE_CARD_GAP)
            card_rect = pygame.Rect(cx, y, card_w, _FEATURE_CARD_H)
            pygame.draw.rect(surface, (30, 30, 45), card_rect, border_radius=6)
            pygame.draw.rect(surface, C_DIVIDER, card_rect, 1, border_radius=6)

            ty = y + _PAD_CARD
            tx = cx + _PAD_CARD

            icon = icons.get(icon_key) if (icons and icon_key) else None
            ix = tx
            if icon:
                surface.blit(icon, icon.get_rect(midleft=(ix, ty + _ICON_SZ // 2 + 1)))
                ix += _ICON_SZ + _ICON_GAP
            title_surf = font_md.render(title, True, color)
            surface.blit(title_surf, (ix, ty))
            ty += title_surf.get_height() + 3

            sub_surf = font_sm.render(subtitle, True, C_TEXT)
            surface.blit(sub_surf, (tx, ty))
            ty += sub_surf.get_height() + 5

            desc_max_w = card_w - 2 * _PAD_CARD
            words = desc.split()
            line: str = ""
            lines: list[str] = []
            for word in words:
                test = (line + " " + word).strip()
                if font_sm.size(test)[0] <= desc_max_w:
                    line = test
                else:
                    if line:
                        lines.append(line)
                    line = word
            if line:
                lines.append(line)
            for dl in lines[:2]:
                ds = font_sm.render(dl, True, C_DIM)
                surface.blit(ds, (tx, ty))
                ty += ds.get_height() + 1

        return y + _FEATURE_CARD_H

    def _draw_column(
        self,
        surface: pygame.Surface,
        font: pygame.font.Font,
        x: int,
        start_y: int,
        entries: list,
        icons: dict | None = None,
    ) -> None:
        _ICON_SZ = 14
        _ICON_GAP = 5
        y = start_y
        first_section = True

        for entry in entries:
            kind = entry[0]

            if kind == "section":
                if not first_section:
                    y += _SECTION_PRE_GAP
                first_section = False
                icon_key = entry[2] if len(entry) > 2 else None
                icon = icons.get(icon_key) if (icons and icon_key) else None
                ix = x
                if icon:
                    surface.blit(icon, icon.get_rect(midleft=(ix, y + _ICON_SZ // 2 + 1)))
                    ix += _ICON_SZ + _ICON_GAP
                lbl = font.render(entry[1], True, C_SECTION)
                surface.blit(lbl, (ix, y))
                y += lbl.get_height() + 3
                pygame.draw.line(
                    surface, C_DIVIDER, (x, y), (x + self._col_w, y), 1
                )
                y += _SECTION_UNDER_H

            else:
                _, name, desc, color = entry[:4]
                icon_key = entry[4] if len(entry) > 4 else None
                icon = icons.get(icon_key) if (icons and icon_key) else None
                ix = x + 2
                if icon:
                    surface.blit(icon, icon.get_rect(midleft=(ix, y + _ICON_SZ // 2 + 1)))
                    ix += _ICON_SZ + _ICON_GAP
                name_surf = font.render(f"• {name}", True, color)
                surface.blit(name_surf, (ix, y))
                y += _ITEM_NAME_H
                desc_surf = font.render(desc, True, C_DIM)
                surface.blit(desc_surf, (x + 12, y))
                y += _ITEM_DESC_H + _ITEM_GAP
