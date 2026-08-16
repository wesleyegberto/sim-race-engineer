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

_GT7_TRACKS = [
    "Alsace Village",
    "Autodromo Nazionale di Monza",
    "Blue Moon Bay Speedway",
    "Brands Hatch",
    "Circuit de Barcelona-Catalunya",
    "Circuit de la Sarthe",
    "Circuit de Sainte-Croix",
    "Daytona International Speedway",
    "Deep Forest Raceway",
    "Dragon Trail Gardens",
    "Fuji International Speedway",
    "Grand Valley Speedway",
    "High Speed Ring",
    "Interlagos",
    "Kyoto Driving Park",
    "Laguna Seca",
    "Lake Louise",
    "Mount Panorama Motor Racing Circuit",
    "Nurburgring Grand Prix Circuit",
    "Nurburgring Nordschleife",
    "Red Bull Ring",
    "Sardegna Road Track",
    "Special Stage Route X",
    "Spa-Francorchamps",
    "Suzuka Circuit",
    "Tokyo Expressway",
    "Trial Mountain Circuit",
    "Tsukuba Circuit",
    "Watkins Glen International",
    "Willow Springs International Raceway",
]

_TRACK_OPTIONS = [{"label": t, "value": t} for t in _GT7_TRACKS]

_LEVEL_OPTIONS = [
    {"label": "Basic (pressure, camber, differential)", "value": "basic"},
    {"label": "Advanced (+ suspension, brakes, aero)", "value": "advanced"},
]

_BACKEND_OPTIONS = [
    {"label": "OpenAI compatible (LM Studio, LocalAI…)", "value": "openai"},
    {"label": "Ollama (local)", "value": "ollama"},
    {"label": "Anthropic API", "value": "anthropic"},
]

_DROPDOWN_STYLE = {
    "backgroundColor": _SURFACE,
    "color": _TEXT,
    "border": f"1px solid {_BORDER}",
    "fontFamily": "monospace",
}

_LABEL_STYLE = {"color": "#888", "fontSize": "12px", "marginBottom": "4px"}


