"""Help overlay: describes every dashboard element."""

import pygame

C_OVERLAY = (0, 0, 0, 185)
C_CARD = (22, 22, 30)
C_TITLE_BAR = (28, 28, 42)
C_BORDER = (60, 60, 80)
C_DIVIDER = (42, 42, 55)
C_TITLE = (230, 230, 230)
C_SECTION = (80, 140, 220)
C_TEXT = (200, 200, 210)
C_DIM = (95, 95, 108)
C_ACCENT = (80, 140, 220)
C_ORANGE = (255, 165, 0)
C_SPIN = (255, 140, 0)
C_LOCK = (0, 190, 230)
C_RED = (210, 55, 55)
C_YELLOW = (240, 210, 0)
C_LIGHT = (190, 200, 255)

# fmt: off
_LEFT = [
    ("section", "GAUGES"),
    ("item",  "Velocidade",     "gauge esq. · km/h · arco: verde→laranja→vermelho ao se aproximar do limite",  C_ACCENT),
    ("item",  "RPM",            "gauge dir. · rotação do motor · mesmo esquema de cores da velocidade",          C_ACCENT),
    ("item",  "Barra RPM",      "faixa no topo · verde / laranja / vermelho conforme a zona de rotação",         C_ACCENT),

    ("section", "MARCHAS & PEDAIS"),
    ("item",  "Marcha",         "número grande no centro · N=neutro · R=ré",                                     C_TEXT),
    ("item",  "→ N (laranja)",  "marcha sugerida pelo jogo — aparece quando diferente da atual",                  C_ORANGE),
    ("item",  "C · B · T",      "barras verticais: embreagem (azul) · freio (vermelho) · acelerador (verde)",     C_TEXT),
    ("item",  "FUEL (barra)",   "percentual de combustível restante no tanque",                                   C_ACCENT),

    ("section", "G-METER (inf. esq.)"),
    ("item",  "Ponto móvel",    "posição = força G atual: lateral (esq/dir) e longitudinal",                     C_TEXT),
    ("item",  "Cor do ponto",   "verde <0.8G · laranja <1.5G · vermelho ≥1.5G",                                  C_TEXT),
    ("item",  "Orientação",     "topo=frenagem · base=aceleração · lados=curvas esq./dir.",                      C_DIM),
]

_RIGHT = [
    ("section", "PNEUS (centro inf.)"),
    ("item",  "Cor do tile",       "azul=frio (<60°C) · verde=ideal (60-130°C) · vermelho=quente (>130°C)",      C_TEXT),
    ("item",  "Borda laranja",     "wheelspin: roda girando mais rápido que o esperado pela velocidade atual",    C_SPIN),
    ("item",  "Borda ciano",       "lockup: roda travando sob frenagem intensa",                                  C_LOCK),

    ("section", "INDICADORES (strip abaixo do RPM)"),
    ("item",  "TCS / ASM",         "controle de tração (laranja) ou estabilidade (amarelo) interveio",           C_SPIN),
    ("item",  "REV / HB",          "limitador de RPM ativo · freio de mão acionado",                             C_RED),
    ("item",  "LIGHT",             "faróis ligados — útil em corridas com segmentos noturnos",                   C_LIGHT),
    ("item",  "OIL! / H₂O!",      "temperatura crítica: óleo >130°C ou água >105°C",                            C_RED),

    ("section", "PAINEL DE INFO (dir.)"),
    ("item",  "LAP / BEST / LAST", "volta atual · melhor volta · última volta completa",                          C_TEXT),
    ("item",  "FUEL / FUEL·LAP",   "litros no tanque · consumo por volta após a 1ª troca de volta",              C_ACCENT),
    ("item",  "LAPS LEFT",         "estimativa de voltas restantes com o combustível atual",                      C_TEXT),
    ("item",  "WATER · OIL · BOOST", "fluidos e turbo · laranja = acima do limite seguro",                       C_ORANGE),
]
# fmt: on

_FOOTER = "ESC ou clique fora para fechar"

_CARD_X, _CARD_Y = 56, 58       # card sits just below the header
_CARD_W, _CARD_H = 1168, 632    # bottom ≈ 690, leaves margin on 720px screen
_PAD = 24
_COL_GAP = 28
_TITLE_H = 44
_ITEM_NAME_H = 18   # advance per name line (14pt ≈ 17-18px)
_ITEM_DESC_H = 18   # advance per description line
_ITEM_GAP = 3       # gap between items
_SECTION_PRE_GAP = 8
_SECTION_UNDER_H = 5


