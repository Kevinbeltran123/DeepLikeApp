"""Agent 3 of the multi-agent pipeline: the translator.

Receives the domain hint produced by TerminologyAgent and the source language
detected by DetectorAgent, then asks Qwen for a translation. Returns the raw
result without quality checks — those are the next agent's job.
"""

import asyncio

from langchain.schema import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from app.config import get_settings

from .base import AgentResult


class TranslatorAgent:
    name = "traductor"
    icon = "globe"
    description = "Traduce usando Qwen via Ollama"

    def __init__(self) -> None:
        settings = get_settings()
        self.llm = ChatOllama(
            model=settings.llm_model,
            base_url=settings.ollama_base_url,
            temperature=settings.llm_temperature,
        )

    async def run(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        terminology_hint: str,
    ) -> AgentResult:
        system = (
            f"You are an expert professional translator.\n"
            f"Translate from {source_lang} to {target_lang}.\n"
            f"{terminology_hint}\n"
            f"Rules:\n"
            f"- Return ONLY the translated text, nothing else.\n"
            f"- Preserve all formatting and line breaks.\n"
            f"- Maintain the original tone and register."
        )
        messages = [SystemMessage(content=system), HumanMessage(content=text)]

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: self.llm.invoke(messages))

        return AgentResult(
            agent=self.name,
            output=response.content.strip(),
            metadata={"source": source_lang, "target": target_lang},
        )
