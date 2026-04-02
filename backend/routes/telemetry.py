from __future__ import annotations

import numpy as np
from fastapi import APIRouter

from backend.core.acm import run_acm_cycle
from backend.core.runtime import runtime
from backend.models.schemas import TelemetryRequest, TelemetryResponse
from backend.models.state import Debris, Satellite

router = APIRouter(prefix="/api", tags=["telemetry"])


@router.post("/telemetry", response_model=TelemetryResponse)
def ingest_telemetry(payload: TelemetryRequest) -> TelemetryResponse:
    runtime.state.simulation_time = payload.timestamp_seconds

    for obj in payload.objects:
        state = np.asarray(obj.state_vector, dtype=float)
        if obj.kind == "satellite":
            sat = Satellite(
                object_id=obj.object_id,
                state_vector=state,
                fuel_mass_kg=obj.fuel_mass_kg if obj.fuel_mass_kg is not None else 50.0,
                dry_mass_kg=obj.dry_mass_kg if obj.dry_mass_kg is not None else 500.0,
            )
            runtime.state.add_satellite(sat)
            runtime.station_keeping.set_nominal_slot(sat.object_id, sat.state_vector[:3])
        else:
            runtime.state.add_debris(Debris(object_id=obj.object_id, state_vector=state))

    warnings = run_acm_cycle(dt_seconds=0.0)
    return TelemetryResponse(ack=True, cdm_warning_count=len(warnings), warnings=warnings)
