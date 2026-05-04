"""Pipeline translator — fixed sequence: detect -> build prompt -> stream LLM -> emit.

There is no decision logic here. The flow never branches based on model output.
This is what distinguishes the pipeline mode from the agent modes.
"""

import json
from typing import AsyncIterator

from app.config import get_settings
from app.domain.languages import LANGUAGES, english_name
from app.infrastructure.detection.language_detector import detect_language_code
from app.infrastructure.llm.ollama_client import OllamaClient

from .prompt_builder import build_translation_prompt


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


async def stream_translation(
    text: str,
    source_lang: str,
    target_lang: str,
) -> AsyncIterator[str]:
    """Yield SSE-framed events for a single translation request."""
    actual_source = source_lang
    if source_lang == "auto":
        actual_source = detect_language_code(text)

    source_display = LANGUAGES[actual_source].display if actual_source in LANGUAGES else actual_source
    yield _sse({"type": "detected_lang", "code": actual_source, "display": source_display})

    if actual_source == target_lang:
        yield _sse({"type": "token", "content": text})
        yield _sse({
            "type": "final",
            "translation": text,
            "metadata": {"source": actual_source, "target": target_lang, "skipped": True},
        })
        yield "data: [DONE]\n\n"
        return

    prompt = build_translation_prompt(text, actual_source, target_lang)
    settings = get_settings()
    client = OllamaClient()

    accumulated: list[str] = []
    try:
        async for token in client.stream_generate(prompt, temperature=settings.llm_temperature):
            accumulated.append(token)
            yield _sse({"type": "token", "content": token})
    except Exception as exc:
        yield _sse({"type": "error", "message": f"LLM error: {exc}"})
        yield "data: [DONE]\n\n"
        return

    yield _sse({
        "type": "final",
        "translation": "".join(accumulated).strip(),
        "metadata": {
            "source": actual_source,
            "source_name": english_name(actual_source),
            "target": target_lang,
            "target_name": english_name(target_lang),
            "model": settings.llm_model,
        },
    })
    yield "data: [DONE]\n\n"
