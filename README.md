# Project AETHER

Project AETHER is an autonomous collision-management simulation platform for Low Earth Orbit (LEO) constellations. It combines orbital propagation, conjunction detection, autonomous collision avoidance, fuel-aware scheduling, and a live web dashboard.

## Table of Contents

- [Overview](#overview)
- [Core Features](#core-features)
- [Repository Structure](#repository-structure)
- [Technology Stack](#technology-stack)
- [Quick Start](#quick-start)
- [Run with Docker](#run-with-docker)
- [Run with Docker Compose](#run-with-docker-compose)
- [Run Locally (Python)](#run-locally-python)
- [API Endpoints](#api-endpoints)
- [Testing](#testing)
- [Configuration and Constraints](#configuration-and-constraints)
- [Troubleshooting](#troubleshooting)

## Overview

The platform models and manages conjunction risk in near-real time by:

- Propagating object states using vectorized RK4 integration with J2 perturbations
- Detecting close approaches through broad-phase and narrow-phase screening
- Scheduling autonomous evasion and recovery burns under operational constraints
- Tracking fuel usage through a Tsiolkovsky-style propellant model
- Visualizing current orbital state and risk events in a browser dashboard

## Core Features

- Autonomous Collision Management (ACM) decision loop
- Scheduler with command delay and burn cooldown handling
- Station-keeping monitoring and correction hooks
- Ground-station aware telemetry/runtime context
- Frontend dashboard with ground track, bullseye view, telemetry, and maneuver timeline
- Test suite covering propagation, conjunction logic, maneuver logic, and integration flows

## Repository Structure

```text
project-aether/
  backend/
    core/         # ACM loop, runtime state, scheduler, station-keeping
    data/         # Static datasets (ground stations)
    models/       # Request/response schemas and state models
    physics/      # Propagation, conjunction, maneuver, fuel, transforms
    routes/       # FastAPI route handlers
    utils/        # Logging and shared utilities
    main.py       # FastAPI application entrypoint
  frontend/
    css/          # Dashboard styles
    js/           # Rendering, API polling, charts
    index.html    # Dashboard shell
  tests/          # Unit and integration tests
  Dockerfile      # Container image definition
  requirements.txt
```

## Technology Stack

- Backend: FastAPI, NumPy
- Frontend: HTML5 Canvas, vanilla JavaScript
- Testing: pytest
- Packaging: Docker

## Quick Start

Choose one of the following:

1. Run with Docker (recommended for reproducibility)
2. Run locally with Python

Then open http://localhost:8000 and use the dashboard to inspect telemetry, risk events, and maneuver activity.

## Run with Docker

From the repository root:

```bash
docker build -t project-aether .
docker run --rm -p 8000:8000 --name project-aether project-aether
```

Validate service health:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok"}
```

## Run with Docker Compose

From the repository root:

```bash
docker compose up --build
```

To run in detached mode:

```bash
docker compose up --build -d
```

To stop:

```bash
docker compose down
```

## Run Locally (Python)

### Prerequisites

- Python 3.11+
- pip

### Setup and Launch

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

- `GET /health`
  - Liveness probe for service status
- `POST /api/telemetry`
  - Ingests satellites and debris states into runtime context
- `POST /api/simulate/step`
  - Advances the simulation by one step and runs ACM checks
- `POST /api/maneuver/schedule`
  - Validates and queues maneuvers with delay/cooldown constraints
- `GET /api/visualization/snapshot`
  - Returns frontend-ready simulation state

## Testing

Run all tests:

```bash
pytest -q
```

Targeted runs:

```bash
pytest tests/test_propagator.py -q
pytest tests/test_conjunction.py -q
pytest tests/test_integration.py -q
```

## Configuration and Constraints

The current implementation enforces key operational policies such as:

- Signal delay before maneuver execution
- Per-satellite maneuver cooldown windows
- Fuel-aware burn planning and depletion tracking
- Critical-distance-driven avoidance behavior
- Autonomous handling of repeated or conflicting warnings

Tune constants in backend configuration and core modules to adapt to mission profiles.

## Troubleshooting

- Port already in use:
  - Launch on a different host port, for example `-p 8080:8000`
- Dashboard loads but no dynamics:
  - Check telemetry ingestion and simulate-step calls
- Import errors locally:
  - Confirm virtual environment activation and dependency installation
- Docker build fails on network-restricted environments:
  - Retry with network access or a mirror for package installation

## License

This repository is intended for hackathon/demo use.
