"""Alert message templates for EN and PT."""

_TEMPLATES: dict[str, dict[str, str]] = {
    "en": {
        "fuel_last_lap": "Less than one lap of fuel. Save fuel or pit now.",
        "fuel_critical": "Fuel critical. {fuel:.0f} litres remaining. {laps_text}",
        "fuel_low": "Fuel at {pct:.0f} percent. {laps_text}",
        "lap_completed": "Lap {lap} done. {lap_time}.",
        "best_lap": "New best lap! {lap_time}.",
        "final_lap": "Last lap. Take care and bring it home.",
        "engine_temp_high": "Water temp {temp:.0f} degrees. Watch the engine.",
        "tire_temp_high": "Tyre temp high. {corners}.",
        "tire_wear_excessive": "Excessive tyre wear. {corners}.",
        "tyre_wear_milestone": "Tyre wear at {wear}%.",
        "oil_temp_high": "Oil temp {temp:.0f} degrees. Watch the engine.",
        "tire_pressure_low": "Tyre pressure low. {corners}.",
        "tire_pressure_high": "Tyre pressure high. {corners}.",
        "lap_delta_warn": "You are {delta:.1f} seconds off pace.",
        "pit_window": "Box box box. {laps:.0f} laps of fuel.",
        "strategy_pit_window": "Box box box. {reason}. Pit in {laps} lap.",
        "strategy_pit_window_now": "Box box box. {reason}. Pit at the end of this lap.",
        "fuel_save_finish": "Save fuel. Bring it home.",
        "strategy_tyres_warn": "Tyres at {wear}%. Plan pit in {laps} laps.",
        "strategy_can_finish": "Fuel and tyres OK to finish. {laps} laps remaining.",
        "planned_pit_window_approaching": "Pit window opens in {laps} laps. Prepare to box.",
        "planned_pit_window_open": "Pit window open. {laps} laps to box.",
        "planned_pit_window_fuel_warn": "Box box box. Fuel for {laps:.0f} laps only.",
        "race_report": "P{pos}. {laps} laps to go. Tyres at {wear:.0f} percent average.",
        "race_report_tyre_warn": "{corner} tyre is your highest at {wear:.0f} percent. Keep an eye on it.",
        "planned_pit_missed": "Missed pit window. Window was laps {open} to {close}. Re-evaluating.",
        "planned_pit_rescheduled": "Planned stop rescheduled to lap {lap}. Fuel window.",
        "tyre_wont_reach": "Warning: tyres last {life_lap} laps. Pit window opens at lap {plan_lap}.",
    },
    "pt": {
        "fuel_last_lap": "Menos de uma volta de combustível. Economize ou vá ao box agora.",
        "fuel_critical": "Combustível crítico. {fuel:.0f} litros restantes. {laps_text}",
        "fuel_low": "Combustível em {pct:.0f} porcento. {laps_text}",
        "lap_completed": "Volta {lap} completa. {lap_time}.",
        "best_lap": "Melhor volta! {lap_time}.",
        "final_lap": "Última volta. Cuida do carro e traz pra casa.",
        "engine_temp_high": "Temperatura da água {temp:.0f} graus. Atenção ao motor.",
        "tire_temp_high": "Temperatura dos pneus alta. {corners}.",
        "tire_wear_excessive": "Desgaste excessivo de pneu. {corners}.",
        "tyre_wear_milestone": "Desgaste de pneu em {wear}%.",
        "oil_temp_high": "Temperatura do óleo {temp:.0f} graus. Atenção ao motor.",
        "tire_pressure_low": "Pressão dos pneus baixa. {corners}.",
        "tire_pressure_high": "Pressão dos pneus alta. {corners}.",
        "lap_delta_warn": "Você está {delta:.1f} segundos abaixo do ritmo.",
        "pit_window": "Box box box. {laps:.0f} voltas de combustível.",
        "strategy_pit_window": "Box box box. {reason}. Pit em {laps} volta.",
        "strategy_pit_window_now": "Box box box. {reason}. Pit ao fim desta volta.",
        "fuel_save_finish": "Economize combustível. Traga o carro pra casa.",
        "strategy_tyres_warn": "Pneus a {wear}%. Planejar pit em {laps} voltas.",
        "strategy_can_finish": "Combustível e pneus OK para terminar. {laps} voltas restantes.",
        "planned_pit_window_approaching": "Janela de pit em {laps} voltas. Prepare-se.",
        "planned_pit_window_open": "Janela de pit aberta. {laps} voltas para o box.",
        "planned_pit_window_fuel_warn": "Box box box. Combustível para {laps:.0f} voltas.",
        "race_report": "P{pos}. {laps} voltas restantes. Pneus com desgaste médio de {wear:.0f} porcento.",
        "race_report_tyre_warn": "Pneu {corner} com maior desgaste, em {wear:.0f} porcento. Fique atento.",
        "planned_pit_missed": "Janela de pit perdida. Voltas {open} a {close}. Reavaliando.",
        "planned_pit_rescheduled": "Parada reagendada para a volta {lap}. Janela de combustível.",
        "tyre_wont_reach": "Atenção: pneus estimados até volta {life_lap}. Janela abre na {plan_lap}.",
    },
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


def format_alert(alert_type: str, lang: str, **kwargs: object) -> str:
    tmpl = _TEMPLATES.get(lang, _TEMPLATES["en"]).get(alert_type, "")
    if not tmpl:
        return ""
    return tmpl.format(**kwargs)
