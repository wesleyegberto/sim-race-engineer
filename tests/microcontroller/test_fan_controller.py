"""Unit tests for `FanController`'s speed->duty mapping, throttle, and
periodic-resend (device failsafe compliance) logic.

Uses a stub `Transport` that records every `send_line()` call instead of doing
real serial I/O — mirrors the `_StubTransport` pattern already used in
`test_service.py`.
"""

from simraceengineer.microcontroller.fan_controller import FanController


class _StubTransport:
    def __init__(self, connected: bool = True) -> None:
        self.connected = connected
        self.sent: list[str] = []

    def send_line(self, line: str) -> None:
        self.sent.append(line)

    @property
    def is_connected(self) -> bool:
        return self.connected


# ── duty-cycle mapping ───────────────────────────────────────────────────────
#
# Fan duty is computed on an absolute km/h scale: `pct = speed_kmh /
# speed_ceiling_kmh`, clamped to 100% — a single configurable ceiling shared
# across all cars, rather than a per-car relative scale driven by telemetry's
# `speed_max_kmh` (which no longer factors into this calculation at all).

def test_speed_zero_sends_duty_zero():
    transport = _StubTransport()
    fan = FanController(transport)

    fan.on_frame(speed_kmh=0.0, paused=False, now=0.0)

    assert transport.sent == ["FAN:0\n"]


def test_speed_equal_to_ceiling_sends_full_duty():
    transport = _StubTransport()
    fan = FanController(transport, speed_ceiling_kmh=200.0)

    fan.on_frame(speed_kmh=200.0, paused=False, now=0.0)

    assert transport.sent == ["FAN:255\n"]


def test_speed_above_ceiling_is_clamped_to_full_duty():
    transport = _StubTransport()
    fan = FanController(transport, speed_ceiling_kmh=200.0)

    fan.on_frame(speed_kmh=300.0, paused=False, now=0.0)

    assert transport.sent == ["FAN:255\n"]


def test_intermediate_speed_scales_linearly():
    transport = _StubTransport()
    fan = FanController(transport, speed_ceiling_kmh=200.0, kick_start_duration_s=0.0)

    # 50 km/h of a 200 km/h ceiling == 25% duty == round(0.25 * 255) == 64
    fan.on_frame(speed_kmh=50.0, paused=False, now=0.0)

    assert transport.sent == ["FAN:64\n"]


def test_default_ceiling_is_220_kmh():
    transport = _StubTransport()
    fan = FanController(transport, kick_start_duration_s=0.0)

    # 110 km/h of the default 220 km/h ceiling == 50% duty == round(0.5 * 255) == 128
    fan.on_frame(speed_kmh=110.0, paused=False, now=0.0)

    assert transport.sent == ["FAN:128\n"]


def test_zero_or_negative_ceiling_is_treated_as_always_full_duty():
    transport = _StubTransport()
    fan = FanController(transport, speed_ceiling_kmh=0.0, kick_start_duration_s=0.0)

    # Must not raise (no division by zero) and must not produce a negative/
    # nonsensical percentage — treated as always-full-duty instead.
    fan.on_frame(speed_kmh=10.0, paused=False, now=0.0)

    assert transport.sent == ["FAN:255\n"]

    transport2 = _StubTransport()
    fan2 = FanController(transport2, speed_ceiling_kmh=-50.0, kick_start_duration_s=0.0)

    fan2.on_frame(speed_kmh=10.0, paused=False, now=0.0)

    assert transport2.sent == ["FAN:255\n"]


# ── paused handling ──────────────────────────────────────────────────────────

def test_paused_forces_duty_zero_regardless_of_speed():
    transport = _StubTransport()
    fan = FanController(transport, speed_ceiling_kmh=200.0)

    fan.on_frame(speed_kmh=250.0, paused=True, now=0.0)

    assert transport.sent == ["FAN:0\n"]


def test_paused_after_high_speed_sends_zero_once_interval_elapses():
    transport = _StubTransport(connected=True)
    fan = FanController(transport, speed_ceiling_kmh=200.0, send_interval_s=0.1)

    fan.on_frame(speed_kmh=200.0, paused=False, now=0.0)
    fan.on_frame(speed_kmh=200.0, paused=True, now=0.2)

    assert transport.sent == ["FAN:255\n", "FAN:0\n"]


# ── disconnected transport ───────────────────────────────────────────────────

def test_does_nothing_when_transport_not_connected():
    transport = _StubTransport(connected=False)
    fan = FanController(transport, speed_ceiling_kmh=200.0)

    fan.on_frame(speed_kmh=200.0, paused=False, now=0.0)

    assert transport.sent == []


# ── throttle window ──────────────────────────────────────────────────────────

