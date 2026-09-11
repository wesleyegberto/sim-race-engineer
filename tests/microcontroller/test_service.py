"""Unit tests for `MicrocontrollerService`'s port auto-detect-or-manual algorithm.

The transport itself is stubbed out (`_StubTransport`) — these tests only care
about *which* port `MicrocontrollerService.start()` decides to connect to, per
the algorithm documented in the architecture doc:

  - explicit `config.microcontroller_port` -> always used as-is
  - empty config port + exactly one candidate -> auto-connect to it
  - empty config port + zero or multiple candidates -> do not auto-connect
"""

from simraceengineer.config import AppConfig
from simraceengineer.microcontroller import MicrocontrollerService


class _StubTransport:
    """Records the port it was constructed with instead of touching real serial I/O.

    Also records every line handed to `send_line()` — used by the `stop()`
    tests below, since `MicrocontrollerService` wraps this stub in a real
    (non-stubbed) `FanController`, whose `shutdown()` writes through it.
    """

    instances: list["_StubTransport"] = []

    def __init__(self, port: str, post_open_delay_s: float = 2.0) -> None:
        self.port = port
        self.connected = False
        self.sent: list[str] = []
        _StubTransport.instances.append(self)

    def connect(self) -> None:
        self.connected = True

    def disconnect(self) -> None:
        self.connected = False

    def send_line(self, line: str) -> None:
        self.sent.append(line)

    @property
    def is_connected(self) -> bool:
        return self.connected


def _make_config(port: str = "") -> AppConfig:
    config = AppConfig.__new__(AppConfig)
    config.microcontroller_enabled = True
    config.microcontroller_port = port
    return config


def test_start_uses_explicit_port_without_consulting_candidates(monkeypatch):
    _StubTransport.instances.clear()
    monkeypatch.setattr(
        "simraceengineer.microcontroller.list_serial_ports",
        lambda: (_ for _ in ()).throw(AssertionError("should not be called")),
    )
    monkeypatch.setattr("simraceengineer.microcontroller.SerialTransport", _StubTransport)

    service = MicrocontrollerService(_make_config(port="/dev/explicit"))
    service.start()

    assert len(_StubTransport.instances) == 1
    assert _StubTransport.instances[0].port == "/dev/explicit"
    assert service.is_connected is True


def test_start_auto_connects_when_exactly_one_candidate(monkeypatch):
    _StubTransport.instances.clear()
    monkeypatch.setattr(
        "simraceengineer.microcontroller.list_serial_ports", lambda: ["/dev/only-one"]
    )
    monkeypatch.setattr("simraceengineer.microcontroller.SerialTransport", _StubTransport)

    service = MicrocontrollerService(_make_config(port=""))
    service.start()

    assert len(_StubTransport.instances) == 1
    assert _StubTransport.instances[0].port == "/dev/only-one"
    assert service.is_connected is True


def test_start_does_not_autoconnect_with_zero_candidates(monkeypatch):
    _StubTransport.instances.clear()
    monkeypatch.setattr("simraceengineer.microcontroller.list_serial_ports", lambda: [])
    monkeypatch.setattr("simraceengineer.microcontroller.SerialTransport", _StubTransport)

    service = MicrocontrollerService(_make_config(port=""))
    service.start()

    assert _StubTransport.instances == []
    assert service.is_connected is False


def test_start_does_not_autoconnect_with_multiple_candidates(monkeypatch):
    _StubTransport.instances.clear()
    monkeypatch.setattr(
        "simraceengineer.microcontroller.list_serial_ports",
        lambda: ["/dev/a", "/dev/b"],
    )
    monkeypatch.setattr("simraceengineer.microcontroller.SerialTransport", _StubTransport)

    service = MicrocontrollerService(_make_config(port=""))
    service.start()

    assert _StubTransport.instances == []
    assert service.is_connected is False


def test_stop_disconnects_transport(monkeypatch):
    _StubTransport.instances.clear()
    monkeypatch.setattr(
        "simraceengineer.microcontroller.list_serial_ports", lambda: ["/dev/only-one"]
    )
    monkeypatch.setattr("simraceengineer.microcontroller.SerialTransport", _StubTransport)

    service = MicrocontrollerService(_make_config(port=""))
    service.start()
    service.stop()

    assert service.is_connected is False
    assert _StubTransport.instances[0].connected is False


# ── Story 3: safe shutdown ───────────────────────────────────────────────────

def test_stop_sends_fan_off_before_disconnecting(monkeypatch):
    _StubTransport.instances.clear()
    monkeypatch.setattr(
        "simraceengineer.microcontroller.list_serial_ports", lambda: ["/dev/only-one"]
    )
    monkeypatch.setattr("simraceengineer.microcontroller.SerialTransport", _StubTransport)

    service = MicrocontrollerService(_make_config(port=""))
    service.start()
    service.stop()

    assert _StubTransport.instances[0].sent == ["FAN:0\n"]


def test_stop_called_twice_sends_fan_off_exactly_once_and_does_not_raise(monkeypatch):
    _StubTransport.instances.clear()
    monkeypatch.setattr(
        "simraceengineer.microcontroller.list_serial_ports", lambda: ["/dev/only-one"]
    )
    monkeypatch.setattr("simraceengineer.microcontroller.SerialTransport", _StubTransport)

    service = MicrocontrollerService(_make_config(port=""))
    service.start()
    transport = _StubTransport.instances[0]

    service.stop()
    service.stop()  # already disconnected — must not raise or resend

    assert transport.sent == ["FAN:0\n"]


def test_stop_without_start_does_not_raise():
    service = MicrocontrollerService(_make_config(port=""))

    service.stop()  # start() was never called — _fan/_transport are None

    assert service.is_connected is False


def test_stop_after_start_found_no_port_does_not_raise(monkeypatch):
    monkeypatch.setattr("simraceengineer.microcontroller.list_serial_ports", lambda: [])

    service = MicrocontrollerService(_make_config(port=""))
    service.start()  # zero candidates — never connects, _fan/_transport stay None

    service.stop()  # must not raise

    assert service.is_connected is False
