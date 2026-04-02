from __future__ import annotations

from fastapi import APIRouter

from backend.core.runtime import runtime
from backend.models.schemas import SatelliteSnapshot, VisualizationSnapshotResponse
from backend.utils.coordinate_transforms import eci_to_lla

router = APIRouter(prefix="/api", tags=["visualization"])


@router.get("/visualization/snapshot", response_model=VisualizationSnapshotResponse)
def get_snapshot() -> VisualizationSnapshotResponse:
    state = runtime.state
    satellites = []
    for sat in state.satellites.values():
        lat, lon, alt = eci_to_lla(sat.state_vector[:3], state.simulation_time)
        fuel_frac = sat.fuel_mass_kg / max(sat.fuel_mass_kg + sat.dry_mass_kg, 1e-6)
        satellites.append(
            SatelliteSnapshot(
                satellite_id=sat.object_id,
                lat=lat,
                lon=lon,
                alt_km=alt,
                fuel_fraction=fuel_frac,
                status=sat.status,
            )
        )

    debris = []
    for d in state.debris.values():
        x, y, z = d.state_vector[:3]
        debris.append([float(x), float(y), float(z)])

    return VisualizationSnapshotResponse(
        simulation_time=state.simulation_time,
        satellites=satellites,
        debris=debris,
        events=state.events[-300:],
    )
