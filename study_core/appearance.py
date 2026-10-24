"""Local, accessible background preferences for the Tkinter flashcard app."""

import json
import os
import re
import tempfile
from pathlib import Path

DEFAULT_BACKGROUND = '#F4F6FA'
DEFAULT_BUTTON = '#DEE5EE'
BACKGROUND_PRESETS = (
    ('Default', DEFAULT_BACKGROUND),
    ('Warm cream', '#FFF6E5'),
    ('Soft sage', '#EBF5EC'),
    ('Pale blue', '#EAF4FC'),
    ('Lavender', '#F2EEFA'),
    ('Soft rose', '#FCEFF3'),
    # Slightly richer shades, validated against all existing text colours.
    ('Warm sand', '#EFD9B4'),
    ('Eucalyptus', '#D0E5D6'),
    ('Sky blue', '#CDE3F5'),
    ('Mauve', '#E0D3F1'),
    ('Apricot', '#F5D8C6'),
    ('Butter yellow', '#F5E4A9'),
)

BUTTON_PRESETS = (
    ('Default', DEFAULT_BUTTON),
    ('Warm sand', '#EFD9B4'),
    ('Sage', '#D0E5D6'),
    ('Sky blue', '#CDE3F5'),
    ('Lavender', '#E0D3F1'),
    ('Soft coral', '#F5D8C6'),
    ('Butter yellow', '#F5E4A9'),
    ('Sea glass', '#D1E6DF'),
    ('Cornflower', '#D0E1F9'),
    ('Dusty rose', '#E6D3DA'),
    ('Pistachio', '#DDE8C0'),
    ('Oat', '#E4D9CD'),
)

# These match TkLayoutMaker's high-contrast light theme.
_TEXT_COLORS = ('#17212B', '#895000', '#116239', '#A61B1B')
_HEX_COLOR = re.compile(r'#[0-9a-fA-F]{6}\Z')


def contrast_ratio(first, second):
    """WCAG contrast ratio for two #RRGGBB colours."""
    def luminance(color):
        channels = [int(color[index:index + 2], 16) / 255.0
                    for index in (1, 3, 5)]
        linear = [value / 12.92 if value <= 0.04045
                  else ((value + 0.055) / 1.055) ** 2.4
                  for value in channels]
        return sum(value * weight for value, weight in
                   zip(linear, (0.2126, 0.7152, 0.0722)))

    high, low = sorted((luminance(first), luminance(second)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def is_readable_background(color):
    """Allow light colours that retain clear regular text and coloured feedback."""
    if not isinstance(color, str) or not _HEX_COLOR.fullmatch(color):
        return False
    return (contrast_ratio(_TEXT_COLORS[0], color) >= 7.0 and
            all(contrast_ratio(accent, color) >= 4.5
                for accent in _TEXT_COLORS[1:]))


def is_readable_button(color):
    """Require strong contrast with the regular dark button label."""
    return (isinstance(color, str) and _HEX_COLOR.fullmatch(color) is not None
            and contrast_ratio(_TEXT_COLORS[0], color) >= 7.0)


def active_button_color(color):
    """Darken slightly for hover/press, keeping dark text legible."""
    darker = '#' + ''.join(f'{round(int(color[i:i+2], 16) * .92):02X}'
                         for i in (1, 3, 5))
    if is_readable_button(darker):
        return darker
    return '#' + ''.join(f'{round(int(color[i:i+2], 16) * .8 + 51):02X}'
                       for i in (1, 3, 5))


def preference_path(card_path):
    """Keep preferences beside the selected deck (including test-data overrides)."""
    return Path(card_path).with_name('.flashcards-appearance.json')


def _read_preferences(path):
    try:
        data = json.loads(Path(path).read_text(encoding='utf-8'))
        return data if isinstance(data, dict) else {}
    except (OSError, UnicodeError, ValueError, TypeError):
        return {}


def load_background(path):
    """Read the background without affecting the separately saved button choice."""
    color = _read_preferences(path).get('background')
    return color.upper() if is_readable_background(color) else DEFAULT_BACKGROUND


def load_buttons(path):
    """Recover a readable saved button colour or use the default."""
    color = _read_preferences(path).get('buttons')
    return color.upper() if is_readable_button(color) else DEFAULT_BUTTON


def _save_preference(path, key, color):
    """Atomically save one appearance choice while retaining the other."""
    path = Path(path)
    data = _read_preferences(path)
    data[key] = color.upper()
    descriptor, temporary = tempfile.mkstemp(
        prefix='.flashcards-appearance-', suffix='.tmp', dir=path.parent
    )
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as handle:
            json.dump(data, handle, indent=2)
            handle.write('\n')
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def save_background(path, color):
    """Persist background while preserving an existing button-colour choice."""
    if not is_readable_background(color):
        raise ValueError('Background is too dark or invalid for readable text.')
    _save_preference(path, 'background', color)


def save_buttons(path, color):
    """Persist buttons while preserving an existing background colour."""
    if not is_readable_button(color):
        raise ValueError('Button colour is too dark or invalid for readable text.')
    _save_preference(path, 'buttons', color)
