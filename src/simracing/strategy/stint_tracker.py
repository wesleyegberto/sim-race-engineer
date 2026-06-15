"""Tracks tyre stint: laps on current compound and wear via dynamic radius."""

from collections import deque

from ..telemetry.models import TelemetryData

_PIT_FUEL_GAIN = 0.01           # litres/frame → refuelling in progress
_PIT_HOLD_FRAMES = 30           # frames to keep in_pit_stop=True after signal

_RADIUS_SMOOTH_N = 20           # rolling-average window (frames) to filter deformation
_MIN_VALID_RADIUS = 0.25        # metres — sanity gate; below this → ignore reading
_TYRE_WEAR_DEPTH_M = 0.003      # radius reduction (m) that maps to 100% wear
_TYRE_CHANGE_THRESHOLD_M = 0.0008  # smoothed radius gain (m) → new tyre detected


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
        self._initial_radii: list[float] = [0.0] * 4

    # ── helpers ──────────────────────────────────────────────────────────────

    def _update_radius(self, i: int, raw: float) -> float:
        """Update rolling average; return smoothed radius or 0 if invalid."""
        if raw < _MIN_VALID_RADIUS:
            return self._smooth_radii[i]
        self._radius_bufs[i].append(raw)
        sr = sum(self._radius_bufs[i]) / len(self._radius_bufs[i])
        self._smooth_radii[i] = sr
        return sr

    def _reset_tyre(self, i: int, initial_radius: float) -> None:
        self._radius_bufs[i].clear()
        self._initial_radii[i] = initial_radius
        self._smooth_radii[i] = 0.0

    # ── main update ──────────────────────────────────────────────────────────

    def update(self, data: TelemetryData) -> bool:
        """Process a telemetry frame. Returns True when a tyre change is detected.

        Populates data.tires[i].wear (0.0 = new, 1.0 = worn) in place from the
        dynamic radius reported by GT7 (offsets 0xB4–0xC0).
        """
        if not data.tires or data.current_lap <= 0:
            return False

        any_tyre_changed = False

        for i, tire in enumerate(data.tires):
            sr = self._update_radius(i, tire.radius)
            if sr < _MIN_VALID_RADIUS:
                continue

            ref = self._initial_radii[i]

            if ref < _MIN_VALID_RADIUS:
                # First valid reading → establish fresh-tyre reference
                self._initial_radii[i] = sr
                ref = sr

            elif sr > ref + _TYRE_CHANGE_THRESHOLD_M:
                # Radius increased (new tyre fitted) → reset reference
                self._initial_radii[i] = sr
                ref = sr
                any_tyre_changed = True

            # Calculate and publish wear for this tyre
            tire.wear = max(0.0, min(1.0, (ref - sr) / _TYRE_WEAR_DEPTH_M))

        avg_wear = sum(t.wear for t in data.tires) / len(data.tires)
        self.current_avg_wear = avg_wear

        # ── Per-frame pit stop detection ─────────────────────────────────────
        if self._prev_fuel >= 0:
            fuel_rising = data.fuel_level > self._prev_fuel + _PIT_FUEL_GAIN
            if fuel_rising or any_tyre_changed:
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
            return any_tyre_changed

        if data.current_lap == self._prev_lap:
            return any_tyre_changed

        wear_delta = avg_wear - self._prev_avg_wear
        self._prev_lap = data.current_lap
        self._prev_avg_wear = avg_wear

        if any_tyre_changed or wear_delta < -0.05:
            self.stint_laps = 0
            self.wear_per_lap = 0.0
            self._wear_deltas = []
            return True

        if wear_delta > 0:
            self.stint_laps += 1
            self._wear_deltas.append(wear_delta)
            self.wear_per_lap = sum(self._wear_deltas) / len(self._wear_deltas)

        return any_tyre_changed

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
        self._initial_radii = [0.0] * 4
