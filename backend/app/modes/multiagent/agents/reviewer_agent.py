"""Agent 4 of the multi-agent pipeline: quality reviewer.

Two-stage review:
  1. Cheap heuristics (length ratio, identical-to-original) reject obvious junk
     without burning a model call.
  2. If the heuristics pass, Qwen re-reads the translation and returns either
     the same text or an improved version.

A sanity check on the reviewer's output prevents the model from deciding to
"explain" the translation instead of returning it.
"""

import asyncio

from langchain.schema import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from app.config import get_settings

from .base import AgentResult


# TODO(student): these thresholds determine when the reviewer flags a translation
# as suspicious without invoking the LLM. They are intentionally conservative.
# Lower _MIN_LENGTH_RATIO if you translate to dense languages (Chinese, Japanese);
# raise _MAX_LENGTH_RATIO if you translate from them.
_MIN_LENGTH_RATIO = 0.15
_MAX_LENGTH_RATIO = 6.0


class ReviewerAgent:
    name = "revisor"
    icon = "check"
    description = "Verifica calidad, tono y fidelidad"

    def __init__(self) -> None:
        settings = get_settings()
        # Lower temperature — the reviewer should be deterministic.
        self.llm = ChatOllama(
            model=settings.llm_model,
            base_url=settings.ollama_base_url,
            temperature=0.05,
        )

    async def run(
        self,
        original: str,
        translation: str,
        source_lang: str,
        target_lang: str,
    ) -> AgentResult:
        ratio = len(translation) / max(len(original), 1)

        if translation.strip() == original.strip():
            return AgentResult(
                agent=self.name,
                output=translation,
                metadata={"status": "warning", "issue": "identical to original",
                          "length_ratio": round(ratio, 2)},
            )
        if ratio < _MIN_LENGTH_RATIO or ratio > _MAX_LENGTH_RATIO:
            return AgentResult(
                agent=self.name,
                output=translation,
                metadata={"status": "warning", "issue": f"unusual length ratio {ratio:.2f}",
                          "length_ratio": round(ratio, 2)},
            )

        system = (
            "You are a professional translation quality reviewer.\n"
            "Your job: review a translation and return an improved version if needed.\n"
            "Return ONLY the final translation text -- no comments, no explanations."
        )
        prompt = (
            f"Original ({source_lang}):\n{original}\n\n"
            f"Translation ({target_lang}):\n{translation}\n\n"
            f"Review the translation for:\n"
            f"1. Accuracy -- does it convey the same meaning?\n"
            f"2. Fluency -- does it sound natural in {target_lang}?\n"
            f"3. Register -- is the tone appropriate?\n\n"
            f"If the translation is good, return it as-is.\n"
            f"If it needs improvement, return the corrected version."
        )

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.llm.invoke([SystemMessage(content=system), HumanMessage(content=prompt)]),
        )
        reviewed = response.content.strip()

        # Sanity check: if the reviewer's output is wildly different in length,
        # assume it explained instead of translating and revert to the original
        # translation.
        rev_ratio = len(reviewed) / max(len(translation), 1)
        if rev_ratio < 0.3 or rev_ratio > 3.0:
            reviewed = translation

        return AgentResult(
            agent=self.name,
            output=reviewed,
            metadata={"status": "ok", "length_ratio": round(ratio, 2)},
        )
