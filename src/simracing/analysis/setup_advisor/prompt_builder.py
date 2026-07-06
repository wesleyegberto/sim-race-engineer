from __future__ import annotations

from simracing.analysis.setup_advisor.aggregator import SetupStats
from simracing.analysis.setup_advisor.gt7_setup_options import build_params_section

_PSI_FACTOR = 0.145038
_WHEELS = ("FL", "FR", "RL", "RR")

_UNAVAILABLE = {"pt": "dados não disponíveis", "en": "data not available"}


def _na(lang: str) -> str:
    return _UNAVAILABLE.get(lang, _UNAVAILABLE["pt"])


def _psi(kpa: float) -> str:
    return f"{kpa * _PSI_FACTOR:.1f}"


def _temp_row(wheel: str, surf: float, inner: float, middle: float) -> str:
    return f"| {wheel} | {surf:.1f} | {inner:.1f} | {middle:.1f} |"


def _pressure_row(wheel: str, kpa: float) -> str:
    return f"| {wheel} | {kpa:.1f} | {_psi(kpa)} |"


def _sus_row(wheel: str, val: float) -> str:
    return f"| {wheel} | {val * 1000:.1f} mm |"


def _section_temps(stats: SetupStats, lang: str) -> str:
    have = stats.data_quality.get("surf_temp", False)
    if lang == "en":
        title = "## Tyre Temperatures (°C)"
        header = "| Wheel | Surface | Inner | Middle |"
        sep = "|-------|---------|-------|--------|"
    else:
        title = "## Temperaturas de Pneus (°C)"
        header = "| Roda | Superfície | Interna | Média |"
        sep = "|------|-----------|---------|-------|"

    if not have:
        return f"{title}\n{_na(lang)}\n"

    rows = "\n".join(
        _temp_row(w, stats.surf_temp[w], stats.inner_temp[w], stats.middle_temp[w])
        for w in _WHEELS
    )
    return f"{title}\n{header}\n{sep}\n{rows}\n"


def _section_pressure(stats: SetupStats, lang: str) -> str:
    have = stats.data_quality.get("pressure", False)
    if lang == "en":
        title = "## Tyre Pressures (kPa / PSI)"
        header = "| Wheel | kPa | PSI |"
        sep = "|-------|-----|-----|"
    else:
        title = "## Pressões (kPa / PSI)"
        header = "| Roda | kPa | PSI |"
        sep = "|------|-----|-----|"

    if not have:
        return f"{title}\n{_na(lang)}\n"

    rows = "\n".join(_pressure_row(w, stats.pressure_kpa[w]) for w in _WHEELS)
    return f"{title}\n{header}\n{sep}\n{rows}\n"


def _section_imbalances(stats: SetupStats, lang: str) -> str:
    have = stats.data_quality.get("surf_temp", False)
    if lang == "en":
        title = "## Temperature Imbalances"
        if not have:
            return f"{title}\n{_na(lang)}\n"
        return (
            f"{title}\n"
            f"- Left-Right: {stats.temp_imbalance_left_right:+.1f} °C "
            "(positive = left warmer)\n"
            f"- Front-Rear: {stats.temp_imbalance_front_rear:+.1f} °C "
            "(positive = front warmer)\n"
            f"- Diagonal FL-RR: {stats.temp_imbalance_diag_flrr:+.1f} °C\n"
            f"- Diagonal FR-RL: {stats.temp_imbalance_diag_frrl:+.1f} °C\n"
        )

    title = "## Desequilíbrios de Temperatura"
    if not have:
        return f"{title}\n{_na(lang)}\n"
    return (
        f"{title}\n"
        f"- Esquerda-Direita: {stats.temp_imbalance_left_right:+.1f} °C "
        "(positivo = esq. mais quente)\n"
        f"- Dianteiro-Traseiro: {stats.temp_imbalance_front_rear:+.1f} °C "
        "(positivo = diant. mais quente)\n"
        f"- Diagonal FL-RR: {stats.temp_imbalance_diag_flrr:+.1f} °C\n"
        f"- Diagonal FR-RL: {stats.temp_imbalance_diag_frrl:+.1f} °C\n"
    )


