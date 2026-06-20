"""Race engineer strategy advisor: derives proactive strategy recommendations."""

from dataclasses import dataclass

from .planned_strategy import PlannedStrategy

_INF = 9999.0


@dataclass
class StrategyReport:
    laps_remaining: int
    fuel_to_finish: float          # litres needed from current lap to end
    fuel_delta: float              # positive = surplus, negative = shortfall
    laps_to_fuel_out_avg: float    # based on average fuel_per_lap
    laps_to_fuel_out_last: float   # based on last lap fuel consumption
    fuel_save_laps: int            # extra laps attainable if saving ~10% per lap
    recommended_stops: int         # 0, 1, 2, or 3
    stop_windows: list[tuple[int, int]]  # computed optimal windows (open, close)
    strategy_health: str           # "ON_PLAN" | "REVISE" | "CRITICAL"
    deviation_laps: int            # laps off from planned stop target (0 if no plan)
    deviation_alert: str | None    # human-readable note when health != ON_PLAN
    avg_lap_time_ms: int           # average of last N completed laps (0 if unavailable)


def _check_in_laps(total_laps: int, interval: int) -> set[int]:
    """Return set of laps where a strategy check-in should fire."""
    if total_laps <= 0:
        return set()
    if total_laps >= 10:
        # Fire at ~33% and ~66% of the race
        return {max(1, total_laps // 3), max(1, (total_laps * 2) // 3)}
    # Short race: fire every `interval` laps
    return {lap for lap in range(interval, total_laps, interval)}


class StrategyAdvisor:
    """Derives race strategy recommendations from telemetry and configuration."""

    def compute(
        self,
        current_lap: int,
        total_laps: int,
        fuel_level: float,
        fuel_per_lap_avg: float,
        last_lap_fuel: float,
        avg_lap_time_ms: int,
        avg_wear: float,  # noqa: ARG002 — reserved for tyre-stop calc
        wear_per_lap: float,  # noqa: ARG002
        tyre_wear_limit: float,  # noqa: ARG002
        pit_buffer_laps: int,
        planned_strategy: PlannedStrategy | None = None,
        pit_loss_time_s: float = 25.0,  # noqa: ARG002 — reserved for time-loss model
        fuel_save_pct: float = 0.10,
    ) -> StrategyReport | None:
        """Return a StrategyReport, or None when there is insufficient data."""
        if current_lap <= 0 or total_laps <= 0 or fuel_per_lap_avg <= 0:
            return None

        laps_remaining = max(0, total_laps - current_lap + 1)
        fuel_to_finish = laps_remaining * fuel_per_lap_avg
        fuel_delta = fuel_level - fuel_to_finish

        laps_to_fuel_out_avg: float = fuel_level / fuel_per_lap_avg
        laps_to_fuel_out_last: float = (
            fuel_level / last_lap_fuel if last_lap_fuel > 0 else _INF
        )

        # How many extra laps if driver saves fuel_save_pct per lap
        if fuel_per_lap_avg > 0 and fuel_save_pct > 0:
            effective_rate = fuel_per_lap_avg * (1.0 - fuel_save_pct)
            laps_saved = fuel_level / effective_rate - laps_to_fuel_out_avg
            fuel_save_laps = max(0, int(laps_saved))
        else:
            fuel_save_laps = 0

        # How many fuel stops are needed
        if fuel_delta >= 0:
            recommended_stops = 0
            stop_windows = []
        else:
            # Each stop provides a full tank refill (approximated as fuel_capacity)
            # We don't have fuel_capacity here, so estimate via fuel_per_lap * laps
            # A conservative approach: count how many stints of laps_to_fuel_out_avg fit
            stints_needed = int(-fuel_delta / (fuel_per_lap_avg * max(1, laps_to_fuel_out_avg))) + 1
            recommended_stops = max(1, min(3, stints_needed))
            stop_windows = _compute_stop_windows(
                current_lap, total_laps, recommended_stops, pit_buffer_laps
            )

        # Strategy health vs planned
        strategy_health, deviation_laps, deviation_alert = _evaluate_health(
            current_lap=current_lap,
            total_laps=total_laps,
            fuel_delta=fuel_delta,
            recommended_stops=recommended_stops,
            planned_strategy=planned_strategy,
        )

        return StrategyReport(
            laps_remaining=laps_remaining,
            fuel_to_finish=fuel_to_finish,
            fuel_delta=fuel_delta,
            laps_to_fuel_out_avg=laps_to_fuel_out_avg,
            laps_to_fuel_out_last=laps_to_fuel_out_last,
            fuel_save_laps=fuel_save_laps,
            recommended_stops=recommended_stops,
            stop_windows=stop_windows,
            strategy_health=strategy_health,
            deviation_laps=deviation_laps,
            deviation_alert=deviation_alert,
            avg_lap_time_ms=avg_lap_time_ms,
        )

    def should_check_in(
        self, current_lap: int, total_laps: int, interval: int, fired_laps: set[int]
    ) -> bool:
        """Return True if a strategy check-in should fire on this lap."""
        targets = _check_in_laps(total_laps, interval)
        return current_lap in targets and current_lap not in fired_laps


def _compute_stop_windows(
    current_lap: int,
    total_laps: int,
    num_stops: int,
    buffer_laps: int,
) -> list[tuple[int, int]]:
    """Distribute pit stops evenly across remaining laps."""
    laps_remaining = max(0, total_laps - current_lap)
    if num_stops <= 0 or laps_remaining <= 0:
        return []
    segment = laps_remaining // (num_stops + 1)
    windows: list[tuple[int, int]] = []
    for i in range(1, num_stops + 1):
        target = current_lap + segment * i
        open_lap = max(current_lap + 1, target - buffer_laps)
        close_lap = min(total_laps - 1, target + buffer_laps)
        windows.append((open_lap, close_lap))
    return windows


def _evaluate_health(
    current_lap: int,
    total_laps: int,
    fuel_delta: float,
    recommended_stops: int,
    planned_strategy: PlannedStrategy | None,
) -> tuple[str, int, str | None]:
    """Return (strategy_health, deviation_laps, deviation_alert)."""
    if fuel_delta < -5.0:
        return "CRITICAL", 0, f"Fuel shortfall {abs(fuel_delta):.1f}L"

    if planned_strategy is None or not planned_strategy.stops:
        if recommended_stops == 0:
            return "ON_PLAN", 0, None
        return "REVISE", 0, f"Needs {recommended_stops} stop(s), none planned"

    next_stop = planned_strategy.next_stop(current_lap)
    if next_stop is None:
        return "ON_PLAN", 0, None

    # Compare planned target vs recommended based on fuel
    planned_target = next_stop.target_lap
    if recommended_stops == 0 and planned_strategy.stops:
        # Can finish direct but user planned stops — minor deviation
        deviation = planned_target - total_laps
        if abs(deviation) <= 3:
            return "ON_PLAN", 0, None
        return "REVISE", abs(deviation), "May not need planned stops"

    # Check if planned stop is within reasonable range
    laps_remaining = max(0, total_laps - current_lap)
    if laps_remaining > 0:
        segment = laps_remaining // max(1, recommended_stops + 1)
        ideal_next = current_lap + segment
        deviation = abs(planned_target - ideal_next)
        if deviation > 5:
            return "REVISE", deviation, f"Planned lap {planned_target}, ideal ~{ideal_next}"

    return "ON_PLAN", 0, None
