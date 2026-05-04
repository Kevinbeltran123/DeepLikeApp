"""Registry of supported languages.

Each language has three representations:
- code: ISO code used internally and in API requests (e.g. "es", "zh-cn")
- display: Native name shown in the UI (e.g. "Espanol", "Deutsch")
- english: English name injected into LLM prompts (e.g. "Spanish", "German")
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Language:
    code: str
    display: str
    english: str


LANGUAGES: dict[str, Language] = {
    "es": Language("es", "Espanol", "Spanish"),
    "en": Language("en", "English", "English"),
    "fr": Language("fr", "Francais", "French"),
    "de": Language("de", "Deutsch", "German"),
    "pt": Language("pt", "Portugues", "Portuguese"),
    "it": Language("it", "Italiano", "Italian"),
    "zh-cn": Language("zh-cn", "Chinese", "Chinese"),
    "ja": Language("ja", "Japanese", "Japanese"),
    "ko": Language("ko", "Korean", "Korean"),
    "ru": Language("ru", "Russian", "Russian"),
    "ar": Language("ar", "Arabic", "Arabic"),
    "nl": Language("nl", "Nederlands", "Dutch"),
}


def get_language(code: str) -> Language | None:
    return LANGUAGES.get(code)


def english_name(code: str) -> str:
    lang = LANGUAGES.get(code)
    return lang.english if lang else code


def display_map() -> dict[str, str]:
    return {code: lang.display for code, lang in LANGUAGES.items()}