def test_throttle_skips_second_send_before_interval_elapses():
    transport = _StubTransport()
    fan = FanController(transport, speed_ceiling_kmh=200.0, send_interval_s=0.1, kick_start_duration_s=0.0)

    fan.on_frame(speed_kmh=50.0, paused=False, now=0.0)
    fan.on_frame(speed_kmh=100.0, paused=False, now=0.05)

    assert transport.sent == ["FAN:64\n"]


def test_throttle_allows_send_once_interval_elapses():
    transport = _StubTransport()
    fan = FanController(transport, speed_ceiling_kmh=200.0, send_interval_s=0.1, kick_start_duration_s=0.0)

    fan.on_frame(speed_kmh=50.0, paused=False, now=0.0)
    fan.on_frame(speed_kmh=100.0, paused=False, now=0.1)

    assert transport.sent == ["FAN:64\n", "FAN:128\n"]


def test_skipped_send_does_not_reset_throttle_clock():
    transport = _StubTransport()
    fan = FanController(transport, speed_ceiling_kmh=200.0, send_interval_s=0.1, kick_start_duration_s=0.0)

    fan.on_frame(speed_kmh=50.0, paused=False, now=0.0)
    # Skipped: interval hasn't elapsed since the last real send.
    fan.on_frame(speed_kmh=100.0, paused=False, now=0.05)
    # Still measured from the last real send (t=0.0), not the skipped call
    # (t=0.05) — so this must go through at t=0.1, not be skipped again.
    fan.on_frame(speed_kmh=100.0, paused=False, now=0.1)

    assert transport.sent == ["FAN:64\n", "FAN:128\n"]


# ── periodic resend / device failsafe compliance ─────────────────────────────
#
# The device firmware zeroes the fans if no `FAN:` command arrives within
# 5000ms (see docs/hardware/microcontroller.md), even to re-affirm an
# unchanged value. `on_frame()` must therefore keep sending at the throttle
# cadence regardless of whether the computed duty changed — otherwise a car
# holding a stable speed (e.g. cruising near top speed on a straight) goes
# silent for long enough that the device's own failsafe cuts the fans,
# only resuming once the next duty *change* triggers a fresh send.

def test_resends_periodically_even_when_duty_is_unchanged():
    transport = _StubTransport()
    fan = FanController(transport, speed_ceiling_kmh=200.0, send_interval_s=0.1, kick_start_duration_s=0.0)

    fan.on_frame(speed_kmh=100.0, paused=False, now=0.0)
    fan.on_frame(speed_kmh=100.0, paused=False, now=0.2)
    fan.on_frame(speed_kmh=100.0, paused=False, now=0.4)

    assert transport.sent == ["FAN:128\n", "FAN:128\n", "FAN:128\n"]


def test_still_throttled_when_duty_is_unchanged_within_interval():
    transport = _StubTransport()
    fan = FanController(transport, speed_ceiling_kmh=200.0, send_interval_s=0.1, kick_start_duration_s=0.0)

    fan.on_frame(speed_kmh=100.0, paused=False, now=0.0)
    fan.on_frame(speed_kmh=100.0, paused=False, now=0.05)

    assert transport.sent == ["FAN:128\n"]


def test_dedup_does_not_apply_across_different_duty_values():
    transport = _StubTransport()
    fan = FanController(transport, speed_ceiling_kmh=200.0, send_interval_s=0.1, kick_start_duration_s=0.0)

    fan.on_frame(speed_kmh=50.0, paused=False, now=0.0)
    fan.on_frame(speed_kmh=100.0, paused=False, now=0.2)

    assert transport.sent == ["FAN:64\n", "FAN:128\n"]


# ── kick-start (static-friction breakaway) ────────────────────────────────────
#
# A fan motor's breakaway torque isn't constant — it depends on where the
# rotor happens to be sitting relative to the stator poles when power is
# (re)applied, so the same low target duty that starts the fan reliably one
# time may only buzz without spinning the next. Whenever the computed duty
# transitions from 0 (or the controller's initial unsent state) to non-zero,
# on_frame() overrides the wire value to `kick_start_duty` for
# `kick_start_duration_s`, bypassing the throttle so the kick begins
# immediately, before letting the real computed duty take over.

def test_first_nonzero_duty_is_kick_started_at_full_power():
    transport = _StubTransport()
    fan = FanController(transport, speed_ceiling_kmh=200.0, kick_start_duration_s=0.2)

    # Target duty would be 64 (25% of 255), but the fan was at rest (never
    # sent before) — it must be kick-started at full power instead.
    fan.on_frame(speed_kmh=50.0, paused=False, now=0.0)

    assert transport.sent == ["FAN:255\n"]


