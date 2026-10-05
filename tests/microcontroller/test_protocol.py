"""Unit tests for the microcontroller wire-format protocol module."""

import pytest

from simraceengineer.microcontroller.protocol import (
    FAN,
    PING,
    PONG,
    encode_fan_command,
    is_pong,
)


# ── constants ────────────────────────────────────────────────────────────────

def test_constants():
    assert FAN == "FAN"
    assert PING == "PING"
    assert PONG == "PONG"


# ── encode_fan_command ────────────────────────────────────────────────────────

def test_encode_fan_command_in_range():
    assert encode_fan_command(0) == "FAN:0\n"
    assert encode_fan_command(255) == "FAN:255\n"
    assert encode_fan_command(180) == "FAN:180\n"


def test_encode_fan_command_clamps_above_max():
    assert encode_fan_command(300) == "FAN:255\n"


def test_encode_fan_command_clamps_below_min():
    assert encode_fan_command(-10) == "FAN:0\n"


# ── is_pong ────────────────────────────────────────────────────────────────

def test_is_pong_exact():
    assert is_pong("PONG") is True


def test_is_pong_with_trailing_newline():
    assert is_pong("PONG\n") is True


def test_is_pong_with_surrounding_whitespace():
    assert is_pong("  PONG  \r\n") is True


def test_is_pong_false_for_other_text():
    assert is_pong("PING") is False
    assert is_pong("") is False
    assert is_pong("PONGX") is False


# ── Transport ABC ────────────────────────────────────────────────────────────

def test_transport_cannot_be_instantiated_directly():
    from simraceengineer.microcontroller.transport import Transport

    with pytest.raises(TypeError):
        Transport()  # type: ignore[abstract]
