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
    _STRATEGY = "strategy"

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
        self.voice_alert_tyre_wear: bool = True
        self.voice_tyre_wear_threshold_pct: float = 0.10
        self.voice_alert_oil_temp: bool = True
        self.voice_alert_tire_pressure: bool = True
        self.voice_alert_lap_delta: bool = True
        self.voice_alert_pit_window: bool = True
        self.voice_engine_temp_threshold: float = 105.0
        self.voice_tire_temp_threshold: float = 100.0
        self.voice_tire_inner_temp_threshold: float = 110.0
        self.voice_oil_temp_threshold: float = 130.0
        self.voice_tire_pressure_low_kpa: float = 160.0
        self.voice_tire_pressure_high_kpa: float = 250.0
        self.voice_lap_delta_threshold_s: float = 3.0
        self.voice_pit_window_min_laps: float = 2.0
        self.voice_pit_window_max_laps: float = 4.0

        # Race strategy (auto)
        self.tyre_wear_limit_pct: float = 0.80
        self.pit_buffer_laps: int = 1
        self.voice_alert_strategy: bool = True
        self.voice_strategy_interval_s: float = 30.0

        # Race strategy (user-defined)
        self.planned_stops: int = 0
        self.planned_stop_laps: list[int] = []

        self.load()

    def load(self) -> None:
        if self.PATH.exists():
            cp = ConfigParser()
            cp.read(self.PATH)
            self._load_from_file(cp)
        if not self.device_ip:
            self.device_ip = os.environ.get(self.ENV_VAR, "")

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
            "alert_tyre_wear": str(self.voice_alert_tyre_wear),
            "tyre_wear_threshold_pct": str(self.voice_tyre_wear_threshold_pct),
            "alert_oil_temp": str(self.voice_alert_oil_temp),
            "alert_tire_pressure": str(self.voice_alert_tire_pressure),
            "alert_lap_delta": str(self.voice_alert_lap_delta),
            "alert_pit_window": str(self.voice_alert_pit_window),
            "engine_temp_threshold": str(self.voice_engine_temp_threshold),
            "tire_temp_threshold": str(self.voice_tire_temp_threshold),
            "tire_inner_temp_threshold": str(self.voice_tire_inner_temp_threshold),
            "oil_temp_threshold": str(self.voice_oil_temp_threshold),
            "tire_pressure_low_kpa": str(self.voice_tire_pressure_low_kpa),
            "tire_pressure_high_kpa": str(self.voice_tire_pressure_high_kpa),
            "lap_delta_threshold_s": str(self.voice_lap_delta_threshold_s),
            "pit_window_min_laps": str(self.voice_pit_window_min_laps),
            "pit_window_max_laps": str(self.voice_pit_window_max_laps),
        }
        cp[self._STRATEGY] = {
            "tyre_wear_limit_pct": str(self.tyre_wear_limit_pct),
            "pit_buffer_laps": str(self.pit_buffer_laps),
            "voice_alert_strategy": str(self.voice_alert_strategy),
            "voice_strategy_interval_s": str(self.voice_strategy_interval_s),
            "planned_stops": str(self.planned_stops),
            "planned_stop_laps": ",".join(str(x) for x in self.planned_stop_laps),
        }
        self.PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(self.PATH, "w") as fh:
            cp.write(fh)

    def _load_from_file(self, cp: ConfigParser) -> None:
        self.device_ip = cp.get(self._SECTION, "device_ip", fallback="")
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
        self.voice_alert_tyre_wear = cp.getboolean(self._VOICE, "alert_tyre_wear", fallback=True)
        self.voice_tyre_wear_threshold_pct = cp.getfloat(self._VOICE, "tyre_wear_threshold_pct", fallback=0.10)
        self.voice_alert_oil_temp = cp.getboolean(self._VOICE, "alert_oil_temp", fallback=True)
        self.voice_alert_tire_pressure = cp.getboolean(self._VOICE, "alert_tire_pressure", fallback=True)
        self.voice_alert_lap_delta = cp.getboolean(self._VOICE, "alert_lap_delta", fallback=True)
        self.voice_alert_pit_window = cp.getboolean(self._VOICE, "alert_pit_window", fallback=True)
        self.voice_engine_temp_threshold = cp.getfloat(self._VOICE, "engine_temp_threshold", fallback=105.0)
        self.voice_tire_temp_threshold = cp.getfloat(self._VOICE, "tire_temp_threshold", fallback=100.0)
        self.voice_tire_inner_temp_threshold = cp.getfloat(self._VOICE, "tire_inner_temp_threshold", fallback=110.0)
        self.voice_oil_temp_threshold = cp.getfloat(self._VOICE, "oil_temp_threshold", fallback=130.0)
        self.voice_tire_pressure_low_kpa = cp.getfloat(self._VOICE, "tire_pressure_low_kpa", fallback=160.0)
        self.voice_tire_pressure_high_kpa = cp.getfloat(self._VOICE, "tire_pressure_high_kpa", fallback=250.0)
        self.voice_lap_delta_threshold_s = cp.getfloat(self._VOICE, "lap_delta_threshold_s", fallback=3.0)
        self.voice_pit_window_min_laps = cp.getfloat(self._VOICE, "pit_window_min_laps", fallback=2.0)
        self.voice_pit_window_max_laps = cp.getfloat(self._VOICE, "pit_window_max_laps", fallback=4.0)
        self.tyre_wear_limit_pct = cp.getfloat(self._STRATEGY, "tyre_wear_limit_pct", fallback=0.80)
        self.pit_buffer_laps = cp.getint(self._STRATEGY, "pit_buffer_laps", fallback=1)
        self.voice_alert_strategy = cp.getboolean(self._STRATEGY, "voice_alert_strategy", fallback=True)
        self.voice_strategy_interval_s = cp.getfloat(self._STRATEGY, "voice_strategy_interval_s", fallback=30.0)
        self.planned_stops = cp.getint(self._STRATEGY, "planned_stops", fallback=0)
        raw_laps = cp.get(self._STRATEGY, "planned_stop_laps", fallback="")
        self.planned_stop_laps = [int(x) for x in raw_laps.split(",") if x.strip().isdigit()]
