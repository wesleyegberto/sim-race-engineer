import ast
from pathlib import Path

import pytest

import simraceengineer.dashboard.settings_form as settings_form_module
from simraceengineer.config import AppConfig
from simraceengineer.dashboard.settings_form import (
    BOOL_FIELDS,
    VOICE_ALERT_FIELDS,
    SettingsForm,
)

_COVERED_FIELDS = (
    *BOOL_FIELDS,
    "device_ip",
    "fuel_estimation",
    "voice_language",
    "voice_tyre_wear_threshold_pct",
    "microcontroller_port",
    "fan_speed_ceiling_kmh",
)


@pytest.fixture
def conf_path(tmp_path, monkeypatch):
    path = tmp_path / "sim-race.conf"
    monkeypatch.setattr(AppConfig, "PATH", path)
    return path


@pytest.fixture
def config(conf_path):
    cfg = AppConfig()
    cfg.device_ip = "192.168.1.10"
    cfg.voice_enabled = True
    cfg.voice_alert_tyre_wear = True
    cfg.voice_tyre_wear_threshold_pct = 0.29
    cfg.microcontroller_enabled = True
    cfg.microcontroller_port = "/dev/cu.usbmodem1"
    cfg.fan_speed_ceiling_kmh = 220.5
    return cfg


def _snapshot(cfg: AppConfig) -> dict[str, object]:
    return {name: getattr(cfg, name) for name in _COVERED_FIELDS}


def _enabled_voice_form(config: AppConfig, unlocked: bool = True) -> SettingsForm:
    return SettingsForm.from_config(config, show_microcontroller=unlocked)


# ── module purity ────────────────────────────────────────────────────────────

def test_module_does_not_import_pygame():
    tree = ast.parse(Path(settings_form_module.__file__).read_text())
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert "pygame" not in imported


def test_form_covers_every_field_copied_by_app_save_block():
    expected = {
        "device_ip", "fuel_estimation", "recording_on_start", "voice_enabled",
        "voice_language", "voice_tyre_wear_threshold_pct", "microcontroller_enabled",
        "microcontroller_port", "fan_speed_ceiling_kmh",
        *VOICE_ALERT_FIELDS,
    }
    covered = set(BOOL_FIELDS) | set(SettingsForm.TEXT_FIELDS) | {
        "fuel_estimation", "voice_language",
    }
    assert expected <= covered
    assert len(VOICE_ALERT_FIELDS) == 21


# ── round trip / isolation ───────────────────────────────────────────────────

@pytest.mark.parametrize("unlocked", [True, False])
def test_round_trip_preserves_every_field(config, unlocked):
    before = _snapshot(config)
    form = SettingsForm.from_config(config, show_microcontroller=unlocked)
    form.apply_to(config)
    assert _snapshot(config) == before


def test_round_trip_with_default_config(conf_path):
    cfg = AppConfig()
    before = _snapshot(cfg)
    SettingsForm.from_config(cfg, show_microcontroller=True).apply_to(cfg)
    assert _snapshot(cfg) == before
    assert isinstance(cfg.fan_speed_ceiling_kmh, float)


def test_round_trip_save_output_unchanged(config, conf_path):
    config.save()
    before = conf_path.read_text()
    SettingsForm.from_config(config, show_microcontroller=True).apply_to(config)
    config.save()
    assert conf_path.read_text() == before


def test_texts_are_loaded_from_config(config):
    form = _enabled_voice_form(config)
    assert form.texts == {
        "device_ip": "192.168.1.10",
        "voice_tyre_wear_threshold_pct": "29",
        "microcontroller_port": "/dev/cu.usbmodem1",
        "fan_speed_ceiling_kmh": "220",
    }
    assert form.fuel_estimation == config.fuel_estimation
    assert form.voice_language == config.voice_language


def test_edits_do_not_mutate_config_before_apply(config):
    before = _snapshot(config)
    form = _enabled_voice_form(config)
    form.toggle("voice_enabled")
    form.toggle("recording_on_start")
    form.type_char("device_ip", "9")
    form.backspace("microcontroller_port")
    form.fuel_estimation = "last"
    form.voice_language = "pt"
    assert _snapshot(config) == before


