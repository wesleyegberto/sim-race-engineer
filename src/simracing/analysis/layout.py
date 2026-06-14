"""Dash application layout — no callbacks, no side effects."""
from __future__ import annotations

from dash import dcc, html

_COLOR_OPTIONS = [
    {"label": "Speed (km/h)", "value": "speed_kmh"},
    {"label": "Brake intensity", "value": "brake"},
    {"label": "Throttle", "value": "throttle"},
    {"label": "Gear", "value": "gear"},
]

_AXES_OPTIONS = [
    {"label": "X / Y", "value": "xy"},
    {"label": "X / Z", "value": "xz"},
]

_DARK = "#111111"
_SURFACE = "#1a1a1a"
_BORDER = "#2a2a2a"
_TEXT = "#dddddd"
_ACCENT = "#00ff88"


def create_layout(lap_numbers: list[int], filename: str) -> html.Div:
    sorted_laps = sorted(lap_numbers)
    lap_options = [{"label": f"Lap {n}", "value": n} for n in sorted_laps]
    preferred = 1 if 1 in lap_numbers else (sorted_laps[0] if sorted_laps else None)
    default_laps = [preferred] if preferred is not None else []

    return html.Div(
        style={"backgroundColor": _DARK, "minHeight": "100vh", "fontFamily": "monospace", "color": _TEXT},
        children=[
            # ── Header ──────────────────────────────────────────────────────
            html.Div(
                style={
                    "padding": "10px 16px",
                    "borderBottom": f"1px solid {_BORDER}",
                    "backgroundColor": _SURFACE,
                },
                children=[
                    html.H3(
                        f"SimRacing Analysis — {filename}",
                        style={"color": _ACCENT, "margin": "0 0 10px 0", "fontSize": "16px"},
                    ),
                    html.Div(
                        style={
                            "display": "flex",
                            "gap": "24px",
                            "alignItems": "center",
                            "flexWrap": "wrap",
                        },
                        children=[
                            html.Div(
                                style={"display": "flex", "alignItems": "center", "gap": "8px"},
                                children=[
                                    html.Label("Laps:", style={"color": "#888", "whiteSpace": "nowrap"}),
                                    dcc.Checklist(
                                        id="lap-selector",
                                        options=lap_options,
                                        value=default_laps,
                                        inline=True,
                                        labelStyle={"color": _TEXT, "marginRight": "12px", "cursor": "pointer"},
                                        inputStyle={"marginRight": "4px", "cursor": "pointer"},
                                    ),
                                ],
                            ),
                            html.Div(
                                style={"display": "flex", "alignItems": "center", "gap": "8px"},
                                children=[
                                    html.Label("Track color:", style={"color": "#888", "whiteSpace": "nowrap"}),
                                    dcc.Dropdown(
                                        id="color-by",
                                        options=_COLOR_OPTIONS,
                                        value="speed_kmh",
                                        clearable=False,
                                        style={"width": "175px"},
                                    ),
                                ],
                            ),
                            html.Div(
                                style={"display": "flex", "alignItems": "center", "gap": "8px"},
                                children=[
                                    html.Label("Track axes:", style={"color": "#888", "whiteSpace": "nowrap"}),
                                    dcc.Dropdown(
                                        id="track-axes",
                                        options=_AXES_OPTIONS,
                                        value="xz",
                                        clearable=False,
                                        style={"width": "110px"},
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
            # ── Charts ──────────────────────────────────────────────────────
            html.Div(
                style={"padding": "8px 8px 0"},
                children=[dcc.Graph(id="track-map", style={"height": "440px"})],
            ),
            html.Div(
                style={"padding": "4px 8px 0"},
                children=[dcc.Graph(id="timeseries-chart")],
            ),
            html.Div(
                style={"padding": "4px 8px 8px"},
                children=[dcc.Graph(id="tire-temp-chart", style={"height": "220px"})],
            ),
        ],
    )
