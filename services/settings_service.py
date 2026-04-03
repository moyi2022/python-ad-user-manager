import json
import os

class SettingsService:
    _settings_path = os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'AdUserManager', 'settings.json')

    def __init__(self):
        self.settings = self._load()

    def _load(self):
        try:
            if os.path.exists(self._settings_path):
                with open(self._settings_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return self._default_settings()

    def _default_settings(self):
        return {
            'saved_username': '',
            'page_size': 25,
            'window_width': 800,
            'window_height': 500
        }

    def save(self):
        try:
            directory = os.path.dirname(self._settings_path)
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            with open(self._settings_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            from .log_service import LogService
            LogService.log('Settings saved')
        except Exception as ex:
            from .log_service import LogService
            LogService.log_error('Failed to save settings', ex)

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        self.settings[key] = value