def test_apply_writes_edited_values(config):
    form = _enabled_voice_form(config)
    form.texts["device_ip"] = "10.0.0.5"
    form.texts["voice_tyre_wear_threshold_pct"] = "15"
    form.texts["fan_speed_ceiling_kmh"] = "180"
    form.texts["microcontroller_port"] = "COM3"
    form.toggle("voice_alert_overtake")
    form.fuel_estimation = "last"
    form.voice_language = "pt"
    overtake = form.bools["voice_alert_overtake"]
    form.apply_to(config)
    assert config.device_ip == "10.0.0.5"
    assert config.voice_tyre_wear_threshold_pct == pytest.approx(0.15)
    assert config.fan_speed_ceiling_kmh == 180.0
    assert isinstance(config.fan_speed_ceiling_kmh, float)
    assert config.microcontroller_port == "COM3"
    assert config.voice_alert_overtake is overtake
    assert config.fuel_estimation == "last"
    assert config.voice_language == "pt"


# ── validation ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "ip", ["1.2.3", "256.1.1.1", "1..2.3", ".1.2.3", "1.2.3.", "1.2.3.4.5", "1.2.3.4444"]
)
def test_validate_rejects_bad_ips(config, ip):
    form = _enabled_voice_form(config)
    form.texts["device_ip"] = ip
    assert "device_ip" in form.validate()


@pytest.mark.parametrize("ip", ["", "192.168.1.10", "0.0.0.0", "255.255.255.255"])
def test_validate_accepts_good_ips(config, ip):
    form = _enabled_voice_form(config)
    form.texts["device_ip"] = ip
    assert form.validate() == {}


@pytest.mark.parametrize("value", ["0", "100", "", "999"])
def test_wear_out_of_range_rejected_when_relevant(config, value):
    form = _enabled_voice_form(config)
    form.texts["voice_tyre_wear_threshold_pct"] = value
    assert "voice_tyre_wear_threshold_pct" in form.validate()


@pytest.mark.parametrize("value", ["1", "50", "99"])
def test_wear_in_range_accepted(config, value):
    form = _enabled_voice_form(config)
    form.texts["voice_tyre_wear_threshold_pct"] = value
    assert form.validate() == {}


@pytest.mark.parametrize("disable", ["voice_enabled", "voice_alert_tyre_wear"])
def test_wear_ignored_and_kept_when_not_relevant(config, disable):
    form = _enabled_voice_form(config)
    form.toggle(disable)
    form.texts["voice_tyre_wear_threshold_pct"] = "0"
    assert form.validate() == {}
    form.apply_to(config)
    assert config.voice_tyre_wear_threshold_pct == 0.29


@pytest.mark.parametrize("value", ["0", ""])
def test_ceiling_rejected_when_unlocked_and_enabled(config, value):
    form = _enabled_voice_form(config, unlocked=True)
    form.texts["fan_speed_ceiling_kmh"] = value
    assert "fan_speed_ceiling_kmh" in form.validate()


@pytest.mark.parametrize("value", ["0", ""])
def test_ceiling_ignored_when_microcontroller_disabled(config, value):
    form = _enabled_voice_form(config, unlocked=True)
    form.toggle("microcontroller_enabled")
    form.texts["fan_speed_ceiling_kmh"] = value
    assert form.validate() == {}
    form.apply_to(config)
    assert config.fan_speed_ceiling_kmh == 220.5
    assert config.microcontroller_enabled is False


@pytest.mark.parametrize("value", ["0", ""])
def test_ceiling_ignored_when_gate_locked(config, value):
    form = _enabled_voice_form(config, unlocked=False)
    form.texts["fan_speed_ceiling_kmh"] = value
    assert form.validate() == {}


def test_locked_gate_leaves_microcontroller_fields_untouched(config):
    form = _enabled_voice_form(config, unlocked=False)
    form.toggle("microcontroller_enabled")
    form.texts["microcontroller_port"] = "COM9"
    form.texts["fan_speed_ceiling_kmh"] = "100"
    form.apply_to(config)
    assert config.microcontroller_enabled is True
    assert config.microcontroller_port == "/dev/cu.usbmodem1"
    assert config.fan_speed_ceiling_kmh == 220.5


def test_apply_raises_when_invalid(config):
    before = _snapshot(config)
    form = _enabled_voice_form(config)
    form.texts["device_ip"] = "1.2.3"
    with pytest.raises(ValueError):
        form.apply_to(config)
    assert _snapshot(config) == before


def test_validate_rejects_unknown_choices(config):
    form = _enabled_voice_form(config)
    form.fuel_estimation = "median"
    form.voice_language = "de"
    assert set(form.validate()) == {"fuel_estimation", "voice_language"}


# ── text entry filters ───────────────────────────────────────────────────────

def test_type_char_ip_filter_and_max_len(config):
    form = _enabled_voice_form(config)
    form.texts["device_ip"] = ""
    assert form.type_char("device_ip", "a") is False
    assert form.type_char("device_ip", "-") is False
    for ch in "192.168.100.200":
        assert form.type_char("device_ip", ch) is True
    assert form.texts["device_ip"] == "192.168.100.200"
    assert form.type_char("device_ip", "1") is False
    assert len(form.texts["device_ip"]) == 15


