from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Vector3:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


@dataclass
class TireData:
    """Per-tire telemetry. Positions: FL, FR, RL, RR."""
    surface_temp: float = 0.0    # °C
    inner_temp: float = 0.0      # °C
    middle_temp: float = 0.0     # °C
    outer_temp: float = 0.0      # °C
    wear: float = 0.0            # 0.0–1.0
    wheel_rpm: float = 0.0
    radius: float = 0.0          # metres
    suspension_height: float = 0.0  # metres


@dataclass
class TelemetryData:
    """Unified, game-agnostic telemetry snapshot."""

    # Motion
    position: Vector3 = field(default_factory=Vector3)
    velocity: Vector3 = field(default_factory=Vector3)
    rotation: Vector3 = field(default_factory=Vector3)       # pitch, yaw, roll (rad)
    angular_velocity: Vector3 = field(default_factory=Vector3)
    g_force: Vector3 = field(default_factory=Vector3)        # lateral, longitudinal, vertical

    # Powertrain
    speed_ms: float = 0.0        # m/s
    speed_max_kmh: float = 0.0   # calculated top speed (0 = unknown)
    rpm: float = 0.0
    rpm_max: float = 8000.0
    rpm_idle: float = 800.0
    gear: int = 0                # 0=neutral, 15=reverse
    suggested_gear: int = 0
    throttle: float = 0.0        # 0.0–1.0
    brake: float = 0.0           # 0.0–1.0
    clutch: float = 0.0          # 0.0–1.0
    handbrake: float = 0.0       # 0.0–1.0
    turbo_boost: float = 0.0     # bar above atm

    # Engine / temps
    oil_temp: float = 0.0        # °C
    water_temp: float = 0.0      # °C
    oil_pressure: float = 0.0    # kPa
    fuel_level: float = 0.0      # litres
    fuel_capacity: float = 0.0   # litres

    # Tires (FL, FR, RL, RR)
    tires: list[TireData] = field(default_factory=lambda: [TireData() for _ in range(4)])

    # Lap / race
    current_lap: int = 0
    total_laps: int = 0
    lap_time_ms: int = 0
    last_lap_ms: int = 0
    best_lap_ms: int = 0
    race_position: int = 0
    cars_in_race: int = 0

    # Flags
    in_race: bool = False
    paused: bool = False
    loading: bool = False
    rev_limiter: bool = False

    # Raw timestamp from the game packet (monotonic counter)
    packet_id: int = 0

    @property
    def speed_kmh(self) -> float:
        return self.speed_ms * 3.6

    @property
    def fuel_pct(self) -> float:
        if self.fuel_capacity <= 0:
            return 0.0
        return self.fuel_level / self.fuel_capacity

    @property
    def gear_label(self) -> str:
        if self.gear == 0:
            return "N"
        if self.gear == 15:
            return "R"
        return str(self.gear)

    @property
    def avg_tire_temp(self) -> Optional[float]:
        if not self.tires:
            return None
        return sum(t.surface_temp for t in self.tires) / len(self.tires)
