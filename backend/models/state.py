from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

import numpy as np


@dataclass
class SpaceObject:
    object_id: str
    state_vector: np.ndarray
    epoch_seconds: float = 0.0

    def __post_init__(self) -> None:
        self.state_vector = np.asarray(self.state_vector, dtype=float)
        if self.state_vector.shape != (6,):
            raise ValueError("state_vector must be shape (6,)")


@dataclass
class Satellite(SpaceObject):
    dry_mass_kg: float = 500.0
    fuel_mass_kg: float = 50.0
    status: str = "NOMINAL"

    @property
    def total_mass_kg(self) -> float:
        return self.dry_mass_kg + self.fuel_mass_kg


@dataclass
class Debris(SpaceObject):
    size_m: float = 0.1


@dataclass
class SimulationState:
    simulation_time: float = 0.0
    satellites: Dict[str, Satellite] = field(default_factory=dict)
    debris: Dict[str, Debris] = field(default_factory=dict)
    events: List[dict] = field(default_factory=list)

    def add_satellite(self, sat: Satellite) -> None:
        self.satellites[sat.object_id] = sat

    def add_debris(self, obj: Debris) -> None:
        self.debris[obj.object_id] = obj
