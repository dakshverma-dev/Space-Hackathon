from __future__ import annotations

import math
import random
from typing import List

from backend.config import MU, RE


def circular_orbit_state(radius_km: float, phase_rad: float) -> List[float]:
    x = radius_km * math.cos(phase_rad)
    y = radius_km * math.sin(phase_rad)
    z = 0.0
    v = math.sqrt(MU / radius_km)
    vx = -v * math.sin(phase_rad)
    vy = v * math.cos(phase_rad)
    vz = 0.0
    return [x, y, z, vx, vy, vz]


def generate_telemetry_payload(num_satellites: int = 50, num_debris: int = 10_000) -> dict:
    rng = random.Random(7)
    objects = []

    for i in range(num_satellites):
        phase = (2 * math.pi * i) / max(1, num_satellites)
        objects.append(
            {
                "object_id": f"SAT-{i:03d}",
                "kind": "satellite",
                "state_vector": circular_orbit_state(RE + 550.0, phase),
                "dry_mass_kg": 500.0,
                "fuel_mass_kg": 50.0 - (i * 0.2),
            }
        )

    for i in range(num_debris):
        phase = rng.uniform(0, 2 * math.pi)
        radius = RE + rng.uniform(500, 750)
        sv = circular_orbit_state(radius, phase)
        sv[2] = rng.uniform(-30, 30)
        sv[5] = rng.uniform(-0.2, 0.2)
        objects.append(
            {
                "object_id": f"DEB-{i:05d}",
                "kind": "debris",
                "state_vector": sv,
            }
        )

    return {"timestamp_seconds": 0, "objects": objects}
