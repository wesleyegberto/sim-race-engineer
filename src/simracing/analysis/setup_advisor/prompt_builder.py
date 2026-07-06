from __future__ import annotations

from simracing.analysis.setup_advisor.aggregator import SetupStats

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
        "**Sugestão:** [ação concreta a tomar no menu de setup do GT7]\n"
        "**Porquê:** [explicação didática do princípio de engenharia]\n"
        f"{focus_extra}\n\n"
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
        "**Suggestion:** [concrete action to take in the GT7 setup menu]\n"
        "**Why:** [didactic explanation of the engineering principle]\n"
        f"{focus_extra}\n\n"
        "Warning: these suggestions are based on statistical telemetry patterns. "
        "Apply them incrementally, testing one change at a time."
    )


def build(stats: SetupStats, track: str, level: str, lang: str = "pt") -> str:
    """Build a prompt string for the LLM setup advisor.

    Parameters
    ----------
    stats:
        Aggregated telemetry statistics from ``aggregator.compute()``.
    track:
        Track name (free text).
    level:
        Detail level – ``"basic"`` or ``"advanced"`` (case-insensitive).
    lang:
        Language for instructions – ``"pt"`` (default) or ``"en"``.

    Returns
    -------
    str
        Full prompt to send as the user message to the LLM.
    """
    level = level.lower()
    if level not in {"basic", "advanced"}:
        raise ValueError(f"level must be 'basic' or 'advanced', got {level!r}")

    laps_str = ", ".join(str(n) for n in stats.laps_analyzed) or "—"

    if lang == "en":
        persona = (
            "# Context\n"
            "You are an experienced racing engineer specialised in Gran Turismo 7. "
            "Analyse the telemetry data below and provide concrete, actionable setup "
            "suggestions. Use the structured format defined in the Instructions section."
        )
        session_header = "# Session Data"
        car_label = "Car"
        track_label = "Track"
        laps_label = "Laps analysed"
    else:
        persona = (
            "# Contexto\n"
            "Você é um engenheiro de corrida experiente especializado em Gran Turismo 7. "
            "Analise os dados de telemetria abaixo e forneça sugestões de setup concretas "
            "e acionáveis. Use o formato estruturado definido na seção de Instruções."
        )
        session_header = "# Dados da Sessão"
        car_label = "Carro"
        track_label = "Pista"
        laps_label = "Voltas analisadas"

    sections = [
        persona,
        "",
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
