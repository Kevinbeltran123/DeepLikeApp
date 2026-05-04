"""Agent 1 of the multi-agent pipeline: language detection.

Uses langdetect statistically — no LLM call. This deliberately mirrors the
pipeline mode's first step. The point of the multi-agent comparison is the
ROLE separation, not making every step LLM-powered.
"""

from app.domain.languages import LANGUAGES, english_name
from app.infrastructure.detection.language_detector import detect_language_code

from .base import AgentResult


class DetectorAgent:
    name = "detector"
    icon = "search"
    description = "Detecta el idioma del texto de entrada"

    def run(self, text: str) -> AgentResult:
        code = detect_language_code(text)
        display = LANGUAGES[code].display if code in LANGUAGES else code
        return AgentResult(
            agent=self.name,
            output=english_name(code),
            metadata={"code": code, "display": display},
        )
