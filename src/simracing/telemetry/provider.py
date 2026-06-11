from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Optional

from .models import TelemetryData


class TelemetryProvider(ABC):
    """Abstract base for all sim-racing telemetry sources.

    Subclasses implement connection logic and packet parsing for a specific
    game/simulator. The dashboard only depends on this interface.
    """

    @abstractmethod
    async def connect(self) -> None:
        """Open the underlying transport (UDP socket, named pipe, etc.)."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Close the transport and release resources."""

    @abstractmethod
    async def read(self) -> Optional[TelemetryData]:
        """Return the next telemetry snapshot, or None if no data yet."""

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[None, None]:
        await self.connect()
        try:
            yield
        finally:
            await self.disconnect()

    async def stream(self) -> AsyncGenerator[TelemetryData, None]:
        """Yield telemetry snapshots indefinitely while connected."""
        while True:
            data = await self.read()
            if data is not None:
                yield data
