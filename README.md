# Project AETHER

Project AETHER is an autonomous collision-management simulation platform for LEO constellations. It combines a FastAPI backend, a physics/conjunction engine, an ACM decision layer, and a high-performance Canvas dashboard.

## Architecture

- Backend: FastAPI + NumPy
- Physics: RK4 + J2 perturbation, conjunction broad/narrow phase, RTN maneuver planning, fuel model
- Core: ACM decision engine, scheduler (signal delay/cooldown), station-keeping monitor
- Frontend: Orbital Insight dashboard with 4 panels and 2-second polling

## Run Locally

```bash
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000`.

## Docker

```bash
docker build -t project-aether .
docker run --rm -p 8000:8000 project-aether
```

## API

- `POST /api/telemetry`
  - Ingests satellite and debris state vectors
  - Triggers initial ACM conjunction screening
- `POST /api/maneuver/schedule`
  - Validates and queues maneuvers (signal delay + cooldown)
- `POST /api/simulate/step`
  - Propagates all objects, executes due maneuvers, runs ACM cycle
- `GET /api/visualization/snapshot`
  - Returns frontend-optimized snapshot payload

## Key Constraints Implemented

- 10-second signal delay enforced in scheduler
- 600-second cooldown enforced per satellite
- Debris never maneuvers
- Maneuver planning in RTN, converted to ECI for execution
- Dynamic fuel mass tracking via Tsiolkovsky equation
- Critical-fuel graveyard trigger behavior

## Testing

```bash
pytest -q
```

Includes unit tests for physics modules and integration tests for:

- telemetry -> conjunction -> maneuver -> simulation flow
- fuel depletion behavior
- station-keeping and blackout stability
- EOL/graveyard logic
- stress case: 50 satellites + 10,000 debris

## Logging

Structured JSON logging is configured in `backend/utils/logging_config.py` and emitted to stdout for grading/inspection.
