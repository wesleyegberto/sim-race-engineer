# Gran Turismo 7 — Telemetry Integration

## Overview

Gran Turismo 7 (PS5) streams real-time telemetry data over **UDP** to the local network.
The stream is encrypted with **Salsa20** and requires periodic heartbeat packets
to keep the transmission alive.

### In-game prerequisite

Enable data output at:
**Options → Machine Settings → Send Vehicle Data → On**

---

## Network Protocol

| Parameter | Value |
|---|---|
| Protocol | UDP/IPv4 |
| Receive port (PS5 → client) | `33740` |
| Heartbeat port (client → PS5) | `33739` |
| Packet size | `296 bytes` |
| Transmission rate | ~60 Hz |

### Heartbeat

The PS5 only transmits data while it receives a `b"A"` packet (1 byte, ASCII) on port `33739`
every **100 ms**. Without heartbeats, the stream stops after a few seconds.

```
Client  ──── b"A" ────▶  PS5:33739   (every 100 ms)
Client  ◀─── packet ───  PS5:33740   (~60 Hz)
```

---

## Encryption

Each packet is encrypted with **Salsa20** (stream cipher).

| Parameter | Value |
|---|---|
| Algorithm | Salsa20 |
| Key | `Simulator Interface Packet GT7 ver 0.0` (38 bytes, ASCII) |
| Nonce | bytes `[0x40–0x47]` of the **encrypted** packet, reversed |

### Decryption process

```python
nonce = raw_packet[0x40:0x48][::-1]          # 8 bytes, reversed
cipher = Salsa20.new(key=KEY, nonce=nonce)
decrypted = cipher.decrypt(raw_packet)
```

### Magic number validation

After decryption, the first 4 bytes must be `0x47375330` (`G75\x30` in little-endian).
Discard the packet if they do not match.

---

## Packet Structure (296 bytes, little-endian)

All offsets are in bytes after decryption.
Types: `f32` = 32-bit float, `u8/u16/u32` = unsigned int, `i16/i32/i64` = signed int.

### Identification

| Offset | Type | Field | Description |
|---|---|---|---|
| `0x00` | `u32` | `magic` | Magic number `0x47375330` — validates the packet |
| `0x68` | `u32` | `packet_id` | Monotonic packet counter (increments each frame) |

---

### Position and Motion

| Offset | Type | Field | Unit | Description |
|---|---|---|---|---|
| `0x04` | `f32×3` | `position` | metres | Car position X, Y, Z in the 3D world |
| `0x10` | `f32×3` | `velocity` | m/s | Velocity vector X, Y, Z |
| `0x1C` | `f32×3` | `rotation` | rad | Car orientation: pitch (X), yaw (Y), roll (Z) |
| `0x28` | `f32×3` | `angular_velocity` | rad/s | Angular velocity on each axis |
| `0x34` | `f32` | `body_height` | metres | Centre-of-mass height above the road |
| `0x44` | `f32` | `speed` | m/s | Scalar car speed (negative when reversing — use `abs()` for display) |

> **Note:** GT7's Y axis is vertical (up). `rotation.y` is the yaw angle (heading) in radians.

---

### Engine and Powertrain

| Offset | Type | Field | Unit | Description |
|---|---|---|---|---|
| `0x38` | `f32` | `engine_rpm` | RPM | Current engine revs |
| `0x80` | `u16` | `min_alert_rpm` | RPM | Minimum alert RPM (near idle) |
| `0x82` | `u16` | `max_alert_rpm` | RPM | Maximum alert RPM (redline for the current car) |
| `0x84` | `u16` | `calc_max_speed` | km/h | Calculated top speed for the current car (0 = unknown) |
| `0x48` | `f32` | `turbo_boost` | bar | Turbo pressure **above** 1 atm (e.g. `0.5` = 1.5 bar absolute) |
| `0xD0` | `f32` | `clutch` | 0–1 | Clutch position (0 = fully pressed, 1 = released) |
| `0xD4` | `f32` | `clutch_engagement` | 0–1 | Clutch bite point |
| `0xD8` | `f32` | `rpm_after_clutch` | RPM | Transmission-side RPM (after clutch) |

