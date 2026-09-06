"""
Studio Head Agent

The executive decision-maker: synthesizes the Location Scout and Logistics
outputs into a single risk verdict, concrete recommendations, and an
estimated cost impact. This is the agent whose output drives the dashboard's
traffic-light system and proactive alerts.
"""

from __future__ import annotations
from app.agents.gemini_client import get_gemini_client
from app.models import (
    EquipmentAvailability,
    LocationAssessment,
    RiskLevel,
    Scene,
    StudioHeadDecision,
)

SYSTEM_INSTRUCTION = """You are a studio production executive reviewing risk
signals for a scene. Given the location assessment and logistics assessment,
write 2-4 concrete, actionable recommendations and estimate the additional
cost impact in USD if the risks materialize. Return ONLY JSON of this shape:

{
  "recommendations": ["..."],
  "cost_impact": "$<amount> additional"
}
"""

_RISK_ORDER = {RiskLevel.LOW: 0, RiskLevel.MEDIUM: 1, RiskLevel.HIGH: 2}
_BASE_COST_BY_RISK = {RiskLevel.LOW: "$0", RiskLevel.MEDIUM: "$4,000 additional", RiskLevel.HIGH: "$12,500 additional"}


def _combine_risk(location: LocationAssessment, logistics: EquipmentAvailability) -> RiskLevel:
    worst = max(_RISK_ORDER[location.weather_risk], _RISK_ORDER[logistics.overall_risk])
    return {v: k for k, v in _RISK_ORDER.items()}[worst]


class StudioHeadAgent:
    def decide(
        self, scene: Scene, location: LocationAssessment, logistics: EquipmentAvailability
    ) -> StudioHeadDecision:
        overall_risk = _combine_risk(location, logistics)

        fallback_recs = []
        if location.weather_risk != RiskLevel.LOW:
            alt = location.alternative_dates[0] if location.alternative_dates else "a later date"
            fallback_recs.append(f"Reschedule scene {scene.id} to {alt} due to {location.weather_forecast}")
        for item, status in logistics.availability.items():
            if status not in ("available",):
                fallback_recs.append(f"Secure a backup for '{item}' ({status})")
        if not logistics.crew_available:
            fallback_recs.append("Resolve crew scheduling conflicts before the shoot date")
        if not fallback_recs:
            fallback_recs.append("No action needed — proceed as scheduled")

        fallback = {
            "recommendations": fallback_recs,
            "cost_impact": _BASE_COST_BY_RISK[overall_risk],
        }

        payload = {
            "scene": scene.model_dump(),
            "location": location.model_dump(),
            "logistics": logistics.model_dump(),
        }
        result = get_gemini_client().generate_json(
            SYSTEM_INSTRUCTION, str(payload), fallback
        )

        return StudioHeadDecision(
            scene_id=scene.id,
            overall_risk=overall_risk,
            recommendations=result.get("recommendations", fallback_recs),
            cost_impact=result.get("cost_impact", fallback["cost_impact"]),
            action_required=overall_risk != RiskLevel.LOW,
        )
