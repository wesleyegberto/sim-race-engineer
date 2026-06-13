# Race Engineer — Dashboard Guide

Real-time telemetry overlay for Gran Turismo 7. Receives UDP packets from the PS5 (or PC via GT7 mod) and displays driving data at 60 Hz.

---

## Layout Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  RACE ENGINEER          device: 192.168.x.x          [?]  [⚙]   │  ← Header
├─────────────────────────────────────────────────────────────────┤
│  ████████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   │  ← RPM bar
│  [ TCS ][ ASM ][ REV ][ HB ][ LIGHT ][ OIL! ][ H₂O! ]           │  ← Status strip
│                                                                 │
│   SPEED         [GEAR]          [C][B][T]          ENGINE RPM   │
│   gauge                         pedals             gauge        │
│                                 [FUEL]                          │
│                                                                 │
│ G-METER  SLIP▬▬▬▬▬▬  |FL||FR|  ░░░░░░░  LAP / BEST / LAST       │
│                       |RL||RR|           FUEL · WATER · OIL     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Header

| Element | Description |
|---------|-------------|
| **RACE ENGINEER** | App title and icon |
| **device: x.x.x.x** | PS5 IP address currently in use. Orange if not configured. |
| **?** | Opens the in-app help overlay |
| **⚙** | Opens the Settings panel |

---

## Settings Panel

Opened via the **⚙** button in the header.

| Option | Description |
|--------|-------------|
| **Device IP** | IP address of the PS5 (or PC running GT7). Persisted to `~/simracing.conf`. |
| **Flash screen at rev limiter** | When enabled, the entire screen flashes red each time the rev limiter is hit. Disable if the effect is distracting. Default: on. |

Settings are saved on **Save** and take effect immediately.

---

## RPM Bar

A full-width strip at the top of the dashboard reflecting engine rev zone:

| Color | Zone |
|-------|------|
| Green | Below 82% of rev limit — safe cruising range |
| Orange | 82–93% — approaching power peak, shift soon |
| Red | Above 93% — at or past the power peak, shift now |

**Use:** Peripheral vision cue for shift timing without looking away from the road.

---

## Status Strip

Seven indicator chips displayed below the RPM bar. Dim when inactive, lit with color when active.

| Chip | Meaning | Color when active |
|------|---------|-------------------|
| **TCS** | Traction Control System intervened | Orange |
| **ASM** | Active Stability Management intervened | Yellow |
| **REV** | Rev limiter hit | Red |
| **HB** | Handbrake applied | Yellow |
| **LIGHT** | Headlights on | Light blue |
| **OIL!** | Oil temperature above 130 °C | Red |
| **H₂O!** | Water temperature above 105 °C | Red |

**TCS/ASM use:** Frequent flashing of TCS or ASM indicates the driver is consistently exceeding the grip limit. In time-attack, the goal is to keep these off entirely. In race conditions, occasional TCS activation is acceptable but sustained intervention means the entry or exit speed is too aggressive.

**OIL!/H₂O! use:** Sustained red on either fluid chip risks engine damage. Back off, allow temperatures to drop before pushing again.

---

## Speed Gauge (left)

Analog arc gauge showing current speed in km/h.

- Scale maximum adapts to the car's calculated top speed when available, otherwise defaults to 320 km/h.
- Arc turns **orange** above 85% of max speed, **red** above 95%.

**Use:** Cross-reference with braking points. Knowing your entry speed for each corner is the foundation of consistent lap times.

---

## Engine RPM Gauge (right)

Analog arc gauge showing engine RPM.

- Same color zones as the RPM bar (green / orange / red).
- Scale maximum is the car's rev limit.

**Use:** Identify the optimal shift point for each gear. Shifting too early loses torque; shifting too late causes the rev limiter to cut power.

---

## Gear Display (center)

Large number showing the current gear engaged.

| Value | Meaning |
|-------|---------|
| **1–8** | Numbered gear |
| **N** | Neutral |
| **R** | Reverse |

Below the gear number, a smaller **> N** in orange appears when the game's suggested gear differs from the current gear. This is the AI's upshift/downshift recommendation based on speed and throttle position. The indicator is hidden when the game sends no suggestion.

