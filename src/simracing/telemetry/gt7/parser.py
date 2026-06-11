"""GT7 packet parser.

GT7 sends 296-byte UDP datagrams encrypted with Salsa20.
Key  : b"Simulator Interface Packet GT7 ver 0.0"
Nonce: bytes 0x40–0x47 of the raw (encrypted) packet, reversed.

Struct layout (little-endian, all offsets in bytes after decryption):
  0x00  magic          u32   must be 0x47375330
  0x04  position       3×f32
  0x10  velocity       3×f32
  0x1C  rotation       3×f32  (pitch, yaw, roll rad)
  0x28  angular_vel    3×f32
  0x34  body_height    f32
  0x38  engine_rpm     f32
  0x3C  gas_level      f32
  0x40  gas_capacity   f32
  0x44  speed          f32   (m/s, may be negative)
  0x48  boost          f32   (bar above 1 atm, i.e. boost-1)
  0x4C  oil_pressure   f32   (bar)
  0x50  water_temp     f32   (°C)
  0x54  oil_temp       f32   (°C)
  0x58  tire_fl_temp   f32   (°C surface)
  0x5C  tire_fr_temp   f32
  0x60  tire_rl_temp   f32
  0x64  tire_rr_temp   f32
  0x68  packet_id      u32
  0x6C  lap_count      u16
  0x6E  laps_in_race   u16
  0x70  best_lap_ms    i32
  0x74  last_lap_ms    i32
  0x78  time_of_day_ms i32
  0x7C  race_start_pos i16
  0x7E  pre_race_count i16
  0x80  min_alert_rpm  u16
  0x82  max_alert_rpm  u16
  0x84  calc_max_speed u16
  0x86  flags          u16
  0x88  gear (bits 0-3) + suggested_gear (bits 4-7)  u8
  0x89  throttle       u8   (0-255)
  0x8A  brake          u8   (0-255)
  0x8B  unk
  0x8C  road_plane     3×f32
  0x98  road_dist      f32
  0x9C  tire_fl_rps    f32   (wheel rotations/sec, signed)
  0xA0  tire_fr_rps    f32
  0xA4  tire_rl_rps    f32
  0xA8  tire_rr_rps    f32
  0xAC  tire_fl_radius f32   (metres)
  0xB0  tire_fr_radius f32
  0xB4  tire_rl_radius f32
  0xB8  tire_rr_radius f32
  0xBC  tire_fl_sus    f32   (suspension height)
  0xC0  tire_fr_sus    f32
  0xC4  tire_rl_sus    f32
  0xC8  tire_rr_sus    f32
  0xCC  (reserved)
  0xD0  clutch         f32   (0-1)
  0xD4  clutch_engage  f32
  0xD8  rpm_after_clutch f32
  0xDC  tire_fl_temp2  f32   (inner)
  0xE0  tire_fl_temp3  f32   (middle)
  0xE4  tire_fl_temp4  f32   (outer)
  (pattern repeats for FR, RL, RR — 0xE8…0x107)
  0x108 handbrake      f32
  0x10C gear_ratio_0   f32   (reverse)
  ...   (8 gear ratios)
  0x128 car_code       i64
"""

import struct
from typing import Optional

from Crypto.Cipher import Salsa20

from ..models import TelemetryData, TireData, Vector3

_MAGIC = 0x47375330
_SALSA_KEY = b"Simulator Interface Packet GT7 ver 0.0"
_PACKET_SIZE = 296


def _decrypt(data: bytes) -> Optional[bytes]:
    nonce = data[0x40:0x48][::-1]
    cipher = Salsa20.new(key=_SALSA_KEY, nonce=nonce)
    decrypted = cipher.decrypt(data)
    magic = struct.unpack_from("<I", decrypted, 0)[0]
    if magic != _MAGIC:
        return None
    return decrypted


def _vec3(buf: bytes, offset: int) -> Vector3:
    x, y, z = struct.unpack_from("<fff", buf, offset)
    return Vector3(x, y, z)


def _tire(buf: bytes, rps_off: int, rad_off: int, sus_off: int,
          surface_temp: float, inner_off: int) -> TireData:
    rps = struct.unpack_from("<f", buf, rps_off)[0]
    rad = struct.unpack_from("<f", buf, rad_off)[0]
    sus = struct.unpack_from("<f", buf, sus_off)[0]
    t_inner, t_mid, t_outer = struct.unpack_from("<fff", buf, inner_off)
    wheel_rpm = abs(rps) * 60.0
    return TireData(
        surface_temp=surface_temp,
        inner_temp=t_inner,
        middle_temp=t_mid,
        outer_temp=t_outer,
        wheel_rpm=wheel_rpm,
        radius=rad,
        suspension_height=sus,
    )


