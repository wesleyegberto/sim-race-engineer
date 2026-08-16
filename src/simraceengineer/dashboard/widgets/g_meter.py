"""G-meter widget: circle with moving dot showing lateral and longitudinal G-force."""

import math

import pygame

C_BG = (28, 28, 36)
C_OUTER = (42, 42, 55)
C_RING = (58, 58, 72)
C_CROSS = (50, 50, 65)
C_TEXT = (230, 230, 230)
C_DIM = (100, 100, 110)
C_GREEN = (60, 200, 80)
C_ORANGE = (255, 165, 0)
C_RED = (220, 60, 60)


def draw_g_meter(
    surface: pygame.Surface,
    cx: int,
    cy: int,
    radius: int,
    lat_g: float,
    lon_g: float,
    font: pygame.font.Font | None = None,
    max_g: float = 2.0,
) -> None:
    """Draw a G-meter circle.

    Dot moves right for right-turn lateral G, up for braking (negative lon),
    down for acceleration (positive lon).
    """
    pygame.draw.circle(surface, C_OUTER, (cx, cy), radius)
    pygame.draw.circle(surface, C_RING, (cx, cy), radius, 1)

    # Concentric G-rings at 0.5G intervals
    for ring_g in (0.5, 1.0, 1.5):
        r = int(radius * ring_g / max_g)
        if r > 0:
            pygame.draw.circle(surface, C_RING, (cx, cy), r, 1)

    # Crosshairs
    pygame.draw.line(surface, C_CROSS, (cx - radius, cy), (cx + radius, cy), 1)
    pygame.draw.line(surface, C_CROSS, (cx, cy - radius), (cx, cy + radius), 1)

    # Dot position: lat_g → X, lon_g → Y (flip: up = braking = negative lon)
    ndx = lat_g / max_g
    ndy = -lon_g / max_g
    dist = math.hypot(ndx, ndy)
    if dist > 1.0:
        ndx /= dist
        ndy /= dist

    inner_r = radius - 6
    dot_x = int(cx + ndx * inner_r)
    dot_y = int(cy + ndy * inner_r)

    g_mag = math.hypot(lat_g, lon_g)
    dot_color = C_RED if g_mag > 1.5 else (C_ORANGE if g_mag > 0.8 else C_GREEN)

    pygame.draw.circle(surface, dot_color, (dot_x, dot_y), 5)
    pygame.draw.circle(surface, C_TEXT, (dot_x, dot_y), 5, 1)

    if font:
        title = font.render("G-METER", True, C_DIM)
        surface.blit(title, title.get_rect(center=(cx, cy + radius + 11)))
        lat_surf = font.render(f"LAT {lat_g:+.2f}g", True, C_TEXT)
        lon_surf = font.render(f"LON {lon_g:+.2f}g", True, C_TEXT)
        surface.blit(lat_surf, lat_surf.get_rect(center=(cx, cy + radius + 24)))
        surface.blit(lon_surf, lon_surf.get_rect(center=(cx, cy + radius + 37)))
