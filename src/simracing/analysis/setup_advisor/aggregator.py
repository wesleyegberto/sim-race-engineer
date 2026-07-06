from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

_UNKNOWN = "Desconhecido"

_cars: dict[str, str] | None = None


def _load_cars() -> dict[str, str]:
    global _cars
    if _cars is None:
        data_file = Path(__file__).parent / "gt7_cars.json"
        with data_file.open(encoding="utf-8") as fh:
            _cars = json.load(fh)
    assert _cars is not None
    return _cars


def lookup_car_name(car_code: int) -> str:
    if car_code == 0:
        return _UNKNOWN
    return _load_cars().get(str(car_code), _UNKNOWN)


# ---------------------------------------------------------------------------
# Setup statistics
# ---------------------------------------------------------------------------

_TIRE_SURF_COLS = {
    "FL": "tire_fl_temp",
    "FR": "tire_fr_temp",
    "RL": "tire_rl_temp",
    "RR": "tire_rr_temp",
}
_TIRE_INNER_COLS = {
    "FL": "tire_fl_inner",
    "FR": "tire_fr_inner",
    "RL": "tire_rl_inner",
    "RR": "tire_rr_inner",
}
_TIRE_MIDDLE_COLS = {
    "FL": "tire_fl_middle",
    "FR": "tire_fr_middle",
    "RL": "tire_rl_middle",
    "RR": "tire_rr_middle",
}
_TIRE_PRESSURE_COLS = {
    "FL": "tire_fl_pressure",
    "FR": "tire_fr_pressure",
    "RL": "tire_rl_pressure",
    "RR": "tire_rr_pressure",
}
_SUS_COLS = {
    "FL": "sus_fl",
    "FR": "sus_fr",
    "RL": "sus_rl",
    "RR": "sus_rr",
}
_TICK_COLS = (
    "full_throttle_ticks",
    "full_brake_ticks",
    "throttle_and_brake_ticks",
    "coasting_ticks",
)


@dataclass
class SetupStats:
    car_name: str
    laps_analyzed: list[int]
    # Temperaturas por pneu (médias, °C)
    surf_temp: dict[str, float]
    inner_temp: dict[str, float]
    middle_temp: dict[str, float]
    # Pressão média por pneu (kPa)
    pressure_kpa: dict[str, float]
    # Desequilíbrios de temperatura (°C, positivo = lado esq mais quente)
    temp_imbalance_left_right: float
    temp_imbalance_front_rear: float
    temp_imbalance_diag_flrr: float
    temp_imbalance_diag_frrl: float
    # Slip angle
    slip_angle_mean: float
    slip_angle_p95: float
    # G-forces
    g_lat_max: float
    g_lat_mean: float
    # Eletrônicos
    tcs_active_pct: float
    asm_active_pct: float
    # Suspensão (médias, m)
    sus_mean: dict[str, float]
    # Pedais (% sobre total de ticks por volta)
    full_throttle_pct: float
    full_brake_pct: float
    coasting_pct: float
    throttle_brake_pct: float
    # Disponibilidade de dados
    data_quality: dict[str, bool] = field(default_factory=dict)


def _col_mean(df: "pd.DataFrame", col: str) -> float:
    if col not in df.columns:
        return 0.0
    return float(df[col].fillna(0.0).mean())  # type: ignore[arg-type]


def _tire_dict_means(df: "pd.DataFrame", col_map: dict[str, str]) -> dict[str, float]:
    return {k: _col_mean(df, col) for k, col in col_map.items()}


def _all_cols_available(df: "pd.DataFrame", col_map: dict[str, str]) -> bool:
    return all(c in df.columns for c in col_map.values())


