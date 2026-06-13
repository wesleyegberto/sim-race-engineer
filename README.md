# Sim Race Engineer

**Sim Race Engineer** is a real-time telemetry dashboard for sim racing, built in Python with pygame.
It connects to Gran Turismo 7 via UDP and displays live driving data on a second screen or overlay,
giving the driver the kind of feedback a real motorsport engineer would provide from the pit wall.

The dashboard is designed to help drivers improve lap times by making tyre state, weight transfer,
G-forces, fuel consumption, and electronic interventions immediately visible — information that is
buried inside the game's menus or simply not shown at all.

![](./img/dashboard-print-1.png)

---

## Features

### Dashboard

| Widget | Data |
|--------|------|
| Speed & RPM gauges | Current speed (km/h) and engine revs with colour-coded zones |
| RPM bar | Full-width strip for at-a-glance shift timing |
| Gear display | Current gear, neutral, reverse, and game-suggested gear |
| Pedal bars | Clutch · Brake · Throttle input (0–100%) |
| Fuel bar | Tank fill percentage |
| G-meter | Lateral and longitudinal G-force as a circular trace |
| Slip angle | Horizontal bar showing yaw between heading and velocity (oversteer) |
| Tyre tiles | Per-corner surface temperature with colour zones (cold / optimal / hot) |
| Wheel slip | Orange border = wheelspin · Red border = lockup |
| Suspension bars | Per-corner travel bar showing load distribution in real time |
| Status strip | TCS · ASM · REV limiter · Handbrake · Lights · OIL! · H₂O! chips |
| Info panel | Lap times · Race position · Fuel/lap · Laps remaining · Water/oil · Boost |
| Race status | IN RACE · PIT / MENU · FINISHED · FREE SESSION badges in the header |
| Rev flash | Optional full-screen red flash at rev limiter |

### Voice Alerts — Pit Wall Engineer

Spoken alerts via offline Piper TTS. Available in **English** and **Portuguese**.
Each alert has an independent cooldown to avoid repetition.

| Alert | Trigger | Cooldown |
|-------|---------|----------|
| Lap completed | Lap counter changes, no new best lap | — |
| Best lap | New personal best set | — |
| Final lap | Entering the last lap of a race | — |
| Lap delta | Lap time > 3 s off best (fires once, after halfway point) | once/lap |
| Fuel low | Fuel < 20% · includes estimated laps remaining | 15 s |
| Fuel critical | Fuel < 10% | 15 s |
| Pit window | 2–4 laps of fuel remaining in a race ("Box box box") | 15 s |
| Water temp | Coolant > 105 °C | 20 s |
| Oil temp | Oil > 130 °C | 20 s |
| Tyre temp | Any surface > 100 °C · names the hot corners | 30 s |
| Tyre wear | Any inner zone > 110 °C (proxy for wear) · names corners | 30 s |
| Pressure low | Any tyre < 160 kPa | 30 s |
| Pressure high | Any tyre > 250 kPa | 30 s |

All thresholds are configurable in `~/simracing/simracing.conf`.
Each alert can be individually enabled or disabled in the in-app Settings panel.

### Lap Recording

Sessions and laps are saved automatically as **Apache Parquet** (Snappy) at ~60 Hz.
No manual action required — recording starts with the session and stops at race end.

| What | Detail |
|------|--------|
| Location | `~/simracing_laps/<YYYY-MM-DDTHHMMSS>/lap_NN.parquet` |
| Per-frame | Speed · RPM · gear · throttle · brake · clutch · handbrake |
| Per-frame | Position (XYZ) · velocity · G-forces · slip angle |
| Per-frame | Tyre temps (surface + inner/mid/outer) · tyre pressure · suspension |
| Per-frame | Water temp · oil temp · fuel level · turbo boost |
| Per-lap | Lap time · fuel used · fuel avg · pedal counters |

Recording can be toggled mid-session via the **REC** button in the header.

---

## In-App Help

Press **?** (info button in the header) to open the UI Guide — a 3-tab reference panel:

