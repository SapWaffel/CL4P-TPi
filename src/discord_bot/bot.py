import os
import discord
from discord.ext import commands
import logging

from src.config_manager import ConfigManager, StringManager
from src.discord_bot.services.restriction_service import RestrictionService

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# load config
TOKEN = ConfigManager.get_config("discord.token")
GUILD_ID = discord.Object(id=int(ConfigManager.get_config("discord.guild_id")))

# StringManager beim Start initialisieren
string_manager = StringManager()

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class CL4PiBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.synced = False
    
    async def on_ready(self):
        logging.info(f"Logged in as {self.user} (ID: {self.user.id})")

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
bot = CL4PiBot(command_prefix="/", intents=intents)

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
    
    logger.info("Starting CL4P-TPi Bot...")
    try:
        bot.run(TOKEN)
    except Exception as e:
        logger.error(f"Error running the bot: {e}")

if __name__ == "__main__":
    run()