import json
import os
from typing import Dict, Any

from .paths import DATA_DIR


SETTINGS_PATH = os.path.join(DATA_DIR, 'settings.json')

DEFAULT_SETTINGS: Dict[str, Any] = {
    'tor_enabled': False,
    'homepage': 'http://google.com',
}


def load_settings() -> Dict[str, Any]:
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    merged = DEFAULT_SETTINGS.copy()
                    merged.update(data)
                    return merged
        except Exception:
            pass
    return DEFAULT_SETTINGS.copy()


def save_settings(settings: Dict[str, Any]) -> None:
    to_save = DEFAULT_SETTINGS.copy()
    to_save.update(settings)
    try:
        with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
            json.dump(to_save, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

