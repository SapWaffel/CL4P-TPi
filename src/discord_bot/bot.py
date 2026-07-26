import os
import discord
from discord.ext import commands
from discord import app_commands
import logging

from src.config_manager import ConfigManager, StringManager, StringType
from src.discord_bot.services.update_presence import update_presence
from src.discord_bot.checks import get_rights_level
from src.models import RightsLevel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
ConfigManager = ConfigManager()
StringManager = StringManager()

TOKEN = ConfigManager.get("discord.token")
GUILD_ID = discord.Object(id=int(ConfigManager.get("discord.guild_id")))

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

async def global_maintenance_check(interaction: discord.Interaction) -> bool:
    if not ConfigManager.get("maintenance", False):
        return True

    rights_level = get_rights_level(interaction.user.id)
    if rights_level and rights_level >= RightsLevel.ADMIN:
        return True

    await interaction.response.send_message(
        StringManager.get(StringType.WARN, "error.maintenance"), ephemeral=True
    )
    return False

# hook for the global check to be used in the command tree
class CL4PiCommandTree(app_commands.CommandTree):
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return await global_maintenance_check(interaction)


class CL4PiBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.synced = False

    async def on_ready(self):
        logging.info(f"Logged in as {self.user} (ID: {self.user.id})")

        await update_presence(self)

        if not self.synced:
            await self.__sync_commands()
            self.synced = True

    async def __sync_commands(self):
        try:
            synced = await self.tree.sync(guild=GUILD_ID)
            logging.info(f"Synced {len(synced)} commands to guild {GUILD_ID.id}")
        except Exception as e:
            logging.error(f"Error syncing commands: {e}")

    async def close(self):
        await super().close()
        logging.info("Bot has been closed.")

# Bot
bot = CL4PiBot(command_prefix="/", intents=intents, tree_cls=CL4PiCommandTree)


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        return
    logging.error(f"Unhandled app command error: {error}", exc_info=error)


async def load_cogs():
    cogs_dir = os.path.join(os.path.dirname(__file__), "cogs")
    for root, dirs, files in os.walk(cogs_dir):
        for file in files:
            if file.endswith(".py") and not file.startswith("__"):
                rel_path = os.path.relpath(os.path.join(root, file), os.path.dirname(__file__))
                module = rel_path.replace(os.sep, ".")[:-3] 
                module = f"src.discord_bot.{module}"
                try:
                    await bot.load_extension(module)
                    logging.info(f"Loaded cog: {module}")
                except Exception as e:
                    logging.error(f"Failed to load cog {module}: {e}")

@bot.event
async def setup_hook():
    await load_cogs()

def run():
    if TOKEN is None or TOKEN == "YOUR_BOT_TOKEN":
        raise ValueError("Bot token is not set in the configuration.")
    if GUILD_ID is None or GUILD_ID.id == 0 or GUILD_ID.id == "YOUR_GUILD_ID":
        raise ValueError("Guild ID is not set in the configuration.")
    
    logger.info("Starting CL4P-TPi Bot...")

    try:
        bot.run(TOKEN)
    except Exception as e:
        logger.error(f"Error running the bot: {e}")

if __name__ == "__main__":
    run()