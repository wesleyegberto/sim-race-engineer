"""Tracks tyre stint: laps on current compound and wear via effective rolling radius."""

import logging
import math
from collections import deque

from ..telemetry.models import TelemetryData

log = logging.getLogger(__name__)

_PIT_FUEL_GAIN = 0.01       # litres/frame → refuelling in progress
_PIT_HOLD_FRAMES = 30       # frames to keep in_pit_stop=True after signal

_RADIUS_SMOOTH_N = 60       # rolling-average window — larger to smooth slip transients
_MIN_VALID_RADIUS = 0.25    # metres — reject below this (wheelspin / stopped wheel)
_MAX_VALID_RADIUS = 0.40    # metres — reject above this (lockup / nearly-stopped wheel)
_MIN_SPEED_MS = 15.0        # sample only above ~54 km/h (avoids heavy-slip zones)
_MIN_WHEEL_RPM = 30.0       # ignore nearly-stationary wheels
_TYRE_WEAR_DEPTH_M = 0.003  # effective-radius reduction (m) = 100% worn

_TWO_PI = 2.0 * math.pi


class StintTracker:
    def __init__(self) -> None:
        self.stint_laps: int = 0
        self.wear_per_lap: float = 0.0
        self.current_avg_wear: float = 0.0
        self.in_pit_stop: bool = False

        self._prev_lap: int = -1
        self._prev_avg_wear: float = 0.0
        self._wear_deltas: list[float] = []
        self._prev_fuel: float = -1.0
        self._pit_hold: int = 0

        # per-tyre effective-radius tracking (index = FL/FR/RL/RR)
        self._radius_bufs: list[deque] = [deque(maxlen=_RADIUS_SMOOTH_N) for _ in range(4)]
        self._smooth_radii: list[float] = [0.0] * 4
        self._max_radii: list[float] = [0.0] * 4   # fresh-tyre reference

    # ── helpers ──────────────────────────────────────────────────────────────

    def _effective_radius(self, speed_ms: float, wheel_rpm: float) -> float:
        """Compute rolling radius from speed and wheel rotation rate."""
        if wheel_rpm < _MIN_WHEEL_RPM or speed_ms < _MIN_SPEED_MS:
            return 0.0
        rps = wheel_rpm / 60.0
        return speed_ms / (rps * _TWO_PI)

    def _update_smooth(self, i: int, r: float) -> float:
        """Append radius to rolling average; return smoothed value.

        Samples outside [_MIN_VALID_RADIUS, _MAX_VALID_RADIUS] are discarded
        to reject lockup (eff_r >> real) and wheelspin (eff_r << real) outliers.
        """
        if r < _MIN_VALID_RADIUS or r > _MAX_VALID_RADIUS:
            return self._smooth_radii[i]
        self._radius_bufs[i].append(r)
        sr = sum(self._radius_bufs[i]) / len(self._radius_bufs[i])
        self._smooth_radii[i] = sr
        return sr

    # ── main update ──────────────────────────────────────────────────────────

    def update(self, data: TelemetryData) -> bool:
        """Process a telemetry frame. Returns True when a tyre change is detected.

        Populates data.tires[i].wear (0.0 = new, 1.0 = worn) in place using
        effective rolling radius: speed_ms / (wheel_rps × 2π).  As rubber
        wears the tyre shrinks, forcing higher RPM for the same speed, which
        lowers the effective radius.  We track the maximum smoothed radius seen
        (= fresh-tyre reference) and compute wear as how far below that maximum
        the current value is.
        """
        if not data.tires or data.current_lap <= 0:
            return False

        tyre_changed = False
        speed = data.speed_ms

        for i, tire in enumerate(data.tires):
            eff_r = self._effective_radius(speed, tire.wheel_rpm)
            sr = self._update_smooth(i, eff_r)
            if sr < _MIN_VALID_RADIUS:
                continue

            prev_max = self._max_radii[i]
            if sr > prev_max:
                if prev_max > _MIN_VALID_RADIUS and sr > prev_max + _TYRE_WEAR_DEPTH_M * 0.5:
                    tyre_changed = True
                self._max_radii[i] = sr

            ref = self._max_radii[i]
            tire.wear = max(0.0, min(1.0, (ref - sr) / _TYRE_WEAR_DEPTH_M))

        avg_wear = sum(t.wear for t in data.tires) / len(data.tires)
        self.current_avg_wear = avg_wear

        # ── Per-frame pit stop detection ─────────────────────────────────────
        if self._prev_fuel >= 0:
            fuel_rising = data.fuel_level > self._prev_fuel + _PIT_FUEL_GAIN
            if fuel_rising or tyre_changed:
                self._pit_hold = _PIT_HOLD_FRAMES

        self._prev_fuel = data.fuel_level

        if self._pit_hold > 0:
            self._pit_hold -= 1
            self.in_pit_stop = True
        else:
            self.in_pit_stop = False

        # ── Lap-transition wear-rate tracking ────────────────────────────────
        if self._prev_lap < 0:
            self._prev_lap = data.current_lap
            self._prev_avg_wear = avg_wear
            return tyre_changed

        if data.current_lap == self._prev_lap:
            return tyre_changed

        log.info(
            "WEAR DBG lap=%d eff_r=%s max_r=%s wear=%s",
            data.current_lap,
            [f"{r:.5f}" for r in self._smooth_radii],
            [f"{r:.5f}" for r in self._max_radii],
            [f"{t.wear*100:.2f}%" for t in data.tires],
        )

        wear_delta = avg_wear - self._prev_avg_wear
        self._prev_lap = data.current_lap
        self._prev_avg_wear = avg_wear

        if tyre_changed or wear_delta < -0.05:
            self.stint_laps = 0
            self.wear_per_lap = 0.0
            self._wear_deltas = []
            return True

        if wear_delta > 0:
            self.stint_laps += 1
            self._wear_deltas.append(wear_delta)
            self.wear_per_lap = sum(self._wear_deltas) / len(self._wear_deltas)

        return tyre_changed

    def reset(self) -> None:
        self.stint_laps = 0
        self.wear_per_lap = 0.0
        self.current_avg_wear = 0.0
        self.in_pit_stop = False
        self._prev_lap = -1
        self._prev_avg_wear = 0.0
        self._wear_deltas = []
        self._prev_fuel = -1.0
        self._pit_hold = 0
        self._radius_bufs = [deque(maxlen=_RADIUS_SMOOTH_N) for _ in range(4)]
        self._smooth_radii = [0.0] * 4
        self._max_radii = [0.0] * 4
