"""Tracks tyre stint: laps on current compound and average wear rate per lap."""

from ..telemetry.models import TelemetryData

_PIT_WEAR_LAP_DROP = 0.15    # wear drop between laps → confirms new tyres
_PIT_FUEL_GAIN = 0.01        # litres gained per frame → refueling
_PIT_WEAR_FRAME_DROP = 0.001 # wear drop per frame → tyre swap in progress
_PIT_HOLD_FRAMES = 30        # frames to keep in_pit_stop=True after signal stops


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
        self._prev_frame_wear: float = -1.0
        self._pit_hold: int = 0

    def update(self, data: TelemetryData) -> bool:
        """Process a telemetry frame. Returns True when a tyre change is detected."""
        if not data.tires or data.current_lap <= 0:
            return False

        avg_wear = sum(t.wear for t in data.tires) / len(data.tires)
        self.current_avg_wear = avg_wear

        # ── Per-frame pit stop detection ──────────────────────────────────────
        if self._prev_fuel >= 0:
            fuel_rising = data.fuel_level > self._prev_fuel + _PIT_FUEL_GAIN
            wear_dropping = (
                self._prev_frame_wear >= 0
                and avg_wear < self._prev_frame_wear - _PIT_WEAR_FRAME_DROP
            )
            if fuel_rising or wear_dropping:
                self._pit_hold = _PIT_HOLD_FRAMES

        self._prev_fuel = data.fuel_level
        self._prev_frame_wear = avg_wear

        if self._pit_hold > 0:
            self._pit_hold -= 1
            self.in_pit_stop = True
        else:
            self.in_pit_stop = False

        # ── Lap-transition tyre change detection ──────────────────────────────
        if self._prev_lap < 0:
            self._prev_lap = data.current_lap
            self._prev_avg_wear = avg_wear
            return False

        if data.current_lap == self._prev_lap:
            return False

        wear_delta = avg_wear - self._prev_avg_wear
        self._prev_lap = data.current_lap
        self._prev_avg_wear = avg_wear

        if wear_delta < -_PIT_WEAR_LAP_DROP:
            self.stint_laps = 0
            self.wear_per_lap = 0.0
            self._wear_deltas = []
            return True

        if wear_delta > 0:
            self.stint_laps += 1
            self._wear_deltas.append(wear_delta)
            self.wear_per_lap = sum(self._wear_deltas) / len(self._wear_deltas)

        return False

    def reset(self) -> None:
        self.stint_laps = 0
        self.wear_per_lap = 0.0
        self.current_avg_wear = 0.0
        self.in_pit_stop = False
        self._prev_lap = -1
        self._prev_avg_wear = 0.0
        self._wear_deltas = []
        self._prev_fuel = -1.0
        self._prev_frame_wear = -1.0
        self._pit_hold = 0
