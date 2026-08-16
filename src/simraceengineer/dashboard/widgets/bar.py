"""Linear bar widgets: throttle, brake, fuel."""

import pygame

C_TEXT = (230, 230, 230)
C_DIM = (100, 100, 110)


def draw_bar(
    surface: pygame.Surface,
    x: int,
    y: int,
    width: int,
    height: int,
    value: float,          # 0.0–1.0
    color: tuple,
    label: str,
    font: pygame.font.Font | None = None,
    vertical: bool = True,
) -> None:
    """Draw a filled progress bar."""
    border = pygame.Rect(x, y, width, height)
    pygame.draw.rect(surface, (40, 40, 50), border, border_radius=4)

    fill_h = int(height * value) if vertical else 0
    fill_w = 0 if vertical else int(width * value)

    if vertical:
        fill = pygame.Rect(x, y + height - fill_h, width, fill_h)
    else:
        fill = pygame.Rect(x, y, fill_w, height)

    if value > 0:
        pygame.draw.rect(surface, color, fill, border_radius=4)

    pygame.draw.rect(surface, (70, 70, 80), border, 1, border_radius=4)

    if font:
        pct_txt = font.render(f"{value * 100:.0f}%", True, C_TEXT)
        if vertical:
            surface.blit(pct_txt, pct_txt.get_rect(center=(x + width // 2, y - 14)))
        lbl = font.render(label, True, C_DIM)
        if vertical:
            surface.blit(lbl, lbl.get_rect(center=(x + width // 2, y + height + 14)))
        else:
            surface.blit(lbl, lbl.get_rect(midright=(x - 8, y + height // 2)))
