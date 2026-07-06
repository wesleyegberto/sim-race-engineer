import pytest
import pandas as pd

from simracing.analysis.setup_advisor.aggregator import lookup_car_name, compute, SetupStats


def test_known_car_code_returns_name() -> None:
    # ID 24 → "180SX Type X '96" per gt7_cars.json
    assert lookup_car_name(24) == "180SX Type X '96"


def test_another_known_car_code() -> None:
    # ID 82 → "Supra RZ '97"
    assert lookup_car_name(82) == "Supra RZ '97"


def test_zero_returns_desconhecido() -> None:
    assert lookup_car_name(0) == "Desconhecido"


def test_absent_code_returns_desconhecido() -> None:
    # 99999999 is not a real GT7 car code
    assert lookup_car_name(99999999) == "Desconhecido"


def test_cache_is_shared_between_calls() -> None:
    from simracing.analysis.setup_advisor import aggregator

    aggregator._cars = None  # reset cache
    result1 = lookup_car_name(24)
    cache_after_first = aggregator._cars
    result2 = lookup_car_name(82)
    cache_after_second = aggregator._cars

    assert result1 == "180SX Type X '96"
    assert result2 == "Supra RZ '97"
    assert cache_after_first is cache_after_second  # same dict object, loaded once


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _full_df() -> pd.DataFrame:
    """Two-lap DataFrame with all columns present and controlled values."""
    rows = []
    for lap in (1, 2):
        for _ in range(5):  # 5 frames per lap
            rows.append(
                {
                    "lap_number": lap,
                    # surface temps
                    "tire_fl_temp": 90.0,
                    "tire_fr_temp": 85.0,
                    "tire_rl_temp": 80.0,
                    "tire_rr_temp": 75.0,
                    # inner temps
                    "tire_fl_inner": 100.0,
                    "tire_fr_inner": 95.0,
                    "tire_rl_inner": 88.0,
                    "tire_rr_inner": 82.0,
                    # middle temps
                    "tire_fl_middle": 95.0,
                    "tire_fr_middle": 90.0,
                    "tire_rl_middle": 84.0,
                    "tire_rr_middle": 78.0,
                    # pressure
                    "tire_fl_pressure": 200.0,
                    "tire_fr_pressure": 202.0,
                    "tire_rl_pressure": 198.0,
                    "tire_rr_pressure": 200.0,
                    # suspension
                    "sus_fl": 0.05,
                    "sus_fr": 0.05,
                    "sus_rl": 0.06,
                    "sus_rr": 0.06,
                    # slip angle
                    "slip_angle_deg": 3.0,
                    # g-forces
                    "g_lat": 1.5,
                    "g_lon": -0.8,
                    # electronics
                    "tcs_active": True,
                    "asm_active": False,
                    # pedal ticks (same value every frame in the lap)
                    "full_throttle_ticks": 400,
                    "full_brake_ticks": 200,
                    "throttle_and_brake_ticks": 50,
                    "coasting_ticks": 350,
                }
            )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# compute() — basic return type
# ---------------------------------------------------------------------------

class TestComputeReturnType:
    def test_returns_setup_stats_instance(self) -> None:
        result = compute(_full_df(), car_name="Test Car")
        assert isinstance(result, SetupStats)

    def test_car_name_propagated(self) -> None:
        result = compute(_full_df(), car_name="Supra RZ '97")
        assert result.car_name == "Supra RZ '97"

    def test_default_car_name_desconhecido(self) -> None:
        result = compute(_full_df())
        assert result.car_name == "Desconhecido"

    def test_laps_analyzed_sorted(self) -> None:
        result = compute(_full_df())
        assert result.laps_analyzed == [1, 2]


# ---------------------------------------------------------------------------
# Temperature means
# ---------------------------------------------------------------------------

class TestTemperatureMeans:
    def setup_method(self) -> None:
        self.stats = compute(_full_df())

    def test_surf_temp_fl(self) -> None:
        assert self.stats.surf_temp["FL"] == pytest.approx(90.0)

    def test_surf_temp_rr(self) -> None:
        assert self.stats.surf_temp["RR"] == pytest.approx(75.0)

    def test_inner_temp_fl(self) -> None:
        assert self.stats.inner_temp["FL"] == pytest.approx(100.0)

    def test_middle_temp_fr(self) -> None:
        assert self.stats.middle_temp["FR"] == pytest.approx(90.0)


# ---------------------------------------------------------------------------
# Temperature imbalances
# ---------------------------------------------------------------------------

class TestTemperatureImbalances:
    def setup_method(self) -> None:
        self.stats = compute(_full_df())

    def test_diag_flrr(self) -> None:
        # FL=90, RR=75 → 15.0
        assert self.stats.temp_imbalance_diag_flrr == pytest.approx(15.0)

    def test_diag_frrl(self) -> None:
        # FR=85, RL=80 → 5.0
        assert self.stats.temp_imbalance_diag_frrl == pytest.approx(5.0)

    def test_left_right(self) -> None:
        # left=(90+80)/2=85, right=(85+75)/2=80 → 5.0
        assert self.stats.temp_imbalance_left_right == pytest.approx(5.0)

    def test_front_rear(self) -> None:
        # front=(90+85)/2=87.5, rear=(80+75)/2=77.5 → 10.0
        assert self.stats.temp_imbalance_front_rear == pytest.approx(10.0)