def test_kick_start_bypasses_the_send_throttle():
    transport = _StubTransport()
    fan = FanController(transport, speed_ceiling_kmh=200.0, send_interval_s=0.1, kick_start_duration_s=0.2)

    fan.on_frame(speed_kmh=0.0, paused=False, now=0.0)
    # Only 10ms since the last send — would normally be throttled, but a
    # fresh kick-start must never be delayed by the steady-state throttle.
    fan.on_frame(speed_kmh=50.0, paused=False, now=0.01)

    assert transport.sent == ["FAN:0\n", "FAN:255\n"]


def test_kick_continues_for_its_full_duration_then_hands_off_to_real_duty():
    transport = _StubTransport()
    fan = FanController(transport, speed_ceiling_kmh=200.0, send_interval_s=0.1, kick_start_duration_s=0.2)

    # Gaps of 0.12s (not 0.1s) between calls to stay clear of the throttle
    # window's boundary, which is otherwise sensitive to float rounding
    # (e.g. 0.3 - 0.2 == 0.09999999999999998, just under a 0.1s threshold).
    fan.on_frame(speed_kmh=50.0, paused=False, now=0.0)   # kick starts
    fan.on_frame(speed_kmh=50.0, paused=False, now=0.12)  # still kicking
    fan.on_frame(speed_kmh=50.0, paused=False, now=0.24)  # kick just ended
    fan.on_frame(speed_kmh=50.0, paused=False, now=0.36)  # real duty continues

    assert transport.sent == ["FAN:255\n", "FAN:255\n", "FAN:64\n", "FAN:64\n"]


def test_custom_kick_start_duty_is_used_instead_of_full_power():
    transport = _StubTransport()
    fan = FanController(transport, speed_ceiling_kmh=200.0, kick_start_duty=200, kick_start_duration_s=0.2)

    fan.on_frame(speed_kmh=50.0, paused=False, now=0.0)

    assert transport.sent == ["FAN:200\n"]


def test_returning_to_zero_then_moving_again_triggers_a_fresh_kick():
    transport = _StubTransport()
    fan = FanController(transport, speed_ceiling_kmh=200.0, send_interval_s=0.1, kick_start_duration_s=0.2)

    fan.on_frame(speed_kmh=50.0, paused=False, now=0.0)  # kick #1
    fan.on_frame(speed_kmh=0.0, paused=False, now=0.3)   # stopped
    fan.on_frame(speed_kmh=50.0, paused=False, now=0.4)  # kick #2 (fresh)

    assert transport.sent == ["FAN:255\n", "FAN:0\n", "FAN:255\n"]


def test_no_kick_when_duty_never_leaves_zero():
    transport = _StubTransport()
    fan = FanController(transport, speed_ceiling_kmh=200.0, send_interval_s=0.1, kick_start_duration_s=0.2)

    fan.on_frame(speed_kmh=0.0, paused=False, now=0.0)
    fan.on_frame(speed_kmh=0.0, paused=False, now=0.2)

    assert transport.sent == ["FAN:0\n", "FAN:0\n"]


def test_shutdown_resets_kick_state_so_next_on_frame_kicks_again():
    transport = _StubTransport()
    fan = FanController(transport, speed_ceiling_kmh=200.0, kick_start_duration_s=0.2)

    fan.on_frame(speed_kmh=50.0, paused=False, now=0.0)  # kick #1...
    fan.on_frame(speed_kmh=50.0, paused=False, now=0.5)  # ...settles to real duty
    fan.shutdown()
    transport.sent.clear()

    # Same instant as the last on_frame() call — would be a no-op throttle
    # skip if shutdown() hadn't reset the kick/throttle state.
    fan.on_frame(speed_kmh=50.0, paused=False, now=0.5)

    assert transport.sent == ["FAN:255\n"]


# ── minimum sustain duty ─────────────────────────────────────────────────────
#
# Separately from the kick-start's brief full-power pulse, a fan's *sustained*
# rotation can also stutter or stall at a very low but non-zero duty, once
# already spinning. Any computed duty above 0 is floored to `min_sustain_duty`.
# Disabled by default (0) — the right value is fan/voltage-specific and must
# be found empirically on the bench.

def test_low_nonzero_duty_is_floored_to_minimum_sustain_duty():
    transport = _StubTransport()
    fan = FanController(transport, speed_ceiling_kmh=200.0, min_sustain_duty=60, kick_start_duration_s=0.0)

    # 10 km/h of 200 km/h max == round(0.05 * 255) == 13, well under the floor.
    fan.on_frame(speed_kmh=10.0, paused=False, now=0.0)

    assert transport.sent == ["FAN:60\n"]


