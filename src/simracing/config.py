"""App configuration: reads/writes ~/simracing.conf.

Priority for device_ip:
  1. ~/simracing.conf  [simracing] device_ip
  2. Environment variable SIMRACING_DEVICE_IP
  3. Empty string (triggers settings dialog on startup)
"""

import logging
import os
from configparser import ConfigParser
from pathlib import Path

log = logging.getLogger(__name__)


def _parse_stop_windows(raw: str) -> list[tuple[int, int]]:
    """Parse comma-separated stop entries into (open, close) tuples.

    Accepts both "25" (single lap → 25-25) and "23-27" (window).
    """
    windows: list[tuple[int, int]] = []
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        if "-" in token:
            parts = token.split("-", 1)
            try:
                o, c = int(parts[0]), int(parts[1])
                windows.append((o, max(o, c)))
            except ValueError:
                pass
        elif token.isdigit():
            n = int(token)
            windows.append((n, n))
    return windows


class AppConfig:
    PATH = Path.home() / "simracing" / "simracing.conf"
    ENV_VAR = "SIMRACING_DEVICE_IP"
    _SECTION = "simracing"

    _VOICE = "voice"
    _STRATEGY = "strategy"
    _LLM = "llm"

    def __init__(self) -> None:
        self.device_ip: str = ""
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
        self.voice_alert_race_report: bool = True
        self.voice_alert_engine_temp: bool = True
        self.voice_alert_tire_temp: bool = True
        self.voice_alert_tire_inner_temp: bool = True
        self.voice_alert_tyre_wear: bool = True
        self.voice_tyre_wear_threshold_pct: float = 0.10
        self.voice_alert_oil_temp: bool = True
        self.voice_alert_tire_pressure: bool = True
        self.voice_alert_lap_delta: bool = True
        self.voice_alert_pit_window: bool = True
        self.voice_alert_overtake: bool = True
        self.voice_alert_laps_to_finish: bool = True
        self.voice_alert_fuel_save: bool = True
        self.voice_alert_strategy_check_in: bool = True
        self.voice_alert_strategy_revised: bool = True
        self.voice_alert_fuel_save_recommend: bool = True
        self.voice_alert_advisor_pit_window: bool = True
        self.voice_engine_temp_threshold: float = 105.0
        self.voice_tire_temp_threshold: float = 100.0
        self.voice_tire_inner_temp_threshold: float = 110.0
        self.voice_oil_temp_threshold: float = 130.0
        self.voice_tire_pressure_low_kpa: float = 160.0
        self.voice_tire_pressure_high_kpa: float = 250.0
        self.voice_lap_delta_threshold_s: float = 3.0
        self.voice_pit_window_min_laps: float = 2.0
        self.voice_pit_window_max_laps: float = 4.0

        # Tyre wear estimation
        self.tire_wear_range_m: float = 0.003   # usable rubber depth in metres (GT7: radius shrinks ~1-3 mm per stint)

        # Race strategy (auto)
        self.tyre_wear_limit_pct: float = 0.80
        self.pit_buffer_laps: int = 1
        self.voice_alert_strategy: bool = True
        self.voice_strategy_interval_s: float = 30.0

        # Strategy advisor
        self.pit_loss_time_s: float = 25.0
        self.strategy_check_in_interval_laps: int = 3
        self.fuel_save_delta_l: float = 2.0
        self.lap_time_buffer: int = 3

        # Race strategy (user-defined)
        self.planned_stops: int = 0
        # Each window is (open_lap, close_lap); if open==close it's a single-lap stop.
        self.planned_stop_windows: list[tuple[int, int]] = []

        # LLM
        self.llm_backend: str = "openai"
        self.llm_model: str = "gemma4:12b"
        self.llm_api_key: str = ""
        self.llm_base_url: str = "http://localhost:1234/v1"

        # Recording
        self.recording_on_start: bool = True
        self.recording_suffix: str = ""

        self.load()

    def load(self) -> None:
        if self.PATH.exists():
            cp = ConfigParser()
            cp.read(self.PATH)
            try:
                self._load_from_file(cp)
            except Exception:
                log.warning("Config corrupted, using defaults: %s", self.PATH)
        if not self.device_ip:
            self.device_ip = os.environ.get(self.ENV_VAR, "")

    def save(self) -> None:
        cp = ConfigParser()
        cp[self._SECTION] = {
            "device_ip": self.device_ip,
            "fuel_estimation": self.fuel_estimation,
            "recording_on_start": str(self.recording_on_start),
            "recording_suffix": self.recording_suffix,
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
            "alert_race_report": str(self.voice_alert_race_report),
            "alert_engine_temp": str(self.voice_alert_engine_temp),
            "alert_tire_temp": str(self.voice_alert_tire_temp),
            "alert_tire_inner_temp": str(self.voice_alert_tire_inner_temp),
            "alert_tyre_wear": str(self.voice_alert_tyre_wear),
            "tyre_wear_threshold_pct": str(self.voice_tyre_wear_threshold_pct),
            "alert_oil_temp": str(self.voice_alert_oil_temp),
            "alert_tire_pressure": str(self.voice_alert_tire_pressure),
            "alert_lap_delta": str(self.voice_alert_lap_delta),
            "alert_pit_window": str(self.voice_alert_pit_window),
            "alert_overtake": str(self.voice_alert_overtake),
            "alert_laps_to_finish": str(self.voice_alert_laps_to_finish),
            "alert_fuel_save": str(self.voice_alert_fuel_save),
            "alert_strategy_check_in": str(self.voice_alert_strategy_check_in),
            "alert_strategy_revised": str(self.voice_alert_strategy_revised),
            "alert_fuel_save_recommend": str(self.voice_alert_fuel_save_recommend),
            "alert_advisor_pit_window": str(self.voice_alert_advisor_pit_window),
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
            "tire_wear_range_m": str(self.tire_wear_range_m),
            "tyre_wear_limit_pct": str(self.tyre_wear_limit_pct),
            "pit_buffer_laps": str(self.pit_buffer_laps),
            "voice_alert_strategy": str(self.voice_alert_strategy),
            "voice_strategy_interval_s": str(self.voice_strategy_interval_s),
            "planned_stops": str(self.planned_stops),
            "planned_stop_laps": ",".join(
                f"{o}-{c}" if o != c else str(o)
                for o, c in self.planned_stop_windows
            ),
            "pit_loss_time_s": str(self.pit_loss_time_s),
            "strategy_check_in_interval_laps": str(self.strategy_check_in_interval_laps),
            "fuel_save_delta_l": str(self.fuel_save_delta_l),
            "lap_time_buffer": str(self.lap_time_buffer),
        }
        cp[self._LLM] = {
            "backend": self.llm_backend,
            "model": self.llm_model,
            "api_key": self.llm_api_key,
            "base_url": self.llm_base_url,
        }
        self.PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(self.PATH, "w") as fh:
            cp.write(fh)

    def _load_from_file(self, cp: ConfigParser) -> None:
        self.device_ip = cp.get(self._SECTION, "device_ip", fallback="")
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
        self.voice_alert_race_report = cp.getboolean(self._VOICE, "alert_race_report", fallback=True)
        self.voice_alert_engine_temp = cp.getboolean(self._VOICE, "alert_engine_temp", fallback=True)
        self.voice_alert_tire_temp = cp.getboolean(self._VOICE, "alert_tire_temp", fallback=True)
        self.voice_alert_tire_inner_temp = cp.getboolean(self._VOICE, "alert_tire_inner_temp", fallback=True)
        self.voice_alert_tyre_wear = cp.getboolean(self._VOICE, "alert_tyre_wear", fallback=True)
        self.voice_tyre_wear_threshold_pct = cp.getfloat(self._VOICE, "tyre_wear_threshold_pct", fallback=0.10)
        self.voice_alert_oil_temp = cp.getboolean(self._VOICE, "alert_oil_temp", fallback=True)
        self.voice_alert_tire_pressure = cp.getboolean(self._VOICE, "alert_tire_pressure", fallback=True)
        self.voice_alert_lap_delta = cp.getboolean(self._VOICE, "alert_lap_delta", fallback=True)
        self.voice_alert_pit_window = cp.getboolean(self._VOICE, "alert_pit_window", fallback=True)
        self.voice_alert_overtake = cp.getboolean(self._VOICE, "alert_overtake", fallback=True)
        self.voice_alert_laps_to_finish = cp.getboolean(self._VOICE, "alert_laps_to_finish", fallback=True)
        self.voice_alert_fuel_save = cp.getboolean(self._VOICE, "alert_fuel_save", fallback=True)
        self.voice_alert_strategy_check_in = cp.getboolean(self._VOICE, "alert_strategy_check_in", fallback=True)
        self.voice_alert_strategy_revised = cp.getboolean(self._VOICE, "alert_strategy_revised", fallback=True)
        self.voice_alert_fuel_save_recommend = cp.getboolean(self._VOICE, "alert_fuel_save_recommend", fallback=True)
        self.voice_alert_advisor_pit_window = cp.getboolean(self._VOICE, "alert_advisor_pit_window", fallback=True)
        self.voice_engine_temp_threshold = cp.getfloat(self._VOICE, "engine_temp_threshold", fallback=105.0)
        self.voice_tire_temp_threshold = cp.getfloat(self._VOICE, "tire_temp_threshold", fallback=100.0)
        self.voice_tire_inner_temp_threshold = cp.getfloat(self._VOICE, "tire_inner_temp_threshold", fallback=110.0)
        self.voice_oil_temp_threshold = cp.getfloat(self._VOICE, "oil_temp_threshold", fallback=130.0)
        self.voice_tire_pressure_low_kpa = cp.getfloat(self._VOICE, "tire_pressure_low_kpa", fallback=160.0)
        self.voice_tire_pressure_high_kpa = cp.getfloat(self._VOICE, "tire_pressure_high_kpa", fallback=250.0)
        self.voice_lap_delta_threshold_s = cp.getfloat(self._VOICE, "lap_delta_threshold_s", fallback=3.0)
        self.voice_pit_window_min_laps = cp.getfloat(self._VOICE, "pit_window_min_laps", fallback=2.0)
        self.voice_pit_window_max_laps = cp.getfloat(self._VOICE, "pit_window_max_laps", fallback=4.0)
        self.tire_wear_range_m = cp.getfloat(self._STRATEGY, "tire_wear_range_m", fallback=0.015)
        self.tyre_wear_limit_pct = cp.getfloat(self._STRATEGY, "tyre_wear_limit_pct", fallback=0.80)
        self.pit_buffer_laps = cp.getint(self._STRATEGY, "pit_buffer_laps", fallback=1)
        self.voice_alert_strategy = cp.getboolean(self._STRATEGY, "voice_alert_strategy", fallback=True)
        self.voice_strategy_interval_s = cp.getfloat(self._STRATEGY, "voice_strategy_interval_s", fallback=30.0)
        self.planned_stops = cp.getint(self._STRATEGY, "planned_stops", fallback=0)
        raw_laps = cp.get(self._STRATEGY, "planned_stop_laps", fallback="")
        self.planned_stop_windows = _parse_stop_windows(raw_laps)
        self.pit_loss_time_s = cp.getfloat(self._STRATEGY, "pit_loss_time_s", fallback=25.0)
        self.strategy_check_in_interval_laps = cp.getint(self._STRATEGY, "strategy_check_in_interval_laps", fallback=3)
        self.fuel_save_delta_l = cp.getfloat(self._STRATEGY, "fuel_save_delta_l", fallback=2.0)
        self.lap_time_buffer = cp.getint(self._STRATEGY, "lap_time_buffer", fallback=3)
        self.llm_backend = cp.get(self._LLM, "backend", fallback="openai")
        self.llm_model = cp.get(self._LLM, "model", fallback="gemma4:12b")
        self.llm_api_key = cp.get(self._LLM, "api_key", fallback="") or os.environ.get("LLM_API_KEY", "")
        self.llm_base_url = cp.get(self._LLM, "base_url", fallback="http://localhost:1234/v1")
        self.recording_on_start = cp.getboolean(self._SECTION, "recording_on_start", fallback=True)
        self.recording_suffix = cp.get(self._SECTION, "recording_suffix", fallback="")
