from __future__ import annotations

import logging
from typing import Dict, List

import numpy as np

from backend.config import CRITICAL_DISTANCE, FUEL_CRITICAL_THRESHOLD
from backend.core.runtime import runtime
from backend.core.scheduler import ScheduledManeuver
from backend.models.state import Satellite
from backend.physics.conjunction import detect_conjunctions
from backend.physics.maneuver import compute_evasion_burn, compute_recovery_burn

log = logging.getLogger("aether.acm")


def _log_decision(message: str, **kwargs: object) -> None:
    rec = logging.LogRecord(log.name, logging.INFO, __file__, 0, message, args=(), exc_info=None)
    rec.extra_payload = kwargs
    log.handle(rec)


def _schedule_critical_evasion(warning: Dict, now: float) -> None:
    sat_id = warning["satellite_id"]
    sat = runtime.state.satellites.get(sat_id)
    if sat is None:
        return

    burn = compute_evasion_burn(sat.state_vector, warning, target_miss_distance_km=1.0)
    evasion = ScheduledManeuver(
        satellite_id=sat_id,
        execute_at=now + 10.0,
        dv_eci_km_s=np.asarray(burn["dv_eci_km_s"], dtype=float),
        maneuver_type="EVASION",
    )
    ok, reason = runtime.scheduler.schedule(evasion, now)
    if not ok:
        _log_decision("evasion_rejected", satellite_id=sat_id, reason=reason)
        return

    recovery = compute_recovery_burn(sat.state_vector, sat.state_vector)
    rec_m = ScheduledManeuver(
        satellite_id=sat_id,
        execute_at=now + float(warning.get("tca_seconds", 120.0)) + 30.0,
        dv_eci_km_s=np.asarray(recovery["dv_eci_km_s"], dtype=float),
        maneuver_type="RECOVERY",
    )
    runtime.scheduler.schedule(rec_m, now)
    _log_decision(
        "critical_evasion_scheduled",
        satellite_id=sat_id,
        debris_id=warning.get("debris_id"),
        miss_distance_km=warning.get("miss_distance_km"),
        collision_probability=warning.get("collision_probability"),
    )


def _deconflict_warnings(warnings: List[Dict]) -> List[Dict]:
    """Keep the riskiest warning per satellite first and stagger simultaneous maneuvers.

    This avoids multiple evasion burns for the same vehicle in the same tick and
    spreads out closely coupled burns for satellites that are near each other.
    """
    by_sat: Dict[str, Dict] = {}
    for warning in warnings:
        sat_id = warning["satellite_id"]
        current = by_sat.get(sat_id)
        if current is None:
            by_sat[sat_id] = warning
            continue
        if float(warning.get("collision_probability", 0.0)) > float(current.get("collision_probability", 0.0)):
            by_sat[sat_id] = warning

    selected = list(by_sat.values())
    selected.sort(key=lambda w: (-float(w.get("collision_probability", 0.0)), w["miss_distance_km"]))

    deferred: List[Dict] = []
    accepted_positions: List[np.ndarray] = []
    for warning in selected:
        sat = runtime.state.satellites.get(warning["satellite_id"])
        if sat is None:
            continue
        position = np.asarray(sat.state_vector[:3], dtype=float)
        too_close = any(float(np.linalg.norm(position - other_pos)) < 100.0 for other_pos in accepted_positions)
        if too_close:
            warning = dict(warning)
            warning["deconflicted"] = True
            warning["deferred_seconds"] = 120.0
        accepted_positions.append(position)
        deferred.append(warning)

    return deferred


def _schedule_graveyard_if_needed(sat: Satellite, now: float) -> None:
    fuel_fraction = sat.fuel_mass_kg / max((sat.fuel_mass_kg + sat.dry_mass_kg), 1e-6)
    if fuel_fraction >= FUEL_CRITICAL_THRESHOLD:
        return

    dv = np.array([0.0, 0.0, 0.002], dtype=float)
    m = ScheduledManeuver(
        satellite_id=sat.object_id,
        execute_at=now + 10.0,
        dv_eci_km_s=dv,
        maneuver_type="GRAVEYARD",
    )
    ok, reason = runtime.scheduler.schedule(m, now)
    if ok:
        _log_decision("graveyard_scheduled", satellite_id=sat.object_id)
    else:
        _log_decision("graveyard_rejected", satellite_id=sat.object_id, reason=reason)


def run_acm_cycle(dt_seconds: float) -> List[Dict]:
    now = runtime.state.simulation_time
    satellites = list(runtime.state.satellites.values())
    debris = list(runtime.state.debris.values())

    warnings = detect_conjunctions(
        satellites=satellites,
        debris=debris,
        broad_phase_radius_km=20.0,
        horizon_seconds=1200,
        step_seconds=60,
    )

    warnings = _deconflict_warnings(warnings)

    for warning in warnings:
        if float(warning["miss_distance_km"]) < CRITICAL_DISTANCE:
            _schedule_critical_evasion(warning, now)

    for sat in satellites:
        _schedule_graveyard_if_needed(sat, now)
        in_slot = runtime.station_keeping.update(sat.object_id, sat.state_vector[:3], dt_seconds)
        if not in_slot:
            _log_decision("station_keeping_outage", satellite_id=sat.object_id)

    return warnings
