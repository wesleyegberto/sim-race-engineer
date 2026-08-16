"""Computes optimal pit stop window from fuel and tyre wear data."""

from dataclasses import dataclass

_INF = 9999.0


@dataclass
class StrategyResult:
    laps_to_fuel_out: float
    laps_to_tyre_limit: float
    recommended_pit_lap: int
    laps_to_pit: int
    is_in_pit_window: bool
    pit_reason: str          # "FUEL" | "TYRES" | "FUEL+TYRES"
    can_finish_direct: bool


class RaceStrategyEngine:
    def compute(
        self,
        current_lap: int,
        total_laps: int,
        fuel_level: float,
        fuel_per_lap: float,
        avg_wear: float,
        wear_per_lap: float,
        tyre_wear_limit: float = 0.80,
        pit_buffer_laps: int = 1,
    ) -> StrategyResult | None:
        """Return strategy result, or None when there is not enough data."""
        if current_lap <= 0 or total_laps <= 0:
            return None

        laps_remaining = max(0, total_laps - current_lap + 1)

        laps_to_fuel_out: float = _INF
        if fuel_per_lap > 0:
            laps_to_fuel_out = fuel_level / fuel_per_lap

        laps_to_tyre_limit: float = _INF
        if wear_per_lap > 0 and avg_wear < tyre_wear_limit:
            laps_to_tyre_limit = (tyre_wear_limit - avg_wear) / wear_per_lap

        if laps_to_fuel_out == _INF and laps_to_tyre_limit == _INF:
            return None

        can_finish_direct = (
            laps_to_fuel_out >= laps_remaining
            and laps_to_tyre_limit >= laps_remaining
        )

        close = (
            laps_to_fuel_out < _INF
            and laps_to_tyre_limit < _INF
            and abs(laps_to_fuel_out - laps_to_tyre_limit) <= 2
        )

        if close:
            pit_reason = "FUEL+TYRES"
            limiting = min(laps_to_fuel_out, laps_to_tyre_limit)
        elif laps_to_tyre_limit < laps_to_fuel_out and laps_to_tyre_limit < _INF:
            pit_reason = "TYRES"
            limiting = laps_to_tyre_limit
        elif laps_to_fuel_out < _INF:
            pit_reason = "FUEL"
            limiting = laps_to_fuel_out
        else:
            pit_reason = "TYRES"
            limiting = laps_to_tyre_limit

        raw_laps = max(0, int(limiting) - pit_buffer_laps)
        recommended_pit_lap = current_lap + raw_laps
        laps_to_pit = recommended_pit_lap - current_lap

        return StrategyResult(
            laps_to_fuel_out=laps_to_fuel_out,
            laps_to_tyre_limit=laps_to_tyre_limit,
            recommended_pit_lap=recommended_pit_lap,
            laps_to_pit=laps_to_pit,
            is_in_pit_window=laps_to_pit <= 0,
            pit_reason=pit_reason,
            can_finish_direct=can_finish_direct,
        )
