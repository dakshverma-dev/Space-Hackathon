from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from backend.config import (
    CONJUNCTION_HORIZON,
    DEFAULT_BROAD_PHASE_RADIUS_KM,
    DEFAULT_CONJUNCTION_STEP,
    WARNING_DISTANCE,
)
from backend.models.state import Debris, Satellite
from backend.physics.propagator import rk4_step


@dataclass
class OctreeObject:
    object_id: str
    position: np.ndarray
    state_vector: np.ndarray


class OctreeNode:
    def __init__(self, center: np.ndarray, half_size: float, capacity: int = 32, depth: int = 0) -> None:
        self.center = np.asarray(center, dtype=float)
        self.half_size = float(half_size)
        self.capacity = capacity
        self.depth = depth
        self.objects: List[OctreeObject] = []
        self.children: Optional[List[OctreeNode]] = None

    def _contains(self, point: np.ndarray) -> bool:
        return np.all(np.abs(point - self.center) <= self.half_size)

    def _child_index(self, point: np.ndarray) -> int:
        idx = 0
        idx |= int(point[0] >= self.center[0])
        idx |= int(point[1] >= self.center[1]) << 1
        idx |= int(point[2] >= self.center[2]) << 2
        return idx

    def _subdivide(self) -> None:
        child_half = self.half_size / 2.0
        offsets = np.array(
            [
                [-1, -1, -1],
                [1, -1, -1],
                [-1, 1, -1],
                [1, 1, -1],
                [-1, -1, 1],
                [1, -1, 1],
                [-1, 1, 1],
                [1, 1, 1],
            ],
            dtype=float,
        )
        self.children = [
            OctreeNode(self.center + offset * child_half, child_half, self.capacity, self.depth + 1)
            for offset in offsets
        ]

        for obj in self.objects:
            self.children[self._child_index(obj.position)].insert(obj)
        self.objects.clear()

    def insert(self, obj: OctreeObject) -> bool:
        if not self._contains(obj.position):
            return False

        if self.children is None and len(self.objects) < self.capacity:
            self.objects.append(obj)
            return True

        if self.children is None:
            self._subdivide()

        return self.children[self._child_index(obj.position)].insert(obj)

    def query_sphere(self, center: np.ndarray, radius: float, out: List[OctreeObject]) -> None:
        center = np.asarray(center, dtype=float)
        if not self._intersects_sphere(center, radius):
            return

        if self.children is not None:
            for child in self.children:
                child.query_sphere(center, radius, out)
            return

        r2 = radius * radius
        for obj in self.objects:
            if np.sum((obj.position - center) ** 2) <= r2:
                out.append(obj)

    def _intersects_sphere(self, sphere_center: np.ndarray, radius: float) -> bool:
        d = np.maximum(np.abs(sphere_center - self.center) - self.half_size, 0.0)
        return np.dot(d, d) <= radius * radius


def estimate_collision_probability(
    miss_distance_km: float,
    relative_speed_km_s: float,
    hard_body_radius_km: float = 0.05,
) -> float:
    """Heuristic Pc estimate that grows as miss distance shrinks and approach speed rises."""
    scale = max(0.15, 0.03 + 0.015 * relative_speed_km_s)
    x = max(miss_distance_km - hard_body_radius_km, 0.0)
    pc = float(np.exp(-((x / scale) ** 2)))
    return float(np.clip(pc, 0.0, 1.0))


def build_debris_octree(debris: Sequence[Debris]) -> OctreeNode:
    if not debris:
        return OctreeNode(np.zeros(3), 1.0)

    positions = np.array([d.state_vector[:3] for d in debris], dtype=float)
    mins = positions.min(axis=0)
    maxs = positions.max(axis=0)
    center = (mins + maxs) / 2.0
    half_size = max(float(np.max(maxs - mins)) / 2.0, 1.0) + 1.0
    root = OctreeNode(center, half_size)
    for d in debris:
        root.insert(OctreeObject(d.object_id, d.state_vector[:3], d.state_vector.copy()))
    return root


def broad_phase_candidates(
    satellites: Sequence[Satellite],
    debris_tree: OctreeNode,
    radius_km: float = DEFAULT_BROAD_PHASE_RADIUS_KM,
) -> List[Tuple[Satellite, OctreeObject]]:
    pairs: List[Tuple[Satellite, OctreeObject]] = []
    for sat in satellites:
        found: List[OctreeObject] = []
        debris_tree.query_sphere(sat.state_vector[:3], radius_km, found)
        for obj in found:
            pairs.append((sat, obj))
    return pairs


def find_tca(
    sat_state: np.ndarray,
    debris_state: np.ndarray,
    horizon_seconds: int = CONJUNCTION_HORIZON,
    step_seconds: int = DEFAULT_CONJUNCTION_STEP,
) -> Dict[str, np.ndarray | float]:
    sat = np.asarray(sat_state, dtype=float).copy()
    deb = np.asarray(debris_state, dtype=float).copy()

    best_d = float("inf")
    best_t = 0.0
    best_rel_pos = np.zeros(3)
    best_rel_vel = np.zeros(3)

    n_steps = int(horizon_seconds // step_seconds)
    for i in range(n_steps + 1):
        rel_pos = deb[:3] - sat[:3]
        dist = float(np.linalg.norm(rel_pos))
        if dist < best_d:
            best_d = dist
            best_t = i * step_seconds
            best_rel_pos = rel_pos
            best_rel_vel = deb[3:6] - sat[3:6]

        sat = rk4_step(sat, step_seconds)
        deb = rk4_step(deb, step_seconds)

    return {
        "miss_distance_km": best_d,
        "tca_seconds": best_t,
        "relative_position_km": best_rel_pos,
        "approach_vector_km_s": best_rel_vel,
    }


def detect_conjunctions(
    satellites: Sequence[Satellite],
    debris: Sequence[Debris],
    warning_distance_km: float = WARNING_DISTANCE,
    broad_phase_radius_km: float = DEFAULT_BROAD_PHASE_RADIUS_KM,
    horizon_seconds: int = CONJUNCTION_HORIZON,
    step_seconds: int = DEFAULT_CONJUNCTION_STEP,
) -> List[dict]:
    if not satellites or not debris:
        return []

    tree = build_debris_octree(debris)
    candidate_pairs = broad_phase_candidates(satellites, tree, broad_phase_radius_km)

    warnings: List[dict] = []
    for sat, debris_obj in candidate_pairs:
        tca = find_tca(sat.state_vector, debris_obj.state_vector, horizon_seconds, step_seconds)
        rel_speed = float(np.linalg.norm(np.asarray(tca["approach_vector_km_s"])))
        pc = estimate_collision_probability(float(tca["miss_distance_km"]), rel_speed)
        if tca["miss_distance_km"] <= warning_distance_km:
            warnings.append(
                {
                    "satellite_id": sat.object_id,
                    "debris_id": debris_obj.object_id,
                    "miss_distance_km": tca["miss_distance_km"],
                    "tca_seconds": tca["tca_seconds"],
                    "collision_probability": pc,
                    "risk_level": "CRITICAL" if pc >= 0.7 else "WARNING" if pc >= 0.2 else "WATCH",
                    "approach_vector_km_s": np.asarray(tca["approach_vector_km_s"]).tolist(),
                    "relative_position_km": np.asarray(tca["relative_position_km"]).tolist(),
                }
            )

    warnings.sort(key=lambda w: (-float(w.get("collision_probability", 0.0)), w["miss_distance_km"], w["tca_seconds"]))
    return warnings
