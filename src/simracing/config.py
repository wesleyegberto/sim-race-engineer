"""App configuration: reads/writes ~/simracing.conf.

Priority for device_ip:
  1. ~/simracing.conf  [simracing] device_ip
  2. Environment variable SIMRACING_DEVICE_IP
  3. Empty string (triggers settings dialog on startup)
"""

import os
from configparser import ConfigParser
from pathlib import Path


class AppConfig:
    PATH = Path.home() / "simracing.conf"
    ENV_VAR = "SIMRACING_DEVICE_IP"
    _SECTION = "simracing"

    def __init__(self) -> None:
        self.device_ip: str = ""
        self.load()

    def load(self) -> None:
        ip = self._read_file()
        if not ip:
            ip = os.environ.get(self.ENV_VAR, "")
        self.device_ip = ip

    def save(self) -> None:
        cp = ConfigParser()
        cp[self._SECTION] = {"device_ip": self.device_ip}
        with open(self.PATH, "w") as fh:
            cp.write(fh)

    def _read_file(self) -> str:
        if not self.PATH.exists():
            return ""
        cp = ConfigParser()
        cp.read(self.PATH)
        return cp.get(self._SECTION, "device_ip", fallback="")