def _advisor_tab(llm_backend: str, llm_model: str) -> dcc.Tab:
    return dcc.Tab(
        label="Setup Advisor",
        value="advisor-tab",
        style={"backgroundColor": _SURFACE, "color": "#888", "border": f"1px solid {_BORDER}"},
        selected_style={"backgroundColor": _DARK, "color": _ACCENT, "border": f"1px solid {_BORDER}"},
        children=[
            html.Div(
                style={"padding": "12px 16px", "maxWidth": "900px"},
                children=[
                    # ── Car info ────────────────────────────────────────────
                    html.Div(
                        id="advisor-car-display",
                        style={"color": _ACCENT, "fontSize": "13px", "marginBottom": "8px"},
                        children="",
                    ),
                    # ── Lap range ───────────────────────────────────────────
                    html.Div(
                        style={"marginBottom": "12px"},
                        children=[
                            html.Label("Laps to analyze:", style=_LABEL_STYLE),
                            html.Div(
                                id="advisor-lap-slider-container",
                                children=[
                                    html.Span(
                                        "Select a session first.",
                                        id="advisor-no-session-msg",
                                        style={"color": "#666", "fontSize": "12px"},
                                    ),
                                    # Slider lives in the initial layout so State("advisor-lap-range")
                                    # is always valid for the client-side renderer.
                                    # dcc.RangeSlider (Dash 4) does not accept a `style` prop,
                                    # so visibility is controlled via the wrapper div.
                                    html.Div(
                                        id="advisor-lap-range-wrapper",
                                        style={"display": "none"},
                                        children=[
                                            dcc.RangeSlider(
                                                id="advisor-lap-range",
                                                min=0, max=1, step=1,
                                                value=[0, 1],
                                                marks={0: "0", 1: "1"},
                                                allowCross=False,
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),
                    # ── Track + Level row ───────────────────────────────────
                    html.Div(
                        style={"display": "flex", "gap": "16px", "flexWrap": "wrap", "marginBottom": "12px"},
                        children=[
                            html.Div(
                                style={"flex": "2", "minWidth": "180px"},
                                children=[
                                    html.Label("Track:", style=_LABEL_STYLE),
                                    dcc.Dropdown(
                                        id="advisor-track",
                                        options=_TRACK_OPTIONS,
                                        placeholder="Select track…",
                                        clearable=False,
                                        style=_DROPDOWN_STYLE,
                                    ),
                                ],
                            ),
                            html.Div(
                                style={"flex": "2", "minWidth": "200px"},
                                children=[
                                    html.Label("Analysis level:", style=_LABEL_STYLE),
                                    dcc.RadioItems(
                                        id="advisor-level",
                                        options=_LEVEL_OPTIONS,
                                        value="basic",
                                        labelStyle={"display": "block", "color": _TEXT, "marginBottom": "4px"},
                                        inputStyle={"marginRight": "6px"},
                                    ),
                                ],
                            ),
                        ],
                    ),
                    # ── LLM config row ──────────────────────────────────────
                    html.Div(
                        style={"display": "flex", "gap": "16px", "flexWrap": "wrap", "marginBottom": "16px"},
                        children=[
                            html.Div(
                                style={"flex": "1", "minWidth": "140px"},
                                children=[
                                    html.Label("Backend LLM:", style=_LABEL_STYLE),
                                    dcc.Dropdown(
                                        id="advisor-backend",
                                        options=_BACKEND_OPTIONS,
                                        value=llm_backend,
                                        clearable=False,
                                        style=_DROPDOWN_STYLE,
                                    ),
                                ],
                            ),
                            html.Div(
                                style={"flex": "2", "minWidth": "160px"},
                                children=[
                                    html.Label("Model:", style=_LABEL_STYLE),
                                    dcc.Input(
                                        id="advisor-model",
                                        type="text",
                                        value=llm_model,
                                        placeholder="ex: gemma4:12b",
                                        style={
                                            "width": "100%",
                                            "backgroundColor": _SURFACE,
                                            "color": _TEXT,
                                            "border": f"1px solid {_BORDER}",
                                            "fontFamily": "monospace",
                                            "padding": "6px 8px",
                                            "boxSizing": "border-box",
                                        },
                                    ),
                                ],
                            ),
                        ],
                    ),
                    # ── Run button ──────────────────────────────────────────
                    html.Button(
                        "Analyze Setup",
                        id="advisor-run-btn",
                        n_clicks=0,
                        style={
                            "backgroundColor": _ACCENT,
                            "color": _DARK,
                            "border": "none",
                            "padding": "8px 20px",
                            "fontFamily": "monospace",
                            "fontWeight": "bold",
                            "cursor": "pointer",
                            "fontSize": "14px",
                            "marginBottom": "16px",
                        },
                    ),
                    # ── Warning card ────────────────────────────────────────
                    html.Div(
                        style={
                            "border": "1px solid #554400",
                            "backgroundColor": "#221a00",
                            "padding": "8px 12px",
                            "marginBottom": "16px",
                            "fontSize": "12px",
                            "color": "#ccaa00",
                        },
                        children=(
                            "⚠ Suggestions based on telemetry statistical patterns. "
                            "Apply incrementally — test one change at a time."
                        ),
                    ),
                    # ── Report area ─────────────────────────────────────────
                    dcc.Loading(
                        id="advisor-loading",
                        type="circle",
                        color=_ACCENT,
                        children=dcc.Markdown(
                            id="advisor-report",
                            children="",
                            style={
                                "backgroundColor": _SURFACE,
                                "padding": "12px",
                                "border": f"1px solid {_BORDER}",
                                "color": _TEXT,
                                "fontFamily": "monospace",
                                "fontSize": "13px",
                                "minHeight": "100px",
                                "whiteSpace": "pre-wrap",
                            },
                        ),
                    ),
                ],
            ),
        ],
    )


def create_layout(
    lap_numbers: list[int],
    filename: str,
    llm_backend: str = "ollama",
    llm_model: str = "gemma4:12b",
) -> html.Div:
    sorted_laps = sorted(lap_numbers)
    lap_options = [{"label": f"Lap {n}", "value": n} for n in sorted_laps]
    preferred = 1 if 1 in lap_numbers else (sorted_laps[0] if sorted_laps else None)
    default_laps = [preferred] if preferred is not None else []

    analysis_tab_content = html.Div(
        children=[
            html.Div(
                style={
                    "padding": "10px 16px",
                    "borderBottom": f"1px solid {_BORDER}",
                    "backgroundColor": _SURFACE,
                },
                children=[
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
        ]
    )

    return html.Div(
        style={"backgroundColor": _DARK, "minHeight": "100vh", "fontFamily": "monospace", "color": _TEXT},
        children=[
            html.Div(
                style={
                    "padding": "8px 16px 0",
                    "borderBottom": f"1px solid {_BORDER}",
                    "backgroundColor": _SURFACE,
                },
                children=[
                    html.H3(
                        f"SimRacing Analysis — {filename}",
                        style={"color": _ACCENT, "margin": "0 0 8px 0", "fontSize": "16px"},
                    ),
                ],
            ),
            dcc.Tabs(
                id="main-tabs",
                value="analysis-tab",
                style={"backgroundColor": _SURFACE},
                children=[
                    dcc.Tab(
                        label="Analysis",
                        value="analysis-tab",
                        style={"backgroundColor": _SURFACE, "color": "#888", "border": f"1px solid {_BORDER}"},
                        selected_style={"backgroundColor": _DARK, "color": _ACCENT, "border": f"1px solid {_BORDER}"},
                        children=[analysis_tab_content],
                    ),
                    _advisor_tab(llm_backend, llm_model),
                ],
            ),
        ],
    )
