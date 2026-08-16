"""Unit tests for StrategyAdvisor and helpers."""

import pytest

from simraceengineer.strategy.strategy_advisor import (
    StrategyAdvisor,
    StrategyReport,
    _check_in_laps,
    _compute_stop_windows,
    _evaluate_health,
)


# ── _check_in_laps ────────────────────────────────────────────────────────────

def test_check_in_laps_zero():
    assert _check_in_laps(0, 3) == set()


def test_check_in_laps_long_race():
    # 30-lap race, interval=3 → range(3, 30, 3) = {3,6,9,12,15,18,21,24,27}
    result = _check_in_laps(30, 3)
    assert result == set(range(3, 30, 3))


def test_check_in_laps_exactly_10():
    # 10-lap race, interval=3 → {3, 6, 9}
    result = _check_in_laps(10, 3)
    assert result == {3, 6, 9}


def test_check_in_laps_short_race():
    # 6-lap race, interval=3 → [3] (range(3,6,3)={3})
    result = _check_in_laps(6, 3)
    assert result == {3}


def test_check_in_laps_very_short():
    # 2-lap race, interval=3 → empty (no lap in range(3,2,3))
    result = _check_in_laps(2, 3)
    assert result == set()


# ── _compute_stop_windows ─────────────────────────────────────────────────────

def test_stop_windows_one_stop():
    # 20 laps, current=1, 1 stop, buffer=1 → segment=9, target=10
    windows = _compute_stop_windows(1, 20, 1, 1)
    assert len(windows) == 1
    open_lap, close_lap = windows[0]
    assert open_lap >= 2
    assert close_lap <= 19
    assert open_lap <= close_lap


def test_stop_windows_two_stops():
    windows = _compute_stop_windows(1, 30, 2, 1)
    assert len(windows) == 2
    assert windows[0][1] < windows[1][0] or windows[0][0] < windows[1][0]


def test_stop_windows_no_stops():
    assert _compute_stop_windows(1, 20, 0, 1) == []


def test_stop_windows_clamps_to_race():
    windows = _compute_stop_windows(18, 20, 1, 5)
    for open_lap, close_lap in windows:
        assert open_lap >= 19
        assert close_lap <= 19  # total_laps - 1


def test_stop_windows_never_inverted():
    # Edge case: few laps remaining, segment=0 with old code → inverted window
    windows = _compute_stop_windows(19, 20, 1, 0)
    for open_lap, close_lap in windows:
        assert open_lap <= close_lap


def test_stop_windows_fuel_cap_first_window():
    # Lap 3, fuel for 2 laps → fuel_out_lap=5, cap close at 4
    # Without cap: even distribution in 20-lap race puts window at ~6-8
    windows = _compute_stop_windows(3, 20, 1, 1, fuel_out_lap=5)
    assert len(windows) == 1
    _, close_lap = windows[0]
    assert close_lap <= 4  # must pit before lap 5 (fuel_out_lap - 1)


def test_stop_windows_many_stops_few_laps():
    # 3 stops needed with only 3 laps left: should produce ≤ 3 valid windows
    windows = _compute_stop_windows(17, 20, 3, 1)
    for open_lap, close_lap in windows:
        assert open_lap <= close_lap
        assert open_lap >= 18
        assert close_lap <= 19


# ── _evaluate_health ──────────────────────────────────────────────────────────

def test_evaluate_health_can_finish_no_plan():
    health, dev, alert = _evaluate_health(5, 20, 10.0, 0, None, [])
    assert health == "ON_PLAN"
    assert dev == 0
    assert alert is None


def test_evaluate_health_critical_fuel():
    health, _, alert = _evaluate_health(5, 20, -10.0, 2, None, [])
    assert health == "CRITICAL"
    assert alert is not None and "10.0" in alert


def test_evaluate_health_needs_stop_no_plan():
    health, _, alert = _evaluate_health(5, 20, -3.0, 1, None, [])
    assert health == "REVISE"
    assert alert is not None and "1 stop" in alert


def test_evaluate_health_missed_stop_becomes_revise():
    from simraceengineer.strategy.planned_strategy import PlannedStop, PlannedStrategy
    stop = PlannedStop(stop_number=1, window_open=8, window_close=10)
    plan = PlannedStrategy(stops=[stop])
    # current_lap=14: window_close(10) < current_lap-2(12) → missed (grace period=2)
    health, _, alert = _evaluate_health(14, 20, 0.0, 0, plan, [])
    assert health == "REVISE"
    assert alert is not None and "Missed" in alert