**Use:** The suggested gear is useful when learning a new track or car. In competition it is often ignored in favour of driver judgement.

---

## Pedal Bars (center)

Three vertical bars showing input percentage (0–100%):

| Bar | Input | Color |
|-----|-------|-------|
| **C** | Clutch | Blue |
| **B** | Brake | Red |
| **T** | Throttle | Green |

**Use:** The most direct feedback tool for driving style analysis.
- **Brake + Throttle overlap** (both bars simultaneously lit): trail braking — advanced technique to maintain rear weight while turning in.
- **Abrupt brake release** (bar drops instantly): risk of understeer on entry. A gradual release is smoother.
- **Throttle application point**: throttle should begin as the steering wheel returns to centre on exit. Early application causes wheelspin; late application wastes time.

---

## Fuel Bar

A narrow vertical bar to the left of the pedal bars showing the percentage of fuel remaining in the tank (blue fill).

**Use:** Quick visual check of fuel state during a race. For precise consumption data, see the Info Panel.

---

## G-Meter (bottom left)

A circular dial with a moving dot representing the combined lateral and longitudinal G-force.

| Axis | Direction | Meaning |
|------|-----------|---------|
| Horizontal | Left / Right | Lateral G (cornering load) |
| Vertical | Up | Longitudinal G braking |
| Vertical | Down | Longitudinal G acceleration |

**Dot color:**

| Color | G magnitude |
|-------|-------------|
| Green | Below 0.8 G — light load |
| Orange | 0.8–1.5 G — moderate load |
| Red | Above 1.5 G — high load |

**Use:** The G-meter is the definitive picture of how the car's weight is being managed.

- A **smooth arc** through the corner — the dot moves diagonally from the top (braking) to the side (peak lateral) to the bottom (acceleration) — indicates a well-executed corner using the traction circle efficiently.
- A **dot that jumps** or stays fixed means inputs are not smooth, wasting available grip.
- **Peak lateral G** is a proxy for corner speed. If the dot barely reaches the orange zone through a fast corner, there is unused grip.

---

## Slip Angle Bar (bottom, between G-meter and tires)

A horizontal bar showing the angle between the car's heading direction and its actual velocity vector.

| Region | Value | Meaning |
|--------|-------|---------|
| Center | ≈ 0° | Car going where it is pointed |
| Right fill | Positive | Rear sliding to the right (oversteer right) |
| Left fill | Negative | Rear sliding to the left (oversteer left) |

**Color thresholds:**

| Color | Angle | Interpretation |
|-------|-------|----------------|
| Green | < 5° | Neutral — minimal rotation |
| Orange | 5–12° | Controlled oversteer or yaw build-up |
| Red | ≥ 12° | High oversteer — risk of spin |

**Use:** The slip angle bar distinguishes between *rotation* (desirable, controlled rear movement that tightens the line) and *oversteer* (uncontrolled, leading to a spin). A brief orange flash on corner entry when rotating the car is normal in rear-wheel-drive vehicles. A sustained red reading means the driver has exceeded the car's limit.

> The value is derived from `velocity` and the car's quaternion (`rotation.x/y/z` are the imaginary components qi, qj, qk) in the GT7 packet. The car's forward vector is reconstructed from the unit quaternion before computing the angle. The result is smoothed with an EMA filter and decays to zero below 5 m/s to avoid noise at low speed.

---

## Tire Display (bottom center)

A 2×2 grid of tiles representing the four tires: **FL** (front-left), **FR** (front-right), **RL** (rear-left), **RR** (rear-right).

### Tile fill color — Surface temperature

| Color | Temperature | Interpretation |
|-------|------------|----------------|
| Blue | < 60 °C | Cold — grip is reduced, tires need warming |
| Green → transitioning | 60–100 °C | Warming up |
| Green | 60–130 °C | Optimal operating window |
| Green → Red | 130–180 °C | Overheating — grip degrading |
| Red | > 180 °C | Critically hot |

