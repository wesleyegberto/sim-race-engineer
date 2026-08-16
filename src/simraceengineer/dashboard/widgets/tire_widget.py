"""Tire temperature / wear display (four corners)."""

import pygame

C_COLD = (60, 100, 200)
C_COLD_WARMING = (220, 210, 100)   # 60–70 °C — cool but warming
C_OPTIMAL = (60, 200, 80)
C_HOT = (220, 60, 40)
C_TEXT = (40, 40, 45)
C_DIM = (100, 100, 110)
C_BORDER = (70, 70, 80)
C_SLIP_SPIN = (255, 140, 0)    # wheelspin — orange
C_SLIP_LOCK = (220, 40, 40)    # lockup   — red

_SUS_BG = (30, 30, 40)
_SUS_BORDER = (55, 55, 68)
_SUS_MAX = 0.15   # metres — full-travel reference
_SUS_BAR_W = 6
_SUS_BAR_GAP = 2   # gap between tile and sus bar

_WEAR_BG = (30, 30, 40)
_WEAR_BORDER = (55, 55, 68)
_WEAR_BAR_W = 6
_WEAR_BAR_GAP = 5   # gap between outer tile edge and wear bar

_ICON_COLOR = (140, 140, 155)   # dim gray — visible on dark bar background


def _temp_color(temp: float) -> tuple:
    if temp < 60:
        return C_COLD
    if temp < 70:
        t = (temp - 60) / 10
        return (
            int(C_COLD[0] + t * (C_COLD_WARMING[0] - C_COLD[0])),
            int(C_COLD[1] + t * (C_COLD_WARMING[1] - C_COLD[1])),
            int(C_COLD[2] + t * (C_COLD_WARMING[2] - C_COLD[2])),
        )
    if temp < 95:
        t = (temp - 70) / 25
        return (
            int(C_COLD_WARMING[0] + t * (C_OPTIMAL[0] - C_COLD_WARMING[0])),
            int(C_COLD_WARMING[1] + t * (C_OPTIMAL[1] - C_COLD_WARMING[1])),
            int(C_COLD_WARMING[2] + t * (C_OPTIMAL[2] - C_COLD_WARMING[2])),
        )
    if temp < 103:
        t = (temp - 95) / 8
        return (
            int(C_OPTIMAL[0] + t * (255 - C_OPTIMAL[0])),
            int(C_OPTIMAL[1] + t * (165 - C_OPTIMAL[1])),
            int(C_OPTIMAL[2] + t * (0   - C_OPTIMAL[2])),
        )
    t = min(1.0, (temp - 103) / 20)
    return (
        int(255 + t * (C_HOT[0] - 255)),
        int(165 + t * (C_HOT[1] - 165)),
        int(t * C_HOT[2]),
    )


def _wear_color(wear: float) -> tuple:
    """Color for wear bar fill: green (new) → yellow → orange → red (bald)."""
    if wear < 0.40:
        return (60, 200, 80)
    if wear < 0.65:
        return (220, 180, 0)
    if wear < 0.80:
        return (255, 120, 0)
    return (220, 40, 40)


_SLIP_THRESHOLD = 0.05   # below this = no significant slip


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
    slip_ratios: list | None = None,        # 4 floats, positive=wheelspin, negative=lockup
    suspension_heights: list | None = None,  # 4 floats in metres
    wear_pcts: list | None = None,          # 4 floats, 0=new tyre … 1=bald
    suspension_icon: pygame.Surface | None = None,
) -> None:
    """Draw a 2×2 grid of tire tiles centered at (cx, cy).

    When slip_ratios is provided, tile borders reflect slip state.
    When suspension_heights is provided, narrow vertical bars are drawn
    on the outer side of each tile (left for FL/RL, right for FR/RR).
    When wear_pcts is provided, narrow vertical bars are drawn on the
    inner side of each tile showing remaining rubber (fills from bottom).
    """
    positions = [
        (cx - tile_w - gap // 2, cy - tile_h - gap // 2),   # FL
        (cx + gap // 2, cy - tile_h - gap // 2),             # FR
        (cx - tile_w - gap // 2, cy + gap // 2),             # RL
        (cx + gap // 2, cy + gap // 2),                      # RR
    ]
    labels = ["FL", "FR", "RL", "RR"]
    # Suspension → inner side (between the two columns)
    # Wear       → outer side (far edge of each tile)
    _sus_left  = [False, True, False, True]
    _wear_left = [True, False, True, False]

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
            surface.blit(t_txt, t_txt.get_rect(center=(tx + tile_w // 2, ty + tile_h // 2 + 4)))

        # Suspension travel bar (outer side)
        if suspension_heights and i < len(suspension_heights):
            sus_h = suspension_heights[i]
            pct = max(0.0, min(1.0, 1.0 - sus_h / _SUS_MAX))  # 1=compressed, 0=extended
            if _sus_left[i]:
                bx = tx - _SUS_BAR_GAP - _SUS_BAR_W
            else:
                bx = tx + tile_w + _SUS_BAR_GAP
            bg_rect = pygame.Rect(bx, ty, _SUS_BAR_W, tile_h)
            pygame.draw.rect(surface, _SUS_BG, bg_rect, border_radius=2)
            filled_h = max(2, int(pct * tile_h))
            fill_rect = pygame.Rect(bx, ty + tile_h - filled_h, _SUS_BAR_W, filled_h)
            pygame.draw.rect(surface, _sus_color(pct), fill_rect, border_radius=2)
            pygame.draw.rect(surface, _SUS_BORDER, bg_rect, 1, border_radius=2)
            # Suspension icon above the bar
            if suspension_icon:
                iw, ih = suspension_icon.get_size()
                surface.blit(suspension_icon, (bx + (_SUS_BAR_W - iw) // 2, ty - ih - 2))

        # Wear bar (outer side) — full tile height, fills from bottom
        if wear_pcts and i < len(wear_pcts):
            wear = wear_pcts[i]
            remaining = 1.0 - wear
            if _wear_left[i]:
                bx = tx - _WEAR_BAR_GAP - _WEAR_BAR_W
            else:
                bx = tx + tile_w + _WEAR_BAR_GAP
            bg_rect = pygame.Rect(bx, ty, _WEAR_BAR_W, tile_h)
            pygame.draw.rect(surface, _WEAR_BG, bg_rect, border_radius=2)
            if wear > 0.0:
                filled_h = max(2, int(remaining * tile_h))
                fill_rect = pygame.Rect(bx, ty + tile_h - filled_h, _WEAR_BAR_W, filled_h)
                pygame.draw.rect(surface, _wear_color(wear), fill_rect, border_radius=2)
            pygame.draw.rect(surface, _WEAR_BORDER, bg_rect, 1, border_radius=2)
            # Wheel icon: outer ring + center dot above the bar
            icx = bx + _WEAR_BAR_W // 2
            pygame.draw.circle(surface, _ICON_COLOR, (icx, ty - 6), 3, 1)
            pygame.draw.circle(surface, _ICON_COLOR, (icx, ty - 6), 1)