def parse(raw: bytes) -> Optional[TelemetryData]:
    if len(raw) < _PACKET_SIZE:
        return None
    buf = _decrypt(raw)
    if buf is None:
        return None

    (pos_x, pos_y, pos_z) = struct.unpack_from("<fff", buf, 0x04)
    (vel_x, vel_y, vel_z) = struct.unpack_from("<fff", buf, 0x10)
    (rot_x, rot_y, rot_z) = struct.unpack_from("<fff", buf, 0x1C)
    (ang_x, ang_y, ang_z) = struct.unpack_from("<fff", buf, 0x28)

    engine_rpm = struct.unpack_from("<f", buf, 0x38)[0]
    fuel_level = struct.unpack_from("<f", buf, 0x3C)[0]
    fuel_cap = struct.unpack_from("<f", buf, 0x40)[0]
    speed_ms = struct.unpack_from("<f", buf, 0x44)[0]
    boost = struct.unpack_from("<f", buf, 0x48)[0]
    oil_pressure = struct.unpack_from("<f", buf, 0x4C)[0] * 100.0   # bar→kPa
    water_temp = struct.unpack_from("<f", buf, 0x50)[0]
    oil_temp = struct.unpack_from("<f", buf, 0x54)[0]

    surf_temps = struct.unpack_from("<ffff", buf, 0x58)   # FL FR RL RR

    packet_id = struct.unpack_from("<I", buf, 0x68)[0]
    lap_count, laps_in_race = struct.unpack_from("<HH", buf, 0x6C)
    best_lap = struct.unpack_from("<i", buf, 0x70)[0]
    last_lap = struct.unpack_from("<i", buf, 0x74)[0]

    min_rpm, max_rpm = struct.unpack_from("<HH", buf, 0x80)
    calc_max_speed = struct.unpack_from("<H", buf, 0x84)[0]   # km/h, 0=unknown
    flags = struct.unpack_from("<H", buf, 0x86)[0]
    gear_byte = struct.unpack_from("<B", buf, 0x88)[0]
    throttle_raw = struct.unpack_from("<B", buf, 0x89)[0]
    brake_raw = struct.unpack_from("<B", buf, 0x8A)[0]

    gear = gear_byte & 0x0F
    suggested_gear = (gear_byte >> 4) & 0x0F

    clutch = struct.unpack_from("<f", buf, 0xD0)[0]
    handbrake = struct.unpack_from("<f", buf, 0x108)[0]

    # Tire detailed data: FL=0, FR=1, RL=2, RR=3
    rps_offsets = [0x9C, 0xA0, 0xA4, 0xA8]
    rad_offsets = [0xAC, 0xB0, 0xB4, 0xB8]
    sus_offsets = [0xBC, 0xC0, 0xC4, 0xC8]
    inner_offsets = [0xDC, 0xE8, 0xF4, 0x100]

    tires = [
        _tire(buf, rps_offsets[i], rad_offsets[i], sus_offsets[i],
              surf_temps[i], inner_offsets[i])
        for i in range(4)
    ]

    # flags bits: 0=in_race, 1=paused, 5=loading, 6=in_gear, 7=has_turbo,
    #             8=rev_limiter, 9=hand_brake, 10=lights, 11=low_beam,
    #             12=high_beam, 13=asm, 14=tcs
    in_race = bool(flags & (1 << 0))
    paused = bool(flags & (1 << 1))
    loading = bool(flags & (1 << 5))
    rev_limiter = bool(flags & (1 << 8))

    return TelemetryData(
        position=Vector3(pos_x, pos_y, pos_z),
        velocity=Vector3(vel_x, vel_y, vel_z),
        rotation=Vector3(rot_x, rot_y, rot_z),
        angular_velocity=Vector3(ang_x, ang_y, ang_z),
        speed_ms=abs(speed_ms),
        speed_max_kmh=float(calc_max_speed) if calc_max_speed > 0 else 0.0,
        rpm=engine_rpm,
        rpm_max=float(max_rpm) if max_rpm > 0 else 8000.0,
        rpm_idle=float(min_rpm) if min_rpm > 0 else 800.0,
        gear=gear,
        suggested_gear=suggested_gear,
        throttle=throttle_raw / 255.0,
        brake=brake_raw / 255.0,
        clutch=clutch,
        handbrake=handbrake,
        turbo_boost=boost,
        oil_temp=oil_temp,
        water_temp=water_temp,
        oil_pressure=oil_pressure,
        fuel_level=fuel_level,
        fuel_capacity=fuel_cap,
        tires=tires,
        current_lap=lap_count,
        total_laps=laps_in_race,
        best_lap_ms=best_lap if best_lap > 0 else 0,
        last_lap_ms=last_lap if last_lap > 0 else 0,
        in_race=in_race,
        paused=paused,
        loading=loading,
        rev_limiter=rev_limiter,
        packet_id=packet_id,
    )