**Use:** Tire temperature balance reveals setup and driving problems.
- **Front tires hotter than rear**: understeer — car is pushing the fronts past their limit.
- **Rear tires hotter than front**: oversteer tendency — rear is working harder.
- **Outer edge hotter than inner** (not shown here, but derivable from inner/outer temps): too little camber.
- **All tires cold after several laps**: tires never reached the window — wrong compound for conditions.

### Tile border — Wheel slip

| Border | Meaning |
|--------|---------|
| **Orange** (thick) | Wheelspin — wheel rotating faster than ground speed predicts. Power is not being transferred. |
| **Red** (thick) | Lockup — wheel rotating slower than ground speed predicts. Brake is locking the wheel. |
| Dim grey (thin) | Normal rolling |

**Wheelspin use:** Sustained orange on rear tires during acceleration means the driver is applying throttle before sufficient weight has transferred to the rear, or the throttle application is too aggressive for the grip available.

**Lockup use:** Red on front tires under braking is lockup — the driver has exceeded the braking threshold. ABS (if off) would need earlier or lighter brake application.

### Side bar — Suspension travel

Narrow vertical bar on the outer edge of each tile (left side for FL/RL, right side for FR/RR).

- **Fill from the bottom**: more filled = more compressed (more load on that corner).
- **Empty**: suspension extended (wheel lightly loaded or in the air).

| Color | Load level |
|-------|-----------|
| Blue | Light / extended — under 30% of travel |
| Green | Nominal — 30–65% |
| Orange | Heavy load — 65–85% |
| Red | Near limit — above 85% |

**Use:** The four bars together form an instant picture of weight distribution.
- **Both front bars higher than rear** (braking): weight transfer to front — normal under braking.
- **Left bars higher than right bars** (right-hand corner): lateral load transfer to the left — normal.
- **One bar dramatically higher than its axle partner**: could indicate a bump, kerb strike, or suspension setup imbalance.
- **Rear bars consistently at orange/red, fronts near blue**: car is heavily rear-biased — rear springs may be too stiff or rear ride height too low.

---

## Info Panel (right side)

Text readouts updated every frame.

| Label | Value | Notes |
|-------|-------|-------|
| **LAP** | `current / total` | Current lap number over total laps in race |
| **LAP TIME** | `M:SS.mmm` | Current lap time (only valid while in race) |
| **BEST** | `M:SS.mmm` | Best lap time this session (green) |
| **LAST** | `M:SS.mmm` | Last completed lap time |
| **WATER** | `°C` | Coolant temperature · orange if above 105 °C |
| **OIL** | `°C` | Oil temperature · orange if above 130 °C |
| **FUEL** | `L` | Current fuel level in litres |
| **FUEL/LAP** | `L` | Average fuel consumed per lap (appears after 1st lap change) |
| **LAPS LEFT** | number | Estimated laps remaining at current consumption rate · orange if below 3 |
| **BOOST** | `bar` | Turbo boost pressure above atmospheric · blue if positive, dim if zero |

**FUEL/LAP and LAPS LEFT use:** Essential for endurance pit-stop strategy. If LAPS LEFT drops below the number of laps to the next scheduled stop, either save fuel (lift-and-coast, short-shift, reduce throttle on straights) or plan an early stop.

**WATER / OIL use:** Temperatures rise under sustained high-RPM use and fall when engine load is reduced. If either approaches the warning threshold on a long straight, check that the car's cooling is adequate for the track and ambient conditions in the game.

---

## Out-of-Race State

When the car is not in an active race (garage, menu, loading, or after finish), the dashboard freezes: gauges, G-meter, slip angle, tire temperatures, and all derived metrics are cleared and not updated. Only the header with the connection status remains visible.

All values reset when a new race session begins.

When the car is not in an active race, additional flags may appear in the info panel:

| Label | Meaning |
|-------|---------|
| **PAUSE** | Game is paused |
| **LOAD** | Game is loading |
| **MENU** | Car is in the garage / menu, not on track |

---

## Interpreting the Dashboard as a Whole

The dashboard is designed so that the most time-critical information is readable with peripheral vision while focusing on a screen or TV:

1. **RPM bar** — shift cue without moving your eyes.
2. **Status strip** — TCS/ASM flicker visible at the top of the peripheral field.
3. **Gear number** — large, centre screen.
4. **Pedals** — muscle-memory verification.

