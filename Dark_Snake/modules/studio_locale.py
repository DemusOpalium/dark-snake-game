"""Language selection and text lookup for World Studio."""

from modules.editor_buttons import BUTTON_EN
from modules.studio_editor_text import EDITOR_EN
from modules.studio_panel_text import PANEL_EN
from modules.studio_tutorial_text import TUTORIAL_EN


DEFAULT_STUDIO_LANGUAGE = "en"
STUDIO_LANGUAGES = ("en", "de")


def normalize_studio_language(value):
    if isinstance(value, str):
        code = value.strip().lower()
        if code in STUDIO_LANGUAGES:
            return code
    return DEFAULT_STUDIO_LANGUAGE


class StudioLocale:
    """Keep source text readable when an English translation is unavailable."""

    def __init__(self, language=DEFAULT_STUDIO_LANGUAGE):
        self.language = language

    @property
    def language(self):
        return self._language

    @language.setter
    def language(self, value):
        self._language = normalize_studio_language(value)

    def __call__(self, message, **values):
        localized = _ENGLISH.get(message, message) if self.language == "en" else message
        if not values:
            return localized
        try:
            return localized.format(**values)
        except (IndexError, KeyError, ValueError):
            # A malformed translation must not prevent the editor from drawing.
            try:
                return message.format(**values)
            except (IndexError, KeyError, ValueError):
                return message


_ENGLISH = BUTTON_EN | PANEL_EN | EDITOR_EN | TUTORIAL_EN