# ---------------------------------------------------------------------------
# Pressure
# ---------------------------------------------------------------------------

class TestPressure:
    def test_pressure_values_correct(self) -> None:
        stats = compute(_full_df())
        assert stats.pressure_kpa["FL"] == pytest.approx(200.0)
        assert stats.pressure_kpa["FR"] == pytest.approx(202.0)

    def test_pressure_data_quality_true_when_present(self) -> None:
        stats = compute(_full_df())
        assert stats.data_quality["pressure"] is True

    def test_pressure_zero_and_quality_false_when_absent(self) -> None:
        df = _full_df().drop(
            columns=["tire_fl_pressure", "tire_fr_pressure", "tire_rl_pressure", "tire_rr_pressure"]
        )
        stats = compute(df)
        assert stats.data_quality["pressure"] is False
        assert stats.pressure_kpa["FL"] == pytest.approx(0.0)
        assert stats.pressure_kpa["RR"] == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Slip angle
# ---------------------------------------------------------------------------

class TestSlipAngle:
    def test_slip_angle_mean(self) -> None:
        stats = compute(_full_df())
        assert stats.slip_angle_mean == pytest.approx(3.0)

    def test_slip_angle_p95(self) -> None:
        stats = compute(_full_df())
        assert stats.slip_angle_p95 == pytest.approx(3.0)

    def test_slip_angle_zero_when_absent(self) -> None:
        df = _full_df().drop(columns=["slip_angle_deg"])
        stats = compute(df)
        assert stats.slip_angle_mean == pytest.approx(0.0)
        assert stats.data_quality["slip_angle"] is False


# ---------------------------------------------------------------------------
# Electronics
# ---------------------------------------------------------------------------

class TestElectronics:
    def test_tcs_active_100pct(self) -> None:
        # all rows have tcs_active=True
        stats = compute(_full_df())
        assert stats.tcs_active_pct == pytest.approx(100.0)

    def test_asm_active_0pct(self) -> None:
        stats = compute(_full_df())
        assert stats.asm_active_pct == pytest.approx(0.0)

    def test_tcs_zero_when_absent(self) -> None:
        df = _full_df().drop(columns=["tcs_active"])
        stats = compute(df)
        assert stats.tcs_active_pct == pytest.approx(0.0)
        assert stats.data_quality["tcs"] is False


# ---------------------------------------------------------------------------
# Pedal ticks
# ---------------------------------------------------------------------------

class TestPedalTicks:
    def test_pedal_pcts_sum_to_100(self) -> None:
        stats = compute(_full_df())
        total = (
            stats.full_throttle_pct
            + stats.full_brake_pct
            + stats.coasting_pct
            + stats.throttle_brake_pct
        )
        assert total == pytest.approx(100.0, abs=0.1)

    def test_full_throttle_pct_correct(self) -> None:
        # ticks: 400 + 200 + 50 + 350 = 1000; throttle = 400/1000 = 40%
        stats = compute(_full_df())
        assert stats.full_throttle_pct == pytest.approx(40.0)

    def test_pedal_zero_when_absent(self) -> None:
        df = _full_df().drop(columns=list(["full_throttle_ticks", "full_brake_ticks",
                                           "throttle_and_brake_ticks", "coasting_ticks"]))
        stats = compute(df)
        assert stats.full_throttle_pct == pytest.approx(0.0)
        assert stats.data_quality["pedal_ticks"] is False


# ---------------------------------------------------------------------------
# Data quality flags — missing surf temp columns
# ---------------------------------------------------------------------------

class TestDataQualityFlags:
    def test_surf_temp_quality_false_when_partial(self) -> None:
        df = _full_df().drop(columns=["tire_fl_temp"])
        stats = compute(df)
        assert stats.data_quality["surf_temp"] is False

    def test_all_quality_true_for_full_df(self) -> None:
        stats = compute(_full_df())
        for key in ("surf_temp", "inner_temp", "middle_temp", "pressure",
                    "slip_angle", "g_lat", "tcs", "asm", "suspension", "pedal_ticks"):
            assert stats.data_quality[key] is True, f"data_quality[{key!r}] should be True"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_df_returns_setup_stats(self) -> None:
        df = pd.DataFrame()
        stats = compute(df)
        assert isinstance(stats, SetupStats)
        assert stats.laps_analyzed == []
        assert stats.surf_temp == {"FL": 0.0, "FR": 0.0, "RL": 0.0, "RR": 0.0}

    def test_no_lap_number_column(self) -> None:
        df = _full_df().drop(columns=["lap_number"])
        stats = compute(df)
        assert stats.laps_analyzed == []