def test_evaluate_health_missed_stop_grace_period():
    from simraceengineer.strategy.planned_strategy import PlannedStop, PlannedStrategy
    stop = PlannedStop(stop_number=1, window_open=8, window_close=10)
    plan = PlannedStrategy(stops=[stop])
    # current_lap=12: window_close(10) == current_lap-2(10) → not missed yet
    health, _, _ = _evaluate_health(12, 20, 0.0, 0, plan, [])
    assert health == "ON_PLAN"


def test_evaluate_health_unnecessary_stop_always_revise():
    from simraceengineer.strategy.planned_strategy import PlannedStop, PlannedStrategy
    # recommended_stops=0 but user has stop planned near end of race
    stop = PlannedStop(stop_number=1, window_open=18, window_close=19)
    plan = PlannedStrategy(stops=[stop])
    health, _, alert = _evaluate_health(5, 20, 5.0, 0, plan, [])
    assert health == "REVISE"
    assert alert is not None and "not need" in alert


def test_evaluate_health_unnecessary_stop_too_early_no_revise():
    from simraceengineer.strategy.planned_strategy import PlannedStop, PlannedStrategy
    # recommended_stops=0 on lap 3 — fuel avg unstable, should NOT trigger REVISE
    stop = PlannedStop(stop_number=1, window_open=18, window_close=19)
    plan = PlannedStrategy(stops=[stop])
    health, _, _ = _evaluate_health(3, 20, 5.0, 0, plan, [])
    assert health == "ON_PLAN"


def test_evaluate_health_planned_within_advisor_window():
    from simraceengineer.strategy.planned_strategy import PlannedStop, PlannedStrategy
    # advisor window [9,11], planned stop target=10 → ON_PLAN
    stop = PlannedStop(stop_number=1, window_open=10, window_close=10)
    plan = PlannedStrategy(stops=[stop])
    health, _, _ = _evaluate_health(1, 20, -5.0, 1, plan, [(9, 11)])
    assert health == "ON_PLAN"


def test_evaluate_health_planned_outside_advisor_window():
    from simraceengineer.strategy.planned_strategy import PlannedStop, PlannedStrategy
    # advisor window [8,10], planned target=18, tolerance=max(2,20//15)=2 → REVISE
    stop = PlannedStop(stop_number=1, window_open=18, window_close=18)
    plan = PlannedStrategy(stops=[stop])
    health, dev, alert = _evaluate_health(1, 20, -5.0, 1, plan, [(8, 10)])
    assert health == "REVISE"
    assert dev > 0
    assert alert is not None and "ideal" in alert


# ── StrategyAdvisor.compute ───────────────────────────────────────────────────

def _make_advisor() -> StrategyAdvisor:
    return StrategyAdvisor()


def test_compute_returns_none_for_no_fuel_rate():
    advisor = _make_advisor()
    result = advisor.compute(
        current_lap=1, total_laps=20,
        fuel_level=50.0, fuel_per_lap_avg=0.0,
        last_lap_fuel=0.0, avg_lap_time_ms=0,
        avg_wear=0.0, wear_per_lap=0.0,
        tyre_wear_limit=0.8, pit_buffer_laps=1,
    )
    assert result is None


def test_compute_can_finish_without_stop():
    advisor = _make_advisor()
    result = advisor.compute(
        current_lap=1, total_laps=20,
        fuel_level=60.0, fuel_per_lap_avg=2.0,  # needs 40L, has 60L
        last_lap_fuel=2.0, avg_lap_time_ms=90_000,
        avg_wear=0.2, wear_per_lap=0.01,
        tyre_wear_limit=0.8, pit_buffer_laps=1,
    )
    assert isinstance(result, StrategyReport)
    assert result.recommended_stops == 0
    assert result.fuel_delta > 0
    assert result.strategy_health == "ON_PLAN"
    assert result.laps_remaining == 20


def test_compute_needs_one_stop():
    advisor = _make_advisor()
    result = advisor.compute(
        current_lap=1, total_laps=20,
        fuel_level=20.0, fuel_per_lap_avg=2.0,  # needs 40L, has 20L → shortfall 20L
        last_lap_fuel=2.1, avg_lap_time_ms=0,
        avg_wear=0.0, wear_per_lap=0.0,
        tyre_wear_limit=0.8, pit_buffer_laps=1,
        fuel_capacity=60.0,  # tank holds 60L → ceil(20/60)=1 stop
    )
    assert result is not None
    assert result.fuel_delta < 0
    assert result.recommended_stops == 1
    assert len(result.stop_windows) == 1


