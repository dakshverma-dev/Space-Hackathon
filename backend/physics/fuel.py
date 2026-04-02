from __future__ import annotations

import math
from typing import Dict

from backend.config import G0, ISP


def fuel_used_tsiolkovsky(delta_v_m_s: float, initial_mass_kg: float, isp_s: float = ISP) -> float:
    if delta_v_m_s < 0:
        raise ValueError("delta_v_m_s must be >= 0")
    if initial_mass_kg <= 0:
        raise ValueError("initial_mass_kg must be > 0")
    if isp_s <= 0:
        raise ValueError("isp_s must be > 0")

    mass_ratio = math.exp(delta_v_m_s / (isp_s * G0))
    final_mass = initial_mass_kg / mass_ratio
    return initial_mass_kg - final_mass


def apply_burn(
    dry_mass_kg: float,
    fuel_mass_kg: float,
    delta_v_m_s: float,
    isp_s: float = ISP,
) -> Dict[str, float]:
    total_mass = dry_mass_kg + fuel_mass_kg
    required_fuel = fuel_used_tsiolkovsky(delta_v_m_s, total_mass, isp_s)
    used_fuel = min(required_fuel, fuel_mass_kg)
    remaining_fuel = max(fuel_mass_kg - used_fuel, 0.0)

    return {
        "fuel_used_kg": used_fuel,
        "fuel_remaining_kg": remaining_fuel,
        "new_total_mass_kg": dry_mass_kg + remaining_fuel,
    }
