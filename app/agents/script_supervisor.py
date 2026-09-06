"""
Script Supervisor Agent

Reads raw script text and extracts a structured breakdown per scene:
location, props, atmosphere, characters, and special production
requirements (weather effects, stunts, sound cues, etc).
"""

from __future__ import annotations
from app.agents.gemini_client import get_gemini_client
from app.models import Scene, ScriptAnalysis

SYSTEM_INSTRUCTION = """You are a professional script supervisor breaking down a
screenplay for production planning. Given raw script text, extract every scene
and return ONLY a JSON object of this exact shape, no markdown fences, no prose:

{
  "scenes": [
    {
      "id": "SCENE_<number>",
      "location": "<INT/EXT description>",
      "props": ["..."],
      "atmosphere": "<mood/lighting/weather cues>",
      "characters": ["..."],
      "special_requirements": ["<e.g. rain_effect, stunt, night_shoot>"]
    }
  ]
}
"""


def _naive_fallback_parse(script_text: str) -> dict:
    """
    Deterministic, dependency-free scene splitter used when no Gemini API key
    is configured. Splits on lines that look like sluglines
    (INT./EXT. ... - DAY/NIGHT) so the rest of the pipeline still has
    something to work with in an offline demo.
    """
    import re

    lines = script_text.splitlines()
    scenes = []
    current = None
    scene_num = 0
    # Matches sluglines anywhere in the line, e.g. "INT. OFFICE - DAY" or
    # "SCENE 12 - EXT. WAREHOUSE - DAY".
    slugline_re = re.compile(r"\b(INT|EXT|INT/EXT|I/E)\.\s")

    def flush():
        if current is not None:
            scenes.append(current)

    for line in lines:
        stripped = line.strip()
        if slugline_re.search(stripped.upper()):
            flush()
            scene_num += 1
            current = {
                "id": f"SCENE_{scene_num}",
                "location": stripped,
                "props": [],
                "atmosphere": None,
                "characters": [],
                "special_requirements": [],
            }
        elif current is not None and stripped:
            # crude character-name detection: ALL CAPS short line
            if stripped.isupper() and len(stripped.split()) <= 4:
                name = stripped.split("(")[0].strip()
                if name not in current["characters"]:
                    current["characters"].append(name)
            for keyword, tag in (
                ("rain", "rain_effect"),
                ("crash", "crash_sound"),
                ("stunt", "stunt"),
                ("night", "night_shoot"),
                ("flashlight", None),
            ):
                if keyword in stripped.lower() and tag and tag not in current["special_requirements"]:
                    current["special_requirements"].append(tag)
    flush()
    if not scenes:
        scenes = [{
            "id": "SCENE_1",
            "location": "UNKNOWN",
            "props": [],
            "atmosphere": None,
            "characters": [],
            "special_requirements": [],
        }]
    return {"scenes": scenes}


class ScriptSupervisorAgent:
    def analyze(self, script_text: str) -> ScriptAnalysis:
        fallback = _naive_fallback_parse(script_text)
        result = get_gemini_client().generate_json(
            SYSTEM_INSTRUCTION, script_text, fallback
        )
        scenes = [Scene(**s) for s in result.get("scenes", fallback["scenes"])]
        return ScriptAnalysis(scenes=scenes)
