"""Speed-to-fan-duty decision logic (pure, no I/O beyond the injected `Transport`).

Mirrors `voice.alert_engine.AlertEngine`'s shape: a plain class that takes a
telemetry-derived frame plus context and decides what to do, delegating the
actual send to a collaborator (`Transport`) rather than performing I/O itself.
"""

from . import protocol
from .transport import Transport

__all__ = ["FanController"]


class FanController:
    def __init__(
        self,
        transport: Transport,
        max_speed_fallback_kmh: float = 250.0,
        send_interval_s: float = 0.1,
    ) -> None:
        self._transport = transport
        self._max_speed_fallback_kmh = max_speed_fallback_kmh
        self._send_interval_s = send_interval_s
        self._last_duty: int | None = None
        self._last_sent_at: float | None = None

    def on_frame(self, speed_kmh: float, speed_max_kmh: float, paused: bool, now: float) -> None:
        """Call once per telemetry frame. Throttles actual sends to ~1 per
        `send_interval_s` and only sends when the resulting duty cycle changed.
        """
        if not self._transport.is_connected:
            return

        if paused:
            duty = 0
        else:
            effective_max = speed_max_kmh if speed_max_kmh > 0 else self._max_speed_fallback_kmh
            pct = max(0.0, min(1.0, speed_kmh / effective_max))
            duty = round(pct * 255)

        if self._last_sent_at is not None and now - self._last_sent_at < self._send_interval_s:
            return

        if duty == self._last_duty:
            return

        self._transport.send_line(protocol.encode_fan_command(duty))
        self._last_duty = duty
        self._last_sent_at = now

    def shutdown(self) -> None:
        """Force-send `FAN:0`, bypassing the throttle/dedup checks in `on_frame`.

        Called on graceful app/service stop to guarantee a final "off" command
        reaches the device. Safe to call regardless of `Transport.is_connected`
        — a disconnected/never-connected transport treats `send_line()` as a
        no-op rather than raising. Also resets throttle/dedup state so a
        subsequent `on_frame()` call (e.g. after a service restart) isn't
        skipped because of a stale `_last_duty`/`_last_sent_at`.
        """
        self._transport.send_line(protocol.encode_fan_command(0))
        self._last_duty = None
        self._last_sent_at = None
