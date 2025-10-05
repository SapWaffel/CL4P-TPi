from enum import Enum
import os
import time
from src.config_manager import ConfigManager

global CURRENT
CURRENT = None

class LogType(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

class RelevanceLogger:

    @classmethod
    def create_log_file(cls):
        current_time = time.strftime("%Y-%m-%d_%H-%M-%S")
        log_dir = os.path.dirname(os.path.abspath(__file__))
        log_file_name = f"rl_{current_time}.log"
        log_file_path = os.path.join(log_dir, log_file_name)

        # Ensure log directory exists
        os.makedirs(log_dir, exist_ok=True)

        with open(log_file_path, 'w') as log_file:
            pass

        global CURRENT
        CURRENT = log_file_name

        # if more than max_log_files, delete the oldest one
        max_log_files = ConfigManager.get_config('discord_bot')["max_log_files"]
        log_files = [f for f in os.listdir(log_dir) if f.startswith("rl_") and f.endswith(".log")]
        log_files.sort()
        if len(log_files) > max_log_files:
            oldest_file = log_files[0]
            oldest_file_path = os.path.join(log_dir, oldest_file)
            os.remove(oldest_file_path)

        return log_file_path

    @classmethod
    def write_log_entry(cls, msg, user_id, type=LogType.INFO):
        if CURRENT is None:
            cls.create_log_file()
        log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CURRENT)

        entry = f"[{time.strftime('%Y-%m-%d %H:%M:%S')} | {type.value.upper()} | {user_id}] {msg}\n"

        with open(log_file_path, 'a') as log_file:
            log_file.write(entry)
