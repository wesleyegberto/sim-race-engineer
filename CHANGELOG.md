# Changelog

All notable changes to this project will be documented in this file.

---

## [v0.1.0] — 2026-08-15

Initial release of **Sim Race Engineer** — a real-time telemetry dashboard for Gran Turismo 7 with voice alerts, race strategy, lap recording, and post-session analysis.

### Dashboard

Live telemetry display powered by pygame-ce, designed for a second screen or overlay.

| Widget | Data shown |
|--------|-----------|
| Speed & RPM gauges | Current speed (km/h) and engine revs with colour-coded zones |
| RPM bar | Full-width strip for at-a-glance shift timing |
| Gear display | Current gear, neutral, reverse, and game-suggested gear |
| Pedal bars | Clutch · Brake · Throttle (0–100%) |
| Fuel bar | Tank fill percentage |
| G-meter | Lateral and longitudinal G-force as a circular trace |
| Slip angle | Horizontal bar showing yaw between heading and velocity (oversteer indicator) |
| Tyre tiles | Per-corner surface temperature with colour zones (cold / optimal / hot) |
| Wheel slip | Orange border = wheelspin · Red border = lockup |
| Suspension bars | Per-corner travel bar showing load distribution in real time |
| Status strip | TCS · ASM · REV limiter · Handbrake · Lights · OIL! · H₂O! chips |
| Info panel | Lap times · Race position · Fuel/lap · Laps remaining · Water/oil temp · Boost |
| Race status badge | IN RACE · PIT / MENU · FINISHED · FREE SESSION in the header |
| Rev flash | Optional full-screen red flash at rev limiter |

### Voice Communication — Pit Wall Engineer

Offline spoken alerts via **Piper TTS** in **English** and **Portuguese (PT-BR)**. Each alert has an independent cooldown to avoid repetition. Voice can be toggled and configured per-alert in the Settings panel.

**Lap events**
- Lap completed (time read aloud)
- New personal best lap
- Final lap of the race
- Lap delta warning (> 3 s off best, fires once per lap after the halfway point)

**Fuel**
- Fuel low (< 20% — includes estimated laps remaining)
- Fuel critical (< 10%)
- Fuel under 1 lap remaining
- Pit window (2–4 laps of fuel left — "Box box box")

**Thermals & tyres**
- Water temperature high (> 105 °C)
- Oil temperature high (> 130 °C)
- Tyre surface overheating (> 100 °C — names the affected corners)
- Tyre wear warning (inner zone proxy > 110 °C)
- Tyre wear percentage milestones (each 10% block above threshold)
- Tyre pressure low (< 160 kPa)
- Tyre pressure high (> 250 kPa)

**Race position**
- Position gained (single and multi-car overtake variants)
- Position lost

**Race summary**
- End-of-race report (position, laps completed, total time)
- Laps-to-finish countdown

**Strategy alerts**
- Auto strategy: in pit window, cannot finish without stopping (reason named: FUEL / TYRES / FUEL+TYRES)
- Auto strategy: tyres degrading, 2–5 laps to projected mandatory pit
- Planned stop approaching (2 laps before) — "Pit in N lap(s)"
- Planned stop now — "Box this lap. On strategy."
- Planned stop tyre warning — tyres won't last to the planned stop lap
- Planned stop missed — auto-reschedule to earliest safe lap
- Strategy revised (when auto strategy recalculates target lap)
- Strategy check-in briefing (every configurable N laps)

### Race Strategy

**Auto Strategy** — recalculated every lap from live fuel and tyre data:

| Field | Description |
|-------|-------------|
| Laps to fuel out | Fuel remaining ÷ average fuel per lap |
| Laps to tyre limit | Laps until wear reaches the configured threshold (default 80%) |
| Recommended pit lap | Earliest safe stop, accounting for pit buffer (default 1 lap) |
| Pit reason | FUEL · TYRES · FUEL+TYRES |
| Can finish direct | Whether fuel and tyres last to the end without stopping |

**Planned Strategy** — up to 3 user-defined stops with optional lap windows (e.g. `23-27`), configured via the Strategy panel (**S** key). Pit entry is detected automatically and marks the corresponding stop as done.

**Strategy Advisor** — proactive per-lap computation:

| Output | Description |
|--------|-------------|
| Fuel to finish | Total litres needed from current lap to chequered flag |
| Fuel delta | Surplus or shortfall vs. current tank level |
| Fuel-save target | Reduction per lap needed to reach the finish |
| Tyre projection | Estimated lap at which wear threshold will be reached |
| Stop window | Earliest and latest safe pit lap balancing fuel and tyres |

Tyre wear limit and pit buffer are configurable in the Strategy panel and `~/sim-race-engineer/sim-race.conf`.

### Lap Recording

Telemetry saved automatically as **Apache Parquet** (Snappy compressed) at ~60 Hz. No manual action required — recording starts with the session.

- **Location:** `~/sim-race-engineer/laps/<YYYY-MM-DDTHHMMSS>/lap_NN.parquet`
- **Per-frame fields:** speed · RPM · gear · throttle · brake · clutch · handbrake · position (XYZ) · velocity · G-forces · slip angle · tyre temps (surface + inner/mid/outer) · tyre pressure · suspension travel · water temp · oil temp · fuel level · turbo boost
- **Per-lap summary:** lap time · fuel used · fuel average · pedal counters
- **Extras:** `session.parquet` (all laps concatenated) written at session end; incomplete lap saved on exit
- Recording can be toggled mid-session via the **REC** button in the header

### Lap Analysis — Post-Session Web Viewer

Interactive browser UI (Dash + Plotly) for comparing laps after a session.

```bash
sim-analysis ~/sim-race-engineer/laps/<session-folder>
```

| Chart | Data |
|-------|------|
| Track map | Racing line from XYZ position data, coloured by speed or TCS/ASM intervention |
| Tyre temperatures | Surface temp per corner across the lap, overlaid for all selected laps |
| Timeseries | Throttle · Brake · Gear · Speed · Slip angle on a shared time axis |

### Setup Advisor (Experimental)

AI-powered car setup advisor integrated into the post-session analysis viewer. Reads aggregated telemetry from the session and produces setup change suggestions using a configurable LLM backend (Ollama, Anthropic, or OpenAI). Includes a structured catalogue of GT7 car setup parameters. Bilingual output (English / Portuguese).

### In-App Help

Press **?** (info button in the header) to open a 3-tab reference panel:

| Tab | Content |
|-----|---------|
| DASHBOARD | Every widget, indicator, and colour code explained |
| APP GUIDE | Lap recording format, settings, and header controls |
| VOICE ALERTS | Each voice event, its trigger condition, and how to interpret it |

### Settings

All thresholds and toggles live in `~/sim-race-engineer/sim-race.conf` and are also accessible via the Settings panel (**C** key) without restarting the app. Configurable options include: device IP, fuel estimation method (last lap vs. rolling average), voice language, per-alert enable/disable, temperature thresholds, tyre wear limit, pit buffer laps, and LLM provider.

### Distribution

- macOS `.app` bundle packaged with PyInstaller (`./build.sh`)
- Supports Apple Silicon (M-series) and Intel Macs
- Requires macOS 12+

[v0.0.1]: https://github.com/wesleyegberto/sim-race-engineer/releases/tag/v0.0.1
