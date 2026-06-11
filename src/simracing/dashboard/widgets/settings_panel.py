"""Settings overlay modal."""

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

_CARD_W, _CARD_H = 480, 210
_ALLOWED_CHARS = set("0123456789.")

Action = Literal["saved", "cancelled"] | None


class SettingsPanel:
    def __init__(self, win_w: int, win_h: int) -> None:
        self._win_w = win_w
        self._win_h = win_h
        self.active = False
        self._ip_text = ""
        self._cursor_visible = True
        self._cursor_timer = 0

        cx = (win_w - _CARD_W) // 2
        cy = (win_h - _CARD_H) // 2
        self._card = pygame.Rect(cx, cy, _CARD_W, _CARD_H)

        field_x = cx + 20
        field_y = cy + 90
        self._field = pygame.Rect(field_x, field_y, _CARD_W - 40, 38)

        btn_y = cy + _CARD_H - 56
        self._btn_save = pygame.Rect(cx + _CARD_W - 210, btn_y, 90, 36)
        self._btn_cancel = pygame.Rect(cx + _CARD_W - 110, btn_y, 90, 36)

    def open(self, current_ip: str) -> None:
        self._ip_text = current_ip
        self.active = True
        self._cursor_timer = 0
        self._cursor_visible = True

    def handle_event(self, event: pygame.event.Event) -> Action:
        if not self.active:
            return None

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                return self._save()
            if event.key == pygame.K_ESCAPE:
                self.active = False
                return "cancelled"
            if event.key == pygame.K_BACKSPACE:
                self._ip_text = self._ip_text[:-1]
            elif event.unicode in _ALLOWED_CHARS and len(self._ip_text) < 15:
                self._ip_text += event.unicode

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self._btn_save.collidepoint(pos):
                return self._save()
            if self._btn_cancel.collidepoint(pos):
                self.active = False
                return "cancelled"
            if not self._card.collidepoint(pos):
                self.active = False
                return "cancelled"

        return None

    def draw(self, screen: pygame.Surface, font_md: pygame.font.Font,
             font_sm: pygame.font.Font, dt_ms: int) -> None:
        if not self.active:
            return

        # Cursor blink
        self._cursor_timer += dt_ms
        if self._cursor_timer >= 500:
            self._cursor_timer = 0
            self._cursor_visible = not self._cursor_visible

        # Semi-transparent overlay
        overlay = pygame.Surface((self._win_w, self._win_h), pygame.SRCALPHA)
        overlay.fill(C_OVERLAY)
        screen.blit(overlay, (0, 0))

        # Card
        pygame.draw.rect(screen, C_CARD, self._card, border_radius=10)
        pygame.draw.rect(screen, C_BORDER, self._card, 1, border_radius=10)

        # Title
        title = font_md.render("Settings", True, C_TEXT)
        screen.blit(title, (self._card.x + 20, self._card.y + 18))
        pygame.draw.line(screen, C_BORDER,
                         (self._card.x + 1, self._card.y + 52),
                         (self._card.right - 1, self._card.y + 52))

        # Label
        lbl = font_sm.render("Device IP  (PS5 or PC)", True, C_DIM)
        screen.blit(lbl, (self._field.x, self._field.y - 20))

        # Input field
        pygame.draw.rect(screen, C_INPUT_ACTIVE, self._field, border_radius=6)
        pygame.draw.rect(screen, C_ACCENT, self._field, 1, border_radius=6)

        display = self._ip_text + ("|" if self._cursor_visible else " ")
        ip_surf = font_md.render(display, True, C_TEXT)
        screen.blit(ip_surf, (self._field.x + 10, self._field.y + 8))

        # Buttons
        mouse = pygame.mouse.get_pos()
        self._draw_btn(screen, font_sm, self._btn_save, "Save",
                       C_BTN_SAVE if not self._btn_save.collidepoint(mouse) else C_BTN_HOVER)
        self._draw_btn(screen, font_sm, self._btn_cancel, "Cancel",
                       C_BTN_CANCEL if not self._btn_cancel.collidepoint(mouse) else (80, 80, 95))

    def _draw_btn(self, screen, font, rect: pygame.Rect, text: str, color: tuple) -> None:
        pygame.draw.rect(screen, color, rect, border_radius=6)
        pygame.draw.rect(screen, C_BORDER, rect, 1, border_radius=6)
        surf = font.render(text, True, C_TEXT)
        screen.blit(surf, surf.get_rect(center=rect.center))

    def _save(self) -> Action:
        self.active = False
        return "saved"

    @property
    def ip_text(self) -> str:
        return self._ip_text
