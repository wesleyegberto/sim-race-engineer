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
        return "No lap selected."
    all_df = pd.concat(dfs.values(), ignore_index=True)
    max_t = all_df["lap_time_s"].max().item() if "lap_time_s" in all_df.columns else 0.0  # type: ignore[union-attr]
    max_spd = all_df["speed_kmh"].max().item() if "speed_kmh" in all_df.columns else 0.0  # type: ignore[union-attr]
    if max_t < 0.01 and max_spd < 1.0:
        return (
            "Session has no driving data — timer stopped and car stationary.<br>"
            "Select a parquet recorded during a lap on track."
        )
    return ""


def _car_name_from_df(df: pd.DataFrame) -> str:
    from simraceengineer.analysis.setup_advisor.aggregator import lookup_car_name

    if "car_code" not in df.columns:
        return ""
    code = int(df["car_code"].dropna().iloc[0]) if len(df) > 0 else 0
    name = lookup_car_name(code)
    return f"🚗 {name}" if name != "Unknown" else ""


def register(app) -> None:  # type: ignore[type-arg]
    from dash import Input, Output, State, no_update

    from .charts import build_timeseries, build_track_map, build_tire_temps

    @app.callback(
        Output("track-map", "figure"),
        Output("timeseries-chart", "figure"),
        Output("tire-temp-chart", "figure"),
        Input("lap-selector", "value"),
        Input("color-by", "value"),
        Input("track-axes", "value"),
    )
    def update_charts(  # type: ignore[return]
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

    # ── Setup Advisor callbacks ─────────────────────────────────────────────

    @app.callback(
        Output("advisor-no-session-msg", "style"),
        Output("advisor-lap-range-wrapper", "style"),
        Output("advisor-lap-range", "min"),
        Output("advisor-lap-range", "max"),
        Output("advisor-lap-range", "marks"),
        Output("advisor-lap-range", "value"),
        Output("advisor-car-display", "children"),
        Input("main-tabs", "value"),
    )
    def update_advisor_info(tab: str):  # type: ignore[return]
        if tab != "advisor-tab":
            return (no_update,) * 7

        _HIDDEN = {"display": "none"}

        if not _ALL_LAPS:
            return (
                {"color": "#666", "fontSize": "12px"},
                _HIDDEN,
                0, 1, {0: "0", 1: "1"}, [0, 1],
                "",
            )

        laps = sorted(_ALL_LAPS.keys())
        marks = {n: str(n) for n in laps}
        df_first = next(iter(_ALL_LAPS.values()))
        return (
            _HIDDEN,
            {},
            laps[0],
            laps[-1],
            marks,
            [laps[0], laps[-1]],
            _car_name_from_df(df_first),
        )

    @app.callback(
        Output("advisor-report", "children"),
        Input("advisor-run-btn", "n_clicks"),
        State("advisor-lap-range", "value"),
        State("advisor-track", "value"),
        State("advisor-level", "value"),
        State("advisor-backend", "value"),
        State("advisor-model", "value"),
        prevent_initial_call=True,
    )
    def run_advisor(  # type: ignore[return]
        _n_clicks: int,
        lap_range: list[int] | None,
        track: str | None,
        level: str,
        backend: str,
        model: str,
    ) -> str:
        from simraceengineer.analysis.setup_advisor import aggregator
        from simraceengineer.analysis.setup_advisor import prompt_builder  # type: ignore[attr-defined]
        from simraceengineer.analysis.setup_advisor.aggregator import lookup_car_name
        from simraceengineer.config import AppConfig

        if not _ALL_LAPS:
            return "_No session loaded._"
        if not track:
            return "_Select a track before analyzing._"

        if lap_range:
            lo, hi = int(lap_range[0]), int(lap_range[1])
            laps_sel = {k: v for k, v in _ALL_LAPS.items() if lo <= k <= hi}
        else:
            laps_sel = _ALL_LAPS

        df = pd.concat(laps_sel.values(), ignore_index=True) if laps_sel else pd.concat(_ALL_LAPS.values(), ignore_index=True)

        car_code = 0
        if "car_code" in df.columns and len(df) > 0:
            car_code = int(df["car_code"].dropna().iloc[0])  # type: ignore[arg-type]
        car_name = lookup_car_name(car_code)

        stats = aggregator.compute(df, car_name=car_name)  # type: ignore[arg-type]

        try:
            cfg = AppConfig()
            cfg.llm_backend = backend or cfg.llm_backend
            cfg.llm_model = model or cfg.llm_model

            lang = cfg.voice_language
            system = prompt_builder.build_system_prompt(lang)
            prompt = prompt_builder.build(
                stats, track=track, level=level or "basic", lang=lang
            )

            from simraceengineer.analysis.setup_advisor.llm_client import create_client

            client = create_client(cfg)
            report = client.generate(prompt, system=system)
        except ImportError as exc:
            return (
                f"**SDK not installed:** {exc}\n\n"
                "Install with: `pip install 'sim-race-engineer[advisor]'`"
            )
        except Exception as exc:
            return f"**Error calling LLM:** {exc}"

        return report
