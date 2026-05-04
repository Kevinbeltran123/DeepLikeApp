"""langdetect wrapper that returns ISO codes from our supported language registry.

Uses a fixed seed so detection is deterministic across requests.
Texts under ~20 characters often produce unreliable results — callers should treat
those as a hint, not a hard signal.
"""

from langdetect import DetectorFactory, detect
from langdetect.lang_detect_exception import LangDetectException

from app.domain.languages import LANGUAGES

DetectorFactory.seed = 42

_FALLBACK_CODE = "en"


def detect_language_code(text: str) -> str:
    """Return an ISO code present in the language registry, or English as fallback."""
    try:
        raw = detect(text)
    except LangDetectException:
        return _FALLBACK_CODE

    if raw.startswith("zh"):
        raw = "zh-cn"

    return raw if raw in LANGUAGES else _FALLBACK_CODE
