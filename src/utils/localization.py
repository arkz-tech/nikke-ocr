import json
import os
from typing import Dict

from src.config import Config


class Localization:
    def __init__(self):
        self.current_language = "en"
        self.translations: Dict[str, Dict[str, str]] = {"en": {}, "es": {}}
        self.load_translations()

    def load_translations(self):
        for lang in ["en", "es"]:
            file_path = os.path.join(Config.LANG_DIR, f"{lang}.json")
            with open(file_path, "r", encoding="utf-8") as f:
                self.translations[lang] = json.load(f)

    def set_language(self, lang: str):
        if lang in self.translations:
            self.current_language = lang

    def get_text(self, key: str) -> str:
        return self.translations[self.current_language].get(key, key)


_localization = Localization()


def get_localized_text(key: str) -> str:
    return _localization.get_text(key)


def set_language(lang: str):
    _localization.set_language(lang)
