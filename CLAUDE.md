# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Setup (macOS — requires SDL2 via Homebrew)
make install

# Run dashboard (with voice alerts)
make run-voice DEVICE_IP=192.168.1.x

# Run in debug mode
make run-debug DEVICE_IP=192.168.1.x

# Run post-session lap analysis web viewer
make run-analysis SESSION_DIR=~/simracing_laps/<session-folder>

# Lint
make lint

# Tests
make test

# macOS .app bundle via PyInstaller
make build
```

Single test file: `.venv/bin/pytest tests/path/to/test_file.py`

## Architecture

Python 3.11+, `pygame-ce` for the UI, `uv` for dependency management.

Entry point: `src/simracing/main.py` — loads config, starts telemetry, launches dashboard.

**Runtime flow:**
1. `AppConfig` (`config.py`) — reads `~/simracing/simracing.conf`, env vars, CLI args
2. `TelemetryController` — runs GT7 UDP receiver on a daemon thread with asyncio event loop
3. `GT7TelemetryProvider` decrypts/parses packets → pushes `TelemetryData` into a bounded `queue.Queue`
4. `DashboardApp` (`dashboard/app.py`) — pygame main loop, consumes queue each frame

**Source packages under `src/simracing/`:**

| Package | Responsibility |
|---------|---------------|
| `telemetry/gt7/` | UDP socket, Salsa20 decryption, packet parsing → `TelemetryData` |
| `dashboard/` | pygame UI: `app.py` orchestrates all widgets; `widgets/` has individual components |
| `strategy/` | `race_strategy.py` (auto pit calc), `planned_strategy.py` (user stops), `stint_tracker.py` |
| `recording/` | `lap_recorder.py` — saves per-lap telemetry to Parquet via pandas |
| `voice/` | `VoiceService` — Piper TTS alerts; each alert has its own cooldown |
| `analysis/` | Dash/Plotly web viewer for post-session lap review (`cli.py` is entry point) |

## Language

All commit messages and code comments must be written in English.

## Key Conventions

### Configuration
Every configurable threshold/toggle lives in `AppConfig` (`config.py`) and must also:
1. Map to a `[simracing]` key in `~/simracing/simracing.conf`
2. Have a corresponding control in `dashboard/widgets/settings_panel.py`
3. Be documented in the Settings tab of `dashboard/widgets/help_panel.py` (UI Guide)

### Dashboard widgets
Every new dashboard element must be documented in `docs/dashboard-guide.md` and in the Dashboard tab of `help_panel.py`.

### New features
Document in `README.md`.

### Colour palette
Colours are defined as constants in `dashboard/app.py` (prefixed `C_`). Use those constants — never hardcode RGB values in widgets.

### Strategy
`race_strategy.py` recalculates every lap from fuel/tyre averages. `planned_strategy.py` manages up to 3 user stops and fires alerts at the lap boundaries defined in the README.

### Voice alerts
Each alert in `VoiceService` is gated by a per-alert enabled flag in `AppConfig` (e.g. `voice_alert_fuel_low`). New alerts need:
1. A config flag and cooldown field in `AppConfig`
2. Wiring in `dashboard/widgets/settings_panel.py`
3. Entry in the Voice Alerts tab of `dashboard/widgets/help_panel.py` (UI Guide)
4. Documentation in `README.md`

### PyInstaller build — bundling data files
The build is driven by `build.sh` (not `SimRaceEngineer.spec`, which is auto-generated and discarded). Any non-Python file that code accesses via `Path(__file__).parent / "filename"` at runtime **must** be declared in `build.sh` with `--add-data`:

```
--add-data "src/simracing/path/to/file:simracing/path/to"
```

Format: `source_path:dest_dir_inside_bundle` (colon-separated on macOS/Linux).

Current data files bundled:
- `src/simracing/img` → `simracing/img`
- `src/simracing/analysis/setup_advisor/gt7_cars.json` → `simracing/analysis/setup_advisor`
