"""Unit tests for `SerialTransport`, exercised against a fake serial object.

No real hardware or `loop://` URL is required — `serial.Serial` is monkeypatched
with `FakeSerial`, a minimal stand-in exposing the subset of pyserial's API
`SerialTransport` actually uses (`write`, `readline`, `reset_input_buffer`,
`close`, `timeout`).
"""

import sys
import time

import pytest

from simraceengineer.microcontroller.serial_transport import (
    SerialTransport,
    list_serial_ports,
)

# Keep the post-open-delay tiny in tests — the 2s production default would
# make the whole suite slow without adding coverage.
_FAST_DELAY_S = 0.01


class FakeSerial:
    """Minimal stand-in for `serial.Serial`."""

    def __init__(self, responses: list[bytes] | None = None) -> None:
        self.written: list[bytes] = []
        self.closed = False
        self.timeout: float | None = None
        self._responses = list(responses or [])

    def write(self, data: bytes) -> int:
        self.written.append(data)
        return len(data)

    def readline(self) -> bytes:
        if self._responses:
            return self._responses.pop(0)
        return b""

    def reset_input_buffer(self) -> None:
        pass

    def close(self) -> None:
        self.closed = True


@pytest.fixture
def fake_serial() -> FakeSerial:
    return FakeSerial()


def _patch_serial(monkeypatch: pytest.MonkeyPatch, fake: FakeSerial) -> None:
    monkeypatch.setattr("serial.Serial", lambda *a, **kw: fake)


def _wait_until(predicate, timeout: float = 1.0) -> bool:
    """Poll `predicate()` until it's truthy or `timeout` elapses."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.005)
    return predicate()


def _connect_and_wait(transport: SerialTransport) -> None:
    transport.connect()
    assert _wait_until(lambda: transport.is_connected), "transport never became connected"


# ── connect / disconnect lifecycle ──────────────────────────────────────────

def test_connect_opens_port_and_becomes_connected(monkeypatch, fake_serial):
    _patch_serial(monkeypatch, fake_serial)
    transport = SerialTransport("/dev/fake0", post_open_delay_s=_FAST_DELAY_S)

    assert transport.is_connected is False
    _connect_and_wait(transport)

    assert transport.is_connected is True
    transport.disconnect()


def test_connect_failure_leaves_disconnected(monkeypatch):
    def _boom(*a, **kw):
        raise OSError("port not found")

    monkeypatch.setattr("serial.Serial", _boom)
    transport = SerialTransport("/dev/does-not-exist", post_open_delay_s=_FAST_DELAY_S)

    transport.connect()

    assert transport.is_connected is False


def test_disconnect_closes_serial_and_resets_state(monkeypatch, fake_serial):
    _patch_serial(monkeypatch, fake_serial)
    transport = SerialTransport("/dev/fake0", post_open_delay_s=_FAST_DELAY_S)
    _connect_and_wait(transport)

    transport.disconnect()

    assert fake_serial.closed is True
    assert transport.is_connected is False


def test_disconnect_before_connect_is_a_noop():
    transport = SerialTransport("/dev/fake0")
    transport.disconnect()  # must not raise
    assert transport.is_connected is False


def test_missing_pyserial_disables_transport_permanently(monkeypatch):
    monkeypatch.setitem(sys.modules, "serial", None)
    transport = SerialTransport("/dev/fake0")

    transport.connect()

    assert transport.is_connected is False


# ── send_line / read_line ───────────────────────────────────────────────────

def test_send_line_writes_through_the_queue(monkeypatch, fake_serial):
    _patch_serial(monkeypatch, fake_serial)
    transport = SerialTransport("/dev/fake0", post_open_delay_s=_FAST_DELAY_S)
    _connect_and_wait(transport)

    transport.send_line("FAN:128\n")

    assert _wait_until(lambda: fake_serial.written)
    assert fake_serial.written == [b"FAN:128\n"]
    transport.disconnect()


def test_send_line_before_connect_is_ignored():
    transport = SerialTransport("/dev/fake0")
    transport.send_line("FAN:0\n")  # must not raise, no serial to write to


def test_read_line_returns_none_when_nothing_available(monkeypatch, fake_serial):
    _patch_serial(monkeypatch, fake_serial)
    transport = SerialTransport("/dev/fake0", post_open_delay_s=_FAST_DELAY_S)
    _connect_and_wait(transport)

    assert transport.read_line(timeout=0.05) is None
    transport.disconnect()


# ── test_connection ──────────────────────────────────────────────────────────

def test_test_connection_succeeds_on_pong(monkeypatch):
    fake = FakeSerial(responses=[b"PONG\n"])
    _patch_serial(monkeypatch, fake)
    transport = SerialTransport("/dev/fake0", post_open_delay_s=_FAST_DELAY_S)
    _connect_and_wait(transport)

    assert transport.test_connection(timeout=0.5) is True
    assert fake.written == [b"PING\n"]
    transport.disconnect()


def test_test_connection_times_out_without_pong(monkeypatch):
    fake = FakeSerial(responses=[])  # never replies
    _patch_serial(monkeypatch, fake)
    transport = SerialTransport("/dev/fake0", post_open_delay_s=_FAST_DELAY_S)
    _connect_and_wait(transport)

    assert transport.test_connection(timeout=0.1) is False
    transport.disconnect()


def test_test_connection_ignores_non_pong_replies(monkeypatch):
    fake = FakeSerial(responses=[b"GARBAGE\n", b"PONG\n"])
    _patch_serial(monkeypatch, fake)
    transport = SerialTransport("/dev/fake0", post_open_delay_s=_FAST_DELAY_S)
    _connect_and_wait(transport)

    assert transport.test_connection(timeout=0.5) is True
    transport.disconnect()


def test_test_connection_without_connect_returns_false():
    transport = SerialTransport("/dev/fake0")
    assert transport.test_connection(timeout=0.1) is False


# ── list_serial_ports ────────────────────────────────────────────────────────

def test_list_serial_ports_returns_sorted_devices(monkeypatch):
    class _Port:
        def __init__(self, device: str) -> None:
            self.device = device

    monkeypatch.setattr(
        "serial.tools.list_ports.comports",
        lambda: [_Port("/dev/tty.usbserial-B"), _Port("/dev/tty.usbserial-A")],
    )

    assert list_serial_ports() == ["/dev/tty.usbserial-A", "/dev/tty.usbserial-B"]


def test_list_serial_ports_missing_pyserial_returns_empty(monkeypatch):
    monkeypatch.setitem(sys.modules, "serial.tools.list_ports", None)
    monkeypatch.setitem(sys.modules, "serial.tools", None)

    assert list_serial_ports() == []
