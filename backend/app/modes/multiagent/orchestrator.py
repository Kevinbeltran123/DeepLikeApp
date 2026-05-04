"""Orchestrator for the multi-agent translator.

Coordinates the four specialized agents in sequence:
    Detector -> Terminologist -> Translator -> Reviewer

Each step emits SSE events so the frontend can render the pipeline as it
executes. The orchestrator is fully deterministic — unlike the mono-agent,
the order of agents is fixed in code.
"""

import json
from typing import Any, AsyncIterator

from app.config import get_settings
from app.domain.languages import LANGUAGES, english_name

from .agents.detector_agent import DetectorAgent
from .agents.reviewer_agent import ReviewerAgent
from .agents.terminology_agent import TerminologyAgent
from .agents.translator_agent import TranslatorAgent


def _sse(data: dict[str, Any]) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


class TranslationOrchestrator:
    def __init__(self) -> None:
        self.detector = DetectorAgent()
        self.terminology = TerminologyAgent()
        self.translator = TranslatorAgent()
        self.reviewer = ReviewerAgent()

    async def run(self, text: str, target_lang_code: str) -> AsyncIterator[str]:
        target_lang = english_name(target_lang_code)

        yield _sse({"type": "agent_start", "agent": "orchestrator", "icon": "spark",
                    "message": "Iniciando pipeline multi-agente..."})

        # Step 1 — Detector
        yield _sse({"type": "agent_start", "agent": self.detector.name,
                    "icon": self.detector.icon, "message": "Detectando idioma..."})
        det = self.detector.run(text)
        source_lang = det.output
        yield _sse({"type": "agent_done", "agent": self.detector.name,
                    "icon": self.detector.icon,
                    "result": f"Idioma detectado: {det.metadata.get('display', source_lang)}",
                    "metadata": det.metadata})

        # Short-circuit when source equals target
        if det.metadata.get("code") == target_lang_code:
            yield _sse({"type": "final", "translation": text,
                        "metadata": {"source": source_lang, "target": target_lang,
                                     "skipped": True, "reason": "source equals target"}})
            yield "data: [DONE]\n\n"
            return

        # Step 2 — Terminologist
        yield _sse({"type": "agent_start", "agent": self.terminology.name,
                    "icon": self.terminology.icon,
                    "message": "Analizando dominio y terminologia..."})
        term = self.terminology.run(text)
        domain = term.metadata.get("domain", "general")
        yield _sse({"type": "agent_done", "agent": self.terminology.name,
                    "icon": self.terminology.icon,
                    "result": f"Dominio: {domain} -- {term.output[:120]}",
                    "metadata": term.metadata})

        # Step 3 — Translator
        yield _sse({"type": "agent_start", "agent": self.translator.name,
                    "icon": self.translator.icon,
                    "message": f"Traduciendo {source_lang} -> {target_lang}..."})
        try:
            trans = await self.translator.run(text, source_lang, target_lang, term.output)
        except Exception as exc:
            yield _sse({"type": "error", "message": f"Translator agent failed: {exc}"})
            yield "data: [DONE]\n\n"
            return
        preview = trans.output if len(trans.output) <= 200 else trans.output[:200] + "..."
        yield _sse({"type": "agent_done", "agent": self.translator.name,
                    "icon": self.translator.icon, "result": preview,
                    "metadata": trans.metadata})

        # Step 4 — Reviewer
        yield _sse({"type": "agent_start", "agent": self.reviewer.name,
                    "icon": self.reviewer.icon,
                    "message": "Revisando calidad y fidelidad..."})
        try:
            rev = await self.reviewer.run(text, trans.output, source_lang, target_lang)
        except Exception as exc:
            yield _sse({"type": "error", "message": f"Reviewer agent failed: {exc}"})
            yield "data: [DONE]\n\n"
            return
        yield _sse({"type": "agent_done", "agent": self.reviewer.name,
                    "icon": self.reviewer.icon,
                    "result": f"Revision completada -- ratio: {rev.metadata.get('length_ratio', '?')}",
                    "metadata": rev.metadata})

        # Final result
        yield _sse({"type": "final", "translation": rev.output,
                    "metadata": {"source": source_lang, "target": target_lang,
                                 "domain": domain, "review_status": rev.metadata.get("status"),
                                 "model": get_settings().llm_model}})
        yield "data: [DONE]\n\n"
