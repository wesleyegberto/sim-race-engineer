"""GT7 setup parameter catalogue.

Single source of truth for every adjustable parameter in the GT7 Garage → Tune menu.
Used to build LLM system-prompt sections and validate suggestions.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SetupCategory(str, Enum):
    TYRES = "tyres"
    SUSPENSION = "suspension"
    AERODYNAMICS = "aerodynamics"
    TRANSMISSION = "transmission"
    DIFFERENTIAL = "differential"
    BRAKES = "brakes"
    PERFORMANCE = "performance"
    ELECTRONICS = "electronics"


@dataclass(frozen=True)
class SetupParam:
    key: str
    category: SetupCategory
    name_en: str
    name_pt: str
    range_en: str
    range_pt: str
    # True = requires a specific upgrade part or drivetrain type
    conditional: bool = False
    condition_en: str = ""
    condition_pt: str = ""


GT7_SETUP_PARAMS: list[SetupParam] = [
    # -------------------------------------------------------------------------
    # Tyres
    # -------------------------------------------------------------------------
    SetupParam(
        key="tyre_compound",
        category=SetupCategory.TYRES,
        name_en="Tyre Compound",
        name_pt="Composto de Pneu",
        range_en="Comfort H/M/S · Sport H/M/S · Racing H/M/S/I/W (front & rear independently)",
        range_pt="Conforto D/M/S · Sport D/M/S · Racing D/M/S/I/W (dianteiro e traseiro independentes)",
    ),
    SetupParam(
        key="tyre_pressure_front",
        category=SetupCategory.TYRES,
        name_en="Tyre Pressure — Front",
        name_pt="Pressão de Pneu — Dianteiro",
        range_en="~100–400 kPa; adjust in 10–20 kPa steps; target ~220–290 kPa warm",
        range_pt="~100–400 kPa; ajuste em passos de 10–20 kPa; alvo ~220–290 kPa a quente",
    ),
    SetupParam(
        key="tyre_pressure_rear",
        category=SetupCategory.TYRES,
        name_en="Tyre Pressure — Rear",
        name_pt="Pressão de Pneu — Traseiro",
        range_en="~100–400 kPa; adjust in 10–20 kPa steps; target ~220–290 kPa warm",
        range_pt="~100–400 kPa; ajuste em passos de 10–20 kPa; alvo ~220–290 kPa a quente",
    ),
    # -------------------------------------------------------------------------
    # Suspension (requires Height-Adjustable Sports or Fully Customisable suspension)
    # -------------------------------------------------------------------------
    SetupParam(
        key="ride_height_front",
        category=SetupCategory.SUSPENSION,
        name_en="Ride Height — Front",
        name_pt="Altura de Mola — Dianteiro",
        range_en="Varies by car (mm); lower = less drag & better CG, but risk of bottoming out",
        range_pt="Varia por carro (mm); mais baixo = menos arrasto e melhor CG, risco de tocar o fundo",
        conditional=True,
        condition_en="Requires Height-Adjustable Sports or Fully Customisable Suspension",
        condition_pt="Requer Suspensão Esportiva com Ajuste de Altura ou Suspensão Totalmente Personalizável",
    ),
    SetupParam(
        key="ride_height_rear",
        category=SetupCategory.SUSPENSION,
        name_en="Ride Height — Rear",
        name_pt="Altura de Mola — Traseiro",
        range_en="Varies by car (mm); rake (rear higher than front) improves cornering",
        range_pt="Varia por carro (mm); rake (traseiro mais alto) melhora a curva",
        conditional=True,
        condition_en="Requires Height-Adjustable Sports or Fully Customisable Suspension",
        condition_pt="Requer Suspensão Esportiva com Ajuste de Altura ou Suspensão Totalmente Personalizável",
    ),
    SetupParam(
        key="spring_rate_front",
        category=SetupCategory.SUSPENSION,
        name_en="Spring Rate — Front",
        name_pt="Rigidez de Mola — Dianteiro",
        range_en="Varies by car (kgf/mm or natural frequency Hz); stiffer = less body roll, less grip on bumps",
        range_pt="Varia por carro (kgf/mm ou frequência natural Hz); mais rígido = menos rolagem, menos aderência em irregularidades",
        conditional=True,
        condition_en="Requires Fully Customisable Suspension",
        condition_pt="Requer Suspensão Totalmente Personalizável",
    ),
    SetupParam(
        key="spring_rate_rear",
        category=SetupCategory.SUSPENSION,
        name_en="Spring Rate — Rear",
        name_pt="Rigidez de Mola — Traseiro",
        range_en="Varies by car (kgf/mm or natural frequency Hz); rear slightly stiffer than front is a common baseline",
        range_pt="Varia por carro (kgf/mm ou frequência natural Hz); traseiro ligeiramente mais rígido que dianteiro é baseline comum",
        conditional=True,
        condition_en="Requires Fully Customisable Suspension",
        condition_pt="Requer Suspensão Totalmente Personalizável",
    ),
    SetupParam(
        key="damper_compression_front",
        category=SetupCategory.SUSPENSION,
        name_en="Damper — Compression (Front)",
        name_pt="Amortecedor — Compressão (Dianteiro)",
        range_en="1–10; controls how fast the suspension compresses over bumps",
        range_pt="1–10; controla a velocidade de compressão da suspensão em irregularidades",
        conditional=True,
        condition_en="Requires Fully Customisable Suspension",
        condition_pt="Requer Suspensão Totalmente Personalizável",
    ),
    SetupParam(
        key="damper_compression_rear",
        category=SetupCategory.SUSPENSION,
        name_en="Damper — Compression (Rear)",
        name_pt="Amortecedor — Compressão (Traseiro)",
        range_en="1–10; controls how fast the suspension compresses over bumps",
        range_pt="1–10; controla a velocidade de compressão da suspensão em irregularidades",
        conditional=True,
        condition_en="Requires Fully Customisable Suspension",
        condition_pt="Requer Suspensão Totalmente Personalizável",
    ),
    SetupParam(
        key="damper_extension_front",
        category=SetupCategory.SUSPENSION,
        name_en="Damper — Extension/Rebound (Front)",
        name_pt="Amortecedor — Extensão/Retorno (Dianteiro)",
        range_en="1–10; controls how fast the suspension returns after compression",
        range_pt="1–10; controla a velocidade de retorno da suspensão após compressão",
        conditional=True,
        condition_en="Requires Fully Customisable Suspension",
        condition_pt="Requer Suspensão Totalmente Personalizável",
    ),
    SetupParam(
        key="damper_extension_rear",
        category=SetupCategory.SUSPENSION,
        name_en="Damper — Extension/Rebound (Rear)",
        name_pt="Amortecedor — Extensão/Retorno (Traseiro)",
        range_en="1–10; controls how fast the suspension returns after compression",
        range_pt="1–10; controla a velocidade de retorno da suspensão após compressão",
        conditional=True,
        condition_en="Requires Fully Customisable Suspension",
        condition_pt="Requer Suspensão Totalmente Personalizável",
    ),
    SetupParam(
        key="anti_roll_bar_front",
        category=SetupCategory.SUSPENSION,
        name_en="Anti-Roll Bar — Front",
        name_pt="Barra Estabilizadora — Dianteira",
        range_en="1–7; higher = less body roll, less individual wheel travel and mechanical grip",
        range_pt="1–7; mais alto = menos rolagem, menos viagem individual da roda e grip mecânico",
        conditional=True,
        condition_en="Requires Fully Customisable Suspension",
        condition_pt="Requer Suspensão Totalmente Personalizável",
    ),
    SetupParam(
        key="anti_roll_bar_rear",
        category=SetupCategory.SUSPENSION,
        name_en="Anti-Roll Bar — Rear",
        name_pt="Barra Estabilizadora — Traseira",
        range_en="1–7; higher = less body roll, less individual wheel travel and mechanical grip",
        range_pt="1–7; mais alto = menos rolagem, menos viagem individual da roda e grip mecânico",
        conditional=True,
        condition_en="Requires Fully Customisable Suspension",
        condition_pt="Requer Suspensão Totalmente Personalizável",
    ),
    SetupParam(
        key="camber_front",
        category=SetupCategory.SUSPENSION,
        name_en="Camber Angle — Front",
        name_pt="Câmber — Dianteiro",
        range_en="0.0° to −5.0°; more negative = inner grip, less outer contact patch",
        range_pt="0,0° a −5,0°; mais negativo = mais grip interno, menor patch de contato externo",
        conditional=True,
        condition_en="Requires Fully Customisable Suspension",
        condition_pt="Requer Suspensão Totalmente Personalizável",
    ),
    SetupParam(
        key="camber_rear",
        category=SetupCategory.SUSPENSION,
        name_en="Camber Angle — Rear",
        name_pt="Câmber — Traseiro",
        range_en="0.0° to −5.0°; more negative = inner grip, less outer contact patch",
        range_pt="0,0° a −5,0°; mais negativo = mais grip interno, menor patch de contato externo",
        conditional=True,
        condition_en="Requires Fully Customisable Suspension",
        condition_pt="Requer Suspensão Totalmente Personalizável",
    ),
    SetupParam(
        key="toe_front",
        category=SetupCategory.SUSPENSION,
        name_en="Toe Angle — Front",
        name_pt="Convergência (Toe) — Dianteiro",
        range_en="−0.50° to +0.50°; toe-in (+) = stability, toe-out (−) = sharper turn-in",
        range_pt="−0,50° a +0,50°; positivo (convergência) = estabilidade, negativo (divergência) = entrada de curva mais afiada",
        conditional=True,
        condition_en="Requires Fully Customisable Suspension",
        condition_pt="Requer Suspensão Totalmente Personalizável",
    ),
    SetupParam(
        key="toe_rear",
        category=SetupCategory.SUSPENSION,
        name_en="Toe Angle — Rear",
        name_pt="Convergência (Toe) — Traseiro",
        range_en="−0.50° to +0.50°; toe-in (+) = rear stability, toe-out (−) = rotation",
        range_pt="−0,50° a +0,50°; positivo (convergência) = estabilidade traseira, negativo = rotação",
        conditional=True,
        condition_en="Requires Fully Customisable Suspension",
        condition_pt="Requer Suspensão Totalmente Personalizável",
    ),
    # -------------------------------------------------------------------------
    # Aerodynamics (requires aero parts installed via GT Auto)
    # -------------------------------------------------------------------------
    SetupParam(
        key="aero_front_downforce",
        category=SetupCategory.AERODYNAMICS,
        name_en="Front Downforce",
        name_pt="Pressão Aerodinâmica Dianteira",
        range_en="Varies by part; higher = more front grip and drag, promotes oversteer",
        range_pt="Varia por peça; mais alto = mais grip dianteiro e arrasto, promove sobreviragem",
        conditional=True,
        condition_en="Requires front aero parts installed (GT Auto → Customisation Parts)",
        condition_pt="Requer peças aerodinâmicas dianteiras instaladas (GT Auto → Peças de Customização)",
    ),
    SetupParam(
        key="aero_rear_downforce",
        category=SetupCategory.AERODYNAMICS,
        name_en="Rear Downforce",
        name_pt="Pressão Aerodinâmica Traseira",
        range_en="Varies by part; higher = more rear stability and drag, promotes understeer",
        range_pt="Varia por peça; mais alto = mais estabilidade traseira e arrasto, promove subviragem",
        conditional=True,
        condition_en="Requires rear aero parts installed (GT Auto → Customisation Parts)",
        condition_pt="Requer peças aerodinâmicas traseiras instaladas (GT Auto → Peças de Customização)",
    ),
    # -------------------------------------------------------------------------
    # Transmission (requires Sport or Fully Customisable Transmission)
    # -------------------------------------------------------------------------
    SetupParam(
        key="transmission_top_speed",
        category=SetupCategory.TRANSMISSION,
        name_en="Top Speed (Final Drive)",
        name_pt="Velocidade Máxima (Relação Final)",
        range_en="Varies by car (km/h target); adjusts all gear ratios proportionally",
        range_pt="Varia por carro (km/h alvo); ajusta todos os ratios proporcionalmente",
        conditional=True,
        condition_en="Requires Sport or Fully Customisable Transmission",
        condition_pt="Requer Câmbio Esportivo ou Totalmente Personalizável",
    ),
    SetupParam(
        key="transmission_gear_ratios",
        category=SetupCategory.TRANSMISSION,
        name_en="Individual Gear Ratios (1st–7th)",
        name_pt="Ratios de Marcha Individuais (1ª–7ª)",
        range_en="Varies by car; lower ratio = higher top speed in that gear, less acceleration",
        range_pt="Varia por carro; ratio menor = maior velocidade máxima na marcha, menos aceleração",
        conditional=True,
        condition_en="Requires Fully Customisable Transmission",
        condition_pt="Requer Câmbio Totalmente Personalizável",
    ),
    # -------------------------------------------------------------------------
    # Differential / LSD (requires LSD or Twin-Plate Clutch LSD)
    # -------------------------------------------------------------------------
    SetupParam(
        key="lsd_initial_torque",
        category=SetupCategory.DIFFERENTIAL,
        name_en="LSD — Initial Torque",
        name_pt="LSD — Torque Inicial",
        range_en="5–50 Nm; higher = more locked diff at low-torque phases (corner entry/exit)",
        range_pt="5–50 Nm; mais alto = diferencial mais travado em fases de baixo torque (entrada/saída de curva)",
        conditional=True,
        condition_en="Requires LSD (Limited-Slip Differential) upgrade",
        condition_pt="Requer upgrade de LSD (Diferencial de Deslizamento Limitado)",
    ),
    SetupParam(
        key="lsd_acceleration_sensitivity",
        category=SetupCategory.DIFFERENTIAL,
        name_en="LSD — Acceleration Sensitivity",
        name_pt="LSD — Sensibilidade de Aceleração",
        range_en="5–60; how aggressively the diff locks under throttle",
        range_pt="5–60; quão agressivamente o diferencial trava sob aceleração",
        conditional=True,
        condition_en="Requires LSD upgrade",
        condition_pt="Requer upgrade de LSD",
    ),
    SetupParam(
        key="lsd_deceleration_sensitivity",
        category=SetupCategory.DIFFERENTIAL,
        name_en="LSD — Deceleration/Braking Sensitivity",
        name_pt="LSD — Sensibilidade de Desaceleração",
        range_en="5–60; how aggressively the diff locks on lift-off or braking",
        range_pt="5–60; quão agressivamente o diferencial trava ao soltar o acelerador ou frear",
        conditional=True,
        condition_en="Requires LSD upgrade",
        condition_pt="Requer upgrade de LSD",
    ),
    # -------------------------------------------------------------------------
    # Brakes
    # -------------------------------------------------------------------------
    SetupParam(
        key="brake_balance",
        category=SetupCategory.BRAKES,
        name_en="Brake Balance (Front/Rear Bias)",
        name_pt="Distribuição de Frenagem (Dianteiro/Traseiro)",
        range_en="e.g. 6:4 to 3:7; more front = stronger braking but risk of front lock-up",
        range_pt="ex.: 6:4 a 3:7; mais dianteiro = maior potência de frenagem, risco de travamento dianteiro",
    ),
    SetupParam(
        key="brake_pressure",
        category=SetupCategory.BRAKES,
        name_en="Brake Pressure",
        name_pt="Pressão de Freio",
        range_en="80–120%; reduce if wheels lock under heavy braking",
        range_pt="80–120%; reduza se as rodas travarem em frenagens fortes",
    ),
    SetupParam(
        key="handbrake_torque",
        category=SetupCategory.BRAKES,
        name_en="Handbrake Torque",
        name_pt="Torque do Freio de Mão",
        range_en="Varies; adjusts rear braking force when handbrake is applied",
        range_pt="Varia; ajusta a força de frenagem traseira ao acionar o freio de mão",
        conditional=True,
        condition_en="Requires Hydraulic Handbrake upgrade",
        condition_pt="Requer upgrade de Freio de Mão Hidráulico",
    ),
    # -------------------------------------------------------------------------
    # Performance Adjustments
    # -------------------------------------------------------------------------
    SetupParam(
        key="ballast_weight",
        category=SetupCategory.PERFORMANCE,
        name_en="Ballast Weight",
        name_pt="Peso de Lastro",
        range_en="0–200 kg; increases car weight, lowers PP rating",
        range_pt="0–200 kg; aumenta o peso do carro, diminui o PP",
    ),
    SetupParam(
        key="ballast_position",
        category=SetupCategory.PERFORMANCE,
        name_en="Ballast Position",
        name_pt="Posição do Lastro",
        range_en="−50 (full front) to +50 (full rear); affects front-rear weight balance",
        range_pt="−50 (todo dianteiro) a +50 (todo traseiro); afeta o equilíbrio dianteiro-traseiro",
    ),
    SetupParam(
        key="power_restrictor",
        category=SetupCategory.PERFORMANCE,
        name_en="Power Restrictor",
        name_pt="Limitador de Potência",
        range_en="Varies (%); reduces engine output to lower PP",
        range_pt="Varia (%); reduz a potência do motor para diminuir o PP",
        conditional=True,
        condition_en="Requires Power Restrictor part installed",
        condition_pt="Requer peça Limitador de Potência instalada",
    ),
    SetupParam(
        key="ecu_output",
        category=SetupCategory.PERFORMANCE,
        name_en="ECU Output Level",
        name_pt="Nível de Saída do ECU",
        range_en="Varies (%); reduces engine power output via ECU mapping",
        range_pt="Varia (%); reduz a potência via mapeamento do ECU",
        conditional=True,
        condition_en="Requires ECU upgrade installed",
        condition_pt="Requer upgrade de ECU instalado",
    ),
    # -------------------------------------------------------------------------
    # Electronics / Driving Aids
    # -------------------------------------------------------------------------
    SetupParam(
        key="tcs",
        category=SetupCategory.ELECTRONICS,
        name_en="TCS — Traction Control System",
        name_pt="TCS — Controle de Tração",
        range_en="0 (off) to 10 (maximum); adjustable mid-race; lower = faster but more sliding",
        range_pt="0 (desligado) a 10 (máximo); ajustável durante a corrida; menor = mais rápido, mais deslizamento",
    ),
    SetupParam(
        key="abs",
        category=SetupCategory.ELECTRONICS,
        name_en="ABS — Anti-lock Braking System",
        name_pt="ABS — Sistema Antibloqueio",
        range_en="1 (weak) to 10 (strong); higher = more brake pressure before ABS triggers",
        range_pt="1 (fraco) a 10 (forte); mais alto = mais pressão de freio antes do ABS atuar",
    ),
    SetupParam(
        key="asm",
        category=SetupCategory.ELECTRONICS,
        name_en="ASM — Active Stability Management",
        name_pt="ASM — Controle de Estabilidade",
        range_en="0 (off) to 10 (maximum); lower = more rotation in corners",
        range_pt="0 (desligado) a 10 (máximo); menor = mais rotação em curvas",
    ),
    SetupParam(
        key="countersteering_assist",
        category=SetupCategory.ELECTRONICS,
        name_en="Countersteering Assistance",
        name_pt="Assistência de Contragolpe de Direção",
        range_en="0 (off) to 5 (maximum); helps correct oversteer automatically",
        range_pt="0 (desligado) a 5 (máximo); auxilia na correção de sobreviragem automaticamente",
    ),
]


def params_by_category() -> dict[SetupCategory, list[SetupParam]]:
    """Return params grouped by category, preserving declaration order."""
    result: dict[SetupCategory, list[SetupParam]] = {c: [] for c in SetupCategory}
    for p in GT7_SETUP_PARAMS:
        result[p.category].append(p)
    return result


def build_params_section(lang: str = "en") -> str:
    """Render the full GT7 setup parameter catalogue as a Markdown section."""
    grouped = params_by_category()

    _CATEGORY_LABELS: dict[SetupCategory, dict[str, str]] = {
        SetupCategory.TYRES:        {"en": "Tyres",            "pt": "Pneus"},
        SetupCategory.SUSPENSION:   {"en": "Suspension",       "pt": "Suspensão"},
        SetupCategory.AERODYNAMICS: {"en": "Aerodynamics",     "pt": "Aerodinâmica"},
        SetupCategory.TRANSMISSION: {"en": "Transmission",     "pt": "Câmbio"},
        SetupCategory.DIFFERENTIAL: {"en": "Differential (LSD)", "pt": "Diferencial (LSD)"},
        SetupCategory.BRAKES:       {"en": "Brakes",           "pt": "Freios"},
        SetupCategory.PERFORMANCE:  {"en": "Performance Adjustments", "pt": "Ajustes de Performance"},
        SetupCategory.ELECTRONICS:  {"en": "Electronics / Driving Aids", "pt": "Eletrônicos / Assistências"},
    }

    if lang == "en":
        header = (
            "# GT7 Setup Parameters (Garage → Tune)\n"
            "Only suggest parameters listed here. "
            "Parameters marked *[conditional]* require the corresponding upgrade part "
            "to be installed — skip them if not available for this car/session."
        )
    else:
        header = (
            "# Parâmetros de Setup do GT7 (Garagem → Ajuste)\n"
            "Sugira apenas parâmetros listados aqui. "
            "Parâmetros marcados com *[condicional]* requerem a peça de upgrade correspondente "
            "instalada — omita-os se não estiver disponível para este carro/sessão."
        )

    lines = [header]
    for category, params in grouped.items():
        if not params:
            continue
        label = _CATEGORY_LABELS[category][lang]
        lines.append(f"\n## {label}")
        for p in params:
            name = p.name_en if lang == "en" else p.name_pt
            rng = p.range_en if lang == "en" else p.range_pt
            cond = ""
            if p.conditional:
                note = p.condition_en if lang == "en" else p.condition_pt
                cond = f" *[conditional: {note}]*"
            lines.append(f"- **{name}**{cond} — {rng}")

    return "\n".join(lines)
