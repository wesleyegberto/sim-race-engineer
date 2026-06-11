# Roadmap — Telemetry Features

## Completed

| # | Feature | Notes |
|---|---------|-------|
| 1 | G-Meter (lateral + longitudinal) | Bottom-left circle · EMA smoothed |
| 2 | Wheel slip per tyre | Orange border = wheelspin · Red = lockup |
| 3 | TCS / ASM / REV / HB status strip | 7 chips below RPM bar |
| 4 | Slip angle / oversteer indicator | Horizontal bar · green / orange / red thresholds |
| 5 | Suspension travel per corner | Side bars on tyre tiles · fill = compression |
| 6 | Fuel consumption rate per lap | Δfuel on lap change · laps remaining estimate |

---

## Pending

### 7. Voice Communication

Spoken feedback from the dashboard, replicating a real pit-wall engineer calling out information during the lap.

**Planned alerts:**
- Tyre temperature out of window ("Fronts are cold", "Rear right overheating")
- Fuel warning with laps remaining ("Four laps of fuel left")
- Oil / water temperature critical
- TCS / ASM sustained intervention ("You're losing it on exit")
- Shift cue when near redline

**Implementation notes:**
- Use `pyttsx3` (offline) or a cloud TTS API for voice synthesis
- Throttle alerts with cooldown timers to avoid repetition
- Configurable alert thresholds and voice toggle in Settings

---

### 8. Multi-Game Support

Extend the telemetry layer to support additional sim racing titles beyond GT7.

| Game | Protocol | Notes |
|------|----------|-------|
| **Assetto Corsa** | UDP shared-memory bridge | `ac_physics` struct, port 9996 |
| **Assetto Corsa Competizione** | UDP JSON (`graphics`, `physics`, `static`) | Port 9000 |
| **F1 24 / F1 25** | Codemasters UDP telemetry | 20-byte header + typed packets |
| **iRacing** | iRacing SDK shared memory | Windows only, requires `pyirsdk` |

**Implementation notes:**
- Each game gets its own `simracing/telemetry/<game>/parser.py` + `receiver.py`
- All parsers output a common `TelemetryData` object — dashboard requires no changes
- Game auto-detection or manual selection in Settings panel
- Some fields (e.g. suspension travel, angular velocity) may not be available in all titles and should fall back gracefully to zero / hidden widget