---

### Gearbox and Pedals

| Offset | Type | Field | Description |
|---|---|---|---|
| `0x88` | `u8` | `gear_byte` | Bits `[3:0]` = current gear · Bits `[7:4]` = suggested gear |
| `0x89` | `u8` | `throttle` | Throttle position, 0–255 (divide by 255 for 0.0–1.0) |
| `0x8A` | `u8` | `brake` | Brake position, 0–255 |
| `0x108` | `f32` | `handbrake` | Handbrake, 0.0–1.0 |

#### Gear decoding

```
current_gear   = gear_byte & 0x0F    # 0=neutral, 1–8=gears, 15=reverse
suggested_gear = (gear_byte >> 4) & 0x0F   # 0 = no suggestion
```

#### Gear ratios

| Offset | Field | Description |
|---|---|---|
| `0x10C` | `gear_ratio[0]` | Reverse ratio |
| `0x110` | `gear_ratio[1]` | 1st gear ratio |
| `0x114–0x128` | `gear_ratio[2–6]` | Remaining gear ratios (up to 8th) |

---

### Fluids and Temperatures

| Offset | Type | Field | Unit | Notes |
|---|---|---|---|---|
| `0x3C` | `f32` | `fuel_level` | litres | Current fuel in tank |
| `0x40` | `f32` | `fuel_capacity` | litres | Total tank capacity |
| `0x4C` | `f32` | `oil_pressure` | bar | Oil pressure (multiply × 100 for kPa) |
| `0x50` | `f32` | `water_temp` | °C | Coolant temperature |
| `0x54` | `f32` | `oil_temp` | °C | Engine oil temperature |

---

### Tires — Surface Temperature

All 4 tires follow the order **FL · FR · RL · RR** across all fields.

| Offset | Field | Unit |
|---|---|---|
| `0x58` | `tire_fl_surface_temp` | °C |
| `0x5C` | `tire_fr_surface_temp` | °C |
| `0x60` | `tire_rl_surface_temp` | °C |
| `0x64` | `tire_rr_surface_temp` | °C |

### Tires — Internal Temperature (3 zones)

Each tire has **inner · middle · outer** zones (inner edge → outer edge).

| Offset | Tire | Fields |
|---|---|---|
| `0xDC–0xE4` | FL | inner, middle, outer (3 × f32) |
| `0xE8–0xF0` | FR | inner, middle, outer |
| `0xF4–0xFC` | RL | inner, middle, outer |
| `0x100–0x107` | RR | inner, middle, outer |

### Tires — Dynamics

| Offset | Field | Unit | Description |
|---|---|---|---|
| `0x9C` | `tire_fl_rps` | rad/s | FL wheel angular velocity (negative = reversing) |
| `0xA0` | `tire_fr_rps` | rad/s | FR wheel angular velocity |
| `0xA4` | `tire_rl_rps` | rad/s | RL wheel angular velocity |
| `0xA8` | `tire_rr_rps` | rad/s | RR wheel angular velocity |
| `0xAC` | `tire_fl_radius` | metres | Effective FL tyre radius |
| `0xB0` | `tire_fr_radius` | metres | Effective FR tyre radius |
| `0xB4` | `tire_rl_radius` | metres | Effective RL tyre radius |
| `0xB8` | `tire_rr_radius` | metres | Effective RR tyre radius |
| `0xBC` | `tire_fl_suspension` | metres | FL suspension travel (compression height) |
| `0xC0` | `tire_fr_suspension` | metres | FR suspension travel |
| `0xC4` | `tire_rl_suspension` | metres | RL suspension travel |
| `0xC8` | `tire_rr_suspension` | metres | RR suspension travel |

