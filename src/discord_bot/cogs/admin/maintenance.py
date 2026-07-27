import discord
from discord.ext import commands
from discord import app_commands

from src.config_manager import ConfigManager, StringManager, StringType
from src.discord_bot.services.update_presence import update_presence
from src.discord_bot.checks import require_rights
from src.models import RightsLevel

GUILD_ID = int(ConfigManager.get("discord.guild_id"))

class MaintenanceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.command(name="maintenance", description="Toggle maintenance mode")
    @require_rights(RightsLevel.ADMIN)
    async def maintenance(self, interaction: discord.Interaction):
        current_state = ConfigManager.get("maintenance", False)
        new_state = not current_state

        ConfigManager.set("maintenance", new_state)

        await update_presence(self.bot)

        status = "enabled" if new_state else "disabled"
        response = StringManager.get(
            StringType.ANSWER, f"response.maintenance.{status}"
        )
        await interaction.response.send_message(response)

async def setup(bot):
    await bot.add_cog(MaintenanceCog(bot))