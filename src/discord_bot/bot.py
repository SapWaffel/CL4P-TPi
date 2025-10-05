# src/discord_bot/bot.py
import time
import logging
import os
from xml.sax import handler

import discord
from discord.ext import commands
import asyncio

from src.config_manager import ConfigManager, StringManager, StringType
from src.discord_bot.logs.rl_log.log_handler import RelevanceLogger, LogType
from src.discord_bot.util.refresh_presence import refresh_presence
from src.discord_bot.util.is_admin_on_guild import is_admin_on_guild

from src.discord_bot.util.custom_help_command import CustomHelpCommand
from src.discord_bot.util.respond_after_reload import respond_after_reload

# CONFIG
config = ConfigManager.get_config('discord_bot')
TOKEN = config["token"]
PREFIX = config["prefix"]
MAINTENANCE = config["maintenance"]

# RELEVANCE LOGGING
RelevanceLogger.create_log_file()
RelevanceLogger.write_log_entry("Bot is starting...", "SYSTEM")

# DISCORD NATIVE LOGGING
discord_log_dir = 'src/discord_bot/logs/discord_log'
os.makedirs(discord_log_dir, exist_ok=True)  # Verzeichnis anlegen, falls nicht vorhanden

discord_log_file_name = f'discord_{time.strftime("%Y-%m-%d_%H-%M-%S")}'

discord_log_handler = logging.FileHandler(
    filename=f'{discord_log_dir}/{discord_log_file_name}.log',
    encoding='utf-8',
    mode='w'
)

# remove old log files
max_log_files = config["max_log_files"]
log_files = sorted([f for f in os.listdir(discord_log_dir) if f.startswith('discord_') and f.endswith('.log')])
if len(log_files) > max_log_files:
    for old_file in log_files[:-max_log_files]:
        os.remove(os.path.join(discord_log_dir, old_file))

# BOT INTENTS
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# BOT SETUP
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=CustomHelpCommand())

@bot.event
async def on_ready():
    logging.basicConfig(level=logging.INFO, handlers=[discord_log_handler])
    logging.info(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    RelevanceLogger.write_log_entry(f"Bot is ready as {bot.user.name} (ID: {bot.user.id})", "SYSTEM")

    if MAINTENANCE:
        await bot.application.edit(description="Currently in maintenance mode.")
    RelevanceLogger.write_log_entry("Bot is online and operational", "SYSTEM")

    # Presence
    await refresh_presence(bot)

    # Check for reload response
    reload_response = ConfigManager.get_config('discord_bot')["reload_response"]
    if reload_response["waiting_for_response"] and reload_response["user"] is not None:
        await respond_after_reload(bot, reload_response["user"])
        
@bot.event
async def on_message(message):
    # ignore bot messages
    if message.author.bot:
        return
    # wrong channel
    cmd_channel_name = config["commands_channel_name"]
    if isinstance(message.channel, discord.TextChannel) and message.channel.name != cmd_channel_name:
        await message.delete()
        await message.channel.send(StringManager.get_string(StringType.INFO, "error.wrong_channel", channel=cmd_channel_name), delete_after=10)

        return
   # maintenance mode (ignore admins, ignore help command)
    if MAINTENANCE and not await is_admin_on_guild(bot, message.author.id) and not message.content.startswith(f"{PREFIX}help"):
        await message.channel.send(StringManager.get_string(StringType.WARNING, "error.maintenance"))
        RelevanceLogger.write_log_entry(f"{message.author}", "attempt to use bot refused (maintenance)", type=LogType.WARNING)
        return
    # process commands
    await bot.process_commands(message)

@bot.event
async def on_command_error(ctx, error):
    # unknown command
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(StringManager.get_string(StringType.ERROR, "error.unknown_command", prefix=PREFIX))
        RelevanceLogger.write_log_entry(f"cmd.{ctx.command} failed (unknown command)", f"{ctx.author}", type=LogType.INFO)
        return
    # only in pms
    elif isinstance(error, commands.PrivateMessageOnly):
        RelevanceLogger.write_log_entry(f"cmd.{ctx.command} failed (private message only)", f"{ctx.author}", type=LogType.INFO)
        if is_admin_on_guild(bot, ctx.author.id):
            await ctx.send(StringManager.get_string(StringType.ERROR, "error.private_message_only"))
        else:
            await ctx.send(StringManager.get_string(StringType.ERROR, "error.no_permission"))
        return
    # no permission
    elif isinstance(error, commands.MissingPermissions):
        RelevanceLogger.write_log_entry(f"cmd.{ctx.command} failed (no permission)", f"{ctx.author}", type=LogType.INFO)
        await ctx.send(StringManager.get_string(StringType.ERROR, "error.no_permission"))
        return
    # other errors
    else:
        RelevanceLogger.write_log_entry(f"cmd.{ctx.command} failed (unknown error: {str(error)})", f"{ctx.author}", type=LogType.ERROR)
        raise error
    
# LOAD COGS
async def load_cogs():
    base_package = "src.discord_bot.cogs"
    base_dir = os.path.join(os.path.dirname(__file__), "cogs")
    for root, dirs, files in os.walk(base_dir):
        for filename in files:
            if filename.endswith('.py') and not filename.startswith('__'):
                try:
                    rel_path = os.path.relpath(os.path.join(root, filename), base_dir)
                    module_path = rel_path.replace(os.sep, '.')[:-3]  # remove .py
                    cog_path = f"{base_package}.{module_path}"
                    await bot.load_extension(cog_path)
                    RelevanceLogger.write_log_entry(f"Loaded cog: {filename}", "SYSTEM")
                except Exception as e:
                    RelevanceLogger.write_log_entry(f"Failed to load cog: {filename} ({str(e)})", "SYSTEM", type=LogType.ERROR)

if __name__ == '__main__':
    asyncio.run(load_cogs())
    bot.run(TOKEN, log_handler=discord_log_handler, log_level=logging.DEBUG)