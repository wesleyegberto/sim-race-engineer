"""Small modal for editing the session recording suffix."""

import pygame

C_OVERLAY     = (0, 0, 0, 160)
C_CARD        = (28, 28, 36)
C_BORDER      = (60, 60, 75)
C_TEXT        = (230, 230, 230)
C_DIM         = (120, 120, 135)
C_ACCENT      = (80, 140, 220)
C_INPUT_BG    = (18, 18, 24)
C_INPUT_ACTIVE = (40, 60, 100)
C_BTN_SAVE    = (60, 120, 200)
C_BTN_CANCEL  = (55, 55, 68)
C_BTN_HOVER   = (80, 140, 220)

_CARD_W, _CARD_H = 360, 200
_MAX_LEN = 30
_ALLOWED = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")


class SuffixInputPanel:
    def __init__(self, win_w: int, win_h: int) -> None:
        self._win_w = win_w
        self._win_h = win_h
        self.active = False
        self._text = ""
        self._cursor_visible = True
        self._cursor_timer = 0
        self._hover_save = False
        self._hover_cancel = False

        cx = (win_w - _CARD_W) // 2
        cy = (win_h - _CARD_H) // 2
        self._card = pygame.Rect(cx, cy, _CARD_W, _CARD_H)

        field_x = cx + 20
        field_y = cy + 82
        self._field = pygame.Rect(field_x, field_y, _CARD_W - 40, 36)

        btn_y = cy + _CARD_H - 52
        self._btn_save   = pygame.Rect(cx + _CARD_W - 210, btn_y, 90, 34)
        self._btn_cancel = pygame.Rect(cx + _CARD_W - 110, btn_y, 90, 34)

        self._overlay = pygame.Surface((win_w, win_h), pygame.SRCALPHA)
        self._overlay.fill(C_OVERLAY)

    def open(self, current_suffix: str) -> None:
        self._text = current_suffix
        self.active = True
        self._cursor_visible = True
        self._cursor_timer = 0
        self._hover_save = False
        self._hover_cancel = False

    def handle_event(self, event: pygame.event.Event) -> str | None:
        """Return confirmed suffix string on save, None otherwise."""
        if not self.active:
            return None

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.active = False
                return self._text
            if event.key == pygame.K_ESCAPE:
                self.active = False
                return None
            if event.key == pygame.K_BACKSPACE:
                self._text = self._text[:-1]
            elif event.unicode == " ":
                if len(self._text) < _MAX_LEN:
                    self._text += "_"
            elif event.unicode in _ALLOWED and len(self._text) < _MAX_LEN:
                self._text += event.unicode

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._btn_save.collidepoint(event.pos):
                self.active = False
                return self._text
            if self._btn_cancel.collidepoint(event.pos):
                self.active = False
                return None
            if not self._card.collidepoint(event.pos):
                self.active = False
                return None

        elif event.type == pygame.MOUSEMOTION:
            self._hover_save   = self._btn_save.collidepoint(event.pos)
            self._hover_cancel = self._btn_cancel.collidepoint(event.pos)

        return None

    def update(self) -> None:
        if not self.active:
            return
        self._cursor_timer += 1
        if self._cursor_timer >= 30:
            self._cursor_timer = 0
            self._cursor_visible = not self._cursor_visible

    def draw(self, screen: pygame.Surface, font_md: pygame.font.Font, font_sm: pygame.font.Font) -> None:
        if not self.active:
            return

        screen.blit(self._overlay, (0, 0))
        pygame.draw.rect(screen, C_CARD, self._card, border_radius=10)
        pygame.draw.rect(screen, C_BORDER, self._card, width=1, border_radius=10)

        cx = self._card.x
        cy = self._card.y

        title = font_md.render("Session Suffix", True, C_TEXT)
        screen.blit(title, (cx + 20, cy + 18))

        hint1 = font_sm.render("Letters, digits, _ and - only.", True, C_DIM)
        hint2 = font_sm.render("Leave blank for no suffix.", True, C_DIM)
        screen.blit(hint1, (cx + 20, cy + 44))
        screen.blit(hint2, (cx + 20, cy + 60))

        pygame.draw.rect(screen, C_INPUT_ACTIVE, self._field, border_radius=6)
        display = self._text + ("|" if self._cursor_visible else "")
        txt_surf = font_md.render(display, True, C_TEXT)
        screen.blit(txt_surf, txt_surf.get_rect(midleft=(self._field.x + 8, self._field.centery)))

        save_bg = C_BTN_HOVER if self._hover_save else C_BTN_SAVE
        pygame.draw.rect(screen, save_bg, self._btn_save, border_radius=6)
        save_lbl = font_sm.render("Save", True, C_TEXT)
        screen.blit(save_lbl, save_lbl.get_rect(center=self._btn_save.center))

        cancel_bg = C_BTN_HOVER if self._hover_cancel else C_BTN_CANCEL
        pygame.draw.rect(screen, cancel_bg, self._btn_cancel, border_radius=6)
        cancel_lbl = font_sm.render("Cancel", True, C_TEXT)
        screen.blit(cancel_lbl, cancel_lbl.get_rect(center=self._btn_cancel.center))
        if self._hover_save or self._hover_cancel:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
