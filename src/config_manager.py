import json
from pathlib import Path
from typing import Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ConfigManager:
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_path: str = "config/config.json"):
        if ConfigManager._config is not None:
            return
        
        self.config_path = Path(config_path)
        self._load_config()
    
    def _load_config(self) -> None:
        try:
            # Checke ob config.json existiert
            if not self.config_path.exists():
                logger.warning(f"Config file not found at {self.config_path}")
                
                # Versuche aus Template zu erstellen
                template_path = self.config_path.parent / "config_template.json"
                
                if template_path.exists():
                    import shutil
                    shutil.copy(template_path, self.config_path)
                    logger.info(f" Config created successfully at {self.config_path}")
                else:
                    raise FileNotFoundError(
                        f"Config file not found at {self.config_path} and template not found at {template_path}"
                    )
            
            # Lade die Config
            with open(self.config_path, 'r', encoding='utf-8') as f:
                ConfigManager._config = json.load(f)
        
        except Exception as e:
            raise RuntimeError(f"Error loading/creating configuration file: {e}")
        
    @staticmethod
    def get_config(key_path: str, default: Any = None) -> Any:
        if ConfigManager._config is None:
            raise RuntimeError("Configuration not loaded. Please initialize ConfigManager first.")
        
        keys = key_path.split('.')
        value = ConfigManager._config
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default

        return value if value is not None else default
    
    @staticmethod
    def reload() -> None:
        ConfigManager._config = None
        manager = ConfigManager()
        manager._load_config()
_manager = ConfigManager()

class StringManager:
    _instance = None
    _strings = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if StringManager._strings:
            return
        self._load_strings()

    def _load_strings(self) -> None:
        try:
            with open("config/strings.json", 'r', encoding='utf-8') as f:
                StringManager._strings = json.load(f)
        except Exception as e:
            raise RuntimeError(f"Error loading strings file: {e}")
        
    @classmethod
    def get(cls, msg_type, key, default=None, **kwargs) -> str:
        keys = key.split('.')
        string = cls._strings

        for k in keys:
            if isinstance(string, dict):
                if default is not None:
                    string = string.get(k, default)
                else:
                    string = string.get(k, f"Missing string for key: {key}")
            else:
                return f"Invalid string path: {key}"
        
        if isinstance(string, str):
            prefix = cls.msg_type_prefix(msg_type)
            return f"{prefix}{string.format(**kwargs)}"
        return f"String for key '{key}' is not a valid string."
    
    @classmethod
    def msg_type_prefix(cls, msg_type: str) -> str:
        try: 
            return cls._strings['message_types'][msg_type.value]
        except KeyError:
            return cls._strings['message_types']['info']

class StringType(Enum):
    SUCCESS = "success"
    ANSWER = "answer"
    DENY = "deny"
    INFO = "info"
    WARN = "warn"
    APPENDIX = "appendix"