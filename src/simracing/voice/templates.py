"""Alert message templates for EN and PT."""

_TEMPLATES: dict[str, dict[str, str]] = {
    "en": {
        "fuel_critical": "Fuel critical. {fuel:.0f} litres remaining. {laps_text}",
        "fuel_low": "Fuel at {pct:.0f} percent. {laps_text}",
        "lap_completed": "Lap {lap} done. {lap_time}.",
        "best_lap": "New best lap! {lap_time}.",
        "final_lap": "Final lap. Push!",
        "engine_temp_high": "Water temp {temp:.0f} degrees. Watch the engine.",
        "tire_temp_high": "Tyre temp high. {corners}.",
        "tire_wear_excessive": "Excessive tyre wear. {corners}.",
    },
    "pt": {
        "fuel_critical": "Combustível crítico. {fuel:.0f} litros restantes. {laps_text}",
        "fuel_low": "Combustível em {pct:.0f} porcento. {laps_text}",
        "lap_completed": "Volta {lap} completa. {lap_time}.",
        "best_lap": "Melhor volta! {lap_time}.",
        "final_lap": "Última volta. Vai!",
        "engine_temp_high": "Temperatura da água {temp:.0f} graus. Atenção ao motor.",
        "tire_temp_high": "Temperatura dos pneus alta. {corners}.",
        "tire_wear_excessive": "Desgaste excessivo de pneu. {corners}.",
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


def hot_corners_text(temps: list[float], threshold: float, lang: str) -> str:
    names = _CORNERS.get(lang, _CORNERS["en"])
    hot = [names[i] for i, t in enumerate(temps) if t > threshold]
    return ", ".join(hot)


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


def format_alert(alert_type: str, lang: str, **kwargs: object) -> str:
    tmpl = _TEMPLATES.get(lang, _TEMPLATES["en"]).get(alert_type, "")
    if not tmpl:
        return ""
    return tmpl.format(**kwargs)
