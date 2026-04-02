from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from backend.core.scheduler import ManeuverScheduler
from backend.core.station_keeping import StationKeepingMonitor
from backend.models.state import SimulationState
from backend.physics.ground_stations import GroundStation, load_ground_stations


@dataclass
class RuntimeContext:
    state: SimulationState = field(default_factory=SimulationState)
    scheduler: ManeuverScheduler = field(default_factory=ManeuverScheduler)
    station_keeping: StationKeepingMonitor = field(default_factory=StationKeepingMonitor)
    ground_stations: List[GroundStation] = field(default_factory=list)


runtime = RuntimeContext()


def load_default_ground_stations() -> None:
    data_path = Path(__file__).resolve().parent.parent / "data" / "ground_stations.csv"
    runtime.ground_stations = load_ground_stations(data_path)
