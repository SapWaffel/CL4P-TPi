import discord
from discord.ext import commands
from discord import app_commands
from src.mqtt import MqttManager
from src.discord_bot.logs.rl_log.log_handler import RelevanceLogger, LogType
from src.config_manager import StringManager, StringType

from src.config_manager import ConfigManager
GUILD_ID = discord.Object(id=ConfigManager.get_config('discord_bot')['guild_id'])

class StatusCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.guilds(GUILD_ID)
    @app_commands.command(name="status", description="Fragt CL4P-TPs aktuellen Status ab.")
    async def status_command(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            status = MqttManager.read("status")
        except Exception as e:
            RelevanceLogger.write_log_entry(f"cmd.status - failed to get status: {e}", interaction.user, LogType.ERROR)
            await interaction.followup.send(StringManager.get_string(StringType.ERROR, "error.generic"))
            return
        if status == "starting": status = "am booten"
        await interaction.followup.send(StringManager.get_string(StringType.SUCCESS, "response.status", status=str(status)))
        RelevanceLogger.write_log_entry(f"cmd.status - success ({status})", interaction.user, LogType.INFO)

async def setup(bot):
    await bot.add_cog(StatusCog(bot))