"""Circular arc gauge (speedometer, tachometer)."""

import math

import pygame

# Colors
C_BG = (18, 18, 22)
C_ARC = (50, 50, 60)
C_NEEDLE = (220, 60, 60)
C_WARN = (255, 165, 0)
C_CRIT = (220, 40, 40)
C_TEXT = (230, 230, 230)
C_DIM = (120, 120, 130)


def draw_gauge(
    surface: pygame.Surface,
    cx: int,
    cy: int,
    radius: int,
    value: float,
    min_val: float,
    max_val: float,
    label: str,
    unit: str,
    warn_pct: float = 0.85,
    crit_pct: float = 0.95,
    start_angle_deg: float = 225.0,
    sweep_deg: float = 270.0,
    tick_count: int = 10,
    font_large: pygame.font.Font | None = None,
    font_small: pygame.font.Font | None = None,
) -> None:
    """Draw a circular gauge centred at (cx, cy)."""
    pct = max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))

    arc_start = math.radians(start_angle_deg)
    arc_sweep = math.radians(sweep_deg)

    # Background arc
    _draw_arc(surface, cx, cy, radius, arc_start, arc_sweep, C_ARC, width=8)

    # Colored fill arc
    fill_color = C_CRIT if pct >= crit_pct else (C_WARN if pct >= warn_pct else (80, 200, 120))
    _draw_arc(surface, cx, cy, radius, arc_start, arc_sweep * pct, fill_color, width=8)

    # Tick marks
    for i in range(tick_count + 1):
        t = i / tick_count
        angle = arc_start + arc_sweep * t
        inner = radius - 14 if i % (tick_count // 5 or 1) == 0 else radius - 8
        ox = cx + math.cos(angle) * radius
        oy = cy - math.sin(angle) * radius
        ix = cx + math.cos(angle) * inner
        iy = cy - math.sin(angle) * inner
        pygame.draw.line(surface, C_DIM, (int(ox), int(oy)), (int(ix), int(iy)), 2)

    # Needle
    needle_angle = arc_start + arc_sweep * pct
    nx = cx + math.cos(needle_angle) * (radius - 16)
    ny = cy - math.sin(needle_angle) * (radius - 16)
    pygame.draw.line(surface, C_NEEDLE, (cx, cy), (int(nx), int(ny)), 3)
    pygame.draw.circle(surface, C_NEEDLE, (cx, cy), 6)

    # Value text
    if font_large:
        txt = font_large.render(f"{value:.0f}", True, C_TEXT)
        surface.blit(txt, txt.get_rect(center=(cx, cy + radius // 3)))
    if font_small:
        u = font_small.render(unit, True, C_DIM)
        surface.blit(u, u.get_rect(center=(cx, cy + radius // 3 + 22)))
        lbl = font_small.render(label, True, C_DIM)
        surface.blit(lbl, lbl.get_rect(center=(cx, cy + radius // 2 + 14)))


def _draw_arc(
    surface: pygame.Surface,
    cx: int,
    cy: int,
    radius: int,
    start: float,
    sweep: float,
    color: tuple,
    width: int = 4,
    steps: int = 120,
) -> None:
    if sweep <= 0:
        return
    prev = None
    for i in range(steps + 1):
        angle = start + sweep * (i / steps)
        x = int(cx + math.cos(angle) * radius)
        y = int(cy - math.sin(angle) * radius)
        if prev:
            pygame.draw.line(surface, color, prev, (x, y), width)
        prev = (x, y)
