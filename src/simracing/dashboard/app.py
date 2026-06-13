"""Main pygame dashboard application."""

import asyncio
import logging
import math
import sys
from collections.abc import Callable
from pathlib import Path

import pygame

from ..config import AppConfig
from ..recording.lap_recorder import LapRecorder
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
WIN_W, WIN_H = 1280, 800
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

# In a PyInstaller bundle __file__ is inside a temp dir; assets land in sys._MEIPASS.
_BASE = Path(getattr(sys, "_MEIPASS", Path(__file__).parent.parent))
_IMG_DIR = _BASE / "simracing" / "img" if hasattr(sys, "_MEIPASS") else Path(__file__).parent.parent / "img"


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
        self._data: TelemetryData | None = None
        self._running = False
        self._icon: pygame.Surface | None = None
        self._icon_settings: pygame.Surface | None = None
        self._icon_info: pygame.Surface | None = None
        self._icon_close: pygame.Surface | None = None
        self._recorder = LapRecorder()
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

    def _reset_derived(self) -> None:
        self._prev_lap = -1
        self._lap_fuel_start = 0.0
        self._fuel_per_lap = 0.0
        self._prev_speed_ms = 0.0
        self._g_lat = 0.0
        self._g_lon = 0.0
        self._slip_ratios = [0.0, 0.0, 0.0, 0.0]
        self._slip_angle = 0.0
        self._data = None

    def _update_telemetry(self, d: TelemetryData, dt_ms: float) -> None:
        """Process a new telemetry frame: update derived metrics and store data."""
        # State transition logging
        if d.in_race != self._prev_in_race:
            log.info("Race state → %s", "IN RACE" if d.in_race else "OUT OF RACE")
            self._prev_in_race = d.in_race
            if d.in_race:
                self._recorder.start_session()
            else:
                self._recorder.stop_session()
                self._reset_derived()

        if not d.in_race:
            return
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

        # Slip angle: angle between velocity vector and car heading.
        # rotation.(x,y,z) are quaternion imaginary components (qi, qj, qk).
        # Reconstruct qw from unit-quaternion constraint, then derive the
        # world-space forward vector (GT7: Y-up, -Z = car forward).
        if d.speed_ms > 5.0:
            qi, qj, qk = d.rotation.x, d.rotation.y, d.rotation.z
            qw = math.sqrt(max(0.0, 1.0 - qi*qi - qj*qj - qk*qk))
            # Forward vector in world XZ (car's -Z axis rotated by quaternion)
            fwd_x = 2.0 * (qi * qk - qw * qj)
            fwd_z = -(1.0 - 2.0 * (qi * qi + qj * qj))
            # Project velocity onto car frame: dot=forward component, cross=lateral
            dot   = d.velocity.x * fwd_x + d.velocity.z * fwd_z
            cross = d.velocity.z * fwd_x - d.velocity.x * fwd_z
            raw_slip = math.degrees(math.atan2(cross, dot))
            self._slip_angle = 0.2 * raw_slip + 0.8 * self._slip_angle
        else:
            self._slip_angle *= 0.9  # decay to zero at low speed

        self._recorder.on_frame(d, self._g_lat, self._g_lon, self._slip_angle)
        self._data = d

    def _load_assets(self) -> None:
        def _load_icon(filename: str, size: int, tint: tuple | None = None) -> pygame.Surface | None:
            path = _IMG_DIR / filename
            if not path.exists():
                log.warning("Icon not found: %s", path)
                return None
            surf = pygame.image.load(str(path)).convert_alpha()
            surf = pygame.transform.smoothscale(surf, (size, size))
            if tint:
                surf.fill(tint, special_flags=pygame.BLEND_RGB_MAX)
            return surf

        self._icon = _load_icon("engineer.png", 32, C_TEXT)
        self._icon_settings = _load_icon("settings.png", 18, C_TEXT)
        self._icon_info = _load_icon("info.png", 18, C_TEXT)
        self._icon_close = _load_icon("close.png", 16)
        self._icon_flags = _load_icon("flags.png", 15, C_DIM)
        self._icon_tire_wheel = _load_icon("wheel.png", 15, C_DIM)
        self._icon_fuel = _load_icon("fuel.png", 15, C_DIM)
        self._icon_wheel = _load_icon("steering-wheel.png", 15, C_DIM)
        self._icon_suspension = _load_icon("suspension.png", 15, C_DIM)
        self._icon_gearbox = _load_icon("gearbox.png", 16, C_DIM)
        self._icon_gearbox_lg = _load_icon("gearbox.png", 40, C_DIM)
        self._icon_turbo = _load_icon("turbo.png", 15, C_DIM)
        self._icon_oil_sm = _load_icon("oil.png", 15, C_DIM)
        self._icon_coolant_sm = _load_icon("engine-coolant.png", 15, C_DIM)
        self._icon_speedometer = _load_icon("speedometer.png", 15, C_DIM)
        self._icon_rpm = _load_icon("rpm.png", 15, C_DIM)
        self._icon_panel_cluster = _load_icon("panel-cluster.png", 15, C_DIM)
        self._icon_tcs = _load_icon("tcs.png", 20, C_TEXT)
        self._icon_asm = _load_icon("asm.png", 20, C_TEXT)
        self._icon_parking = _load_icon("parking.png", 20, C_TEXT)
        self._icon_car_pedals = _load_icon("car-pedals.png", 15, C_DIM)
        self._icon_headlight = _load_icon("headlight.png", 20, C_TEXT)
        self._icon_oil = _load_icon("oil.png", 20, C_TEXT)
        self._icon_coolant = _load_icon("engine-coolant.png", 20, C_TEXT)
        self._icon_gforce = _load_icon("g-force.png", 15, C_DIM)
        self._icon_drifting = _load_icon("drifting.png", 15, C_DIM)
        self._icon_race_pos = _load_icon("race-pos.png", 15, C_DIM)
        self._icon_stopwatch = _load_icon("stopwatch.png", 15, C_DIM)

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
            self._settings.open(self._config.device_ip, self._config.rpm_flash)

        font_xl  = pygame.font.SysFont("monospace", 64, bold=True)
        font_spd = pygame.font.SysFont("monospace", 48, bold=True)
        font_lg  = pygame.font.SysFont("monospace", 32, bold=True)
        font_md  = pygame.font.SysFont("monospace", 20)
        font_sm  = pygame.font.SysFont("monospace", 14)

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
                        self._config.rpm_flash = self._settings.rpm_flash
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
                        self._settings.open(self._config.device_ip, self._config.rpm_flash)
                    elif self._help_btn.collidepoint(event.pos):
                        self._help.open()

            while not self._queue.empty():
                try:
                    self._update_telemetry(self._queue.get_nowait(), dt)
                except asyncio.QueueEmpty:
                    break

            screen.fill(C_BG)
            self._draw(screen, font_xl, font_spd, font_lg, font_md, font_sm)
            if self._settings:
                self._settings.draw(screen, font_md, font_sm, dt)
            if self._help:
                self._help.draw(screen, font_md, font_sm, self._icon_close,
                                icons={"wheel": self._icon_wheel, "fuel": self._icon_fuel, "flags": self._icon_flags, "suspension": self._icon_suspension, "gearbox": self._icon_gearbox, "turbo": self._icon_turbo, "speedometer": self._icon_speedometer, "rpm": self._icon_rpm, "panel-cluster": self._icon_panel_cluster, "tcs": self._icon_tcs, "asm": self._icon_asm, "parking": self._icon_parking, "car-pedals": self._icon_car_pedals, "headlight": self._icon_headlight, "oil": self._icon_oil, "tire-wheel": self._icon_tire_wheel, "coolant": self._icon_coolant, "g-force": self._icon_gforce, "drifting": self._icon_drifting, "race-pos": self._icon_race_pos, "stopwatch": self._icon_stopwatch})
            pygame.display.flip()

        pygame.quit()

    def _draw(self, screen, font_xl, font_spd, font_lg, font_md, font_sm) -> None:
        d = self._data if self._data is not None else TelemetryData()

        self._draw_header(screen, font_md, font_sm)

        draw_gauge(
            screen, cx=220, cy=380, radius=155,
            value=d.speed_kmh, min_val=0, max_val=d.speed_max_kmh if d.speed_max_kmh > 0 else 320,
            label="SPEED", unit="km/h",
            warn_pct=0.85, crit_pct=0.95,
            font_large=font_spd, font_small=font_sm,
        )

        draw_gauge(
            screen, cx=1100, cy=380, radius=155,
            value=d.rpm, min_val=0, max_val=d.rpm_max,
            label="ENGINE", unit="RPM",
            warn_pct=0.85, crit_pct=0.95,
            font_large=font_lg, font_small=font_sm,
        )

        CX = 600  # visual center between left gauge and info panel

        gear_surf = font_xl.render(d.gear_label, True, C_TEXT)
        if self._icon_gearbox_lg:
            gap = 10
            combined_w = self._icon_gearbox_lg.get_width() + gap + gear_surf.get_width()
            start_x = CX - combined_w // 2
            screen.blit(self._icon_gearbox_lg, self._icon_gearbox_lg.get_rect(midleft=(start_x, 155)))
            screen.blit(gear_surf, gear_surf.get_rect(midleft=(start_x + self._icon_gearbox_lg.get_width() + gap, 155)))
        else:
            screen.blit(gear_surf, gear_surf.get_rect(center=(CX, 155)))

        gear_lbl = font_sm.render("GEAR", True, C_DIM)
        if self._icon_gearbox:
            combined_w = self._icon_gearbox.get_width() + 5 + gear_lbl.get_width()
            lbl_x = CX - combined_w // 2
            screen.blit(self._icon_gearbox, self._icon_gearbox.get_rect(midleft=(lbl_x, 222)))
            screen.blit(gear_lbl, gear_lbl.get_rect(midleft=(lbl_x + self._icon_gearbox.get_width() + 5, 222)))
        else:
            screen.blit(gear_lbl, gear_lbl.get_rect(center=(CX, 222)))

        if 0 < d.suggested_gear < 15 and d.suggested_gear != d.gear:
            sg = font_lg.render(f"> {d.suggested_gear}", True, C_ORANGE)
            screen.blit(sg, sg.get_rect(center=(CX, 252)))

        bar_y = 300
        bar_h = 200
        bar_w = 42
        bar_gap = 22
        bar_start = CX - (3 * bar_w + 2 * bar_gap) // 2

        draw_bar(screen, x=bar_start, y=bar_y, width=bar_w, height=bar_h,
                 value=d.clutch, color=(80, 140, 220), label="C", font=font_sm)
        draw_bar(screen, x=bar_start + bar_w + bar_gap, y=bar_y, width=bar_w, height=bar_h,
                 value=d.brake, color=(220, 60, 60), label="B", font=font_sm)
        draw_bar(screen, x=bar_start + 2 * (bar_w + bar_gap), y=bar_y, width=bar_w, height=bar_h,
                 value=d.throttle, color=(60, 200, 80), label="T", font=font_sm)

        draw_tires(screen, cx=CX, cy=630,
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

        if d.rev_limiter and self._config.rpm_flash:
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
            info_text = f"[!] {error[:36]}"
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

        # Help button
        hbtn_color = C_BTN_GEAR_HOVER if self._help_btn.collidepoint(mouse) else C_BTN_GEAR
        pygame.draw.rect(screen, hbtn_color, self._help_btn, border_radius=5)
        if self._icon_info:
            screen.blit(self._icon_info, self._icon_info.get_rect(center=self._help_btn.center))
        else:
            h_sym = font_md.render("?", True, C_TEXT)
            screen.blit(h_sym, h_sym.get_rect(center=self._help_btn.center))

        # Settings button
        gbtn_color = C_BTN_GEAR_HOVER if self._gear_btn.collidepoint(mouse) else C_BTN_GEAR
        pygame.draw.rect(screen, gbtn_color, self._gear_btn, border_radius=5)
        if self._icon_settings:
            screen.blit(self._icon_settings, self._icon_settings.get_rect(center=self._gear_btn.center))
        else:
            gear_sym = font_md.render("S", True, C_TEXT)
            screen.blit(gear_sym, gear_sym.get_rect(center=self._gear_btn.center))

    def _draw_indicators(self, screen, font: pygame.font.Font, d: TelemetryData) -> None:
        """Status chip strip between RPM bar and main gauges."""
        CHIP_W, CHIP_H = 88, 32
        CHIP_GAP = 8
        STRIP_Y = RPM_BAR_Y + 16 + 5   # 5px below RPM bar

        # (label, active, active_fg, active_bg, icon)
        chips = [
            ("TCS",   d.tcs_active,        (15, 10, 5),     (255, 140, 0),    self._icon_tcs),
            ("ASM",   d.asm_active,         (15, 10, 5),     (255, 190, 0),    self._icon_asm),
            ("HB",    d.handbrake_active,   (15, 15, 5),     (240, 210, 0),    self._icon_parking),
            ("LIGHT", d.lights_on,          (10, 10, 20),    (190, 200, 255),  self._icon_headlight),
            ("OIL!",  d.oil_temp > 130,     (255, 240, 240), (200, 30, 30),    self._icon_oil),
            ("H2O!",  d.water_temp > 105,   (255, 240, 240), (200, 30, 30),    self._icon_coolant),
            ("REV",   d.rev_limiter,        (255, 240, 240), (200, 30, 30),    None),
        ]

        total_w = len(chips) * CHIP_W + (len(chips) - 1) * CHIP_GAP
        x = (WIN_W - total_w) // 2

        for label, active, fg, bg, icon in chips:
            rect = pygame.Rect(x, STRIP_Y, CHIP_W, CHIP_H)
            if active:
                pygame.draw.rect(screen, bg, rect, border_radius=4)
                pygame.draw.rect(screen, fg, rect, 1, border_radius=4)
                color = fg
            else:
                pygame.draw.rect(screen, (28, 28, 36), rect, border_radius=4)
                pygame.draw.rect(screen, (48, 48, 58), rect, 1, border_radius=4)
                color = (52, 52, 62)
            if icon:
                screen.blit(icon, icon.get_rect(center=rect.center))
            else:
                txt = font.render(label, True, color)
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
        PX, PY, PW = 710, 295, 210
        PAD = 10
        ICON_SZ = 14
        ICON_GAP = 5
        SEP_COLOR = (50, 50, 68)
        line_h = 30

        label_x = PX + PAD
        val_rx = PX + PW - PAD  # right edge for value alignment

        # pre-draw card (fixed height covers max possible rows)
        card_h = line_h * 12 + PAD * 2 + 14
        card_surf = pygame.Surface((PW, card_h), pygame.SRCALPHA)
        card_surf.fill((15, 15, 22, 190))
        screen.blit(card_surf, (PX, PY))
        pygame.draw.rect(screen, SEP_COLOR, pygame.Rect(PX, PY, PW, card_h), 1, border_radius=8)

        y = PY + PAD
        font_h = font_sm.get_height()

        def row(label: str, value: str, color=C_TEXT, icon=None) -> None:
            nonlocal y
            ix = label_x
            if icon is not None:
                screen.blit(icon, icon.get_rect(midleft=(ix, y + font_h // 2)))
                ix += ICON_SZ + ICON_GAP
            screen.blit(font_sm.render(label, True, C_DIM), (ix, y))
            val_surf = font_sm.render(value, True, color)
            screen.blit(val_surf, val_surf.get_rect(midright=(val_rx, y + font_h // 2)))
            y += line_h

        def sep() -> None:
            nonlocal y
            pygame.draw.line(screen, SEP_COLOR, (PX + PAD, y - 4), (PX + PW - PAD, y - 4), 1)

        lap_str = str(d.current_lap) if d.total_laps == 0 else f"{d.current_lap} / {d.total_laps}"
        row("LAP", lap_str, icon=self._icon_flags)
        if d.race_position > 0 and d.cars_in_race > 0:
            row("POS", f"{d.race_position} / {d.cars_in_race}", icon=self._icon_race_pos)
        row("LAP TIME", _fmt_lap(d.lap_time_ms), C_ACCENT, icon=self._icon_stopwatch)
        row("BEST", _fmt_lap(d.best_lap_ms), C_GREEN, icon=self._icon_stopwatch)
        row("LAST", _fmt_lap(d.last_lap_ms), icon=self._icon_stopwatch)

        sep()

        row("BOOST", f"{d.turbo_boost:+.2f} bar",
            C_ACCENT if d.turbo_boost > 0 else C_DIM, icon=self._icon_turbo)
        row("FUEL", f"{d.fuel_level:.1f} L", icon=self._icon_fuel)
        if self._fuel_per_lap > 0:
            laps_left = d.fuel_level / self._fuel_per_lap
            row("FUEL/LAP", f"{self._fuel_per_lap:.2f} L", C_ACCENT, icon=self._icon_fuel)
            row("LAPS LEFT", f"{laps_left:.1f}",
                C_ORANGE if laps_left < 3 else C_TEXT, icon=self._icon_fuel)
        row("OIL", f"{d.oil_temp:.0f} °C",
            C_ORANGE if d.oil_temp > 130 else C_TEXT, icon=self._icon_oil_sm)
        row("WATER", f"{d.water_temp:.0f} °C",
            C_ORANGE if d.water_temp > 105 else C_TEXT, icon=self._icon_coolant_sm)

        flags = []
        if d.paused:
            flags.append("PAUSE")
        if d.loading:
            flags.append("LOAD")
        if not d.in_race:
            flags.append("MENU")
        if flags:
            sep()
            screen.blit(font_sm.render(" | ".join(flags), True, C_ORANGE), (label_x, y))
