"""Pure chart-building functions — no Dash dependency, only plotly."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

_LAP_COLORS = ["#00ff88", "#ff8800", "#4488ff", "#ff44aa", "#ffff44", "#aa44ff"]

_COLORSCALES: dict[str, str] = {
    "speed_kmh": "Jet",
    "brake": "Reds",
    "throttle": "Greens",
    "gear": "Viridis",
}

_TIRE_COLORS = {
    "fl": ("#4499ff", "FL"),
    "fr": ("#ff4444", "FR"),
    "rl": ("#44ffaa", "RL"),
    "rr": ("#ffaa00", "RR"),
}

_SLIP_THRESHOLD = 8.0  # degrees — above this is significant oversteer


def build_track_map(
    dfs: dict[int, pd.DataFrame],
    color_by: str = "speed_kmh",
    x_col: str = "pos_x",
    y_col: str = "pos_y",
) -> go.Figure:
    """Scatter plot of the circuit trace, coloured by a telemetry metric.

    Overlays markers for TCS (wheelspin) and ASM (oversteer/stability) events.
    """
    scale = _COLORSCALES.get(color_by, "Jet")
    fig = go.Figure()

    for i, (lap, df) in enumerate(sorted(dfs.items())):
        if x_col not in df.columns or y_col not in df.columns:
            continue
        metric = df[color_by] if color_by in df.columns else None

        # Main trace
        fig.add_trace(
            go.Scatter(
                x=df[x_col],
                y=df[y_col],
                mode="markers",
                marker=dict(
                    size=2,
                    color=metric,
                    colorscale=scale,
                    showscale=(i == 0 and metric is not None),
                    colorbar=dict(thickness=12, len=0.8, title=dict(text=color_by, side="right")),
                ),
                name=f"Lap {lap}",
                legendgroup=f"lap{lap}",
                hovertemplate=(
                    f"Lap {lap}<br>{x_col}: %{{x:.0f}} m<br>"
                    f"{y_col}: %{{y:.0f}} m<br>"
                    f"{color_by}: %{{marker.color:.2f}}<extra></extra>"
                ),
            )
        )

        # TCS intervention markers (wheelspin)
        if "tcs_active" in df.columns:
            tcs = df[df["tcs_active"]]
            if not tcs.empty:
                fig.add_trace(go.Scatter(
                    x=tcs[x_col], y=tcs[y_col],
                    mode="markers",
                    marker=dict(size=7, color="#ffdd00", symbol="circle-open", line=dict(width=1.5)),
                    name=f"TCS L{lap}",
                    legendgroup=f"tcs{lap}",
                    hovertemplate=f"TCS L{lap}<br>%{{x:.0f}}, %{{y:.0f}}<extra></extra>",
                ))

        # ASM intervention markers (oversteer / instability)
        if "asm_active" in df.columns:
            asm = df[df["asm_active"]]
            if not asm.empty:
                fig.add_trace(go.Scatter(
                    x=asm[x_col], y=asm[y_col],
                    mode="markers",
                    marker=dict(size=7, color="#ff4444", symbol="x", line=dict(width=1.5)),
                    name=f"ASM L{lap}",
                    legendgroup=f"asm{lap}",
                    hovertemplate=f"ASM L{lap}<br>%{{x:.0f}}, %{{y:.0f}}<extra></extra>",
                ))

    fig.update_layout(
        template="plotly_dark",
        title=dict(text="Track Map", x=0.5),
        yaxis=dict(scaleanchor="x", scaleratio=1),
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        uirevision="track-map",
    )
    return fig


def build_timeseries(dfs: dict[int, pd.DataFrame]) -> go.Figure:
    """Four-row subplot: throttle/brake, gear (stepped), speed, slip angle — shared x-axis."""
    fig = make_subplots(
        rows=4,
        cols=1,
        shared_xaxes=True,
        subplot_titles=("Throttle / Brake", "Gear", "Speed", "Slip Angle"),
        vertical_spacing=0.055,
        row_heights=[0.32, 0.13, 0.30, 0.25],
    )

    for i, (lap, df) in enumerate(sorted(dfs.items())):
        color = _LAP_COLORS[i % len(_LAP_COLORS)]
        show = i == 0

        # Row 1 — throttle (positive) + brake (negative mirror)
        fig.add_trace(go.Scatter(
            x=df["lap_time_s"], y=df["throttle"],
            mode="lines", line=dict(color="#00cc44", width=1),
            fill="tozeroy", fillcolor="rgba(0,204,68,0.20)",
            name=f"Throttle L{lap}", legendgroup=f"lap{lap}",
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df["lap_time_s"], y=-df["brake"],
            mode="lines", line=dict(color="#ff3333", width=1),
            fill="tozeroy", fillcolor="rgba(255,51,51,0.20)",
            name=f"Brake L{lap}", legendgroup=f"lap{lap}", showlegend=False,
        ), row=1, col=1)

        # Row 2 — gear (stepped line)
        fig.add_trace(go.Scatter(
            x=df["lap_time_s"], y=df["gear"],
            mode="lines", line=dict(color=color, width=1.5, shape="hv"),
            name=f"Gear L{lap}", legendgroup=f"lap{lap}", showlegend=False,
        ), row=2, col=1)

        # Row 3 — speed trace
        fig.add_trace(go.Scatter(
            x=df["lap_time_s"], y=df["speed_kmh"],
            mode="lines", line=dict(color=color, width=1.5),
            name=f"Speed L{lap}", legendgroup=f"lap{lap}", showlegend=show,
        ), row=3, col=1)

        # Row 4 — slip angle + oversteer zone markers
        if "slip_angle_deg" in df.columns:
            fig.add_trace(go.Scatter(
                x=df["lap_time_s"], y=df["slip_angle_deg"],
                mode="lines", line=dict(color=color, width=1.2),
                name=f"Slip L{lap}", legendgroup=f"lap{lap}", showlegend=False,
            ), row=4, col=1)

            # Highlight frames where |slip| exceeds threshold
            over = df[df["slip_angle_deg"].abs() > _SLIP_THRESHOLD]
            if not over.empty:
                fig.add_trace(go.Scatter(
                    x=over["lap_time_s"], y=over["slip_angle_deg"],
                    mode="markers",
                    marker=dict(size=4, color="#ff4444", opacity=0.7),
                    name=f"Oversteer L{lap}", legendgroup=f"lap{lap}", showlegend=show,
                ), row=4, col=1)

    # Reference lines for slip threshold
    fig.add_hline(y=_SLIP_THRESHOLD, line_dash="dot", line_color="#ff4444",
                  line_width=1, opacity=0.5, row=4, col=1)
    fig.add_hline(y=-_SLIP_THRESHOLD, line_dash="dot", line_color="#ff4444",
                  line_width=1, opacity=0.5, row=4, col=1)
    fig.add_hline(y=0, line_dash="dot", line_color="#555555",
                  line_width=1, opacity=0.5, row=4, col=1)

    fig.update_layout(
        template="plotly_dark",
        height=780,
        margin=dict(l=55, r=20, t=50, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        uirevision="timeseries",
    )
    fig.update_yaxes(range=[-1.05, 1.05], title_text="Input", row=1, col=1)
    fig.update_yaxes(tickmode="linear", tick0=0, dtick=1, title_text="Gear", row=2, col=1)
    fig.update_yaxes(title_text="km/h", row=3, col=1)
    fig.update_yaxes(title_text="deg", row=4, col=1)
    fig.update_xaxes(title_text="Lap Time (s)", row=4, col=1)

    return fig


def build_tire_temps(dfs: dict[int, pd.DataFrame]) -> go.Figure:
    """Line chart with surface temperature for all four tyres."""
    _dashes = ["solid", "dash", "dot", "dashdot"]
    fig = go.Figure()

    for i, (lap, df) in enumerate(sorted(dfs.items())):
        dash = _dashes[i % len(_dashes)]
        for pos, (color, label) in _TIRE_COLORS.items():
            col = f"tire_{pos}_temp"
            if col not in df.columns:
                continue
            fig.add_trace(go.Scatter(
                x=df["lap_time_s"],
                y=df[col],
                mode="lines",
                line=dict(color=color, width=1.5, dash=dash),
                name=f"{label} L{lap}",
                legendgroup=f"tire_{pos}",
                hovertemplate=f"{label} L{lap}: %{{y:.0f}} °C<extra></extra>",
            ))

    fig.update_layout(
        template="plotly_dark",
        height=220,
        margin=dict(l=55, r=20, t=35, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        uirevision="tire-temps",
        title=dict(text="Tire Temperature", x=0.5, font=dict(size=13)),
    )
    fig.update_yaxes(title_text="°C")
    fig.update_xaxes(title_text="Lap Time (s)")
    return fig
