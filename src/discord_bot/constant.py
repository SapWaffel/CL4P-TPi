import discord
from src.config_manager import ConfigManager

GUILD_ID = discord.Object(id=ConfigManager.get_config('discord_bot')['guild_id'])
