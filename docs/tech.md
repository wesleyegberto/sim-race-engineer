# Tech Doc

## Architecture

```
simraceengineer/
├── telemetry/
│   ├── models.py           ← TelemetryData + TireData (game-agnostic)
│   ├── provider.py         ← TelemetryProvider (ABC)
│   └── gt7/
│       ├── parser.py       ← Salsa20 decrypt + struct parse (296-byte packets)
│       └── receiver.py     ← UDP socket + heartbeat loop
├── voice/
│   ├── __init__.py         ← VoiceService (daemon thread, speak queue)
│   ├── tts_service.py      ← Piper TTS wrapper (offline, afplay playback)
│   ├── alert_engine.py     ← Threshold monitor → alert text + strategy alerts
│   └── templates.py        ← Message templates EN / PT
├── recording/
│   └── lap_recorder.py     ← Session + lap lifecycle, Parquet writer
├── strategy/
│   ├── race_strategy.py    ← RaceStrategyEngine: computes optimal pit window (fuel + tyres)
│   ├── planned_strategy.py ← PlannedStrategyMonitor: tracks user-defined stops by lap
│   └── stint_tracker.py    ← StintTracker: wear rate per lap, tyre change detection
├── analysis/
│   ├── cli.py              ← Entry point `sim-race-analyze` (launches Dash server)
│   ├── loader.py           ← Reads session.parquet / lap_*.parquet into DataFrames
│   ├── layout.py           ← Dash layout: lap selector, chart grid
│   ├── charts.py           ← Plotly figure builders (speed, throttle, brakes, tyres…)
│   └── callbacks.py        ← Dash callbacks: lap selection → chart update
├── config.py               ← AppConfig (INI read/write, ~/sim-race-engineer/sim-race.conf)
└── dashboard/
    ├── app.py              ← pygame event loop + layout
    └── widgets/
        ├── gauge.py        ← Circular speed / RPM gauges
        ├── bar.py          ← Throttle / brake / clutch / fuel bars
        ├── tire_widget.py  ← 4-corner tyre tiles + slip borders + suspension bars
        ├── g_meter.py      ← G-force circular trace
        ├── slip_angle.py   ← Horizontal slip angle bar
        ├── strategy_panel.py ← Pit strategy overlay (fuel, tyres, planned stops)
        ├── settings_panel.py ← Settings overlay (IP, voice, recording, strategy)
        └── help_panel.py   ← In-app UI guide (3 tabs)
```

## Dependencies

### Core (always installed)

| Library | Version | Why |
|---|---|---|
| `pygame-ce` | ≥ 2.4 | Dashboard UI — Community Edition has better performance and active maintenance. Handles 2D widget rendering, event loop, and font rendering. |
| `pycryptodome` | ≥ 3.20 | Salsa20 decryption for GT7 packets. `pysalsa20` is abandoned; pycryptodome is the maintained drop-in with wheels for all platforms. |
| `pandas` | ≥ 2.0 | Aggregates per-frame telemetry into DataFrames for Parquet writes and analysis viewer reads. |
| `pyarrow` | ≥ 15.0 | Parquet engine with Snappy compression. Chosen over `fastparquet` for better type support and API stability. |

### Optional — `[voice]`

| Library | Version | Why |
|---|---|---|
| `piper-tts` | ≥ 1.2.0 | Offline TTS with ONNX models — no cloud, no network latency. Models are auto-downloaded from HuggingFace on first run. Voices: `en_US-lessac-medium`, `pt_BR-faber-medium`. |

### Optional — `[analysis]`

| Library | Version | Why |
|---|---|---|
| `plotly` | ≥ 5.20 | Interactive charts (zoom, hover) for lap analysis. |
| `dash` | ≥ 2.17 | Local web server for the post-session viewer. Launched via `sim-race-analyze`. |

### Dev

| Library | Why |
|---|---|
| `hatchling` | Build backend; packages `src/simraceengineer` as a wheel. |
| `ruff` | Linting + formatting in a single tool. |
| `pytest` + `pytest-asyncio` | Unit tests; `asyncio_mode=auto` for coroutines. |

## Game Protocol

### GT7 Protocol

- GT7 sends 296-byte UDP packets on port **33740** at ~60 Hz
- Encrypted with **Salsa20**, key `"Simulator Interface Packet GT7 ver 0.0"`
- Requires a heartbeat packet (`b"A"`) every ~100 ms to port **33739**

Full protocol reference: [`docs/gt7-telemetry.md`](docs/gt7-telemetry.md)

## Design Decisions

### Per-lap Parquet writes
Each lap is written to `lap_<N>.parquet` immediately on crossing the finish line, not only at session end. This prevents data loss on crash. At session close, all files are concatenated into `session.parquet` via `pd.concat`.

### Stateless strategy engine
`RaceStrategyEngine.compute()` is pure (no side effects): it receives a telemetry snapshot and returns `StrategyResult`. Planned strategy state (`PlannedStrategyMonitor`) is held in memory by `AlertEngine` and reset each session.

### Non-blocking voice queue
`VoiceService` uses `queue.SimpleQueue` drained by a daemon thread. The pygame event loop never blocks on audio synthesis. Alerts with the same `key` are rate-limited by `_maybe_fire_interval` to prevent spam.

### Analysis viewer decoupled from dashboard
`sim-race-analyze` is an independent process that reads recorded Parquet files. There is no real-time communication with the dashboard. This keeps the dashboard free of Dash/Plotly dependencies and allows running the viewer on a separate machine.

### INI config
`AppConfig` uses `configparser` (stdlib) — no extra dependency. File lives at `~/sim-race-engineer/sim-race.conf` and is created with defaults on first run.

## Pending — Linux and Windows Support

### `afplay` — macOS only
`tts_service.py` calls `subprocess.run(["afplay", ...])` to play the WAV generated by Piper. This command does not exist on Linux or Windows.

**Required fix:**
- Linux: `aplay` (ALSA) or `paplay` (PulseAudio/PipeWire)
- Windows: `winsound.PlaySound()` (stdlib) or `playsound` lib
- Implement platform detection in `_play_wav(path)` and dispatch to the correct player.

### `piper-tts` — native wheels
`piper-tts` depends on native binaries. Verify wheel availability on PyPI for `linux/x86_64`, `linux/aarch64`, and `win/x86_64`. If missing, the standalone `piper` binary may need to be bundled and invoked via subprocess instead of the Python API.

### POSIX signals — Windows
`main.py` registers `signal.SIGTERM` and `signal.SIGINT`. On Windows, `SIGTERM` is not reliably supported by Python. Use `signal.SIGBREAK` or `atexit` as a fallback.

### Config and data paths
`Path.home() / "sim-race-engineer"` works on all three platforms. No changes needed.

### pygame-ce on Linux
Requires `libsdl2-dev` installed via the system package manager. Document in the installation README.

### UDP socket on Windows
`receiver.py` sets `SO_REUSEADDR`. On Windows this flag has different semantics (allows multiple processes to bind the same port). Evaluate whether `SO_EXCLUSIVEADDRUSE` is needed to prevent conflicts.
