"""User-defined pit stop strategy tracker."""

from dataclasses import dataclass, field


@dataclass
class PlannedStop:
    stop_number: int
    planned_lap: int
    done: bool = False


@dataclass
class PlannedStrategy:
    stops: list[PlannedStop] = field(default_factory=list)

    def next_stop(self, current_lap: int) -> PlannedStop | None:
        for stop in sorted(self.stops, key=lambda s: s.planned_lap):
            if not stop.done and stop.planned_lap >= current_lap - 1:
                return stop
        return None

    def mark_stop_done(self, stop_number: int) -> None:
        for stop in self.stops:
            if stop.stop_number == stop_number:
                stop.done = True
                return

    def reset_done_flags(self) -> None:
        for stop in self.stops:
            stop.done = False


@dataclass
class PlannedStrategyStatus:
    next_stop: PlannedStop
    laps_to_planned_stop: int
    tyres_can_reach_planned_stop: bool
    tyre_life_remaining_laps: float
    strategy_alert: str | None  # "APPROACHING" | "NOW" | "MISSED" | "TYRE_WARNING" | None


class PlannedStrategyMonitor:
    def __init__(self) -> None:
        self._strategy: PlannedStrategy | None = None

    def set_strategy(self, strategy: PlannedStrategy | None) -> None:
        self._strategy = strategy

    def on_pit_detected(self, current_lap: int) -> None:
        if self._strategy is None:
            return
        stop = self._strategy.next_stop(current_lap)
        if stop:
            self._strategy.mark_stop_done(stop.stop_number)

    def reschedule_missed_stop(self, stop_number: int, new_lap: int) -> None:
        if self._strategy is None:
            return
        for stop in self._strategy.stops:
            if stop.stop_number == stop_number and not stop.done:
                stop.planned_lap = new_lap
                break

    def evaluate(
        self,
        current_lap: int,
        avg_wear: float,
        wear_per_lap: float,
        tyre_wear_limit: float,
    ) -> PlannedStrategyStatus | None:
        if self._strategy is None or not self._strategy.stops:
            return None

        stop = self._strategy.next_stop(current_lap)
        if stop is None:
            return None

        laps_to_stop = stop.planned_lap - current_lap

        tyre_life: float = 9999.0
        if wear_per_lap > 0 and avg_wear < tyre_wear_limit:
            tyre_life = (tyre_wear_limit - avg_wear) / wear_per_lap

        can_reach = tyre_life >= laps_to_stop

        if laps_to_stop < 0:
            alert: str | None = "MISSED"
        elif laps_to_stop == 0:
            alert = "NOW"
        elif laps_to_stop <= 2:
            alert = "APPROACHING"
        elif not can_reach:
            alert = "TYRE_WARNING"
        else:
            alert = None

        return PlannedStrategyStatus(
            next_stop=stop,
            laps_to_planned_stop=laps_to_stop,
            tyres_can_reach_planned_stop=can_reach,
            tyre_life_remaining_laps=tyre_life,
            strategy_alert=alert,
        )

    def reset(self) -> None:
        if self._strategy:
            self._strategy.reset_done_flags()
