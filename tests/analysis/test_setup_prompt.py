import pytest

from simracing.analysis.setup_advisor.aggregator import SetupStats
from simracing.analysis.setup_advisor.prompt_builder import build


@pytest.fixture
def full_stats() -> SetupStats:
    return SetupStats(
        car_name="Mazda RX-7 Spirit R '02",
        laps_analyzed=[1, 2, 3],
        surf_temp={"FL": 90.0, "FR": 80.0, "RL": 85.0, "RR": 75.0},
        inner_temp={"FL": 95.0, "FR": 85.0, "RL": 90.0, "RR": 80.0},
        middle_temp={"FL": 92.0, "FR": 82.0, "RL": 87.0, "RR": 77.0},
        pressure_kpa={"FL": 220.0, "FR": 218.0, "RL": 225.0, "RR": 222.0},
        temp_imbalance_left_right=7.5,
        temp_imbalance_front_rear=5.0,
        temp_imbalance_diag_flrr=15.0,
        temp_imbalance_diag_frrl=5.0,
        slip_angle_mean=3.2,
        slip_angle_p95=8.5,
        g_lat_max=2.1,
        g_lat_mean=0.8,
        tcs_active_pct=12.5,
        asm_active_pct=0.0,
        sus_mean={"FL": 0.05, "FR": 0.05, "RL": 0.06, "RR": 0.06},
        full_throttle_pct=42.0,
        full_brake_pct=18.0,
        coasting_pct=15.0,
        throttle_brake_pct=2.0,
        data_quality={
            "surf_temp": True,
            "inner_temp": True,
            "middle_temp": True,
            "pressure": True,
            "slip_angle": True,
            "g_lat": True,
            "tcs": True,
            "asm": True,
            "suspension": True,
            "pedal_ticks": True,
        },
    )


@pytest.fixture
def legacy_stats(full_stats: SetupStats) -> SetupStats:
    """Stats with pressure unavailable (legacy Parquet)."""
    from dataclasses import replace

    dq = dict(full_stats.data_quality)
    dq["pressure"] = False
    return replace(
        full_stats,
        pressure_kpa={"FL": 0.0, "FR": 0.0, "RL": 0.0, "RR": 0.0},
        data_quality=dq,
    )


def test_build_returns_string(full_stats: SetupStats) -> None:
    result = build(full_stats, "Suzuka Circuit", "basic")
    assert isinstance(result, str)
    assert len(result) > 0


def test_prompt_contains_car_name(full_stats: SetupStats) -> None:
    result = build(full_stats, "Suzuka Circuit", "basic")
    assert "Mazda RX-7 Spirit R '02" in result


def test_prompt_contains_track(full_stats: SetupStats) -> None:
    result = build(full_stats, "Suzuka Circuit", "basic")
    assert "Suzuka Circuit" in result


def test_prompt_contains_laps(full_stats: SetupStats) -> None:
    result = build(full_stats, "Suzuka Circuit", "basic")
    assert "1" in result
    assert "2" in result
    assert "3" in result


def test_basic_level_excludes_advanced_domains(full_stats: SetupStats) -> None:
    result = build(full_stats, "Suzuka Circuit", "basic")
    result_lower = result.lower()
    assert "suspensão" not in result_lower or "posição média" not in result_lower
    assert "aerodinâmica" not in result_lower
    assert "acelerador fundo" not in result_lower


def test_advanced_level_includes_suspension(full_stats: SetupStats) -> None:
    result = build(full_stats, "Suzuka Circuit", "advanced")
    assert "Suspensão" in result


def test_advanced_level_includes_pedals(full_stats: SetupStats) -> None:
    result = build(full_stats, "Suzuka Circuit", "advanced")
    assert "Acelerador fundo" in result or "Pedais" in result


def test_both_levels_include_pressure(full_stats: SetupStats) -> None:
    for level in ("basic", "advanced"):
        result = build(full_stats, "Monza", level)
        assert "Pressões" in result or "kPa" in result


def test_data_quality_false_shows_unavailable(legacy_stats: SetupStats) -> None:
    result = build(legacy_stats, "Monza", "basic")
    assert "dados não disponíveis" in result


def test_case_insensitive_level(full_stats: SetupStats) -> None:
    r_lower = build(full_stats, "Monza", "basic")
    r_upper = build(full_stats, "Monza", "BASIC")
    r_mixed = build(full_stats, "Monza", "Basic")
    assert r_lower == r_upper == r_mixed


def test_invalid_level_raises(full_stats: SetupStats) -> None:
    with pytest.raises(ValueError):
        build(full_stats, "Monza", "expert")
