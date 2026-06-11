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


async def _telemetry_loop(provider, queue: asyncio.Queue) -> None:
    async with provider.session():
        log.info("Telemetry stream started")
        async for data in provider.stream():
            try:
                queue.put_nowait(data)
            except asyncio.QueueFull:
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
                queue.put_nowait(data)


def _run_asyncio(provider, queue: asyncio.Queue) -> None:
    asyncio.run(_telemetry_loop(provider, queue))


def main() -> None:
    parser = argparse.ArgumentParser(description="Sim Racing Cockpit Dashboard")
    parser.add_argument("--ps5-ip", default=None,
                        help="IP of the telemetry device (overrides config file and env var)")
    parser.add_argument("--bind", default="0.0.0.0", help="Local IP to bind UDP socket")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Load config (file → env var); CLI arg takes highest priority
    config = AppConfig()
    if args.ps5_ip:
        config.device_ip = args.ps5_ip

    queue: asyncio.Queue = asyncio.Queue(maxsize=4)

    if config.device_ip:
        provider = GT7TelemetryProvider(ps5_ip=config.device_ip, bind_ip=args.bind)
        t = threading.Thread(target=_run_asyncio, args=(provider, queue), daemon=True)
        t.start()
        log.info("Connecting to device at %s", config.device_ip)
    else:
        log.warning("No device IP configured — open Settings (⚙) to set it")

    app = DashboardApp(telemetry_queue=queue, config=config)
    app.run()

    log.info("Dashboard closed")


if __name__ == "__main__":
    main()
