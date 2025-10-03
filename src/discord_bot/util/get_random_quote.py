from src.config_manager import ConfigManager
import random

def get_random_quote():
    quotes = ConfigManager.get_config('discord_bot')['quotes']
    return random.choice(quotes)