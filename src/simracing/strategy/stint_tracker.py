"""Tracks tyre stint: laps on current compound and wear via dynamic radius."""

from collections import deque

from ..telemetry.models import TelemetryData

_PIT_FUEL_GAIN = 0.01       # litres/frame → refuelling in progress
_PIT_HOLD_FRAMES = 30       # frames to keep in_pit_stop=True after signal

_RADIUS_SMOOTH_N = 20       # rolling-average window (frames) to filter deformation
_MIN_VALID_RADIUS = 0.25    # metres — sanity gate; below this → ignore reading
_TYRE_WEAR_DEPTH_M = 0.003  # radius reduction (m) that maps to 100% wear


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

        # per-tyre radius tracking (index = FL/FR/RL/RR)
        self._radius_bufs: list[deque] = [deque(maxlen=_RADIUS_SMOOTH_N) for _ in range(4)]
        self._smooth_radii: list[float] = [0.0] * 4
        # Max radius seen in this session — new tyre naturally raises this
        self._max_radii: list[float] = [0.0] * 4

    # ── helpers ──────────────────────────────────────────────────────────────

    def _update_radius(self, i: int, raw: float) -> float:
        """Append raw radius to rolling average; return smoothed value."""
        if raw < _MIN_VALID_RADIUS:
            return self._smooth_radii[i]
        self._radius_bufs[i].append(raw)
        sr = sum(self._radius_bufs[i]) / len(self._radius_bufs[i])
        self._smooth_radii[i] = sr
        return sr

    # ── main update ──────────────────────────────────────────────────────────

    def update(self, data: TelemetryData) -> bool:
        """Process a telemetry frame. Returns True when a tyre change is detected.

        Populates data.tires[i].wear (0.0 = new, 1.0 = worn) in place.

        Strategy: use the maximum smoothed radius ever seen as the fresh-tyre
        reference.  When new tyres are fitted the radius increases, which
        naturally raises the max reference and resets wear to ~0.  Transient
        radius drops (hard braking / cornering deformation) shrink the
        current value but do not reset the max, so they appear only as
        momentary wear spikes that smooth out on the next straight.
        """
        if not data.tires or data.current_lap <= 0:
            return False

        tyre_changed = False

        for i, tire in enumerate(data.tires):
            sr = self._update_radius(i, tire.radius)
            if sr < _MIN_VALID_RADIUS:
                continue

            prev_max = self._max_radii[i]

            if sr > prev_max:
                if prev_max > _MIN_VALID_RADIUS and sr > prev_max + _TYRE_WEAR_DEPTH_M * 0.5:
                    # Jumped by ≥ half the wear-depth: very likely a fresh tyre
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
