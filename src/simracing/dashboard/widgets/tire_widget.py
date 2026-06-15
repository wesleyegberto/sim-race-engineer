"""Tire temperature / wear display (four corners)."""

import pygame

C_COLD = (60, 100, 200)
C_OPTIMAL = (60, 200, 80)
C_HOT = (220, 60, 40)
C_TEXT = (230, 230, 230)
C_DIM = (100, 100, 110)
C_BORDER = (70, 70, 80)
C_SLIP_SPIN = (255, 140, 0)    # wheelspin — orange
C_SLIP_LOCK = (220, 40, 40)    # lockup   — red

_SUS_BG = (30, 30, 40)
_SUS_BORDER = (55, 55, 68)
_SUS_MAX = 0.15   # metres — full-travel reference
_SUS_BAR_W = 6
_SUS_BAR_GAP = 5   # gap between tile and sus bar


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


_SLIP_THRESHOLD = 0.05   # below this = no significant slip

C_WEAR_OK   = (60, 200, 80)    # green  — < 30 %
C_WEAR_MED  = (255, 190, 0)    # yellow — 30–60 %
C_WEAR_HIGH = (220, 60, 40)    # red    — > 60 %


def _wear_color(wear: float) -> tuple:
    if wear < 0.30:
        return C_WEAR_OK
    if wear < 0.60:
        return C_WEAR_MED
    return C_WEAR_HIGH


def _sus_color(pct: float) -> tuple:
    """Color for suspension bar fill based on compression (0=extended, 1=bottomed)."""
    if pct < 0.30:
        return (60, 100, 200)    # blue  — light / extended
    if pct < 0.65:
        return (60, 200, 80)     # green — nominal
    if pct < 0.85:
        return (255, 165, 0)     # orange — heavily loaded
    return (220, 60, 60)         # red   — near bottomed out


def draw_tires(
    surface: pygame.Surface,
    cx: int,
    cy: int,
    tire_data: list,   # list[TireData], 4 elements FL FR RL RR
    font: pygame.font.Font | None = None,
    tile_w: int = 52,
    tile_h: int = 70,
    gap: int = 8,
    slip_ratios: list | None = None,       # 4 floats, positive=wheelspin, negative=lockup
    suspension_heights: list | None = None,  # 4 floats in metres
) -> None:
    """Draw a 2×2 grid of tire tiles centered at (cx, cy).

    When slip_ratios is provided, tile borders reflect slip state.
    When suspension_heights is provided, narrow vertical bars are drawn
    on the outer side of each tile (left for FL/RL, right for FR/RR).
    """
    positions = [
        (cx - tile_w - gap // 2, cy - tile_h - gap // 2),   # FL
        (cx + gap // 2, cy - tile_h - gap // 2),             # FR
        (cx - tile_w - gap // 2, cy + gap // 2),             # RL
        (cx + gap // 2, cy + gap // 2),                      # RR
    ]
    labels = ["FL", "FR", "RL", "RR"]
    # True = bar goes to the left of the tile; False = to the right
    _bar_left = [True, False, True, False]

    for i, (tx, ty) in enumerate(positions):
        tire = tire_data[i] if i < len(tire_data) else None
        temp = tire.surface_temp if tire else 0.0
        color = _temp_color(temp)

        slip = slip_ratios[i] if slip_ratios and i < len(slip_ratios) else 0.0
        if slip > _SLIP_THRESHOLD:
            border_color = C_SLIP_SPIN
            border_w = 2
        elif slip < -_SLIP_THRESHOLD:
            border_color = C_SLIP_LOCK
            border_w = 3
        else:
            border_color = C_BORDER
            border_w = 1

        rect = pygame.Rect(tx, ty, tile_w, tile_h)
        pygame.draw.rect(surface, color, rect, border_radius=6)
        pygame.draw.rect(surface, border_color, rect, border_w, border_radius=6)

        if font:
            lbl = font.render(labels[i], True, C_TEXT)
            surface.blit(lbl, lbl.get_rect(center=(tx + tile_w // 2, ty + 14)))
            t_txt = font.render(f"{temp:.0f}°", True, C_TEXT)
            surface.blit(t_txt, t_txt.get_rect(center=(tx + tile_w // 2, ty + tile_h // 2)))
            wear_pct = (tire.wear * 100) if tire else 0.0
            w_col = _wear_color(tire.wear) if tire else C_DIM
            w_txt = font.render(f"{wear_pct:.0f}%", True, w_col)
            surface.blit(w_txt, w_txt.get_rect(center=(tx + tile_w // 2, ty + tile_h - 12)))

        # Suspension travel bar
        if suspension_heights and i < len(suspension_heights):
            sus_h = suspension_heights[i]
            pct = max(0.0, min(1.0, 1.0 - sus_h / _SUS_MAX))  # 1=compressed, 0=extended
            if _bar_left[i]:
                bx = tx - _SUS_BAR_GAP - _SUS_BAR_W
            else:
                bx = tx + tile_w + _SUS_BAR_GAP
            bg_rect = pygame.Rect(bx, ty, _SUS_BAR_W, tile_h)
            pygame.draw.rect(surface, _SUS_BG, bg_rect, border_radius=2)
            filled_h = max(2, int(pct * tile_h))
            fill_rect = pygame.Rect(bx, ty + tile_h - filled_h, _SUS_BAR_W, filled_h)
            pygame.draw.rect(surface, _sus_color(pct), fill_rect, border_radius=2)
            pygame.draw.rect(surface, _SUS_BORDER, bg_rect, 1, border_radius=2)
