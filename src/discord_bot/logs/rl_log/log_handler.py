from enum import Enum
import os
import time
from src.config_manager import ConfigManager

class LogType(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

class RelevanceLogger:
    log_dir = os.path.dirname(os.path.abspath(__file__))
    latest_log_file = os.path.join(log_dir, "latest.log")
    final_log_file_name = None

    @classmethod
    def create_log_file(cls):
        # Set the final log file name for later renaming
        current_time = time.strftime("%Y-%m-%d_%H-%M-%S")
        cls.final_log_file_name = f"rl_{current_time}.log"
        os.makedirs(cls.log_dir, exist_ok=True)
        # Create/clear latest.log
        with open(cls.latest_log_file, 'w') as log_file:
            pass
        # Delete old log files if more than max_log_files exist
        max_log_files = ConfigManager.get_config("discord_bot")["max_log_files"]
        log_files = [f for f in os.listdir(cls.log_dir) if f.startswith("rl_") and f.endswith(".log")]
        log_files.sort()
        while len(log_files) >= max_log_files:
            os.remove(os.path.join(cls.log_dir, log_files.pop(0)))

    @classmethod
    def write_log_entry(cls, msg, user_id, type=LogType.INFO):
        if not os.path.exists(cls.latest_log_file):
            cls.create_log_file()
        entry = f"[{time.strftime('%Y-%m-%d %H:%M:%S')} | {type.value.upper()} | {user_id}] {msg}\n"
        with open(cls.latest_log_file, 'a') as log_file:
            log_file.write(entry)

    @classmethod
    def finalize_log_file(cls):
        # Rename latest.log to the final log file name
        if cls.final_log_file_name and os.path.exists(cls.latest_log_file):
            final_path = os.path.join(cls.log_dir, cls.final_log_file_name)
            os.rename(cls.latest_log_file, final_path)

