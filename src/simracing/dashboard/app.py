"""Main pygame dashboard application."""

import asyncio
import logging
import math
from collections.abc import Callable
from pathlib import Path

import pygame

from ..config import AppConfig
from ..telemetry.models import TelemetryData
from .widgets.bar import draw_bar
from .widgets.g_meter import draw_g_meter
from .widgets.gauge import draw_gauge
from .widgets.help_panel import HelpPanel
from .widgets.settings_panel import SettingsPanel
from .widgets.slip_angle import draw_slip_angle
from .widgets.tire_widget import draw_tires

log = logging.getLogger(__name__)

# ── Layout constants ──────────────────────────────────────────────────────────
WIN_W, WIN_H = 1280, 720
FPS = 60

HEADER_H = 52
RPM_BAR_Y = HEADER_H + 10

C_BG = (14, 14, 18)
C_HEADER = (20, 20, 26)
C_TEXT = (230, 230, 230)
C_DIM = (100, 100, 110)
C_ACCENT = (80, 140, 220)
C_GREEN = (60, 200, 80)
C_ORANGE = (255, 165, 0)
C_RED = (220, 60, 60)
C_SEPARATOR = (45, 45, 55)
C_BTN_GEAR = (38, 38, 50)
C_BTN_GEAR_HOVER = (55, 55, 70)

ERROR_BAR_H = 22

_IMG_DIR = Path(__file__).parent.parent / "img"


def _fmt_lap(ms: int) -> str:
    if ms <= 0:
        return "--:--.---"
    m = ms // 60000
    s = (ms % 60000) // 1000
    ms_r = ms % 1000
    return f"{m}:{s:02d}.{ms_r:03d}"


