"""GT7 UDP telemetry receiver.

GT7 only streams data while an active heartbeat is received.
Send the ASCII byte 'A' to <ps5_ip>:33739 every ~100 ms to keep the stream alive.
GT7 broadcasts on port 33740.
"""

import asyncio
import logging
import socket
from typing import Optional

from ..models import TelemetryData
from ..provider import TelemetryProvider
from .parser import parse

log = logging.getLogger(__name__)

_RECV_PORT = 33740
_SEND_PORT = 33739
_HEARTBEAT_INTERVAL = 0.1   # seconds
_RECV_TIMEOUT = 0.02         # non-blocking read window


class GT7TelemetryProvider(TelemetryProvider):
    """Connects to a PS5 running GT7 and decodes telemetry packets."""

    def __init__(self, ps5_ip: str, bind_ip: str = "0.0.0.0") -> None:
        self.ps5_ip = ps5_ip
        self.bind_ip = bind_ip
        self._sock: Optional[socket.socket] = None
        self._heartbeat_task: Optional[asyncio.Task] = None

    async def connect(self) -> None:
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((self.bind_ip, _RECV_PORT))
        self._sock.setblocking(False)
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        log.info("GT7 receiver bound to %s:%d, sending heartbeats to %s:%d",
                 self.bind_ip, _RECV_PORT, self.ps5_ip, _SEND_PORT)

    async def disconnect(self) -> None:
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        if self._sock:
            self._sock.close()
            self._sock = None
        log.info("GT7 receiver disconnected")

    async def read(self) -> Optional[TelemetryData]:
        if self._sock is None:
            return None
        loop = asyncio.get_running_loop()
        try:
            raw = await asyncio.wait_for(
                loop.sock_recv(self._sock, 4096),
                timeout=_RECV_TIMEOUT,
            )
            log.debug("UDP recv %d bytes — first8=%s", len(raw), raw[:8].hex())
            result = parse(raw)
            if result is None:
                log.warning("parse() returned None for %d-byte packet — magic mismatch or bad decrypt", len(raw))
            else:
                log.debug("Parsed OK — pkt_id=%d  spd=%.0f km/h  rpm=%.0f  gear=%s",
                          result.packet_id, result.speed_kmh, result.rpm, result.gear_label)
            return result
        except TimeoutError:
            return None
        except OSError as exc:
            log.warning("Socket error: %s", exc)
            return None

    async def _heartbeat_loop(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            while True:
                try:
                    sock.sendto(b"A", (self.ps5_ip, _SEND_PORT))
                except OSError as exc:
                    log.debug("Heartbeat send failed: %s", exc)
                await asyncio.sleep(_HEARTBEAT_INTERVAL)
        finally:
            sock.close()