def _section_g_lat(stats: SetupStats, lang: str) -> str:
    have = stats.data_quality.get("g_lat", False)
    if lang == "en":
        title = "## Lateral G-Forces"
        if not have:
            return f"{title}\n{_na(lang)}\n"
        return (
            f"{title}\n"
            f"- Maximum: {stats.g_lat_max:.2f} g\n"
            f"- Average: {stats.g_lat_mean:.2f} g\n"
        )

    title = "## Forças Laterais"
    if not have:
        return f"{title}\n{_na(lang)}\n"
    return (
        f"{title}\n"
        f"- Máxima: {stats.g_lat_max:.2f} g\n"
        f"- Média: {stats.g_lat_mean:.2f} g\n"
    )


def _section_slip(stats: SetupStats, lang: str) -> str:
    have = stats.data_quality.get("slip_angle", False)
    if lang == "en":
        title = "## Slip Angle (degrees)"
        if not have:
            return f"{title}\n{_na(lang)}\n"
        return (
            f"{title}\n"
            f"- Average: {stats.slip_angle_mean:.2f}°\n"
            f"- P95: {stats.slip_angle_p95:.2f}°\n"
        )

    title = "## Slip Angle (graus)"
    if not have:
        return f"{title}\n{_na(lang)}\n"
    return (
        f"{title}\n"
        f"- Médio: {stats.slip_angle_mean:.2f}°\n"
        f"- P95: {stats.slip_angle_p95:.2f}°\n"
    )


def _section_electronics(stats: SetupStats, lang: str) -> str:
    tcs_ok = stats.data_quality.get("tcs", False)
    asm_ok = stats.data_quality.get("asm", False)
    na = _na(lang)

    tcs = f"{stats.tcs_active_pct:.1f}%" if tcs_ok else na
    asm = f"{stats.asm_active_pct:.1f}%" if asm_ok else na

    if lang == "en":
        return (
            "## Electronics\n"
            f"- TCS active: {tcs}\n"
            f"- ASM active: {asm}\n"
        )
    return (
        "## Eletrônicos\n"
        f"- TCS ativo: {tcs}\n"
        f"- ASM ativo: {asm}\n"
    )


def _section_suspension(stats: SetupStats, lang: str) -> str:
    have = stats.data_quality.get("suspension", False)
    if lang == "en":
        title = "## Suspension (average position)"
        header = "| Wheel | Position |"
        sep = "|-------|----------|"
    else:
        title = "## Suspensão (posição média)"
        header = "| Roda | Posição |"
        sep = "|------|---------|"

    if not have:
        return f"{title}\n{_na(lang)}\n"

    rows = "\n".join(_sus_row(w, stats.sus_mean[w]) for w in _WHEELS)
    return f"{title}\n{header}\n{sep}\n{rows}\n"


def _section_pedals(stats: SetupStats, lang: str) -> str:
    have = stats.data_quality.get("pedal_ticks", False)
    if lang == "en":
        title = "## Pedals (% of time)"
        if not have:
            return f"{title}\n{_na(lang)}\n"
        return (
            f"{title}\n"
            f"- Full throttle: {stats.full_throttle_pct:.1f}%\n"
            f"- Full brake: {stats.full_brake_pct:.1f}%\n"
            f"- Coasting: {stats.coasting_pct:.1f}%\n"
            f"- Throttle+Brake overlap: {stats.throttle_brake_pct:.1f}%\n"
        )

    title = "## Pedais (% do tempo)"
    if not have:
        return f"{title}\n{_na(lang)}\n"
    return (
        f"{title}\n"
        f"- Acelerador fundo: {stats.full_throttle_pct:.1f}%\n"
        f"- Freio fundo: {stats.full_brake_pct:.1f}%\n"
        f"- Rolagem livre: {stats.coasting_pct:.1f}%\n"
        f"- Acelerador+Freio simultâneos: {stats.throttle_brake_pct:.1f}%\n"
    )


# ---------------------------------------------------------------------------
# System prompt (GT7 knowledge base)
# ---------------------------------------------------------------------------

