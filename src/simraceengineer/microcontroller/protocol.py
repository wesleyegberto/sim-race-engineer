"""Wire format for the airflow-simulation microcontroller (ASCII lines, `\\n`-terminated).

| Direction     | Message         | Meaning                                     |
|---------------|-----------------|----------------------------------------------|
| App -> device | `FAN:<0-255>\\n` | Set PWM duty cycle for both frontal fans      |
| App -> device | `PING\\n`        | Connection test                               |
| Device -> app | `PONG\\n`        | Reply to `PING`                               |

No binary framing, no checksums — deliberately simple for a hobby-hardware v1.
"""

FAN = "FAN"
PING = "PING"
PONG = "PONG"


def encode_fan_command(duty_cycle: int) -> str:
    """Build a `FAN:<0-255>\\n` command, clamping out-of-range input to [0, 255]."""
    clamped = max(0, min(255, duty_cycle))
    return f"{FAN}:{clamped}\n"


def is_pong(line: str) -> bool:
    """True if `line` (after stripping whitespace) is exactly `PONG`."""
    return line.strip() == PONG
