from configparser import ConfigParser

import pytest

from simraceengineer.config import AppConfig
from simraceengineer.dashboard.widgets.help_panel import (
    _RIGHT,
    _SETTINGS_LEFT,
    _without_microcontroller,
)


@pytest.fixture
def conf_path(tmp_path, monkeypatch):
    path = tmp_path / "sim-race.conf"
    monkeypatch.setattr(AppConfig, "PATH", path)
    return path


def _write(path, **micro):
    cp = ConfigParser()
    cp["microcontroller"] = micro
    with open(path, "w") as fh:
        cp.write(fh)


def test_unlocked_defaults_to_false_when_absent(conf_path):
    _write(conf_path, enabled="True")
    cfg = AppConfig()
    assert cfg.microcontroller_unlocked is False
    assert cfg.microcontroller_enabled is True


def test_unlocked_read_from_file(conf_path):
    _write(conf_path, unlocked="true")
    assert AppConfig().microcontroller_unlocked is True


def test_save_omits_unlocked_key_while_locked(conf_path):
    AppConfig().save()
    cp = ConfigParser()
    cp.read(conf_path)
    assert not cp.has_option("microcontroller", "unlocked")


def test_save_keeps_unlocked_key_once_unlocked(conf_path):
    _write(conf_path, unlocked="true")
    AppConfig().save()
    assert AppConfig().microcontroller_unlocked is True


def test_help_filter_drops_airflow_section_and_fan_chip():
    settings = _without_microcontroller(_SETTINGS_LEFT)
    dashboard = _without_microcontroller(_RIGHT)
    titles = {e[1] for e in settings + dashboard}
    assert "AIRFLOW SIMULATION" not in titles
    assert "Fan speed ceiling" not in titles
    assert "FAN" not in titles
    # Unrelated entries survive, including the section right before airflow
    assert "TYRE WEAR ALERT" in titles
    assert "OIL" in titles
