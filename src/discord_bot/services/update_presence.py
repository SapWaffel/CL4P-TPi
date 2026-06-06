import discord
from src.config_manager import ConfigManager
import random

async def update_presence(self):
    MAINTENANCE = ConfigManager.get("maintenance", False)
    if MAINTENANCE:
        await self.change_presence(activity=discord.CustomActivity(name="Maintenance"), status=discord.Status.do_not_disturb)
    else:
        quotes = ConfigManager.get("discord.quotes", [])
        await self.application.edit(description=random.choice(quotes))
        await self.change_presence(activity=discord.Game(name="Borderlands"))
