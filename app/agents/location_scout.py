"""
Location Scout Agent

Given a scene, proposes a real-world filming location and checks weather
risk for the planned shoot date using the free Open-Meteo API (no key
required) so the risk signal is genuinely live rather than fabricated.
"""

from __future__ import annotations
import logging
import httpx

from app.agents.gemini_client import get_gemini_client
from app.models import LocationAssessment, RiskLevel, Scene

logger = logging.getLogger("location_scout")

SYSTEM_INSTRUCTION = """You are a film location scout. Given a scene
description, suggest one plausible real-world filming location, whether a
permit is likely required, and its status. Return ONLY JSON of this shape:

{
  "location_found": "<venue, city>",
  "permit_required": true,
  "permit_status": "pending" | "approved" | "not_required",
  "latitude": <float>,
  "longitude": <float>
}
"""

RAIN_KEYWORDS = ("warehouse", "exterior", "ext", "outdoor", "street", "forest", "beach")


def _fetch_weather_risk(lat: float, lon: float, target_date: str) -> tuple[str, str]:
    """Returns (forecast_summary, risk_level) using Open-Meteo's free forecast API."""
    try:
        resp = httpx.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "daily": "precipitation_probability_max,weathercode",
                "start_date": target_date,
                "end_date": target_date,
                "timezone": "auto",
            },
            timeout=10.0,
        )
        resp.raise_for_status()
        data = resp.json()
        prob = data["daily"]["precipitation_probability_max"][0]
        if prob >= 60:
            return f"rain_expected ({prob}% chance)", RiskLevel.HIGH
        if prob >= 30:
            return f"possible_showers ({prob}% chance)", RiskLevel.MEDIUM
        return f"clear ({prob}% chance rain)", RiskLevel.LOW
    except Exception as exc:  # pragma: no cover
        logger.warning("Weather lookup failed, defaulting to MEDIUM risk: %s", exc)
        return "forecast_unavailable", RiskLevel.MEDIUM


class LocationScoutAgent:
    def assess(self, scene: Scene, shoot_date: str) -> LocationAssessment:
        fallback = {
            "location_found": f"Generic set matching '{scene.location}'",
            "permit_required": any(k in scene.location.lower() for k in RAIN_KEYWORDS),
            "permit_status": "pending",
            "latitude": 34.0522,
            "longitude": -118.2437,  # default: Los Angeles
        }
        result = get_gemini_client().generate_json(
            SYSTEM_INSTRUCTION, scene.model_dump_json(), fallback
        )

        lat = result.get("latitude", fallback["latitude"])
        lon = result.get("longitude", fallback["longitude"])
        forecast, weather_risk = _fetch_weather_risk(lat, lon, shoot_date)

        alt_dates = []
        if weather_risk != RiskLevel.LOW:
            from datetime import date, timedelta
            base = date.fromisoformat(shoot_date)
            alt_dates = [(base + timedelta(days=d)).isoformat() for d in (3, 4)]

        return LocationAssessment(
            scene_id=scene.id,
            location_found=result.get("location_found", fallback["location_found"]),
            permit_required=result.get("permit_required", fallback["permit_required"]),
            permit_status=result.get("permit_status", fallback["permit_status"]),
            weather_forecast=forecast,
            weather_risk=weather_risk,
            alternative_dates=alt_dates,
        )
