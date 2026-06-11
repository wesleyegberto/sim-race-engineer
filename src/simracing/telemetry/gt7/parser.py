"""GT7 packet parser.

GT7 sends 296-byte UDP datagrams encrypted with Salsa20.
Key  : b"Simulator Interface Packet GT7 ver 0.0"[:32]
Nonce: derived from bytes 0x40–0x43 of the raw (encrypted) packet:
         iv1   = int.from_bytes(dat[0x40:0x44], 'little')
         iv2   = iv1 ^ 0xDEADBEAF
         nonce = iv2.to_bytes(4,'little') + iv1.to_bytes(4,'little')

Struct layout (little-endian, all offsets in bytes after decryption):
  0x00  magic          u32   must be 0x47375330
  0x04  position       3×f32
  0x10  velocity       3×f32
  0x1C  rotation       3×f32  (pitch, yaw, roll rad)
  0x28  unk
  0x2C  angular_vel    3×f32
  0x38  body_height    f32
  0x3C  engine_rpm     f32
  0x40  unk
  0x44  gas_level      f32
  0x48  gas_capacity   f32
  0x4C  speed          f32   (m/s, may be negative)
  0x50  boost          f32   (absolute bar; subtract 1 for gauge bar)
  0x54  oil_pressure   f32   (bar)
  0x58  water_temp     f32   (°C)
  0x5C  oil_temp       f32   (°C)
  0x60  tire_fl_temp   f32   (°C surface)
  0x64  tire_fr_temp   f32
  0x68  tire_rl_temp   f32
  0x6C  tire_rr_temp   f32
  0x70  packet_id      u32
  0x74  lap_count      i16
  0x76  laps_in_race   i16
  0x78  best_lap_ms    i32
  0x7C  last_lap_ms    i32
  0x80  time_of_day_ms i32
  0x84  race_start_pos i16
  0x86  total_positions i16
  0x88  min_alert_rpm  u16
  0x8A  max_alert_rpm  u16
  0x8C  calc_max_speed i16
  0x8E  flags          u16
  0x90  gear (bits 0-3) + suggested_gear (bits 4-7)  u8
  0x91  throttle       u8   (0-255)
  0x92  brake          u8   (0-255)
  0xA4  tire_fl_rps    f32   (wheel rotations/sec, signed)
  0xA8  tire_fr_rps    f32
  0xAC  tire_rl_rps    f32
  0xB0  tire_rr_rps    f32
  0xB4  tire_fl_radius f32   (metres)
  0xB8  tire_fr_radius f32
  0xBC  tire_rl_radius f32
  0xC0  tire_rr_radius f32
  0xC4  tire_fl_sus    f32   (suspension height)
  0xC8  tire_fr_sus    f32
  0xCC  tire_rl_sus    f32
  0xD0  tire_rr_sus    f32
  0xF4  clutch         f32   (0-1)
  0xF8  clutch_engage  f32
  0xFC  rpm_after_clutch f32
  0x104 gear_ratio_1   f32
  ...   (8 gear ratios to 0x120)
  0x124 car_code       i32
"""

import logging
import struct
from typing import Optional

from Crypto.Cipher import Salsa20

from ..models import TelemetryData, TireData, Vector3

log = logging.getLogger(__name__)

_MAGIC = 0x47375330
_SALSA_KEY = b"Simulator Interface Packet GT7 ver 0.0"[:32]
_PACKET_SIZE = 296


