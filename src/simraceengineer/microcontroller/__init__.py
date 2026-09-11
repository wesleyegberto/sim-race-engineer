"""Serial-connected microcontroller integration (airflow fan simulation).

`MicrocontrollerService` is the orchestrator wired into `main.py` /
`dashboard/app.py`, mirroring `voice.VoiceService`'s shape: constructed once,
`start()`/`stop()` bracket `app.run()`, and `on_frame()` (added in a later
story, together with `FanController`) is called unconditionally every frame.
"""

import logging
import time

from ..config import AppConfig
from ..telemetry.models import TelemetryData
from .fan_controller import FanController
from .serial_transport import SerialTransport, list_serial_ports

log = logging.getLogger(__name__)

__all__ = ["MicrocontrollerService", "list_serial_ports"]


class MicrocontrollerService:
    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._transport: SerialTransport | None = None
        self._fan: FanController | None = None

    def start(self) -> None:
        port = self._config.microcontroller_port
        if not port:
            candidates = list_serial_ports()
            if len(candidates) == 1:
                port = candidates[0]
                log.info("Auto-detected microcontroller port: %s", port)
            else:
                log.warning(
                    "Microcontroller port not configured and %d candidate(s) found — "
                    "enter the port manually in Settings", len(candidates),
                )
                return

        self._transport = SerialTransport(port)
        self._fan = FanController(self._transport)
        self._transport.connect()

    def stop(self) -> None:
        """Shut down fans, then tear down the transport, in that deterministic order.

        Safe to call when `start()` was never called or found no port (both
        `_fan`/`_transport` are `None`), and safe to call twice — `disconnect()`
        is idempotent and `shutdown()` only ever writes through `send_line()`,
        which itself no-ops on a disconnected/absent serial connection.
        """
        if self._fan is not None:
            self._fan.shutdown()
        if self._transport is not None:
            self._transport.disconnect()
            self._transport = None
        self._fan = None

    def on_frame(self, data: TelemetryData) -> None:
        if self._fan is None:
            return
        self._fan.on_frame(data.speed_kmh, data.speed_max_kmh, data.paused, time.monotonic())

    def test_connection(self, port: str | None = None, timeout: float = 1.0) -> bool:
        """Test connectivity on `port` (falls back to the configured/connected port).

        Reuses the already-connected transport when it matches the requested
        port; otherwise opens a short-lived probe connection, waits out the
        post-open delay (board auto-reset), tests, and tears it down again.
        """
        target_port = port or self._config.microcontroller_port

        if self._transport is not None and target_port in ("", None, self._transport.port):
            return self._transport.test_connection(timeout=timeout)

        if not target_port:
            candidates = list_serial_ports()
            if len(candidates) != 1:
                return False
            target_port = candidates[0]

        probe = SerialTransport(target_port)
        probe.connect()
        try:
            deadline = time.monotonic() + probe.post_open_delay_s + timeout
            while not probe.is_connected and time.monotonic() < deadline:
                time.sleep(0.05)
            if not probe.is_connected:
                return False
            return probe.test_connection(timeout=timeout)
        finally:
            probe.disconnect()

    @property
    def is_connected(self) -> bool:
        return self._transport.is_connected if self._transport is not None else False
