"""Serial-port `Transport` implementation for the airflow-simulation microcontroller.

`pyserial` is imported lazily inside the methods that need it (not at module
top-level) — the `microcontroller` extra is optional, and a missing install
must degrade to `is_connected = False` rather than crash the app, exactly
like `TTSService` handles a missing `piper-tts`.
"""

import logging
import queue
import threading
import time

from . import protocol
from .transport import Transport

log = logging.getLogger(__name__)

_BAUD_RATE = 9600
# Many Arduino-class boards auto-reset when the serial port is opened; writing
# immediately after connect() would be lost during bootloader/boot.
_POST_OPEN_DELAY_S = 2.0


def list_serial_ports() -> list[str]:
    """Return the device paths of all currently available serial ports."""
    try:
        from serial.tools import list_ports  # type: ignore[import]
    except ImportError:
        log.warning("pyserial not installed — cannot list serial ports. "
                    "Install with: pip install 'sim-race-engineer[microcontroller]'")
        return []
    return sorted(p.device for p in list_ports.comports())


class SerialTransport(Transport):
    def __init__(self, port: str, post_open_delay_s: float = _POST_OPEN_DELAY_S) -> None:
        self._port = port
        self._post_open_delay_s = post_open_delay_s
        self._serial = None
        self._write_q: queue.SimpleQueue[str | None] = queue.SimpleQueue()
        self._write_thread: threading.Thread | None = None
        self._is_connected = False

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    @property
    def port(self) -> str:
        return self._port

    @property
    def post_open_delay_s(self) -> float:
        return self._post_open_delay_s

    def connect(self) -> None:
        try:
            import serial  # type: ignore[import]
        except ImportError:
            log.warning("pyserial not installed — microcontroller support disabled. "
                        "Install with: pip install 'sim-race-engineer[microcontroller]'")
            self._is_connected = False
            return

        try:
            self._serial = serial.Serial(self._port, _BAUD_RATE, timeout=0.2)
        except Exception:
            log.exception("Failed to open serial port %r", self._port)
            self._serial = None
            self._is_connected = False
            return

        self._write_thread = threading.Thread(
            target=self._writer_loop, daemon=True, name="microcontroller-writer"
        )
        self._write_thread.start()

    def disconnect(self) -> None:
        self._write_q.put(None)
        if self._write_thread is not None:
            self._write_thread.join(timeout=self._post_open_delay_s + 1.0)
            self._write_thread = None
        if self._serial is not None:
            try:
                self._serial.close()
            except Exception:
                log.exception("Error closing serial port %r", self._port)
            self._serial = None
        self._is_connected = False

    def send_line(self, line: str) -> None:
        if self._serial is None:
            return
        self._write_q.put(line)

    def read_line(self, timeout: float) -> str | None:
        if self._serial is None:
            return None
        try:
            self._serial.timeout = timeout
            raw = self._serial.readline()
        except Exception:
            log.exception("Error reading from serial port %r", self._port)
            return None
        if not raw:
            return None
        return raw.decode("ascii", errors="ignore")

    def test_connection(self, timeout: float = 1.0) -> bool:
        """Send PING and look for PONG. Blocks for up to `timeout` seconds.

        Only ever called from a deliberate settings-panel button click — an
        acceptable, bounded exception to the "no blocking I/O on the main
        thread" rule elsewhere in this class.
        """
        if self._serial is None:
            return False
        try:
            self._serial.reset_input_buffer()
        except Exception:
            log.debug("reset_input_buffer not supported by this serial backend", exc_info=True)
        try:
            self._serial.write(f"{protocol.PING}\n".encode("ascii"))
        except Exception:
            log.exception("Error sending PING on port %r", self._port)
            return False

        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return False
            line = self.read_line(min(remaining, 0.2))
            if line and protocol.is_pong(line):
                return True

    def _writer_loop(self) -> None:
        time.sleep(self._post_open_delay_s)
        self._is_connected = True
        while True:
            item = self._write_q.get()
            if item is None:
                break
            serial_obj = self._serial
            if serial_obj is None:
                continue
            try:
                serial_obj.write(item.encode("ascii"))
            except Exception:
                log.exception("Error writing to serial port %r", self._port)
