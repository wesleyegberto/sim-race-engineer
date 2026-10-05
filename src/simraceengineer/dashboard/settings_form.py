"""Pure model of the Settings form (no pygame).

``SettingsForm`` holds the editable state of every ``AppConfig`` field exposed in
the Settings window, applies the per-field character filters, validates the
values and writes them back to an ``AppConfig`` only on an explicit
``apply_to``. Editing a form never mutates the config it was built from.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from simraceengineer.config import AppConfig

VOICE_ALERT_FIELDS: tuple[str, ...] = (
    "voice_alert_fuel_critical",
    "voice_alert_fuel_low",
    "voice_alert_lap_completed",
    "voice_alert_best_lap",
    "voice_alert_final_lap",
    "voice_alert_race_report",
    "voice_alert_engine_temp",
    "voice_alert_tire_temp",
    "voice_alert_tire_inner_temp",
    "voice_alert_oil_temp",
    "voice_alert_tire_pressure",
    "voice_alert_lap_delta",
    "voice_alert_pit_window",
    "voice_alert_tyre_wear",
    "voice_alert_overtake",
    "voice_alert_laps_to_finish",
    "voice_alert_fuel_save",
    "voice_alert_strategy_check_in",
    "voice_alert_strategy_revised",
    "voice_alert_fuel_save_recommend",
    "voice_alert_advisor_pit_window",
)

BOOL_FIELDS: tuple[str, ...] = (
    "recording_on_start",
    "voice_enabled",
    *VOICE_ALERT_FIELDS,
    "microcontroller_enabled",
)

FUEL_ESTIMATION_OPTIONS: tuple[str, ...] = ("last", "average")
VOICE_LANGUAGE_OPTIONS: tuple[str, ...] = ("en", "pt")

# Fields only shown/applied while the airflow feature gate is unlocked.
_MICROCONTROLLER_FIELDS: frozenset[str] = frozenset(
    {"microcontroller_enabled", "microcontroller_port", "fan_speed_ceiling_kmh"}
)
# Fields that additionally require the microcontroller to be enabled.
_MICROCONTROLLER_DEPENDENT: frozenset[str] = frozenset(
    {"microcontroller_port", "fan_speed_ceiling_kmh", "test_microcontroller"}
)

_DEFAULT_FAN_CEILING_KMH = 220.0


def _is_ip_char(ch: str) -> bool:
    return ch in "0123456789."


def _is_digit(ch: str) -> bool:
    return ch.isdigit() and ch.isascii()


def _is_printable(ch: str) -> bool:
    return len(ch) == 1 and ch.isprintable()


@dataclass(frozen=True)
class TextFieldSpec:
    """Input rules for a free-text field: allowed characters and max length."""

    name: str
    max_len: int
    accept: Callable[[str], bool]


def is_valid_ip(text: str) -> bool:
    """Return True for a dotted IPv4 address with 4 octets in 0-255."""
    parts = text.split(".")
    if len(parts) != 4:
        return False
    for part in parts:
        if not part or not part.isdigit() or not part.isascii() or len(part) > 3:
            return False
        if int(part) > 255:
            return False
    return True


def _parse_int(text: str) -> int | None:
    try:
        return int(text)
    except ValueError:
        return None


class SettingsForm:
    """Editable, validatable snapshot of the Settings-exposed ``AppConfig`` fields."""

    TEXT_FIELDS: ClassVar[dict[str, TextFieldSpec]] = {
        spec.name: spec
        for spec in (
            TextFieldSpec("device_ip", 15, _is_ip_char),
            TextFieldSpec("voice_tyre_wear_threshold_pct", 3, _is_digit),
            TextFieldSpec("microcontroller_port", 40, _is_printable),
            TextFieldSpec("fan_speed_ceiling_kmh", 3, _is_digit),
        )
    }

    def __init__(
        self,
        show_microcontroller: bool,
        detect_port: Callable[[], str | None] = lambda: None,
    ) -> None:
        self.show_microcontroller = show_microcontroller
        self._detect_port = detect_port
        self.bools: dict[str, bool] = dict.fromkeys(BOOL_FIELDS, False)
        self.texts: dict[str, str] = dict.fromkeys(self.TEXT_FIELDS, "")
        self.fuel_estimation: str = "average"
        self.voice_language: str = "en"
        # Texts as loaded from config: an untouched field keeps the exact
        # config value on apply (avoids rounding e.g. 220.5 km/h to 220).
        self._initial_texts: dict[str, str] = {}

    @classmethod
    def from_config(
        cls,
        config: AppConfig,
        show_microcontroller: bool,
        detect_port: Callable[[], str | None] = lambda: None,
    ) -> SettingsForm:
        form = cls(show_microcontroller, detect_port)
        for name in BOOL_FIELDS:
            form.bools[name] = bool(getattr(config, name))
        form.fuel_estimation = config.fuel_estimation
        form.voice_language = config.voice_language

        ceiling = config.fan_speed_ceiling_kmh
        if ceiling <= 0:
            ceiling = _DEFAULT_FAN_CEILING_KMH
        form.texts["device_ip"] = config.device_ip
        form.texts["voice_tyre_wear_threshold_pct"] = str(
            round(config.voice_tyre_wear_threshold_pct * 100)
        )
        form.texts["microcontroller_port"] = config.microcontroller_port
        form.texts["fan_speed_ceiling_kmh"] = str(int(ceiling))
        form._initial_texts = dict(form.texts)

        if (show_microcontroller and form.bools["microcontroller_enabled"]
                and not form.texts["microcontroller_port"]):
            form.texts["microcontroller_port"] = detect_port() or ""
        return form

    # ── editing ──────────────────────────────────────────────────────────────

    def toggle(self, name: str) -> None:
        """Flip a boolean field; enabling the microcontroller auto-detects the port."""
        if name not in self.bools:
            raise KeyError(name)
        self.bools[name] = not self.bools[name]
        if (name == "microcontroller_enabled" and self.bools[name]
                and not self.texts["microcontroller_port"]):
            self.texts["microcontroller_port"] = self._detect_port() or ""

    def type_char(self, name: str, ch: str) -> bool:
        """Append ``ch`` if the field's filter and max length allow it.

        Returns True when the value changed (the panel resets the
        microcontroller test result on a port change).
        """
        spec = self.TEXT_FIELDS[name]
        current = self.texts[name]
        if not ch or not all(spec.accept(c) for c in ch):
            return False
        if len(current) + len(ch) > spec.max_len:
            return False
        self.texts[name] = current + ch
        return True

    def backspace(self, name: str) -> bool:
        """Delete the last character; returns True when the value changed."""
        current = self.texts[name]
        if not current:
            return False
        self.texts[name] = current[:-1]
        return True

    def is_enabled(self, name: str) -> bool:
        """Whether a control is interactive given the current form state."""
        if name in _MICROCONTROLLER_FIELDS or name in _MICROCONTROLLER_DEPENDENT:
            if not self.show_microcontroller:
                return False
            if name in _MICROCONTROLLER_DEPENDENT:
                return self.bools["microcontroller_enabled"]
            return True
        if name.startswith("voice_alert_") or name == "voice_tyre_wear_threshold_pct":
            return self.bools["voice_enabled"]
        return True

    # ── validation / output ──────────────────────────────────────────────────

    def _wear_relevant(self) -> bool:
        return self.bools["voice_enabled"] and self.bools["voice_alert_tyre_wear"]

    def _ceiling_relevant(self) -> bool:
        return self.show_microcontroller and self.bools["microcontroller_enabled"]

    def validate(self) -> dict[str, str]:
        """Return ``{field: message}`` for every invalid field; empty means valid."""
        errors: dict[str, str] = {}

        ip = self.texts["device_ip"]
        if ip and not is_valid_ip(ip):
            errors["device_ip"] = "Enter an IPv4 address like 192.168.1.10"

        if self._wear_relevant():
            wear = _parse_int(self.texts["voice_tyre_wear_threshold_pct"])
            if wear is None or not 1 <= wear <= 99:
                errors["voice_tyre_wear_threshold_pct"] = "Enter a value from 1 to 99"

        if self._ceiling_relevant():
            ceiling = _parse_int(self.texts["fan_speed_ceiling_kmh"])
            if ceiling is None or not 1 <= ceiling <= 999:
                errors["fan_speed_ceiling_kmh"] = "Enter a speed from 1 to 999 km/h"

        if self.fuel_estimation not in FUEL_ESTIMATION_OPTIONS:
            errors["fuel_estimation"] = "Choose last or average"
        if self.voice_language not in VOICE_LANGUAGE_OPTIONS:
            errors["voice_language"] = "Choose en or pt"
        return errors

    def _changed(self, name: str) -> bool:
        return self.texts[name] != self._initial_texts.get(name)

    def apply_to(self, config: AppConfig) -> None:
        """Write the form into ``config``; raises ValueError when invalid."""
        errors = self.validate()
        if errors:
            raise ValueError(f"Invalid settings: {errors}")

        config.device_ip = self.texts["device_ip"]
        config.fuel_estimation = self.fuel_estimation
        config.voice_language = self.voice_language
        for name in BOOL_FIELDS:
            if name in _MICROCONTROLLER_FIELDS:
                continue
            setattr(config, name, self.bools[name])

        name = "voice_tyre_wear_threshold_pct"
        if self._wear_relevant() and self._changed(name):
            config.voice_tyre_wear_threshold_pct = int(self.texts[name]) / 100.0

        if not self.show_microcontroller:
            return
        config.microcontroller_enabled = self.bools["microcontroller_enabled"]
        config.microcontroller_port = self.texts["microcontroller_port"]
        name = "fan_speed_ceiling_kmh"
        if self._ceiling_relevant() and self._changed(name):
            config.fan_speed_ceiling_kmh = float(int(self.texts[name]))
