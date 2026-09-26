"""Speed-to-fan-duty decision logic (pure, no I/O beyond the injected `Transport`).

Mirrors `voice.alert_engine.AlertEngine`'s shape: a plain class that takes a
telemetry-derived frame plus context and decides what to do, delegating the
actual send to a collaborator (`Transport`) rather than performing I/O itself.
"""

import logging

from . import protocol
from .transport import Transport

__all__ = ["FanController"]

log = logging.getLogger(__name__)


class FanController:
    def __init__(
        self,
        transport: Transport,
        max_speed_fallback_kmh: float = 250.0,
        send_interval_s: float = 0.1,
        kick_start_duty: int = 255,
        kick_start_duration_s: float = 0.2,
        min_sustain_duty: int = 0,
    ) -> None:
        self._transport = transport
        self._max_speed_fallback_kmh = max_speed_fallback_kmh
        self._send_interval_s = send_interval_s
        self._kick_start_duty = kick_start_duty
        self._kick_start_duration_s = kick_start_duration_s
        self._min_sustain_duty = min_sustain_duty
        self._last_duty: int | None = None
        self._last_sent_at: float | None = None
        self._kick_until: float | None = None

    def on_frame(self, speed_kmh: float, speed_max_kmh: float, paused: bool, now: float) -> None:
        """Call once per telemetry frame. Throttles actual sends to ~1 per
        `send_interval_s`.

        Always re-sends at that cadence, even when the computed duty cycle is
        unchanged from the last send — the device firmware has its own
        failsafe that zeroes the fans if no `FAN:` command arrives within
        5000ms (see docs/hardware/microcontroller.md), so a sustained,
        unchanging duty (e.g. cruising at a stable speed) must still be
        refreshed periodically or the firmware will cut the fans on its own.
        `send_interval_s` (default 100ms) gives a comfortable ~50x margin
        under that 5000ms window.

        Kick-start: a fan motor's static-friction breakaway torque isn't
        constant — it depends on where the rotor happens to be sitting
        relative to the stator poles when power is (re)applied, so the same
        low target duty that starts the fan reliably one time may only buzz
        without spinning the next. Whenever the computed duty transitions
        from 0 to non-zero (fan was stopped, now needs to move), this
        overrides the wire value to `kick_start_duty` (full power) for
        `kick_start_duration_s`, bypassing the send throttle so the kick
        begins immediately, before letting the actual computed duty take
        over. This guarantees the fan physically starts moving every time,
        regardless of rotor rest position, instead of occasionally just
        buzzing at a too-low duty until speed increases further.

        Minimum sustain duty: separately from the kick-start's brief full-
        power pulse, a fan's *sustained* rotation can also stutter or stall
        at a very low but non-zero duty, once already spinning. Any computed
        duty above 0 is floored to `min_sustain_duty` so cruising at low
        in-game speed never asks the fan to run below the level it can
        reliably sustain. Duty 0 (stopped/paused) is never floored — the fan
        is meant to be fully off then. Defaults to 0 (disabled) since the
        right value is fan- and voltage-dependent and must be found by
        bench testing (see docs/hardware/microcontroller.md).
        """
        if not self._transport.is_connected:
            return

        if paused:
            duty = 0
        else:
            effective_max = speed_max_kmh if speed_max_kmh > 0 else self._max_speed_fallback_kmh
            pct = max(0.0, min(1.0, speed_kmh / effective_max))
            duty = round(pct * 255)
            if duty > 0:
                duty = max(duty, self._min_sustain_duty)

        just_started_kick = False
        if duty == 0:
            self._kick_until = None
        elif self._last_duty == 0 or self._last_duty is None:
            self._kick_until = now + self._kick_start_duration_s
            just_started_kick = True

        send_duty = duty
        if duty > 0 and self._kick_until is not None and now < self._kick_until:
            send_duty = self._kick_start_duty

        if (
            not just_started_kick
            and self._last_sent_at is not None
            and now - self._last_sent_at < self._send_interval_s
        ):
            return

        self._transport.send_line(protocol.encode_fan_command(send_duty))
        if send_duty != self._last_duty:
            log.debug("FAN duty %s -> %d sent to device", self._last_duty, send_duty)
        self._last_duty = send_duty
        self._last_sent_at = now

    def shutdown(self) -> None:
        """Force-send `FAN:0`, bypassing the throttle/dedup checks in `on_frame`.

        Called on graceful app/service stop to guarantee a final "off" command
        reaches the device. Safe to call regardless of `Transport.is_connected`
        — a disconnected/never-connected transport treats `send_line()` as a
        no-op rather than raising. Also resets throttle/dedup/kick-start state
        so a subsequent `on_frame()` call (e.g. after a service restart) isn't
        skipped or affected by stale state from before shutdown.
        """
        self._transport.send_line(protocol.encode_fan_command(0))
        log.debug("FAN duty -> 0 sent to device (shutdown)")
        self._last_duty = None
        self._last_sent_at = None
        self._kick_until = None
