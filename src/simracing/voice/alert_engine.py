"""Monitors telemetry frames and fires voice alerts when thresholds are crossed."""

import time

from ..config import AppConfig
from ..strategy.planned_strategy import (
    PlannedStop,
    PlannedStrategy,
    PlannedStrategyMonitor,
    PlannedStrategyStatus,
)
from ..strategy.race_strategy import RaceStrategyEngine, StrategyResult
from ..strategy.stint_tracker import StintTracker
from ..telemetry.models import TelemetryData
from .templates import _lap_time_text, _laps_text, corner_name, format_alert, hot_corners_text

_ENGINE_COOLDOWN_S = 20.0
_OIL_COOLDOWN_S = 20.0


class AlertEngine:
    def __init__(self, config: AppConfig) -> None:
        self._config: AppConfig = config
        self._last_fired: dict[str, float] = {}
        self._prev_lap: int = -1
        self._prev_best_lap_ms: int = 0
        self._stint = StintTracker()
        self._strategy_engine = RaceStrategyEngine()
        self._planned_monitor = PlannedStrategyMonitor()
        self._strategy_result: StrategyResult | None = None
        self._planned_status: PlannedStrategyStatus | None = None
        self._window_entry_fired: set[int] = set()   # stop_numbers that got "window open" alert
        self._window_fuel_fired: set[int] = set()    # stop_numbers that got fuel warning in window
        self._last_fuel_alert_lap: int = -1          # gate: at most one fuel alert per lap
        self._race_report_fired: set[int] = set()    # checkpoints (35, 70) already reported
        self._apply_planned_strategy(config)

    def process(self, data: TelemetryData, fuel_per_lap: float) -> list[str]:
        """Return list of alert texts to speak (empty when nothing to say)."""
        if not data.in_race or data.paused or data.loading:
            return []

        alerts: list[str] = []
        now = time.monotonic()
        cfg = self._config
        lang: str = cfg.voice_language

        # ── Lap events ────────────────────────────────────────────────────────
        lap = data.current_lap
        if self._prev_lap >= 0 and lap != self._prev_lap:
            total: int = data.total_laps

            if cfg.voice_alert_final_lap and total > 0 and lap == total:
                alerts.append(format_alert("final_lap", lang))
            elif data.last_lap_ms > 0:
                lap_time = _lap_time_text(data.last_lap_ms, lang)
                is_best = (
                    cfg.voice_alert_best_lap
                    and data.best_lap_ms > 0
                    and data.best_lap_ms == data.last_lap_ms
                    and (self._prev_best_lap_ms == 0 or data.best_lap_ms < self._prev_best_lap_ms)
                )
                if is_best:
                    text = format_alert("best_lap", lang, lap_time=lap_time)
                elif cfg.voice_alert_lap_completed:
                    text = format_alert("lap_completed", lang, lap=self._prev_lap, lap_time=lap_time)
                else:
                    text = ""
                if text:
                    alerts.append(text)

        self._prev_lap = lap
        if data.best_lap_ms > 0:
            self._prev_best_lap_ms = data.best_lap_ms

        # ── Fuel ──────────────────────────────────────────────────────────────
        total_laps = data.total_laps
        clap = data.current_lap
        is_last_lap = total_laps > 0 and clap >= total_laps
        if data.fuel_capacity > 0 and not is_last_lap and self._last_fuel_alert_lap != clap:
            pct = data.fuel_pct
            laps_left = data.fuel_level / fuel_per_lap if fuel_per_lap > 0 else -1.0
            laps_text = _laps_text(laps_left, lang)
            critical_pct: float = cfg.voice_fuel_critical_pct
            low_pct: float = cfg.voice_fuel_low_pct

            if 0 < laps_left < 1.0:
                text = self._maybe_fire_interval(
                    f"fuel_last_lap_{clap}", now, 9999.0,
                    format_alert("fuel_last_lap", lang),
                )
                if text:
                    self._last_fuel_alert_lap = clap
                    alerts.append(text)
            elif cfg.voice_alert_fuel_critical and pct < critical_pct:
                text = self._maybe_fire_interval(
                    f"fuel_critical_{clap}", now, 9999.0,
                    format_alert("fuel_critical", lang,
                                 fuel=data.fuel_level, pct=pct * 100, laps_text=laps_text),
                )
                if text:
                    self._last_fuel_alert_lap = clap
                    alerts.append(text)
            elif cfg.voice_alert_fuel_low and pct < low_pct:
                text = self._maybe_fire_interval(
                    f"fuel_low_{clap}", now, 9999.0,
                    format_alert("fuel_low", lang,
                                 fuel=data.fuel_level, pct=pct * 100, laps_text=laps_text),
                )
                if text:
                    self._last_fuel_alert_lap = clap
                    alerts.append(text)

        # ── Engine temp ───────────────────────────────────────────────────────
        if cfg.voice_alert_engine_temp and data.water_temp > 0:
            threshold: float = cfg.voice_engine_temp_threshold
            if data.water_temp > threshold:
                text = self._maybe_fire_interval(
                    "engine_temp", now, _ENGINE_COOLDOWN_S,
                    format_alert("engine_temp_high", lang, temp=data.water_temp),
                )
                if text:
                    alerts.append(text)

        # ── Tire temp ─────────────────────────────────────────────────────────
        if cfg.voice_alert_tire_temp and data.tires:
            tire_threshold: float = cfg.voice_tire_temp_threshold
            temps = [t.surface_temp for t in data.tires]
            if any(t > tire_threshold for t in temps):
                corners = hot_corners_text(temps, tire_threshold, lang)
                text = self._maybe_fire_interval(
                    f"tire_temp_{data.current_lap}", now, 9999.0,
                    format_alert("tire_temp_high", lang, corners=corners),
                )
                if text:
                    alerts.append(text)

        # ── Tire inner zone temp (proxy for wear) ─────────────────────────────
        if cfg.voice_alert_tire_inner_temp and data.tires and self._stint.stint_laps > 0:
            inner_threshold: float = cfg.voice_tire_inner_temp_threshold
            inner_temps = [t.inner_temp for t in data.tires]
            if any(t > inner_threshold for t in inner_temps):
                corners = hot_corners_text(inner_temps, inner_threshold, lang)
                text = self._maybe_fire_interval(
                    f"tire_wear_{data.current_lap}", now, 9999.0,
                    format_alert("tire_wear_excessive", lang, corners=corners),
                )
                if text:
                    alerts.append(text)

        # ── Oil temperature ───────────────────────────────────────────────────
        if cfg.voice_alert_oil_temp and data.oil_temp > 0:
            oil_threshold: float = cfg.voice_oil_temp_threshold
            if data.oil_temp > oil_threshold:
                text = self._maybe_fire_interval(
                    "oil_temp", now, _OIL_COOLDOWN_S,
                    format_alert("oil_temp_high", lang, temp=data.oil_temp),
                )
                if text:
                    alerts.append(text)

        # ── Tire pressure ─────────────────────────────────────────────────────
        if cfg.voice_alert_tire_pressure and data.tires:
            pres_low: float = cfg.voice_tire_pressure_low_kpa
            pres_high: float = cfg.voice_tire_pressure_high_kpa
            pressures = [t.pressure for t in data.tires]
            if any(p > 0 for p in pressures):  # only when data is populated
                low_temps = [p for p in pressures if 0 < p < pres_low]
                high_temps = [p for p in pressures if p > pres_high]
                if low_temps:
                    corners = hot_corners_text(
                        pressures, pres_low,
                        lang,
                        invert=True,
                    )
                    text = self._maybe_fire_interval(
                        f"tire_pres_low_{data.current_lap}", now, 9999.0,
                        format_alert("tire_pressure_low", lang, corners=corners),
                    )
                    if text:
                        alerts.append(text)
                elif high_temps:
                    corners = hot_corners_text(pressures, pres_high, lang)
                    text = self._maybe_fire_interval(
                        f"tire_pres_high_{data.current_lap}", now, 9999.0,
                        format_alert("tire_pressure_high", lang, corners=corners),
                    )
                    if text:
                        alerts.append(text)

        # ── Lap delta ─────────────────────────────────────────────────────────
        if cfg.voice_alert_lap_delta and data.best_lap_ms > 0 and data.lap_time_ms > 0:
            delta_threshold_ms = int(cfg.voice_lap_delta_threshold_s * 1000)
            delta_ms = data.lap_time_ms - data.best_lap_ms
            past_halfway = data.lap_time_ms > data.best_lap_ms * 0.5
            if delta_ms > delta_threshold_ms and past_halfway:
                lap_key = f"lap_delta_{data.current_lap}"
                text = self._maybe_fire_interval(
                    lap_key, now, 9999.0,
                    format_alert("lap_delta_warn", lang, delta=delta_ms / 1000.0),
                )
                if text:
                    alerts.append(text)

        # ── Stint tracker + auto strategy ─────────────────────────────────────
        pit_detected = self._stint.update(data)
        if pit_detected:
            self._planned_monitor.on_pit_detected(data.current_lap)
            # Clear wear milestone keys so new stint fires alerts from scratch
            for k in list(self._last_fired):
                if k.startswith("tyre_wear_ms_"):
                    del self._last_fired[k]

        # ── Tyre wear milestone alerts ─────────────────────────────────────────
        if cfg.voice_alert_tyre_wear and self._stint.stint_laps > 0:
            avg_wear = self._stint.current_avg_wear
            threshold = cfg.voice_tyre_wear_threshold_pct
            if avg_wear >= threshold:
                bucket = int(avg_wear * 10)  # 0–10 → each 10% block
                text = self._maybe_fire_interval(
                    f"tyre_wear_ms_{bucket}", now, 9999.0,
                    format_alert("tyre_wear_milestone", lang, wear=bucket * 10),
                )
                if text:
                    alerts.append(text)

        self._strategy_result = self._strategy_engine.compute(
            current_lap=data.current_lap,
            total_laps=data.total_laps,
            fuel_level=data.fuel_level,
            fuel_per_lap=fuel_per_lap,
            avg_wear=self._stint.current_avg_wear,
            wear_per_lap=self._stint.wear_per_lap,
            tyre_wear_limit=cfg.tyre_wear_limit_pct,
            pit_buffer_laps=cfg.pit_buffer_laps,
        )

        self._planned_status = self._planned_monitor.evaluate(
            current_lap=data.current_lap,
            avg_wear=self._stint.current_avg_wear,
            wear_per_lap=self._stint.wear_per_lap,
            tyre_wear_limit=cfg.tyre_wear_limit_pct,
        )

        result = self._strategy_result
        clap = data.current_lap

        if cfg.voice_alert_strategy and result is not None:
            if is_last_lap and result.is_in_pit_window and not result.can_finish_direct:
                pit_is_fuel = "FUEL" in (result.pit_reason or "")
                if pit_is_fuel and self._last_fuel_alert_lap != clap:
                    text = self._maybe_fire_interval(
                        f"fuel_save_finish_{clap}", now, 9999.0,
                        format_alert("fuel_save_finish", lang),
                    )
                    if text:
                        self._last_fuel_alert_lap = clap
                        alerts.append(text)
            elif result.is_in_pit_window and not result.can_finish_direct and not is_last_lap:
                laps_label = max(0, result.laps_to_pit)
                pit_is_fuel = "FUEL" in (result.pit_reason or "")
                if not pit_is_fuel or self._last_fuel_alert_lap != clap:
                    _tmpl = "strategy_pit_window_now" if laps_label == 0 else "strategy_pit_window"
                    text = self._maybe_fire_interval(
                        f"strategy_pit_{clap}", now, 9999.0,
                        format_alert(_tmpl, lang,
                                     reason=result.pit_reason, laps=laps_label),
                    )
                    if text:
                        if pit_is_fuel:
                            self._last_fuel_alert_lap = clap
                        alerts.append(text)
            elif 2 <= result.laps_to_pit <= 5 and result.pit_reason in ("TYRES", "FUEL+TYRES") and not is_last_lap:
                text = self._maybe_fire_interval(
                    f"strategy_warn_{clap}", now, 9999.0,
                    format_alert("strategy_tyres_warn", lang,
                                 wear=int(self._stint.current_avg_wear * 100),
                                 laps=result.laps_to_pit),
                )
                if text:
                    alerts.append(text)
        elif cfg.voice_alert_pit_window and fuel_per_lap > 0 and data.total_laps > 0 and self._last_fuel_alert_lap != clap:
            # Fall back to basic pit window alert when auto strategy is disabled
            laps_of_fuel = data.fuel_level / fuel_per_lap
            laps_remaining = max(0, data.total_laps - data.current_lap + 1)
            pit_min: float = cfg.voice_pit_window_min_laps
            pit_max: float = cfg.voice_pit_window_max_laps
            if pit_min <= laps_of_fuel <= pit_max and laps_remaining > 1:
                text = self._maybe_fire_interval(
                    f"pit_window_{clap}", now, 9999.0,
                    format_alert("pit_window", lang, laps=laps_of_fuel),
                )
                if text:
                    self._last_fuel_alert_lap = clap
                    alerts.append(text)

        # ── Planned strategy alerts ───────────────────────────────────────────
        ps = self._planned_status
        if cfg.voice_alert_strategy and ps is not None:
            stop = ps.next_stop
            sn = stop.stop_number
            sa = ps.strategy_alert

            if sa == "APPROACHING_WINDOW":
                # Fire once per approaching lap ("window opens in 2 laps", then "in 1 lap")
                text = self._maybe_fire_interval(
                    f"plan_approaching_{sn}_{clap}", now, 9999.0,
                    format_alert("planned_pit_window_approaching", lang,
                                 laps=ps.laps_to_window_open),
                )
                if text:
                    alerts.append(text)

            elif sa in ("IN_WINDOW", "NOW", "PAST_TARGET", "WINDOW_CLOSING"):
                # On first entry into the window: announce once with laps available
                if sn not in self._window_entry_fired:
                    laps_available = ps.laps_to_window_close + 1
                    text = format_alert("planned_pit_window_open", lang, laps=laps_available)
                    if text:
                        self._window_entry_fired.add(sn)
                        alerts.append(text)
                # Inside the window: one additional alert only if fuel is running out
                elif sn not in self._window_fuel_fired and fuel_per_lap > 0 and self._last_fuel_alert_lap != clap:
                    laps_of_fuel = data.fuel_level / fuel_per_lap
                    if laps_of_fuel < 3.0:
                        text = format_alert("planned_pit_window_fuel_warn", lang, laps=laps_of_fuel)
                        if text:
                            self._window_fuel_fired.add(sn)
                            self._last_fuel_alert_lap = clap
                            alerts.append(text)

            elif sa == "MISSED":
                result = self._strategy_result
                if result is not None and result.laps_to_fuel_out > 1.0:
                    new_lap = result.recommended_pit_lap
                    self._planned_monitor.reschedule_missed_stop(sn, new_lap)
                    text = self._maybe_fire_interval(
                        f"plan_rescheduled_{sn}", now, 9999.0,
                        format_alert("planned_pit_rescheduled", lang, lap=new_lap),
                    )
                else:
                    text = self._maybe_fire_interval(
                        f"plan_missed_{sn}", now, 9999.0,
                        format_alert("planned_pit_missed", lang,
                                     open=stop.window_open, close=stop.window_close),
                    )
                if text:
                    alerts.append(text)

            elif sa == "TYRE_WARNING":
                life_lap = int(data.current_lap + ps.tyre_life_remaining_laps)
                text = self._maybe_fire_interval(
                    f"plan_tyre_warn_{sn}_{clap}", now, 9999.0,
                    format_alert("tyre_wont_reach", lang,
                                 life_lap=life_lap,
                                 plan_lap=stop.window_open),
                )
                if text:
                    alerts.append(text)

        # ── Race status report at 35% and 70% ────────────────────────────────
        if cfg.voice_alert_race_report and data.total_laps > 0 and data.current_lap > 0:
            race_pct = data.current_lap / data.total_laps * 100
            for checkpoint in (35, 70):
                if race_pct >= checkpoint and checkpoint not in self._race_report_fired:
                    self._race_report_fired.add(checkpoint)
                    avg_wear_pct = self._stint.current_avg_wear * 100
                    laps_remaining = data.total_laps - data.current_lap
                    report = format_alert("race_report", lang,
                                          pos=data.race_position,
                                          wear=avg_wear_pct,
                                          laps=laps_remaining)
                    if report and data.tires:
                        wears = [t.wear for t in data.tires]
                        max_wear = max(wears)
                        if max_wear > 0.30:
                            worst_idx = wears.index(max_wear)
                            cname = corner_name(lang, worst_idx)
                            warn = format_alert("race_report_tyre_warn", lang,
                                                corner=cname, wear=max_wear * 100)
                            if warn:
                                report = f"{report} {warn}"
                    if report:
                        alerts.append(report)

        return alerts

    @property
    def strategy_result(self) -> StrategyResult | None:
        return self._strategy_result

    @property
    def planned_status(self) -> PlannedStrategyStatus | None:
        return self._planned_status

    @property
    def stint(self) -> StintTracker:
        return self._stint

    def update_planned_strategy(self, config: AppConfig) -> None:
        self._apply_planned_strategy(config)

    def _apply_planned_strategy(self, config: AppConfig) -> None:
        if config.planned_stops <= 0 or not config.planned_stop_windows:
            self._planned_monitor.set_strategy(None)
            return
        stops = [
            PlannedStop(stop_number=i + 1, window_open=o, window_close=c)
            for i, (o, c) in enumerate(config.planned_stop_windows[:config.planned_stops])
        ]
        self._planned_monitor.set_strategy(PlannedStrategy(stops=stops))

    def reset(self) -> None:
        self._last_fired.clear()
        self._prev_lap = -1
        self._prev_best_lap_ms = 0
        self._stint.reset()
        self._planned_monitor.reset()
        self._strategy_result = None
        self._planned_status = None
        self._window_entry_fired.clear()
        self._window_fuel_fired.clear()
        self._last_fuel_alert_lap = -1
        self._race_report_fired.clear()

    def _maybe_fire(self, key: str, now: float, text: str) -> str | None:
        interval: float = self._config.voice_min_interval_s
        return self._maybe_fire_interval(key, now, interval, text)

    def _maybe_fire_interval(self, key: str, now: float, interval: float, text: str) -> str | None:
        if now - self._last_fired.get(key, 0.0) < interval:
            return None
        self._last_fired[key] = now
        return text
