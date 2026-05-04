"""Tools available to the ReAct mono-agent.

Each tool has a single, narrow responsibility. The agent reads the docstrings to
decide when to invoke them, so the wording matters: it directly steers the model.
"""

import json

from langchain.tools import tool
from langchain_ollama import ChatOllama
from langchain.schema import HumanMessage, SystemMessage

from app.config import get_settings
from app.domain.languages import LANGUAGES
from app.infrastructure.detection.language_detector import detect_language_code


# TODO(student): extend or refine these dictionaries with terms that matter for
# your translation use case. The mono-agent decides whether to call this tool
# based on its docstring, but once called, what it FINDS depends on these lists.
_DOMAIN_TERMS: dict[str, list[str]] = {
    "medical": [
        "diagnosis", "syndrome", "chronic", "acute", "therapy", "dosage",
        "diagnostico", "sindrome", "cronico", "terapia", "dosis",
    ],
    "legal": [
        "hereby", "pursuant", "jurisdiction", "liability", "clause",
        "por medio", "jurisdiccion", "responsabilidad", "clausula",
    ],
    "technical": [
        "algorithm", "bandwidth", "latency", "protocol", "API",
        "algoritmo", "ancho de banda", "protocolo",
    ],
    "financial": [
        "dividend", "equity", "portfolio", "leverage", "hedge",
        "dividendo", "patrimonio", "cartera", "apalancamiento",
    ],
}


@tool
def detect_language(text: str) -> str:
    """Detect the language of a piece of text. Returns the language name in English.
    Always use this as the FIRST step before translating, unless the source language is already known."""
    code = detect_language_code(text)
    lang = LANGUAGES.get(code)
    name = lang.english if lang else "Unknown"
    return f"Detected language: {name} (code: {code})"


@tool
def lookup_technical_terms(text: str) -> str:
    """Scan the text for specialized terminology in known domains
    (medical, legal, technical, financial). Use this BEFORE translating to
    inform the translation. Returns a list of detected terms or a no-match message."""
    text_lower = text.lower()
    found: list[str] = []
    for domain, terms in _DOMAIN_TERMS.items():
        hits = [t for t in terms if t.lower() in text_lower]
        if hits:
            found.append(f"{domain}: {', '.join(hits)}")
    if found:
        return f"Technical terms detected -- {'; '.join(found)}. Preserve these terms carefully."
    return "No specialized technical terms detected. Standard translation applies."


def _parse_json_input(raw: str | dict, required_keys: list[str]) -> dict:
    """LangChain ReAct tools receive a single Action Input string.
    The agent is instructed to format multi-arg tools as a JSON object;
    this helper validates that contract and produces a clear error message
    when the model deviates from it."""
    if isinstance(raw, dict):
        data = raw
    else:
        text = raw.strip()
        if text.startswith("```"):
            text = text.strip("`").strip()
            if text.lower().startswith("json"):
                text = text[4:].strip()
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Tool input must be valid JSON with keys {required_keys}. Got: {raw!r}. "
                f"Parse error: {exc}"
            )
    missing = [k for k in required_keys if k not in data]
    if missing:
        raise ValueError(f"Missing required keys {missing} in tool input. Got: {data}")
    return data


@tool
def translate_text(input: str) -> str:
    """Translate text using the LLM. Input MUST be a JSON object with three keys:
    {"text": "...", "source_language": "Spanish", "target_language": "English"}.
    Use English language names. This is the main translation tool.
    Always run detect_language and lookup_technical_terms first."""
    args = _parse_json_input(input, ["text", "source_language", "target_language"])
    settings = get_settings()
    llm = ChatOllama(
        model=settings.llm_model,
        base_url=settings.ollama_base_url,
        temperature=settings.llm_temperature,
    )
    system = (
        f"You are an expert professional translator. "
        f"Translate from {args['source_language']} to {args['target_language']}. "
        f"Return ONLY the translated text, no explanations, no quotes, no notes. "
        f"Preserve formatting and line breaks."
    )
    response = llm.invoke([SystemMessage(content=system), HumanMessage(content=str(args["text"]))])
    return response.content.strip()


@tool
def check_translation_quality(input: str) -> str:
    """Check that a translation is plausible. Input MUST be a JSON object with two keys:
    {"original": "...", "translation": "..."}.
    Verifies the translation is non-empty, not identical to the original, and within a
    reasonable length range. Use this AFTER translating to confirm the result."""
    # TODO(student): tune these thresholds. 0.2 and 5.0 are conservative defaults.
    # Languages with high information density (Chinese, Japanese) can produce ratios
    # well outside [0.2, 5.0] without being wrong, so consider per-language ratios.
    args = _parse_json_input(input, ["original", "translation"])
    original, translation = str(args["original"]), str(args["translation"])

    if not translation or not translation.strip():
        return "Quality check FAILED: translation is empty"

    ratio = len(translation) / max(len(original), 1)
    if translation.strip() == original.strip():
        return "Quality check FAILED: translation is identical to original"
    if ratio < 0.2:
        return f"Quality check WARNING: translation suspiciously short (ratio {ratio:.2f})"
    if ratio > 5.0:
        return f"Quality check WARNING: translation suspiciously long (ratio {ratio:.2f})"
    return f"Quality check PASSED: translation looks good (length ratio {ratio:.2f})"
