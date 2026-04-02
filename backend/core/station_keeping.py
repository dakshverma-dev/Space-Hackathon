from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

import numpy as np

from backend.config import STATION_KEEPING_RADIUS


@dataclass
class StationKeepingMonitor:
    nominal_slots: Dict[str, np.ndarray] = field(default_factory=dict)
    outage_seconds: Dict[str, float] = field(default_factory=dict)

    def set_nominal_slot(self, satellite_id: str, nominal_position_km: np.ndarray) -> None:
        self.nominal_slots[satellite_id] = np.asarray(nominal_position_km, dtype=float)
        self.outage_seconds.setdefault(satellite_id, 0.0)

    def update(self, satellite_id: str, current_position_km: np.ndarray, dt_seconds: float) -> bool:
        nominal = self.nominal_slots.get(satellite_id)
        if nominal is None:
            self.set_nominal_slot(satellite_id, current_position_km)
            return True

        dist = float(np.linalg.norm(np.asarray(current_position_km) - nominal))
        if dist > STATION_KEEPING_RADIUS:
            self.outage_seconds[satellite_id] = self.outage_seconds.get(satellite_id, 0.0) + dt_seconds
            return False
        return True
