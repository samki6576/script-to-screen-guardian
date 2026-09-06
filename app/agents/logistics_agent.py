"""
Logistics & Gear Agent

Determines what equipment a scene needs (via Gemini) and checks real
availability against the ClickHouse `equipment_inventory` and
`crew_schedules` tables — this is the ClickHouse partner-integration piece.
"""

from __future__ import annotations
import logging

from app.agents.gemini_client import get_gemini_client
from app.database.clickhouse_client import get_clickhouse_client
from app.models import EquipmentAvailability, RiskLevel, Scene

logger = logging.getLogger("logistics_agent")

SYSTEM_INSTRUCTION = """You are a film logistics coordinator. Given a scene's
props and special requirements, list the physical equipment needed to shoot
it. Return ONLY JSON of this shape:

{
  "equipment_needed": ["ARRI_Alexa", "lighting_kit", "..."]
}
"""

DEFAULT_EQUIPMENT = ["ARRI_Alexa", "lighting_kit"]
REQUIREMENT_EQUIPMENT_MAP = {
    "rain_effect": "rain_machine",
    "crash_sound": "foley_kit",
    "stunt": "stunt_rigging",
    "night_shoot": "generator_lighting",
}


class LogisticsAgent:
    def assess(self, scene: Scene, shoot_date: str) -> EquipmentAvailability:
        fallback_equipment = list(DEFAULT_EQUIPMENT)
        for req in scene.special_requirements:
            mapped = REQUIREMENT_EQUIPMENT_MAP.get(req)
            if mapped:
                fallback_equipment.append(mapped)

        result = get_gemini_client().generate_json(
            SYSTEM_INSTRUCTION,
            scene.model_dump_json(),
            {"equipment_needed": fallback_equipment},
        )
        equipment_needed = result.get("equipment_needed", fallback_equipment)

        try:
            ch = get_clickhouse_client()
            availability = ch.get_equipment_availability(equipment_needed)
            crew_conflicts = ch.get_crew_conflicts(shoot_date)
            crew_available = len(crew_conflicts) == 0
        except Exception as exc:  # pragma: no cover
            logger.warning("ClickHouse unavailable, using offline demo data: %s", exc)
            availability = {item: "available" for item in equipment_needed}
            # Simulate one known conflict so the demo still shows a real signal.
            if "rain_machine" in equipment_needed:
                availability["rain_machine"] = "maintenance_scheduled"
            crew_available = True

        unavailable_count = sum(
            1 for status in availability.values() if status not in ("available",)
        )
        if unavailable_count >= 2 or not crew_available:
            overall_risk = RiskLevel.HIGH
        elif unavailable_count == 1:
            overall_risk = RiskLevel.MEDIUM
        else:
            overall_risk = RiskLevel.LOW

        return EquipmentAvailability(
            equipment_needed=equipment_needed,
            availability=availability,
            crew_available=crew_available,
            overall_risk=overall_risk,
        )
