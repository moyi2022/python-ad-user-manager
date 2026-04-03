import os
from datetime import datetime

class LogService:
    _log_path = os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'AdUserManager', 'app.log')

    @classmethod
    def log(cls, message):
        try:
            directory = os.path.dirname(cls._log_path)
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open(cls._log_path, 'a', encoding='utf-8') as f:
                f.write(f'[{timestamp}] {message}\n')
        except Exception:
            pass

    @classmethod
    def log_error(cls, message, ex):
        cls.log(f'ERROR: {message} - {ex}')
