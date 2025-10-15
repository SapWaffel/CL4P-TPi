# GitHub Updater
import src.discord_bot.util.GitUpdater

# Discord Bot
import os, random
import discord
from discord.ext import commands

from src.config_manager import ConfigManager, StringManager, StringType
from src.discord_bot.logs.rl_log.log_handler import RelevanceLogger, LogType
from src.discord_bot.util.respond_after_reload import respond_after_reload

# CONFIG
config = ConfigManager.get_config('discord_bot')
TOKEN = config["token"]
MAINTENANCE = config["maintenance"]
GUILD_ID = discord.Object(id=config["guild_id"])

class Bot(commands.Bot):
    async def on_ready(self):
        RelevanceLogger.write_log_entry(f"Bot is ready as {self.user} (ID: {self.user.id}).", "SYSTEM", LogType.INFO)
        if MAINTENANCE: RelevanceLogger.write_log_entry("Bot is in maintenance mode", "SYSTEM", type=LogType.WARNING)
        await self.update_presence()

        await setup(self)

        # Sync commands to guild
        try:
            synced = await self.tree.sync(guild=GUILD_ID)
            RelevanceLogger.write_log_entry(f"Synced {len(synced)} command(s) to the guild {GUILD_ID.id}.", "SYSTEM", LogType.INFO)
        except Exception as e:
            RelevanceLogger.write_log_entry(f"Failed to sync commands to guild {GUILD_ID.id}: {e}", "SYSTEM", LogType.ERROR)

        # Respond after reload
        response_data = ConfigManager.get_config('discord_bot')['reload_response']
        if response_data["waiting_for_response"] and response_data["channel"] is not None:
            await respond_after_reload(bot, response_data)

    async def update_presence(self):
        if MAINTENANCE:
            await self.change_presence(activity=discord.CustomActivity(name="Maintenance"), status=discord.Status.do_not_disturb)
        else:
            quotes = ConfigManager.get_config('discord_bot')['quotes']
            await self.application.edit(description=random.choice(quotes))
            await self.change_presence(activity=discord.Game(name="Borderlands 3"), status=discord.Status.online)

    async def close(self):
        RelevanceLogger.write_log_entry("Bot is shutting down...", "SYSTEM", LogType.INFO)
        RelevanceLogger.write_log_entry("Goodbye!", "SYSTEM", LogType.INFO)
        RelevanceLogger.finalize_log_file()
        await super().close()

    async def on_message(self, message):
        if message.author == self.user:
            return

        if config['watch_for_steve'] and message.content.strip() == "Hey-ooo":
            await message.reply("**SHUT THE FUCK UP, STEVE!**")

        if message.content.startswith("!"):
            await message.channel.send(StringManager.get_string(StringType.ERROR, "error.non_slash_prefix", user=message.author.mention))
            await message.delete()
            return
        
        await self.process_commands(message)

intents = discord.Intents.default()
intents.message_content = True
bot = Bot(command_prefix="!", intents=intents)
bot.GUILD_ID = GUILD_ID

async def setup(bot):
    cogs_dir = os.path.join(os.path.dirname(__file__), "cogs")
    for root, dirs, files in os.walk(cogs_dir):
        for file in files:
            if file.endswith(".py") and not file.startswith("__"):
                rel_path = os.path.relpath(os.path.join(root, file), os.path.dirname(__file__))
                module = rel_path.replace(os.sep, ".")[:-3]  # .py entfernen
                module = f"src.discord_bot.{module}"
                try:
                    await bot.load_extension(module)
                    RelevanceLogger.write_log_entry(f"Loaded extension: {module}", "SYSTEM", LogType.INFO)
                except Exception as e:
                    RelevanceLogger.write_log_entry(f"Failed to load extension {module}: {e}", "SYSTEM", LogType.ERROR)
        

async def maintenance_check(interaction: discord.Interaction) -> bool:
    if MAINTENANCE:
        if interaction.user.guild_permissions.administrator:
            return True
        await interaction.response.send_message(
            StringManager.get_string(StringType.ERROR, "maintenance"),
            ephemeral=True
        )
        return False
    return True

bot.tree.interaction_check = maintenance_check

if __name__ == '__main__':
    if ConfigManager.get_config('_global')['auto_update']:
        src.discord_bot.util.GitUpdater.check_for_updates()

    bot.run(TOKEN)