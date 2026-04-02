from __future__ import annotations

from typing import Tuple

import numpy as np

from backend.config import J2, MU, RE


def _ensure_2d_states(state: np.ndarray) -> Tuple[np.ndarray, bool]:
    arr = np.asarray(state, dtype=float)
    if arr.ndim == 1:
        if arr.shape[0] != 6:
            raise ValueError("1D state must have 6 elements")
        return arr.reshape(1, 6), True
    if arr.ndim == 2 and arr.shape[1] == 6:
        return arr, False
    raise ValueError("state must be shape (6,) or (N, 6)")


def j2_acceleration(position_km: np.ndarray) -> np.ndarray:
    """Compute acceleration with central gravity + J2 in km/s^2."""
    pos = np.asarray(position_km, dtype=float)
    if pos.ndim == 1:
        if pos.shape[0] != 3:
            raise ValueError("1D position must have 3 elements")
        r = pos.reshape(1, 3)
        squeezed = True
    elif pos.ndim == 2 and pos.shape[1] == 3:
        r = pos
        squeezed = False
    else:
        raise ValueError("position must be shape (3,) or (N, 3)")

    x = r[:, 0]
    y = r[:, 1]
    z = r[:, 2]

    r2 = np.sum(r * r, axis=1)
    r_norm = np.sqrt(r2)
    r5 = r_norm**5
    r7 = r_norm**7

    with np.errstate(divide="ignore", invalid="ignore"):
        a_central = -MU * r / r_norm[:, None] ** 3

        z2 = z * z
        factor = 1.5 * J2 * MU * RE * RE / r5
        common = 5.0 * z2 / r2
        a_j2_x = factor * x * (common - 1.0)
        a_j2_y = factor * y * (common - 1.0)
        a_j2_z = factor * z * (common - 3.0)
        a_j2 = np.column_stack((a_j2_x, a_j2_y, a_j2_z))

        accel = a_central + a_j2

    accel = np.nan_to_num(accel, nan=0.0, posinf=0.0, neginf=0.0)
    if squeezed:
        return accel[0]
    return accel


def state_derivative(state: np.ndarray) -> np.ndarray:
    states, squeezed = _ensure_2d_states(state)
    vel = states[:, 3:6]
    acc = j2_acceleration(states[:, :3])
    deriv = np.hstack((vel, acc))
    if squeezed:
        return deriv[0]
    return deriv


def rk4_step(state: np.ndarray, dt_seconds: float) -> np.ndarray:
    states, squeezed = _ensure_2d_states(state)
    dt = float(dt_seconds)

    k1 = state_derivative(states)
    k2 = state_derivative(states + 0.5 * dt * k1)
    k3 = state_derivative(states + 0.5 * dt * k2)
    k4 = state_derivative(states + dt * k3)

    next_states = states + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
    if squeezed:
        return next_states[0]
    return next_states


def propagate_state(state: np.ndarray, dt_seconds: float, steps: int = 1) -> np.ndarray:
    if steps < 1:
        raise ValueError("steps must be >= 1")
    out = np.asarray(state, dtype=float)
    for _ in range(steps):
        out = rk4_step(out, dt_seconds)
    return out


def estimate_orbital_period_seconds(state: np.ndarray) -> float:
    vec = np.asarray(state, dtype=float)
    r = np.linalg.norm(vec[:3])
    v = np.linalg.norm(vec[3:])
    specific_energy = 0.5 * v * v - MU / r
    semi_major_axis = -MU / (2.0 * specific_energy)
    return 2.0 * np.pi * np.sqrt(semi_major_axis**3 / MU)
