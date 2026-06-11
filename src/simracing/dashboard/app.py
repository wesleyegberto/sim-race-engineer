"""Main pygame dashboard application."""

import asyncio
import logging
from pathlib import Path

import pygame

from ..telemetry.models import TelemetryData
from .widgets.bar import draw_bar
from .widgets.gauge import draw_gauge
from .widgets.tire_widget import draw_tires

log = logging.getLogger(__name__)

# ── Layout constants ──────────────────────────────────────────────────────────
WIN_W, WIN_H = 1280, 720
FPS = 60

HEADER_H = 52          # height of the title strip
RPM_BAR_Y = HEADER_H + 10

C_BG = (14, 14, 18)
C_HEADER = (20, 20, 26)
C_TEXT = (230, 230, 230)
C_DIM = (100, 100, 110)
C_ACCENT = (80, 140, 220)
C_RED = (220, 60, 60)
C_GREEN = (60, 200, 80)
C_ORANGE = (255, 165, 0)
C_PANEL = (22, 22, 28)
C_SEPARATOR = (45, 45, 55)

_IMG_DIR = Path(__file__).parent.parent / "img"


def _fmt_lap(ms: int) -> str:
    if ms <= 0:
        return "--:--.---"
    m = ms // 60000
    s = (ms % 60000) // 1000
    ms_r = ms % 1000
    return f"{m}:{s:02d}.{ms_r:03d}"


class DashboardApp:
    def __init__(self, telemetry_queue: asyncio.Queue) -> None:
        self._queue = telemetry_queue
        self._data = TelemetryData()
        self._running = False
        self._icon: pygame.Surface | None = None

    def _load_assets(self) -> None:
        icon_path = _IMG_DIR / "engineer.png"
        if icon_path.exists():
            raw = pygame.image.load(str(icon_path)).convert_alpha()
            self._icon = pygame.transform.smoothscale(raw, (32, 32))
        else:
            log.warning("Icon not found: %s", icon_path)

    def run(self) -> None:
        pygame.init()
        pygame.display.set_caption("Race Engineer")
        screen = pygame.display.set_mode((WIN_W, WIN_H))
        clock = pygame.time.Clock()

        self._load_assets()

        font_xl = pygame.font.SysFont("monospace", 64, bold=True)
        font_lg = pygame.font.SysFont("monospace", 32, bold=True)
        font_md = pygame.font.SysFont("monospace", 20)
        font_sm = pygame.font.SysFont("monospace", 14)

        self._running = True
        while self._running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self._running = False

            while not self._queue.empty():
                try:
                    self._data = self._queue.get_nowait()
                except asyncio.QueueEmpty:
                    break

            screen.fill(C_BG)
            self._draw(screen, font_xl, font_lg, font_md, font_sm)
            pygame.display.flip()
            clock.tick(FPS)

        pygame.quit()

    def _draw(self, screen, font_xl, font_lg, font_md, font_sm) -> None:
        d = self._data

        # ── Header ────────────────────────────────────────────────────────────
        self._draw_header(screen, font_md)

        # ── Speedometer (left) ────────────────────────────────────────────────
        draw_gauge(
            screen, cx=220, cy=380, radius=155,
            value=d.speed_kmh, min_val=0, max_val=d.speed_max_kmh if d.speed_max_kmh > 0 else 320,
            label="SPEED", unit="km/h",
            warn_pct=0.85, crit_pct=0.95,
            font_large=font_lg, font_small=font_sm,
        )

        # ── Tachometer (right) ────────────────────────────────────────────────
        draw_gauge(
            screen, cx=1060, cy=380, radius=155,
            value=d.rpm, min_val=0, max_val=d.rpm_max,
            label="ENGINE", unit="RPM",
            warn_pct=0.85, crit_pct=0.95,
            font_large=font_lg, font_small=font_sm,
        )

        # ── Gear (centre-top) ─────────────────────────────────────────────────
        gear_surf = font_xl.render(d.gear_label, True, C_TEXT)
        screen.blit(gear_surf, gear_surf.get_rect(center=(640, 155)))

        gear_lbl = font_sm.render("GEAR", True, C_DIM)
        screen.blit(gear_lbl, gear_lbl.get_rect(center=(640, 222)))

        if d.suggested_gear > 0 and d.suggested_gear != d.gear:
            sg = font_lg.render(f"→ {d.suggested_gear}", True, C_ORANGE)
            screen.blit(sg, sg.get_rect(center=(640, 252)))

        # ── Clutch / Brake / Throttle bars (centre) ───────────────────────────
        bar_y = 300
        bar_h = 200
        bar_w = 42
        bar_gap = 22
        bar_start = 640 - (3 * bar_w + 2 * bar_gap) // 2

        draw_bar(screen, x=bar_start, y=bar_y, width=bar_w, height=bar_h,
                 value=d.clutch, color=(80, 140, 220),
                 label="C", font=font_sm)

        draw_bar(screen, x=bar_start + bar_w + bar_gap, y=bar_y, width=bar_w, height=bar_h,
                 value=d.brake, color=(220, 60, 60),
                 label="B", font=font_sm)

        draw_bar(screen, x=bar_start + 2 * (bar_w + bar_gap), y=bar_y, width=bar_w, height=bar_h,
                 value=d.throttle, color=(60, 200, 80),
                 label="T", font=font_sm)

        # ── Tire temps (bottom-centre) ────────────────────────────────────────
        draw_tires(screen, cx=640, cy=648,
                   tire_data=d.tires, font=font_sm,
                   tile_w=60, tile_h=68, gap=14)

        # ── Info panel (right-centre) ─────────────────────────────────────────
        self._draw_info(screen, font_sm, d)

        # ── Fuel bar (left of pedals) ─────────────────────────────────────────
        draw_bar(screen, x=bar_start - 58, y=bar_y, width=30, height=bar_h,
                 value=d.fuel_pct, color=(80, 140, 220),
                 label="FUEL", font=font_sm)

        # ── RPM bar (below header) ────────────────────────────────────────────
        self._draw_rpm_bar(screen, d)

        # ── Rev limiter flash ─────────────────────────────────────────────────
        if d.rev_limiter:
            overlay = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
            overlay.fill((220, 40, 40, 40))
            screen.blit(overlay, (0, 0))

    def _draw_header(self, screen, font_md: pygame.font.Font) -> None:
        pygame.draw.rect(screen, C_HEADER, (0, 0, WIN_W, HEADER_H))
        pygame.draw.line(screen, C_SEPARATOR, (0, HEADER_H), (WIN_W, HEADER_H), 1)

        icon_x, icon_y = 14, (HEADER_H - 32) // 2
        if self._icon:
            screen.blit(self._icon, (icon_x, icon_y))

        title = font_md.render("RACE ENGINEER", True, C_TEXT)
        text_x = icon_x + 32 + 10
        text_y = (HEADER_H - title.get_height()) // 2
        screen.blit(title, (text_x, text_y))

    def _draw_rpm_bar(self, screen, d: TelemetryData) -> None:
        bar_x, bar_y, bar_w, bar_h = 80, RPM_BAR_Y, WIN_W - 160, 16
        pct = (d.rpm / d.rpm_max) if d.rpm_max > 0 else 0.0
        pct = max(0.0, min(1.0, pct))

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
            f_surf = font_sm.render(" | ".join(flags), True, C_ORANGE)
            screen.blit(f_surf, (x, y))
