import discord
from discord.ext import commands
from discord import app_commands
import logging
import asyncio
import sys

from src.config_manager import ConfigManager, StringManager, StringType 
from src.util.git_update import GitUpdater

logger = logging.getLogger(__name__)
GUILD_ID = discord.Object(id=ConfigManager.get_config("discord.guild_id"))

class UpdateCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="update", description="Fetch the latest changes from git and restart the bot")
    @app_commands.guilds(GUILD_ID)
    @app_commands.default_permissions(administrator=True)
    async def update(self, interaction: discord.Interaction):

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                StringManager.get(StringType.DENY, "error.no_permission"),
                ephemeral=True
            )
            logger.warning(f"Unauthorized update attempted by {interaction.user}")
            return

        await interaction.response.defer()

        try:
            await interaction.followup.send(StringManager.get(StringType.INFO, "response.update.fetch"))
            logger.info(f"User {interaction.user} initiated an update")

            result = GitUpdater.update()

            if result["success"]:
                #edit message to show the output of the git pull command
                await interaction.edit_original_response(content=StringManager.get(StringType.INFO, "response.update.success"))
                logger.info("Update successful, bot is restarting")

                await asyncio.sleep(2)
                sys.exit(0)
            else:
                await interaction.followup.send(StringManager.get(StringType.WARN, "response.update.error", error=result['error']))
                logger.error(f"Update failed: {result['error']}")

        except Exception as e:
            await interaction.followup.send(StringManager.get(StringType.WARN, "response.update.error", error=str(e)))
            logger.error(f"Error during update: {e}")

async def setup(bot):
    await bot.add_cog(UpdateCog(bot))