class HelpPanel:
    def __init__(self, win_w: int, win_h: int) -> None:
        self.active = False
        self._card = pygame.Rect(_CARD_X, _CARD_Y, _CARD_W, _CARD_H)
        col_w = (_CARD_W - 2 * _PAD - _COL_GAP) // 2
        self._col_w = col_w
        self._col_left_x = _CARD_X + _PAD
        self._col_right_x = self._col_left_x + col_w + _COL_GAP
        close_sz = 22
        self._close_btn = pygame.Rect(
            _CARD_X + _CARD_W - close_sz - 10,
            _CARD_Y + (_TITLE_H - close_sz) // 2,
            close_sz, close_sz,
        )

    def open(self) -> None:
        self.active = True

    def handle_event(self, event: pygame.event.Event) -> str | None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.active = False
            return "closed"
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.active = False
            return "closed"
        return None

    def draw(
        self,
        surface: pygame.Surface,
        font_md: pygame.font.Font,
        font_sm: pygame.font.Font,
    ) -> None:
        if not self.active:
            return

        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill(C_OVERLAY)
        surface.blit(overlay, (0, 0))

        pygame.draw.rect(surface, C_CARD, self._card, border_radius=10)
        pygame.draw.rect(surface, C_BORDER, self._card, 1, border_radius=10)

        title_bar = pygame.Rect(_CARD_X, _CARD_Y, _CARD_W, _TITLE_H)
        pygame.draw.rect(surface, C_TITLE_BAR, title_bar,
                         border_top_left_radius=10, border_top_right_radius=10)
        pygame.draw.line(
            surface, C_BORDER,
            (_CARD_X, _CARD_Y + _TITLE_H),
            (_CARD_X + _CARD_W, _CARD_Y + _TITLE_H), 1,
        )
        title = font_md.render("RACE ENGINEER  —  GUIA DOS ELEMENTOS", True, C_TITLE)
        surface.blit(title, title.get_rect(midleft=(_CARD_X + _PAD, _CARD_Y + _TITLE_H // 2)))

        mouse = pygame.mouse.get_pos()
        close_bg = (70, 40, 40) if self._close_btn.collidepoint(mouse) else (42, 42, 58)
        pygame.draw.rect(surface, close_bg, self._close_btn, border_radius=4)
        x_surf = font_sm.render("✕", True, C_TITLE)
        surface.blit(x_surf, x_surf.get_rect(center=self._close_btn.center))

        content_y = _CARD_Y + _TITLE_H + 12
        self._draw_column(surface, font_sm, self._col_left_x, content_y, _LEFT)

        div_x = self._col_right_x - _COL_GAP // 2
        pygame.draw.line(
            surface, C_DIVIDER,
            (div_x, _CARD_Y + _TITLE_H + 8),
            (div_x, _CARD_Y + _CARD_H - 28), 1,
        )
        self._draw_column(surface, font_sm, self._col_right_x, content_y, _RIGHT)

        footer = font_sm.render(_FOOTER, True, C_DIM)
        surface.blit(footer, footer.get_rect(
            center=(_CARD_X + _CARD_W // 2, _CARD_Y + _CARD_H - 14)))

    def _draw_column(
        self,
        surface: pygame.Surface,
        font: pygame.font.Font,
        x: int,
        start_y: int,
        entries: list,
    ) -> None:
        y = start_y
        first_section = True

        for entry in entries:
            kind = entry[0]

            if kind == "section":
                if not first_section:
                    y += _SECTION_PRE_GAP
                first_section = False
                lbl = font.render(entry[1], True, C_SECTION)
                surface.blit(lbl, (x, y))
                y += lbl.get_height() + 3
                pygame.draw.line(
                    surface, C_DIVIDER, (x, y), (x + self._col_w, y), 1
                )
                y += _SECTION_UNDER_H

            else:
                _, name, desc, color = entry
                name_surf = font.render(f"• {name}", True, color)
                surface.blit(name_surf, (x + 2, y))
                y += _ITEM_NAME_H
                desc_surf = font.render(desc, True, C_DIM)
                surface.blit(desc_surf, (x + 12, y))
                y += _ITEM_DESC_H + _ITEM_GAP