| Tab | Content |
|-----|---------|
| DASHBOARD | Every widget, indicator, and colour code explained |
| APP GUIDE | Lap recording format, settings, and header controls |
| VOICE ALERTS | Each voice event, its trigger condition, and how to interpret it |

---

## Architecture

```
simracing/
├── telemetry/
│   ├── models.py           ← TelemetryData + TireData (game-agnostic)
│   ├── provider.py         ← TelemetryProvider (ABC)
│   └── gt7/
│       ├── parser.py       ← Salsa20 decrypt + struct parse (296-byte packets)
│       └── receiver.py     ← UDP socket + heartbeat loop
├── voice/
│   ├── __init__.py         ← VoiceService (daemon thread, speak queue)
│   ├── tts_service.py      ← Piper TTS wrapper (offline, afplay playback)
│   ├── alert_engine.py     ← Threshold monitor → alert text
│   └── templates.py        ← Message templates EN / PT
├── recording/
│   └── lap_recorder.py     ← Session + lap lifecycle, Parquet writer
├── config.py               ← AppConfig (INI read/write, ~/simracing/simracing.conf)
└── dashboard/
    ├── app.py              ← pygame event loop + layout
    └── widgets/
        ├── gauge.py        ← Circular speed / RPM gauges
        ├── bar.py          ← Throttle / brake / clutch / fuel bars
        ├── tire_widget.py  ← 4-corner tyre tiles + slip borders + suspension bars
        ├── g_meter.py      ← G-force circular trace
        ├── slip_angle.py   ← Horizontal slip angle bar
        ├── settings_panel.py ← Settings overlay (IP, voice, recording)
        └── help_panel.py   ← In-app UI guide (3 tabs)
```

---

## Setup

```bash
uv venv && source .venv/bin/activate

# Dashboard only
uv pip install -e ".[dev]"

# With voice alerts (requires Piper TTS models in ~/simracing/piper/)
uv pip install -e ".[dev,voice]"
```

### Piper TTS models

Download models into `~/simracing/piper/`:

```bash
# English (default)
# en_US-lessac-medium.onnx + .json

# Portuguese
# pt_BR-faber-medium.onnx + .json
```

Models are available at [rhasspy/piper](https://github.com/rhasspy/piper/blob/master/VOICES.md).

---

## Running

```bash
sim-dashboard
```

On first launch, the Settings panel opens automatically. Enter the PS5 IP address and save.
The IP is persisted to `~/simracing/simracing.conf` and reused on subsequent launches.

```bash
# Or pass the IP directly
sim-dashboard --ps5-ip 192.168.1.100

# Or via environment variable
SIMRACING_DEVICE_IP=192.168.1.100 sim-dashboard
```

The PS5 must be on the same network. Enable telemetry output in GT7:
**Options → Machine Settings → Send Vehicle Data → On**

---

## GT7 Protocol

- GT7 sends 296-byte UDP packets on port **33740** at ~60 Hz
- Encrypted with **Salsa20**, key `"Simulator Interface Packet GT7 ver 0.0"`
- Requires a heartbeat packet (`b"A"`) every ~100 ms to port **33739**

Full protocol reference: [`docs/gt7-telemetry.md`](docs/gt7-telemetry.md)

---

## Roadmap

| # | Feature | Status |
|---|---------|--------|
| 1 | G-Meter (lateral + longitudinal) | ✅ Done |
| 2 | Wheel slip per tyre (wheelspin / lockup) | ✅ Done |
| 3 | TCS / ASM / REV / HB status indicators | ✅ Done |
| 4 | Slip angle / oversteer indicator | ✅ Done |
| 5 | Suspension travel per corner | ✅ Done |
| 6 | Fuel consumption rate per lap | ✅ Done |
| 7 | Voice communication (pit-wall alerts) | ✅ Done |
| 8 | Lap recording (Parquet, ~60 Hz) | ✅ Done |
| 9 | Multi-game support (ACC, F1, iRacing) | 🔜 Pending |

---

## Adding a new game

1. Create `simracing/telemetry/<game>/` with `parser.py` + `receiver.py`
2. Implement `TelemetryProvider` (`connect` / `disconnect` / `read`)
3. Pass the instance to `DashboardApp` via `main.py`
