from __future__ import annotations

import numpy as np
from fastapi import APIRouter

from backend.config import COLLISION_DISTANCE
from backend.core.acm import run_acm_cycle
from backend.core.runtime import runtime
from backend.models.schemas import SimulateStepRequest, SimulateStepResponse
from backend.physics.fuel import apply_burn
from backend.physics.propagator import rk4_step

router = APIRouter(prefix="/api", tags=["simulate"])


@router.post("/simulate/step", response_model=SimulateStepResponse)
def simulate_step(payload: SimulateStepRequest) -> SimulateStepResponse:
    dt = payload.step_seconds
    state = runtime.state
    state.simulation_time += dt

    for sat in state.satellites.values():
        sat.state_vector = rk4_step(sat.state_vector, dt)
    for deb in state.debris.values():
        deb.state_vector = rk4_step(deb.state_vector, dt)

    due = runtime.scheduler.pop_due(state.simulation_time)
    executed = 0
    for m in due:
        sat = state.satellites.get(m.satellite_id)
        if sat is None:
            continue

        dv_m_s = float(np.linalg.norm(m.dv_eci_km_s) * 1000.0)
        fuel = apply_burn(sat.dry_mass_kg, sat.fuel_mass_kg, dv_m_s)
        sat.fuel_mass_kg = fuel["fuel_remaining_kg"]
        sat.state_vector[3:6] += m.dv_eci_km_s
        sat.status = m.maneuver_type
        executed += 1
        state.events.append(
            {
                "time": state.simulation_time,
                "satellite_id": sat.object_id,
                "type": m.maneuver_type,
                "dv_m_s": dv_m_s,
            }
        )

    warnings = run_acm_cycle(dt)
    deconflicted = sum(1 for warning in warnings if warning.get("deconflicted"))

    for warning in warnings:
        state.events.append(
            {
                "time": state.simulation_time,
                "satellite_id": warning.get("satellite_id"),
                "debris_id": warning.get("debris_id"),
                "type": "CDM",
                "miss_distance_km": warning.get("miss_distance_km"),
                "collision_probability": warning.get("collision_probability"),
                "deconflicted": warning.get("deconflicted", False),
            }
        )

    collision_count = 0
    for sat in state.satellites.values():
        sat_pos = sat.state_vector[:3]
        for deb in state.debris.values():
            if np.linalg.norm(sat_pos - deb.state_vector[:3]) <= COLLISION_DISTANCE:
                collision_count += 1

    return SimulateStepResponse(
        simulation_time=state.simulation_time,
        collision_count=collision_count,
        maneuvers_executed=executed,
        warnings=warnings,
        conflicts_deconflicted=deconflicted,
    )
