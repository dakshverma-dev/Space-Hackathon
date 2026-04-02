import numpy as np

from backend.config import MU, RE
from backend.physics.propagator import estimate_orbital_period_seconds, propagate_state


def test_circular_leo_stability_for_one_orbit() -> None:
    altitude_km = 500.0
    r0 = RE + altitude_km
    v0 = np.sqrt(MU / r0)
    state = np.array([r0, 0.0, 0.0, 0.0, v0, 0.0], dtype=float)

    period_s = estimate_orbital_period_seconds(state)
    dt_s = 10.0
    steps = int(period_s // dt_s)

    propagated = propagate_state(state, dt_s, steps)

    r_initial = np.linalg.norm(state[:3])
    r_final = np.linalg.norm(propagated[:3])
    rel_radius_error = abs(r_final - r_initial) / r_initial

    assert rel_radius_error < 0.01
