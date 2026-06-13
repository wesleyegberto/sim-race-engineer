"""Lap telemetry recorder — buffers per-frame data and saves each lap as Parquet.

Files are written to ~/simracing_laps/<session>/lap_<N:02d>.parquet
where <session> is the ISO timestamp of race start (e.g. 2026-06-11T183000).

Schema (one row per telemetry frame, ~60 Hz):
    tick              int    — frame index within the lap (0-based)
    packet_id         int    — monotonic counter from GT7
    lap_time_ms       int    — elapsed time in current lap (ms)

    speed_kmh         float
    rpm               float
    gear              int
    throttle          float  — 0.0–1.0
    brake             float  — 0.0–1.0
    clutch            float  — 0.0–1.0
    handbrake         float  — 0.0–1.0
    turbo_boost       float  — bar above atm

    pos_x, pos_y, pos_z      float  — world position (m)
    vel_x, vel_y, vel_z      float  — velocity (m/s)

    g_lat             float  — lateral G (EMA smoothed, computed by app)
    g_lon             float  — longitudinal G (EMA smoothed, computed by app)
    slip_angle_deg    float  — yaw slip angle (deg, computed by app)

    tire_fl_temp … tire_rr_temp   float  — surface temp (°C)
    sus_fl … sus_rr               float  — suspension height (m)

    fuel_level        float  — litres
    water_temp        float  — °C
    oil_temp          float  — °C

    tcs_active        bool
    asm_active        bool
    rev_limiter       bool

    # Aggregated stats (filled at lap end, same value on every row of the lap)
    lap_number        int
    lap_finish_ms     int    — 0 while lap is live, final time after crossing line
    fuel_at_start     float
    fuel_at_end       float
    fuel_used         float  — litres consumed this lap (fuel_at_start − fuel_at_end)
    fuel_avg          float  — session average litres/lap at the moment the lap ended
    full_throttle_ticks   int
    full_brake_ticks      int
    throttle_and_brake_ticks int
    coasting_ticks        int
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from ..telemetry.models import TelemetryData

log = logging.getLogger(__name__)

_SAVE_DIR = Path.home() / "simracing_laps"

_FULL_THROTTLE = 0.98
_FULL_BRAKE    = 0.98
_COAST_THRESH  = 0.05


@dataclass
class LapData:
    """Accumulates per-frame data for one lap."""
    lap_number: int = 0
    fuel_at_start: float = 0.0
    fuel_at_end: float = -1.0
    fuel_used: float = 0.0
    fuel_avg: float = 0.0

    # Per-frame lists (one entry per telemetry packet)
    tick:             list[int]   = field(default_factory=list)
    packet_id:        list[int]   = field(default_factory=list)
    lap_time_ms:      list[int]   = field(default_factory=list)
    speed_kmh:        list[float] = field(default_factory=list)
    rpm:              list[float] = field(default_factory=list)
    gear:             list[int]   = field(default_factory=list)
    throttle:         list[float] = field(default_factory=list)
    brake:            list[float] = field(default_factory=list)
    clutch:           list[float] = field(default_factory=list)
    handbrake:        list[float] = field(default_factory=list)
    turbo_boost:      list[float] = field(default_factory=list)
    pos_x:            list[float] = field(default_factory=list)
    pos_y:            list[float] = field(default_factory=list)
    pos_z:            list[float] = field(default_factory=list)
    vel_x:            list[float] = field(default_factory=list)
    vel_y:            list[float] = field(default_factory=list)
    vel_z:            list[float] = field(default_factory=list)
    g_lat:            list[float] = field(default_factory=list)
    g_lon:            list[float] = field(default_factory=list)
    slip_angle_deg:   list[float] = field(default_factory=list)
    tire_fl_temp:     list[float] = field(default_factory=list)
    tire_fr_temp:     list[float] = field(default_factory=list)
    tire_rl_temp:     list[float] = field(default_factory=list)
    tire_rr_temp:     list[float] = field(default_factory=list)
    sus_fl:           list[float] = field(default_factory=list)
    sus_fr:           list[float] = field(default_factory=list)
    sus_rl:           list[float] = field(default_factory=list)
    sus_rr:           list[float] = field(default_factory=list)
    fuel_level:       list[float] = field(default_factory=list)
    water_temp:       list[float] = field(default_factory=list)
    oil_temp:         list[float] = field(default_factory=list)
    tcs_active:       list[bool]  = field(default_factory=list)
    asm_active:       list[bool]  = field(default_factory=list)
    rev_limiter:      list[bool]  = field(default_factory=list)

    # Aggregated counters
    full_throttle_ticks:      int = 0
    full_brake_ticks:         int = 0
    throttle_and_brake_ticks: int = 0
    coasting_ticks:           int = 0

    lap_finish_ms: int = 0

    def record(
        self,
        d: TelemetryData,
        g_lat: float,
        g_lon: float,
        slip_angle: float,
    ) -> None:
        t = d.tires
        self.tick.append(len(self.tick))
        self.packet_id.append(d.packet_id)
        self.lap_time_ms.append(d.lap_time_ms)
        self.speed_kmh.append(d.speed_kmh)
        self.rpm.append(d.rpm)
        self.gear.append(d.gear)
        self.throttle.append(d.throttle)
        self.brake.append(d.brake)
        self.clutch.append(d.clutch)
        self.handbrake.append(d.handbrake)
        self.turbo_boost.append(d.turbo_boost)
        self.pos_x.append(d.position.x)
        self.pos_y.append(d.position.y)
        self.pos_z.append(d.position.z)
        self.vel_x.append(d.velocity.x)
        self.vel_y.append(d.velocity.y)
        self.vel_z.append(d.velocity.z)
        self.g_lat.append(g_lat)
        self.g_lon.append(g_lon)
        self.slip_angle_deg.append(slip_angle)
        self.tire_fl_temp.append(t[0].surface_temp if len(t) > 0 else 0.0)
        self.tire_fr_temp.append(t[1].surface_temp if len(t) > 1 else 0.0)
        self.tire_rl_temp.append(t[2].surface_temp if len(t) > 2 else 0.0)
        self.tire_rr_temp.append(t[3].surface_temp if len(t) > 3 else 0.0)
        self.sus_fl.append(t[0].suspension_height if len(t) > 0 else 0.0)
        self.sus_fr.append(t[1].suspension_height if len(t) > 1 else 0.0)
        self.sus_rl.append(t[2].suspension_height if len(t) > 2 else 0.0)
        self.sus_rr.append(t[3].suspension_height if len(t) > 3 else 0.0)
        self.fuel_level.append(d.fuel_level)
        self.water_temp.append(d.water_temp)
        self.oil_temp.append(d.oil_temp)
        self.tcs_active.append(d.tcs_active)
        self.asm_active.append(d.asm_active)
        self.rev_limiter.append(d.rev_limiter)

        # Aggregated counters
        if d.throttle >= _FULL_THROTTLE:
            self.full_throttle_ticks += 1
        if d.brake >= _FULL_BRAKE:
            self.full_brake_ticks += 1
        if d.throttle >= _COAST_THRESH and d.brake >= _COAST_THRESH:
            self.throttle_and_brake_ticks += 1
        if d.throttle < _COAST_THRESH and d.brake < _COAST_THRESH:
            self.coasting_ticks += 1

    def num_frames(self) -> int:
        return len(self.tick)

    def to_dataframe(self):
        import pandas as pd
        n = self.num_frames()
        return pd.DataFrame({
            "tick":                   self.tick,
            "packet_id":              self.packet_id,
            "lap_number":             [self.lap_number] * n,
            "lap_time_ms":            self.lap_time_ms,
            "lap_finish_ms":          [self.lap_finish_ms] * n,
            "speed_kmh":              self.speed_kmh,
            "rpm":                    self.rpm,
            "gear":                   self.gear,
            "throttle":               self.throttle,
            "brake":                  self.brake,
            "clutch":                 self.clutch,
            "handbrake":              self.handbrake,
            "turbo_boost":            self.turbo_boost,
            "pos_x":                  self.pos_x,
            "pos_y":                  self.pos_y,
            "pos_z":                  self.pos_z,
            "vel_x":                  self.vel_x,
            "vel_y":                  self.vel_y,
            "vel_z":                  self.vel_z,
            "g_lat":                  self.g_lat,
            "g_lon":                  self.g_lon,
            "slip_angle_deg":         self.slip_angle_deg,
            "tire_fl_temp":           self.tire_fl_temp,
            "tire_fr_temp":           self.tire_fr_temp,
            "tire_rl_temp":           self.tire_rl_temp,
            "tire_rr_temp":           self.tire_rr_temp,
            "sus_fl":                 self.sus_fl,
            "sus_fr":                 self.sus_fr,
            "sus_rl":                 self.sus_rl,
            "sus_rr":                 self.sus_rr,
            "fuel_level":             self.fuel_level,
            "water_temp":             self.water_temp,
            "oil_temp":               self.oil_temp,
            "tcs_active":             self.tcs_active,
            "asm_active":             self.asm_active,
            "rev_limiter":            self.rev_limiter,
            "fuel_at_start":          [self.fuel_at_start] * n,
            "fuel_at_end":            [self.fuel_at_end] * n,
            "fuel_used":              [self.fuel_used] * n,
            "fuel_avg":               [self.fuel_avg] * n,
            "full_throttle_ticks":    [self.full_throttle_ticks] * n,
            "full_brake_ticks":       [self.full_brake_ticks] * n,
            "throttle_and_brake_ticks": [self.throttle_and_brake_ticks] * n,
            "coasting_ticks":         [self.coasting_ticks] * n,
        })


class LapRecorder:
    """Detects lap transitions and saves each completed lap to a Parquet file."""

    def __init__(self) -> None:
        self._session_dir: Path | None = None
        self._current: LapData | None = None
        self._prev_lap: int = -1

    def start_session(self) -> None:
        ts = datetime.now().strftime("%Y-%m-%dT%H%M%S")
        self._session_dir = _SAVE_DIR / ts
        self._session_dir.mkdir(parents=True, exist_ok=True)
        self._current = None
        self._prev_lap = -1
        log.info("LapRecorder session started — saving to %s", self._session_dir)

    def stop_session(self) -> None:
        if self._current and self._current.num_frames() > 0:
            self._save(self._current, label="incomplete")
        self._current = None
        self._session_dir = None
        log.info("LapRecorder session stopped")

    def on_frame(
        self,
        d: TelemetryData,
        g_lat: float,
        g_lon: float,
        slip_angle: float,
        fuel_avg: float = 0.0,
    ) -> None:
        if self._session_dir is None:
            return

        lap_num = d.current_lap

        # Lap change detected
        if lap_num != self._prev_lap:
            if self._current is not None and self._current.num_frames() > 0:
                # Finalize the lap that just ended
                self._current.fuel_at_end = d.fuel_level
                self._current.fuel_used = max(0.0, self._current.fuel_at_start - d.fuel_level)
                self._current.fuel_avg = fuel_avg
                self._current.lap_finish_ms = d.last_lap_ms
                self._save(self._current)
            # Start new lap buffer
            self._current = LapData(lap_number=lap_num, fuel_at_start=d.fuel_level)
            self._prev_lap = lap_num
            log.info("LapRecorder — lap %d started", lap_num)

        if self._current is not None:
            self._current.record(d, g_lat, g_lon, slip_angle)

    def _save(self, lap: LapData, label: str = "") -> None:
        if self._session_dir is None:
            return
        suffix = f"_{label}" if label else ""
        filename = f"lap_{lap.lap_number:02d}{suffix}.parquet"
        path = self._session_dir / filename
        try:
            df = lap.to_dataframe()
            df.to_parquet(path, index=False, engine="pyarrow", compression="snappy")
            log.info(
                "Lap %d saved → %s  (%d frames, %.1f s)",
                lap.lap_number, path, lap.num_frames(),
                lap.lap_finish_ms / 1000.0 if lap.lap_finish_ms > 0 else 0.0,
            )
        except Exception:
            log.exception("Failed to save lap %d to %s", lap.lap_number, path)