def test_duty_above_minimum_sustain_duty_is_not_altered():
    transport = _StubTransport()
    fan = FanController(transport, speed_ceiling_kmh=200.0, min_sustain_duty=60, kick_start_duration_s=0.0)

    # 50 km/h of 200 km/h max == round(0.25 * 255) == 64, already above the floor.
    fan.on_frame(speed_kmh=50.0, paused=False, now=0.0)

    assert transport.sent == ["FAN:64\n"]


def test_zero_duty_is_never_floored():
    transport = _StubTransport()
    fan = FanController(transport, speed_ceiling_kmh=200.0, min_sustain_duty=60, kick_start_duration_s=0.0)

    fan.on_frame(speed_kmh=0.0, paused=False, now=0.0)

    assert transport.sent == ["FAN:0\n"]


def test_paused_duty_is_never_floored_even_at_high_speed():
    transport = _StubTransport()
    fan = FanController(transport, speed_ceiling_kmh=200.0, min_sustain_duty=60, kick_start_duration_s=0.0)

    fan.on_frame(speed_kmh=200.0, paused=True, now=0.0)

    assert transport.sent == ["FAN:0\n"]


def test_min_sustain_duty_disabled_by_default():
    transport = _StubTransport()
    fan = FanController(transport, speed_ceiling_kmh=200.0, kick_start_duration_s=0.0)

    fan.on_frame(speed_kmh=10.0, paused=False, now=0.0)

    assert transport.sent == ["FAN:13\n"]


def test_kick_start_duty_still_wins_over_minimum_sustain_duty_during_kick():
    transport = _StubTransport()
    fan = FanController(
        transport, speed_ceiling_kmh=200.0, min_sustain_duty=60, kick_start_duty=255, kick_start_duration_s=0.2
    )

    # Kick-start (255) applies while starting, even though the floored
    # target duty (60) is lower than the kick value.
    fan.on_frame(speed_kmh=10.0, paused=False, now=0.0)

    assert transport.sent == ["FAN:255\n"]


# ── ~10 Hz cap under a busy input pattern ────────────────────────────────────

def test_no_more_than_ten_sends_per_second_under_rapidly_changing_input():
    transport = _StubTransport()
    fan = FanController(transport, speed_ceiling_kmh=200.0, send_interval_s=0.1)

    # 1000 frames spread over 1 simulated second (~1ms apart), each with a
    # different speed, so every call is a candidate for a send if unthrottled.
    for i in range(1000):
        now = i * 0.001
        speed = float(i % 200)
        fan.on_frame(speed_kmh=speed, paused=False, now=now)

    assert len(transport.sent) <= 11  # ~10 Hz over ~1s, with rounding tolerance


# ── shutdown() ───────────────────────────────────────────────────────────────

def test_shutdown_sends_fan_off():
    transport = _StubTransport()
    fan = FanController(transport, speed_ceiling_kmh=200.0)

    fan.shutdown()

    assert transport.sent == ["FAN:0\n"]


def test_shutdown_bypasses_throttle_window():
    transport = _StubTransport()
    fan = FanController(transport, speed_ceiling_kmh=200.0, send_interval_s=0.1)

    fan.on_frame(speed_kmh=200.0, paused=False, now=0.0)
    fan.shutdown()  # would normally be throttled if it were a regular on_frame() call

    assert transport.sent == ["FAN:255\n", "FAN:0\n"]


def test_shutdown_bypasses_dedup_when_duty_was_already_zero():
    transport = _StubTransport()
    fan = FanController(transport, speed_ceiling_kmh=200.0)

    fan.on_frame(speed_kmh=0.0, paused=False, now=0.0)
    fan.shutdown()  # duty is already 0 — a regular on_frame() call would be deduped

    assert transport.sent == ["FAN:0\n", "FAN:0\n"]


def test_shutdown_works_even_when_transport_not_connected():
    transport = _StubTransport(connected=False)
    fan = FanController(transport, speed_ceiling_kmh=200.0)

    fan.shutdown()  # must not raise; send_line() is a safe no-op on a real Transport

    assert transport.sent == ["FAN:0\n"]


def test_shutdown_resets_throttle_state_for_subsequent_on_frame_calls():
    transport = _StubTransport()
    fan = FanController(transport, speed_ceiling_kmh=200.0, send_interval_s=0.1)

    fan.on_frame(speed_kmh=200.0, paused=False, now=0.0)
    fan.shutdown()
    transport.sent.clear()

    # Immediately after shutdown(), at the same "time" — would be throttled/deduped
    # if shutdown() hadn't reset _last_sent_at/_last_duty.
    fan.on_frame(speed_kmh=200.0, paused=False, now=0.0)

    assert transport.sent == ["FAN:255\n"]
