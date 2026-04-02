from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

import numpy as np

from backend.utils.coordinate_transforms import geodetic_to_ecef


@dataclass
class GroundStation:
    station_id: str
    name: str
    lat_deg: float
    lon_deg: float
    alt_km: float
    elevation_mask_deg: float

    @property
    def ecef_km(self) -> np.ndarray:
        return geodetic_to_ecef(self.lat_deg, self.lon_deg, self.alt_km)


def load_ground_stations(csv_path: str | Path) -> List[GroundStation]:
    stations: List[GroundStation] = []
    with open(csv_path, "r", newline="", encoding="utf-8") as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            stations.append(
                GroundStation(
                    station_id=row["station_id"],
                    name=row["name"],
                    lat_deg=float(row["lat_deg"]),
                    lon_deg=float(row["lon_deg"]),
                    alt_km=float(row.get("alt_km", 0.0)),
                    elevation_mask_deg=float(row.get("elevation_mask_deg", 10.0)),
                )
            )
    return stations


def elevation_angle_deg(station_ecef_km: np.ndarray, sat_ecef_km: np.ndarray) -> float:
    station = np.asarray(station_ecef_km, dtype=float)
    sat = np.asarray(sat_ecef_km, dtype=float)

    los = sat - station
    up = station / np.linalg.norm(station)
    los_norm = np.linalg.norm(los)
    if los_norm <= 0.0:
        return -90.0

    sin_elev = np.dot(los / los_norm, up)
    sin_elev = float(np.clip(sin_elev, -1.0, 1.0))
    return math.degrees(math.asin(sin_elev))


def has_line_of_sight(station: GroundStation, sat_ecef_km: np.ndarray) -> bool:
    elev = elevation_angle_deg(station.ecef_km, sat_ecef_km)
    return elev >= station.elevation_mask_deg


def visible_stations(stations: Iterable[GroundStation], sat_ecef_km: np.ndarray) -> List[GroundStation]:
    return [station for station in stations if has_line_of_sight(station, sat_ecef_km)]


def first_visible_station(stations: Iterable[GroundStation], sat_ecef_km: np.ndarray) -> Optional[GroundStation]:
    for station in stations:
        if has_line_of_sight(station, sat_ecef_km):
            return station
    return None