def _decrypt(data: bytes) -> Optional[bytes]:
    # Nonce is derived from the 4-byte seed at 0x40 of the encrypted packet.
    # iv1 XOR'd with 0xDEADBEAF (note: BEAF not BEEF) builds the 8-byte nonce.
    oiv = data[0x40:0x44]
    iv1 = int.from_bytes(oiv, byteorder='little')
    iv2 = iv1 ^ 0xDEADBEAF
    nonce = iv2.to_bytes(4, 'little') + iv1.to_bytes(4, 'little')

    log.debug("decrypt — pkt_size=%d  oiv=%s  nonce=%s", len(data), oiv.hex(), nonce.hex())

    cipher = Salsa20.new(key=_SALSA_KEY, nonce=nonce)
    decrypted = cipher.decrypt(data)
    magic = struct.unpack_from("<I", decrypted, 0)[0]
    if magic == _MAGIC:
        log.debug("decrypt OK")
        return decrypted

    log.warning("decrypt failed — magic=0x%08X  expected=0x%08X", magic, _MAGIC)
    return None


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
    (ang_x, ang_y, ang_z) = struct.unpack_from("<fff", buf, 0x2C)

    engine_rpm = struct.unpack_from("<f", buf, 0x3C)[0]
    fuel_level = struct.unpack_from("<f", buf, 0x44)[0]
    fuel_cap = struct.unpack_from("<f", buf, 0x48)[0]
    speed_ms = struct.unpack_from("<f", buf, 0x4C)[0]
    boost = struct.unpack_from("<f", buf, 0x50)[0] - 1.0   # absolute bar → gauge bar
    oil_pressure = struct.unpack_from("<f", buf, 0x54)[0] * 100.0   # bar→kPa
    water_temp = struct.unpack_from("<f", buf, 0x58)[0]
    oil_temp = struct.unpack_from("<f", buf, 0x5C)[0]

    surf_temps = struct.unpack_from("<ffff", buf, 0x60)   # FL FR RL RR

    packet_id = struct.unpack_from("<I", buf, 0x70)[0]
    lap_count, laps_in_race = struct.unpack_from("<hh", buf, 0x74)
    best_lap = struct.unpack_from("<i", buf, 0x78)[0]
    last_lap = struct.unpack_from("<i", buf, 0x7C)[0]

    min_rpm, max_rpm = struct.unpack_from("<HH", buf, 0x88)
    calc_max_speed = struct.unpack_from("<h", buf, 0x8C)[0]   # km/h, 0=unknown
    flags = struct.unpack_from("<H", buf, 0x8E)[0]
    gear_byte = struct.unpack_from("<B", buf, 0x90)[0]
    throttle_raw = struct.unpack_from("<B", buf, 0x91)[0]
    brake_raw = struct.unpack_from("<B", buf, 0x92)[0]

    gear = gear_byte & 0x0F
    suggested_gear = (gear_byte >> 4) & 0x0F

    clutch = struct.unpack_from("<f", buf, 0xF4)[0]
    handbrake = struct.unpack_from("<f", buf, 0x110)[0]

    # Tire detailed data: FL=0, FR=1, RL=2, RR=3
    rps_offsets = [0xA4, 0xA8, 0xAC, 0xB0]
    rad_offsets = [0xB4, 0xB8, 0xBC, 0xC0]
    sus_offsets = [0xC4, 0xC8, 0xCC, 0xD0]
    inner_offsets = [0xE4, 0xF0, 0xFC, 0x108]

    tires = [
        _tire(buf, rps_offsets[i], rad_offsets[i], sus_offsets[i],
              surf_temps[i], inner_offsets[i])
        for i in range(4)
    ]

    # flags byte at 0x8E (low byte of u16):
    # bit 0 = in_race, bit 1 = paused, bit 2 = loading, bit 3 = in_gear,
    # bit 4 = has_turbo, bit 5 = rev_limiter, bit 6 = handbrake_active,
    # bit 7 = lights_on
    # flags byte at 0x8F (high byte):
    # bit 8 = low_beam, bit 9 = high_beam, bit 10 = asm_active, bit 11 = tcs_active
    in_race = bool(flags & 0x0001)
    paused = bool(flags & 0x0002)
    loading = bool(flags & 0x0004)
    rev_limiter = bool(flags & 0x0020)
    handbrake_active = bool(flags & 0x0040)
    lights_on = bool(flags & 0x0080)
    high_beam = bool(flags & 0x0200)
    asm_active = bool(flags & 0x0400)
    tcs_active = bool(flags & 0x0800)

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
        handbrake_active=handbrake_active,
        tcs_active=tcs_active,
        asm_active=asm_active,
        lights_on=lights_on,
        high_beam=high_beam,
        packet_id=packet_id,
    )
