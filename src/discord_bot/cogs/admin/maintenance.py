import discord
from discord.ext import commands
from discord import app_commands

from src.config_manager import ConfigManager, StringManager, StringType
from src.discord_bot.services.update_presence import update_presence
from src.util.db.database_manager import DatabaseManager

GUILD_ID = int(ConfigManager.get("discord.guild_id"))

class MaintenanceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.command(name="maintenance", description="Toggle maintenance mode")
    async def maintenance(self, interaction: discord.Interaction):

        rights_level = DatabaseManager.get("discord", "user", {"discord_id": int(interaction.user.id)}, "rights_level")
        if not rights_level:
            response = StringManager.get(StringType.WARN, "error.generic")
            await interaction.response.send_message(response, ephemeral=True)
            return

        if rights_level < 3:
            response = StringManager.get(StringType.WARN, "error.no_permission")
            await interaction.response.send_message(response, ephemeral=True)
            return

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