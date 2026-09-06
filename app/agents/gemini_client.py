"""
Shared helper for calling the Gemini API with a strict "JSON-only" contract.

Each agent gives this a system instruction + user content and gets back a
parsed dict. Centralizing this keeps prompt-formatting and error handling
consistent across all four agents.
"""

from __future__ import annotations
import json
import logging
import google.generativeai as genai

from app.config import get_settings

logger = logging.getLogger("gemini_client")


class GeminiJSONClient:
    def __init__(self):
        settings = get_settings()
        if settings.gemini_api_key:
            genai.configure(api_key=settings.gemini_api_key)
        self.model_name = settings.gemini_model
        self._enabled = bool(settings.gemini_api_key)

    def generate_json(self, system_instruction: str, user_content: str, fallback: dict) -> dict:
        """
        Calls Gemini with a system instruction that demands raw JSON output.
        Falls back to a caller-supplied default if the API key isn't
        configured or the call/parsing fails, so the demo still runs without
        live credentials.
        """
        if not self._enabled:
            logger.warning("GEMINI_API_KEY not set — returning fallback output.")
            return fallback

        try:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_instruction,
            )
            response = model.generate_content(
                user_content,
                generation_config={"response_mime_type": "application/json"},
            )
            return json.loads(response.text)
        except Exception as exc:  # pragma: no cover
            logger.error("Gemini call failed, using fallback: %s", exc)
            return fallback


_client: GeminiJSONClient | None = None


def get_gemini_client() -> GeminiJSONClient:
    global _client
    if _client is None:
        _client = GeminiJSONClient()
    return _client
