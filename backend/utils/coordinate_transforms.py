from __future__ import annotations

import math
from typing import Tuple

import numpy as np

from backend.config import RE

EARTH_ROT_RATE_RAD_S = 7.2921159e-5
WGS84_A = 6378.137
WGS84_F = 1.0 / 298.257223563
WGS84_E2 = WGS84_F * (2.0 - WGS84_F)


def eci_to_ecef(position_eci_km: np.ndarray, time_seconds: float) -> np.ndarray:
    theta = EARTH_ROT_RATE_RAD_S * time_seconds
    c = math.cos(theta)
    s = math.sin(theta)
    rot = np.array([[c, s, 0.0], [-s, c, 0.0], [0.0, 0.0, 1.0]], dtype=float)
    return rot @ np.asarray(position_eci_km, dtype=float)


def ecef_to_eci(position_ecef_km: np.ndarray, time_seconds: float) -> np.ndarray:
    theta = EARTH_ROT_RATE_RAD_S * time_seconds
    c = math.cos(theta)
    s = math.sin(theta)
    rot = np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]], dtype=float)
    return rot @ np.asarray(position_ecef_km, dtype=float)


def geodetic_to_ecef(lat_deg: float, lon_deg: float, alt_km: float = 0.0) -> np.ndarray:
    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg)
    sin_lat = math.sin(lat)
    cos_lat = math.cos(lat)
    sin_lon = math.sin(lon)
    cos_lon = math.cos(lon)

    n = WGS84_A / math.sqrt(1.0 - WGS84_E2 * sin_lat * sin_lat)
    x = (n + alt_km) * cos_lat * cos_lon
    y = (n + alt_km) * cos_lat * sin_lon
    z = (n * (1.0 - WGS84_E2) + alt_km) * sin_lat
    return np.array([x, y, z], dtype=float)


def ecef_to_lla(position_ecef_km: np.ndarray) -> Tuple[float, float, float]:
    x, y, z = np.asarray(position_ecef_km, dtype=float)
    lon = math.atan2(y, x)
    p = math.hypot(x, y)

    lat = math.atan2(z, p * (1.0 - WGS84_E2))
    for _ in range(8):
        sin_lat = math.sin(lat)
        n = WGS84_A / math.sqrt(1.0 - WGS84_E2 * sin_lat * sin_lat)
        alt = p / math.cos(lat) - n
        lat = math.atan2(z, p * (1.0 - WGS84_E2 * n / (n + alt)))

    sin_lat = math.sin(lat)
    n = WGS84_A / math.sqrt(1.0 - WGS84_E2 * sin_lat * sin_lat)
    alt = p / math.cos(lat) - n

    return math.degrees(lat), math.degrees(lon), alt


def eci_to_lla(position_eci_km: np.ndarray, time_seconds: float) -> Tuple[float, float, float]:
    return ecef_to_lla(eci_to_ecef(position_eci_km, time_seconds))


def horizon_distance_km(altitude_km: float) -> float:
    return math.sqrt(max((RE + altitude_km) ** 2 - RE**2, 0.0))
