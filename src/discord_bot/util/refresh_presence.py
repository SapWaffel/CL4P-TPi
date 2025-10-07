# presence
import discord
from src.config_manager import ConfigManager
import random

from src.discord_bot.logs.rl_log.log_handler import RelevanceLogger, LogType

def get_random_quote():
    quotes = ConfigManager.get_config('discord_bot')['quotes']
    return random.choice(quotes)

async def refresh_presence(bot):
    MAINTENANCE = ConfigManager.get_config('discord_bot')["maintenance"]

    if MAINTENANCE:
        RelevanceLogger.write_log_entry("Bot is in maintenance mode", "SYSTEM", type=LogType.WARNING)
        await bot.change_presence(activity=discord.CustomActivity(name="Maintenance"), status=discord.Status.do_not_disturb)
    else:
        print("Bot is online and operational")
        await bot.change_presence(activity=discord.Game(name="Borderlands 3"), status=discord.Status.online)
        await bot.application.edit(description=get_random_quote())
    