_SYSTEM_EN = """\
# Role
You are an experienced racing engineer specialised in Gran Turismo 7. \
Your task is to analyse telemetry data and provide concrete, actionable setup \
suggestions. Always use the structured format defined in the Instructions section \
of the user message.

# GT7 Tyre Temperature Reference (°C)
Ideal operating range varies by tyre compound. Use this to assess whether the \
recorded temperatures indicate the car is within, below, or above the working range.

| Compound         | Too Cold | Optimal     | Too Hot |
|------------------|----------|-------------|---------|
| Comfort (H/M/S)  | <50      | 50–80       | >90     |
| Sport (H/M/S)    | <65      | 65–95       | >105    |
| Racing Hard (RH) | <70      | 70–100      | >110    |
| Racing Medium (RM)| <75     | 75–105      | >115    |
| Racing Soft (RS) | <80      | 80–110      | >120    |
| Racing Inter (RI)| <60      | 60–90       | >100    |

Inner vs. outer temperature imbalance indicates camber setting:
- Inner hotter than outer: too much negative camber → reduce camber magnitude
- Outer hotter than inner: too little negative camber → increase camber magnitude
- Difference > 10 °C: significant; difference > 20 °C: critical

# GT7 Tyre Pressure Reference
- Typical target range: 220–290 kPa (32–42 PSI)
- Higher pressure → firmer tyre, less contact patch, higher peak temps
- Lower pressure → more compliant, more grip on smooth surfaces, risk of overheating edges
- Warm/hot pressure matters more than cold; these values are mid-stint averages

""" + build_params_section("en") + "\n"

_SYSTEM_PT = """\
# Papel
Você é um engenheiro de corrida experiente especializado em Gran Turismo 7. \
Sua tarefa é analisar dados de telemetria e fornecer sugestões de setup concretas \
e acionáveis. Sempre use o formato estruturado definido na seção de Instruções \
da mensagem do usuário.

# Referência de Temperatura de Pneus no GT7 (°C)
A faixa ideal de operação varia conforme o composto. Use estes valores para avaliar \
se as temperaturas registradas indicam que o carro está dentro, abaixo ou acima da \
faixa de trabalho.

| Composto             | Frio demais | Ideal       | Quente demais |
|----------------------|-------------|-------------|---------------|
| Conforto (H/M/S)     | <50         | 50–80       | >90           |
| Sport (H/M/S)        | <65         | 65–95       | >105          |
| Racing Hard (RH)     | <70         | 70–100      | >110          |
| Racing Medium (RM)   | <75         | 75–105      | >115          |
| Racing Soft (RS)     | <80         | 80–110      | >120          |
| Racing Inter (RI)    | <60         | 60–90       | >100          |

Desequilíbrio entre temperatura interna e externa indica câmber:
- Interna mais quente que externa: câmber negativo excessivo → diminuir magnitude
- Externa mais quente que interna: câmber negativo insuficiente → aumentar magnitude
- Diferença > 10 °C: significativa; diferença > 20 °C: crítica

# Referência de Pressão de Pneus no GT7
- Faixa típica de alvo: 220–290 kPa (32–42 PSI)
- Pressão mais alta → pneu mais rígido, menor área de contato, temperaturas mais altas
- Pressão mais baixa → mais conformidade, mais aderência em superfícies lisas, risco de superaquecimento nas bordas
- A pressão a quente (meio do stint) importa mais; estes valores são médias do stint

""" + build_params_section("pt") + "\n"


def build_system_prompt(lang: str = "pt") -> str:
    """Return the GT7 knowledge-base system prompt for the given language."""
    return _SYSTEM_EN if lang == "en" else _SYSTEM_PT


# ---------------------------------------------------------------------------
# Instructions (appended to the user message)
# ---------------------------------------------------------------------------

