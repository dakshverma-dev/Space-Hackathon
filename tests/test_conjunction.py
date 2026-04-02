import numpy as np

from backend.models.state import Debris, Satellite
from backend.physics.conjunction import broad_phase_candidates, build_debris_octree, detect_conjunctions


def test_broad_phase_returns_only_nearby_debris() -> None:
    sat = Satellite("SAT-1", np.array([7000.0, 0.0, 0.0, 0.0, 7.5, 0.0]))
    near = Debris("DEB-NEAR", np.array([7010.0, 0.0, 0.0, 0.0, 7.5, 0.0]))
    far = Debris("DEB-FAR", np.array([7300.0, 0.0, 0.0, 0.0, 7.5, 0.0]))

    tree = build_debris_octree([near, far])
    pairs = broad_phase_candidates([sat], tree, radius_km=50.0)
    pair_ids = {(s.object_id, d.object_id) for s, d in pairs}

    assert ("SAT-1", "DEB-NEAR") in pair_ids
    assert ("SAT-1", "DEB-FAR") not in pair_ids


def test_detect_conjunction_warns_for_close_approach() -> None:
    sat = Satellite("SAT-1", np.array([7000.0, 0.0, 0.0, 0.0, 7.5, 0.0]))
    debris = Debris("DEB-1", np.array([7000.3, 0.0, 0.0, 0.0, 7.5, 0.0]))

    warnings = detect_conjunctions(
        [sat],
        [debris],
        warning_distance_km=1.0,
        broad_phase_radius_km=50.0,
        horizon_seconds=60,
        step_seconds=10,
    )

    assert len(warnings) >= 1
    assert warnings[0]["satellite_id"] == "SAT-1"
    assert warnings[0]["debris_id"] == "DEB-1"
    assert warnings[0]["miss_distance_km"] <= 1.0