def compute(df: "pd.DataFrame", car_name: str = _UNKNOWN) -> SetupStats:
    """Aggregate telemetry DataFrame into setup statistics.

    Missing columns are treated as zero and flagged in *data_quality*.
    """
    dq: dict[str, bool] = {}

    # ---- laps ----------------------------------------------------------------
    if "lap_number" in df.columns:
        laps_analyzed: list[int] = sorted(df["lap_number"].dropna().unique().tolist())
    else:
        laps_analyzed = []

    # ---- tire temperatures ---------------------------------------------------
    dq["surf_temp"] = _all_cols_available(df, _TIRE_SURF_COLS)
    dq["inner_temp"] = _all_cols_available(df, _TIRE_INNER_COLS)
    dq["middle_temp"] = _all_cols_available(df, _TIRE_MIDDLE_COLS)

    surf_temp = _tire_dict_means(df, _TIRE_SURF_COLS)
    inner_temp = _tire_dict_means(df, _TIRE_INNER_COLS)
    middle_temp = _tire_dict_means(df, _TIRE_MIDDLE_COLS)

    # ---- pressure ------------------------------------------------------------
    dq["pressure"] = _all_cols_available(df, _TIRE_PRESSURE_COLS)
    pressure_kpa = _tire_dict_means(df, _TIRE_PRESSURE_COLS)

    # ---- temperature imbalances (use surface temps as reference) -------------
    fl = surf_temp["FL"]
    fr = surf_temp["FR"]
    rl = surf_temp["RL"]
    rr = surf_temp["RR"]
    temp_imbalance_left_right = (fl + rl) / 2.0 - (fr + rr) / 2.0
    temp_imbalance_front_rear = (fl + fr) / 2.0 - (rl + rr) / 2.0
    temp_imbalance_diag_flrr = fl - rr
    temp_imbalance_diag_frrl = fr - rl

    # ---- slip angle ----------------------------------------------------------
    dq["slip_angle"] = "slip_angle_deg" in df.columns
    if dq["slip_angle"]:
        abs_slip = df["slip_angle_deg"].abs().fillna(0.0)
        slip_angle_mean = float(abs_slip.mean())  # type: ignore[arg-type]
        slip_angle_p95 = float(abs_slip.quantile(0.95))  # type: ignore[arg-type]
    else:
        slip_angle_mean = 0.0
        slip_angle_p95 = 0.0

    # ---- G-forces ------------------------------------------------------------
    dq["g_lat"] = "g_lat" in df.columns
    if dq["g_lat"]:
        g_lat_series = df["g_lat"].fillna(0.0)
        g_lat_max = float(g_lat_series.abs().max())  # type: ignore[arg-type]
        g_lat_mean = float(g_lat_series.abs().mean())  # type: ignore[arg-type]
    else:
        g_lat_max = 0.0
        g_lat_mean = 0.0

    # ---- electronics ---------------------------------------------------------
    dq["tcs"] = "tcs_active" in df.columns
    if dq["tcs"]:
        tcs_active_pct = float(df["tcs_active"].fillna(False).astype(bool).mean() * 100.0)
    else:
        tcs_active_pct = 0.0

    dq["asm"] = "asm_active" in df.columns
    if dq["asm"]:
        asm_active_pct = float(df["asm_active"].fillna(False).astype(bool).mean() * 100.0)
    else:
        asm_active_pct = 0.0

    # ---- suspension ----------------------------------------------------------
    dq["suspension"] = _all_cols_available(df, _SUS_COLS)
    sus_mean = _tire_dict_means(df, _SUS_COLS)

    # ---- pedals (tick counters are per-lap totals, repeated across rows) -----
    dq["pedal_ticks"] = all(c in df.columns for c in _TICK_COLS)
    if dq["pedal_ticks"] and "lap_number" in df.columns:
        # Group by lap, take max per lap (all rows in same lap share same value),
        # then average across laps to get a representative lap.
        per_lap = df.groupby("lap_number")[list(_TICK_COLS)].max()
        tick_totals = per_lap.sum(axis=1)  # type: ignore[union-attr]
        nonzero = tick_totals[tick_totals > 0]
        if len(nonzero) > 0:
            lap_idx = nonzero.index  # type: ignore[union-attr]
            full_throttle_pct = float(  # type: ignore[arg-type]
                (per_lap.loc[lap_idx, "full_throttle_ticks"] / nonzero).mean() * 100.0  # type: ignore[index]
            )
            full_brake_pct = float(  # type: ignore[arg-type]
                (per_lap.loc[lap_idx, "full_brake_ticks"] / nonzero).mean() * 100.0  # type: ignore[index]
            )
            throttle_brake_pct = float(  # type: ignore[arg-type]
                (per_lap.loc[lap_idx, "throttle_and_brake_ticks"] / nonzero).mean() * 100.0  # type: ignore[index]
            )
            coasting_pct = float(  # type: ignore[arg-type]
                (per_lap.loc[lap_idx, "coasting_ticks"] / nonzero).mean() * 100.0  # type: ignore[index]
            )
        else:
            full_throttle_pct = full_brake_pct = throttle_brake_pct = coasting_pct = 0.0
    elif dq["pedal_ticks"]:
        # No lap_number — use single-row max as best effort
        row = df[list(_TICK_COLS)].max()
        total = row.sum()
        if total > 0:
            full_throttle_pct = float(row["full_throttle_ticks"] / total * 100.0)
            full_brake_pct = float(row["full_brake_ticks"] / total * 100.0)
            throttle_brake_pct = float(row["throttle_and_brake_ticks"] / total * 100.0)
            coasting_pct = float(row["coasting_ticks"] / total * 100.0)
        else:
            full_throttle_pct = full_brake_pct = throttle_brake_pct = coasting_pct = 0.0
    else:
        full_throttle_pct = full_brake_pct = throttle_brake_pct = coasting_pct = 0.0

    return SetupStats(
        car_name=car_name,
        laps_analyzed=laps_analyzed,
        surf_temp=surf_temp,
        inner_temp=inner_temp,
        middle_temp=middle_temp,
        pressure_kpa=pressure_kpa,
        temp_imbalance_left_right=temp_imbalance_left_right,
        temp_imbalance_front_rear=temp_imbalance_front_rear,
        temp_imbalance_diag_flrr=temp_imbalance_diag_flrr,
        temp_imbalance_diag_frrl=temp_imbalance_diag_frrl,
        slip_angle_mean=slip_angle_mean,
        slip_angle_p95=slip_angle_p95,
        g_lat_max=g_lat_max,
        g_lat_mean=g_lat_mean,
        tcs_active_pct=tcs_active_pct,
        asm_active_pct=asm_active_pct,
        sus_mean=sus_mean,
        full_throttle_pct=full_throttle_pct,
        full_brake_pct=full_brake_pct,
        coasting_pct=coasting_pct,
        throttle_brake_pct=throttle_brake_pct,
        data_quality=dq,
    )
