from __future__ import annotations

from typing import Dict

import numpy as np

from backend.config import MAX_DV_PER_BURN
from backend.physics.propagator import estimate_orbital_period_seconds


def rtn_frame_from_state(position_eci_km: np.ndarray, velocity_eci_km_s: np.ndarray) -> np.ndarray:
    r = np.asarray(position_eci_km, dtype=float)
    v = np.asarray(velocity_eci_km_s, dtype=float)

    r_hat = r / np.linalg.norm(r)
    h_hat = np.cross(r, v)
    h_hat = h_hat / np.linalg.norm(h_hat)
    t_hat = np.cross(h_hat, r_hat)
    return np.column_stack((r_hat, t_hat, h_hat))


def rtn_to_eci(dv_rtn_km_s: np.ndarray, state_eci: np.ndarray) -> np.ndarray:
    basis = rtn_frame_from_state(state_eci[:3], state_eci[3:6])
    return basis @ np.asarray(dv_rtn_km_s, dtype=float)


def eci_to_rtn(vec_eci: np.ndarray, state_eci: np.ndarray) -> np.ndarray:
    basis = rtn_frame_from_state(state_eci[:3], state_eci[3:6])
    return basis.T @ np.asarray(vec_eci, dtype=float)


def compute_evasion_burn(
    sat_state_eci: np.ndarray,
    conjunction: Dict[str, float | list],
    target_miss_distance_km: float = 1.0,
    max_dv_per_burn_m_s: float = MAX_DV_PER_BURN,
) -> Dict[str, object]:
    miss_distance = float(conjunction.get("miss_distance_km", 0.0))
    tca_seconds = max(float(conjunction.get("tca_seconds", 1.0)), 1.0)

    needed_offset = max(target_miss_distance_km - miss_distance, 0.0)
    dv_tangential_km_s = needed_offset / tca_seconds
    dv_m_s = dv_tangential_km_s * 1000.0

    if dv_m_s > max_dv_per_burn_m_s:
        dv_m_s = max_dv_per_burn_m_s
        dv_tangential_km_s = dv_m_s / 1000.0

    dv_rtn = np.array([0.0, dv_tangential_km_s, 0.0], dtype=float)
    dv_eci = rtn_to_eci(dv_rtn, sat_state_eci)

    return {
        "dv_rtn_km_s": dv_rtn.tolist(),
        "dv_eci_km_s": dv_eci.tolist(),
        "dv_m_s": dv_m_s,
        "predicted_new_miss_distance_km": miss_distance + dv_tangential_km_s * tca_seconds,
    }


def compute_recovery_burn(
    current_state_eci: np.ndarray,
    nominal_state_eci: np.ndarray,
    max_dv_per_burn_m_s: float = MAX_DV_PER_BURN,
) -> Dict[str, object]:
    current = np.asarray(current_state_eci, dtype=float)
    nominal = np.asarray(nominal_state_eci, dtype=float)

    rel_pos_eci = nominal[:3] - current[:3]
    rel_pos_rtn = eci_to_rtn(rel_pos_eci, current)

    period = estimate_orbital_period_seconds(current)
    desired_tangential_km_s = rel_pos_rtn[1] / max(period, 1.0)
    dv_m_s = min(abs(desired_tangential_km_s) * 1000.0, max_dv_per_burn_m_s)
    signed_tangential_km_s = np.sign(desired_tangential_km_s) * (dv_m_s / 1000.0)

    dv_rtn = np.array([0.0, signed_tangential_km_s, 0.0], dtype=float)
    dv_eci = rtn_to_eci(dv_rtn, current)

    return {
        "dv_rtn_km_s": dv_rtn.tolist(),
        "dv_eci_km_s": dv_eci.tolist(),
        "dv_m_s": dv_m_s,
        "time_to_slot_seconds": period,
    }
