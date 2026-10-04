"""Settings overlay modal."""

from typing import Literal

import pygame

from ...microcontroller.serial_transport import list_serial_ports

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

_CARD_W, _CARD_H = 480, 994
_ALLOWED_CHARS = set("0123456789.")

Action = Literal["saved", "cancelled", "test_voice", "test_microcontroller"] | None


class SettingsPanel:
    def __init__(self, win_w: int, win_h: int, show_microcontroller: bool = False) -> None:
        self._show_micro = show_microcontroller
        self._win_w = win_w
        self._win_h = win_h
        self.active = False
        self._ip_text = ""
        self._fuel_estimation = "average"
        self._voice_enabled = False
        self._voice_language = "en"
        self._voice_alert_fuel_critical = True
        self._voice_alert_fuel_low = True
        self._voice_alert_lap_completed = True
        self._voice_alert_best_lap = True
        self._voice_alert_final_lap = True
        self._voice_alert_race_report = True
        self._voice_alert_engine_temp = True
        self._voice_alert_tire_temp = True
        self._voice_alert_tire_inner_temp = True
        self._voice_alert_oil_temp = True
        self._voice_alert_tire_pressure = True
        self._voice_alert_lap_delta = True
        self._voice_alert_pit_window = True
        self._voice_alert_tyre_wear = True
        self._voice_alert_overtake = True
        self._voice_alert_laps_to_finish = True
        self._voice_alert_fuel_save = True
        self._voice_alert_strategy_check_in = True
        self._voice_alert_strategy_revised = True
        self._voice_alert_fuel_save_recommend = True
        self._voice_alert_advisor_pit_window = True
        self._recording_on_start = True
        self._voice_wear_thr_text = "10"
        self._microcontroller_enabled = False
        self._microcontroller_port = ""
        self._fan_speed_ceiling_text = "220"
        self._fan_speed_ceiling_kmh = 220.0
        self._micro_test_result: bool | None = None
        self._active_field: str | None = None  # "ip" | "wear_thr" | "port" | "fan_ceiling"
        self._cursor_visible = True
        self._cursor_timer = 0

        cx = (win_w - _CARD_W) // 2
        cy = max(4, (win_h - _CARD_H) // 2)
        self._card = pygame.Rect(cx, cy, _CARD_W, _CARD_H)

        field_x = cx + 20
        field_y = cy + 90
        self._field = pygame.Rect(field_x, field_y, _CARD_W - 40, 38)

        # Recording on start checkbox (right below IP field)
        self._rec_on_start_check = pygame.Rect(field_x, field_y + 46, 18, 18)

        fuel_y = field_y + 84
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

        # ── Race group ────────────────────────────────────────────────────────
        self._voice_grp_race_lbl_y    = alerts_y + 24
        self._voice_chk_lap_completed    = pygame.Rect(field_x, alerts_y + 40, 18, 18)
        self._voice_chk_best_lap         = pygame.Rect(col2_x,  alerts_y + 40, 18, 18)
        self._voice_chk_final_lap        = pygame.Rect(field_x, alerts_y + 62, 18, 18)
        self._voice_chk_lap_delta        = pygame.Rect(col2_x,  alerts_y + 62, 18, 18)
        self._voice_chk_race_report      = pygame.Rect(field_x, alerts_y + 84, 18, 18)
        self._voice_chk_overtake         = pygame.Rect(col2_x,  alerts_y + 84, 18, 18)
        self._voice_chk_laps_to_finish   = pygame.Rect(field_x, alerts_y + 106, 18, 18)

        # ── Fuel & Pit group (shifted +22 to make room for laps_to_finish) ───
        self._voice_grp_fuel_sep_y    = alerts_y + 128
        self._voice_grp_fuel_lbl_y    = alerts_y + 134
        self._voice_chk_fuel_low      = pygame.Rect(field_x, alerts_y + 150, 18, 18)
        self._voice_chk_fuel_critical = pygame.Rect(col2_x,  alerts_y + 150, 18, 18)
        self._voice_chk_pit_window    = pygame.Rect(field_x, alerts_y + 172, 18, 18)
        self._voice_chk_fuel_save     = pygame.Rect(col2_x,  alerts_y + 172, 18, 18)

        # ── Car health group ──────────────────────────────────────────────────
        self._voice_grp_car_sep_y       = alerts_y + 194
        self._voice_grp_car_lbl_y       = alerts_y + 200
        self._voice_chk_engine_temp     = pygame.Rect(field_x, alerts_y + 216, 18, 18)
        self._voice_chk_oil_temp        = pygame.Rect(col2_x,  alerts_y + 216, 18, 18)
        self._voice_chk_tire_temp       = pygame.Rect(field_x, alerts_y + 238, 18, 18)
        self._voice_chk_tire_inner_temp = pygame.Rect(col2_x,  alerts_y + 238, 18, 18)
        self._voice_chk_tire_pressure   = pygame.Rect(field_x, alerts_y + 260, 18, 18)

        # ── Tyre wear (real field) ─────────────────────────────────────────────
        self._voice_grp_wear_sep_y    = alerts_y + 282
        self._voice_grp_wear_lbl_y    = alerts_y + 288
        self._voice_chk_tyre_wear     = pygame.Rect(field_x, alerts_y + 304, 18, 18)
        self._voice_wear_thr_field    = pygame.Rect(col2_x + 20, alerts_y + 302, 50, 22)

        # ── Strategy alerts group ──────────────────────────────────────────────
        self._voice_grp_strategy_sep_y = alerts_y + 330
        self._voice_grp_strategy_lbl_y = alerts_y + 336
        self._voice_chk_strategy_check_in   = pygame.Rect(field_x, alerts_y + 352, 18, 18)
        self._voice_chk_strategy_revised    = pygame.Rect(col2_x,  alerts_y + 352, 18, 18)
        self._voice_chk_fuel_save_recommend = pygame.Rect(field_x, alerts_y + 374, 18, 18)
        self._voice_chk_advisor_pit_window  = pygame.Rect(col2_x,  alerts_y + 374, 18, 18)

        # ── Airflow Simulation section ──────────────────────────────────────
        self._micro_sep_y = alerts_y + 404
        self._micro_lbl_y = self._micro_sep_y + 6
        micro_check_y = self._micro_lbl_y + 20
        self._micro_check_box = pygame.Rect(field_x, micro_check_y, 18, 18)
        self._micro_port_lbl_y = micro_check_y + 34
        micro_port_y = self._micro_port_lbl_y + 18
        self._micro_port_field = pygame.Rect(field_x, micro_port_y, 220, 34)
        self._micro_test_btn = pygame.Rect(field_x + 230, micro_port_y, 130, 34)
        self._micro_note_y = micro_port_y + 34 + 10

        # Label sits inline, to the left of the field
        fan_ceiling_y = self._micro_note_y + 22
        self._fan_ceiling_field = pygame.Rect(field_x + 130, fan_ceiling_y, 70, 26)

        # Buttons anchored right below the content; card height follows from them
        content_bottom = (self._fan_ceiling_field.bottom if show_microcontroller
                          else self._voice_chk_advisor_pit_window.bottom)
        btn_y = content_bottom + 16
        self._card.height = btn_y + 36 + 16 - cy
        self._btn_save = pygame.Rect(cx + _CARD_W - 210, btn_y, 90, 36)
        self._btn_cancel = pygame.Rect(cx + _CARD_W - 110, btn_y, 90, 36)

        # Pre-allocated overlay (never changes)
        self._overlay = pygame.Surface((win_w, win_h), pygame.SRCALPHA)
        self._overlay.fill(C_OVERLAY)

    def open(
        self,
        current_ip: str,
        fuel_estimation: str = "average",
        recording_on_start: bool = True,
        voice_enabled: bool = False,
        voice_language: str = "en",
        voice_alert_fuel_critical: bool = True,
        voice_alert_fuel_low: bool = True,
        voice_alert_lap_completed: bool = True,
        voice_alert_best_lap: bool = True,
        voice_alert_final_lap: bool = True,
        voice_alert_race_report: bool = True,
        voice_alert_engine_temp: bool = True,
        voice_alert_tire_temp: bool = True,
        voice_alert_tire_inner_temp: bool = True,
        voice_alert_oil_temp: bool = True,
        voice_alert_tire_pressure: bool = True,
        voice_alert_lap_delta: bool = True,
        voice_alert_pit_window: bool = True,
        voice_alert_tyre_wear: bool = True,
        voice_tyre_wear_threshold_pct: float = 0.10,
        voice_alert_overtake: bool = True,
        voice_alert_laps_to_finish: bool = True,
        voice_alert_fuel_save: bool = True,
        voice_alert_strategy_check_in: bool = True,
        voice_alert_strategy_revised: bool = True,
        voice_alert_fuel_save_recommend: bool = True,
        voice_alert_advisor_pit_window: bool = True,
        microcontroller_enabled: bool = False,
        microcontroller_port: str = "",
        fan_speed_ceiling_kmh: float = 220.0,
    ) -> None:
        self._ip_text = current_ip
        self._fuel_estimation = fuel_estimation
        self._recording_on_start = recording_on_start
        self._voice_enabled = voice_enabled
        self._voice_language = voice_language
        self._voice_alert_fuel_critical = voice_alert_fuel_critical
        self._voice_alert_fuel_low = voice_alert_fuel_low
        self._voice_alert_lap_completed = voice_alert_lap_completed
        self._voice_alert_best_lap = voice_alert_best_lap
        self._voice_alert_final_lap = voice_alert_final_lap
        self._voice_alert_race_report = voice_alert_race_report
        self._voice_alert_engine_temp = voice_alert_engine_temp
        self._voice_alert_tire_temp = voice_alert_tire_temp
        self._voice_alert_tire_inner_temp = voice_alert_tire_inner_temp
        self._voice_alert_oil_temp = voice_alert_oil_temp
        self._voice_alert_tire_pressure = voice_alert_tire_pressure
        self._voice_alert_lap_delta = voice_alert_lap_delta
        self._voice_alert_pit_window = voice_alert_pit_window
        self._voice_alert_tyre_wear = voice_alert_tyre_wear
        self._voice_wear_thr_text = str(int(voice_tyre_wear_threshold_pct * 100))
        self._voice_alert_overtake = voice_alert_overtake
        self._voice_alert_laps_to_finish = voice_alert_laps_to_finish
        self._voice_alert_fuel_save = voice_alert_fuel_save
        self._voice_alert_strategy_check_in = voice_alert_strategy_check_in
        self._voice_alert_strategy_revised = voice_alert_strategy_revised
        self._voice_alert_fuel_save_recommend = voice_alert_fuel_save_recommend
        self._voice_alert_advisor_pit_window = voice_alert_advisor_pit_window
        self._microcontroller_enabled = microcontroller_enabled
        self._microcontroller_port = microcontroller_port
        if self._microcontroller_enabled and not self._microcontroller_port:
            self._microcontroller_port = self._auto_detected_port() or ""
        self._fan_speed_ceiling_kmh = fan_speed_ceiling_kmh if fan_speed_ceiling_kmh > 0 else 220.0
        self._fan_speed_ceiling_text = str(int(self._fan_speed_ceiling_kmh))
        self._micro_test_result = None
        self.active = True
        self._active_field = None
        self._cursor_timer = 0
        self._cursor_visible = True

    def _auto_detected_port(self) -> str | None:
        candidates = list_serial_ports()
        return candidates[0] if len(candidates) == 1 else None

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
                if self._active_field == "wear_thr":
                    self._voice_wear_thr_text = self._voice_wear_thr_text[:-1]
                elif self._active_field == "port":
                    self._microcontroller_port = self._microcontroller_port[:-1]
                elif self._active_field == "fan_ceiling":
                    self._fan_speed_ceiling_text = self._fan_speed_ceiling_text[:-1]
                else:
                    self._ip_text = self._ip_text[:-1]
            elif self._active_field == "port":
                if event.unicode.isprintable() and len(self._microcontroller_port) < 40:
                    self._microcontroller_port += event.unicode
            elif self._active_field == "fan_ceiling":
                if event.unicode.isdigit() and len(self._fan_speed_ceiling_text) < 3:
                    self._fan_speed_ceiling_text += event.unicode
            elif event.unicode in _ALLOWED_CHARS:
                if self._active_field == "wear_thr" and event.unicode.isdigit() and len(self._voice_wear_thr_text) < 3:
                    self._voice_wear_thr_text += event.unicode
                elif self._active_field != "wear_thr" and len(self._ip_text) < 15:
                    self._ip_text += event.unicode

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self._btn_save.collidepoint(pos):
                return self._save()
            if self._btn_cancel.collidepoint(pos):
                self.active = False
                return "cancelled"
            if self._rec_on_start_check.collidepoint(pos):
                self._recording_on_start = not self._recording_on_start
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
            if self._voice_wear_thr_field.collidepoint(pos) and self._voice_enabled:
                self._active_field = "wear_thr"
                return None
            if self._show_micro and self._micro_check_box.collidepoint(pos):
                self._microcontroller_enabled = not self._microcontroller_enabled
                if self._microcontroller_enabled and not self._microcontroller_port:
                    self._microcontroller_port = self._auto_detected_port() or ""
                self._micro_test_result = None
                return None
            if self._show_micro and self._micro_port_field.collidepoint(pos) and self._microcontroller_enabled:
                self._active_field = "port"
                return None
            if self._show_micro and self._fan_ceiling_field.collidepoint(pos) and self._microcontroller_enabled:
                self._active_field = "fan_ceiling"
                return None
            if (self._show_micro and self._micro_test_btn.collidepoint(pos) and self._microcontroller_enabled
                    and self._microcontroller_port):
                return "test_microcontroller"
            if self._field.collidepoint(pos):
                self._active_field = "ip"
                return None
            for chk, attr in (
                (self._voice_chk_lap_completed,   "_voice_alert_lap_completed"),
                (self._voice_chk_best_lap,        "_voice_alert_best_lap"),
                (self._voice_chk_final_lap,       "_voice_alert_final_lap"),
                (self._voice_chk_lap_delta,       "_voice_alert_lap_delta"),
                (self._voice_chk_race_report,     "_voice_alert_race_report"),
                (self._voice_chk_fuel_low,        "_voice_alert_fuel_low"),
                (self._voice_chk_fuel_critical,   "_voice_alert_fuel_critical"),
                (self._voice_chk_pit_window,      "_voice_alert_pit_window"),
                (self._voice_chk_engine_temp,     "_voice_alert_engine_temp"),
                (self._voice_chk_oil_temp,        "_voice_alert_oil_temp"),
                (self._voice_chk_tire_temp,       "_voice_alert_tire_temp"),
                (self._voice_chk_tire_inner_temp, "_voice_alert_tire_inner_temp"),
                (self._voice_chk_tire_pressure,   "_voice_alert_tire_pressure"),
                (self._voice_chk_tyre_wear,         "_voice_alert_tyre_wear"),
                (self._voice_chk_overtake,          "_voice_alert_overtake"),
                (self._voice_chk_laps_to_finish,    "_voice_alert_laps_to_finish"),
                (self._voice_chk_fuel_save,         "_voice_alert_fuel_save"),
                (self._voice_chk_strategy_check_in,   "_voice_alert_strategy_check_in"),
                (self._voice_chk_strategy_revised,    "_voice_alert_strategy_revised"),
                (self._voice_chk_fuel_save_recommend, "_voice_alert_fuel_save_recommend"),
                (self._voice_chk_advisor_pit_window,  "_voice_alert_advisor_pit_window"),
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

        screen.blit(self._overlay, (0, 0))

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
        display = self._ip_text + ("|" if (self._cursor_visible and self._active_field != "wear_thr") else " ")
        ip_surf = font_md.render(display, True, C_TEXT)
        screen.blit(ip_surf, (self._field.x + 10, self._field.y + 8))

        # Recording on start checkbox
        pygame.draw.rect(screen, C_INPUT_BG, self._rec_on_start_check, border_radius=3)
        pygame.draw.rect(screen, C_ACCENT, self._rec_on_start_check, 1, border_radius=3)
        if self._recording_on_start:
            inner = self._rec_on_start_check.inflate(-5, -5)
            pygame.draw.rect(screen, C_ACCENT, inner, border_radius=2)
        rec_lbl = font_sm.render("Record automatically on start", True, C_TEXT)
        screen.blit(rec_lbl, (self._rec_on_start_check.right + 10,
                              self._rec_on_start_check.y + (self._rec_on_start_check.height - rec_lbl.get_height()) // 2))

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

        # Engineer communications section
        pygame.draw.line(screen, C_BORDER,
                         (self._card.x + 1, self._voice_alerts_sep_y),
                         (self._card.right - 1, self._voice_alerts_sep_y))
        alerts_lbl = font_sm.render("Engineer communications", True, C_DIM)
        screen.blit(alerts_lbl, (self._voice_chk_lap_completed.x, self._voice_alerts_sep_y + 6))

        grp_color = (160, 160, 175)
        _sep_x0 = self._card.x + 20
        _sep_x1 = self._card.right - 20

        # Race sub-group
        screen.blit(font_sm.render("Race", True, grp_color),
                    (self._voice_chk_lap_completed.x, self._voice_grp_race_lbl_y))

        # Fuel & Pit sub-group
        pygame.draw.line(screen, (42, 42, 55), (_sep_x0, self._voice_grp_fuel_sep_y),
                         (_sep_x1, self._voice_grp_fuel_sep_y))
        screen.blit(font_sm.render("Fuel & Pit", True, grp_color),
                    (self._voice_chk_lap_completed.x, self._voice_grp_fuel_lbl_y))

        # Car health sub-group
        pygame.draw.line(screen, (42, 42, 55), (_sep_x0, self._voice_grp_car_sep_y),
                         (_sep_x1, self._voice_grp_car_sep_y))
        screen.blit(font_sm.render("Car health", True, grp_color),
                    (self._voice_chk_lap_completed.x, self._voice_grp_car_lbl_y))

        for chk, checked, label in (
            (self._voice_chk_lap_completed,   self._voice_alert_lap_completed,   "Lap completed"),
            (self._voice_chk_best_lap,        self._voice_alert_best_lap,        "Best lap"),
            (self._voice_chk_final_lap,       self._voice_alert_final_lap,       "Final lap"),
            (self._voice_chk_lap_delta,       self._voice_alert_lap_delta,       "Lap delta"),
            (self._voice_chk_race_report,      self._voice_alert_race_report,      "Race report"),
            (self._voice_chk_laps_to_finish,   self._voice_alert_laps_to_finish,   "Laps to go"),
            (self._voice_chk_fuel_low,         self._voice_alert_fuel_low,         "Fuel low"),
            (self._voice_chk_fuel_critical,    self._voice_alert_fuel_critical,    "Fuel critical"),
            (self._voice_chk_pit_window,       self._voice_alert_pit_window,       "Pit window"),
            (self._voice_chk_fuel_save,        self._voice_alert_fuel_save,        "Fuel save"),
            (self._voice_chk_engine_temp,      self._voice_alert_engine_temp,      "Engine temp"),
            (self._voice_chk_oil_temp,        self._voice_alert_oil_temp,        "Oil temp"),
            (self._voice_chk_tire_temp,       self._voice_alert_tire_temp,       "Tyre temp"),
            (self._voice_chk_tire_inner_temp, self._voice_alert_tire_inner_temp, "Inner temp"),
            (self._voice_chk_tire_pressure,   self._voice_alert_tire_pressure,   "Tyre pres."),
            (self._voice_chk_overtake,        self._voice_alert_overtake,        "Overtake"),
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

        # ── Tyre wear (real field) section ───────────────────────────────────
        pygame.draw.line(screen, C_BORDER,
                         (self._card.x + 20, self._voice_grp_wear_sep_y),
                         (self._card.right - 20, self._voice_grp_wear_sep_y))
        grp_wear = font_sm.render("Tyre Wear", True, C_DIM)
        screen.blit(grp_wear, (self._card.x + 20, self._voice_grp_wear_lbl_y))

        enabled = self._voice_enabled
        chk = self._voice_chk_tyre_wear
        pygame.draw.rect(screen, C_INPUT_BG, chk, border_radius=3)
        pygame.draw.rect(screen, C_ACCENT if enabled else (45, 45, 55), chk, 1, border_radius=3)
        if self._voice_alert_tyre_wear and enabled:
            inner = chk.inflate(-5, -5)
            pygame.draw.rect(screen, C_ACCENT, inner, border_radius=2)
        txt_color = C_TEXT if enabled else C_DIM
        surf = font_sm.render("Wear alert", True, txt_color)
        screen.blit(surf, (chk.right + 10, chk.y + (chk.height - surf.get_height()) // 2))

        # Threshold input
        thr_active = self._active_field == "wear_thr" and enabled
        thr_bg = C_INPUT_ACTIVE if thr_active else C_INPUT_BG
        thr_border = C_ACCENT if thr_active else C_BORDER
        pygame.draw.rect(screen, thr_bg, self._voice_wear_thr_field, border_radius=4)
        pygame.draw.rect(screen, thr_border, self._voice_wear_thr_field, 1, border_radius=4)
        thr_cursor = "|" if (thr_active and self._cursor_visible) else ""
        thr_surf = font_sm.render(self._voice_wear_thr_text + thr_cursor, True, txt_color)
        screen.blit(thr_surf, (self._voice_wear_thr_field.x + 4,
                               self._voice_wear_thr_field.y + (self._voice_wear_thr_field.height - thr_surf.get_height()) // 2))
        pct_surf = font_sm.render("%", True, C_DIM)
        screen.blit(pct_surf, (self._voice_wear_thr_field.right + 4,
                               self._voice_wear_thr_field.y + (self._voice_wear_thr_field.height - pct_surf.get_height()) // 2))
        thr_lbl = font_sm.render("Threshold:", True, C_DIM)
        screen.blit(thr_lbl, (self._voice_wear_thr_field.x - font_sm.size("Threshold: ")[0] - 4,
                               self._voice_wear_thr_field.y + (self._voice_wear_thr_field.height - thr_lbl.get_height()) // 2))

        # ── Strategy alerts group ─────────────────────────────────────────────
        pygame.draw.line(screen, C_BORDER,
                         (self._card.x + 20, self._voice_grp_strategy_sep_y),
                         (self._card.right - 20, self._voice_grp_strategy_sep_y))
        grp_strategy = font_sm.render("Strategy Alerts", True, C_DIM)
        screen.blit(grp_strategy, (self._card.x + 20, self._voice_grp_strategy_lbl_y))

        for chk, checked, label in (
            (self._voice_chk_strategy_check_in,   self._voice_alert_strategy_check_in,   "Check-in"),
            (self._voice_chk_strategy_revised,    self._voice_alert_strategy_revised,    "Revised"),
            (self._voice_chk_fuel_save_recommend, self._voice_alert_fuel_save_recommend, "Fuel save+"),
            (self._voice_chk_advisor_pit_window,  self._voice_alert_advisor_pit_window,  "Pit window"),
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

        if self._show_micro:
            self._draw_airflow_section(screen, font_sm)

        # Buttons
        mouse = pygame.mouse.get_pos()
        self._draw_btn(screen, font_sm, self._btn_save, "Save",
                       C_BTN_SAVE if not self._btn_save.collidepoint(mouse) else C_BTN_HOVER)
        self._draw_btn(screen, font_sm, self._btn_cancel, "Cancel",
                       C_BTN_CANCEL if not self._btn_cancel.collidepoint(mouse) else (80, 80, 95))
        _btns = [
            self._fuel_btn_last, self._fuel_btn_avg,
            self._voice_btn_en, self._voice_btn_pt, self._voice_btn_test,
            self._btn_save, self._btn_cancel,
        ]
        if self._show_micro:
            _btns.append(self._micro_test_btn)
        if any(b.collidepoint(mouse) for b in _btns):
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)

    def _draw_airflow_section(self, screen: pygame.Surface, font_sm: pygame.font.Font) -> None:
        pygame.draw.line(screen, C_BORDER,
                         (self._card.x + 1, self._micro_sep_y),
                         (self._card.right - 1, self._micro_sep_y))
        micro_lbl = font_sm.render("Airflow Simulation", True, C_DIM)
        screen.blit(micro_lbl, (self._micro_check_box.x, self._micro_lbl_y))

        pygame.draw.rect(screen, C_INPUT_BG, self._micro_check_box, border_radius=3)
        pygame.draw.rect(screen, C_ACCENT, self._micro_check_box, 1, border_radius=3)
        if self._microcontroller_enabled:
            inner = self._micro_check_box.inflate(-5, -5)
            pygame.draw.rect(screen, C_ACCENT, inner, border_radius=2)
        micro_chk_lbl = font_sm.render("Enable airflow simulation  (* requires restart)", True, C_TEXT)
        screen.blit(micro_chk_lbl, (self._micro_check_box.right + 10,
                                    self._micro_check_box.y + (self._micro_check_box.height - micro_chk_lbl.get_height()) // 2))

        micro_enabled = self._microcontroller_enabled
        port_lbl = font_sm.render("Serial Port  (blank = auto-detect)", True, C_DIM)
        screen.blit(port_lbl, (self._micro_port_field.x, self._micro_port_lbl_y))

        port_active = self._active_field == "port" and micro_enabled
        port_bg = C_INPUT_ACTIVE if port_active else C_INPUT_BG
        port_border = C_ACCENT if port_active else C_BORDER
        port_bg = port_bg if micro_enabled else (30, 30, 40)
        port_border = port_border if micro_enabled else (45, 45, 55)
        pygame.draw.rect(screen, port_bg, self._micro_port_field, border_radius=6)
        pygame.draw.rect(screen, port_border, self._micro_port_field, 1, border_radius=6)
        port_txt_color = C_TEXT if micro_enabled else C_DIM
        port_cursor = "|" if (port_active and self._cursor_visible) else ""
        port_surf = font_sm.render(self._microcontroller_port + port_cursor, True, port_txt_color)
        screen.blit(port_surf, (self._micro_port_field.x + 8,
                                self._micro_port_field.y + (self._micro_port_field.height - port_surf.get_height()) // 2))

        test_ready = micro_enabled and bool(self._microcontroller_port)
        test_bg = (50, 100, 60) if test_ready else (30, 30, 40)
        test_border = (80, 160, 90) if test_ready else (45, 45, 55)
        test_txt = C_TEXT if test_ready else C_DIM
        pygame.draw.rect(screen, test_bg, self._micro_test_btn, border_radius=6)
        pygame.draw.rect(screen, test_border, self._micro_test_btn, 1, border_radius=6)
        test_surf = font_sm.render("Test Connection", True, test_txt)
        screen.blit(test_surf, test_surf.get_rect(center=self._micro_test_btn.center))

        if self._micro_test_result is None:
            note_text = ("No serial port auto-detected — enter one manually"
                         if micro_enabled and not self._microcontroller_port else "")
            note_color = (180, 130, 60)
        elif self._micro_test_result:
            note_text = "Connected — device replied PONG"
            note_color = (90, 200, 110)
        else:
            note_text = "No response from device"
            note_color = (220, 90, 90)
        if note_text:
            note_surf = font_sm.render(note_text, True, note_color)
            screen.blit(note_surf, (self._micro_port_field.x, self._micro_note_y))

        # Fan speed ceiling
        ceiling_lbl_color = C_DIM if micro_enabled else (60, 60, 70)
        ceiling_lbl = font_sm.render("Fan speed ceiling:", True, ceiling_lbl_color)
        screen.blit(ceiling_lbl, (self._micro_port_field.x,
                                  self._fan_ceiling_field.y + (self._fan_ceiling_field.height - ceiling_lbl.get_height()) // 2))

        ceiling_active = self._active_field == "fan_ceiling" and micro_enabled
        ceiling_bg = C_INPUT_ACTIVE if ceiling_active else C_INPUT_BG
        ceiling_border = C_ACCENT if ceiling_active else C_BORDER
        ceiling_bg = ceiling_bg if micro_enabled else (30, 30, 40)
        ceiling_border = ceiling_border if micro_enabled else (45, 45, 55)
        pygame.draw.rect(screen, ceiling_bg, self._fan_ceiling_field, border_radius=4)
        pygame.draw.rect(screen, ceiling_border, self._fan_ceiling_field, 1, border_radius=4)
        ceiling_txt_color = C_TEXT if micro_enabled else C_DIM
        ceiling_cursor = "|" if (ceiling_active and self._cursor_visible) else ""
        ceiling_surf = font_sm.render(self._fan_speed_ceiling_text + ceiling_cursor, True, ceiling_txt_color)
        screen.blit(ceiling_surf, (self._fan_ceiling_field.x + 4,
                                    self._fan_ceiling_field.y + (self._fan_ceiling_field.height - ceiling_surf.get_height()) // 2))
        ceiling_unit_surf = font_sm.render("km/h", True, ceiling_lbl_color)
        screen.blit(ceiling_unit_surf, (self._fan_ceiling_field.right + 6,
                                         self._fan_ceiling_field.y + (self._fan_ceiling_field.height - ceiling_unit_surf.get_height()) // 2))

    def _draw_btn(self, screen, font, rect: pygame.Rect, text: str, color: tuple) -> None:
        pygame.draw.rect(screen, color, rect, border_radius=6)
        pygame.draw.rect(screen, C_BORDER, rect, 1, border_radius=6)
        surf = font.render(text, True, C_TEXT)
        screen.blit(surf, surf.get_rect(center=rect.center))

    def _save(self) -> Action:
        self.active = False
        return "saved"

    @property
    def recording_on_start(self) -> bool:
        return self._recording_on_start

    @property
    def ip_text(self) -> str:
        return self._ip_text

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
    def voice_alert_race_report(self) -> bool:
        return self._voice_alert_race_report

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

    @property
    def voice_alert_tyre_wear(self) -> bool:
        return self._voice_alert_tyre_wear

    @property
    def voice_alert_overtake(self) -> bool:
        return self._voice_alert_overtake

    @property
    def voice_alert_laps_to_finish(self) -> bool:
        return self._voice_alert_laps_to_finish

    @property
    def voice_alert_fuel_save(self) -> bool:
        return self._voice_alert_fuel_save

    @property
    def voice_alert_strategy_check_in(self) -> bool:
        return self._voice_alert_strategy_check_in

    @property
    def voice_alert_strategy_revised(self) -> bool:
        return self._voice_alert_strategy_revised

    @property
    def voice_alert_fuel_save_recommend(self) -> bool:
        return self._voice_alert_fuel_save_recommend

    @property
    def voice_alert_advisor_pit_window(self) -> bool:
        return self._voice_alert_advisor_pit_window

    @property
    def voice_tyre_wear_threshold_pct(self) -> float:
        try:
            v = int(self._voice_wear_thr_text)
            return max(1, min(99, v)) / 100.0
        except ValueError:
            return 0.10

    @property
    def microcontroller_enabled(self) -> bool:
        return self._microcontroller_enabled

    @property
    def microcontroller_port(self) -> str:
        return self._microcontroller_port

    @property
    def fan_speed_ceiling_kmh(self) -> float:
        try:
            v = float(self._fan_speed_ceiling_text)
            if v > 0:
                self._fan_speed_ceiling_kmh = v
        except ValueError:
            pass
        return self._fan_speed_ceiling_kmh

    def set_microcontroller_test_result(self, success: bool) -> None:
        self._micro_test_result = success
