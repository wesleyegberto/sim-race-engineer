"""Tracks tyre stint: laps on current compound and average wear rate per lap."""

from ..telemetry.models import TelemetryData

_PIT_WEAR_DROP = 0.15  # fraction drop that signals a tyre change


class StintTracker:
    def __init__(self) -> None:
        self.stint_laps: int = 0
        self.wear_per_lap: float = 0.0
        self.current_avg_wear: float = 0.0
        self._prev_lap: int = -1
        self._prev_avg_wear: float = 0.0
        self._wear_deltas: list[float] = []

    def update(self, data: TelemetryData) -> bool:
        """Process a telemetry frame. Returns True when a tyre change is detected."""
        if not data.tires or data.current_lap <= 0:
            return False

        avg_wear = sum(t.wear for t in data.tires) / len(data.tires)
        self.current_avg_wear = avg_wear

        if self._prev_lap < 0:
            self._prev_lap = data.current_lap
            self._prev_avg_wear = avg_wear
            return False

        if data.current_lap == self._prev_lap:
            return False

        wear_delta = avg_wear - self._prev_avg_wear
        self._prev_lap = data.current_lap
        self._prev_avg_wear = avg_wear

        if wear_delta < -_PIT_WEAR_DROP:
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
        self._prev_lap = -1
        self._prev_avg_wear = 0.0
        self._wear_deltas = []
