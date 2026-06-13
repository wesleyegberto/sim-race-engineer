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
    PATH = Path.home() / "simracing" / "simracing.conf"
    ENV_VAR = "SIMRACING_DEVICE_IP"
    _SECTION = "simracing"

    _VOICE = "voice"

    def __init__(self) -> None:
        self.device_ip: str = ""
        self.rpm_flash: bool = True
        self.fuel_estimation: str = "average"  # "last" or "average"

        # Voice alerts
        self.voice_enabled: bool = False
        self.voice_language: str = "en"
        self.voice_en: str = "en_US-lessac-medium"
        self.voice_pt: str = "pt_BR-faber-medium"
        self.voice_volume: float = 0.8
        self.voice_min_interval_s: float = 15.0
        self.voice_fuel_critical_pct: float = 0.10
        self.voice_fuel_low_pct: float = 0.20

        self.load()

    def load(self) -> None:
        ip = self._read_file()
        if not ip:
            ip = os.environ.get(self.ENV_VAR, "")
        self.device_ip = ip

    def save(self) -> None:
        cp = ConfigParser()
        cp[self._SECTION] = {
            "device_ip": self.device_ip,
            "rpm_flash": str(self.rpm_flash),
            "fuel_estimation": self.fuel_estimation,
        }
        cp[self._VOICE] = {
            "enabled": str(self.voice_enabled),
            "language": self.voice_language,
            "voice_en": self.voice_en,
            "voice_pt": self.voice_pt,
            "volume": str(self.voice_volume),
            "min_interval_s": str(self.voice_min_interval_s),
            "fuel_critical_pct": str(self.voice_fuel_critical_pct),
            "fuel_low_pct": str(self.voice_fuel_low_pct),
        }
        self.PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(self.PATH, "w") as fh:
            cp.write(fh)

    def _read_file(self) -> str:
        if not self.PATH.exists():
            return ""
        cp = ConfigParser()
        cp.read(self.PATH)
        self.rpm_flash = cp.getboolean(self._SECTION, "rpm_flash", fallback=True)
        self.fuel_estimation = cp.get(self._SECTION, "fuel_estimation", fallback="average")
        self.voice_enabled = cp.getboolean(self._VOICE, "enabled", fallback=False)
        self.voice_language = cp.get(self._VOICE, "language", fallback="en")
        self.voice_en = cp.get(self._VOICE, "voice_en", fallback="en_US-lessac-medium")
        self.voice_pt = cp.get(self._VOICE, "voice_pt", fallback="pt_BR-faber-medium")
        self.voice_volume = cp.getfloat(self._VOICE, "volume", fallback=0.8)
        self.voice_min_interval_s = cp.getfloat(self._VOICE, "min_interval_s", fallback=15.0)
        self.voice_fuel_critical_pct = cp.getfloat(self._VOICE, "fuel_critical_pct", fallback=0.10)
        self.voice_fuel_low_pct = cp.getfloat(self._VOICE, "fuel_low_pct", fallback=0.20)
        return cp.get(self._SECTION, "device_ip", fallback="")
