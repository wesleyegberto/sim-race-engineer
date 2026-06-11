"""Entry point: loads config, connects to telemetry device, runs the dashboard."""

import argparse
import asyncio
import logging
import threading

from .config import AppConfig
from .dashboard.app import DashboardApp
from .telemetry.gt7 import GT7TelemetryProvider

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)
log = logging.getLogger(__name__)

# Connection status literals
STATUS_DISCONNECTED = "disconnected"
STATUS_CONNECTING   = "connecting"
STATUS_CONNECTED    = "connected"
STATUS_ERROR        = "error"


class TelemetryController:
    """Manages the telemetry background thread with start/stop control."""

    def __init__(self, config: AppConfig, bind_ip: str, queue: asyncio.Queue) -> None:
        self._config = config
        self._bind_ip = bind_ip
        self._queue = queue
        self._thread: threading.Thread | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._task: asyncio.Task | None = None
        self.status: str = STATUS_DISCONNECTED
        self.error_msg: str = ""

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        if not self._config.device_ip:
            log.warning("No device IP configured — open Settings (⚙) to set it")
            return
        self.status = STATUS_CONNECTING
        self.error_msg = ""
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        log.info("Connecting to device at %s", self._config.device_ip)

    def stop(self) -> None:
        loop, task = self._loop, self._task
        if loop and task and not loop.is_closed():
            loop.call_soon_threadsafe(task.cancel)
        self.status = STATUS_DISCONNECTED
        self.error_msg = ""
        log.info("Telemetry disconnected")

    def _run(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        provider = GT7TelemetryProvider(
            ps5_ip=self._config.device_ip, bind_ip=self._bind_ip
        )

        async def _main() -> None:
            self._task = asyncio.current_task()
            try:
                async with provider.session():
                    self.status = STATUS_CONNECTED
                    log.info("Telemetry stream started")
                    pkt_count = 0
                    async for data in provider.stream():
                        pkt_count += 1
                        if pkt_count == 1:
                            log.info(
                                "First packet received — pkt_id=%d  car_code=%s",
                                data.packet_id, getattr(data, "car_code", "?"),
                            )
                        elif pkt_count % 300 == 0:
                            log.debug(
                                "pkt=%d  %.0f km/h  %.0f RPM  gear=%s"
                                "  lap=%d/%d  fuel=%.1fL  oil=%.0f°C  H2O=%.0f°C",
                                data.packet_id, data.speed_kmh, data.rpm,
                                data.gear_label, data.current_lap, data.total_laps,
                                data.fuel_level, data.oil_temp, data.water_temp,
                            )
                        try:
                            self._queue.put_nowait(data)
                        except asyncio.QueueFull:
                            try:
                                self._queue.get_nowait()
                            except asyncio.QueueEmpty:
                                pass
                            self._queue.put_nowait(data)
            except asyncio.CancelledError:
                raise
            except OSError as exc:
                self.status = STATUS_ERROR
                self.error_msg = exc.strerror or str(exc)
                log.error("Telemetry connection error: %s", exc)
            except Exception as exc:
                self.status = STATUS_ERROR
                self.error_msg = str(exc)
                log.error("Telemetry error: %s", exc)

        try:
            self._loop.run_until_complete(_main())
        except asyncio.CancelledError:
            pass
        except Exception:
            pass
        finally:
            self._loop.close()
            if self.status not in (STATUS_ERROR, STATUS_DISCONNECTED):
                self.status = STATUS_DISCONNECTED


def main() -> None:
    parser = argparse.ArgumentParser(description="Sim Racing Cockpit Dashboard")
    parser.add_argument("--ps5-ip", default=None,
                        help="IP of the telemetry device (overrides config file and env var)")
    parser.add_argument("--bind", default="0.0.0.0", help="Local IP to bind UDP socket")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    config = AppConfig()
    if args.ps5_ip:
        config.device_ip = args.ps5_ip

    queue: asyncio.Queue = asyncio.Queue(maxsize=4)
    controller = TelemetryController(config=config, bind_ip=args.bind, queue=queue)

    if config.device_ip:
        controller.start()

    app = DashboardApp(
        telemetry_queue=queue,
        config=config,
        connect_fn=controller.start,
        disconnect_fn=controller.stop,
        get_status_fn=lambda: controller.status,
        get_error_fn=lambda: controller.error_msg,
    )
    app.run()

    log.info("Dashboard closed")


if __name__ == "__main__":
    main()
