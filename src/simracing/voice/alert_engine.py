"""Monitors telemetry frames and fires voice alerts when thresholds are crossed."""

import time

from ..telemetry.models import TelemetryData
from .templates import _lap_time_text, _laps_text, format_alert, hot_corners_text

_TIRE_COOLDOWN_S = 30.0
_ENGINE_COOLDOWN_S = 20.0


class AlertEngine:
    def __init__(self, config: object) -> None:
        self._config = config
        self._last_fired: dict[str, float] = {}
        self._prev_lap: int = -1
        self._prev_best_lap_ms: int = 0

    def process(self, data: TelemetryData, fuel_per_lap: float) -> list[str]:
        """Return list of alert texts to speak (empty when nothing to say)."""
        if not data.in_race or data.paused or data.loading:
            return []

        alerts: list[str] = []
        now = time.monotonic()
        cfg = self._config
        lang: str = cfg.voice_language  # type: ignore[attr-defined]

        # ── Lap events ────────────────────────────────────────────────────────
        lap = data.current_lap
        if self._prev_lap >= 0 and lap != self._prev_lap:
            total: int = data.total_laps

            if cfg.voice_alert_final_lap and total > 0 and lap == total:  # type: ignore[attr-defined]
                alerts.append(format_alert("final_lap", lang))
            elif data.last_lap_ms > 0:
                lap_time = _lap_time_text(data.last_lap_ms, lang)
                is_best = (
                    cfg.voice_alert_best_lap  # type: ignore[attr-defined]
                    and data.best_lap_ms > 0
                    and data.best_lap_ms == data.last_lap_ms
                    and (self._prev_best_lap_ms == 0 or data.best_lap_ms < self._prev_best_lap_ms)
                )
                if is_best:
                    text = format_alert("best_lap", lang, lap_time=lap_time)
                elif cfg.voice_alert_lap_completed:  # type: ignore[attr-defined]
                    text = format_alert("lap_completed", lang, lap=self._prev_lap, lap_time=lap_time)
                else:
                    text = ""
                if text:
                    alerts.append(text)

        self._prev_lap = lap
        if data.best_lap_ms > 0:
            self._prev_best_lap_ms = data.best_lap_ms

        # ── Fuel ──────────────────────────────────────────────────────────────
        if data.fuel_capacity > 0:
            pct = data.fuel_pct
            laps_left = data.fuel_level / fuel_per_lap if fuel_per_lap > 0 else -1.0
            laps_text = _laps_text(laps_left, lang)
            critical_pct: float = cfg.voice_fuel_critical_pct  # type: ignore[attr-defined]
            low_pct: float = cfg.voice_fuel_low_pct  # type: ignore[attr-defined]

            if cfg.voice_alert_fuel_critical and pct < critical_pct:  # type: ignore[attr-defined]
                text = self._maybe_fire(
                    "fuel_critical", now,
                    format_alert("fuel_critical", lang,
                                 fuel=data.fuel_level, pct=pct * 100, laps_text=laps_text),
                )
                if text:
                    alerts.append(text)
            elif cfg.voice_alert_fuel_low and pct < low_pct:  # type: ignore[attr-defined]
                text = self._maybe_fire(
                    "fuel_low", now,
                    format_alert("fuel_low", lang,
                                 fuel=data.fuel_level, pct=pct * 100, laps_text=laps_text),
                )
                if text:
                    alerts.append(text)

        # ── Engine temp ───────────────────────────────────────────────────────
        if cfg.voice_alert_engine_temp and data.water_temp > 0:  # type: ignore[attr-defined]
            threshold: float = cfg.voice_engine_temp_threshold  # type: ignore[attr-defined]
            if data.water_temp > threshold:
                text = self._maybe_fire_interval(
                    "engine_temp", now, _ENGINE_COOLDOWN_S,
                    format_alert("engine_temp_high", lang, temp=data.water_temp),
                )
                if text:
                    alerts.append(text)

        # ── Tire temp ─────────────────────────────────────────────────────────
        if cfg.voice_alert_tire_temp and data.tires:  # type: ignore[attr-defined]
            tire_threshold: float = cfg.voice_tire_temp_threshold  # type: ignore[attr-defined]
            temps = [t.surface_temp for t in data.tires]
            if any(t > tire_threshold for t in temps):
                corners = hot_corners_text(temps, tire_threshold, lang)
                text = self._maybe_fire_interval(
                    "tire_temp", now, _TIRE_COOLDOWN_S,
                    format_alert("tire_temp_high", lang, corners=corners),
                )
                if text:
                    alerts.append(text)

        # ── Tire inner zone temp (proxy for wear) ─────────────────────────────
        if cfg.voice_alert_tire_inner_temp and data.tires:  # type: ignore[attr-defined]
            inner_threshold: float = cfg.voice_tire_inner_temp_threshold  # type: ignore[attr-defined]
            inner_temps = [t.inner_temp for t in data.tires]
            if any(t > inner_threshold for t in inner_temps):
                corners = hot_corners_text(inner_temps, inner_threshold, lang)
                text = self._maybe_fire_interval(
                    "tire_wear", now, _TIRE_COOLDOWN_S,
                    format_alert("tire_wear_excessive", lang, corners=corners),
                )
                if text:
                    alerts.append(text)

        return alerts

    def reset(self) -> None:
        self._last_fired.clear()
        self._prev_lap = -1
        self._prev_best_lap_ms = 0

    def _maybe_fire(self, key: str, now: float, text: str) -> str | None:
        interval: float = self._config.voice_min_interval_s  # type: ignore[attr-defined]
        return self._maybe_fire_interval(key, now, interval, text)

    def _maybe_fire_interval(self, key: str, now: float, interval: float, text: str) -> str | None:
        if now - self._last_fired.get(key, 0.0) < interval:
            return None
        self._last_fired[key] = now
        return text
