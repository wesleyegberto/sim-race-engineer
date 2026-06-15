"""Alert message templates for EN and PT."""

_TEMPLATES: dict[str, dict[str, str]] = {
    "en": {
        "fuel_last_lap": "Fuel for less than one lap. Box now.",
        "fuel_critical": "Fuel critical. {fuel:.0f} litres. {laps_text}",
        "fuel_low": "Fuel low. {laps_text}",
        "lap_completed": "Lap {lap}. {lap_time}.",
        "best_lap": "Best lap. {lap_time}.",
        "final_lap": "Last lap. Take care and bring it home.",
        "final_lap_save_fuel": "Last lap. Fuel low. Lift and coast. Bring it home.",
        "engine_temp_high": "Water temp {temp:.0f}. Manage the engine.",
        "tire_temp_high": "Tyre temps high. {corners}.",
        "tire_wear_excessive": "High tyre wear. {corners}.",
        "tyre_wear_milestone": "Tyre wear at {wear} percent.",
        "oil_temp_high": "Oil temp {temp:.0f}. Manage the engine.",
        "tire_pressure_low": "Tyre pressure low. {corners}.",
        "tire_pressure_high": "Tyre pressure high. {corners}.",
        "lap_delta_warn": "{delta:.1f} seconds off pace.",
        "pit_window": "Box box box. Fuel for {laps:.0f} laps.",
        "strategy_pit_window": "Box box box. {reason}. Pit in {laps} laps.",
        "strategy_pit_window_now": "Box box box. {reason}. This is your box lap.",
        "strategy_tyres_warn": "Tyres at {wear} percent. Box window in {laps} laps.",
        "strategy_can_finish": "Fuel and tyres to the flag. {laps} laps remaining.",
        "planned_pit_window_approaching": "Pit window in {laps} laps. Prepare to box.",
        "planned_pit_window_open": "Window open. {laps} laps to box.",
        "planned_pit_window_fuel_warn": "Box box box. Fuel for {laps:.0f} laps only.",
        "race_report": "P{pos}. {laps} laps to go. Tyres at {wear:.0f} percent average.",
        "race_report_tyre_warn": "{corner} leading in wear at {wear:.0f} percent. Monitor.",
        "planned_pit_missed": "Missed window. Laps {open} to {close}. Re-evaluating.",
        "planned_pit_rescheduled": "Box rescheduled. Lap {lap}. Fuel window.",
        "tyre_wont_reach": "Caution. Tyres to lap {life_lap}. Window at lap {plan_lap}.",
    },
    "pt": {
        "fuel_last_lap": "Combustível para menos de uma volta. Box agora.",
        "fuel_critical": "Combustível crítico. {fuel:.0f} litros. {laps_text}",
        "fuel_low": "Combustível baixo. {laps_text}",
        "lap_completed": "Volta {lap}. {lap_time}.",
        "best_lap": "Melhor volta. {lap_time}.",
        "final_lap": "Última volta. Cuida do carro e traz pra casa.",
        "final_lap_save_fuel": "Última volta. Combustível no limite. Gerencia e traz pra casa.",
        "engine_temp_high": "Água em {temp:.0f} graus. Gerencia o motor.",
        "tire_temp_high": "Pneu quente. {corners}.",
        "tire_wear_excessive": "Desgaste alto. {corners}.",
        "tyre_wear_milestone": "Pneu em {wear} porcento.",
        "oil_temp_high": "Óleo em {temp:.0f} graus. Gerencia o motor.",
        "tire_pressure_low": "Pressão baixa. {corners}.",
        "tire_pressure_high": "Pressão alta. {corners}.",
        "lap_delta_warn": "{delta:.1f} segundos fora do ritmo.",
        "pit_window": "Box box box. {laps:.0f} voltas de combustível.",
        "strategy_pit_window": "Box box box. {reason}. Pit em {laps} voltas.",
        "strategy_pit_window_now": "Box box box. {reason}. Esta é a sua volta.",
        "strategy_tyres_warn": "Pneus em {wear} porcento. Janela em {laps} voltas.",
        "strategy_can_finish": "Combustível e pneus para a bandeirada. {laps} voltas.",
        "planned_pit_window_approaching": "Janela em {laps} voltas. Prepare-se para o box.",
        "planned_pit_window_open": "Janela aberta. {laps} voltas para o box.",
        "planned_pit_window_fuel_warn": "Box box box. Combustível para {laps:.0f} voltas.",
        "race_report": "P{pos}. {laps} voltas restantes. Pneus em {wear:.0f} porcento.",
        "race_report_tyre_warn": "Maior desgaste {corner}. {wear:.0f} porcento. Monitora.",
        "planned_pit_missed": "Janela perdida. Voltas {open} a {close}. Reavaliando.",
        "planned_pit_rescheduled": "Box remarcado. Volta {lap}. Janela de combustível.",
        "tyre_wont_reach": "Atenção. Pneu até volta {life_lap}. Janela na volta {plan_lap}.",
    },
}

_PIT_REASON_TEXT: dict[str, dict[str, str]] = {
    "en": {"FUEL": "fuel", "TYRES": "tyres", "FUEL+TYRES": "fuel and tyres"},
    "pt": {"FUEL": "combustível", "TYRES": "pneus", "FUEL+TYRES": "combustível e pneus"},
}

_CORNERS: dict[str, list[str]] = {
    "en": ["front left", "front right", "rear left", "rear right"],
    "pt": ["dianteiro esquerdo", "dianteiro direito", "traseiro esquerdo", "traseiro direito"],
}


def _lap_time_text(ms: int, lang: str) -> str:
    if ms <= 0:
        return ""
    m = ms // 60000
    s = (ms % 60000) // 1000
    t = (ms % 1000) // 100
    if lang == "pt":
        return f"{m} minuto {s} vírgula {t}" if m > 0 else f"{s} vírgula {t} segundos"
    return f"{m} minute {s} point {t}" if m > 0 else f"{s} point {t} seconds"


def hot_corners_text(temps: list[float], threshold: float, lang: str, invert: bool = False) -> str:
    names = _CORNERS.get(lang, _CORNERS["en"])
    if invert:
        corners = [names[i] for i, t in enumerate(temps) if 0 < t < threshold]
    else:
        corners = [names[i] for i, t in enumerate(temps) if t > threshold]
    return ", ".join(corners)


def _laps_text(laps: float, lang: str) -> str:
    if laps < 0:
        return ""
    if lang == "pt":
        if laps < 1.0:
            return "Menos de uma volta restante."
        n = round(laps)
        s = "s" if n != 1 else ""
        return f"{n} volta{s} restante{s}."
    if laps < 1.0:
        return "Less than one lap remaining."
    n = round(laps)
    s = "s" if n != 1 else ""
    return f"{n} lap{s} remaining."


def corner_name(lang: str, idx: int) -> str:
    return _CORNERS.get(lang, _CORNERS["en"])[idx]


def pit_reason_text(lang: str, reason: str) -> str:
    return _PIT_REASON_TEXT.get(lang, _PIT_REASON_TEXT["en"]).get(reason, reason.lower())


def format_alert(alert_type: str, lang: str, **kwargs: object) -> str:
    tmpl = _TEMPLATES.get(lang, _TEMPLATES["en"]).get(alert_type, "")
    if not tmpl:
        return ""
    return tmpl.format(**kwargs)
