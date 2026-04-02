from __future__ import annotations

import numpy as np
from fastapi.testclient import TestClient

from backend.config import RE
from backend.main import app
from tests.generate_test_data import generate_telemetry_payload


def _client() -> TestClient:
    return TestClient(app)


def test_full_flow_ingest_detect_schedule_and_step() -> None:
    client = _client()
    payload = {
        "timestamp_seconds": 0,
        "objects": [
            {
                "object_id": "SAT-1",
                "kind": "satellite",
                "state_vector": [RE + 550, 0, 0, 0, 7.6, 0],
                "fuel_mass_kg": 50,
                "dry_mass_kg": 500,
            },
            {
                "object_id": "DEB-1",
                "kind": "debris",
                "state_vector": [RE + 550.2, 0, 0, 0, 7.6, 0],
            },
        ],
    }

    r1 = client.post("/api/telemetry", json=payload)
    assert r1.status_code == 200

    schedule = {
        "maneuvers": [
            {
                "satellite_id": "SAT-1",
                "execute_at": 20,
                "dv_eci_km_s": [0, 0.0005, 0],
                "maneuver_type": "EVASION",
            }
        ]
    }
    r2 = client.post("/api/maneuver/schedule", json=schedule)
    assert r2.status_code == 200

    r3 = client.post("/api/simulate/step", json={"step_seconds": 30})
    assert r3.status_code == 200
    body = r3.json()
    assert "collision_count" in body
    assert "maneuvers_executed" in body


def test_fuel_depletion_tracking_over_multiple_burns() -> None:
    client = _client()
    client.post(
        "/api/telemetry",
        json={
            "timestamp_seconds": 0,
            "objects": [
                {
                    "object_id": "SAT-FUEL",
                    "kind": "satellite",
                    "state_vector": [RE + 550, 0, 0, 0, 7.6, 0],
                    "fuel_mass_kg": 10,
                    "dry_mass_kg": 500,
                }
            ],
        },
    )

    for t in [20, 700, 1400]:
        client.post(
            "/api/maneuver/schedule",
            json={
                "maneuvers": [
                    {
                        "satellite_id": "SAT-FUEL",
                        "execute_at": t,
                        "dv_eci_km_s": [0, 0.001, 0],
                        "maneuver_type": "EVASION",
                    }
                ]
            },
        )
    client.post("/api/simulate/step", json={"step_seconds": 1500})
    snapshot = client.get("/api/visualization/snapshot").json()
    sat = next(s for s in snapshot["satellites"] if s["satellite_id"] == "SAT-FUEL")
    assert sat["fuel_fraction"] < 0.02


def test_station_keeping_recovery_path_exists() -> None:
    client = _client()
    client.post(
        "/api/telemetry",
        json={
            "timestamp_seconds": 0,
            "objects": [
                {
                    "object_id": "SAT-SK",
                    "kind": "satellite",
                    "state_vector": [RE + 700, 0, 0, 0, 7.4, 0],
                }
            ],
        },
    )
    step = client.post("/api/simulate/step", json={"step_seconds": 120}).json()
    assert "warnings" in step


def test_blackout_scenario_endpoint_stability() -> None:
    client = _client()
    payload = generate_telemetry_payload(num_satellites=1, num_debris=20)
    r = client.post("/api/telemetry", json=payload)
    assert r.status_code == 200
    s = client.post("/api/simulate/step", json={"step_seconds": 60})
    assert s.status_code == 200


def test_eol_graveyard_trigger_when_low_fuel() -> None:
    client = _client()
    client.post(
        "/api/telemetry",
        json={
            "timestamp_seconds": 0,
            "objects": [
                {
                    "object_id": "SAT-EOL",
                    "kind": "satellite",
                    "state_vector": [RE + 550, 0, 0, 0, 7.6, 0],
                    "fuel_mass_kg": 1.0,
                    "dry_mass_kg": 500.0,
                }
            ],
        },
    )
    client.post("/api/simulate/step", json={"step_seconds": 30})
    snap = client.get("/api/visualization/snapshot").json()
    assert any(e["type"] == "GRAVEYARD" for e in snap["events"])


def test_stress_50_sat_10000_debris_single_tick() -> None:
    client = _client()
    payload = generate_telemetry_payload(50, 10_000)
    r = client.post("/api/telemetry", json=payload)
    assert r.status_code == 200
    s = client.post("/api/simulate/step", json={"step_seconds": 10})
    assert s.status_code == 200