def _instructions_pt(level: str) -> str:
    focus_extra = (
        "\n[Nível Avançado: adicionar suspensão (ride height, rigidez de molas), "
        "distribuição de frenagem, aerodinâmica]"
        if level == "advanced"
        else "\n[Nível Básico: focar em pressão de pneus, câmber "
        "(via desequilíbrio de temperatura inner vs outer), diferencial/TCS]"
    )

    return (
        "# Instruções\n"
        "Por favor, analise os dados acima e forneça sugestões de setup no seguinte "
        "formato para CADA aspecto relevante:\n\n"
        "**Diagnóstico:** [o que os dados indicam]\n"
        "**Sugestão:** [ação concreta a tomar no menu de setup do GT7, com valores numéricos sempre que possível]\n"
        "**Porquê:** [explicação didática do princípio de engenharia]\n"
        f"{focus_extra}\n\n"
        "Regra importante: seções marcadas como 'dados não disponíveis' indicam que "
        "aquela métrica não foi coletada nesta sessão. "
        "**Não faça sugestões para parâmetros cujos dados estejam indisponíveis.** "
        "Mencione apenas que os dados não foram coletados se for relevante.\n\n"
        "Aviso: estas sugestões são baseadas em padrões estatísticos de telemetria. "
        "Aplique incrementalmente, testando uma mudança por vez."
    )


def _instructions_en(level: str) -> str:
    focus_extra = (
        "\n[Advanced level: add suspension (ride height, spring stiffness), "
        "brake balance, aerodynamics]"
        if level == "advanced"
        else "\n[Basic level: focus on tyre pressure, camber "
        "(via inner vs outer temperature imbalance), differential/TCS]"
    )

    return (
        "# Instructions\n"
        "Please analyse the data above and provide setup suggestions in the following "
        "format for EACH relevant aspect:\n\n"
        "**Diagnosis:** [what the data indicates]\n"
        "**Suggestion:** [concrete action to take in the GT7 setup menu, with numeric values whenever possible]\n"
        "**Why:** [didactic explanation of the engineering principle]\n"
        f"{focus_extra}\n\n"
        "Important rule: sections marked as 'data not available' indicate that metric "
        "was not collected in this session. "
        "**Do not make suggestions for parameters whose data is unavailable.** "
        "Only mention the absence of data if it is relevant to the analysis.\n\n"
        "Warning: these suggestions are based on statistical telemetry patterns. "
        "Apply them incrementally, testing one change at a time."
    )


# ---------------------------------------------------------------------------
# User message builder
# ---------------------------------------------------------------------------

def build(stats: SetupStats, track: str, level: str, lang: str = "pt") -> str:
    """Build the user-message portion of the LLM setup advisor prompt.

    Parameters
    ----------
    stats:
        Aggregated telemetry statistics from ``aggregator.compute()``.
    track:
        Track name (free text).
    level:
        Detail level – ``"basic"`` or ``"advanced"`` (case-insensitive).
    lang:
        Language – ``"pt"`` (default) or ``"en"``.

    Returns
    -------
    str
        User message to send to the LLM (system prompt built separately via
        ``build_system_prompt``).
    """
    level = level.lower()
    if level not in {"basic", "advanced"}:
        raise ValueError(f"level must be 'basic' or 'advanced', got {level!r}")

    laps_str = ", ".join(str(n) for n in stats.laps_analyzed) or "—"

    if lang == "en":
        session_header = "# Session Data"
        car_label = "Car"
        track_label = "Track"
        laps_label = "Laps analysed"
    else:
        session_header = "# Dados da Sessão"
        car_label = "Carro"
        track_label = "Pista"
        laps_label = "Voltas analisadas"

    sections = [
        session_header,
        f"{car_label}: {stats.car_name}",
        f"{track_label}: {track}",
        f"{laps_label}: {laps_str}",
        "",
        _section_temps(stats, lang),
        _section_pressure(stats, lang),
        _section_imbalances(stats, lang),
        _section_g_lat(stats, lang),
        _section_slip(stats, lang),
        _section_electronics(stats, lang),
    ]

    if level == "advanced":
        sections += [
            _section_suspension(stats, lang),
            _section_pedals(stats, lang),
        ]

    if lang == "en":
        sections.append(_instructions_en(level))
    else:
        sections.append(_instructions_pt(level))

    return "\n".join(sections)
