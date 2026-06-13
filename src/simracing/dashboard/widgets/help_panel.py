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
    ("item",  "Orange border",     "wheelspin · wheel spins faster than expected · TCS may intervene",            C_SPIN, "tire-wheel"),
    ("item",  "Red border",        "lockup: wheel locking under heavy braking",                                  C_LOCK, "tire-wheel"),
    ("item",  "Side bar",          "suspension travel · blue=light · green=nominal · red=max",                   C_DIM, "suspension"),

    ("section", "STATUS STRIP (below RPM bar)", "panel-cluster"),
    ("item",  "TCS / ASM",         "traction control (orange) or stability (yellow) intervened",                C_SPIN, "tcs"),
    ("item",  "REV",                "rev limiter active — engine at max RPM",                                    C_RED),
    ("item",  "HB",                 "handbrake applied",                                                          C_RED, "parking"),
    ("item",  "LIGHT",             "headlights on — useful in races with night segments",                       C_LIGHT, "headlight"),
    ("item",  "OIL!",              "oil temperature critical — above 130°C",                                   C_RED, "oil"),
    ("item",  "WATER!",           "water temperature critical — above 105°C",                                  C_RED, "coolant"),

    ("section", "INFO PANEL (right)", "flags"),
    ("item",  "POS",               "race position · shown when available",                                      C_TEXT, "race-pos"),
    ("item",  "LAP / BEST / LAST", "current lap · best lap · last completed lap",                               C_TEXT, "stopwatch"),
    ("item",  "FUEL / FUEL·LAP",   "litres in tank · consumption per lap after 1st lap change",                 C_TEXT, "fuel"),
    ("item",  "LAPS LEFT",         "estimated laps remaining with current fuel",                                 C_TEXT, "fuel"),
    ("item",  "WATER · OIL · BOOST", "fluids and turbo · orange = above safe limit",                            C_ORANGE, "turbo"),
]
# fmt: on

_TAB_LABELS = ["DASHBOARD", "APP GUIDE"]

# fmt: off
_APP_LEFT = [
    ("section", "LAP RECORDING", "stopwatch"),
    ("item",  "Auto-save",        "laps saved automatically — no manual action required",         C_TEXT, "stopwatch"),
    ("item",  "On lap change",    "previous lap saved when current_lap counter increments",       C_TEXT, "stopwatch"),
    ("item",  "On session end",   "current buffer saved as lap_NN_incomplete.parquet",            C_TEXT, "stopwatch"),
    ("item",  "Location",         "~/simracing_laps/<YYYY-MM-DDTHHMMSS>/lap_NN.parquet",         C_TEXT),
    ("item",  "Format",           "Apache Parquet · Snappy · one row per frame (~60 Hz)",        C_TEXT),

    ("section", "RECORDED PER FRAME", "panel-cluster"),
    ("item",  "Driving inputs",   "speed · rpm · gear · throttle · brake · clutch · handbrake",  C_TEXT, "car-pedals"),
    ("item",  "Position",         "pos_x/y/z · vel_x/y/z — world coordinates (metres)",          C_TEXT, "speedometer"),
    ("item",  "G-force & slip",   "g_lat · g_lon · slip_angle_deg (EMA-smoothed, computed)",     C_TEXT, "g-force"),
    ("item",  "Tires",            "surface temp FL/FR/RL/RR · suspension travel",                C_TEXT, "tire-wheel"),
    ("item",  "Engine & fluids",  "turbo_boost · water_temp · oil_temp · fuel_level",             C_TEXT, "fuel"),
]

