from __future__ import annotations

import csv
import io
import numpy as np
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from backend.core.runtime import runtime
from backend.core.scheduler import ScheduledManeuver
from backend.models.schemas import ManeuverScheduleRequest, ManeuverScheduleResponse

router = APIRouter(prefix="/api", tags=["maneuver"])


@router.post("/maneuver/schedule", response_model=ManeuverScheduleResponse)
def schedule_maneuvers(payload: ManeuverScheduleRequest) -> ManeuverScheduleResponse:
    accepted = 0
    rejected = 0
    reasons = []
    now = runtime.state.simulation_time

    for item in payload.maneuvers:
        sat = runtime.state.satellites.get(item.satellite_id)
        if sat is None:
            rejected += 1
            reasons.append(f"{item.satellite_id}: unknown satellite")
            continue

        maneuver = ScheduledManeuver(
            satellite_id=item.satellite_id,
            execute_at=item.execute_at,
            dv_eci_km_s=np.asarray(item.dv_eci_km_s, dtype=float),
            maneuver_type=item.maneuver_type,
        )
        ok, reason = runtime.scheduler.schedule(maneuver, now)
        if ok:
            accepted += 1
        else:
            rejected += 1
            reasons.append(f"{item.satellite_id}: {reason}")

    return ManeuverScheduleResponse(accepted=accepted, rejected=rejected, reasons=reasons, export_url="/api/maneuver/export.csv")


@router.get("/maneuver/export.csv")
def export_maneuvers_csv() -> StreamingResponse:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["satellite_id", "execute_at", "maneuver_type", "dv_x_km_s", "dv_y_km_s", "dv_z_km_s"])
    for maneuver in runtime.scheduler.queue:
        writer.writerow(
            [
                maneuver.satellite_id,
                maneuver.execute_at,
                maneuver.maneuver_type,
                float(maneuver.dv_eci_km_s[0]),
                float(maneuver.dv_eci_km_s[1]),
                float(maneuver.dv_eci_km_s[2]),
            ]
        )
    buffer.seek(0)
    return StreamingResponse(iter([buffer.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=maneuvers.csv"})
