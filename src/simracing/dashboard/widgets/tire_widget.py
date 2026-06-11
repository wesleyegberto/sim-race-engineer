"""Tire temperature / wear display (four corners)."""

import pygame

C_COLD = (60, 100, 200)
C_OPTIMAL = (60, 200, 80)
C_HOT = (220, 60, 40)
C_TEXT = (230, 230, 230)
C_DIM = (100, 100, 110)
C_BORDER = (70, 70, 80)


def _temp_color(temp: float) -> tuple:
    if temp < 60:
        return C_COLD
    if temp < 100:
        t = (temp - 60) / 40
        return (
            int(C_COLD[0] + t * (C_OPTIMAL[0] - C_COLD[0])),
            int(C_COLD[1] + t * (C_OPTIMAL[1] - C_COLD[1])),
            int(C_COLD[2] + t * (C_OPTIMAL[2] - C_COLD[2])),
        )
    if temp < 130:
        return C_OPTIMAL
    t = min(1.0, (temp - 130) / 50)
    return (
        int(C_OPTIMAL[0] + t * (C_HOT[0] - C_OPTIMAL[0])),
        int(C_OPTIMAL[1] + t * (C_HOT[1] - C_OPTIMAL[1])),
        int(C_OPTIMAL[2] + t * (C_HOT[2] - C_OPTIMAL[2])),
    )


def draw_tires(
    surface: pygame.Surface,
    cx: int,
    cy: int,
    tire_data: list,   # list[TireData], 4 elements FL FR RL RR
    font: pygame.font.Font | None = None,
    tile_w: int = 52,
    tile_h: int = 70,
    gap: int = 8,
) -> None:
    """Draw a 2×2 grid of tire tiles centered at (cx, cy)."""
    positions = [
        (cx - tile_w - gap // 2, cy - tile_h - gap // 2),   # FL
        (cx + gap // 2, cy - tile_h - gap // 2),             # FR
        (cx - tile_w - gap // 2, cy + gap // 2),             # RL
        (cx + gap // 2, cy + gap // 2),                      # RR
    ]
    labels = ["FL", "FR", "RL", "RR"]

    for i, (tx, ty) in enumerate(positions):
        tire = tire_data[i] if i < len(tire_data) else None
        temp = tire.surface_temp if tire else 0.0
        color = _temp_color(temp)

        rect = pygame.Rect(tx, ty, tile_w, tile_h)
        pygame.draw.rect(surface, color, rect, border_radius=6)
        pygame.draw.rect(surface, C_BORDER, rect, 1, border_radius=6)

        if font:
            lbl = font.render(labels[i], True, C_TEXT)
            surface.blit(lbl, lbl.get_rect(center=(tx + tile_w // 2, ty + 14)))
            t_txt = font.render(f"{temp:.0f}°", True, C_TEXT)
            surface.blit(t_txt, t_txt.get_rect(center=(tx + tile_w // 2, ty + tile_h // 2 + 4)))
