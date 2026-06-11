"""Entry point: connects to GT7, runs the dashboard."""

import argparse
import asyncio
import logging
import threading

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
                # Drop oldest, put newest
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
                queue.put_nowait(data)


def _run_asyncio(provider, queue: asyncio.Queue) -> None:
    asyncio.run(_telemetry_loop(provider, queue))


def main() -> None:
    parser = argparse.ArgumentParser(description="Sim Racing Cockpit Dashboard")
    parser.add_argument("--ps5-ip", required=True, help="IP address of the PS5")
    parser.add_argument("--bind", default="0.0.0.0", help="Local IP to bind UDP socket")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    queue: asyncio.Queue = asyncio.Queue(maxsize=4)
    provider = GT7TelemetryProvider(ps5_ip=args.ps5_ip, bind_ip=args.bind)

    # Run telemetry receiver in a background thread (asyncio loop)
    t = threading.Thread(target=_run_asyncio, args=(provider, queue), daemon=True)
    t.start()

    # Run pygame dashboard on the main thread (required by pygame on macOS)
    app = DashboardApp(telemetry_queue=queue)
    app.run()

    log.info("Dashboard closed")


if __name__ == "__main__":
    main()
