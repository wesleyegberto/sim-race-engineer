"""User-defined pit stop strategy tracker."""

from dataclasses import dataclass, field


@dataclass
class PlannedStop:
    stop_number: int
    window_open: int   # earliest lap to pit
    window_close: int  # latest lap to pit

    done: bool = False

    @property
    def target_lap(self) -> int:
        return (self.window_open + self.window_close) // 2

    @property
    def planned_lap(self) -> int:
        """Alias for target_lap — kept for display compat."""
        return self.target_lap


@dataclass
class PlannedStrategy:
    stops: list[PlannedStop] = field(default_factory=list)

    def next_stop(self, current_lap: int) -> PlannedStop | None:
        for stop in sorted(self.stops, key=lambda s: s.window_open):
            if not stop.done and stop.window_close >= current_lap - 1:
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
    laps_to_planned_stop: int     # laps to target_lap (for compat / display)
    laps_to_window_open: int      # negative when already in/past window
    laps_to_window_close: int     # negative when past window
    is_in_window: bool
    tyres_can_reach_planned_stop: bool
    tyre_life_remaining_laps: float
    # APPROACHING_WINDOW | IN_WINDOW | NOW | PAST_TARGET | WINDOW_CLOSING | MISSED | TYRE_WARNING | None
    strategy_alert: str | None


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
                stop.window_open = new_lap
                stop.window_close = new_lap
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

        laps_to_open = stop.window_open - current_lap
        laps_to_close = stop.window_close - current_lap
        is_in_window = laps_to_open <= 0 <= laps_to_close

        tyre_life: float = 9999.0
        if wear_per_lap > 0 and avg_wear < tyre_wear_limit:
            tyre_life = (tyre_wear_limit - avg_wear) / wear_per_lap

        can_reach = tyre_life >= laps_to_open

        if laps_to_close < 0:
            alert: str | None = "MISSED"
        elif is_in_window:
            if current_lap == stop.target_lap:
                alert = "NOW"
            elif laps_to_close == 0:
                # Last lap of window but already past target
                alert = "WINDOW_CLOSING"
            elif current_lap > stop.target_lap:
                alert = "PAST_TARGET"
            else:
                alert = "IN_WINDOW"
        elif 0 < laps_to_open <= 2:
            alert = "APPROACHING_WINDOW"
        elif not can_reach:
            alert = "TYRE_WARNING"
        else:
            alert = None

        return PlannedStrategyStatus(
            next_stop=stop,
            laps_to_planned_stop=stop.target_lap - current_lap,
            laps_to_window_open=laps_to_open,
            laps_to_window_close=laps_to_close,
            is_in_window=is_in_window,
            tyres_can_reach_planned_stop=can_reach,
            tyre_life_remaining_laps=tyre_life,
            strategy_alert=alert,
        )

    def reset(self) -> None:
        if self._strategy:
            self._strategy.reset_done_flags()
