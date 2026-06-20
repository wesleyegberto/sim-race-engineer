"""Strategy overlay panel for configuring user-defined pit stop strategy."""

from typing import Any, Literal

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
C_HEALTH_OK = (60, 190, 100)
C_HEALTH_REVISE = (220, 155, 40)
C_HEALTH_CRITICAL = (210, 65, 65)

_CARD_W, _CARD_H = 480, 630
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

        # Open/Close input fields for each stop (two rects per stop)
        self._open_fields = [
            pygame.Rect(fx + 140, fy + 55 + i * 50, 60, 30)
            for i in range(_MAX_STOPS)
        ]
        self._close_fields = [
            pygame.Rect(fx + 220, fy + 55 + i * 50, 60, 30)
            for i in range(_MAX_STOPS)
        ]

        # Tyre wear limit and pit buffer fields
        self._wear_field   = pygame.Rect(fx + 180, fy + 215, 60, 30)
        self._buffer_field = pygame.Rect(fx + 180, fy + 265, 60, 30)

        # Voice strategy checkbox
        self._voice_chk = pygame.Rect(fx, fy + 315, 18, 18)

        btn_y = cy + _CARD_H - 52
        self._btn_save   = pygame.Rect(cx + _CARD_W - 198, btn_y, 80, 34)
        self._btn_clear  = pygame.Rect(cx + _CARD_W - 326, btn_y, 120, 34)
        self._btn_cancel = pygame.Rect(cx + _CARD_W - 110, btn_y, 90, 34)

        # Pre-allocated overlay (never changes)
        self._overlay = pygame.Surface((win_w, win_h), pygame.SRCALPHA)
        self._overlay.fill(C_OVERLAY)

        # State
        self._planned_stops: int = 0
        self._open_texts: list[str] = ["", "", ""]
        self._close_texts: list[str] = ["", "", ""]
        self._wear_text: str = "80"
        self._buffer_text: str = "1"
        self._voice_strategy: bool = True
        self._active_field: str | None = None  # "open0".."open2","close0".."close2","wear","buffer"
        self._cursor_visible = True
        self._cursor_timer = 0

    # ── Public interface ──────────────────────────────────────────────────────

    def open(
        self,
        planned_stops: int,
        planned_stop_windows: list[tuple[int, int]],
        tyre_wear_limit_pct: float,
        pit_buffer_laps: int,
        voice_alert_strategy: bool,
    ) -> None:
        self._planned_stops = min(planned_stops, _MAX_STOPS)
        self._open_texts = ["", "", ""]
        self._close_texts = ["", "", ""]
        for i, (o, c) in enumerate(planned_stop_windows[:_MAX_STOPS]):
            self._open_texts[i] = str(o)
            self._close_texts[i] = str(c) if c != o else str(o)
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
            for i in range(_MAX_STOPS):
                if self._open_fields[i].collidepoint(pos) and i < self._planned_stops:
                    self._active_field = f"open{i}"
                    return None
                if self._close_fields[i].collidepoint(pos) and i < self._planned_stops:
                    self._active_field = f"close{i}"
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
             font_sm: pygame.font.Font, dt_ms: int,
             report: Any = None) -> None:
        if not self.active:
            return

        self._cursor_timer += dt_ms
        if self._cursor_timer >= 500:
            self._cursor_timer = 0
            self._cursor_visible = not self._cursor_visible

        screen.blit(self._overlay, (0, 0))

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

        # Column headers (shown above first row)
        if self._planned_stops > 0:
            hdr_y = fy + 36
            open_hdr = font_sm.render("Open", True, C_DIM)
            close_hdr = font_sm.render("Close", True, C_DIM)
            tgt_hdr = font_sm.render("Target", True, C_DIM)
            screen.blit(open_hdr, (self._open_fields[0].x + 6, hdr_y))
            screen.blit(close_hdr, (self._close_fields[0].x + 4, hdr_y))
            screen.blit(tgt_hdr, (self._close_fields[0].right + 12, hdr_y))

        # Per-stop rows
        for i in range(_MAX_STOPS):
            open_f = self._open_fields[i]
            close_f = self._close_fields[i]
            enabled = i < self._planned_stops
            color = C_TEXT if enabled else C_DIM

            # Stop label
            lbl = font_sm.render(f"Stop {i + 1}:", True, color)
            screen.blit(lbl, (fx, open_f.y + (open_f.height - font_sm.get_height()) // 2))

            if enabled:
                # Open field
                active_open = self._active_field == f"open{i}"
                pygame.draw.rect(screen, C_INPUT_ACTIVE if active_open else C_INPUT_BG, open_f, border_radius=5)
                pygame.draw.rect(screen, C_ACCENT if active_open else C_BORDER, open_f, 1, border_radius=5)
                cursor_open = "|" if (active_open and self._cursor_visible) else ""
                surf = font_sm.render(self._open_texts[i] + cursor_open, True, C_TEXT)
                screen.blit(surf, (open_f.x + 6, open_f.y + (open_f.height - surf.get_height()) // 2))

                # Separator "—"
                dash = font_sm.render("—", True, C_DIM)
                screen.blit(dash, (open_f.right + 4,
                                   open_f.y + (open_f.height - dash.get_height()) // 2))

                # Close field
                active_close = self._active_field == f"close{i}"
                pygame.draw.rect(screen, C_INPUT_ACTIVE if active_close else C_INPUT_BG, close_f, border_radius=5)
                pygame.draw.rect(screen, C_ACCENT if active_close else C_BORDER, close_f, 1, border_radius=5)
                cursor_close = "|" if (active_close and self._cursor_visible) else ""
                surf = font_sm.render(self._close_texts[i] + cursor_close, True, C_TEXT)
                screen.blit(surf, (close_f.x + 6, close_f.y + (close_f.height - surf.get_height()) // 2))

                # Target label
                try:
                    o = int(self._open_texts[i]) if self._open_texts[i] else 0
                    c = int(self._close_texts[i]) if self._close_texts[i] else o
                    tgt = (o + max(o, c)) // 2 if o > 0 else 0
                    tgt_str = f"→ {tgt}" if tgt > 0 else ""
                except ValueError:
                    tgt_str = ""
                if tgt_str:
                    tgt_surf = font_sm.render(tgt_str, True, C_ACCENT)
                    screen.blit(tgt_surf, (close_f.right + 12,
                                           close_f.y + (close_f.height - tgt_surf.get_height()) // 2))
            else:
                for field in (open_f, close_f):
                    pygame.draw.rect(screen, (20, 20, 28), field, border_radius=5)
                    pygame.draw.rect(screen, (40, 40, 50), field, 1, border_radius=5)

        # Separator
        sep_y = fy + 200
        pygame.draw.line(screen, C_BORDER, (self._card.x + 20, sep_y), (self._card.right - 20, sep_y))

        # Tyre wear limit
        wear_y = sep_y + 15
        wear_lbl = font_sm.render("Tyre wear limit:", True, C_DIM)
        screen.blit(wear_lbl, (fx, wear_y + (self._wear_field.height - font_sm.get_height()) // 2))
        wear_unit = font_sm.render("%", True, C_DIM)
        screen.blit(wear_unit, (self._wear_field.right + 6,
                                wear_y + (self._wear_field.height - wear_unit.get_height()) // 2))
        wear_bg = C_INPUT_ACTIVE if self._active_field == "wear" else C_INPUT_BG
        wear_border = C_ACCENT if self._active_field == "wear" else C_BORDER
        pygame.draw.rect(screen, wear_bg, self._wear_field, border_radius=5)
        pygame.draw.rect(screen, wear_border, self._wear_field, 1, border_radius=5)
        wear_cursor = "|" if (self._active_field == "wear" and self._cursor_visible) else ""
        surf = font_sm.render(self._wear_text + wear_cursor, True, C_TEXT)
        screen.blit(surf, (self._wear_field.x + 6,
                           self._wear_field.y + (self._wear_field.height - surf.get_height()) // 2))

        # Pit buffer
        buf_y = wear_y + 50
        buf_lbl = font_sm.render("Pit buffer:", True, C_DIM)
        screen.blit(buf_lbl, (fx, buf_y + (self._buffer_field.height - font_sm.get_height()) // 2))
        buf_unit = font_sm.render("laps", True, C_DIM)
        screen.blit(buf_unit, (self._buffer_field.right + 6,
                               buf_y + (self._buffer_field.height - buf_unit.get_height()) // 2))
        buf_bg = C_INPUT_ACTIVE if self._active_field == "buffer" else C_INPUT_BG
        buf_border = C_ACCENT if self._active_field == "buffer" else C_BORDER
        pygame.draw.rect(screen, buf_bg, self._buffer_field, border_radius=5)
        pygame.draw.rect(screen, buf_border, self._buffer_field, 1, border_radius=5)
        buf_cursor = "|" if (self._active_field == "buffer" and self._cursor_visible) else ""
        surf = font_sm.render(self._buffer_text + buf_cursor, True, C_TEXT)
        screen.blit(surf, (self._buffer_field.x + 6,
                           self._buffer_field.y + (self._buffer_field.height - surf.get_height()) // 2))

        # Voice strategy checkbox
        pygame.draw.rect(screen, C_INPUT_BG, self._voice_chk, border_radius=3)
        pygame.draw.rect(screen, C_ACCENT, self._voice_chk, 1, border_radius=3)
        if self._voice_strategy:
            inner = self._voice_chk.inflate(-5, -5)
            pygame.draw.rect(screen, C_ACCENT, inner, border_radius=2)
        chk_lbl = font_sm.render("Voice strategy alerts", True, C_TEXT)
        screen.blit(chk_lbl, (self._voice_chk.right + 10,
                               self._voice_chk.y + (self._voice_chk.height - chk_lbl.get_height()) // 2))

        # ── Fuel Analysis / Strategy Health ──────────────────────────────────
        fa_y = fy + 345
        pygame.draw.line(screen, C_BORDER,
                         (self._card.x + 20, fa_y), (self._card.right - 20, fa_y))

        if report is not None:
            # Strategy Health badge
            health = report.strategy_health
            badge_color = (
                C_HEALTH_OK if health == "ON_PLAN"
                else C_HEALTH_CRITICAL if health == "CRITICAL"
                else C_HEALTH_REVISE
            )
            health_lbl = font_sm.render("Strategy:", True, C_DIM)
            screen.blit(health_lbl, (fx, fa_y + 10))
            badge_text = health.replace("_", " ")
            badge_surf = font_sm.render(badge_text, True, badge_color)
            screen.blit(badge_surf, (fx + 100, fa_y + 10))

            # Fuel analysis rows
            pygame.draw.line(screen, C_BORDER,
                             (self._card.x + 20, fa_y + 34), (self._card.right - 20, fa_y + 34))
            fa_title = font_sm.render("Fuel Analysis", True, C_DIM)
            screen.blit(fa_title, (fx, fa_y + 42))

            def _row(label: str, value: str, row: int, val_color: tuple = C_TEXT) -> None:
                y = fa_y + 64 + row * 22
                screen.blit(font_sm.render(label, True, C_DIM), (fx, y))
                screen.blit(font_sm.render(value, True, val_color), (fx + 200, y))

            fuel_delta_color = C_HEALTH_OK if report.fuel_delta >= 0 else C_HEALTH_CRITICAL
            delta_sign = "+" if report.fuel_delta >= 0 else ""
            _row("Fuel to finish:", f"{report.fuel_to_finish:.1f} L", 0)
            _row("Fuel delta:", f"{delta_sign}{report.fuel_delta:.1f} L", 1, fuel_delta_color)
            _row("Laps to fuel out:", f"{report.laps_to_fuel_out_avg:.1f} avg / {report.laps_to_fuel_out_last:.1f} last", 2)
            ms = report.avg_lap_time_ms
            if ms > 0:
                lap_str = f"{ms // 60000}:{(ms % 60000) // 1000:02d}.{(ms % 1000) // 100}"
            else:
                lap_str = "—"
            _row("Avg lap time:", lap_str, 3)
            stops_str = str(report.recommended_stops) if report.recommended_stops >= 0 else "—"
            _row("Recommended stops:", stops_str, 4)
        else:
            no_data = font_sm.render("No data yet — race in progress", True, C_DIM)
            screen.blit(no_data, (fx, fa_y + 14))

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
    def planned_stop_windows(self) -> list[tuple[int, int]]:
        windows: list[tuple[int, int]] = []
        for i in range(self._planned_stops):
            try:
                o = int(self._open_texts[i]) if self._open_texts[i] else 0
                c = int(self._close_texts[i]) if self._close_texts[i] else o
                if o > 0:
                    windows.append((o, max(o, c)))
            except ValueError:
                pass
        return windows

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
        self._open_texts = ["", "", ""]
        self._close_texts = ["", "", ""]
        self.active = False

    def _cycle_focus(self) -> None:
        fields: list[str] = []
        for i in range(self._planned_stops):
            fields += [f"open{i}", f"close{i}"]
        fields += ["wear", "buffer"]
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
        if self._active_field.startswith("open"):
            i = int(self._active_field[4])
            self._open_texts[i] = self._open_texts[i][:-1]
        elif self._active_field.startswith("close"):
            i = int(self._active_field[5])
            self._close_texts[i] = self._close_texts[i][:-1]
        elif self._active_field == "wear":
            self._wear_text = self._wear_text[:-1]
        elif self._active_field == "buffer":
            self._buffer_text = self._buffer_text[:-1]

    def _type_char(self, ch: str) -> None:
        if self._active_field is None:
            return
        if self._active_field.startswith("open"):
            i = int(self._active_field[4])
            candidate = self._open_texts[i] + ch
            if int(candidate) <= _MAX_LAP and len(candidate) <= 3:
                self._open_texts[i] = candidate
        elif self._active_field.startswith("close"):
            i = int(self._active_field[5])
            candidate = self._close_texts[i] + ch
            if int(candidate) <= _MAX_LAP and len(candidate) <= 3:
                self._close_texts[i] = candidate
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