_APP_RIGHT = [
    ("section", "LAP SUMMARY (filled at lap end)", "stopwatch"),
    ("item",  "fuel_at_start",    "fuel level when the lap began (litres)",                       C_TEXT, "fuel"),
    ("item",  "fuel_at_end",      "fuel level when the lap ended (litres)",                       C_TEXT, "fuel"),
    ("item",  "fuel_used",        "litres consumed this lap (start − end)",                       C_TEXT, "fuel"),
    ("item",  "fuel_avg",         "session average litres/lap at the moment lap ended",           C_TEXT, "fuel"),
    ("item",  "lap_finish_ms",    "official lap time from GT7 (milliseconds)",                    C_TEXT,   "stopwatch"),
    ("item",  "Pedal counters",   "full_throttle · full_brake · coasting ticks",                  C_TEXT,   "car-pedals"),

    ("section", "HEADER CONTROLS", "panel-cluster"),
    ("item",  "● REC",            "red = recording · grey = paused · same session mid-race", C_RED, "rec-button"),

    ("section", "SETTINGS  (~/simracing.conf)", "panel-cluster"),
    ("item",  "device_ip",        "PS5 / PC IP address",                                          C_TEXT),
    ("item",  "rev_flash",        "true / false — full-screen flash at rev limiter",               C_TEXT,   "rpm"),
    ("item",  "fuel_estimation",  "\"last\" or \"average\" — how FUEL/LAP is calculated",          C_TEXT,   "fuel"),
]
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


class HelpPanel:
    def __init__(self, win_w: int, win_h: int) -> None:
        self.active = False
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
        tab_w, tab_h = 114, 26
        tab_y = _CARD_Y + (_TITLE_H - tab_h) // 2
        cx = _CARD_X + _CARD_W // 2
        self._tab_rects = [
            pygame.Rect(cx - tab_w - 3, tab_y, tab_w, tab_h),
            pygame.Rect(cx + 3,         tab_y, tab_w, tab_h),
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

        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill(C_OVERLAY)
        surface.blit(overlay, (0, 0))

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
        title = font_md.render("RACE ENGINEER  —  UI GUIDE", True, C_TITLE)
        surface.blit(title, title.get_rect(midleft=(_CARD_X + _PAD, _CARD_Y + _TITLE_H // 2)))

        mouse = pygame.mouse.get_pos()
        for i, (label, tab_rect) in enumerate(zip(_TAB_LABELS, self._tab_rects)):
            active = (i == self._active_tab)
            bg = (45, 72, 140) if active else (38, 38, 58)
            pygame.draw.rect(surface, bg, tab_rect, border_radius=4)
            if active:
                pygame.draw.rect(surface, C_ACCENT, tab_rect, 1, border_radius=4)
            tc = C_TITLE if active else C_DIM
            t = font_sm.render(label, True, tc)
            surface.blit(t, t.get_rect(center=tab_rect.center))

        close_bg = (70, 40, 40) if self._close_btn.collidepoint(mouse) else (42, 42, 58)
        pygame.draw.rect(surface, close_bg, self._close_btn, border_radius=4)
        if icon_close:
            surface.blit(icon_close, icon_close.get_rect(center=self._close_btn.center))
        else:
            x_surf = font_sm.render("X", True, C_TITLE)
            surface.blit(x_surf, x_surf.get_rect(center=self._close_btn.center))

        left_entries  = _LEFT      if self._active_tab == 0 else _APP_LEFT
        right_entries = _RIGHT     if self._active_tab == 0 else _APP_RIGHT
        content_y = _CARD_Y + _TITLE_H + 12
        self._draw_column(surface, font_sm, self._col_left_x, content_y, left_entries, icons)

        div_x = self._col_right_x - _COL_GAP // 2
        pygame.draw.line(
            surface, C_DIVIDER,
            (div_x, _CARD_Y + _TITLE_H + 8),
            (div_x, _CARD_Y + _CARD_H - 28), 1,
        )
        self._draw_column(surface, font_sm, self._col_right_x, content_y, right_entries, icons)

        footer = font_sm.render(_FOOTER, True, C_DIM)
        surface.blit(footer, footer.get_rect(
            center=(_CARD_X + _CARD_W // 2, _CARD_Y + _CARD_H - 14)))

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
