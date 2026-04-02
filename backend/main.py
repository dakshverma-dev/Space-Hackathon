from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.core.runtime import load_default_ground_stations
from backend.routes.maneuver import router as maneuver_router
from backend.routes.simulate import router as simulate_router
from backend.routes.telemetry import router as telemetry_router
from backend.routes.visualization import router as visualization_router
from backend.utils.logging_config import configure_logging

configure_logging()
app = FastAPI(title="Project AETHER", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(telemetry_router)
app.include_router(maneuver_router)
app.include_router(simulate_router)
app.include_router(visualization_router)


@app.on_event("startup")
def on_startup() -> None:
    load_default_ground_stations()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


frontend_path = Path(__file__).resolve().parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
