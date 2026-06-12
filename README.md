# Sim Race Engineer

**Sim Race Engineer** is a real-time telemetry dashboard for sim racing, built in Python with pygame.
It connects to Gran Turismo 7 via UDP and displays live driving data on a second screen or overlay,
giving the driver the kind of feedback a real motorsport engineer would provide from the pit wall.

The dashboard is designed to help drivers improve lap times by making tyre state, weight transfer,
G-forces, fuel consumption, and electronic interventions immediately visible — information that is
buried inside the game's menus or simply not shown at all.

![](./img/dashboard-print-1.png)

---

## What Sim Race Engineer shows

| Widget | Data |
|--------|------|
| Speed & RPM gauges | Current speed (km/h) and engine revs with colour-coded zones |
| RPM bar | Full-width strip for at-a-glance shift timing |
| Gear display | Current gear, neutral, reverse, and game-suggested gear |
| Pedal bars | Clutch · Brake · Throttle input (0–100%) |
| Fuel bar | Tank fill percentage |
| G-meter | Lateral and longitudinal G-force as a circular trace |
| Slip angle | Horizontal bar showing yaw angle between heading and velocity vector |
| Tire tiles | Per-corner surface temperature with colour zones (cold / optimal / hot) |
| Wheel slip | Orange border = wheelspin · Red border = lockup |
| Suspension bars | Per-corner travel bar showing load distribution in real time |
| Status strip | TCS · ASM · REV limiter · Handbrake · Lights · OIL! · H₂O! chips |
| Info panel | Lap times · Fuel/lap · Laps remaining · Water/oil temps · Boost |

Full interpretation guide: [`docs/dashboard-guide.md`](docs/dashboard-guide.md)

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
| 7 | Voice communication (pit-wall alerts) | 🔜 Pending |
| 8 | Multi-game support (ACC, F1, iRacing) | 🔜 Pending |

Full detail: [`docs/roadmap.md`](docs/roadmap.md)

---

## Architecture

```
simracing/
├── telemetry/
│   ├── models.py           ← TelemetryData (game-agnostic model)
│   ├── provider.py         ← TelemetryProvider (ABC)
│   └── gt7/
│       ├── parser.py       ← Salsa20 decrypt + struct parse
│       └── receiver.py     ← UDP socket + heartbeat loop
└── dashboard/
    ├── app.py              ← pygame event loop + layout
    └── widgets/
        ├── gauge.py        ← circular speed / RPM gauges
        ├── bar.py          ← throttle / brake / clutch / fuel bars
        ├── tire_widget.py  ← 4-corner tyre tiles + slip borders + suspension bars
        ├── g_meter.py      ← G-force circular trace
        ├── slip_angle.py   ← horizontal slip angle bar
        ├── settings_panel.py ← IP configuration overlay
        └── help_panel.py   ← in-app element reference overlay
```

---

## Setup

```bash
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
```

---

## Running

```bash
sim-dashboard
```

On first launch, the Settings panel opens automatically. Enter the PS5 IP address and save.
The IP is persisted to `~/simracing.conf` and reused on subsequent launches.

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

## Adding a new game

1. Create `simracing/telemetry/<game>/` with `parser.py` + `receiver.py`
2. Implement `TelemetryProvider` (`connect` / `disconnect` / `read`)
3. Pass the instance to `DashboardApp` via `main.py`

