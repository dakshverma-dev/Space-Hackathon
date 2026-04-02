from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class TelemetryObject(BaseModel):
    object_id: str
    kind: Literal["satellite", "debris"]
    state_vector: List[float] = Field(min_length=6, max_length=6)
    fuel_mass_kg: Optional[float] = None
    dry_mass_kg: Optional[float] = None


class TelemetryRequest(BaseModel):
    timestamp_seconds: float = 0.0
    objects: List[TelemetryObject]


class TelemetryResponse(BaseModel):
    ack: bool
    cdm_warning_count: int
    warnings: List[Dict]


class ManeuverSegment(BaseModel):
    satellite_id: str
    execute_at: float
    dv_eci_km_s: List[float] = Field(min_length=3, max_length=3)
    maneuver_type: Literal["EVASION", "RECOVERY", "GRAVEYARD"]


class ManeuverScheduleRequest(BaseModel):
    maneuvers: List[ManeuverSegment]


class ManeuverScheduleResponse(BaseModel):
    accepted: int
    rejected: int
    reasons: List[str]
    export_url: Optional[str] = None


class SimulateStepRequest(BaseModel):
    step_seconds: float = Field(gt=0)


class SimulateStepResponse(BaseModel):
    simulation_time: float
    collision_count: int
    maneuvers_executed: int
    warnings: List[Dict]
    conflicts_deconflicted: int = 0


class SatelliteSnapshot(BaseModel):
    satellite_id: str
    lat: float
    lon: float
    alt_km: float
    fuel_fraction: float
    status: str


class VisualizationSnapshotResponse(BaseModel):
    simulation_time: float
    satellites: List[SatelliteSnapshot]
    debris: List[List[float]]
    events: List[Dict]
