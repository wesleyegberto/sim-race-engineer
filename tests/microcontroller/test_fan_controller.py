"""Unit tests for `FanController`'s speed->duty mapping, throttle, and dedup logic.

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

def test_speed_zero_sends_duty_zero():
    transport = _StubTransport()
    fan = FanController(transport)

    fan.on_frame(speed_kmh=0.0, speed_max_kmh=200.0, paused=False, now=0.0)

    assert transport.sent == ["FAN:0\n"]


def test_speed_equal_to_max_sends_full_duty():
    transport = _StubTransport()
    fan = FanController(transport)

    fan.on_frame(speed_kmh=200.0, speed_max_kmh=200.0, paused=False, now=0.0)

    assert transport.sent == ["FAN:255\n"]


def test_speed_above_max_is_clamped_to_full_duty():
    transport = _StubTransport()
    fan = FanController(transport)

    fan.on_frame(speed_kmh=300.0, speed_max_kmh=200.0, paused=False, now=0.0)

    assert transport.sent == ["FAN:255\n"]


def test_speed_max_kmh_zero_falls_back_to_default():
    transport = _StubTransport()
    fan = FanController(transport, max_speed_fallback_kmh=250.0)

    # 125 km/h against a 250 km/h fallback == 50% duty == round(0.5 * 255) == 128
    fan.on_frame(speed_kmh=125.0, speed_max_kmh=0.0, paused=False, now=0.0)

    assert transport.sent == ["FAN:128\n"]


def test_speed_max_kmh_zero_never_raises_zero_division_error():
    transport = _StubTransport()
    fan = FanController(transport, max_speed_fallback_kmh=250.0)

    fan.on_frame(speed_kmh=100.0, speed_max_kmh=0.0, paused=False, now=0.0)  # should not raise

    assert transport.sent  # a real command was computed and sent, not skipped


def test_intermediate_speed_scales_linearly():
    transport = _StubTransport()
    fan = FanController(transport)

    # 50 km/h of 200 km/h max == 25% duty == round(0.25 * 255) == 64
    fan.on_frame(speed_kmh=50.0, speed_max_kmh=200.0, paused=False, now=0.0)

    assert transport.sent == ["FAN:64\n"]


# ── paused handling ──────────────────────────────────────────────────────────

def test_paused_forces_duty_zero_regardless_of_speed():
    transport = _StubTransport()
    fan = FanController(transport)

    fan.on_frame(speed_kmh=250.0, speed_max_kmh=200.0, paused=True, now=0.0)

    assert transport.sent == ["FAN:0\n"]


def test_paused_after_high_speed_sends_zero_once_interval_elapses():
    transport = _StubTransport(connected=True)
    fan = FanController(transport, send_interval_s=0.1)

    fan.on_frame(speed_kmh=200.0, speed_max_kmh=200.0, paused=False, now=0.0)
    fan.on_frame(speed_kmh=200.0, speed_max_kmh=200.0, paused=True, now=0.2)

    assert transport.sent == ["FAN:255\n", "FAN:0\n"]


# ── disconnected transport ───────────────────────────────────────────────────

def test_does_nothing_when_transport_not_connected():
    transport = _StubTransport(connected=False)
    fan = FanController(transport)

    fan.on_frame(speed_kmh=200.0, speed_max_kmh=200.0, paused=False, now=0.0)

    assert transport.sent == []


# ── throttle window ──────────────────────────────────────────────────────────

def test_throttle_skips_second_send_before_interval_elapses():
    transport = _StubTransport()
    fan = FanController(transport, send_interval_s=0.1)

    fan.on_frame(speed_kmh=50.0, speed_max_kmh=200.0, paused=False, now=0.0)
    fan.on_frame(speed_kmh=100.0, speed_max_kmh=200.0, paused=False, now=0.05)

    assert transport.sent == ["FAN:64\n"]


def test_throttle_allows_send_once_interval_elapses():
    transport = _StubTransport()
    fan = FanController(transport, send_interval_s=0.1)

    fan.on_frame(speed_kmh=50.0, speed_max_kmh=200.0, paused=False, now=0.0)
    fan.on_frame(speed_kmh=100.0, speed_max_kmh=200.0, paused=False, now=0.1)

    assert transport.sent == ["FAN:64\n", "FAN:128\n"]


def test_skipped_send_does_not_reset_throttle_clock():
    transport = _StubTransport()
    fan = FanController(transport, send_interval_s=0.1)

    fan.on_frame(speed_kmh=50.0, speed_max_kmh=200.0, paused=False, now=0.0)
    # Skipped: interval hasn't elapsed since the last real send.
    fan.on_frame(speed_kmh=100.0, speed_max_kmh=200.0, paused=False, now=0.05)
    # Still measured from the last real send (t=0.0), not the skipped call
    # (t=0.05) — so this must go through at t=0.1, not be skipped again.
    fan.on_frame(speed_kmh=100.0, speed_max_kmh=200.0, paused=False, now=0.1)

    assert transport.sent == ["FAN:64\n", "FAN:128\n"]


# ── dedup on unchanged duty ──────────────────────────────────────────────────

def test_dedup_skips_resend_when_duty_unchanged_after_interval_elapses():
    transport = _StubTransport()
    fan = FanController(transport, send_interval_s=0.1)

    fan.on_frame(speed_kmh=100.0, speed_max_kmh=200.0, paused=False, now=0.0)
    fan.on_frame(speed_kmh=100.0, speed_max_kmh=200.0, paused=False, now=0.2)
    fan.on_frame(speed_kmh=100.0, speed_max_kmh=200.0, paused=False, now=0.4)

    assert transport.sent == ["FAN:128\n"]


def test_dedup_does_not_apply_across_different_duty_values():
    transport = _StubTransport()
    fan = FanController(transport, send_interval_s=0.1)

    fan.on_frame(speed_kmh=50.0, speed_max_kmh=200.0, paused=False, now=0.0)
    fan.on_frame(speed_kmh=100.0, speed_max_kmh=200.0, paused=False, now=0.2)

    assert transport.sent == ["FAN:64\n", "FAN:128\n"]


# ── ~10 Hz cap under a busy input pattern ────────────────────────────────────

def test_no_more_than_ten_sends_per_second_under_rapidly_changing_input():
    transport = _StubTransport()
    fan = FanController(transport, send_interval_s=0.1)

    # 1000 frames spread over 1 simulated second (~1ms apart), each with a
    # different speed, so every call is a candidate for a send if unthrottled.
    for i in range(1000):
        now = i * 0.001
        speed = float(i % 200)
        fan.on_frame(speed_kmh=speed, speed_max_kmh=200.0, paused=False, now=now)

    assert len(transport.sent) <= 11  # ~10 Hz over ~1s, with rounding tolerance


# ── shutdown() ───────────────────────────────────────────────────────────────

def test_shutdown_sends_fan_off():
    transport = _StubTransport()
    fan = FanController(transport)

    fan.shutdown()

    assert transport.sent == ["FAN:0\n"]


def test_shutdown_bypasses_throttle_window():
    transport = _StubTransport()
    fan = FanController(transport, send_interval_s=0.1)

    fan.on_frame(speed_kmh=200.0, speed_max_kmh=200.0, paused=False, now=0.0)
    fan.shutdown()  # would normally be throttled if it were a regular on_frame() call

    assert transport.sent == ["FAN:255\n", "FAN:0\n"]


def test_shutdown_bypasses_dedup_when_duty_was_already_zero():
    transport = _StubTransport()
    fan = FanController(transport)

    fan.on_frame(speed_kmh=0.0, speed_max_kmh=200.0, paused=False, now=0.0)
    fan.shutdown()  # duty is already 0 — a regular on_frame() call would be deduped

    assert transport.sent == ["FAN:0\n", "FAN:0\n"]


def test_shutdown_works_even_when_transport_not_connected():
    transport = _StubTransport(connected=False)
    fan = FanController(transport)

    fan.shutdown()  # must not raise; send_line() is a safe no-op on a real Transport

    assert transport.sent == ["FAN:0\n"]


def test_shutdown_resets_throttle_state_for_subsequent_on_frame_calls():
    transport = _StubTransport()
    fan = FanController(transport, send_interval_s=0.1)

    fan.on_frame(speed_kmh=200.0, speed_max_kmh=200.0, paused=False, now=0.0)
    fan.shutdown()
    transport.sent.clear()

    # Immediately after shutdown(), at the same "time" — would be throttled/deduped
    # if shutdown() hadn't reset _last_sent_at/_last_duty.
    fan.on_frame(speed_kmh=200.0, speed_max_kmh=200.0, paused=False, now=0.0)

    assert transport.sent == ["FAN:255\n"]
