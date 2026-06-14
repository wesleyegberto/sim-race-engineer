"""Dash callbacks — register against an existing Dash app instance."""
from __future__ import annotations

import pandas as pd

# Module-level storage (single-user local tool — no concurrency issues)
_ALL_LAPS: dict[int, pd.DataFrame] = {}


def set_data(laps: dict[int, pd.DataFrame]) -> None:
    global _ALL_LAPS
    _ALL_LAPS = laps


def _empty_fig(msg: str, height: int = 300):  # type: ignore[return]
    import plotly.graph_objects as go  # optional dep — only imported when needed
    fig = go.Figure()
    fig.add_annotation(
        text=msg,
        xref="paper", yref="paper", x=0.5, y=0.5,
        showarrow=False, font=dict(size=14, color="#888888"),
    )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#111111",
        plot_bgcolor="#111111",
        height=height,
        margin=dict(l=10, r=10, t=10, b=10),
    )
    return fig


def _is_trivial(dfs: dict[int, pd.DataFrame]) -> str:
    """Return a warning string if the data has no meaningful variation, else ''."""
    if not dfs:
        return "Nenhuma volta selecionada."
    all_df = pd.concat(dfs.values(), ignore_index=True)
    max_t = all_df["lap_time_s"].max().item() if "lap_time_s" in all_df.columns else 0.0  # type: ignore[union-attr]
    max_spd = all_df["speed_kmh"].max().item() if "speed_kmh" in all_df.columns else 0.0  # type: ignore[union-attr]
    if max_t < 0.01 and max_spd < 1.0:
        return (
            "Sessão sem dados de pilotagem — timer parado e carro estático.<br>"
            "Selecione um parquet gravado durante uma volta no circuito."
        )
    return ""


def register(app) -> None:  # type: ignore[type-arg]
    from dash import Input, Output

    from .charts import build_timeseries, build_track_map, build_tire_temps

    @app.callback(
        Output("track-map", "figure"),
        Output("timeseries-chart", "figure"),
        Output("tire-temp-chart", "figure"),
        Input("lap-selector", "value"),
        Input("color-by", "value"),
        Input("track-axes", "value"),
    )
    def update_charts(
        selected_laps: list[int] | None,
        color_by: str,
        axes: str,
    ):
        laps = selected_laps or (list(_ALL_LAPS.keys())[:1] if _ALL_LAPS else [])
        dfs = {lap: _ALL_LAPS[lap] for lap in laps if lap in _ALL_LAPS}
        if not dfs and _ALL_LAPS:
            first = min(_ALL_LAPS.keys())
            dfs = {first: _ALL_LAPS[first]}

        warn = _is_trivial(dfs)
        if warn:
            empty = _empty_fig(warn)
            return empty, _empty_fig(warn, height=780), _empty_fig(warn, height=220)

        x_col, y_col = ("pos_x", "pos_y") if axes == "xy" else ("pos_x", "pos_z")
        return (
            build_track_map(dfs, color_by=color_by, x_col=x_col, y_col=y_col),
            build_timeseries(dfs),
            build_tire_temps(dfs),
        )