@pytest.mark.parametrize("field", ["voice_tyre_wear_threshold_pct", "fan_speed_ceiling_kmh"])
def test_type_char_numeric_filter_and_max_len(config, field):
    form = _enabled_voice_form(config)
    form.texts[field] = ""
    assert form.type_char(field, ".") is False
    assert form.type_char(field, "x") is False
    assert form.type_char(field, "١") is False  # non-ASCII digit
    for ch in "123":
        assert form.type_char(field, ch) is True
    assert form.type_char(field, "4") is False
    assert form.texts[field] == "123"


def test_type_char_port_printable_and_max_len(config):
    form = _enabled_voice_form(config)
    form.texts["microcontroller_port"] = ""
    assert form.type_char("microcontroller_port", "\t") is False
    assert form.type_char("microcontroller_port", "\x00") is False
    for _ in range(40):
        assert form.type_char("microcontroller_port", "a") is True
    assert form.type_char("microcontroller_port", "a") is False
    assert len(form.texts["microcontroller_port"]) == 40


def test_type_char_rejects_empty_input(config):
    form = _enabled_voice_form(config)
    assert form.type_char("device_ip", "") is False


def test_backspace_reports_change(config):
    form = _enabled_voice_form(config)
    form.texts["microcontroller_port"] = "ab"
    assert form.backspace("microcontroller_port") is True
    assert form.texts["microcontroller_port"] == "a"
    assert form.backspace("microcontroller_port") is True
    assert form.backspace("microcontroller_port") is False
    assert form.texts["microcontroller_port"] == ""


# ── port auto-detection ──────────────────────────────────────────────────────

def test_toggle_on_with_empty_port_auto_detects(config):
    config.microcontroller_enabled = False
    config.microcontroller_port = ""
    form = SettingsForm.from_config(
        config, show_microcontroller=True, detect_port=lambda: "/dev/cu.detected"
    )
    assert form.texts["microcontroller_port"] == ""
    form.toggle("microcontroller_enabled")
    assert form.texts["microcontroller_port"] == "/dev/cu.detected"


def test_toggle_on_keeps_existing_port(config):
    config.microcontroller_enabled = False
    calls = []
    form = SettingsForm.from_config(
        config, show_microcontroller=True, detect_port=lambda: calls.append(1) or "X"
    )
    form.toggle("microcontroller_enabled")
    assert form.texts["microcontroller_port"] == "/dev/cu.usbmodem1"
    assert calls == []


def test_toggle_on_with_no_detected_port_leaves_empty(config):
    config.microcontroller_enabled = False
    config.microcontroller_port = ""
    form = SettingsForm.from_config(config, show_microcontroller=True)
    form.toggle("microcontroller_enabled")
    assert form.texts["microcontroller_port"] == ""


def test_from_config_enabled_with_empty_port_auto_detects(config):
    config.microcontroller_port = ""
    form = SettingsForm.from_config(
        config, show_microcontroller=True, detect_port=lambda: "/dev/cu.detected"
    )
    assert form.texts["microcontroller_port"] == "/dev/cu.detected"


def test_toggle_unknown_field_raises(config):
    form = _enabled_voice_form(config)
    with pytest.raises(KeyError):
        form.toggle("device_ip")


# ── enabled dependencies ─────────────────────────────────────────────────────

def test_voice_dependents_follow_voice_enabled(config):
    form = _enabled_voice_form(config)
    dependents = [*VOICE_ALERT_FIELDS, "voice_tyre_wear_threshold_pct"]
    assert all(form.is_enabled(name) for name in dependents)
    form.toggle("voice_enabled")
    assert not any(form.is_enabled(name) for name in dependents)
    assert form.is_enabled("voice_enabled")
    assert form.is_enabled("device_ip")
    assert form.is_enabled("recording_on_start")


def test_microcontroller_dependents_follow_enabled_flag(config):
    form = _enabled_voice_form(config, unlocked=True)
    dependents = ["microcontroller_port", "fan_speed_ceiling_kmh", "test_microcontroller"]
    assert all(form.is_enabled(name) for name in dependents)
    form.toggle("microcontroller_enabled")
    assert not any(form.is_enabled(name) for name in dependents)
    assert form.is_enabled("microcontroller_enabled")


def test_microcontroller_controls_disabled_when_gate_locked(config):
    form = _enabled_voice_form(config, unlocked=False)
    for name in ("microcontroller_enabled", "microcontroller_port",
                 "fan_speed_ceiling_kmh", "test_microcontroller"):
        assert form.is_enabled(name) is False
