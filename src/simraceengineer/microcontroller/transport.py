from abc import ABC, abstractmethod


class Transport(ABC):
    """Abstract byte-line transport to the airflow-simulation microcontroller.

    Deliberately excludes port discovery — that's serial-specific and doesn't
    generalize to a future Bluetooth/Wi-Fi transport. Concrete implementations
    (e.g. `SerialTransport`) own that concern instead.
    """

    @abstractmethod
    def connect(self) -> None:
        """Open the underlying connection."""

    @abstractmethod
    def disconnect(self) -> None:
        """Close the connection and release resources."""

    @abstractmethod
    def send_line(self, line: str) -> None:
        """Queue `line` for writing. Non-blocking."""

    @abstractmethod
    def read_line(self, timeout: float) -> str | None:
        """Return the next received line, or None if none arrived within `timeout`."""

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Whether the transport currently believes it is connected."""
