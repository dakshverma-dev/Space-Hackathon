from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

import numpy as np

from backend.config import COOLDOWN_PERIOD, SIGNAL_DELAY


@dataclass
class ScheduledManeuver:
    satellite_id: str
    execute_at: float
    dv_eci_km_s: np.ndarray
    maneuver_type: str


@dataclass
class ManeuverScheduler:
    queue: List[ScheduledManeuver] = field(default_factory=list)
    last_burn_time: Dict[str, float] = field(default_factory=dict)

    def validate_schedule_time(self, now: float, execute_at: float) -> Tuple[bool, str]:
        if execute_at < now + SIGNAL_DELAY:
            return False, "Signal delay violation"
        return True, ""

    def validate_cooldown(self, satellite_id: str, execute_at: float) -> Tuple[bool, str]:
        last = self.last_burn_time.get(satellite_id)
        if last is not None and execute_at - last < COOLDOWN_PERIOD:
            return False, "Cooldown violation"
        return True, ""

    def schedule(self, maneuver: ScheduledManeuver, now: float) -> Tuple[bool, str]:
        valid_time, reason = self.validate_schedule_time(now, maneuver.execute_at)
        if not valid_time:
            return False, reason
        valid_cd, reason = self.validate_cooldown(maneuver.satellite_id, maneuver.execute_at)
        if not valid_cd:
            return False, reason
        self.queue.append(maneuver)
        self.queue.sort(key=lambda m: m.execute_at)
        return True, ""

    def pop_due(self, now: float) -> List[ScheduledManeuver]:
        due = [m for m in self.queue if m.execute_at <= now]
        self.queue = [m for m in self.queue if m.execute_at > now]
        for m in due:
            self.last_burn_time[m.satellite_id] = now
        return due