> **Wheel RPM conversion:** O campo `tire_*_rps` é em **rad/s** (não rot/s).
> Conversão: `wheel_rpm = abs(rps) / (2π) × 60`
> Para slip ratio: `exp_rps = speed_ms / (2π × radius)` ; `actual_rps = wheel_rpm / 60`

---

### Race and Lap

| Offset | Type | Field | Unit | Description |
|---|---|---|---|---|
| `0x6C` | `u16` | `lap_count` | — | Current lap number |
| `0x6E` | `u16` | `laps_in_race` | — | Total laps in race (0 = unlimited / not set) |
| `0x70` | `i32` | `best_lap_ms` | ms | Best lap time (−1 = no lap recorded) |
| `0x74` | `i32` | `last_lap_ms` | ms | Last completed lap (−1 = no lap) |
| `0x78` | `i32` | `time_of_day_ms` | ms | In-game time of day (since midnight) |
| `0x7C` | `i16` | `race_start_pos` | — | Grid starting position |
| `0x7E` | `i16` | `pre_race_count` | — | Pre-race countdown value |

> **Note:** The current lap time (`lap_time_ms`) is not included in the UDP packet.
> It must be calculated locally using `packet_id` and the timestamp of the lap start.

---

### Road Plane

| Offset | Type | Field | Description |
|---|---|---|---|
| `0x8C` | `f32×3` | `road_plane` | Normal vector of the road surface beneath the car |
| `0x98` | `f32` | `road_distance` | Distance from centre of mass to the road plane |

---

### Car Identification

| Offset | Type | Field | Description |
|---|---|---|---|
| `0x124` | `i64` | `car_code` | Numeric identifier of the car in the GT7 catalogue |

---

## State Flags (`0x86`, u16)

Each bit represents a boolean game state.

| Bit | Mask | Name | Description |
|---|---|---|---|
| 0 | `0x0001` | `in_race` | Race / practice session active |
| 1 | `0x0002` | `paused` | Game is paused |
| 2 | `0x0004` | `loading` | Loading screen active |
| 3 | `0x0008` | `in_gear` | Car is in gear (not neutral) |
| 4 | `0x0010` | `has_turbo` | Car has a turbocharger |
| 5 | `0x0020` | `rev_limiter` | Rev limiter is active |
| 6 | `0x0040` | `handbrake_active` | Handbrake applied |
| 7 | `0x0080` | `lights_on` | Headlights on |
| 8 | `0x0100` | `low_beam` | Low-beam headlights |
| 9 | `0x0200` | `high_beam` | High-beam headlights |
| 10 | `0x0400` | `asm_active` | ASM (Active Stability Management) intervening |
| 11 | `0x0800` | `tcs_active` | TCS (Traction Control System) intervening |

---

## GT7 UDP Known Limitations

Some fields in the GT7 UDP packet are fixed and do not reflect real in-game values:

| Field | Observed value | Note |
|-------|---------------|------|
| `water_temp` | 85 °C | Always constant — not the actual engine water temperature |
| `oil_temp` | 110 °C | Always constant — not the actual oil temperature |
| `tire_radius` | fixed per compound | Geometric property of the tyre model, does not decrease with wear |

## Fields Not Available

The following data is **not** transmitted by the GT7 UDP protocol:

- Real-time race position (only grid/start position via `race_start_pos`)
- Current lap time in progress (must be calculated locally)
- Brake temperatures
- Tyre wear level
- Data from other cars in the race
- DRS / ERS / battery state

---

## Implementation Reference

| File | Responsibility |
|---|---|
| `src/simracing/telemetry/gt7/parser.py` | Salsa20 decryption + 296-byte packet parsing |
| `src/simracing/telemetry/gt7/receiver.py` | UDP socket + heartbeat loop |
| `src/simracing/telemetry/models.py` | `TelemetryData` — game-agnostic data model |
| `src/simracing/telemetry/provider.py` | `TelemetryProvider` ABC |