The analytical information (G-meter, slip angle, suspension, tire temps) is meant to be reviewed **between laps or during replays**, not mid-corner. Use it to diagnose why a lap was slower than expected:

- Tires not in window → warming strategy or compound change.
- G-meter shows an abrupt transition → smoothness issue at that corner.
- Slip angle sustained in orange/red at a specific corner → exceeding rear grip limit, adjust braking or rotation.
- Suspension bar on one corner consistently red → kerb abuse or setup imbalance.

---

## Setup and Connection

1. Enable the **GT7 telemetry output** in the game: `Settings → GT7 SIM Racing Telemetry → Enabled`.
2. Note the IP address of the PS5.
3. Launch Race Engineer and enter the IP via **⚙ Settings** (or set `SIMRACING_DEVICE_IP` env var, or edit `~/simracing.conf`).
4. Start a race or time trial — data starts flowing immediately.

The app listens on UDP port **33740** by default.

---

## Lap Recording

Race Engineer automatically records every lap to disk — no manual action required.

### When laps are saved

| Event | File written |
|-------|-------------|
| **Lap transition** (`current_lap` increments) | `lap_NN.parquet` for the lap that just ended |
| **Session end** (app closed or race stopped) | `lap_NN_incomplete.parquet` for the current unfinished lap |

### Where files are saved

```
~/simracing_laps/
└── <YYYY-MM-DDTHHMMSS>/        ← session folder, created when recording starts
    ├── lap_01.parquet
    ├── lap_02.parquet
    └── lap_03_incomplete.parquet
```

The session directory name is the ISO timestamp of when the recording session started (e.g. `2026-06-13T143022`).

### File format

Files use **Apache Parquet** with **Snappy** compression. Each file contains one row per telemetry frame (~60 Hz). Columns:

| Column(s) | Description |
|-----------|-------------|
| `tick`, `packet_id`, `lap_time_ms` | Frame index, GT7 packet counter, elapsed lap time (ms) |
| `speed_kmh`, `rpm`, `gear` | Speed, engine revs, current gear |
| `throttle`, `brake`, `clutch`, `handbrake` | Input channels, 0.0–1.0 |
| `turbo_boost` | Turbo pressure above atmospheric (bar) |
| `pos_x/y/z`, `vel_x/y/z` | World position and velocity (metres, m/s) |
| `g_lat`, `g_lon` | Lateral and longitudinal G-force (EMA-smoothed, computed by app) |
| `slip_angle_deg` | Yaw slip angle (computed by app) |
| `tire_fl/fr/rl/rr_temp` | Tyre surface temperatures (°C) |
| `sus_fl/fr/rl/rr` | Suspension travel (metres) |
| `fuel_level`, `water_temp`, `oil_temp` | Fluids |
| `tcs_active`, `asm_active`, `rev_limiter` | Boolean state flags |

**Lap-summary columns** (same value on every row, filled when the lap ends):

| Column | Description |
|--------|-------------|
| `lap_number` | Lap counter from GT7 |
| `lap_finish_ms` | Official lap time from GT7 (ms); `0` while lap is live |
| `fuel_at_start` | Fuel level at the start of the lap (litres) |
| `fuel_at_end` | Fuel level at the end of the lap (litres) |
| `fuel_used` | Litres consumed this lap (`fuel_at_start − fuel_at_end`) |
| `fuel_avg` | Session-average litres/lap at the moment this lap ended |
| `full_throttle_ticks` | Frames with throttle ≥ 98% |
| `full_brake_ticks` | Frames with brake ≥ 98% |
| `throttle_and_brake_ticks` | Frames with both inputs ≥ 5% (trail braking) |
| `coasting_ticks` | Frames with both inputs below 5% |

### Reading lap files

```python
import pandas as pd

df = pd.read_parquet("~/simracing_laps/2026-06-13T143022/lap_01.parquet")
print(df.columns.tolist())
print(f"Lap time: {df['lap_finish_ms'].iloc[-1] / 1000:.3f}s")
print(f"Fuel used: {df['fuel_used'].iloc[-1]:.2f} L")
```

