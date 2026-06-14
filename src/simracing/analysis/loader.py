from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_parquet(path: Path | str) -> tuple[pd.DataFrame, dict[int, pd.DataFrame]]:
    """Load a session or lap parquet file.

    Returns the full DataFrame and a dict mapping lap_number → per-lap DataFrame.
    Both DataFrames include a ``lap_time_s`` column.  When lap_time_ms is all
    zero (garage / menu recording), ``tick`` divided by 60 is used as fallback
    so the time-series charts still have a meaningful x-axis.
    """
    df = pd.read_parquet(Path(path), engine="pyarrow")
    if "lap_time_s" not in df.columns:
        if "lap_time_ms" in df.columns and df["lap_time_ms"].max() > 0:
            df["lap_time_s"] = df["lap_time_ms"] / 1000.0
        else:
            # lap timer never started — use frame index at ~60 Hz
            df["lap_time_s"] = df["tick"].astype(float) / 60.0
    laps = _split_by_lap(df)
    return df, laps


def lap_quality(df: pd.DataFrame) -> dict:
    """Return basic data-quality indicators for a lap DataFrame."""
    def _fmax(col: str) -> float:
        return float(df[col].max()) if col in df.columns else 0.0  # type: ignore[arg-type]

    return {
        "rows": len(df),
        "timer_active": _fmax("lap_time_ms") > 0,
        "car_moving": _fmax("speed_kmh") > 1.0,
        "max_throttle": _fmax("throttle"),
        "max_brake": _fmax("brake"),
        "max_gear": int(_fmax("gear")),
    }


def _split_by_lap(df: pd.DataFrame) -> dict[int, pd.DataFrame]:
    if "lap_number" not in df.columns:
        return {0: df.copy()}
    return {
        int(lap): grp.reset_index(drop=True)  # type: ignore[arg-type]
        for lap, grp in df.groupby("lap_number", sort=True)
    }
