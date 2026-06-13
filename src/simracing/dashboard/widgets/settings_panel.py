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

_CARD_W, _CARD_H = 480, 620
_ALLOWED_CHARS = set("0123456789.")

Action = Literal["saved", "cancelled", "test_voice"] | None


class SettingsPanel:
    def __init__(self, win_w: int, win_h: int) -> None:
        self._win_w = win_w
        self._win_h = win_h
        self.active = False
        self._ip_text = ""
        self._rpm_flash = True
        self._fuel_estimation = "average"
        self._voice_enabled = False
        self._voice_language = "en"
        self._voice_alert_fuel_critical = True
        self._voice_alert_fuel_low = True
        self._voice_alert_lap_completed = True
        self._voice_alert_best_lap = True
        self._voice_alert_final_lap = True
        self._voice_alert_engine_temp = True
        self._voice_alert_tire_temp = True
        self._voice_alert_tire_inner_temp = True
        self._voice_alert_oil_temp = True
        self._voice_alert_tire_pressure = True
        self._voice_alert_lap_delta = True
        self._voice_alert_pit_window = True
        self._cursor_visible = True
        self._cursor_timer = 0

        cx = (win_w - _CARD_W) // 2
        cy = (win_h - _CARD_H) // 2
        self._card = pygame.Rect(cx, cy, _CARD_W, _CARD_H)

        field_x = cx + 20
        field_y = cy + 90
        self._field = pygame.Rect(field_x, field_y, _CARD_W - 40, 38)

        check_y = field_y + 58
        self._check_box = pygame.Rect(field_x, check_y, 18, 18)

        fuel_y = check_y + 44
        self._fuel_btn_last = pygame.Rect(field_x, fuel_y, 130, 30)
        self._fuel_btn_avg = pygame.Rect(field_x + 140, fuel_y, 130, 30)

        # Voice section
        voice_check_y = fuel_y + 66
        self._voice_check_box = pygame.Rect(field_x, voice_check_y, 18, 18)
        self._voice_sep_y = fuel_y + 48

        voice_lang_y = voice_check_y + 44
        self._voice_btn_en = pygame.Rect(field_x, voice_lang_y, 90, 30)
        self._voice_btn_pt = pygame.Rect(field_x + 100, voice_lang_y, 90, 30)
        self._voice_btn_test = pygame.Rect(field_x + 210, voice_lang_y, 110, 30)

        self._voice_restart_note_y = voice_lang_y + 38

        alerts_y = self._voice_restart_note_y + 30
        self._voice_alerts_sep_y = alerts_y
        col2_x = field_x + 220
        self._voice_chk_fuel_low      = pygame.Rect(field_x, alerts_y + 22, 18, 18)
        self._voice_chk_fuel_critical = pygame.Rect(col2_x,  alerts_y + 22, 18, 18)
        self._voice_chk_lap_completed = pygame.Rect(field_x, alerts_y + 48, 18, 18)
        self._voice_chk_best_lap      = pygame.Rect(col2_x,  alerts_y + 48, 18, 18)
        self._voice_chk_final_lap     = pygame.Rect(field_x, alerts_y + 74, 18, 18)
        self._voice_chk_engine_temp   = pygame.Rect(col2_x,  alerts_y + 74, 18, 18)
        self._voice_chk_tire_temp       = pygame.Rect(field_x, alerts_y + 100, 18, 18)
        self._voice_chk_tire_inner_temp = pygame.Rect(col2_x,  alerts_y + 100, 18, 18)
        self._voice_chk_oil_temp        = pygame.Rect(field_x, alerts_y + 126, 18, 18)
        self._voice_chk_tire_pressure   = pygame.Rect(col2_x,  alerts_y + 126, 18, 18)
        self._voice_chk_lap_delta       = pygame.Rect(field_x, alerts_y + 152, 18, 18)
        self._voice_chk_pit_window      = pygame.Rect(col2_x,  alerts_y + 152, 18, 18)

        btn_y = cy + _CARD_H - 56
        self._btn_save = pygame.Rect(cx + _CARD_W - 210, btn_y, 90, 36)
        self._btn_cancel = pygame.Rect(cx + _CARD_W - 110, btn_y, 90, 36)

    def open(
        self,
        current_ip: str,
        rpm_flash: bool = True,
        fuel_estimation: str = "average",
        voice_enabled: bool = False,
        voice_language: str = "en",
        voice_alert_fuel_critical: bool = True,
        voice_alert_fuel_low: bool = True,
        voice_alert_lap_completed: bool = True,
        voice_alert_best_lap: bool = True,
        voice_alert_final_lap: bool = True,
        voice_alert_engine_temp: bool = True,
        voice_alert_tire_temp: bool = True,
        voice_alert_tire_inner_temp: bool = True,
        voice_alert_oil_temp: bool = True,
        voice_alert_tire_pressure: bool = True,
        voice_alert_lap_delta: bool = True,
        voice_alert_pit_window: bool = True,
    ) -> None:
        self._ip_text = current_ip
        self._rpm_flash = rpm_flash
        self._fuel_estimation = fuel_estimation
        self._voice_enabled = voice_enabled
        self._voice_language = voice_language
        self._voice_alert_fuel_critical = voice_alert_fuel_critical
        self._voice_alert_fuel_low = voice_alert_fuel_low
        self._voice_alert_lap_completed = voice_alert_lap_completed
        self._voice_alert_best_lap = voice_alert_best_lap
        self._voice_alert_final_lap = voice_alert_final_lap
        self._voice_alert_engine_temp = voice_alert_engine_temp
        self._voice_alert_tire_temp = voice_alert_tire_temp
        self._voice_alert_tire_inner_temp = voice_alert_tire_inner_temp
        self._voice_alert_oil_temp = voice_alert_oil_temp
        self._voice_alert_tire_pressure = voice_alert_tire_pressure
        self._voice_alert_lap_delta = voice_alert_lap_delta
        self._voice_alert_pit_window = voice_alert_pit_window
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
            if self._check_box.collidepoint(pos):
                self._rpm_flash = not self._rpm_flash
                return None
            if self._fuel_btn_last.collidepoint(pos):
                self._fuel_estimation = "last"
                return None
            if self._fuel_btn_avg.collidepoint(pos):
                self._fuel_estimation = "average"
                return None
            if self._voice_check_box.collidepoint(pos):
                self._voice_enabled = not self._voice_enabled
                return None
            if self._voice_btn_en.collidepoint(pos):
                self._voice_language = "en"
                return None
            if self._voice_btn_pt.collidepoint(pos):
                self._voice_language = "pt"
                return None
            if self._voice_btn_test.collidepoint(pos) and self._voice_enabled:
                return "test_voice"
            for chk, attr in (
                (self._voice_chk_fuel_low,      "_voice_alert_fuel_low"),
                (self._voice_chk_fuel_critical, "_voice_alert_fuel_critical"),
                (self._voice_chk_lap_completed, "_voice_alert_lap_completed"),
                (self._voice_chk_best_lap,      "_voice_alert_best_lap"),
                (self._voice_chk_final_lap,     "_voice_alert_final_lap"),
                (self._voice_chk_engine_temp,   "_voice_alert_engine_temp"),
                (self._voice_chk_tire_temp,       "_voice_alert_tire_temp"),
                (self._voice_chk_tire_inner_temp, "_voice_alert_tire_inner_temp"),
                (self._voice_chk_oil_temp,        "_voice_alert_oil_temp"),
                (self._voice_chk_tire_pressure,   "_voice_alert_tire_pressure"),
                (self._voice_chk_lap_delta,       "_voice_alert_lap_delta"),
                (self._voice_chk_pit_window,      "_voice_alert_pit_window"),
            ):
                if chk.collidepoint(pos) and self._voice_enabled:
                    setattr(self, attr, not getattr(self, attr))
                    return None
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

        # Device IP
        lbl = font_sm.render("Device IP  (PS5 or PC)", True, C_DIM)
        screen.blit(lbl, (self._field.x, self._field.y - 20))
        pygame.draw.rect(screen, C_INPUT_ACTIVE, self._field, border_radius=6)
        pygame.draw.rect(screen, C_ACCENT, self._field, 1, border_radius=6)
        display = self._ip_text + ("|" if self._cursor_visible else " ")
        ip_surf = font_md.render(display, True, C_TEXT)
        screen.blit(ip_surf, (self._field.x + 10, self._field.y + 8))

        # RPM flash checkbox
        pygame.draw.rect(screen, C_INPUT_BG, self._check_box, border_radius=3)
        pygame.draw.rect(screen, C_ACCENT, self._check_box, 1, border_radius=3)
        if self._rpm_flash:
            inner = self._check_box.inflate(-5, -5)
            pygame.draw.rect(screen, C_ACCENT, inner, border_radius=2)
        check_lbl = font_sm.render("Flash screen at rev limiter", True, C_TEXT)
        screen.blit(check_lbl, (self._check_box.right + 10,
                                self._check_box.y + (self._check_box.height - check_lbl.get_height()) // 2))

        # Fuel estimation mode
        fuel_lbl = font_sm.render("Fuel/Lap estimation", True, C_DIM)
        screen.blit(fuel_lbl, (self._fuel_btn_last.x, self._fuel_btn_last.y - 18))
        for btn, mode, label in (
            (self._fuel_btn_last, "last", "Last lap"),
            (self._fuel_btn_avg, "average", "Average"),
        ):
            active = self._fuel_estimation == mode
            bg = C_ACCENT if active else C_INPUT_BG
            border = C_ACCENT if active else C_BORDER
            pygame.draw.rect(screen, bg, btn, border_radius=6)
            pygame.draw.rect(screen, border, btn, 1, border_radius=6)
            txt_color = (15, 15, 22) if active else C_TEXT
            surf = font_sm.render(label, True, txt_color)
            screen.blit(surf, surf.get_rect(center=btn.center))

        # Voice section separator
        pygame.draw.line(screen, C_BORDER,
                         (self._card.x + 1, self._voice_sep_y),
                         (self._card.right - 1, self._voice_sep_y))

        # Voice enabled checkbox
        pygame.draw.rect(screen, C_INPUT_BG, self._voice_check_box, border_radius=3)
        pygame.draw.rect(screen, C_ACCENT, self._voice_check_box, 1, border_radius=3)
        if self._voice_enabled:
            inner = self._voice_check_box.inflate(-5, -5)
            pygame.draw.rect(screen, C_ACCENT, inner, border_radius=2)
        voice_lbl = font_sm.render("Enable voice alerts", True, C_TEXT)
        screen.blit(voice_lbl, (self._voice_check_box.right + 10,
                                self._voice_check_box.y + (self._voice_check_box.height - voice_lbl.get_height()) // 2))

        # Language buttons (dimmed when voice disabled)
        lang_color = C_DIM if not self._voice_enabled else C_DIM
        lang_lbl = font_sm.render("Language", True, lang_color)
        screen.blit(lang_lbl, (self._voice_btn_en.x, self._voice_btn_en.y - 18))
        for btn, code, label in (
            (self._voice_btn_en, "en", "English"),
            (self._voice_btn_pt, "pt", "Português"),
        ):
            active = self._voice_language == code and self._voice_enabled
            bg = C_ACCENT if active else C_INPUT_BG
            border = C_ACCENT if active else C_BORDER
            alpha_color = bg if self._voice_enabled else (30, 30, 40)
            pygame.draw.rect(screen, alpha_color, btn, border_radius=6)
            pygame.draw.rect(screen, border if self._voice_enabled else (45, 45, 55), btn, 1, border_radius=6)
            txt_color = (15, 15, 22) if active else (C_TEXT if self._voice_enabled else C_DIM)
            surf = font_sm.render(label, True, txt_color)
            screen.blit(surf, surf.get_rect(center=btn.center))

        # Test voice button
        test_bg = (50, 100, 60) if self._voice_enabled else (30, 30, 40)
        test_border = (80, 160, 90) if self._voice_enabled else (45, 45, 55)
        test_txt = C_TEXT if self._voice_enabled else C_DIM
        pygame.draw.rect(screen, test_bg, self._voice_btn_test, border_radius=6)
        pygame.draw.rect(screen, test_border, self._voice_btn_test, 1, border_radius=6)
        surf = font_sm.render("Test Voice", True, test_txt)
        screen.blit(surf, surf.get_rect(center=self._voice_btn_test.center))

        # Restart note
        note_color = (180, 130, 60) if self._voice_enabled else C_DIM
        note = font_sm.render("* Language change requires app restart", True, note_color)
        screen.blit(note, (self._voice_btn_en.x, self._voice_restart_note_y))

        # Alert events section
        pygame.draw.line(screen, C_BORDER,
                         (self._card.x + 1, self._voice_alerts_sep_y),
                         (self._card.right - 1, self._voice_alerts_sep_y))
        alerts_lbl = font_sm.render("Alert events", True, C_DIM if not self._voice_enabled else C_DIM)
        screen.blit(alerts_lbl, (self._voice_chk_fuel_low.x, self._voice_alerts_sep_y + 6))

        for chk, checked, label in (
            (self._voice_chk_fuel_low,      self._voice_alert_fuel_low,      "Fuel low"),
            (self._voice_chk_fuel_critical, self._voice_alert_fuel_critical, "Fuel critical"),
            (self._voice_chk_lap_completed, self._voice_alert_lap_completed, "Lap completed"),
            (self._voice_chk_best_lap,      self._voice_alert_best_lap,      "Best lap"),
            (self._voice_chk_final_lap,     self._voice_alert_final_lap,     "Final lap"),
            (self._voice_chk_engine_temp,   self._voice_alert_engine_temp,   "Engine temp"),
            (self._voice_chk_tire_temp,       self._voice_alert_tire_temp,       "Tyre temp"),
            (self._voice_chk_tire_inner_temp, self._voice_alert_tire_inner_temp, "Tyre wear"),
            (self._voice_chk_oil_temp,        self._voice_alert_oil_temp,        "Oil temp"),
            (self._voice_chk_tire_pressure,   self._voice_alert_tire_pressure,   "Tyre pres."),
            (self._voice_chk_lap_delta,       self._voice_alert_lap_delta,       "Lap delta"),
            (self._voice_chk_pit_window,      self._voice_alert_pit_window,      "Pit window"),
        ):
            enabled = self._voice_enabled
            pygame.draw.rect(screen, C_INPUT_BG, chk, border_radius=3)
            pygame.draw.rect(screen, C_ACCENT if enabled else (45, 45, 55), chk, 1, border_radius=3)
            if checked and enabled:
                inner = chk.inflate(-5, -5)
                pygame.draw.rect(screen, C_ACCENT, inner, border_radius=2)
            txt_color = C_TEXT if enabled else C_DIM
            surf = font_sm.render(label, True, txt_color)
            screen.blit(surf, (chk.right + 10, chk.y + (chk.height - surf.get_height()) // 2))

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

    @property
    def rpm_flash(self) -> bool:
        return self._rpm_flash

    @property
    def fuel_estimation(self) -> str:
        return self._fuel_estimation

    @property
    def voice_enabled(self) -> bool:
        return self._voice_enabled

    @property
    def voice_language(self) -> str:
        return self._voice_language

    @property
    def voice_alert_fuel_critical(self) -> bool:
        return self._voice_alert_fuel_critical

    @property
    def voice_alert_fuel_low(self) -> bool:
        return self._voice_alert_fuel_low

    @property
    def voice_alert_lap_completed(self) -> bool:
        return self._voice_alert_lap_completed

    @property
    def voice_alert_best_lap(self) -> bool:
        return self._voice_alert_best_lap

    @property
    def voice_alert_final_lap(self) -> bool:
        return self._voice_alert_final_lap

    @property
    def voice_alert_engine_temp(self) -> bool:
        return self._voice_alert_engine_temp

    @property
    def voice_alert_tire_temp(self) -> bool:
        return self._voice_alert_tire_temp

    @property
    def voice_alert_tire_inner_temp(self) -> bool:
        return self._voice_alert_tire_inner_temp

    @property
    def voice_alert_oil_temp(self) -> bool:
        return self._voice_alert_oil_temp

    @property
    def voice_alert_tire_pressure(self) -> bool:
        return self._voice_alert_tire_pressure

    @property
    def voice_alert_lap_delta(self) -> bool:
        return self._voice_alert_lap_delta

    @property
    def voice_alert_pit_window(self) -> bool:
        return self._voice_alert_pit_window
