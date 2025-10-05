# src/config_manager.py
import json
import os

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