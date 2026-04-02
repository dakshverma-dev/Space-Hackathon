import numpy as np

from backend.config import RE
from backend.physics.fuel import apply_burn
from backend.physics.ground_stations import GroundStation, has_line_of_sight
from backend.physics.maneuver import compute_evasion_burn, eci_to_rtn, rtn_frame_from_state, rtn_to_eci


def test_rtn_round_trip_conversion() -> None:
    state = np.array([7000.0, 10.0, 5.0, -0.01, 7.5, 0.8], dtype=float)
    vec_rtn = np.array([0.001, 0.002, -0.0005], dtype=float)

    vec_eci = rtn_to_eci(vec_rtn, state)
    recovered = eci_to_rtn(vec_eci, state)
    basis = rtn_frame_from_state(state[:3], state[3:6])

    assert np.allclose(recovered, vec_rtn, atol=1e-9)
    assert np.allclose(basis.T @ basis, np.eye(3), atol=1e-9)


def test_evasion_burn_limited_by_max_dv() -> None:
    state = np.array([7000.0, 0.0, 0.0, 0.0, 7.5, 0.0], dtype=float)
    conjunction = {"miss_distance_km": 0.1, "tca_seconds": 20.0}
    burn = compute_evasion_burn(state, conjunction, target_miss_distance_km=1.0, max_dv_per_burn_m_s=15.0)

    assert burn["dv_m_s"] <= 15.0
    assert burn["predicted_new_miss_distance_km"] >= 0.1


def test_tsiolkovsky_burn_reduces_fuel() -> None:
    result = apply_burn(dry_mass_kg=500.0, fuel_mass_kg=50.0, delta_v_m_s=5.0)
    assert result["fuel_used_kg"] > 0.0
    assert result["fuel_remaining_kg"] < 50.0


def test_ground_station_los_for_overhead_satellite() -> None:
    station = GroundStation("GS-1", "Test", 0.0, 0.0, 0.0, elevation_mask_deg=10.0)
    sat_ecef = np.array([RE + 500.0, 0.0, 0.0], dtype=float)
    assert has_line_of_sight(station, sat_ecef)
