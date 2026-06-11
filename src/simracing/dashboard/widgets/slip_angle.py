"""Slip angle indicator — horizontal bar showing oversteer/understeer."""

import pygame

C_NEUTRAL = (60, 200, 80)
C_MODERATE = (255, 165, 0)
C_HIGH = (220, 40, 40)
C_DIM = (95, 95, 108)
C_BG = (35, 35, 45)
C_BORDER = (60, 60, 80)


def _slip_color(abs_deg: float) -> tuple:
    if abs_deg < 5.0:
        return C_NEUTRAL
    if abs_deg < 12.0:
        return C_MODERATE
    return C_HIGH


def draw_slip_angle(
    surface: pygame.Surface,
    cx: int,
    cy: int,
    width: int,
    slip_deg: float,
    font: pygame.font.Font | None = None,
    max_deg: float = 25.0,
) -> None:
    """Draw a horizontal slip angle bar centered at (cx, cy).

    Label is drawn above the bar, value below.
    Positive slip_deg = rear sliding right (oversteer).
    """
    half_w = width // 2
    bar_h = 10
    bar_y = cy - bar_h // 2

    # Background bar
    bg_rect = pygame.Rect(cx - half_w, bar_y, width, bar_h)
    pygame.draw.rect(surface, C_BG, bg_rect, border_radius=3)

    # Fill from center toward slip direction
    clamped = max(-max_deg, min(max_deg, slip_deg))
    abs_deg = abs(clamped)
    color = _slip_color(abs_deg)

    if abs_deg > 0.2:
        fill_w = max(2, int((abs_deg / max_deg) * half_w))
        fill_x = cx if clamped > 0 else cx - fill_w
        pygame.draw.rect(surface, color, (fill_x, bar_y + 2, fill_w, bar_h - 4))

    # Center tick
    pygame.draw.line(surface, C_BORDER, (cx, bar_y), (cx, bar_y + bar_h), 1)

    # Border
    pygame.draw.rect(surface, C_BORDER, bg_rect, 1, border_radius=3)

    if font:
        lbl = font.render("SLIP", True, C_DIM)
        surface.blit(lbl, lbl.get_rect(midbottom=(cx, bar_y - 3)))

        val_color = color if abs_deg > 0.5 else C_DIM
        val = font.render(f"{slip_deg:+.1f}°", True, val_color)
        surface.blit(val, val.get_rect(midtop=(cx, bar_y + bar_h + 3)))
