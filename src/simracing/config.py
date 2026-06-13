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
        self.voice_alert_fuel_critical: bool = True
        self.voice_alert_fuel_low: bool = True
        self.voice_alert_lap_completed: bool = True
        self.voice_alert_best_lap: bool = True
        self.voice_alert_final_lap: bool = True
        self.voice_alert_engine_temp: bool = True
        self.voice_alert_tire_temp: bool = True
        self.voice_alert_tire_inner_temp: bool = True
        self.voice_engine_temp_threshold: float = 105.0
        self.voice_tire_temp_threshold: float = 100.0
        self.voice_tire_inner_temp_threshold: float = 110.0

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
            "alert_fuel_critical": str(self.voice_alert_fuel_critical),
            "alert_fuel_low": str(self.voice_alert_fuel_low),
            "alert_lap_completed": str(self.voice_alert_lap_completed),
            "alert_best_lap": str(self.voice_alert_best_lap),
            "alert_final_lap": str(self.voice_alert_final_lap),
            "alert_engine_temp": str(self.voice_alert_engine_temp),
            "alert_tire_temp": str(self.voice_alert_tire_temp),
            "alert_tire_inner_temp": str(self.voice_alert_tire_inner_temp),
            "engine_temp_threshold": str(self.voice_engine_temp_threshold),
            "tire_temp_threshold": str(self.voice_tire_temp_threshold),
            "tire_inner_temp_threshold": str(self.voice_tire_inner_temp_threshold),
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
        self.voice_alert_fuel_critical = cp.getboolean(self._VOICE, "alert_fuel_critical", fallback=True)
        self.voice_alert_fuel_low = cp.getboolean(self._VOICE, "alert_fuel_low", fallback=True)
        self.voice_alert_lap_completed = cp.getboolean(self._VOICE, "alert_lap_completed", fallback=True)
        self.voice_alert_best_lap = cp.getboolean(self._VOICE, "alert_best_lap", fallback=True)
        self.voice_alert_final_lap = cp.getboolean(self._VOICE, "alert_final_lap", fallback=True)
        self.voice_alert_engine_temp = cp.getboolean(self._VOICE, "alert_engine_temp", fallback=True)
        self.voice_alert_tire_temp = cp.getboolean(self._VOICE, "alert_tire_temp", fallback=True)
        self.voice_alert_tire_inner_temp = cp.getboolean(self._VOICE, "alert_tire_inner_temp", fallback=True)
        self.voice_engine_temp_threshold = cp.getfloat(self._VOICE, "engine_temp_threshold", fallback=105.0)
        self.voice_tire_temp_threshold = cp.getfloat(self._VOICE, "tire_temp_threshold", fallback=100.0)
        self.voice_tire_inner_temp_threshold = cp.getfloat(self._VOICE, "tire_inner_temp_threshold", fallback=110.0)
        return cp.get(self._SECTION, "device_ip", fallback="")
