"""Monitors telemetry frames and fires voice alerts when thresholds are crossed."""

import time

from ..telemetry.models import TelemetryData
from .templates import _laps_text, format_alert


class AlertEngine:
    def __init__(self, config: object) -> None:
        self._config = config
        self._last_fired: dict[str, float] = {}

    def process(self, data: TelemetryData, fuel_per_lap: float) -> list[str]:
        """Return list of alert texts to speak (empty when nothing to say)."""
        if not data.in_race or data.paused or data.loading:
            return []

        alerts: list[str] = []
        now = time.monotonic()
        lang: str = self._config.voice_language  # type: ignore[attr-defined]

        if data.fuel_capacity > 0:
            pct = data.fuel_pct
            laps_left = data.fuel_level / fuel_per_lap if fuel_per_lap > 0 else -1.0
            laps_text = _laps_text(laps_left, lang)

            critical_pct: float = self._config.voice_fuel_critical_pct  # type: ignore[attr-defined]
            low_pct: float = self._config.voice_fuel_low_pct  # type: ignore[attr-defined]

            if pct < critical_pct:
                text = self._maybe_fire(
                    "fuel_critical", now,
                    format_alert("fuel_critical", lang,
                                 fuel=data.fuel_level, pct=pct * 100, laps_text=laps_text),
                )
                if text:
                    alerts.append(text)
            elif pct < low_pct:
                text = self._maybe_fire(
                    "fuel_low", now,
                    format_alert("fuel_low", lang,
                                 fuel=data.fuel_level, pct=pct * 100, laps_text=laps_text),
                )
                if text:
                    alerts.append(text)

        return alerts

    def reset(self) -> None:
        self._last_fired.clear()

    def _maybe_fire(self, key: str, now: float, text: str) -> str | None:
        interval: float = self._config.voice_min_interval_s  # type: ignore[attr-defined]
        if now - self._last_fired.get(key, 0.0) < interval:
            return None
        self._last_fired[key] = now
        return text
