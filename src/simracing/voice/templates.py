"""Alert message templates for EN and PT."""

_TEMPLATES: dict[str, dict[str, str]] = {
    "en": {
        "fuel_critical": "Fuel critical. {fuel:.0f} litres remaining. {laps_text}",
        "fuel_low": "Fuel at {pct:.0f} percent. {laps_text}",
    },
    "pt": {
        "fuel_critical": "Combustível crítico. {fuel:.0f} litros restantes. {laps_text}",
        "fuel_low": "Combustível em {pct:.0f} porcento. {laps_text}",
    },
}


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