def test_compute_stops_formula_exact_multiple():
    # shortfall == fuel_level: old int(x)+1 formula gave 2; ceil gives 1
    advisor = _make_advisor()
    result = advisor.compute(
        current_lap=1, total_laps=20,
        fuel_level=20.0, fuel_per_lap_avg=2.0,
        last_lap_fuel=2.0, avg_lap_time_ms=0,
        avg_wear=0.0, wear_per_lap=0.0,
        tyre_wear_limit=0.8, pit_buffer_laps=1,
        fuel_capacity=20.0,  # refuel capacity = shortfall → exactly 1 stop
    )
    assert result is not None
    assert result.recommended_stops == 1


def test_compute_fuel_delta_values():
    advisor = _make_advisor()
    result = advisor.compute(
        current_lap=5, total_laps=20,
        fuel_level=30.0, fuel_per_lap_avg=2.0,  # 16 laps × 2L = 32L needed; delta = -2
        last_lap_fuel=1.9, avg_lap_time_ms=0,
        avg_wear=0.0, wear_per_lap=0.0,
        tyre_wear_limit=0.8, pit_buffer_laps=1,
    )
    assert result is not None
    assert result.laps_remaining == 16
    assert result.fuel_to_finish == pytest.approx(32.0)
    assert result.fuel_delta == pytest.approx(-2.0)


def test_compute_laps_to_fuel_out():
    advisor = _make_advisor()
    result = advisor.compute(
        current_lap=1, total_laps=30,
        fuel_level=40.0, fuel_per_lap_avg=2.0,
        last_lap_fuel=2.5, avg_lap_time_ms=0,
        avg_wear=0.0, wear_per_lap=0.0,
        tyre_wear_limit=0.8, pit_buffer_laps=1,
    )
    assert result is not None
    assert result.laps_to_fuel_out_avg == pytest.approx(20.0)
    assert result.laps_to_fuel_out_last == pytest.approx(16.0)


def test_compute_fuel_save_laps():
    advisor = _make_advisor()
    result = advisor.compute(
        current_lap=1, total_laps=20,
        fuel_level=20.0, fuel_per_lap_avg=2.0,  # 10 laps at normal rate
        last_lap_fuel=2.0, avg_lap_time_ms=0,
        avg_wear=0.0, wear_per_lap=0.0,
        tyre_wear_limit=0.8, pit_buffer_laps=1,
        fuel_save_pct=0.10,
    )
    assert result is not None
    # saving 10%: effective rate = 1.8 → 20/1.8 ≈ 11.1 laps, saves ~1 lap
    assert result.fuel_save_laps >= 1


def test_compute_avg_lap_time_propagated():
    advisor = _make_advisor()
    result = advisor.compute(
        current_lap=3, total_laps=10,
        fuel_level=15.0, fuel_per_lap_avg=1.5,
        last_lap_fuel=1.4, avg_lap_time_ms=95_000,
        avg_wear=0.0, wear_per_lap=0.0,
        tyre_wear_limit=0.8, pit_buffer_laps=1,
    )
    assert result is not None
    assert result.avg_lap_time_ms == 95_000


# ── StrategyAdvisor.should_check_in ──────────────────────────────────────────

def test_should_check_in_fires_at_target():
    advisor = _make_advisor()
    # 30-lap race, interval=3: targets = {3,6,9,12,...}
    assert advisor.should_check_in(12, 30, 3, set()) is True


def test_should_check_in_not_at_non_target():
    advisor = _make_advisor()
    assert advisor.should_check_in(5, 30, 3, set()) is False


def test_should_check_in_skips_fired():
    advisor = _make_advisor()
    assert advisor.should_check_in(12, 30, 3, {12}) is False


def test_should_check_in_short_race():
    advisor = _make_advisor()
    # 6-lap race, interval=3 → target = {3}
    assert advisor.should_check_in(3, 6, 3, set()) is True
    assert advisor.should_check_in(4, 6, 3, set()) is False


def test_should_check_in_interval_applies_to_all_race_lengths():
    advisor = _make_advisor()
    # interval=5: fires at 5, 10, 15, 20, 25 regardless of total
    for total in (8, 10, 20, 50):
        assert advisor.should_check_in(5, total, 5, set()) is True
        assert advisor.should_check_in(4, total, 5, set()) is False
