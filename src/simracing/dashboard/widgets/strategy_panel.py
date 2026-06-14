"""Strategy overlay panel for configuring user-defined pit stop strategy."""

from typing import Literal

import pygame

C_OVERLAY = (0, 0, 0, 160)
C_CARD = (28, 28, 36)
C_BORDER = (60, 60, 75)
C_TEXT = (230, 230, 230)
C_DIM = (120, 120, 135)
C_ACCENT = (80, 140, 220)
C_INPUT_BG = (18, 18, 24)
C_INPUT_ACTIVE = (40, 60, 100)
C_BTN_SAVE = (60, 120, 200)
C_BTN_CANCEL = (55, 55, 68)
C_BTN_HOVER = (80, 140, 220)
C_BTN_CLEAR = (80, 50, 50)

_CARD_W, _CARD_H = 420, 460
_ALLOWED_DIGITS = set("0123456789")
_MAX_LAP = 999

Action = Literal["saved", "cancelled", "cleared"] | None

_MAX_STOPS = 3


class StrategyPanel:
    def __init__(self, win_w: int, win_h: int) -> None:
        self._win_w = win_w
        self._win_h = win_h
        self.active = False

        cx = (win_w - _CARD_W) // 2
        cy = (win_h - _CARD_H) // 2
        self._card = pygame.Rect(cx, cy, _CARD_W, _CARD_H)

        fx = cx + 20
        fy = cy + 70

        # Stops count buttons: 0/1/2/3
        self._stop_btns = [
            pygame.Rect(fx + i * 60, fy, 50, 30)
            for i in range(4)
        ]

        # Lap input fields for each stop
        self._lap_fields = [
            pygame.Rect(fx + 120, fy + 50 + i * 40, 80, 30)
            for i in range(_MAX_STOPS)
        ]

        # Tyre wear limit field
        self._wear_field = pygame.Rect(fx + 180, fy + 170 + 20, 60, 30)

        # Pit buffer field
        self._buffer_field = pygame.Rect(fx + 180, fy + 220 + 20, 60, 30)

        # Voice strategy checkbox
        self._voice_chk = pygame.Rect(fx, fy + 280, 18, 18)

        btn_y = cy + _CARD_H - 52
        self._btn_save   = pygame.Rect(cx + _CARD_W - 198, btn_y, 80, 34)
        self._btn_clear  = pygame.Rect(cx + _CARD_W - 326, btn_y, 120, 34)
        self._btn_cancel = pygame.Rect(cx + _CARD_W - 110, btn_y, 90, 34)

        # State
        self._planned_stops: int = 0
        self._lap_texts: list[str] = ["", "", ""]
        self._wear_text: str = "80"
        self._buffer_text: str = "1"
        self._voice_strategy: bool = True
        self._active_field: str | None = None  # "lap0","lap1","lap2","wear","buffer"
        self._cursor_visible = True
        self._cursor_timer = 0

    # ── Public interface ──────────────────────────────────────────────────────

    def open(
        self,
        planned_stops: int,
        planned_stop_laps: list[int],
        tyre_wear_limit_pct: float,
        pit_buffer_laps: int,
        voice_alert_strategy: bool,
    ) -> None:
        self._planned_stops = min(planned_stops, _MAX_STOPS)
        self._lap_texts = ["", "", ""]
        for i, lap in enumerate(planned_stop_laps[:_MAX_STOPS]):
            self._lap_texts[i] = str(lap)
        self._wear_text = str(int(tyre_wear_limit_pct * 100))
        self._buffer_text = str(pit_buffer_laps)
        self._voice_strategy = voice_alert_strategy
        self._active_field = None
        self._cursor_timer = 0
        self._cursor_visible = True
        self.active = True

    def handle_event(self, event: pygame.event.Event) -> Action:
        if not self.active:
            return None

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                return self._save()
            if event.key == pygame.K_ESCAPE:
                self.active = False
                return "cancelled"
            if event.key == pygame.K_TAB:
                self._cycle_focus()
                return None
            if event.key == pygame.K_BACKSPACE:
                self._backspace_active()
            elif event.unicode in _ALLOWED_DIGITS:
                self._type_char(event.unicode)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self._btn_save.collidepoint(pos):
                return self._save()
            if self._btn_cancel.collidepoint(pos):
                self.active = False
                return "cancelled"
            if self._btn_clear.collidepoint(pos):
                self._clear()
                return "saved"
            for i, btn in enumerate(self._stop_btns):
                if btn.collidepoint(pos):
                    self._planned_stops = i
                    return None
            for i, field in enumerate(self._lap_fields):
                if field.collidepoint(pos) and i < self._planned_stops:
                    self._active_field = f"lap{i}"
                    return None
            if self._wear_field.collidepoint(pos):
                self._active_field = "wear"
                return None
            if self._buffer_field.collidepoint(pos):
                self._active_field = "buffer"
                return None
            if self._voice_chk.collidepoint(pos):
                self._voice_strategy = not self._voice_strategy
                return None
            if not self._card.collidepoint(pos):
                self.active = False
                return "cancelled"

        return None

    def draw(self, screen: pygame.Surface, font_md: pygame.font.Font,
             font_sm: pygame.font.Font, dt_ms: int) -> None:
        if not self.active:
            return

        self._cursor_timer += dt_ms
        if self._cursor_timer >= 500:
            self._cursor_timer = 0
            self._cursor_visible = not self._cursor_visible

        overlay = pygame.Surface((self._win_w, self._win_h), pygame.SRCALPHA)
        overlay.fill(C_OVERLAY)
        screen.blit(overlay, (0, 0))

        pygame.draw.rect(screen, C_CARD, self._card, border_radius=10)
        pygame.draw.rect(screen, C_BORDER, self._card, 1, border_radius=10)

        title = font_md.render("Race Strategy", True, C_TEXT)
        screen.blit(title, (self._card.x + 20, self._card.y + 18))
        pygame.draw.line(screen, C_BORDER,
                         (self._card.x + 1, self._card.y + 52),
                         (self._card.right - 1, self._card.y + 52))

        fx = self._card.x + 20
        fy = self._card.y + 70

        # Stops count
        stops_lbl = font_sm.render("Planned pit stops", True, C_DIM)
        screen.blit(stops_lbl, (fx, fy - 18))
        for i, btn in enumerate(self._stop_btns):
            active = self._planned_stops == i
            bg = C_ACCENT if active else C_INPUT_BG
            pygame.draw.rect(screen, bg, btn, border_radius=5)
            pygame.draw.rect(screen, C_ACCENT if active else C_BORDER, btn, 1, border_radius=5)
            surf = font_sm.render(str(i), True, (15, 15, 22) if active else C_TEXT)
            screen.blit(surf, surf.get_rect(center=btn.center))

        # Lap inputs
        for i, field in enumerate(self._lap_fields):
            enabled = i < self._planned_stops
            lbl = font_sm.render(f"Stop {i + 1} — Lap:", True, C_TEXT if enabled else C_DIM)
            screen.blit(lbl, (fx, field.y + (field.height - font_sm.get_height()) // 2))
            if enabled:
                bg = C_INPUT_ACTIVE if self._active_field == f"lap{i}" else C_INPUT_BG
                border = C_ACCENT if self._active_field == f"lap{i}" else C_BORDER
                pygame.draw.rect(screen, bg, field, border_radius=5)
                pygame.draw.rect(screen, border, field, 1, border_radius=5)
                cursor = "|" if (self._active_field == f"lap{i}" and self._cursor_visible) else ""
                surf = font_sm.render(self._lap_texts[i] + cursor, True, C_TEXT)
                screen.blit(surf, (field.x + 8, field.y + (field.height - surf.get_height()) // 2))
            else:
                pygame.draw.rect(screen, (20, 20, 28), field, border_radius=5)
                pygame.draw.rect(screen, (40, 40, 50), field, 1, border_radius=5)

        # Separator
        sep_y = fy + 170
        pygame.draw.line(screen, C_BORDER, (self._card.x + 20, sep_y), (self._card.right - 20, sep_y))

        # Tyre wear limit
        wear_y = sep_y + 20
        wear_lbl = font_sm.render("Tyre wear limit:", True, C_DIM)
        screen.blit(wear_lbl, (fx, wear_y + (self._wear_field.height - font_sm.get_height()) // 2))
        wear_unit = font_sm.render("%", True, C_DIM)
        screen.blit(wear_unit, (self._wear_field.right + 6, wear_y + (self._wear_field.height - wear_unit.get_height()) // 2))
        wear_bg = C_INPUT_ACTIVE if self._active_field == "wear" else C_INPUT_BG
        wear_border = C_ACCENT if self._active_field == "wear" else C_BORDER
        pygame.draw.rect(screen, wear_bg, self._wear_field, border_radius=5)
        pygame.draw.rect(screen, wear_border, self._wear_field, 1, border_radius=5)
        wear_cursor = "|" if (self._active_field == "wear" and self._cursor_visible) else ""
        surf = font_sm.render(self._wear_text + wear_cursor, True, C_TEXT)
        screen.blit(surf, (self._wear_field.x + 6, self._wear_field.y + (self._wear_field.height - surf.get_height()) // 2))

        # Pit buffer
        buf_y = wear_y + 50
        buf_lbl = font_sm.render("Pit buffer:", True, C_DIM)
        screen.blit(buf_lbl, (fx, buf_y + (self._buffer_field.height - font_sm.get_height()) // 2))
        buf_unit = font_sm.render("laps", True, C_DIM)
        screen.blit(buf_unit, (self._buffer_field.right + 6, buf_y + (self._buffer_field.height - buf_unit.get_height()) // 2))
        buf_bg = C_INPUT_ACTIVE if self._active_field == "buffer" else C_INPUT_BG
        buf_border = C_ACCENT if self._active_field == "buffer" else C_BORDER
        pygame.draw.rect(screen, buf_bg, self._buffer_field, border_radius=5)
        pygame.draw.rect(screen, buf_border, self._buffer_field, 1, border_radius=5)
        buf_cursor = "|" if (self._active_field == "buffer" and self._cursor_visible) else ""
        surf = font_sm.render(self._buffer_text + buf_cursor, True, C_TEXT)
        screen.blit(surf, (self._buffer_field.x + 6, self._buffer_field.y + (self._buffer_field.height - surf.get_height()) // 2))

        # Voice strategy checkbox
        pygame.draw.rect(screen, C_INPUT_BG, self._voice_chk, border_radius=3)
        pygame.draw.rect(screen, C_ACCENT, self._voice_chk, 1, border_radius=3)
        if self._voice_strategy:
            inner = self._voice_chk.inflate(-5, -5)
            pygame.draw.rect(screen, C_ACCENT, inner, border_radius=2)
        chk_lbl = font_sm.render("Voice strategy alerts", True, C_TEXT)
        screen.blit(chk_lbl, (self._voice_chk.right + 10,
                               self._voice_chk.y + (self._voice_chk.height - chk_lbl.get_height()) // 2))

        # Buttons
        mouse = pygame.mouse.get_pos()
        self._draw_btn(screen, font_sm, self._btn_save, "Save",
                       C_BTN_SAVE if not self._btn_save.collidepoint(mouse) else C_BTN_HOVER)
        self._draw_btn(screen, font_sm, self._btn_clear, "Clear Strategy",
                       C_BTN_CLEAR if not self._btn_clear.collidepoint(mouse) else (120, 60, 60))
        self._draw_btn(screen, font_sm, self._btn_cancel, "Cancel",
                       C_BTN_CANCEL if not self._btn_cancel.collidepoint(mouse) else (80, 80, 95))

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def planned_stops(self) -> int:
        return self._planned_stops

    @property
    def planned_stop_laps(self) -> list[int]:
        laps = []
        for i in range(self._planned_stops):
            try:
                laps.append(int(self._lap_texts[i]))
            except ValueError:
                pass
        return laps

    @property
    def tyre_wear_limit_pct(self) -> float:
        try:
            v = int(self._wear_text)
            return max(50, min(100, v)) / 100.0
        except ValueError:
            return 0.80

    @property
    def pit_buffer_laps(self) -> int:
        try:
            return max(0, min(5, int(self._buffer_text)))
        except ValueError:
            return 1

    @property
    def voice_alert_strategy(self) -> bool:
        return self._voice_strategy

    # ── Private helpers ───────────────────────────────────────────────────────

    def _save(self) -> Action:
        self.active = False
        return "saved"

    def _clear(self) -> None:
        self._planned_stops = 0
        self._lap_texts = ["", "", ""]
        self.active = False

    def _cycle_focus(self) -> None:
        fields = [f"lap{i}" for i in range(self._planned_stops)] + ["wear", "buffer"]
        if not fields:
            return
        current = self._active_field
        if current is None or current not in fields:
            self._active_field = fields[0]
            return
        idx = fields.index(current)
        self._active_field = fields[(idx + 1) % len(fields)]

    def _backspace_active(self) -> None:
        if self._active_field is None:
            return
        if self._active_field.startswith("lap"):
            i = int(self._active_field[3])
            self._lap_texts[i] = self._lap_texts[i][:-1]
        elif self._active_field == "wear":
            self._wear_text = self._wear_text[:-1]
        elif self._active_field == "buffer":
            self._buffer_text = self._buffer_text[:-1]

    def _type_char(self, ch: str) -> None:
        if self._active_field is None:
            return
        if self._active_field.startswith("lap"):
            i = int(self._active_field[3])
            candidate = self._lap_texts[i] + ch
            if int(candidate) <= _MAX_LAP and len(candidate) <= 3:
                self._lap_texts[i] = candidate
        elif self._active_field == "wear":
            candidate = self._wear_text + ch
            if len(candidate) <= 3:
                self._wear_text = candidate
        elif self._active_field == "buffer":
            candidate = self._buffer_text + ch
            if len(candidate) <= 1:
                self._buffer_text = candidate

    def _draw_btn(self, screen, font, rect: pygame.Rect, text: str, color: tuple) -> None:
        pygame.draw.rect(screen, color, rect, border_radius=6)
        pygame.draw.rect(screen, C_BORDER, rect, 1, border_radius=6)
        surf = font.render(text, True, C_TEXT)
        screen.blit(surf, surf.get_rect(center=rect.center))
