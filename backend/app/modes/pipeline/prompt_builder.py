"""Prompt template for the pipeline translator.

The prompt is intentionally direct — pipeline mode has no agent loop, no tools,
no quality check. Everything that controls translation behavior lives here.
"""

from app.domain.languages import english_name


_TEMPLATE = """You are an expert professional translator specializing in accurate, natural-sounding translations.

Translate the following {source_name} text into {target_name}.

Rules:
- Return ONLY the translated text. No explanations, no notes, no quotes.
- Preserve all formatting, line breaks, and punctuation exactly.
- Maintain the tone and register of the original (formal/informal).
- Keep proper nouns, brand names, and technical terms unless a standard translation exists.

Text:
{text}

Translation:"""


def build_translation_prompt(text: str, source_code: str, target_code: str) -> str:
    return _TEMPLATE.format(
        source_name=english_name(source_code),
        target_name=english_name(target_code),
        text=text,
    )
