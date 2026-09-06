"""
Pydantic models shared across agents, routes, and the orchestrator.
"""

from __future__ import annotations
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Scene(BaseModel):
    id: str
    location: str
    props: list[str] = Field(default_factory=list)
    atmosphere: Optional[str] = None
    characters: list[str] = Field(default_factory=list)
    special_requirements: list[str] = Field(default_factory=list)
    raw_text: Optional[str] = None


class ScriptAnalysis(BaseModel):
    scenes: list[Scene]


class LocationAssessment(BaseModel):
    scene_id: str
    location_found: str
    permit_required: bool
    permit_status: str
    weather_forecast: str
    weather_risk: RiskLevel
    alternative_dates: list[str] = Field(default_factory=list)


class EquipmentAvailability(BaseModel):
    equipment_needed: list[str]
    availability: dict[str, str]
    crew_available: bool
    overall_risk: RiskLevel


class StudioHeadDecision(BaseModel):
    scene_id: str
    overall_risk: RiskLevel
    recommendations: list[str]
    cost_impact: str
    action_required: bool


class ProductionRiskReport(BaseModel):
    scene: Scene
    location: LocationAssessment
    logistics: EquipmentAvailability
    decision: StudioHeadDecision


class ScriptUploadRequest(BaseModel):
    script_text: str
    shoot_start_date: Optional[str] = None


class RescheduleRequest(BaseModel):
    scene_id: str
    proposed_date: str
    reason: str
