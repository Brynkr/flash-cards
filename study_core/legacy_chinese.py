"""Read Hanzi alternatives from legacy pinyin + Chinese flashcard fields.

Cards continue to use the repository's existing WORD_DELIMITER.  This adapter
is intentionally narrow: it extracts the Hanzi from each explicit alternative,
then lets the existing strict answer checker decide whether a guess matches.

Pinyin is *not* accepted as a Chinese-character answer.  A separate pinyin
exercise will be implemented later, with its own explicit answer mode.
"""


def _is_hanzi(char: str) -> bool:
    codepoint = ord(char)
    return (
        codepoint == 0x3007  # Ideographic number zero
        or 0x3400 <= codepoint <= 0x9FFF
        or 0xF900 <= codepoint <= 0xFAFF
        or 0x20000 <= codepoint <= 0x2FA1F
        or 0x30000 <= codepoint <= 0x323AF
    )


def extract_hanzi_answers(value: str, delimiter: str) -> list[str]:
    """Return unique, explicitly listed Chinese-character answers.

    Example with delimiter ``||``::

        'nǐ hǎo 你好 || zài jiàn 再见' -> ['你好', '再见']

    Empty entries and translations containing no Hanzi are ignored.  Never
    accept an empty guess or arbitrarily infer synonyms from another entry.
    """
    if not isinstance(value, str) or not isinstance(delimiter, str):
        raise TypeError("value and delimiter must be strings")
    if not delimiter:
        raise ValueError("delimiter must not be empty")

    answers = []
    for entry in value.split(delimiter):
        hanzi = "".join(char for char in entry if _is_hanzi(char))
        if hanzi and hanzi not in answers:
            answers.append(hanzi)
    return answers


def extract_pinyin_answers(value: str, delimiter: str) -> list[str]:
    """Read the non-Hanzi pinyin for each explicitly delimited alternative.

    Does not guess pinyin from Chinese characters or silently change tones.
    """
    if not isinstance(value, str) or not isinstance(delimiter, str):
        raise TypeError("value and delimiter must be strings")
    if not delimiter:
        raise ValueError("delimiter must not be empty")

    answers = []
    for entry in value.split(delimiter):
        # The legacy format is `pinyin 汉字`. Remove Hanzi but retain tone marks.
        pinyin = " ".join("".join(
            " " if _is_hanzi(char) else char for char in entry
        ).split()).strip()
        if pinyin and pinyin not in answers:
            answers.append(pinyin)
    return answers
