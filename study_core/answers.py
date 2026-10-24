"""Conservative answer matching for language-study cards.

Only explicitly provided alternatives are accepted.  This deliberately avoids
fuzzy matching, automatic translation, or silently forgiving missing words.
"""

import re
import unicodedata
from collections.abc import Iterable
from typing import Literal

Language = Literal["en", "zh", "pinyin"]
SUPPORTED_LANGUAGES = frozenset({"en", "zh", "pinyin"})
_HAN_ONLY_WITH_SPACES = re.compile(r"[\u3400-\u9fff\s]+\Z")
_FINAL_PUNCTUATION = re.compile(r"[.!?。！？]+\Z")


def normalize_answer(value: str, language: Language = "en") -> str:
    """Normalize superficial differences without erasing meaningful errors.

    * All modes: normalize Unicode width, whitespace, terminal sentence
      punctuation, and typographic apostrophes.
    * English: compare case-insensitively, retaining articles and word order.
    * Chinese: ignore optional spaces if the entire answer consists of Hanzi.
    * Pinyin: compare case-insensitively but *preserve tone marks and numbers*.

    This does not translate, convert Traditional to Simplified, or make
    pinyin tone-number and tone-mark spellings equivalent.
    """
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language: {language!r}")
    if not isinstance(value, str):
        raise TypeError("Answer must be a string")

    text = unicodedata.normalize("NFKC", value).strip()
    text = text.replace("’", "'").replace("‘", "'")
    text = " ".join(text.split())
    text = _FINAL_PUNCTUATION.sub("", text).strip()

    if language == "zh" and _HAN_ONLY_WITH_SPACES.fullmatch(text):
        text = "".join(text.split())
    return text.casefold()


def answer_matches(
    response: str,
    accepted_answers: Iterable[str],
    language: Language = "en",
) -> bool:
    """Return True if response equals one of the explicitly accepted answers.

    Supply accepted_answers as a collection, e.g. ["hello", "hi"], not a
    single pipe/comma-delimited string.  Empty reference answers are rejected.
    """
    if isinstance(accepted_answers, str):
        raise TypeError("accepted_answers must be a collection of strings")

    normalized = {normalize_answer(item, language) for item in accepted_answers}
    normalized.discard("")
    if not normalized:
        raise ValueError("At least one nonempty accepted answer is required")

    guess = normalize_answer(response, language)
    return bool(guess) and guess in normalized
