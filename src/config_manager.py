# src/config_manager.py
import json, os
from enum import Enum

class ConfigManager:
    _configs = {}

    @classmethod
    def get_config(cls, module):
        if module not in cls._configs:
            config_path = os.path.join(os.path.dirname(__file__), '../config', f'{module}.json')
            with open(config_path, encoding="utf-8") as f:
                cls._configs[module] = json.load(f)
        return cls._configs[module]
    
    @classmethod
    def merge_config(cls, module, new_data):
        config = cls.get_config(module)
        config.update(new_data)
        config_path = os.path.join(os.path.dirname(__file__), '../config', f'{module}.json')
        with open(config_path, 'w', encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        cls._configs[module] = config

class StringManager:
    _strings = ConfigManager.get_config('strings')

    @classmethod
    # Example usage: StringManager.get_string(StringType.SUCCESS, "response.reload.start")
    def get_string(cls, msg_type ,key, **kwargs):
        # Nested key access
        keys = key.split('.')
        string = cls._strings.get(msg_type.value, cls._strings)
        for i, k in enumerate(keys):
            if isinstance(string, dict):
                string = string.get(k, f'Key "{key}" not found in strings.json')
            else:
                return f'Key "{key}" not found in strings.json'
        if isinstance(string, str):
            prefix = cls.msg_type_prefix(msg_type)
            return f'{prefix} {string}'.format(**kwargs)
        return f'Key "{key}" not found in strings.json'
    @classmethod
    def msg_type_prefix(cls, msg_type):
        try:
            return cls._strings['message_types'][msg_type.value]
        except KeyError:
            return cls._strings['message_types']["info"]

class StringType(Enum):
    SUCCESS = "success"
    ERROR = "error"
    INFO = "info"
    WARNING = "warning"
    PROCESSING = "processing"
    APPENDIX = "appendix"