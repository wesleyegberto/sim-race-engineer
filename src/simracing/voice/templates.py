"""Alert message templates for EN and PT."""

import random

_TEMPLATES: dict[str, dict[str, str]] = {
    "en": {
        "fuel_last_lap": "Fuel last lap. Box now. Box now.",
        "fuel_critical": "Fuel critical. {fuel:.0f} litres. {laps_text}",
        "fuel_low": "Fuel low. {laps_text}",
        "lap_completed": "Lap {lap}. {lap_time}.",
        "best_lap": "Best lap. {lap_time}.",
        "final_lap": "Last lap. Take care and bring it home.",
        "final_lap_save_fuel": "Last lap. Fuel low. Lift and coast. Bring it home.",
        "engine_temp_high": "Water temp {temp:.0f}. Manage the engine.",
        "tire_temp_high": "Tyre temps high on {corners}.",
        "tire_wear_excessive": "High inner wear on {corners}. Monitor.",
        "tyre_wear_milestone": "Tyre wear at {wear} percent.",
        "oil_temp_high": "Oil temp {temp:.0f}. Manage the engine.",
        "tire_pressure_low": "Low tyre pressure on {corners}.",
        "tire_pressure_high": "High tyre pressure on {corners}.",
        "lap_delta_warn": "{delta:.1f} seconds off pace.",
        "pit_window": "Box box box. Fuel for {laps:.0f} laps.",
        "strategy_pit_window": "Box box box. {reason}. Box in {laps} laps.",
        "strategy_pit_window_now": "Box box box. {reason}. Box this lap.",
        "strategy_tyres_warn": "Tyres at {wear} percent. Box window in {laps} laps.",
        "strategy_can_finish": "Fuel and tyres to the flag. {laps} laps remaining.",
        "planned_pit_window_approaching": "Pit window in {laps} laps. Prepare to box.",
        "planned_pit_window_open": "Window open. {laps} laps to box.",
        "planned_pit_window_fuel_warn": "Box box box. Fuel for {laps:.0f} laps only.",
        "race_report": "P{pos}. {laps} laps to go. Tyres at {wear:.0f} percent average.",
        "race_report_no_wear": "P{pos}. {laps} laps to go.",
        "race_report_tyre_warn": "{corner} leading in wear at {wear:.0f} percent. Monitor.",
        "planned_pit_missed": "Window missed. Laps {open} to {close}. Stand by.",
        "planned_pit_rescheduled": "Box rescheduled. New target lap {lap}.",
        "tyre_wont_reach": "Caution. Tyres to lap {life_lap}. Window at lap {plan_lap}.",
        "fuel_to_finish": "Fuel to the flag. {laps} laps remaining. No more fuel calls.",
        "laps_to_finish": "{laps} laps to go.",
        "fuel_save_mode": "Fuel is tight. Save fuel. Lift and coast where possible.",
        "strategy_check_in": "Strategy check: fuel for {fuel_laps:.0f} laps. Box lap {pit_lap}. {laps} to go.",
        "strategy_check_in_ok": "Strategy check: on plan. Fuel for {fuel_laps:.0f} laps. {laps} laps to go.",
        "strategy_check_in_critical": "Strategy critical. Fuel for {fuel_laps:.0f} laps only. Box lap {pit_lap}.",
        "strategy_revised": "Strategy revised. Box now lap {new_lap} instead of {old_lap}.",
        "fuel_save_recommend": "Fuel tight. Save fuel. Lift and coast to extend {save_laps} laps.",
    },
    "pt": {
        "fuel_last_lap": "Combustível na última volta. Box agora, box agora.",
        "fuel_critical": "Combustível crítico. {fuel:.0f} litros. {laps_text}",
        "fuel_low": "Combustível baixo. {laps_text}",
        "lap_completed": "Volta {lap}. {lap_time}.",
        "best_lap": "Melhor volta. {lap_time}.",
        "final_lap": "Última volta. Cuida do carro e traz pra casa.",
        "final_lap_save_fuel": "Última volta. Combustível no limite. Gerencia e traz pra casa.",
        "engine_temp_high": "Água em {temp:.0f} graus. Gerencia o motor.",
        "tire_temp_high": "Temperatura alta. {corners}.",
        "tire_wear_excessive": "Desgaste interno alto. {corners}. Monitora.",
        "tyre_wear_milestone": "Pneu em {wear} por cento.",
        "oil_temp_high": "Óleo em {temp:.0f} graus. Gerencia o motor.",
        "tire_pressure_low": "Pressão baixa em {corners}.",
        "tire_pressure_high": "Pressão alta em {corners}.",
        "lap_delta_warn": "{delta:.1f} segundos fora do ritmo.",
        "pit_window": "Box box box. {laps:.0f} voltas de combustível.",
        "strategy_pit_window": "Box box box. {reason}. Box em {laps} voltas.",
        "strategy_pit_window_now": "Box box box. {reason}. Box nesta volta.",
        "strategy_tyres_warn": "Pneus em {wear} por cento. Janela em {laps} voltas.",
        "strategy_can_finish": "Combustível e pneus para a bandeirada. {laps} voltas.",
        "planned_pit_window_approaching": "Janela em {laps} voltas. Prepare-se para o box.",
        "planned_pit_window_open": "Janela aberta. {laps} voltas para o box.",
        "planned_pit_window_fuel_warn": "Box box box. Combustível para {laps:.0f} voltas.",
        "race_report": "P{pos}. {laps} voltas restantes. Pneus em {wear:.0f} por cento.",
        "race_report_no_wear": "P{pos}. {laps} voltas restantes.",
        "race_report_tyre_warn": "Maior desgaste {corner}. {wear:.0f} por cento. Monitora.",
        "planned_pit_missed": "Janela perdida. Voltas {open} a {close}. Aguarda.",
        "planned_pit_rescheduled": "Box remarcado. Nova janela na volta {lap}.",
        "tyre_wont_reach": "Atenção. Pneu até volta {life_lap}. Janela na volta {plan_lap}.",
        "fuel_to_finish": "Combustível até a bandeirada. {laps} voltas restantes. Sem mais chamadas de combustível.",
        "laps_to_finish": "{laps} voltas restantes.",
        "fuel_save_mode": "Combustível no limite. Economize. Levanta o pé onde possível.",
        "strategy_check_in": "Revisão de estratégia: combustível para {fuel_laps:.0f} voltas. Box na volta {pit_lap}. {laps} a cumprir.",
        "strategy_check_in_ok": "Revisão de estratégia: no plano. Combustível para {fuel_laps:.0f} voltas. {laps} voltas restantes.",
        "strategy_check_in_critical": "Estratégia crítica. Combustível para {fuel_laps:.0f} voltas apenas. Box na volta {pit_lap}.",
        "strategy_revised": "Estratégia revisada. Box na volta {new_lap} em vez da volta {old_lap}.",
        "fuel_save_recommend": "Combustível no limite. Economize. Levanta o pé para ganhar {save_laps} voltas.",
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


_MULTI_OVERTAKE_TEMPLATES: dict[str, list[str]] = {
    "en": [
        "P{new_pos}. What a move! Keep pushing!",
        "P{new_pos}. Two for one! Brilliant work.",
        "P{new_pos}. Double overtake! You've got the pace.",
    ],
    "pt": [
        "P{new_pos}. Linda ultrapassagem! Bora para cima.",
        "P{new_pos}. Dois coelhos com uma cajadada! Excelente trabalho.",
        "P{new_pos}. Dupla ultrapassagem! Você tem o dom.",
    ],
}

_OVERTAKE_TEMPLATES: dict[str, list[str]] = {
    "en": [
        "P{new_pos}. Good pass. Keep pushing.",
        "P{new_pos}. Well done. Stay focused.",
        "P{new_pos}. Nice move. Maintain the pace.",
        "P{new_pos}. Position gained. Keep it up.",
        "P{new_pos}. Good work. Stay on it.",
        "P{new_pos}. Clean pass. Push on.",
    ],
    "pt": [
        "P{new_pos}. Boa ultrapassagem. Segue firme.",
        "P{new_pos}. Bela manobra. Mantém o ritmo.",
        "P{new_pos}. Muito bem. Continua assim.",
        "P{new_pos}. Posição ganha. Segue em frente.",
        "P{new_pos}. Excelente. Mantém a pressão.",
        "P{new_pos}. Bom trabalho. Foca no próximo.",
    ],
}

_OVERTAKEN_TEMPLATES: dict[str, list[str]] = {
    "en": [
        "P{new_pos}. Regroup. Stay focused.",
        "P{new_pos}. Keep your head. Push back.",
        "P{new_pos}. Stay calm. Respond.",
        "P{new_pos}. Don't panic. Keep pushing.",
        "P{new_pos}. Focus. We'll get it back.",
        "P{new_pos}. Stay with it. Manage the gap.",
    ],
    "pt": [
        "P{new_pos}. Mantém a cabeça. Foca.",
        "P{new_pos}. Calma. Reage logo.",
        "P{new_pos}. Não desiste. Busca a posição.",
        "P{new_pos}. Mantém o foco. Vamos recuperar.",
        "P{new_pos}. Continua focado. Responde.",
        "P{new_pos}. Segura. Avalia e ataca.",
    ],
}


def format_alert_random(variants: dict[str, list[str]], lang: str, **kwargs: object) -> str:
    pool = variants.get(lang, variants.get("en", []))
    if not pool:
        return ""
    return random.choice(pool).format(**kwargs)