class DashboardApp:
    def __init__(
        self,
        telemetry_queue: asyncio.Queue,
        config: AppConfig,
        connect_fn: Callable[[], None] | None = None,
        disconnect_fn: Callable[[], None] | None = None,
        get_status_fn: Callable[[], str] | None = None,
        get_error_fn: Callable[[], str] | None = None,
    ) -> None:
        self._queue = telemetry_queue
        self._config = config
        self._connect_fn = connect_fn
        self._disconnect_fn = disconnect_fn
        self._get_status_fn = get_status_fn or (lambda: "disconnected")
        self._get_error_fn = get_error_fn or (lambda: "")
        self._data = TelemetryData()
        self._running = False
        self._icon: pygame.Surface | None = None
        self._settings: SettingsPanel | None = None
        self._help: HelpPanel | None = None
        _btn_y = (HEADER_H - 28) // 2
        self._gear_btn = pygame.Rect(WIN_W - 44, _btn_y, 28, 28)
        self._help_btn = pygame.Rect(WIN_W - 44 - 8 - 28, _btn_y, 28, 28)
        self._conn_btn = pygame.Rect(WIN_W - 44 - 8 - 28 - 8 - 72, _btn_y, 72, 28)

        # Fuel rate tracking
        self._prev_lap: int = -1
        self._lap_fuel_start: float = 0.0
        self._fuel_per_lap: float = 0.0

        # State transition tracking (for debug logging)
        self._prev_in_race: bool = False
        self._prev_paused: bool = False
        self._prev_tcs: bool = False
        self._prev_asm: bool = False

        # G-meter (smoothed)
        self._prev_speed_ms: float = 0.0
        self._g_lat: float = 0.0
        self._g_lon: float = 0.0

        # Wheel slip (smoothed, 4 wheels)
        self._slip_ratios: list[float] = [0.0, 0.0, 0.0, 0.0]

        # Slip angle (smoothed)
        self._slip_angle: float = 0.0

    def _update_telemetry(self, d: TelemetryData, dt_ms: float) -> None:
        """Process a new telemetry frame: update derived metrics and store data."""
        # State transition logging
        if d.in_race != self._prev_in_race:
            log.info("Race state → %s", "IN RACE" if d.in_race else "OUT OF RACE")
            self._prev_in_race = d.in_race
        if d.paused != self._prev_paused:
            log.debug("Paused → %s", d.paused)
            self._prev_paused = d.paused
        if d.tcs_active and not self._prev_tcs:
            log.debug("TCS activated  spd=%.0f km/h  gear=%s", d.speed_kmh, d.gear_label)
        self._prev_tcs = d.tcs_active
        if d.asm_active and not self._prev_asm:
            log.debug("ASM activated  spd=%.0f km/h  gear=%s", d.speed_kmh, d.gear_label)
        self._prev_asm = d.asm_active

        # Fuel rate per lap
        if d.current_lap > 0:
            if self._prev_lap < 0:
                self._lap_fuel_start = d.fuel_level
                self._prev_lap = d.current_lap
            elif d.current_lap > self._prev_lap:
                delta = self._lap_fuel_start - d.fuel_level
                if 0 < delta < 200:
                    self._fuel_per_lap = delta
                log.info(
                    "Lap %d complete — time=%s  fuel_used=%.2fL  fuel_left=%.1fL",
                    self._prev_lap,
                    _fmt_lap(d.last_lap_ms),
                    delta if 0 < delta < 200 else 0.0,
                    d.fuel_level,
                )
                self._lap_fuel_start = d.fuel_level
                self._prev_lap = d.current_lap

        # G-forces
        dt_s = max(dt_ms / 1000.0, 1e-4)
        raw_lat = d.speed_ms * d.angular_velocity.y / 9.81
        raw_lon = max(-4.0, min(4.0, (d.speed_ms - self._prev_speed_ms) / dt_s / 9.81))
        self._g_lat = 0.25 * raw_lat + 0.75 * self._g_lat
        self._g_lon = 0.15 * raw_lon + 0.85 * self._g_lon
        self._prev_speed_ms = d.speed_ms

        # Wheel slip ratio per tire
        for i, t in enumerate(d.tires):
            if d.speed_ms > 3.0 and t.radius > 0:
                exp_rps = d.speed_ms / (2.0 * math.pi * t.radius)
                actual_rps = t.wheel_rpm / 60.0
                slip = (actual_rps - exp_rps) / max(exp_rps, 0.5)
                slip = max(-1.5, min(1.5, slip))
            else:
                slip = 0.0
            self._slip_ratios[i] = 0.3 * slip + 0.7 * self._slip_ratios[i]

        # Slip angle: angle between velocity vector and car heading
        if d.speed_ms > 5.0:
            # GT7 forward = -Z, so negate vel.z to get conventional atan2 angle
            vel_dir = math.atan2(d.velocity.x, -d.velocity.z)
            raw_slip = math.degrees(vel_dir - d.rotation.y)
            raw_slip = (raw_slip + 180.0) % 360.0 - 180.0  # normalize to ±180
            self._slip_angle = 0.2 * raw_slip + 0.8 * self._slip_angle
        else:
            self._slip_angle *= 0.9  # decay to zero at low speed

        self._data = d

    def _load_assets(self) -> None:
        icon_path = _IMG_DIR / "engineer.png"
        if icon_path.exists():
            raw = pygame.image.load(str(icon_path)).convert_alpha()
            raw = pygame.transform.smoothscale(raw, (32, 32))
            raw.fill(C_TEXT, special_flags=pygame.BLEND_RGB_MAX)
            self._icon = raw
        else:
            log.warning("Icon not found: %s", icon_path)

    def run(self) -> None:
        pygame.init()
        pygame.display.set_caption("Race Engineer")
        screen = pygame.display.set_mode((WIN_W, WIN_H))
        clock = pygame.time.Clock()

        self._load_assets()
        self._settings = SettingsPanel(WIN_W, WIN_H)
        self._help = HelpPanel(WIN_W, WIN_H)

        # Open settings automatically if no IP configured
        if not self._config.device_ip:
            self._settings.open(self._config.device_ip)

        font_xl = pygame.font.SysFont("monospace", 64, bold=True)
        font_lg = pygame.font.SysFont("monospace", 32, bold=True)
        font_md = pygame.font.SysFont("monospace", 20)
        font_sm = pygame.font.SysFont("monospace", 14)

        self._running = True
        while self._running:
            dt = clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                    continue

                # Help panel absorbs all events when open
                if self._help and self._help.active:
                    self._help.handle_event(event)
                    continue

                # Settings panel absorbs all events when open
                if self._settings and self._settings.active:
                    action = self._settings.handle_event(event)
                    if action == "saved":
                        self._config.device_ip = self._settings.ip_text
                        self._config.save()
                        log.info("Config saved: device_ip=%s", self._config.device_ip)
                        if self._config.device_ip and self._get_status_fn() != "connected":
                            if self._connect_fn:
                                self._connect_fn()
                    continue

                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self._running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self._conn_btn.collidepoint(event.pos):
                        if self._get_status_fn() == "connected":
                            if self._disconnect_fn:
                                self._disconnect_fn()
                        else:
                            if self._connect_fn:
                                self._connect_fn()
                    elif self._gear_btn.collidepoint(event.pos):
                        self._settings.open(self._config.device_ip)
                    elif self._help_btn.collidepoint(event.pos):
                        self._help.open()

            while not self._queue.empty():
                try:
                    self._update_telemetry(self._queue.get_nowait(), dt)
                except asyncio.QueueEmpty:
                    break

            screen.fill(C_BG)
            self._draw(screen, font_xl, font_lg, font_md, font_sm)
            if self._settings:
                self._settings.draw(screen, font_md, font_sm, dt)
            if self._help:
                self._help.draw(screen, font_md, font_sm)
            pygame.display.flip()

        pygame.quit()

    def _draw(self, screen, font_xl, font_lg, font_md, font_sm) -> None:
        d = self._data

        self._draw_header(screen, font_md, font_sm)

        draw_gauge(
            screen, cx=220, cy=380, radius=155,
            value=d.speed_kmh, min_val=0, max_val=d.speed_max_kmh if d.speed_max_kmh > 0 else 320,
            label="SPEED", unit="km/h",
            warn_pct=0.85, crit_pct=0.95,
            font_large=font_lg, font_small=font_sm,
        )

        draw_gauge(
            screen, cx=1060, cy=380, radius=155,
            value=d.rpm, min_val=0, max_val=d.rpm_max,
            label="ENGINE", unit="RPM",
            warn_pct=0.85, crit_pct=0.95,
            font_large=font_lg, font_small=font_sm,
        )

        gear_surf = font_xl.render(d.gear_label, True, C_TEXT)
        screen.blit(gear_surf, gear_surf.get_rect(center=(640, 155)))

        gear_lbl = font_sm.render("GEAR", True, C_DIM)
        screen.blit(gear_lbl, gear_lbl.get_rect(center=(640, 222)))

        if d.suggested_gear > 0 and d.suggested_gear != d.gear:
            sg = font_lg.render(f"→ {d.suggested_gear}", True, C_ORANGE)
            screen.blit(sg, sg.get_rect(center=(640, 252)))

        bar_y = 300
        bar_h = 200
        bar_w = 42
        bar_gap = 22
        bar_start = 640 - (3 * bar_w + 2 * bar_gap) // 2

        draw_bar(screen, x=bar_start, y=bar_y, width=bar_w, height=bar_h,
                 value=d.clutch, color=(80, 140, 220), label="C", font=font_sm)
        draw_bar(screen, x=bar_start + bar_w + bar_gap, y=bar_y, width=bar_w, height=bar_h,
                 value=d.brake, color=(220, 60, 60), label="B", font=font_sm)
        draw_bar(screen, x=bar_start + 2 * (bar_w + bar_gap), y=bar_y, width=bar_w, height=bar_h,
                 value=d.throttle, color=(60, 200, 80), label="T", font=font_sm)

        draw_tires(screen, cx=640, cy=630,
                   tire_data=d.tires, font=font_sm,
                   tile_w=60, tile_h=68, gap=14,
                   slip_ratios=self._slip_ratios,
                   suspension_heights=[t.suspension_height for t in d.tires])

        draw_g_meter(screen, cx=160, cy=615, radius=55,
                     lat_g=self._g_lat, lon_g=self._g_lon, font=font_sm)

        draw_slip_angle(screen, cx=355, cy=615, width=200,
                        slip_deg=self._slip_angle, font=font_sm)

        self._draw_info(screen, font_sm, d)

        draw_bar(screen, x=bar_start - 58, y=bar_y, width=30, height=bar_h,
                 value=d.fuel_pct, color=(80, 140, 220), label="FUEL", font=font_sm)

        self._draw_rpm_bar(screen, d)
        self._draw_indicators(screen, font_sm, d)

        if d.rev_limiter:
            overlay = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
            overlay.fill((220, 40, 40, 40))
            screen.blit(overlay, (0, 0))

    def _draw_header(self, screen, font_md: pygame.font.Font,
                     font_sm: pygame.font.Font) -> None:
        pygame.draw.rect(screen, C_HEADER, (0, 0, WIN_W, HEADER_H))
        pygame.draw.line(screen, C_SEPARATOR, (0, HEADER_H), (WIN_W, HEADER_H), 1)

        icon_x, icon_y = 14, (HEADER_H - 32) // 2
        if self._icon:
            screen.blit(self._icon, (icon_x, icon_y))

        title = font_md.render("RACE ENGINEER", True, C_TEXT)
        screen.blit(title, (icon_x + 32 + 10, (HEADER_H - title.get_height()) // 2))

        # Device IP / error indicator (right of title, left of buttons)
        status = self._get_status_fn()
        error = self._get_error_fn()
        if status == "error" and error:
            info_text = f"⚠ {error[:38]}"
            info_color = C_RED
        else:
            info_text = f"device: {self._config.device_ip or 'not configured'}"
            info_color = C_DIM if self._config.device_ip else C_ORANGE
        info_surf = font_sm.render(info_text, True, info_color)
        screen.blit(info_surf, info_surf.get_rect(
            midright=(self._conn_btn.left - 12, HEADER_H // 2)))

        mouse = pygame.mouse.get_pos()

        # Connect/disconnect button — 4 states
        conn_hover = self._conn_btn.collidepoint(mouse)
        _h = 15 if conn_hover else 0
        if status == "connected":
            conn_bg = (30 + _h, 80 + _h, 35 + _h)
            conn_dot = (60, 220, 80)
            conn_label = "LIVE"
        elif status == "connecting":
            conn_bg = (55 + _h, 50 + _h, 15 + _h)
            conn_dot = (220, 180, 60)
            conn_label = "WAIT"
        elif status == "error":
            conn_bg = (80 + _h, 30 + _h, 10 + _h)
            conn_dot = (220, 110, 40)
            conn_label = "ERR"
        else:
            conn_bg = (70 + _h, 20 + _h, 20 + _h)
            conn_dot = (200, 50, 50)
            conn_label = "OFF"
        pygame.draw.rect(screen, conn_bg, self._conn_btn, border_radius=5)
        pygame.draw.rect(screen, conn_dot, self._conn_btn, 1, border_radius=5)
        dot_x = self._conn_btn.left + 12
        dot_y = self._conn_btn.centery
        pygame.draw.circle(screen, conn_dot, (dot_x, dot_y), 4)
        lbl_surf = font_sm.render(conn_label, True, conn_dot)
        screen.blit(lbl_surf, lbl_surf.get_rect(midleft=(dot_x + 9, dot_y)))

        # Help button ?
        hbtn_color = C_BTN_GEAR_HOVER if self._help_btn.collidepoint(mouse) else C_BTN_GEAR
        pygame.draw.rect(screen, hbtn_color, self._help_btn, border_radius=5)
        h_sym = font_md.render("?", True, C_TEXT)
        screen.blit(h_sym, h_sym.get_rect(center=self._help_btn.center))

        # Settings button ⚙
        gbtn_color = C_BTN_GEAR_HOVER if self._gear_btn.collidepoint(mouse) else C_BTN_GEAR
        pygame.draw.rect(screen, gbtn_color, self._gear_btn, border_radius=5)
        gear_sym = font_md.render("⚙", True, C_TEXT)
        screen.blit(gear_sym, gear_sym.get_rect(center=self._gear_btn.center))

    def _draw_indicators(self, screen, font: pygame.font.Font, d: TelemetryData) -> None:
        """Status chip strip between RPM bar and main gauges."""
        CHIP_W, CHIP_H = 64, 18
        CHIP_GAP = 8
        STRIP_Y = RPM_BAR_Y + 16 + 5   # 5px below RPM bar

        # (label, active, active_fg, active_bg)
        chips = [
            ("TCS",   d.tcs_active,        (15, 10, 5),  (255, 140, 0)),
            ("ASM",   d.asm_active,         (15, 10, 5),  (255, 190, 0)),
            ("REV",   d.rev_limiter,        (255, 240, 240), (200, 30, 30)),
            ("HB",    d.handbrake_active,   (15, 15, 5),  (240, 210, 0)),
            ("LIGHT", d.lights_on,          (10, 10, 20), (190, 200, 255)),
            ("OIL!",  d.oil_temp > 130,     (255, 240, 240), (200, 30, 30)),
            ("H₂O!",  d.water_temp > 105,  (255, 240, 240), (200, 30, 30)),
        ]

        total_w = len(chips) * CHIP_W + (len(chips) - 1) * CHIP_GAP
        x = (WIN_W - total_w) // 2

        for label, active, fg, bg in chips:
            rect = pygame.Rect(x, STRIP_Y, CHIP_W, CHIP_H)
            if active:
                pygame.draw.rect(screen, bg, rect, border_radius=4)
                pygame.draw.rect(screen, fg, rect, 1, border_radius=4)
                txt = font.render(label, True, fg)
            else:
                pygame.draw.rect(screen, (28, 28, 36), rect, border_radius=4)
                pygame.draw.rect(screen, (48, 48, 58), rect, 1, border_radius=4)
                txt = font.render(label, True, (52, 52, 62))
            screen.blit(txt, txt.get_rect(center=rect.center))
            x += CHIP_W + CHIP_GAP

    def _draw_rpm_bar(self, screen, d: TelemetryData) -> None:
        bar_x, bar_y, bar_w, bar_h = 80, RPM_BAR_Y, WIN_W - 160, 16
        pct = max(0.0, min(1.0, (d.rpm / d.rpm_max) if d.rpm_max > 0 else 0.0))

        pygame.draw.rect(screen, (35, 35, 45), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
        if pct > 0:
            color = (220, 40, 40) if pct > 0.93 else ((255, 165, 0) if pct > 0.82 else (60, 200, 80))
            pygame.draw.rect(screen, color, (bar_x, bar_y, int(bar_w * pct), bar_h), border_radius=4)
        pygame.draw.rect(screen, (60, 60, 70), (bar_x, bar_y, bar_w, bar_h), 1, border_radius=4)

    def _draw_info(self, screen, font_sm: pygame.font.Font, d: TelemetryData) -> None:
        x, y = 820, 305
        line_h = 26

        def row(label: str, value: str, color=C_TEXT) -> None:
            nonlocal y
            lbl = font_sm.render(label, True, C_DIM)
            val = font_sm.render(value, True, color)
            screen.blit(lbl, (x, y))
            screen.blit(val, (x + 110, y))
            y += line_h

        row("LAP", f"{d.current_lap} / {d.total_laps}")
        row("LAP TIME", _fmt_lap(d.lap_time_ms), C_ACCENT)
        row("BEST", _fmt_lap(d.best_lap_ms), C_GREEN)
        row("LAST", _fmt_lap(d.last_lap_ms))
        row("WATER", f"{d.water_temp:.0f} °C",
            C_ORANGE if d.water_temp > 105 else C_TEXT)
        row("OIL", f"{d.oil_temp:.0f} °C",
            C_ORANGE if d.oil_temp > 130 else C_TEXT)
        row("FUEL", f"{d.fuel_level:.1f} L")
        if self._fuel_per_lap > 0:
            laps_left = d.fuel_level / self._fuel_per_lap
            row("FUEL/LAP", f"{self._fuel_per_lap:.2f} L", C_ACCENT)
            row("LAPS LEFT", f"{laps_left:.1f}",
                C_ORANGE if laps_left < 3 else C_TEXT)
        row("BOOST", f"{d.turbo_boost:+.2f} bar",
            C_ACCENT if d.turbo_boost > 0 else C_DIM)

        flags = []
        if d.paused:
            flags.append("PAUSE")
        if d.loading:
            flags.append("LOAD")
        if not d.in_race:
            flags.append("MENU")
        if flags:
            screen.blit(font_sm.render(" | ".join(flags), True, C_ORANGE), (x, y))
